"""Tests for Weather API client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api.config import APISettings
from src.api.weather.client import WeatherClient
from src.api.weather.exception import WeatherAPIError
from src.api.weather.schema import WeatherResponse


class TestWeatherClient:
    """Tests for WeatherClient class."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return APISettings(
            base_url="https://test.api.com",
            calendar_id="test",
            request_timeout=5,
        )

    @pytest.fixture
    def client(self, settings):
        """Create test client."""
        return WeatherClient(settings)

    @pytest.fixture
    def sample_response(self):
        """Sample API response data."""
        return {
            "place": "Marburg",
            "forecast": [
                {"day": "thursday", "temperature": {"min": 7, "max": 15}, "weather": "few clouds"},
                {"day": "friday", "temperature": {"min": 6, "max": 14}, "weather": "rain"},
                {"day": "saturday", "temperature": {"min": 5, "max": 11}, "weather": "clear sky"},
            ],
        }

    def test_init_with_settings(self, settings, client):
        """Test client initialization with settings."""
        assert client.settings.base_url == "https://test.api.com"
        assert client.settings.request_timeout == 5

    @patch.object(requests.Session, "post")
    def test_get_forecast_success(self, mock_post, client, sample_response):
        """Test successful weather forecast retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.get_forecast("Marburg")

        assert isinstance(result, WeatherResponse)
        assert result.place == "Marburg"
        assert len(result.forecast) == 3
        assert result.forecast[0].day == "thursday"

    @patch.object(requests.Session, "post")
    def test_get_forecast_http_error(self, mock_post, client):
        """Test HTTP error handling."""
        mock_post.side_effect = requests.exceptions.HTTPError("500 Server Error")

        with pytest.raises(WeatherAPIError) as exc_info:
            client.get_forecast("Marburg")

        assert "HTTP error" in str(exc_info.value)

    @patch.object(requests.Session, "post")
    def test_get_forecast_connection_error(self, mock_post, client):
        """Test connection error handling."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with pytest.raises(WeatherAPIError) as exc_info:
            client.get_forecast("Marburg")

        assert "Connection error" in str(exc_info.value)

    @patch.object(requests.Session, "post")
    def test_get_forecast_timeout(self, mock_post, client):
        """Test timeout handling."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(WeatherAPIError) as exc_info:
            client.get_forecast("Marburg")

        assert "timeout" in str(exc_info.value).lower()

    @patch.object(requests.Session, "post")
    def test_get_weather_for_day(self, mock_post, client, sample_response):
        """Test getting weather for a specific day."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.get_weather_for_day("Marburg", "friday")

        assert result is not None
        assert result.day == "friday"
        assert result.weather == "rain"

    @patch.object(requests.Session, "post")
    def test_get_weather_for_day_not_found(self, mock_post, client, sample_response):
        """Test getting weather for non-existent day."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.get_weather_for_day("Marburg", "monday")

        assert result is None

    @patch.object(requests.Session, "post")
    def test_get_today_weather(self, mock_post, client, sample_response):
        """Test getting today's weather."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_response
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.get_weather_for_today("Marburg")

        assert result is not None
        assert result.day == "thursday"
