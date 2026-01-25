"""Adapter that exposes assistant_step for LLM evaluation."""

from __future__ import annotations

from typing import Any

from ollama import chat

from src.config import settings
from src.dialogue.chat import build_system_prompt
from src.dialogue.tools import TOOLS


WEATHER_TOOLS = {
    "get_weather_forecast",
    "get_weather_for_day",
    "get_weather_for_today",
}

CALENDAR_TOOL_INTENTS = {
    "list_calendar_events": "CAL_LIST",
    "get_calendar_event": "CAL_GET",
    "create_calendar_event": "CAL_CREATE",
    "update_calendar_event": "CAL_UPDATE",
    "delete_calendar_event": "CAL_DELETE",
}


def _extract_tool_call(tool_call: Any) -> tuple[str, dict]:
    name = ""
    args = {}
    if hasattr(tool_call, "function"):
        func = tool_call.function
        name = getattr(func, "name", "")
        args = getattr(func, "arguments", {}) or {}
    return name, args


def _build_calendar_api_call(tool_name: str, args: dict) -> tuple[str, str, dict, dict, dict]:
    method = ""
    params = {"calenderid": settings.api.calendar_id}
    body: dict[str, Any] = {}

    if tool_name == "list_calendar_events":
        method = "GET"
    elif tool_name == "get_calendar_event":
        method = "GET"
        if "event_id" in args:
            params["id"] = str(args["event_id"])
    elif tool_name == "create_calendar_event":
        method = "POST"
        for key in ["title", "start_time", "end_time", "description", "location"]:
            if key in args and args[key] not in (None, ""):
                body[key] = args[key]
    elif tool_name == "update_calendar_event":
        method = "PUT"
        if "event_id" in args:
            params["id"] = str(args["event_id"])
        for key in ["title", "start_time", "end_time", "description", "location"]:
            if key in args and args[key] not in (None, ""):
                body[key] = args[key]
    elif tool_name == "delete_calendar_event":
        method = "DELETE"
        if "event_id" in args:
            params["id"] = str(args["event_id"])

    slots = {}
    if "event_id" in args:
        slots["id"] = str(args["event_id"])
    for key in ["title", "start_time", "end_time", "description", "location"]:
        if key in args and args[key] not in (None, ""):
            slots[key] = args[key]

    return CALENDAR_TOOL_INTENTS.get(tool_name, ""), method, slots, params, body


def _build_weather_api_call(tool_name: str, args: dict) -> tuple[str, dict, dict]:
    slots = {}
    body = {}
    if "place" in args and args["place"] not in (None, ""):
        slots["place"] = args["place"]
        body["place"] = args["place"]

    if tool_name == "get_weather_for_day" and "day" in args:
        slots["day"] = args["day"]
    elif tool_name == "get_weather_for_today":
        slots["day"] = "today"

    return slots, {}, body


def assistant_step(history: list[dict], user_text: str) -> dict:
    """Return structured intent/slots/api_call for evaluation."""
    messages = [{"role": "system", "content": build_system_prompt()}]
    for item in history or []:
        role = item.get("role", "user")
        content = item.get("content") or item.get("text") or ""
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_text})

    response = chat(
        model=settings.dialogue.llm_model,
        messages=messages,
        tools=TOOLS,
        stream=False,
    )

    message = response.message
    tool_calls = message.tool_calls or []

    if not tool_calls:
        return {
            "intent": "CLARIFY",
            "slots": {},
            "api_call": {"method": None, "endpoint": None, "params": {}, "body": {}},
            "assistant_reply": message.content or "",
        }

    tool_name, args = _extract_tool_call(tool_calls[0])

    if tool_name in WEATHER_TOOLS:
        slots, params, body = _build_weather_api_call(tool_name, args)
        return {
            "intent": "WEATHER_QUERY",
            "slots": slots,
            "api_call": {
                "method": "POST",
                "endpoint": "weather",
                "params": params,
                "body": body,
            },
            "assistant_reply": message.content or "",
        }

    if tool_name in CALENDAR_TOOL_INTENTS:
        intent, method, slots, params, body = _build_calendar_api_call(tool_name, args)
        return {
            "intent": intent,
            "slots": slots,
            "api_call": {
                "method": method,
                "endpoint": "calendar",
                "params": params,
                "body": body,
            },
            "assistant_reply": message.content or "",
        }

    return {
        "intent": "CLARIFY",
        "slots": {},
        "api_call": {"method": None, "endpoint": None, "params": {}, "body": {}},
        "assistant_reply": message.content or "",
    }
