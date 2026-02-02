# LLM Benchmark Report

- Generated: 2026-02-02 07:56:16

## Models

- `qwen2.5:1.5b`
- `qwen2.5:1.5b-instruct`
- `qwen2.5:3b`
- `qwen2.5:3b-instruct`
- `qwen2.5:7b`
- `qwen2.5:7b-instruct`
- `qwen3-vl:2b-instruct`
- `qwen3-vl:4b-instruct`
- `qwen3-vl:8b-instruct`
- `llama3.2:1b-instruct-q4_K_M`
- `llama3.2:3b`
- `llama3.1:8b`
- `mistral:7b-instruct`
- `mistral-nemo:12b`
- `granite3-dense:2b`
- `hermes3:8b`
- `command-r7b`

## Results

| Model | Accuracy | Tool Acc | Slot F1 | Pass/Total |
| --- | --- | --- | --- | --- |
| qwen2.5:1.5b | 91.7% | 90.9% | 0.783 | 11/12 |
| qwen2.5:1.5b-instruct | 66.7% | 63.6% | 0.737 | 8/12 |
| qwen2.5:3b | 83.3% | 81.8% | 0.667 | 10/12 |
| qwen2.5:3b-instruct | 91.7% | 90.9% | 0.783 | 11/12 |
| qwen2.5:7b | 100.0% | 100.0% | 0.833 | 12/12 |
| qwen2.5:7b-instruct | 100.0% | 100.0% | 0.833 | 12/12 |
| qwen3-vl:2b-instruct | 75.0% | 72.7% | 0.824 | 9/12 |
| qwen3-vl:4b-instruct | 100.0% | 100.0% | 0.714 | 12/12 |
| qwen3-vl:8b-instruct | 91.7% | 90.9% | 0.818 | 11/12 |
| llama3.2:1b-instruct-q4_K_M | 33.3% | 36.4% | 0.500 | 4/12 |
| llama3.2:3b | 66.7% | 100.0% | 0.609 | 8/12 |
| llama3.1:8b | 83.3% | 90.9% | 0.737 | 10/12 |
| mistral:7b-instruct | 8.3% | 0.0% | 0.000 | 1/12 |
| mistral-nemo:12b | 91.7% | 90.9% | 0.818 | 11/12 |
| granite3-dense:2b | 8.3% | 0.0% | 0.000 | 1/12 |
| hermes3:8b | 75.0% | 72.7% | 1.000 | 9/12 |
| command-r7b | 8.3% | 0.0% | 0.000 | 1/12 |

## Category Breakdown

| Category | qwen2.5:1.5b | qwen2.5:1.5b-instruct | qwen2.5:3b | qwen2.5:3b-instruct | qwen2.5:7b | qwen2.5:7b-instruct | qwen3-vl:2b-instruct | qwen3-vl:4b-instruct | qwen3-vl:8b-instruct | llama3.2:1b-instruct-q4_K_M | llama3.2:3b | llama3.1:8b | mistral:7b-instruct | mistral-nemo:12b | granite3-dense:2b | smollm2:1.7b | hermes3:8b | command-r7b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calendar/create | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) |
| calendar/delete | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) |
| calendar/delete_all | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) |
| calendar/delete_for_date | 100% (1/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) |
| calendar/get | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) |
| calendar/get_for_date | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) |
| calendar/list | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) |
| calendar/update | 0% (0/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) | 0% (0/1) |
| general/no_tool | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) |
| weather/day | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) |
| weather/forecast | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) |
| weather/today | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 100% (1/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) | 0% (0/1) | 100% (1/1) | 0% (0/1) |

## Failures

### qwen2.5:1.5b

- **calendar_update_time**: no_tool_called (tool=`None`)

### qwen2.5:1.5b-instruct

- **calendar_list_basic**: no_tool_called (tool=`None`)
- **calendar_update_time**: no_tool_called (tool=`None`)
- **calendar_list_by_date**: wrong_tool (tool=`list_calendar_events`)
- **calendar_delete_by_date**: wrong_tool (tool=`delete_all_calendar_events`)

### qwen2.5:3b

- **weather_day_friday_frankfurt**: wrong_tool (tool=`get_weather_forecast`)
- **calendar_delete_by_date**: wrong_tool (tool=`delete_all_calendar_events`)

### qwen2.5:3b-instruct

- **calendar_delete_by_date**: wrong_tool (tool=`delete_all_calendar_events`)

### qwen2.5:7b

No failures.

### qwen2.5:7b-instruct

No failures.

### qwen3-vl:2b-instruct

- **calendar_update_time**: wrong_tool (tool=`get_calendar_event`)
- **calendar_list_by_date**: no_tool_called (tool=`None`)
- **calendar_delete_by_date**: wrong_tool (tool=`get_calendar_events_for_date`)

