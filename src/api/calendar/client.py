"""Calendar API client for managing calendar events (CRUD operations)."""

from datetime import datetime
from typing import Optional

import requests

from src.api.config import APISettings
from .exception import CalendarAPIError
from .schema import (
    CalendarBulkDeleteResponse,
    CalendarDateRequest,
    CalendarEventCreateRequest,
    CalendarEventResponse,
    CalendarEventUpdateRequest,
)


class CalendarClient:
    """Client for interacting with the Calendar API."""

    def __init__(self, settings: APISettings):
        """
        Initialize the Calendar API client.

        Args:
            settings: API settings with endpoint and calendar_id configuration.
        """
        self.settings = settings
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    @property
    def calendar_id(self) -> str:
        """Get the calendar ID from settings."""
        return self.settings.calendar_id

    def _get_url(self, event_id: Optional[int] = None) -> str:
        """Build the API URL with calendar ID and optional event ID."""
        url = f"{self.settings.calendar_endpoint}?calenderid={self.calendar_id}"
        if event_id is not None:
            url += f"&id={event_id}"
        return url

    def _handle_response(self, response: requests.Response) -> dict | list | None:
        """Handle API response and raise errors if needed."""
        try:
            response.raise_for_status()
            if response.text:
                return response.json()
            return None
        except requests.exceptions.HTTPError as e:
            raise CalendarAPIError(f"HTTP error: {e}") from e

    def list_events(self) -> list[CalendarEventResponse]:
        """
        List all calendar events.

        Returns:
            List of CalendarEventResponse objects.

        Raises:
            CalendarAPIError: If the API request fails.
        """
        try:
            response = self._session.get(
                self._get_url(),
                timeout=self.settings.request_timeout,
            )
            data = self._handle_response(response)
            if data is None:
                return []
            if isinstance(data, list):
                return [CalendarEventResponse.model_validate(event) for event in data]
            return []
        except requests.exceptions.RequestException as e:
            raise CalendarAPIError(f"Request failed: {e}") from e

    def get_event(self, event_id: int) -> Optional[CalendarEventResponse]:
        """
        Get a single calendar event by ID.

        Args:
            event_id: The ID of the event to retrieve.

        Returns:
            CalendarEventResponse object, or None if not found.

        Raises:
            CalendarAPIError: If the API request fails.
        """
        try:
            response = self._session.get(
                self._get_url(event_id),
                timeout=self.settings.request_timeout,
            )
            data = self._handle_response(response)
            if data is None:
                return None
            if isinstance(data, dict):
                return CalendarEventResponse.model_validate(data)
            return None
        except requests.exceptions.RequestException as e:
            raise CalendarAPIError(f"Request failed: {e}") from e

    def create_event(self, event: CalendarEventCreateRequest) -> Optional[CalendarEventResponse]:
        """
        Create a new calendar event.

        Args:
            event: CalendarEventCreateRequest with event details.

        Returns:
            Created CalendarEventResponse with assigned ID, or None if failed.

        Raises:
            CalendarAPIError: If the API request fails.
        """
        try:
            response = self._session.post(
                self._get_url(),
                json=event.model_dump(),
                timeout=self.settings.request_timeout,
            )
            data = self._handle_response(response)
            if data is None:
                return None
            if isinstance(data, dict):
                return CalendarEventResponse.model_validate(data)
            return None
        except requests.exceptions.RequestException as e:
            raise CalendarAPIError(f"Request failed: {e}") from e

    def update_event(
            self, event_id: int, updates: CalendarEventUpdateRequest | dict
    ) -> Optional[CalendarEventResponse]:
        """
        Update an existing calendar event.

        Args:
            event_id: The ID of the event to update.
            updates: CalendarEventUpdateRequest or dict with fields to update.

        Returns:
            Updated CalendarEventResponse, or None if failed.

        Raises:
            CalendarAPIError: If the API request fails.
        """
        if isinstance(updates, CalendarEventUpdateRequest):
            data = updates.to_dict()
        else:
            data = updates

        try:
            response = self._session.put(
                self._get_url(event_id),
                json=data,
                timeout=self.settings.request_timeout,
            )
            result = self._handle_response(response)
            if result is None:
                return None
            if isinstance(result, dict):
                return CalendarEventResponse.model_validate(result)
            return None
        except requests.exceptions.RequestException as e:
            raise CalendarAPIError(f"Request failed: {e}") from e

    def delete_event(self, event_id: int) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: The ID of the event to delete.

        Returns:
            True if deletion succeeded.

        Raises:
            CalendarAPIError: If the API request fails.
        """
        try:
            response = self._session.delete(
                self._get_url(event_id),
                timeout=self.settings.request_timeout,
            )
            self._handle_response(response)
            return True
        except requests.exceptions.RequestException as e:
            raise CalendarAPIError(f"Request failed: {e}") from e

    def delete_all_events(self) -> CalendarBulkDeleteResponse:
        """
        Delete all calendar events by listing and deleting each event.

        Returns:
            CalendarBulkDeleteResponse with deleted and failed event IDs.

        Raises:
            CalendarAPIError: If listing events fails.
        """
        events = self.list_events()
        deleted_ids: list[int] = []
        failed_ids: list[int] = []

        for event in events:
            if event.id is None:
                continue
            try:
                if self.delete_event(event.id):
                    deleted_ids.append(event.id)
                else:
                    failed_ids.append(event.id)
            except CalendarAPIError:
                failed_ids.append(event.id)

        return CalendarBulkDeleteResponse(
            total_found=len(events),
            deleted=len(deleted_ids),
            failed=len(failed_ids),
            deleted_ids=deleted_ids,
            failed_ids=failed_ids,
        )

    def get_events_by_date(self, request: CalendarDateRequest) -> list[CalendarEventResponse]:
        """
        Get events for a specific date.

        Args:
            request: CalendarDateRequest with the target date.

        Returns:
            List of CalendarEventResponse objects on that date.
        """
        all_events = self.list_events()
        target_date_str = request.date

        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise CalendarAPIError(f"Invalid date format: {target_date_str}") from e

        filtered_events = []
        for event in all_events:
            if event.start_datetime and event.start_datetime.date() == target_date:
                filtered_events.append(event)

        return filtered_events

    def delete_events_by_date(self, request: CalendarDateRequest) -> CalendarBulkDeleteResponse:
        """
        Delete all events on a specific date.

        Args:
            request: CalendarDateRequest with the target date.

        Returns:
            CalendarBulkDeleteResponse with deletion summary.
        """
        events_to_delete = self.get_events_by_date(request)
        deleted_ids: list[int] = []
        failed_ids: list[int] = []

        for event in events_to_delete:
            if event.id is None:
                continue
            try:
                if self.delete_event(event.id):
                    deleted_ids.append(event.id)
                else:
                    failed_ids.append(event.id)
            except CalendarAPIError:
                failed_ids.append(event.id)

        return CalendarBulkDeleteResponse(
            total_found=len(events_to_delete),
            deleted=len(deleted_ids),
            failed=len(failed_ids),
            deleted_ids=deleted_ids,
            failed_ids=failed_ids,
            target_date=request.date
        )
