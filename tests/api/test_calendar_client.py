"""Tests for Calendar API client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api.calendar.client import CalendarAPIError, CalendarClient
from src.api.calendar.schema import (
    CalendarEventCreateRequest,
    CalendarEventResponse,
    CalendarEventUpdateRequest,
)
from src.api.config import APISettings


class TestCalendarClient:
    """Tests for CalendarClient class."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return APISettings(
            base_url="https://test.api.com",
            calendar_id="test-calendar",
            request_timeout=5,
        )

    @pytest.fixture
    def client(self, settings):
        """Create test client."""
        return CalendarClient(settings)

    @pytest.fixture
    def sample_event_data(self):
        """Sample event data from API."""
        return {
            "id": 1,
            "title": "Team Meeting",
            "description": "Weekly standup",
            "start_time": "2025-01-15T09:00",
            "end_time": "2025-01-15T10:00",
            "location": "Room 1",
        }

    def test_init_with_settings(self, settings, client):
        """Test client initialization with settings."""
        assert client.settings.base_url == "https://test.api.com"
        assert client.calendar_id == "test-calendar"

    def test_get_url(self, client):
        """Test URL generation with calendar ID."""
        url = client._get_url()
        assert url == "https://test.api.com/calendar.php?calenderid=test-calendar"

    def test_get_url_with_event_id(self, client):
        """Test URL generation with event ID."""
        url = client._get_url(event_id=42)
        assert url == "https://test.api.com/calendar.php?calenderid=test-calendar&id=42"

    @patch.object(requests.Session, "get")
    def test_list_events_success(self, mock_get, client, sample_event_data):
        """Test listing all events."""
        mock_response = MagicMock()
        mock_response.json.return_value = [sample_event_data]
        mock_response.text = "[{}]"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = client.list_events()

        assert len(result) == 1
        assert isinstance(result[0], CalendarEventResponse)
        assert result[0].id == 1
        assert result[0].title == "Team Meeting"

    @patch.object(requests.Session, "get")
    def test_list_events_empty(self, mock_get, client):
        """Test listing events when none exist."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.text = "[]"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = client.list_events()

        assert result == []

    @patch.object(requests.Session, "get")
    def test_get_event_success(self, mock_get, client, sample_event_data):
        """Test getting a single event."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_event_data
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = client.get_event(1)

        assert result is not None
        assert result.id == 1
        assert result.title == "Team Meeting"

    @patch.object(requests.Session, "get")
    def test_get_event_not_found(self, mock_get, client):
        """Test getting a non-existent event."""
        mock_response = MagicMock()
        mock_response.json.return_value = None
        mock_response.text = ""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = client.get_event(999)

        assert result is None

    @patch.object(requests.Session, "post")
    def test_create_event(self, mock_post, client, sample_event_data):
        """Test creating an event."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_event_data
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        request = CalendarEventCreateRequest(
            title="Team Meeting",
            start_time="2025-01-15T09:00",
            end_time="2025-01-15T10:00",
        )
        result = client.create_event(request)

        assert result is not None
        assert result.id == 1

    @patch.object(requests.Session, "post")
    def test_create_event_simple(self, mock_post, client, sample_event_data):
        """Test creating an event with simple parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_event_data
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        request = CalendarEventCreateRequest(
            title="Team Meeting",
            start_time="2025-01-15T09:00",
            end_time="2025-01-15T10:00",
            description="Weekly standup",
            location="Room 1",
        )
        result = client.create_event(request)

        assert result is not None
        assert result.id == 1

    @patch.object(requests.Session, "put")
    def test_update_event_with_dict(self, mock_put, client, sample_event_data):
        """Test updating an event with dict."""
        updated_data = {**sample_event_data, "title": "Updated Meeting"}
        mock_response = MagicMock()
        mock_response.json.return_value = updated_data
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_response

        result = client.update_event(1, {"title": "Updated Meeting"})

        assert result is not None
        assert result.title == "Updated Meeting"

    @patch.object(requests.Session, "put")
    def test_update_event_with_request(self, mock_put, client, sample_event_data):
        """Test updating an event with CalendarEventUpdateRequest."""
        updated_data = {**sample_event_data, "location": "Room 5"}
        mock_response = MagicMock()
        mock_response.json.return_value = updated_data
        mock_response.text = "{}"
        mock_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_response

        updates = CalendarEventUpdateRequest(location="Room 5")
        result = client.update_event(1, updates)

        assert result is not None
        assert result.location == "Room 5"

    @patch.object(requests.Session, "delete")
    def test_delete_event(self, mock_delete, client):
        """Test deleting an event."""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.raise_for_status = MagicMock()
        mock_delete.return_value = mock_response

        result = client.delete_event(1)

        assert result is True

    @patch.object(requests.Session, "get")
    def test_http_error_handling(self, mock_get, client):
        """Test HTTP error handling."""
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

        with pytest.raises(CalendarAPIError) as exc_info:
            client.list_events()

        assert "Request failed" in str(exc_info.value)

    @patch.object(requests.Session, "get")
    def test_connection_error_handling(self, mock_get, client):
        """Test connection error handling."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(CalendarAPIError) as exc_info:
            client.list_events()

        assert "Request failed" in str(exc_info.value)
