"""Report generator for benchmark results."""

from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Generates markdown benchmark reports."""

    def __init__(
        self,
        models: list[str],
        dialogue: dict,
        e2e: dict,
        skipped: dict,
        dialogue_path: str | None = None,
        e2e_path: str | None = None,
    ):
        self.models, self.dialogue, self.e2e, self.skipped = (
            models,
            dialogue,
            e2e,
            skipped,
        )
        self.dialogue_path, self.e2e_path = dialogue_path, e2e_path

    def save(self, path: str):
        Path(path).write_text(self._generate())

    def _generate(self) -> str:
        parts = [
            self._header(),
            self._table(
                self.dialogue,
                "Tool Selection (Dialogue)",
                ["Accuracy", "Tool Acc", "Slot F1", "Pass/Total"],
                lambda d: f"{d['accuracy']:.1f}% | {d['tool_accuracy']:.1f}% | {d['slot_f1']:.3f} | {d['passed']}/{d['total']}",
            ),
            self._table(
                self.e2e,
                "End-to-End",
                ["Accuracy", "Tool Acc", "Task Success", "Pass/Total"],
                lambda e: f"{e['accuracy']:.1f}% | {e['tool_accuracy']:.1f}% | {e['task_success_rate']:.1f}% | {e['passed']}/{e['total']}",
            ),
            self._failures(),
            self._skipped(),
        ]
        return (
            "\n".join(filter(None, parts))
            + "\n\n---\n\n*Results depend on Ollama and backend availability.*"
        )

    def _header(self) -> str:
        lines = [
            f"# LLM Benchmark Report\n",
            f"- Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
        ]
        if self.dialogue_path:
            lines.append(f"- Dialogue tests: `{self.dialogue_path}`")
        if self.e2e_path:
            lines.append(f"- E2E tests: `{self.e2e_path}`")
        active = [m for m in self.models if m not in self.skipped]
        if active:
            lines.extend(["\n## Models\n"] + [f"- `{m}`" for m in active])
        return "\n".join(lines)

    def _table(self, data: dict, title: str, headers: list, row_fn) -> str:
        if not data:
            return ""
        lines = [
            f"\n## {title}\n",
            "| Model | " + " | ".join(headers) + " |",
            "| --- | " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for m in self.models:
            if m not in self.skipped and m in data:
                lines.append(f"| {m} | {row_fn(data[m])} |")
        return "\n".join(lines)

    def _failures(self) -> str:
        lines = ["\n## Failures\n"]
        for m in self.models:
            if m in self.skipped:
                continue
            failures = [
                r
                for src in [self.dialogue.get(m, {}), self.e2e.get(m, {})]
                for r in src.get("results", [])
                if r.get("status") == "fail"
            ]
            lines.append(f"### {m}\n")
            if failures:
                for f in failures:
                    lines.append(
                        f"- **{f['id']}**: {f.get('failure_reason', 'unknown')} (tool=`{f.get('actual_tool')}`)"
                    )
            else:
                lines.append("No failures.")
            lines.append("")
        return "\n".join(lines)

    def _skipped(self) -> str:
        if not self.skipped:
            return ""
        return "## Skipped\n\n" + "\n".join(
            f"- `{m}`: {r}" for m, r in self.skipped.items()
        )
