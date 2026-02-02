#!/usr/bin/env python3
"""CLI for LLM Benchmark Tool."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.llm.comparison import ModelComparison
from evaluation.llm.test_cases import Category, TestCasesManager
from evaluation.llm.utils import DEFAULT_MODELS
from src.config import settings


def parse_categories(value: str) -> list[Category]:
    """Parse comma-separated category names."""
    categories = []
    for name in value.split(","):
        name = name.strip().upper()
        try:
            categories.append(Category[name])
        except KeyError:
            print(f"Unknown category: {name}")
            print(f"Available: {[c.name for c in Category]}")
            sys.exit(1)
    return categories


def main():
    parser = argparse.ArgumentParser(description="LLM Benchmark Tool")

    # Model selection
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--model", help="Single model to test")
    grp.add_argument("--models", help="Comma-separated models to compare")
    parser.add_argument(
        "--default-models", action="store_true", help="Use default model list"
    )

    # Test configuration
    parser.add_argument(
        "--quick", action="store_true", help="Use quick test subset (1 per category)"
    )
    parser.add_argument("--categories", help="Comma-separated categories to test")

    # Output
    parser.add_argument("-o", "--output", help="Save markdown report")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("--summary", action="store_true", help="Show test case summary")

    args = parser.parse_args()

    # Show summary
    if args.summary:
        manager = TestCasesManager()
        print("Test Case Summary:\n")
        total = 0
        for cat_path, count in manager.summary().items():
            print(f"  {cat_path}: {count} cases")
            total += count
        print(f"\nTotal: {total} cases")
        print(f"Quick mode: {len(manager.get_quick())} cases")
        return

    # Parse categories
    categories = parse_categories(args.categories) if args.categories else None

    # Determine models to test
    if args.default_models:
        models = DEFAULT_MODELS
    elif args.models:
        models = [m.strip() for m in args.models.split(",")]
    elif args.model:
        models = [args.model]
    else:
        models = [settings.llm.model]

    # Determine output path
    suffix = "_quick" if args.quick else ""
    default_filename = f"benchmark{suffix}_report.md"
    output_path = args.output or str(
        Path(__file__).parent / "results" / default_filename
    )

    # Run comparison (works for single or multiple models)
    ModelComparison(models).run(
        quick=args.quick,
        categories=categories,
        output_path=output_path,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
