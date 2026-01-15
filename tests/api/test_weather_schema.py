"""Tests for API schema models."""

import pytest
from pydantic import ValidationError

from src.api.weather.schema import (
    DayForecastResponse,
    TemperatureResponse,
    WeatherResponse,
)


class TestTemperatureResponse:
    """Tests for TemperatureResponse model."""

    def test_create_temperature(self):
        """Test creating a TemperatureResponse instance."""
        temp = TemperatureResponse(min=5, max=15)

        assert temp.min == 5
        assert temp.max == 15

    def test_temperature_from_dict(self):
        """Test creating TemperatureResponse from dict."""
        data = {"min": 10, "max": 20}
        temp = TemperatureResponse.model_validate(data)

        assert temp.min == 10
        assert temp.max == 20

    def test_temperature_required_fields(self):
        """Test that min and max are required."""
        with pytest.raises(ValidationError):
            TemperatureResponse(min=5)  # missing max

        with pytest.raises(ValidationError):
            TemperatureResponse(max=15)  # missing min


class TestDayForecastResponse:
    """Tests for DayForecastResponse model."""

    def test_create_day_forecast(self):
        """Test creating a DayForecastResponse instance."""
        forecast = DayForecastResponse(
            day="monday",
            temperature=TemperatureResponse(min=5, max=15),
            weather="clear sky",
        )

        assert forecast.day == "monday"
        assert forecast.temperature.min == 5
        assert forecast.temperature.max == 15
        assert forecast.weather == "clear sky"

    def test_day_forecast_from_dict(self):
        """Test creating DayForecastResponse from nested dict."""
        data = {
            "day": "tuesday",
            "temperature": {"min": 7, "max": 18},
            "weather": "few clouds",
        }
        forecast = DayForecastResponse.model_validate(data)

        assert forecast.day == "tuesday"
        assert forecast.temperature.min == 7
        assert forecast.weather == "few clouds"


class TestWeatherResponse:
    """Tests for WeatherResponse model."""

    @pytest.fixture
    def sample_forecast_data(self):
        """Sample forecast data fixture."""
        return {
            "place": "Marburg",
            "forecast": [
                {"day": "thursday", "temperature": {"min": 7, "max": 15}, "weather": "few clouds"},
                {"day": "friday", "temperature": {"min": 6, "max": 14}, "weather": "rain"},
                {"day": "saturday", "temperature": {"min": 5, "max": 11}, "weather": "clear sky"},
            ],
        }

    def test_create_weather_response(self, sample_forecast_data):
        """Test creating WeatherResponse from API response data."""
        response = WeatherResponse.model_validate(sample_forecast_data)

        assert response.place == "Marburg"
        assert len(response.forecast) == 3

    def test_get_day(self, sample_forecast_data):
        """Test getting forecast for a specific day."""
        response = WeatherResponse.model_validate(sample_forecast_data)

        friday = response.get_day("friday")
        assert friday is not None
        assert friday.weather == "rain"

        # Test case insensitivity
        friday_upper = response.get_day("FRIDAY")
        assert friday_upper is not None
        assert friday_upper.weather == "rain"

    def test_get_day_not_found(self, sample_forecast_data):
        """Test getting forecast for non-existent day."""
        response = WeatherResponse.model_validate(sample_forecast_data)

        result = response.get_day("monday")
        assert result is None

    def test_get_today(self, sample_forecast_data):
        """Test getting today's forecast (first day)."""
        response = WeatherResponse.model_validate(sample_forecast_data)

        today = response.get_today()
        assert today is not None
        assert today.day == "thursday"

    def test_get_today_empty_forecast(self):
        """Test get_today with empty forecast list."""
        response = WeatherResponse(place="Empty", forecast=[])

        assert response.get_today() is None

    def test_empty_forecast_default(self):
        """Test that forecast defaults to empty list."""
        response = WeatherResponse(place="Test")

        assert response.forecast == []
