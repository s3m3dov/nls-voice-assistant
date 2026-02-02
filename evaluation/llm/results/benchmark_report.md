# LLM Benchmark Report

- Generated: 2026-02-02 08:17:02

## Models

- `qwen2.5:7b-instruct`
- `qwen3-vl:4b-instruct`

## Results

| Model | Accuracy | Tool Acc | Slot F1 | Pass/Total |
| --- | --- | --- | --- | --- |
| qwen2.5:7b-instruct | 81.9% | 100.0% | 0.652 | 77/94 |
| qwen3-vl:4b-instruct | 85.1% | 103.7% | 0.584 | 80/94 |

## Category Breakdown

| Category | qwen2.5:7b-instruct | qwen3-vl:4b-instruct |
| --- | --- | --- |
| calendar/create | 33% (6/18) | 33% (6/18) |
| calendar/delete | 100% (7/7) | 100% (7/7) |
| calendar/delete_all | 100% (4/4) | 100% (4/4) |
| calendar/delete_for_date | 100% (1/1) | 100% (1/1) |
| calendar/get | 100% (6/6) | 100% (6/6) |
| calendar/get_for_date | 100% (1/1) | 100% (1/1) |
| calendar/list | 71% (5/7) | 100% (7/7) |
| calendar/update | 78% (7/9) | 89% (8/9) |
| general/no_tool | 100% (8/8) | 100% (8/8) |
| weather/day | 100% (13/13) | 100% (13/13) |
| weather/forecast | 90% (9/10) | 90% (9/10) |
| weather/today | 100% (10/10) | 100% (10/10) |

## Failures

### qwen2.5:7b-instruct

- **weather_forecast_new_york**: wrong_args (tool=`get_weather_forecast`)
- **calendar_list_busy**: wrong_tool (tool=`get_calendar_events_for_date`)
- **calendar_list_planned**: wrong_tool (tool=`get_calendar_events_for_date`)
- **calendar_create_lunch**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_doctor**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_call**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_interview**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_presentation**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_gym**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_with_description**: wrong_args (tool=`create_calendar_event`)
- **calendar_vague_meeting**: wrong_args (tool=`create_calendar_event`)
- **calendar_natural_language_time**: wrong_args (tool=`create_calendar_event`)
- **calendar_urgent_reminder**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_recurring_style**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_birthday**: wrong_args (tool=`create_calendar_event`)
- **calendar_update_postpone**: wrong_tool (tool=`get_calendar_event`)
- **calendar_update_push_back**: wrong_tool (tool=`get_calendar_event`)

### qwen3-vl:4b-instruct

- **weather_forecast_new_york**: wrong_args (tool=`get_weather_forecast`)
- **calendar_create_lunch**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_doctor**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_call**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_interview**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_presentation**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_gym**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_with_description**: wrong_args (tool=`create_calendar_event`)
- **calendar_vague_meeting**: wrong_args (tool=`create_calendar_event`)
- **calendar_natural_language_time**: wrong_args (tool=`create_calendar_event`)
- **calendar_urgent_reminder**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_recurring_style**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_birthday**: wrong_args (tool=`create_calendar_event`)
- **calendar_update_push_back**: wrong_tool (tool=`get_calendar_event`)


---

*Results depend on Ollama availability.*