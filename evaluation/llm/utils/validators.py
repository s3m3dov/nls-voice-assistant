"""Response validators for tool outputs using Pydantic."""

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from evaluation.llm.utils.normalizers import normalize_value


class WeatherForecastResponse(BaseModel):
    place: str
    forecast: list[dict]


class WeatherDayResponse(BaseModel):
    day: str | None = None
    temperature: float | int | str
    weather: str


class CalendarEventResponse(BaseModel):
    id: int | None = None
    title: str | None = None


@dataclass
class ValidationResult:
    success: bool
    error: str = ""
    event_id: int | None = None


def validate_output(tool_name: str, output: str, expected: dict) -> ValidationResult:
    """Validate tool output against expected schema."""
    if tool_name == "delete_calendar_event":
        if "Successfully deleted event" not in output:
            return ValidationResult(False, f"Delete failed: {output}")
        exp_id = expected.get("event_id")
        if exp_id and str(exp_id) not in output:
            return ValidationResult(False, f"Wrong event deleted: expected {exp_id}")
        return ValidationResult(True)

    try:
        data = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return ValidationResult(False, f"Invalid JSON from {tool_name}")

    validators = {
        "get_weather_forecast": _validate_weather_forecast,
        "get_weather_for_day": _validate_weather_day,
        "get_weather_for_today": _validate_weather_day,
        "list_calendar_events": _validate_calendar_list,
        "create_calendar_event": _validate_calendar_event,
        "update_calendar_event": _validate_calendar_event,
    }

    validator = validators.get(tool_name)
    return validator(data, expected) if validator else ValidationResult(True)


def _validate_weather_forecast(data: dict, expected: dict) -> ValidationResult:
    try:
        resp = WeatherForecastResponse.model_validate(data)
        exp_place = expected.get("place")
        if exp_place and normalize_value(resp.place) != normalize_value(exp_place):
            return ValidationResult(
                False, f"Place mismatch: {exp_place} vs {resp.place}"
            )
        return ValidationResult(True)
    except ValidationError as e:
        return ValidationResult(False, f"Validation: {e.errors()[0]['msg']}")


def _validate_weather_day(data: dict, expected: dict) -> ValidationResult:
    try:
        resp = WeatherDayResponse.model_validate(data)
        exp_day = expected.get("day")
        if (
            exp_day
            and resp.day
            and normalize_value(resp.day) != normalize_value(exp_day)
        ):
            return ValidationResult(False, f"Day mismatch: {exp_day} vs {resp.day}")
        return ValidationResult(True)
    except ValidationError as e:
        return ValidationResult(False, f"Validation: {e.errors()[0]['msg']}")


def _validate_calendar_list(data: Any, expected: dict) -> ValidationResult:
    if not isinstance(data, list):
        return ValidationResult(False, "Expected list for calendar events")
    return ValidationResult(True)


def _validate_calendar_event(data: dict, expected: dict) -> ValidationResult:
    try:
        resp = CalendarEventResponse.model_validate(data)
        for k, v in expected.items():
            if k in data and normalize_value(v) != normalize_value(data[k]):
                return ValidationResult(False, f"Field mismatch: {k}")
        return ValidationResult(True, event_id=resp.id)
    except ValidationError as e:
        return ValidationResult(False, f"Validation: {e.errors()[0]['msg']}")
