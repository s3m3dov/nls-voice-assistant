"""Configuration models for API endpoints and settings using Pydantic."""
from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API configuration settings with environment variable support."""

    # Base URL for the NLP API
    base_url: str = Field(
        default="https://api.responsible-nlp.net",
        description="Base URL for the NLP API",
    )

    # Default calendar ID - replace with your team's unique ID
    calendar_id: str = Field(description="Unique calendar ID for your team")

    # Request timeout in seconds
    request_timeout: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Request timeout in seconds",
    )

    @property
    def weather_endpoint(self) -> str:
        """Weather API endpoint URL."""
        return f"{self.base_url}/weather.php"

    @property
    def calendar_endpoint(self) -> str:
        """Calendar API endpoint URL."""
        return f"{self.base_url}/calendar.php"
