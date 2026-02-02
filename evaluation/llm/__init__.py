"""
LLM Benchmark Package.

Usage:
    from evaluation.llm import BenchmarkRunner, ModelComparison

    runner = BenchmarkRunner()
    results = runner.run_dialogue("test_cases.json")

    comparison = ModelComparison(models=["qwen2.5:7b", "mistral:7b"])
    comparison.run(dialogue_path="test_cases.json", output_path="report.md")
"""

from evaluation.llm.benchmark import BenchmarkRunner
from evaluation.llm.comparison import ModelComparison
from evaluation.llm.utils import (
    BenchmarkMetrics,
    CaseEvaluator,
    TestCase,
    EvalResult,
    ReportGenerator,
    ValidationResult,
    validate_output,
    DEFAULT_MODELS,
    normalize_text,
    normalize_weekday,
    normalize_value,
    normalize_args,
)

__all__ = [
    "BenchmarkRunner",
    "ModelComparison",
    "BenchmarkMetrics",
    "CaseEvaluator",
    "TestCase",
    "EvalResult",
    "ReportGenerator",
    "ValidationResult",
    "validate_output",
    "DEFAULT_MODELS",
    "normalize_text",
    "normalize_weekday",
    "normalize_value",
    "normalize_args",
]