### qwen3-vl:4b-instruct

No failures.

### qwen3-vl:8b-instruct

- **calendar_update_time**: wrong_tool (tool=`get_calendar_event`)

### llama3.2:1b-instruct-q4_K_M

- **weather_day_friday_frankfurt**: wrong_tool (tool=`get_weather_forecast`)
- **calendar_list_basic**: no_tool_called (tool=`None`)
- **calendar_get_event_7**: wrong_args (tool=`get_calendar_event`)
- **calendar_update_time**: no_tool_called (tool=`None`)
- **calendar_delete_5**: no_tool_called (tool=`None`)
- **calendar_delete_all_events**: no_tool_called (tool=`None`)
- **calendar_list_by_date**: no_tool_called (tool=`None`)
- **calendar_delete_by_date**: no_tool_called (tool=`None`)

### llama3.2:3b

- **calendar_get_event_7**: wrong_args (tool=`get_calendar_event`)
- **calendar_update_time**: wrong_args (tool=`update_calendar_event`)
- **calendar_delete_5**: wrong_args (tool=`delete_calendar_event`)
- **general_no_tool_greeting**: unwanted_tool (tool=`list_calendar_events`)

### llama3.1:8b

- **weather_day_friday_frankfurt**: wrong_tool (tool=`get_weather_forecast`)
- **calendar_update_time**: wrong_args (tool=`update_calendar_event`)

### mistral:7b-instruct

- **weather_forecast_marburg**: no_tool_called (tool=`None`)
- **weather_day_friday_frankfurt**: no_tool_called (tool=`None`)
- **weather_today_berlin**: no_tool_called (tool=`None`)
- **calendar_list_basic**: no_tool_called (tool=`None`)
- **calendar_get_event_7**: no_tool_called (tool=`None`)
- **calendar_create_dentist**: no_tool_called (tool=`None`)
- **calendar_update_time**: no_tool_called (tool=`None`)
- **calendar_delete_5**: no_tool_called (tool=`None`)
- **calendar_delete_all_events**: no_tool_called (tool=`None`)
- **calendar_list_by_date**: no_tool_called (tool=`None`)
- **calendar_delete_by_date**: no_tool_called (tool=`None`)

### mistral-nemo:12b

- **calendar_delete_by_date**: no_tool_called (tool=`None`)

### granite3-dense:2b

- **weather_forecast_marburg**: no_tool_called (tool=`None`)
- **weather_day_friday_frankfurt**: no_tool_called (tool=`None`)
- **weather_today_berlin**: no_tool_called (tool=`None`)
- **calendar_list_basic**: no_tool_called (tool=`None`)
- **calendar_get_event_7**: no_tool_called (tool=`None`)
- **calendar_create_dentist**: no_tool_called (tool=`None`)
- **calendar_update_time**: no_tool_called (tool=`None`)
- **calendar_delete_5**: no_tool_called (tool=`None`)
- **calendar_delete_all_events**: no_tool_called (tool=`None`)
- **calendar_list_by_date**: no_tool_called (tool=`None`)
- **calendar_delete_by_date**: no_tool_called (tool=`None`)

### hermes3:8b

- **calendar_create_dentist**: no_tool_called (tool=`None`)
- **calendar_update_time**: no_tool_called (tool=`None`)
- **calendar_delete_5**: no_tool_called (tool=`None`)

### command-r7b

- **weather_forecast_marburg**: no_tool_called (tool=`None`)
- **weather_day_friday_frankfurt**: no_tool_called (tool=`None`)
- **weather_today_berlin**: no_tool_called (tool=`None`)
- **calendar_list_basic**: no_tool_called (tool=`None`)
- **calendar_get_event_7**: no_tool_called (tool=`None`)
- **calendar_create_dentist**: no_tool_called (tool=`None`)
- **calendar_update_time**: no_tool_called (tool=`None`)
- **calendar_delete_5**: no_tool_called (tool=`None`)
- **calendar_delete_all_events**: no_tool_called (tool=`None`)
- **calendar_list_by_date**: no_tool_called (tool=`None`)
- **calendar_delete_by_date**: no_tool_called (tool=`None`)

## Skipped

- `gemma2:2b`: registry.ollama.ai/library/gemma2:2b does not support tools (status code: 400)
- `gemma2:9b`: registry.ollama.ai/library/gemma2:9b does not support tools (status code: 400)
- `phi3.5`: registry.ollama.ai/library/phi3.5:latest does not support tools (status code: 400)
- `aya:8b`: registry.ollama.ai/library/aya:8b does not support tools (status code: 400)
- `falcon3:1b`: registry.ollama.ai/library/falcon3:1b does not support tools (status code: 400)
- `falcon3:7b`: registry.ollama.ai/library/falcon3:7b does not support tools (status code: 400)

---

*Results depend on Ollama availability.*