"""UI-specific configuration settings."""

from pydantic_settings import BaseSettings


class UISettings(BaseSettings):
    """Configuration for the Gradio web UI."""

    host: str = "0.0.0.0"
    port: int = 7860
    share: bool = False
    theme: str = "soft"
    title: str = "Voice Assistant"
