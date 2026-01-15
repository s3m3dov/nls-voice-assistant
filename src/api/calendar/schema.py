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

    title: str = Field(..., min_length=1, description="Event title")
    description: str = Field(default="", description="Event description")
    start_time: str = Field(..., description="Start time in ISO format (e.g., 2025-11-03T09:00)")
    end_time: str = Field(..., description="End time in ISO format")
    location: str = Field(default="", description="Event location")


class CalendarEventUpdateRequest(BaseModel):
    """Request schema for updating a calendar event (all fields optional)."""

    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
