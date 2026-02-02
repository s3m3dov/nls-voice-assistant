"""Ollama client configuration."""
from ollama import Client

from src.config import settings

# Single source of truth for the Ollama client
client = Client(host=settings.llm.base_url)
