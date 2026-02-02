# LLM Benchmark Tool

Evaluates Local LLM performance on tool selection (dialogue understanding) for the Voice Assistant.

## Prerequisites

1. **Ollama** must be running (`ollama serve`).
2. Models must be pulled locally (e.g., `ollama pull qwen2.5:7b-instruct`).
3. Project dependencies installed via `uv`.

## Quick Start

```bash
# Show test case summary
uv run python -m evaluation.llm --summary

# Quick test on default model (1 case per category = 12 tests)
uv run python -m evaluation.llm --quick

# Quick test on all default models (recommended first step)
uv run python -m evaluation.llm --default-models --quick
```

## Usage

```bash
# Run full benchmark on configured default model
uv run python -m evaluation.llm

# Run on a specific model
uv run python -m evaluation.llm --model qwen2.5:7b-instruct

# Run on multiple models
uv run python -m evaluation.llm --models "qwen2.5:7b-instruct,llama3.1:8b"

# Run on ALL default models (skips models not installed locally)
uv run python -m evaluation.llm --default-models

# Run specific categories only
uv run python -m evaluation.llm --categories WEATHER_FORECAST,CALENDAR_CREATE

# Save report to a file
uv run python -m evaluation.llm --default-models -o results/report.md
```

## Test Categories

| Category | Tool | Cases |
|:---------|:-----|------:|
| `WEATHER_FORECAST` | `get_weather_forecast` | 10 |
| `WEATHER_DAY` | `get_weather_for_day` | 13 |
| `WEATHER_TODAY` | `get_weather_for_today` | 10 |
| `CALENDAR_LIST` | `list_calendar_events` | 7 |
| `CALENDAR_GET` | `get_calendar_event` | 6 |
| `CALENDAR_CREATE` | `create_calendar_event` | 18 |
| `CALENDAR_UPDATE` | `update_calendar_event` | 9 |
| `CALENDAR_DELETE` | `delete_calendar_event` | 7 |
| `CALENDAR_DELETE_ALL` | `delete_all_calendar_events` | 4 |
| `CALENDAR_GET_FOR_DATE` | `get_calendar_events_for_date` | 1 |
| `CALENDAR_DELETE_FOR_DATE` | `delete_calendar_events_for_date` | 1 |
| `NO_TOOL` | `null` (no tool expected) | 8 |

**Total: 94 cases** | **Quick mode: 12 cases** (1 per category)

## Estimated Runtimes

Based on ~2 seconds per LLM call on Apple Silicon (M-series).

| Run Type | Test Cases | Est. Time (Per Model) | Est. Time (14 Models) |
|:---------|:-----------|:----------------------|:----------------------|
| **Full Benchmark** | 94 | ~3 minutes | ~42 minutes |
| **Quick Benchmark** | 12 | ~24 seconds | ~5.5 minutes |

## Default Models

The benchmark checks for these model families. Ensure they are installed via `ollama list`.

- **Qwen 2.5 Series** (`qwen2.5:7b-instruct`, `qwen2.5:3b-instruct`...)
- **Meta Llama 3 Series** (`llama3.1:8b`, `llama3.2:3b`...)
- **Mistral Series** (`mistral:7b-instruct`, `mistral-nemo:12b`...)
- **Others** (Gemma 2, Phi 3.5, etc.)

## Directory Structure

```
evaluation/llm/
├── __main__.py          # CLI entry point
├── benchmark.py         # Core benchmark runner
├── comparison.py        # Multi-model comparison
├── test_cases/          # Categorized test cases
│   ├── __init__.py      # TestCasesManager, Category enum
│   └── dialogue/
│       ├── weather/     # Weather tool tests
│       ├── calendar/    # Calendar tool tests
│       └── general/     # No-tool cases
├── utils/               # Helpers (metrics, evaluation, reporting)
└── results/             # Generated reports
```

## CLI Options

| Option | Description |
|:-------|:------------|
| `--model MODEL` | Test a single model |
| `--models MODELS` | Comma-separated models to compare |
| `--default-models` | Use all default models |
| `--quick` | Run quick subset (1 per category) |
| `--categories CATS` | Comma-separated categories to test |
| `-o, --output FILE` | Save markdown report |
| `-q, --quiet` | Minimal output |
| `--summary` | Show test case counts |
