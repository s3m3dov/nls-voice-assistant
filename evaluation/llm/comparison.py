"""Model comparison functionality."""

from ollama import chat

from evaluation.llm.benchmark import BenchmarkRunner
from evaluation.llm.utils import ReportGenerator
from src.config import settings
from src.llm.tools import TOOLS


class ModelComparison:
    """Compares multiple models on benchmarks."""

    def __init__(self, models: list[str] | None = None):
        self.models = models or [settings.llm.model]
        self.dialogue_results: dict = {}
        self.e2e_results: dict = {}
        self.skipped: dict = {}

    def run(
        self,
        dialogue_path: str | None = None,
        e2e_path: str | None = None,
        mode: str = "all",
        output_path: str | None = None,
    ) -> tuple[dict, dict, dict]:
        """Run comparison across all models."""
        for model in self.models:
            self._run_model(model, dialogue_path, e2e_path, mode)

        if output_path:
            ReportGenerator(
                self.models,
                self.dialogue_results,
                self.e2e_results,
                self.skipped,
                dialogue_path,
                e2e_path,
            ).save(output_path)
            print(f"\nReport: {output_path}")

        return self.dialogue_results, self.e2e_results, self.skipped

    def _run_model(
        self, model: str, dialogue_path: str | None, e2e_path: str | None, mode: str
    ):
        print(f"\n{'=' * 60}\nModel: {model}\n{'=' * 60}")
        settings.llm.model = model

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

        runner = BenchmarkRunner(verbose=False)

        if mode in ("all", "dialogue") and dialogue_path:
            self.dialogue_results[model] = runner.run_dialogue(dialogue_path)
            d = self.dialogue_results[model]
            print(
                f"Dialogue: {d['accuracy']:.1f}% | Tool: {d['tool_accuracy']:.1f}% | F1: {d['slot_f1']:.3f}"
            )

        if mode in ("all", "e2e") and e2e_path:
            self.e2e_results[model] = runner.run_e2e(e2e_path)
            e2e_res = self.e2e_results[model]
            print(
                f"E2E: {e2e_res['accuracy']:.1f}% | Tool: {e2e_res['tool_accuracy']:.1f}% | Task: {e2e_res['task_success_rate']:.1f}%"
            )
