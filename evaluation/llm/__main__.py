#!/usr/bin/env python3
"""CLI for LLM Benchmark Tool."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.llm.comparison import ModelComparison
from evaluation.llm.benchmark import BenchmarkRunner
from evaluation.llm.utils import DEFAULT_MODELS
from src.config import settings


def main():
    base = Path(__file__).parent / "json_files"

    parser = argparse.ArgumentParser(description="LLM Benchmark Tool")
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--model", help="Single model to test")
    grp.add_argument("--models", help="Comma-separated models to compare")
    parser.add_argument(
        "--default-models", action="store_true", help="Use default model list"
    )
    parser.add_argument("--mode", choices=["all", "dialogue", "e2e"], default="all")
    parser.add_argument("--dialogue-tests", default=str(base / "test_cases.json"))
    parser.add_argument("--e2e-tests", default=str(base / "test_cases_e2e.json"))
    parser.add_argument("--quick", action="store_true", help="Use quick test subset")
    parser.add_argument("-o", "--output", help="Save markdown report")
    parser.add_argument("-q", "--quiet", action="store_true")

    args = parser.parse_args()

    dialogue = (
        str(base / "test_cases_quick.json") if args.quick else args.dialogue_tests
    )
    e2e = str(base / "test_cases_e2e_quick.json") if args.quick else args.e2e_tests

    if args.mode == "dialogue":
        e2e = None
    elif args.mode == "e2e":
        dialogue = None

    if args.models or args.default_models or args.output:
        models = (
            DEFAULT_MODELS
            if args.default_models
            else (
                [m.strip() for m in args.models.split(",")]
                if args.models
                else [settings.llm.model]
            )
        )
        quick_suffix = "_quick" if args.quick else ""
        default_filename = f"{args.mode}{quick_suffix}_report.md"
        output = args.output or str(base.parent / "results" / default_filename)
        ModelComparison(models).run(dialogue, e2e, args.mode, output)
    else:
        if args.model:
            settings.llm.model = args.model
        print(f"Model: {settings.llm.model}\n")
        results = BenchmarkRunner(verbose=not args.quiet).run(dialogue, e2e, args.mode)
        if args.quiet:
            if "dialogue" in results:
                d = results["dialogue"]
                print(f"Dialogue: {d['accuracy']:.1f}% | F1: {d['slot_f1']:.3f}")
            if "e2e" in results:
                e = results["e2e"]
                print(
                    f"E2E: {e['accuracy']:.1f}% | Task: {e['task_success_rate']:.1f}%"
                )


if __name__ == "__main__":
    main()
