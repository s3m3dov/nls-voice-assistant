"""Dialogue configuration settings."""
from pydantic import Field
from pydantic_settings import BaseSettings


class DialogueSettings(BaseSettings):
    """Dialogue configuration settings."""

    # Model configuration
    llm_model: str = Field(description="Ollama model tag to use for chat")
