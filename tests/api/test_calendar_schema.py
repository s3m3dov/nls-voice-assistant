"""Tests for API schema models."""

import pytest
from pydantic import ValidationError

from src.api.calendar.schema import (
    CalendarEventCreateRequest,
    CalendarEventResponse,
    CalendarEventUpdateRequest,
)


class TestCalendarEventResponse:
    """Tests for CalendarEventResponse model."""

    def test_create_calendar_event_response(self):
        """Test creating a CalendarEventResponse instance."""
        event = CalendarEventResponse(
            id=1,
            title="Meeting",
            description="Team standup",
            start_time="2025-01-15T09:00",
            end_time="2025-01-15T10:00",
            location="Room 1",
        )

        assert event.id == 1
        assert event.title == "Meeting"
        assert event.location == "Room 1"

    def test_calendar_event_response_defaults(self):
        """Test that all fields have sensible defaults."""
        event = CalendarEventResponse()

        assert event.id is None
        assert event.title == ""
        assert event.description == ""
        assert event.start_time == ""
        assert event.end_time == ""
        assert event.location == ""

    def test_start_datetime_property(self):
        """Test start_datetime parsing."""
        event = CalendarEventResponse(start_time="2025-01-15T09:00")

        dt = event.start_datetime
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 9

    def test_start_datetime_empty(self):
        """Test start_datetime with empty string."""
        event = CalendarEventResponse()

        assert event.start_datetime is None

    def test_start_datetime_invalid(self):
        """Test start_datetime with invalid format."""
        event = CalendarEventResponse(start_time="not-a-date")

        assert event.start_datetime is None

    def test_end_datetime_property(self):
        """Test end_datetime parsing."""
        event = CalendarEventResponse(end_time="2025-01-15T10:30")

        dt = event.end_datetime
        assert dt is not None
        assert dt.hour == 10
        assert dt.minute == 30


class TestCalendarEventCreateRequest:
    """Tests for CalendarEventCreateRequest validation model."""

    def test_create_valid_request(self):
        """Test creating a valid request."""
        request = CalendarEventCreateRequest(
            title="Meeting",
            start_time="2025-01-15T09:00",
            end_time="2025-01-15T10:00",
        )

        assert request.title == "Meeting"
        assert request.description == ""
        assert request.location == ""

    def test_title_required(self):
        """Test that title is required."""
        with pytest.raises(ValidationError):
            CalendarEventCreateRequest(
                start_time="2025-01-15T09:00",
                end_time="2025-01-15T10:00",
            )

    def test_title_min_length(self):
        """Test that title must have at least 1 character."""
        with pytest.raises(ValidationError):
            CalendarEventCreateRequest(
                title="",
                start_time="2025-01-15T09:00",
                end_time="2025-01-15T10:00",
            )

    def test_start_time_required(self):
        """Test that start_time is required."""
        with pytest.raises(ValidationError):
            CalendarEventCreateRequest(
                title="Meeting",
                end_time="2025-01-15T10:00",
            )

    def test_end_time_required(self):
        """Test that end_time is required."""
        with pytest.raises(ValidationError):
            CalendarEventCreateRequest(
                title="Meeting",
                start_time="2025-01-15T09:00",
            )


class TestCalendarEventUpdateRequest:
    """Tests for CalendarEventUpdateRequest validation model."""

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        update = CalendarEventUpdateRequest()

        assert update.title is None
        assert update.description is None
        assert update.location is None

    def test_partial_update(self):
        """Test creating a partial update."""
        update = CalendarEventUpdateRequest(title="New Title", location="New Room")

        assert update.title == "New Title"
        assert update.location == "New Room"
        assert update.description is None

    def test_to_dict(self):
        """Test to_dict excludes None values."""
        update = CalendarEventUpdateRequest(title="Updated", location="Room 5")

        result = update.to_dict()

        assert result == {"title": "Updated", "location": "Room 5"}
        assert "description" not in result
        assert "start_time" not in result

    def test_title_min_length_when_provided(self):
        """Test title validation when provided."""
        with pytest.raises(ValidationError):
            CalendarEventUpdateRequest(title="")
