# LLM Benchmark Tool

This tool evaluates Local LLM performance on dialogue understanding and End-to-End (E2E) tasks for the Voice Assistant.

## Prerequisites

1.  **Ollama** must be running (`ollama serve`).
2.  Models must be pulled locally (e.g., `ollama pull qwen2.5:7b-instruct`).
3.  Project dependencies installed via `uv`.

## Quick Mode (Development)

**Recommendation:** If you want to check all models, start with the `--quick` flag first to identify which models are performing well before committing to a full run.

Use the `--quick` flag to run a smaller subset of test cases for faster validation.

```bash
# Quick test on default model
uv run python -m evaluation.llm --quick

# Quick test on all installed default models (Recommended first step)
uv run python -m evaluation.llm --default-models --quick
```

## Usage

Run the benchmark module from the project root:

```bash
# Run on the configured default model (src/config.py)
uv run python -m evaluation.llm

# Run on a specific model
uv run python -m evaluation.llm --model qwen2.5:7b-instruct

# Run on multiple specific models
uv run python -m evaluation.llm --models "qwen2.5:7b-instruct,llama3.1:8b"

# Run on ALL default models (defined in utils/constants.py)
# Note: Skips models not installed locally.
uv run python -m evaluation.llm --default-models

# Save report to a specific file
uv run python -m evaluation.llm --output evaluation/llm/reports/my_benchmark.md
```

### Modes

*   `--mode all` (Default): Runs both Dialogue and E2E tests.
*   `--mode dialogue`: Runs only intent/slot extraction tests.
*   `--mode e2e`: Runs full conversation flow with mocked tools.

## Estimated Runtimes

Estimates based on ~2 seconds per LLM call on Apple Silicon (M-series).

| Run Type | Test Cases | Est. Time (Per Model) | Est. Time (14 Models) |
| :--- | :--- | :--- | :--- |
| **Full Benchmark** | 161 (196 calls) | ~7 minutes | ~1 hr 38 mins |
| **Quick Benchmark** | 23 (27 calls) | ~1.2 minutes | ~17 minutes |

## Default Models

The benchmark suite checks for the following model families. Ensure you have them installed via `ollama list`.

*   **Qwen 2.5 Series** (`qwen2.5:7b-instruct`, `qwen2.5:3b-instruct`...)
*   **Meta Llama 3 Series** (`llama3.1:8b`, `llama3.2:3b`...)
*   **Mistral Series** (`mistral:7b-instruct`, `mistral-nemo:12b`...)
*   **Others** (Gemma 2, Phi 3.5, etc.)

## Directory Structure

*   `json_files/`: Contains `test_cases.json` and `test_cases_e2e.json`.
*   `utils/`: Helper functions for metrics, evaluation, and reporting.
*   `benchmark.py`: Core logic for running tests.
*   `comparison.py`: Logic for iterating over multiple models.