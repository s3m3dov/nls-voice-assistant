"""Benchmark runner for dialogue and E2E tests."""

import json
from pathlib import Path

from evaluation.llm.utils import BenchmarkMetrics, CaseEvaluator, TestCase
from src.api.calendar.client import CalendarClient
from src.config import settings


class BenchmarkRunner:
    """Runs benchmarks on test cases."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def run(
        self,
        dialogue_path: str | None = None,
        e2e_path: str | None = None,
        mode: str = "all",
    ) -> dict:
        """Run benchmarks based on mode."""
        results = {}
        if mode in ("all", "dialogue") and dialogue_path:
            results["dialogue"] = self.run_dialogue(dialogue_path)
        if mode in ("all", "e2e") and e2e_path:
            results["e2e"] = self.run_e2e(e2e_path)
        return results

    def run_dialogue(self, path: str) -> dict:
        """Run dialogue benchmark."""
        cases = json.loads(Path(path).read_text())
        metrics = BenchmarkMetrics(total=len(cases))
        evaluator = CaseEvaluator(verbose=self.verbose)

        if self.verbose:
            print(f"Running dialogue benchmark ({len(cases)} cases)...\n")

        for data in cases:
            result = evaluator.evaluate(TestCase.from_dict(data), metrics, e2e=False)
            metrics.results.append(
                {
                    "id": result.id,
                    "status": result.status,
                    "actual_tool": result.tool,
                    "failure_reason": result.reason,
                }
            )

        if self.verbose:
            self._print_summary("Dialogue", metrics)
        return metrics.to_dict()

    def run_e2e(self, path: str) -> dict:
        """Run E2E benchmark."""
        cases = json.loads(Path(path).read_text())
        calendar = CalendarClient(settings.api)
        metrics = BenchmarkMetrics(total=len(cases))
        evaluator = CaseEvaluator(calendar=calendar, verbose=self.verbose)

        if self.verbose:
            print(f"Running E2E benchmark ({len(cases)} cases)...\n")

        for data in cases:
            result = evaluator.evaluate(TestCase.from_dict(data), metrics, e2e=True)
            metrics.results.append(
                {
                    "id": result.id,
                    "status": result.status,
                    "actual_tool": result.tool,
                    "failure_reason": result.reason,
                }
            )

        if self.verbose:
            self._print_summary("E2E", metrics, show_task=True)
        return metrics.to_dict()

    def _print_summary(self, name: str, m: BenchmarkMetrics, show_task: bool = False):
        print(f"\n{name} Complete: {m.accuracy:.1f}% ({m.passed}/{m.total})")
        if m.tool_expected:
            print(f"Tool Accuracy: {m.tool_accuracy:.1f}%")
        if show_task and m.tool_expected:
            print(f"Task Success: {m.task_success_rate:.1f}%")
        if m.slot_tp + m.slot_fp + m.slot_fn > 0:
            print(f"Slot F1: {m.slot_f1:.3f}")
