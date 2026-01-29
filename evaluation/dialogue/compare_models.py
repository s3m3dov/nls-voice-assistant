#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from ollama import chat

from src.config import settings
from src.dialogue.tools import TOOLS
from evaluate_dialogue import run_evaluation as run_dialogue_eval
from evaluate_e2e import run_evaluation as run_e2e_eval


DEFAULT_MODELS = [
    "qwen2.5:7b-instruct",
    "llama3.2:3b",
    "qwen2.5:3b",
    "mistral-small3.2:24b",
]


def _format_pct(value: float) -> str:
    return f"{value:.1f}%"


def _write_markdown(
    output_path: Path,
    models: List[str],
    dialogue_results: Dict[str, Dict[str, Any]],
    e2e_results: Dict[str, Dict[str, Any]],
    unsupported_models: Dict[str, str],
    dialogue_cases: Path,
    e2e_cases: Path,
) -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Dialogue Model Comparison",
        "",
        f"- Generated: {generated_at}",
        f"- Dialogue test cases: `{dialogue_cases}`",
        f"- E2E test cases: `{e2e_cases}`",
        "",
        "## Models",
        "",
    ]
    lines.extend([f"- `{model}`" for model in models])
    lines.append("")

    lines.extend([
        "## Tool Selection (Dialogue)",
        "",
        "| Model | Accuracy | Tool Accuracy | Slot F1 | Passed/Total |",
        "| --- | --- | --- | --- | --- |",
    ])
    for model in models:
        if model in unsupported_models:
            continue
        metrics = dialogue_results[model]
        lines.append(
            "| {model} | {accuracy} | {tool_accuracy} | {slot_f1} | {passed}/{total} |".format(
                model=model,
                accuracy=_format_pct(metrics["accuracy"]),
                tool_accuracy=_format_pct(metrics["tool_accuracy"]),
                slot_f1=f"{metrics['slot_f1']:.3f}",
                passed=metrics["passed"],
                total=metrics["total"],
            )
        )
    lines.append("")

    lines.extend([
        "## End-to-End (Tools + Data)",
        "",
        "| Model | Overall Accuracy | Tool Accuracy | Task Success | Passed/Total |",
        "| --- | --- | --- | --- | --- |",
    ])
    for model in models:
        if model in unsupported_models:
            continue
        metrics = e2e_results[model]
        lines.append(
            "| {model} | {accuracy} | {tool_accuracy} | {task_success} | {passed}/{total} |".format(
                model=model,
                accuracy=_format_pct(metrics["accuracy"]),
                tool_accuracy=_format_pct(metrics["tool_accuracy"]),
                task_success=_format_pct(metrics["task_success_rate"]),
                passed=metrics["passed"],
                total=metrics["total"],
            )
        )
    lines.append("")
    if unsupported_models:
        lines.append("## Skipped Models")
        lines.append("")
        for model, reason in unsupported_models.items():
            lines.append(f"- `{model}`: {reason}")
        lines.append("")
    lines.append("Notes:")
    lines.append("- Results depend on local Ollama availability and calendar/weather backends.")
    lines.append("- Models that do not support tool calls are skipped.")
    lines.append("")

    output_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare dialogue models on evaluation suites.")
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="Comma-separated Ollama model tags.",
    )
    parser.add_argument(
        "--dialogue-tests",
        default=str(Path(__file__).parent / "test_cases.json"),
    )
    parser.add_argument(
        "--e2e-tests",
        default=str(Path(__file__).parent / "test_cases_e2e.json"),
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "model_comparison.md"),
    )
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    dialogue_cases = Path(args.dialogue_tests)
    e2e_cases = Path(args.e2e_tests)
    output_path = Path(args.output)

    dialogue_results: Dict[str, Dict[str, Any]] = {}
    e2e_results: Dict[str, Dict[str, Any]] = {}
    unsupported_models: Dict[str, str] = {}

    for model in models:
        settings.dialogue.llm_model = model
        try:
            chat(
                model=model,
                messages=[{"role": "user", "content": "ping"}],
                tools=TOOLS,
                stream=False,
            )
        except Exception as exc:
            unsupported_models[model] = f"tool calls not supported ({exc})"
            continue
        settings.dialogue.llm_model = model
        dialogue_results[model] = run_dialogue_eval(str(dialogue_cases), print_results=False)
        e2e_results[model] = run_e2e_eval(str(e2e_cases), print_results=False)

    _write_markdown(
        output_path,
        models,
        dialogue_results,
        e2e_results,
        unsupported_models,
        dialogue_cases,
        e2e_cases,
    )
    print(f"Wrote model comparison to {output_path}")


if __name__ == "__main__":
    main()
