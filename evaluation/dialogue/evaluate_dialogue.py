#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.dialogue.chat import chat_stream, build_system_prompt
from src.dialogue.tools import TOOLS, TOOL_REGISTRY

def load_test_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r') as f:
        return json.load(f)

def run_evaluation(test_cases_path: str):
    cases = load_test_cases(test_cases_path)
    results = []
    
    print(f"Running evaluation on {len(cases)} test cases...\n")
    
    passed_count = 0
    
    for case in cases:
        case_id = case["id"]
        user_input = case["input"]
        expected_tool = case.get("expected_tool")
        expected_args = case.get("expected_args")
        expected_args_contains = case.get("expected_args_contains")
        
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
            print(f"❌ Error during execution: {e}")
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
                print(f"❌ Expected tool '{expected_tool}', but no tool was called.")
        else:
            # For simplicity, check the first tool call
            first_call = tool_calls_found[0]
            actual_tool = first_call["function"]["name"]
            actual_args = first_call["function"]["arguments"]
            
            if expected_tool:
                if actual_tool == expected_tool:
                    # Check arguments
                    args_match = True
                    if expected_args:
                        if actual_args != expected_args:
                            args_match = False
                            print(f"❌ Tool match, but args mismatch.\n   Expected: {expected_args}\n   Actual:   {actual_args}")
                    
                    if expected_args_contains:
                        for k, v in expected_args_contains.items():
                            if actual_args.get(k) != v:
                                args_match = False
                                print(f"❌ Tool match, but arg '{k}' mismatch.\n   Expected: {v}\n   Actual:   {actual_args.get(k)}")
                    
                    if args_match:
                        success = True
                else:
                    print(f"❌ Wrong tool called. Expected '{expected_tool}', got '{actual_tool}'")
            else:
                print(f"❌ Expected no tool, but got '{actual_tool}'")

        if success:
            print("✅ PASS")
            passed_count += 1
        else:
            print("❌ FAIL")
        
        print("-" * 40)
        results.append({
            "id": case_id,
            "status": "pass" if success else "fail",
            "actual_tool": actual_tool,
            "actual_args": actual_args
        })

    accuracy = (passed_count / len(cases)) * 100
    print(f"\nEvaluation Complete.")
    print(f"Accuracy: {accuracy:.1f}% ({passed_count}/{len(cases)})")

if __name__ == "__main__":
    test_file = Path(__file__).parent / "test_cases.json"
    run_evaluation(str(test_file))
