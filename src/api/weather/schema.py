from typing import Optional

from pydantic import BaseModel, Field


class TemperatureResponse(BaseModel):
    """Temperature range in a weather forecast response."""

    min: int = Field(..., description="Minimum temperature in Celsius")
    max: int = Field(..., description="Maximum temperature in Celsius")


class DayForecastResponse(BaseModel):
    """Weather forecast for a single day in the response."""

    day: str = Field(..., description="Day name (e.g., 'monday', 'tuesday')")
    temperature: TemperatureResponse
    weather: str = Field(..., description="Weather condition description")


class WeatherResponse(BaseModel):
    """Complete weather forecast API response."""

    place: str = Field(..., description="Location name")
    forecast: list[DayForecastResponse] = Field(default_factory=list)

    def get_day(self, day_name: str) -> Optional[DayForecastResponse]:
        """Get a forecast for a specific day by name (case-insensitive)."""
        day_lower = day_name.lower()
        for day_forecast in self.forecast:
            if day_forecast.day.lower() == day_lower:
                return day_forecast
        return None

    def get_today(self) -> Optional[DayForecastResponse]:
        """Get today's forecast (first day in the list)."""
        return self.forecast[0] if self.forecast else None
