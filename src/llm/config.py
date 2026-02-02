"""Dialogue configuration settings."""
from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """Dialogue configuration settings."""

    # Model configuration
    model: str = Field(description="Ollama model tag to use for chat")
    base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
        description="Base URL for Ollama API",
    )
