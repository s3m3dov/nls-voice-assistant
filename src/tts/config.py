from pydantic import Field
from pydantic_settings import BaseSettings


class TTSSettings(BaseSettings):
    """TTS configuration settings."""

    model_path: str = Field(description="Path to the Kokoro ONNX model file")
    voices_path: str = Field(description="Path to the Kokoro voices file")
    voice: str = Field(description="Voice ID to use for synthesis")
