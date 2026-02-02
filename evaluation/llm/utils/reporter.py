"""Report generator for benchmark results."""

from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Generates markdown benchmark reports."""

    def __init__(
        self,
        models: list[str],
        results: dict,
        skipped: dict,
    ):
        self.models = models
        self.results = results
        self.skipped = skipped

    def save(self, path: str):
        """Save report to file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(self._generate())

    def _generate(self) -> str:
        """Generate the report content."""
        parts = [
            self._header(),
            self._results_table(),
            self._category_breakdown(),
            self._failures(),
            self._skipped(),
        ]
        return (
            "\n".join(filter(None, parts))
            + "\n\n---\n\n*Results depend on Ollama availability.*"
        )

    def _header(self) -> str:
        """Generate report header."""
        lines = [
            "# LLM Benchmark Report\n",
            f"- Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
        ]
        active = [m for m in self.models if m not in self.skipped]
        if active:
            lines.extend(["\n## Models\n"] + [f"- `{m}`" for m in active])
        return "\n".join(lines)

    def _results_table(self) -> str:
        """Generate results table."""
        if not self.results:
            return ""

        headers = ["Accuracy", "Tool Acc", "Slot F1", "Pass/Total"]
        lines = [
            "\n## Results\n",
            "| Model | " + " | ".join(headers) + " |",
            "| --- | " + " | ".join(["---"] * len(headers)) + " |",
        ]

        for m in self.models:
            if m not in self.skipped and m in self.results:
                r = self.results[m]
                lines.append(
                    f"| {m} | {r['accuracy']:.1f}% | {r['tool_accuracy']:.1f}% | "
                    f"{r['slot_f1']:.3f} | {r['passed']}/{r['total']} |"
                )
        return "\n".join(lines)

    def _category_breakdown(self) -> str:
        """Generate category breakdown table."""
        if not self.results:
            return ""

        # Collect all categories across all models
        categories: set[str] = set()
        for m in self.models:
            if m in self.skipped or m not in self.results:
                continue
            for r in self.results[m].get("results", []):
                if cat := r.get("category"):
                    categories.add(cat)

        if not categories:
            return ""

        sorted_cats = sorted(categories)
        active_models = [
            m for m in self.models if m not in self.skipped and m in self.results
        ]

        lines = [
            "\n## Category Breakdown\n",
            "| Category | " + " | ".join(active_models) + " |",
            "| --- | " + " | ".join(["---"] * len(active_models)) + " |",
        ]

        for cat in sorted_cats:
            row = [cat]
            for m in active_models:
                # Calculate stats for this category and model
                cat_results = [
                    r
                    for r in self.results[m].get("results", [])
                    if r.get("category") == cat
                ]
                if cat_results:
                    passed = sum(1 for r in cat_results if r.get("status") == "pass")
                    total = len(cat_results)
                    pct = (passed / total * 100) if total else 0
                    row.append(f"{pct:.0f}% ({passed}/{total})")
                else:
                    row.append("-")
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    def _failures(self) -> str:
        """Generate failures section."""
        lines = ["\n## Failures\n"]
        for m in self.models:
            if m in self.skipped:
                continue
            failures = [
                r
                for r in self.results.get(m, {}).get("results", [])
                if r.get("status") == "fail"
            ]
            lines.append(f"### {m}\n")
            if failures:
                for f in failures:
                    lines.append(
                        f"- **{f['id']}**: {f.get('failure_reason', 'unknown')} "
                        f"(tool=`{f.get('actual_tool')}`)"
                    )
            else:
                lines.append("No failures.")
            lines.append("")
        return "\n".join(lines)

    def _skipped(self) -> str:
        """Generate skipped models section."""
        if not self.skipped:
            return ""
        return "## Skipped\n\n" + "\n".join(
            f"- `{m}`: {r}" for m, r in self.skipped.items()
        )
