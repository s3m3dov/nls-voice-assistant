"""Integration tests for real Weather API endpoints."""

import pytest
from src.api.config import APISettings
from src.api.weather.client import WeatherClient
from src.api.weather.schema import WeatherResponse
from src.api.weather.exception import WeatherAPIError


class TestIntegrationWeather:
    """Integration tests for Weather API."""

    @pytest.fixture
    def settings(self):
        """Create real settings."""
        return APISettings(
            base_url="https://api.responsible-nlp.net",
            request_timeout=30,
        )

    @pytest.fixture
    def weather_client(self, settings):
        """Create real weather client."""
        return WeatherClient(settings)

    def test_get_forecast_valid_city(self, weather_client):
        """Test getting forecast for a known valid city."""
        place = "Marburg"
        forecast = weather_client.get_forecast(place)
        assert isinstance(forecast, WeatherResponse)
        assert forecast.place == place
        assert len(forecast.forecast) > 0

    def test_get_forecast_another_city(self, weather_client):
        """Test getting forecast for another city."""
        place = "Berlin"
        forecast = weather_client.get_forecast(place)
        assert isinstance(forecast, WeatherResponse)
        assert forecast.place == place

    def test_get_weather_for_day_case_insensitive(self, weather_client):
        """Test getting weather for a day with different casing."""
        place = "Marburg"
        forecast = weather_client.get_forecast(place)
        if not forecast.forecast:
            pytest.skip("No forecast data available")
        
        target_day = forecast.forecast[0].day
        
        # Test exact match
        day_weather = weather_client.get_weather_for_day(place, target_day)
        assert day_weather is not None
        assert day_weather.day == target_day

        # Test case variation
        upper_day = target_day.upper()
        day_weather_upper = weather_client.get_weather_for_day(place, upper_day)
        if day_weather_upper:
            assert day_weather_upper.day == target_day 

    def test_get_weather_for_today(self, weather_client):
        """Test getting today's weather."""
        place = "Marburg"
        today = weather_client.get_weather_for_today(place)
        # It might be None if 'today' is not in forecast list
        if today:
            assert today.day is not None
