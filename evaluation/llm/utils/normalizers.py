"""Text and value normalization utilities."""

import json
import re
from datetime import datetime, timedelta
from typing import Any

WEEKDAYS = {
    "mon": "monday",
    "monday": "monday",
    "tue": "tuesday",
    "tues": "tuesday",
    "tuesday": "tuesday",
    "wed": "wednesday",
    "weds": "wednesday",
    "wednesday": "wednesday",
    "thu": "thursday",
    "thur": "thursday",
    "thurs": "thursday",
    "thursday": "thursday",
    "fri": "friday",
    "friday": "friday",
    "sat": "saturday",
    "saturday": "saturday",
    "sun": "sunday",
    "sunday": "sunday",
}


def normalize_text(value: Any) -> str:
    """Normalize text: strip, lowercase, collapse whitespace."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def normalize_weekday(value: Any) -> str:
    """Normalize day reference to canonical weekday name."""
    text = normalize_text(value)
    if not text:
        return ""

    if text == "today":
        return datetime.today().strftime("%A").lower()
    if text == "tomorrow":
        return (datetime.today() + timedelta(days=1)).strftime("%A").lower()

    text = re.sub(r"^(next|this)\s+", "", text)
    if text in WEEKDAYS:
        return WEEKDAYS[text]

    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        try:
            return datetime.fromisoformat(text).strftime("%A").lower()
        except ValueError:
            pass
    return text


def normalize_value(value: Any) -> Any:
    """Normalize a value for comparison."""
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return str(value)


def normalize_args(args: Any) -> dict:
    """Normalize tool arguments to a dict."""
    if args is None:
        return {}
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
            return parsed if isinstance(parsed, dict) else {"_raw": parsed}
        except json.JSONDecodeError:
            return {"_raw": args}
    return {"_raw": args}
