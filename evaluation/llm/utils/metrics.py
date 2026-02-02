"""Metrics and comparison utilities."""

from dataclasses import dataclass, field

from evaluation.llm.utils.normalizers import normalize_value


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Calculate precision, recall, F1 from counts."""
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def args_match(expected: dict, actual: dict, exact: bool = True) -> bool:
    """Check if expected and actual args match."""
    if exact and set(expected.keys()) != set(actual.keys()):
        return False
    return all(
        normalize_value(v) == normalize_value(actual.get(k))
        for k, v in expected.items()
    )


@dataclass
class BenchmarkMetrics:
    """Aggregated metrics from a benchmark run."""

    total: int = 0
    passed: int = 0
    tool_expected: int = 0
    tool_correct: int = 0
    task_success: int = 0
    slot_tp: int = 0
    slot_fp: int = 0
    slot_fn: int = 0
    results: list[dict] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return (self.passed / self.total) * 100 if self.total else 0.0

    @property
    def tool_accuracy(self) -> float:
        return (
            (self.tool_correct / self.tool_expected) * 100
            if self.tool_expected
            else 0.0
        )

    @property
    def task_success_rate(self) -> float:
        return (
            (self.task_success / self.tool_expected) * 100
            if self.tool_expected
            else 0.0
        )

    @property
    def slot_f1(self) -> float:
        _, _, f1 = precision_recall_f1(self.slot_tp, self.slot_fp, self.slot_fn)
        return f1

    def to_dict(self) -> dict:
        p, r, f1 = precision_recall_f1(self.slot_tp, self.slot_fp, self.slot_fn)
        return {
            "total": self.total,
            "passed": self.passed,
            "accuracy": self.accuracy,
            "tool_expected": self.tool_expected,
            "tool_correct": self.tool_correct,
            "tool_accuracy": self.tool_accuracy,
            "task_success": self.task_success,
            "task_success_rate": self.task_success_rate,
            "slot_precision": p,
            "slot_recall": r,
            "slot_f1": f1,
            "results": self.results,
        }
