"""Test case evaluator for dialogue and E2E modes."""

from dataclasses import dataclass, field
from typing import Any

from evaluation.llm.utils.validators import validate_output, ValidationResult
from evaluation.llm.utils.metrics import BenchmarkMetrics, args_match
from evaluation.llm.utils.normalizers import normalize_args, normalize_value
from src.api.calendar.client import CalendarClient
from src.llm.chat import build_system_prompt, chat_stream


@dataclass
class TestCase:
    """A single test case."""

    id: str
    input: str
    expected_tool: str | None = None
    expected_args: dict = field(default_factory=dict)
    expected_args_contains: dict = field(default_factory=dict)
    cleanup_created_event: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "TestCase":
        return cls(
            id=data["id"],
            input=data["input"],
            expected_tool=data.get("expected_tool"),
            expected_args=data.get("expected_args", {}),
            expected_args_contains=data.get("expected_args_contains", {}),
            cleanup_created_event=data.get("cleanup_created_event", True),
        )


@dataclass
class EvalResult:
    """Result of evaluating a test case."""

    id: str
    status: str  # "pass", "fail", "error"
    tool: str | None = None
    args: dict | None = None
    reason: str | None = None


class CaseEvaluator:
    """Evaluates individual test cases."""

    def __init__(self, calendar: CalendarClient | None = None, verbose: bool = True):
        self.calendar = calendar
        self.verbose = verbose

    def evaluate(
        self, case: TestCase, metrics: BenchmarkMetrics, e2e: bool = False
    ) -> EvalResult:
        """Evaluate a single test case."""
        if case.expected_tool:
            metrics.tool_expected += 1

        self._log(f"Case: {case.id}\nInput: {case.input}")

        # Run chat
        messages: list[dict[str, Any]] = [{"role": "system", "content": build_system_prompt()}]
        try:
            for _ in chat_stream(case.input, messages):
                pass
        except Exception as e:
            self._log(f"Error: {e}\n" + "-" * 40)
            return EvalResult(case.id, "error", reason=str(e))

        # Extract tool calls
        calls: list[dict[str, Any]] = []
        outputs: list[str] = []
        for msg in messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                tool_calls = msg.get("tool_calls")
                if isinstance(tool_calls, list):
                    calls.extend(tool_calls)
            if msg.get("role") == "tool":
                outputs.append(str(msg.get("content", "")))

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

        # Check tool selection
        tool_ok = actual_tool == case.expected_tool
        if case.expected_tool:
            if tool_ok:
                metrics.tool_correct += 1
            else:
                result.reason = "wrong_tool"
                self._log(
                    f"Wrong tool: expected {case.expected_tool}, got {actual_tool}"
                )
        elif actual_tool:
            result.reason = "unwanted_tool"

        # Mode-specific evaluation
        if e2e and tool_ok:
            self._evaluate_e2e(case, result, metrics, outputs[-1] if outputs else "")
        elif not e2e and tool_ok:
            self._evaluate_args(case, result, metrics, actual_args)

        self._log_status(result.status)
        return result

    def _evaluate_args(
        self,
        case: TestCase,
        result: EvalResult,
        metrics: BenchmarkMetrics,
        actual: dict,
    ):
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

    def _evaluate_e2e(
        self, case: TestCase, result: EvalResult, metrics: BenchmarkMetrics, output: str
    ):
        validation: ValidationResult = validate_output(
            result.tool or "", output, case.expected_args_contains
        )
        if validation.success:
            result.status = "pass"
            metrics.passed += 1
            metrics.task_success += 1
            if case.cleanup_created_event and validation.event_id and self.calendar:
                try:
                    self.calendar.delete_event(validation.event_id)
                except Exception:
                    pass
        else:
            result.reason = validation.error

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def _log_status(self, status: str):
        if self.verbose:
            print(f"{'PASS' if status == 'pass' else 'FAIL'}\n" + "-" * 40)
