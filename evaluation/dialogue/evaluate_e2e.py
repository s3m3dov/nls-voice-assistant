#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.dialogue.chat import chat_stream, build_system_prompt
from src.api.calendar.client import CalendarClient
from src.config import settings


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


def _parse_json_safe(text: str) -> Tuple[bool, Any]:
    try:
        return True, json.loads(text)
    except Exception:
        return False, None


def _matches_expected_contains(expected_subset: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, List[str]]:
    mismatches = []
    for key, expected_value in expected_subset.items():
        if _normalize_value(expected_value) != _normalize_value(actual.get(key)):
            mismatches.append(key)
    return (len(mismatches) == 0), mismatches


def load_test_cases(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        return json.load(f)


def _validate_weather_forecast(output_text: str, expected_args: Dict[str, Any]) -> Tuple[bool, str]:
    ok, data = _parse_json_safe(output_text)
    if not ok or not isinstance(data, dict):
        return False, "weather forecast response is not valid JSON"
    place = data.get("place")
    forecast = data.get("forecast")
    if not place or not isinstance(forecast, list):
        return False, "weather forecast response missing place/forecast"
    expected_place = expected_args.get("place")
    if expected_place and _normalize_value(place) != _normalize_value(expected_place):
        return False, f"place mismatch: expected {expected_place}, got {place}"
    return True, ""


def _validate_weather_day(output_text: str, expected_args: Dict[str, Any]) -> Tuple[bool, str]:
    ok, data = _parse_json_safe(output_text)
    if not ok or not isinstance(data, dict):
        return False, "weather day response is not valid JSON"
    if "temperature" not in data or "weather" not in data:
        return False, "weather day response missing temperature/weather"
    expected_day = expected_args.get("day")
    if expected_day:
        actual_day = data.get("day")
        if _normalize_value(actual_day) != _normalize_value(expected_day):
            return False, f"day mismatch: expected {expected_day}, got {actual_day}"
    return True, ""


def _validate_weather_today(output_text: str) -> Tuple[bool, str]:
    ok, data = _parse_json_safe(output_text)
    if not ok or not isinstance(data, dict):
        return False, "weather today response is not valid JSON"
    if "temperature" not in data or "weather" not in data:
        return False, "weather today response missing temperature/weather"
    return True, ""


def _validate_calendar_list(output_text: str) -> Tuple[bool, str]:
    ok, data = _parse_json_safe(output_text)
    if not ok or not isinstance(data, list):
        return False, "calendar list response is not a JSON list"
    return True, ""


def _validate_calendar_event(output_text: str, expected_args: Dict[str, Any]) -> Tuple[bool, str, int | None]:
    ok, data = _parse_json_safe(output_text)
    if not ok or not isinstance(data, dict):
        return False, "calendar event response is not valid JSON", None
    event_id = data.get("id")
    expected_subset = {}
    if expected_args:
        expected_subset.update(expected_args)
    if expected_subset:
        matches, mismatches = _matches_expected_contains(expected_subset, data)
        if not matches:
            return False, f"calendar event mismatch for fields: {', '.join(mismatches)}", event_id
    return True, "", event_id


def _validate_calendar_delete(output_text: str, expected_event_id: int | None) -> Tuple[bool, str]:
    if not isinstance(output_text, str):
        return False, "calendar delete response is not a string"
    if "Successfully deleted event" not in output_text:
        return False, f"calendar delete failed: {output_text}"
    if expected_event_id is not None and str(expected_event_id) not in output_text:
        return False, f"deleted event id mismatch: expected {expected_event_id}, got {output_text}"
    return True, ""


def run_evaluation(test_cases_path: str, *, print_results: bool = True) -> Dict[str, Any]:
    cases = load_test_cases(test_cases_path)
    calendar_client = CalendarClient(settings.api)
    results = []

    if print_results:
        print(f"Running end-to-end evaluation on {len(cases)} test cases...\n")

    passed_count = 0
    tool_expected = 0
    tool_correct = 0
    task_success = 0

    for case in cases:
        case_id = case["id"]
        user_input = case["input"]
        expected_tool = case.get("expected_tool")
        expected_args_contains = case.get("expected_args_contains", {})
        cleanup_created_event = case.get("cleanup_created_event", True)

        if expected_tool:
            tool_expected += 1

        if print_results:
            print(f"Test Case: {case_id}")
            print(f"Input: {user_input}")

        messages = [{"role": "system", "content": build_system_prompt()}]
        response_text = ""
        try:
            for chunk in chat_stream(user_input, messages):
                response_text += chunk
        except Exception as e:
            if print_results:
                print(f"Error during execution: {e}")
            results.append({"id": case_id, "status": "error", "error": str(e)})
            if print_results:
                print("-" * 40)
            continue

        tool_calls_found = []
        tool_outputs = []
        for msg in messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                for tc in msg["tool_calls"]:
                    tool_calls_found.append(tc)
            if msg.get("role") == "tool":
                tool_outputs.append(msg.get("content", ""))

        success = False
        actual_tool = None
        actual_args = None
        last_tool_output = tool_outputs[-1] if tool_outputs else ""

        if not tool_calls_found:
            if expected_tool is None:
                success = True
            else:
                if print_results:
                    print(f"Expected tool '{expected_tool}', but no tool was called.")
        else:
            first_call = tool_calls_found[0]
            actual_tool = first_call["function"]["name"]
            actual_args = _normalize_args(first_call["function"]["arguments"])

            if expected_tool:
                if actual_tool == expected_tool:
                    tool_correct += 1
                else:
                    if print_results:
                        print(f"Wrong tool called. Expected '{expected_tool}', got '{actual_tool}'")

        # E2E validation only if tool matches
        if expected_tool and actual_tool == expected_tool:
            e2e_ok = False
            e2e_error = ""
            created_event_id = None

            if expected_tool == "get_weather_forecast":
                e2e_ok, e2e_error = _validate_weather_forecast(last_tool_output, expected_args_contains)
            elif expected_tool == "get_weather_for_day":
                e2e_ok, e2e_error = _validate_weather_day(last_tool_output, expected_args_contains)
            elif expected_tool == "get_weather_for_today":
                e2e_ok, e2e_error = _validate_weather_today(last_tool_output)
            elif expected_tool == "list_calendar_events":
                e2e_ok, e2e_error = _validate_calendar_list(last_tool_output)
            elif expected_tool == "create_calendar_event":
                e2e_ok, e2e_error, created_event_id = _validate_calendar_event(
                    last_tool_output, expected_args_contains
                )
                if e2e_ok and cleanup_created_event and created_event_id is not None:
                    try:
                        calendar_client.delete_event(int(created_event_id))
                    except Exception:
                        pass
            elif expected_tool == "update_calendar_event":
                e2e_ok, e2e_error, _ = _validate_calendar_event(last_tool_output, expected_args_contains)
            elif expected_tool == "delete_calendar_event":
                expected_id = None
                if "event_id" in expected_args_contains:
                    expected_id = expected_args_contains.get("event_id")
                e2e_ok, e2e_error = _validate_calendar_delete(last_tool_output, expected_id)

            if e2e_ok:
                success = True
                task_success += 1
            else:
                if print_results:
                    print(f"E2E validation failed: {e2e_error}")

        if success:
            if print_results:
                print("PASS")
            passed_count += 1
        else:
            if print_results:
                print("FAIL")

        results.append({
            "id": case_id,
            "status": "pass" if success else "fail",
            "actual_tool": actual_tool,
            "actual_args": actual_args,
        })

        if print_results:
            print("-" * 40)

    accuracy = (passed_count / len(cases)) * 100 if cases else 0.0
    tool_accuracy = (tool_correct / tool_expected) * 100 if tool_expected else 0.0
    task_success_rate = (task_success / tool_expected) * 100 if tool_expected else 0.0

    if print_results:
        print("\nEvaluation Complete.")
        print(f"Overall Accuracy: {accuracy:.1f}% ({passed_count}/{len(cases)})")
        if tool_expected:
            print(f"Tool Accuracy: {tool_accuracy:.1f}% ({tool_correct}/{tool_expected})")
            print(f"Task Success: {task_success_rate:.1f}% ({task_success}/{tool_expected})")

    return {
        "total": len(cases),
        "passed": passed_count,
        "accuracy": accuracy,
        "tool_expected": tool_expected,
        "tool_correct": tool_correct,
        "tool_accuracy": tool_accuracy,
        "task_success": task_success,
        "task_success_rate": task_success_rate,
        "results": results,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run end-to-end dialogue evaluation.")
    parser.add_argument("--test-cases", default=str(Path(__file__).parent / "test_cases_e2e.json"))
    parser.add_argument("--quiet", action="store_true", help="Print only summary metrics.")
    args = parser.parse_args()

    run_evaluation(args.test_cases, print_results=not args.quiet)
