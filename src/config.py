from pydantic_settings import BaseSettings

from src.api.config import APISettings


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
