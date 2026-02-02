# LLM Benchmark Report

- Generated: 2026-02-02 08:27:35

## Models

- `qwen3:4b-instruct`

## Results

| Model | Accuracy | Tool Acc | Slot F1 | Pass/Total |
| --- | --- | --- | --- | --- |
| qwen3:4b-instruct | 84.0% | 100.0% | 0.595 | 79/94 |

## Category Breakdown

| Category | qwen3:4b-instruct |
| --- | --- |
| calendar/create | 33% (6/18) |
| calendar/delete | 100% (7/7) |
| calendar/delete_all | 100% (4/4) |
| calendar/delete_for_date | 100% (1/1) |
| calendar/get | 100% (6/6) |
| calendar/get_for_date | 100% (1/1) |
| calendar/list | 100% (7/7) |
| calendar/update | 89% (8/9) |
| general/no_tool | 100% (8/8) |
| weather/day | 100% (13/13) |
| weather/forecast | 90% (9/10) |
| weather/today | 90% (9/10) |

## Failures

### qwen3:4b-instruct

- **weather_forecast_new_york**: wrong_args (tool=`get_weather_forecast`)
- **weather_specific_hour_today**: wrong_tool (tool=`get_weather_for_day`)
- **calendar_create_lunch**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_doctor**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_call**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_interview**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_presentation**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_gym**: wrong_args (tool=`create_calendar_event`)
- **calendar_create_with_description**: wrong_args (tool=`create_calendar_event`)
- **calendar_vague_meeting**: wrong_args (tool=`create_calendar_event`)
- **calendar_natural_language_time**: wrong_args (tool=`create_calendar_event`)
- **calendar_urgent_reminder**: no_tool_called (tool=`None`)
- **calendar_create_recurring_style**: no_tool_called (tool=`None`)
- **calendar_create_birthday**: wrong_args (tool=`create_calendar_event`)
- **calendar_update_push_back**: no_tool_called (tool=`None`)


---

*Results depend on Ollama availability.*