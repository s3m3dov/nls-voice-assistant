from . import definitions

# List of all available tools for Ollama
TOOLS = [
    definitions.get_weather_forecast,
    definitions.get_weather_for_day,
    definitions.get_weather_for_today,
    definitions.list_calendar_events,
    definitions.get_calendar_event,
    definitions.create_calendar_event,
    definitions.update_calendar_event,
    definitions.delete_calendar_event,
]

TOOL_REGISTRY = {func.__name__: func for func in TOOLS}

TOOL_ANNOUNCEMENTS = {
    "get_weather_forecast": "Checking the weather forecast...",
    "get_weather_for_day": "Checking the forecast for that day...",
    "get_weather_for_today": "Checking today's weather...",
    "list_calendar_events": "Checking your calendar...",
    "get_calendar_event": "Looking up that event...",
    "create_calendar_event": "Scheduling that for you...",
    "update_calendar_event": "Updating your calendar...",
    "delete_calendar_event": "Removing that event...",
}