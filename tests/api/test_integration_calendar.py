"""Integration tests for real Calendar API endpoints."""

import pytest
import uuid
from datetime import datetime, timedelta

from src.api.config import APISettings
from src.api.calendar.client import CalendarClient
from src.api.calendar.schema import CalendarEventCreateRequest, CalendarEventUpdateRequest, CalendarDateRequest


class TestIntegrationCalendar:
    """Integration tests for Calendar API."""

    @pytest.fixture
    def random_calendar_id(self):
        """Generate a random calendar ID for isolation."""
        return f"test-integration-{uuid.uuid4()}"

    @pytest.fixture
    def settings(self, random_calendar_id):
        """Create real settings with isolated calendar."""
        return APISettings(
            base_url="https://api.responsible-nlp.net",
            calendar_id=random_calendar_id,
            request_timeout=30,
        )

    @pytest.fixture
    def calendar_client(self, settings):
        """Create real calendar client."""
        return CalendarClient(settings)

    def test_crud_lifecycle(self, calendar_client):
        """Test full Create-Read-Update-Delete lifecycle."""
        # 1. Create
        start_time = (datetime.now() + timedelta(days=1)).replace(microsecond=0).isoformat()
        end_time = (datetime.now() + timedelta(days=1, hours=1)).replace(microsecond=0).isoformat()
        
        create_request = CalendarEventCreateRequest(
            title="CRUD Lifecycle Event",
            start_time=start_time,
            end_time=end_time,
            description="Integration test event",
            location="Test Lab"
        )
        created = calendar_client.create_event(create_request)
        assert created is not None
        assert created.id is not None
        event_id = created.id

        try:
            # 2. Read (Get)
            fetched = calendar_client.get_event(event_id)
            assert fetched is not None
            assert fetched.id == event_id
            assert fetched.title == "CRUD Lifecycle Event"

            # 3. Read (List)
            events = calendar_client.list_events()
            assert any(e.id == event_id for e in events)

            # 4. Update
            update_request = CalendarEventUpdateRequest(
                title="Updated CRUD Event",
                description="Updated description"
            )
            updated = calendar_client.update_event(event_id, update_request)
            assert updated is not None
            
            assert updated.title == "Updated CRUD Event"
            assert updated.description == "Updated description"
            # Verify other fields preserved
            assert updated.location == "Test Lab"
            
            # Double check with get
            fetched_updated = calendar_client.get_event(event_id)
            assert fetched_updated.title == "Updated CRUD Event"

        finally:
            # 5. Delete
            calendar_client.delete_event(event_id)
            assert calendar_client.get_event(event_id) is None

    def test_create_minimal_event(self, calendar_client):
        """Test creating an event with only required fields."""
        start_time = (datetime.now() + timedelta(days=2)).replace(microsecond=0).isoformat()
        create_request = CalendarEventCreateRequest(
            title="Minimal Event",
            start_time=start_time
            # end_time, description, location are optional
        )
        created = calendar_client.create_event(create_request)
        assert created is not None
        assert created.title == "Minimal Event"
        
        # Cleanup
        if created.id:
            calendar_client.delete_event(created.id)

    def test_delete_all_events(self, calendar_client):
        """Test deleting all events in the calendar."""
        # Create a few events
        for i in range(3):
            start = (datetime.now() + timedelta(days=i)).isoformat()
            calendar_client.create_event(CalendarEventCreateRequest(
                title=f"Delete All {i}", start_time=start
            ))
        
        events_before = calendar_client.list_events()
        assert len(events_before) >= 3

        # Delete all
        summary = calendar_client.delete_all_events()
        assert summary.deleted >= 3
        
        # Verify empty
        events_after = calendar_client.list_events()
        assert len(events_after) == 0

    def test_delete_events_by_date(self, calendar_client):
        """Test deleting events by date."""
        target_date = datetime.now() + timedelta(days=10)
        date_str = target_date.date().isoformat()
        
        # Create event on date
        start = target_date.replace(hour=10).isoformat()
        event = calendar_client.create_event(CalendarEventCreateRequest(
            title="Date Delete Event", start_time=start
        ))
        
        # Create event on another date
        other_date = target_date + timedelta(days=1)
        start_other = other_date.replace(hour=10).isoformat()
        event_other = calendar_client.create_event(CalendarEventCreateRequest(
            title="Keep Event", start_time=start_other
        ))

        assert event is not None
        assert event_other is not None

        # Delete by target date
        summary = calendar_client.delete_events_by_date(CalendarDateRequest(date=date_str))
        assert event.id in summary.deleted_ids
        assert event_other.id not in summary.deleted_ids

        # Verify
        assert calendar_client.get_event(event.id) is None
        assert calendar_client.get_event(event_other.id) is not None

        # Cleanup
        if event_other.id:
            calendar_client.delete_event(event_other.id)

    def test_error_handling(self, calendar_client):
        """Test handling of non-existent events."""
        # Get non-existent
        assert calendar_client.get_event(999999) is None

        # Update non-existent
        # Our updated client attempts get_event first, so it should return None or fail gracefully
        result = calendar_client.update_event(999999, {"title": "Ghost"})
        assert result is None

        # Delete non-existent
        try:
            calendar_client.delete_event(999999)
        except Exception:
            pass
