from pydantic_settings import BaseSettings

from src.api.config import APISettings
from src.api.weather import WeatherClient
from src.api.calendar.client import CalendarClient


class Settings(BaseSettings):
    """
    Application-wide settings container.
    """
    
    # API settings (nested)
    api: APISettings = APISettings(
        calendar_id="team-ezekiel"
    )

    model_config = {
        "extra": "ignore",
    }


# Singleton instances
settings = Settings()

# Pre-initialized API clients using the application settings
weather_client = WeatherClient(settings.api)
calendar_client = CalendarClient(settings.api)
