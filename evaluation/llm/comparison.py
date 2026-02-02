"""Model comparison functionality."""

from ollama import chat

from evaluation.llm.benchmark import BenchmarkRunner
from evaluation.llm.test_cases import Category
from evaluation.llm.utils import ReportGenerator
from src.config import settings
from src.llm.tools import TOOLS


class ModelComparison:
    """Compares multiple models on benchmarks."""

    def __init__(self, models: list[str] | None = None):
        self.models = models or [settings.llm.model]
        self.results: dict = {}
        self.skipped: dict = {}

    def run(
        self,
        quick: bool = False,
        categories: list[Category] | None = None,
        output_path: str | None = None,
        quiet: bool = False,
    ) -> tuple[dict, dict]:
        """Run comparison across all models.

        Args:
            quick: If True, use one test case per category.
            categories: Optional list of categories to filter by.
            output_path: Path to save markdown report.
            quiet: If True, suppress verbose output.

        Returns:
            Tuple of (results dict, skipped dict).
        """
        for model in self.models:
            self._run_model(model, quick, categories, quiet)

        if output_path:
            ReportGenerator(
                models=self.models,
                results=self.results,
                skipped=self.skipped,
            ).save(output_path)
            print(f"\nReport: {output_path}")

        return self.results, self.skipped

    def _run_model(
        self,
        model: str,
        quick: bool,
        categories: list[Category] | None,
        quiet: bool = False,
    ):
        """Run benchmark for a single model."""
        print(f"\n{'=' * 60}\nModel: {model}\n{'=' * 60}")
        settings.llm.model = model

        # Check if model is available
        try:
            chat(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                tools=TOOLS,
                stream=False,
            )
        except Exception as e:
            print(f"Skipping: {e}")
            self.skipped[model] = str(e)
            return

        runner = BenchmarkRunner(verbose=not quiet)
        self.results[model] = runner.run(quick=quick, categories=categories)

        r = self.results[model]
        print(
            f"Accuracy: {r['accuracy']:.1f}% | "
            f"Tool: {r['tool_accuracy']:.1f}% | "
            f"F1: {r['slot_f1']:.3f}"
        )
