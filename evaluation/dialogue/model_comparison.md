# Dialogue Model Comparison

- Generated: 2026-01-29 11:08:55
- Dialogue test cases: `/Users/nasirsabir/PycharmProjects/nls-voice-assistant/evaluation/dialogue/test_cases.json`
- E2E test cases: `/Users/nasirsabir/PycharmProjects/nls-voice-assistant/evaluation/dialogue/test_cases_e2e.json`

## Models

- `qwen2.5:7b-instruct`
- `llama3.2:3b`
- `qwen2.5:3b`
- `mistral-small3.2:24b`

## Tool Selection (Dialogue)

| Model | Accuracy | Tool Accuracy | Slot F1 | Passed/Total |
| --- | --- | --- | --- | --- |
| qwen2.5:7b-instruct | 100.0% | 100.0% | 0.824 | 15/15 |
| llama3.2:3b | 73.3% | 100.0% | 0.526 | 11/15 |
| qwen2.5:3b | 80.0% | 78.6% | 0.783 | 12/15 |
| mistral-small3.2:24b | 86.7% | 85.7% | 0.960 | 13/15 |

## End-to-End (Tools + Data)

| Model | Overall Accuracy | Tool Accuracy | Task Success | Passed/Total |
| --- | --- | --- | --- | --- |
| qwen2.5:7b-instruct | 100.0% | 100.0% | 100.0% | 10/10 |
| llama3.2:3b | 90.0% | 100.0% | 90.0% | 9/10 |
| qwen2.5:3b | 100.0% | 100.0% | 100.0% | 10/10 |
| mistral-small3.2:24b | 80.0% | 80.0% | 80.0% | 8/10 |

## Model Comparison Report

- qwen2.5:7b-instruct is the strongest overall: perfect tool selection and E2E success, most consistent across both suites.
- qwen2.5:3b matches perfect E2E but is weaker on tool selection (lower accuracy/tool accuracy/slot F1), suggesting it sometimes picks the right tool but slips on arguments.
- mistral-small3.2:24b has the best Slot F1 (0.960), meaning when it calls tools it fills arguments very accurately, but overall tool selection and E2E success are lower than Qwen's 7B instruct.
- llama3.2:3b is the most inconsistent: perfect tool accuracy when it picks a tool, but lower overall accuracy and lower slot F1, indicating more frequent wrong/no tool decisions and weaker argument fill.

Key Differences by Behavior
- Tool choice reliability: qwen2.5:7b-instruct > mistral-small3.2:24b > qwen2.5:3b > llama3.2:3b
- Argument quality (Slot F1): mistral-small3.2:24b > qwen2.5:7b-instruct > qwen2.5:3b > llama3.2:3b
- End-to-end success: qwen2.5:7b-instruct = qwen2.5:3b > llama3.2:3b > mistral-small3.2:24b

Notes:
- Results depend on local Ollama availability and calendar/weather backends.
- Models that do not support tool calls are skipped.
