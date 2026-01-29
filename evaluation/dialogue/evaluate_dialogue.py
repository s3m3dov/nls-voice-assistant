#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.dialogue.chat import chat_stream, build_system_prompt
from src.dialogue.tools import TOOLS, TOOL_REGISTRY

def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return str(value)


def _normalize_args(args: Any) -> Dict[str, Any]:
    if args is None:
        return {}
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
            if isinstance(parsed, dict):
                return parsed
            return {"_raw": parsed}
        except json.JSONDecodeError:
            return {"_raw": args}
    return {"_raw": args}


def _args_match(expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
    if set(expected.keys()) != set(actual.keys()):
        return False
    for key, expected_value in expected.items():
        if _normalize_value(expected_value) != _normalize_value(actual.get(key)):
            return False
    return True


def _args_contains(expected_subset: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, List[str]]:
    mismatches = []
    for key, expected_value in expected_subset.items():
        if _normalize_value(expected_value) != _normalize_value(actual.get(key)):
            mismatches.append(key)
    return (len(mismatches) == 0), mismatches


def _slot_pairs(args: Dict[str, Any]) -> set:
    return {(k, _normalize_value(v)) for k, v in args.items()}


def load_test_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r') as f:
        return json.load(f)

def run_evaluation(test_cases_path: str, *, print_results: bool = True) -> Dict[str, Any]:
    cases = load_test_cases(test_cases_path)
    results = []
    
    if print_results:
        print(f"Running evaluation on {len(cases)} test cases...\n")
    
    passed_count = 0
    tool_expected = 0
    tool_correct = 0
    slot_tp = 0
    slot_fp = 0
    slot_fn = 0
    
    for case in cases:
        case_id = case["id"]
        user_input = case["input"]
        expected_tool = case.get("expected_tool")
        expected_args = case.get("expected_args")
        expected_args_contains = case.get("expected_args_contains")
        if expected_tool:
            tool_expected += 1
        
        if print_results:
            print(f"Test Case: {case_id}")
            print(f"Input: {user_input}")
        
        # Reset conversation for each test
        messages = [{"role": "system", "content": build_system_prompt()}]
        
        # We need to consume the generator to trigger tool calls
        # We capture the printed chunks just to silence them or debug
        response_text = ""
        try:
            for chunk in chat_stream(user_input, messages):
                response_text += chunk
        except Exception as e:
            if print_results:
                print(f"Error during execution: {e}")
            results.append({"id": case_id, "status": "error", "error": str(e)})
            continue
            
        # Inspect messages for tool calls
        # We look for the last assistant message that has tool_calls
        tool_calls_found = []
        for msg in messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                for tc in msg["tool_calls"]:
                    tool_calls_found.append(tc)
        
        # Analyze results
        success = False
        actual_tool = None
        actual_args = None
        
        if not tool_calls_found:
            if expected_tool is None:
                success = True # Expected no tool, got no tool
            else:
                if print_results:
                    print(f"Expected tool '{expected_tool}', but no tool was called.")
        else:
            # For simplicity, check the first tool call
            first_call = tool_calls_found[0]
            actual_tool = first_call["function"]["name"]
            actual_args = _normalize_args(first_call["function"]["arguments"])
            
            if expected_tool:
                if actual_tool == expected_tool:
                    tool_correct += 1
                    # Check arguments
                    args_match = True
                    if expected_args:
                        if not _args_match(expected_args, actual_args):
                            args_match = False
                            if print_results:
                                print(f"Tool match, but args mismatch.\n   Expected: {expected_args}\n   Actual:   {actual_args}")
                    
                    if expected_args_contains:
                        contains_ok, mismatches = _args_contains(expected_args_contains, actual_args)
                        if not contains_ok:
                            args_match = False
                            for k in mismatches:
                                if print_results:
                                    print(f"Tool match, but arg '{k}' mismatch.\n   Expected: {expected_args_contains.get(k)}\n   Actual:   {actual_args.get(k)}")
                    
                    if args_match:
                        success = True
                else:
                    if print_results:
                        print(f"Wrong tool called. Expected '{expected_tool}', got '{actual_tool}'")
            else:
                if print_results:
                    print(f"Expected no tool, but got '{actual_tool}'")

        # Slot-level metrics (only when expected tool is defined and tool matches)
        if expected_tool and actual_tool == expected_tool:
            expected_slots = {}
            if expected_args:
                expected_slots.update(expected_args)
            if expected_args_contains:
                expected_slots.update(expected_args_contains)
            if expected_slots:
                gold = _slot_pairs(expected_slots)
                pred = _slot_pairs(actual_args or {})
                slot_tp += len(gold & pred)
                slot_fp += len(pred - gold)
                slot_fn += len(gold - pred)

        if success:
            if print_results:
                print("PASS")
            passed_count += 1
        else:
            if print_results:
                print("FAIL")
        
        if print_results:
            print("-" * 40)
        results.append({
            "id": case_id,
            "status": "pass" if success else "fail",
            "actual_tool": actual_tool,
            "actual_args": actual_args
        })

    accuracy = (passed_count / len(cases)) * 100
    tool_accuracy = (tool_correct / tool_expected) * 100 if tool_expected else 0.0
    slot_precision = (slot_tp / (slot_tp + slot_fp)) if (slot_tp + slot_fp) else 0.0
    slot_recall = (slot_tp / (slot_tp + slot_fn)) if (slot_tp + slot_fn) else 0.0
    if (slot_precision + slot_recall) > 0:
        slot_f1 = 2 * slot_precision * slot_recall / (slot_precision + slot_recall)
    else:
        slot_f1 = 0.0

    if print_results:
        print(f"\nEvaluation Complete.")
        print(f"Accuracy: {accuracy:.1f}% ({passed_count}/{len(cases)})")
        if tool_expected:
            print(f"Tool Accuracy: {tool_accuracy:.1f}% ({tool_correct}/{tool_expected})")
        if (slot_tp + slot_fp + slot_fn) > 0:
            print(f"Slot Precision: {slot_precision:.3f}")
            print(f"Slot Recall: {slot_recall:.3f}")
            print(f"Slot F1: {slot_f1:.3f}")

    return {
        "total": len(cases),
        "passed": passed_count,
        "accuracy": accuracy,
        "tool_expected": tool_expected,
        "tool_correct": tool_correct,
        "tool_accuracy": tool_accuracy,
        "slot_precision": slot_precision,
        "slot_recall": slot_recall,
        "slot_f1": slot_f1,
        "results": results,
    }

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run dialogue tool-selection evaluation.")
    parser.add_argument("--test-cases", default=str(Path(__file__).parent / "test_cases.json"))
    parser.add_argument("--quiet", action="store_true", help="Print only summary metrics.")
    args = parser.parse_args()

    run_evaluation(args.test_cases, print_results=not args.quiet)
