"""Tests for API configuration."""

import pytest

from src.api.config import APISettings


class TestAPISettings:
    """Tests for APISettings Pydantic model."""

    def test_default_values(self):
        """Test that values are set correctly."""
        settings = APISettings(calendar_id="team-ezekiel-calendar-test")

        assert settings.base_url == "https://api.responsible-nlp.net"
        assert settings.calendar_id == "team-ezekiel-calendar-test"
        assert settings.request_timeout == 30

    def test_weather_endpoint_property(self):
        """Test weather_endpoint property returns correct URL."""
        settings = APISettings(calendar_id="team-ezekiel-calendar-test-config")

        assert settings.weather_endpoint == "https://api.responsible-nlp.net/weather.php"

    def test_calendar_endpoint_property(self):
        """Test calendar_endpoint property returns correct URL."""
        settings = APISettings(calendar_id="team-ezekiel-calendar-test-config")
        endpoint = settings.calendar_endpoint
        assert endpoint == "https://api.responsible-nlp.net/calendar.php"

    def test_custom_values(self):
        """Test that custom values can be set."""
        settings = APISettings(
            base_url="https://custom.api.com",
            calendar_id="team-ezekiel-calendar-test-custom",
            request_timeout=60,
        )

        assert settings.base_url == "https://custom.api.com"
        assert settings.calendar_id == "team-ezekiel-calendar-test-custom"
        assert settings.request_timeout == 60
        assert settings.weather_endpoint == "https://custom.api.com/weather.php"

    def test_request_timeout_validation_min(self):
        """Test that request_timeout must be >= 1."""
        with pytest.raises(ValueError):
            APISettings(calendar_id="test", request_timeout=0)

    def test_request_timeout_validation_max(self):
        """Test that request_timeout must be <= 120."""
        with pytest.raises(ValueError):
            APISettings(calendar_id="test", request_timeout=121)

    def test_calendar_id_required(self):
        """Test that calendar_id is required."""
        with pytest.raises(ValueError):
            APISettings()
