from typing import Optional

import requests

from src.api.config import APISettings
from .exception import WeatherAPIError
from .schema import DayForecastResponse, WeatherResponse


class WeatherClient:
    """Client for interacting with the Weather API."""

    def __init__(self, settings: APISettings):
        """
        Initialize the Weather API client.

        Args:
            settings: API settings with endpoint configuration.
        """
        self.settings = settings
        self._session = requests.Session()

    def get_forecast(self, place: str) -> WeatherResponse:
        """
        Get a weather forecast for a location.

        Args:
            place: The location name to get weather for.

        Returns:
            WeatherResponse object containing a 7-day forecast.

        Raises:
            WeatherAPIError: If the API request fails.
        """
        try:
            response = self._session.post(
                self.settings.weather_endpoint,
                data={"place": place},
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            return WeatherResponse.model_validate(response.json())

        except requests.exceptions.HTTPError as e:
            raise WeatherAPIError(f"HTTP error: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise WeatherAPIError(f"Connection error: {e}") from e
        except requests.exceptions.Timeout as e:
            raise WeatherAPIError(f"Request timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            raise WeatherAPIError(f"Request failed: {e}") from e
        except Exception as e:
            raise WeatherAPIError(f"Unexpected error: {e}") from e

    def get_weather_for_day(self, place: str, day: str) -> Optional[DayForecastResponse]:
        """
        Get a weather forecast for a specific day.

        Args:
            place: The location name to get weather for.
            day: The day name (e.g., 'monday', 'tuesday').

        Returns:
            DayForecastResponse for the specified day, or None if not found.

        Raises:
            WeatherAPIError: If the API request fails.
        """
        forecast = self.get_forecast(place)
        return forecast.get_day(day)

    def get_weather_for_today(self, place: str) -> Optional[DayForecastResponse]:
        """
        Get today's weather forecast.

        Args:
            place: The location name to get weather for.

        Returns:
            DayForecastResponse for today, or None if not available.

        Raises:
            WeatherAPIError: If the API request fails.
        """
        forecast = self.get_forecast(place)
        return forecast.get_today()
