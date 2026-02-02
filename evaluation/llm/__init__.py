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
from evaluation.llm.utils import DEFAULT_MODELS, BenchmarkMetrics

__all__ = [
    "BenchmarkRunner",
    "ModelComparison",
    "BenchmarkMetrics",
    "DEFAULT_MODELS",
]
