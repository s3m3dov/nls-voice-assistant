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
    "get_weather_forecast": "Calling tool named get weather forecast...",
    "get_weather_for_day": "Calling tool named get weather for day...",
    "get_weather_for_today": "Calling tool named get weather for today...",
    "list_calendar_events": "Calling tool named list calendar events...",
    "get_calendar_event": "Calling tool named get calendar event...",
    "create_calendar_event": "Calling tool named create calendar event...",
    "update_calendar_event": "Calling tool named update calendar event...",
    "delete_calendar_event": "Calling tool named delete calendar event...",
    "delete_all_calendar_events": "Calling tool named d§elete all calendar events...",
}
