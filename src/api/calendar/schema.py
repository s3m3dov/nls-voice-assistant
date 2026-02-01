from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CalendarEventResponse(BaseModel):
    """Calendar event data returned from the API."""

    id: Optional[int] = Field(default=None, description="Event ID (assigned by server)")
    title: str = Field(default="", description="Event title")
    description: str = Field(default="", description="Event description")
    start_time: str = Field(default="", description="Start time in ISO format")
    end_time: str = Field(default="", description="End time in ISO format")
    location: str = Field(default="", description="Event location")

    @property
    def start_datetime(self) -> Optional[datetime]:
        """Parse start_time string to datetime object."""
        if not self.start_time:
            return None
        try:
            return datetime.fromisoformat(self.start_time)
        except ValueError:
            return None

    @property
    def end_datetime(self) -> Optional[datetime]:
        """Parse end_time string to datetime object."""
        if not self.end_time:
            return None
        try:
            return datetime.fromisoformat(self.end_time)
        except ValueError:
            return None


class CalendarEventCreateRequest(BaseModel):
    """Request schema for creating a new calendar event."""

    title: str = Field(min_length=1, description="Event title")
    start_time: str = Field(description="Start time in ISO format (e.g., 2025-11-03T09:00)")
    end_time: str = Field(description="End time in ISO format")
    description: Optional[str] = Field(..., description="Event description")
    location: Optional[str] = Field(..., description="Event location")



class CalendarEventUpdateRequest(BaseModel):
    """Request schema for updating a calendar event (all fields optional)."""

    title: Optional[str] = Field(default=None, min_length=1, description="Event title")
    start_time: Optional[str] = Field(default=None, description="Start time in ISO format (e.g., 2025-11-03T09:00)")
    end_time: Optional[str] = Field(default=None, description="End time in ISO format")
    description: Optional[str] = Field(default=None, description="Event description")
    location: Optional[str] = Field(default=None, description="Event location")

    def to_dict(self) -> dict:
        """Convert to dict excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class CalendarDateRequest(BaseModel):
    """Request schema for operations on a specific date."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")


class CalendarBulkDeleteResponse(BaseModel):
    """Response schema for bulk deletion operations."""

    total_found: int = Field(..., description="Total number of events found to delete")
    deleted: int = Field(..., description="Number of events successfully deleted")
    failed: int = Field(..., description="Number of events that failed to delete")
    deleted_ids: list[int] = Field(default_factory=list, description="IDs of deleted events")
    failed_ids: list[int] = Field(default_factory=list, description="IDs of events that failed to delete")
    target_date: Optional[str] = Field(default=None, description="Target date if deletion was filtered by date")
