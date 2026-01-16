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

# Map function names to functions for execution
TOOL_REGISTRY = {func.__name__: func for func in TOOLS}
