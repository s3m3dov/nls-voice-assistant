"""Benchmark runner for LLM tool selection tests."""

from evaluation.llm.test_cases import TestCasesManager, TestCase, Category
from evaluation.llm.utils import BenchmarkMetrics, CaseEvaluator


class BenchmarkRunner:
    """Runs benchmarks on test cases."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.manager = TestCasesManager()

    def run(
        self,
        quick: bool = False,
        categories: list[Category] | None = None,
    ) -> dict:
        """Run benchmark.

        Args:
            quick: If True, use one test case per category.
            categories: Optional list of categories to filter by.

        Returns:
            Dictionary with benchmark results.
        """
        cases = self._get_cases(quick, categories)
        metrics = BenchmarkMetrics(total=len(cases))
        evaluator = CaseEvaluator(verbose=self.verbose)

        if self.verbose:
            print(f"Running benchmark ({len(cases)} cases)...\n")

        for case in cases:
            result = evaluator.evaluate(case, metrics)
            metrics.results.append(
                {
                    "id": result.id,
                    "category": case.category.value if case.category else None,
                    "status": result.status,
                    "expected_tool": case.expected_tool,
                    "actual_tool": result.tool,
                    "failure_reason": result.reason,
                }
            )

        if self.verbose:
            self._print_summary(metrics)
        return metrics.to_dict()

    def _get_cases(
        self,
        quick: bool,
        categories: list[Category] | None,
    ) -> list[TestCase]:
        """Get test cases based on options."""
        if categories:
            return self.manager.get_by_category(categories)
        return self.manager.get_quick() if quick else self.manager.get_all()

    def _print_summary(self, m: BenchmarkMetrics):
        """Print benchmark summary."""
        print(f"\nComplete: {m.accuracy:.1f}% ({m.passed}/{m.total})")
        if m.tool_expected:
            print(f"Tool Accuracy: {m.tool_accuracy:.1f}%")
        if m.slot_tp + m.slot_fp + m.slot_fn > 0:
            print(f"Slot F1: {m.slot_f1:.3f}")
