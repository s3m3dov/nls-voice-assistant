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
    definitions.delete_all_calendar_events,
]

TOOL_REGISTRY = {func.__name__: func for func in TOOLS}

TOOL_ANNOUNCEMENTS = {
    "get_weather_forecast": "Calling tool get weather forecast...",
    "get_weather_for_day": "Calling tool get weather for day...",
    "get_weather_for_today": "Calling tool get weather for today...",
    "list_calendar_events": "Calling tool list calendar events...",
    "get_calendar_event": "Calling tool get calendar event...",
    "create_calendar_event": "Calling tool create calendar event...",
    "update_calendar_event": "Calling tool update calendar event...",
    "delete_calendar_event": "Calling tool delete calendar event...",
    "delete_all_calendar_events": "Calling tool delete all calendar events...",
}
