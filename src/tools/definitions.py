from typing import Optional

from src.api.calendar.client import CalendarClient
from src.api.calendar.schema import CalendarEventCreateRequest, CalendarEventUpdateRequest
from src.api.weather.client import WeatherClient
from src.config import settings

_weather_client = WeatherClient(settings.api)
_calendar_client = CalendarClient(settings.api)


def get_weather_forecast(place: str) -> str:
    """Get the 7-day weather forecast for a location.

    Args:
        place: City or location name (e.g., 'Marburg', 'Frankfurt', 'Berlin')

    Returns:
        JSON string with forecast data including temperature and conditions for each day.
    """
    result = _weather_client.get_forecast(place)
    return result.model_dump_json()


def get_weather_for_day(place: str, day: str) -> str:
    """Get weather forecast for a specific day of the week.

    Args:
        place: City or location name (e.g., 'Marburg', 'Frankfurt')
        day: Day of the week (e.g., 'monday', 'tuesday', 'friday')

    Returns:
        JSON string with temperature and weather conditions, or error message if day not found.
    """
    result = _weather_client.get_weather_for_day(place, day)
    if result is None:
        return f"No weather data found for {day} in {place}."
    return result.model_dump_json()


def get_weather_for_today(place: str) -> str:
    """Get today's weather forecast."""
    result = _weather_client.get_weather_for_today(place)
    if result is None:
        return f"No weather data found for today in {place}."
    return result.model_dump_json()


def list_calendar_events() -> str:
    """List all calendar events/appointments.

    Returns:
        JSON array of all calendar events with their details.
    """
    events = _calendar_client.list_events()
    return "[" + ", ".join(e.model_dump_json() for e in events) + "]"


def get_calendar_event(event_id: int) -> str:
    """Get a specific calendar event by its ID.

    Args:
        event_id: The unique identifier of the event.

    Returns:
        JSON string with event details, or error message if not found.
    """
    event = _calendar_client.get_event(event_id)
    if event is None:
        return f"No event found with ID {event_id}."
    return event.model_dump_json()


def create_calendar_event(
        title: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
) -> str:
    """Create a new calendar event/appointment.

    Args:
        title: Title or name of the event (e.g., 'Team Meeting', 'Doctor Appointment')
        start_time: Start time in ISO format (e.g., '2025-01-20T14:00')
        end_time: End time in ISO format (e.g., '2025-01-20T15:00')
        description: Optional description or notes for the event.
        location: Optional location where the event takes place.

    Returns:
        JSON string with the created event including its assigned ID.
    """
    request = CalendarEventCreateRequest(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
    )
    event = _calendar_client.create_event(request)
    if event is None:
        return "Failed to create event."
    return event.model_dump_json()


def update_calendar_event(
        event_id: int,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
) -> str:
    """Update an existing calendar event.

    Args:
        event_id: The unique identifier of the event to update.
        title: New title for the event (optional).
        start_time: New start time in ISO format (optional).
        end_time: New end time in ISO format (optional).
        description: New description (optional).
        location: New location (optional).

    Returns:
        JSON string with the updated event details.
    """
    request = CalendarEventUpdateRequest(
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
    )
    event = _calendar_client.update_event(event_id, request)
    if event is None:
        return f"Failed to update event {event_id}."
    return event.model_dump_json()


def delete_calendar_event(event_id: int) -> str:
    """Delete a calendar event.

    Args:
        event_id: The unique identifier of the event to delete.

    Returns:
        Confirmation message indicating success or failure.
    """
    success = _calendar_client.delete_event(event_id)
    if success:
        return f"Successfully deleted event {event_id}."
    return f"Failed to delete event {event_id}."
