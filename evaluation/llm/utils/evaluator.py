"""Test case evaluator for tool selection tests."""

from dataclasses import dataclass
from typing import Any

from evaluation.llm.test_cases import TestCase
from evaluation.llm.utils.metrics import BenchmarkMetrics, args_match
from evaluation.llm.utils.normalizers import normalize_args, normalize_value
from src.llm.chat import build_system_prompt, chat_stream


@dataclass
class EvalResult:
    """Result of evaluating a test case."""

    id: str
    status: str  # "pass", "fail", "error"
    tool: str | None = None
    args: dict | None = None
    reason: str | None = None


class CaseEvaluator:
    """Evaluates individual test cases for tool selection."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def evaluate(self, case: TestCase, metrics: BenchmarkMetrics) -> EvalResult:
        """Evaluate a single test case."""
        if case.expected_tool:
            metrics.tool_expected += 1

        self._log(f"Case: {case.id}\nInput: {case.input}")

        # Run chat
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": build_system_prompt()}
        ]
        try:
            for _ in chat_stream(case.input, messages):
                pass
        except Exception as e:
            self._log(f"Error: {e}\n" + "-" * 40)
            return EvalResult(case.id, "error", reason=str(e))

        # Extract tool calls
        calls: list[dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                tool_calls = msg.get("tool_calls")
                if isinstance(tool_calls, list):
                    calls.extend(tool_calls)

        # No tool called
        if not calls:
            if not case.expected_tool:
                metrics.passed += 1
                self._log_status("pass")
                return EvalResult(case.id, "pass")
            self._log(f"Expected {case.expected_tool}, got none")
            self._log_status("fail")
            return EvalResult(case.id, "fail", reason="no_tool_called")

        # Extract first call
        first = calls[0]["function"]
        actual_tool, actual_args = first["name"], normalize_args(first["arguments"])
        result = EvalResult(case.id, "fail", tool=actual_tool, args=actual_args)

        # Check tool selection (including expected_tool_one_of)
        tool_ok = self._check_tool(case, actual_tool)
        if case.expected_tool or case.expected_tool_one_of:
            if tool_ok:
                metrics.tool_correct += 1
            else:
                result.reason = "wrong_tool"
                expected = case.expected_tool or case.expected_tool_one_of
                self._log(f"Wrong tool: expected {expected}, got {actual_tool}")
        elif actual_tool:
            result.reason = "unwanted_tool"

        # Evaluate args if tool is correct
        if tool_ok:
            self._evaluate_args(case, result, metrics, actual_args)

        self._log_status(result.status)
        return result

    def _check_tool(self, case: TestCase, actual_tool: str) -> bool:
        """Check if the actual tool matches expected."""
        if case.expected_tool:
            return actual_tool == case.expected_tool
        if case.expected_tool_one_of:
            return actual_tool in case.expected_tool_one_of
        return False

    def _evaluate_args(
        self,
        case: TestCase,
        result: EvalResult,
        metrics: BenchmarkMetrics,
        actual: dict,
    ):
        """Evaluate argument matching."""
        args_ok = True
        if case.expected_args:
            if not args_match(case.expected_args, actual, exact=True):
                args_ok = False
                result.reason = "wrong_args"
        if case.expected_args_contains:
            if not args_match(case.expected_args_contains, actual, exact=False):
                args_ok = False
                result.reason = "wrong_args"
        if args_ok:
            result.status = "pass"
            metrics.passed += 1

        expected = {**case.expected_args, **case.expected_args_contains}
        if expected:
            gold = {(k, normalize_value(v)) for k, v in expected.items()}
            pred = {(k, normalize_value(v)) for k, v in actual.items()}
            metrics.slot_tp += len(gold & pred)
            metrics.slot_fp += len(pred - gold)
            metrics.slot_fn += len(gold - pred)

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def _log_status(self, status: str):
        if self.verbose:
            print(f"{'PASS' if status == 'pass' else 'FAIL'}\n" + "-" * 40)
