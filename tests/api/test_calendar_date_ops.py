"""Tests for Calendar API client date operations."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api.calendar.client import CalendarAPIError, CalendarClient
from src.api.calendar.schema import CalendarDateRequest, CalendarEventResponse
from src.api.config import APISettings


class TestCalendarDateOps:
    """Tests for date-specific CalendarClient operations."""

    @pytest.fixture
    def settings(self):
        return APISettings(
            base_url="https://test.api.com",
            calendar_id="test-calendar",
            request_timeout=5,
        )

    @pytest.fixture
    def client(self, settings):
        return CalendarClient(settings)

    @pytest.fixture
    def mixed_events(self):
        return [
            {
                "id": 1,
                "title": "Meeting 1",
                "start_time": "2025-01-15T09:00",
                "end_time": "2025-01-15T10:00",
                "description": "On target date",
                "location": "Room A"
            },
            {
                "id": 2,
                "title": "Meeting 2",
                "start_time": "2025-01-15T14:00",
                "end_time": "2025-01-15T15:00",
                "description": "Also on target date",
                "location": "Room B"
            },
            {
                "id": 3,
                "title": "Meeting 3",
                "start_time": "2025-01-16T09:00",
                "end_time": "2025-01-16T10:00",
                "description": "Next day",
                "location": "Room C"
            }
        ]

    @patch.object(requests.Session, "get")
    def test_get_events_by_date(self, mock_get, client, mixed_events):
        """Test filtering events by date."""
        # Mock list_events response
        mock_response = MagicMock()
        mock_response.json.return_value = mixed_events
        mock_response.text = str(mixed_events)
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        request = CalendarDateRequest(date="2025-01-15")
        results = client.get_events_by_date(request)

        assert len(results) == 2
        assert results[0].id == 1
        assert results[1].id == 2
        
        # Verify filtering out the other date
        ids = [e.id for e in results]
        assert 3 not in ids

    @patch.object(requests.Session, "get")
    def test_get_events_by_date_no_match(self, mock_get, client, mixed_events):
        """Test filtering when no events match."""
        mock_response = MagicMock()
        mock_response.json.return_value = mixed_events
        mock_response.text = str(mixed_events)
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        request = CalendarDateRequest(date="2025-01-20")
        results = client.get_events_by_date(request)

        assert len(results) == 0

    @patch.object(requests.Session, "get")
    def test_get_events_invalid_date_format(self, mock_get, client, mixed_events):
        """Test error handling for invalid date format."""
        # Even if API returns data, the request validation or processing should fail
        # Actually validation happens in Pydantic model creation if we were using types, 
        # but here we pass a string. The client method does the parsing.
        
        mock_response = MagicMock()
        mock_response.json.return_value = mixed_events
        mock_get.return_value = mock_response

        # Pydantic validation might pass strictly string, but client parses it.
        request = CalendarDateRequest(date="invalid-date")
        
        with pytest.raises(CalendarAPIError) as exc:
            client.get_events_by_date(request)
        
        assert "Invalid date format" in str(exc.value)

    @patch.object(requests.Session, "get")
    @patch.object(requests.Session, "delete")
    def test_delete_events_by_date(self, mock_delete, mock_get, client, mixed_events):
        """Test deleting events for a specific date."""
        # Mock list response
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = mixed_events
        mock_get_response.text = str(mixed_events)
        mock_get_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_get_response

        # Mock delete response
        mock_delete_response = MagicMock()
        mock_delete_response.raise_for_status = MagicMock()
        mock_delete.return_value = mock_delete_response

        request = CalendarDateRequest(date="2025-01-15")
        summary = client.delete_events_by_date(request)

        assert summary.total_found == 2
        assert summary.deleted == 2
        assert summary.failed == 0
        assert 1 in summary.deleted_ids
        assert 2 in summary.deleted_ids
        assert 3 not in summary.deleted_ids

        # Verify delete was called only for matching IDs
        assert mock_delete.call_count == 2
        # We can inspect call args to ensure correct URLs if needed, but simple count is good enough for now.
