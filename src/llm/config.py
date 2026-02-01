"""Dialogue configuration settings."""
from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """Dialogue configuration settings."""

    # Model configuration
    model: str = Field(description="Ollama model tag to use for chat")
