"""ASR configuration settings."""
from pydantic import Field
from pydantic_settings import BaseSettings


class ASRSettings(BaseSettings):
    """ASR configuration settings."""

    # Model configuration
    model_name: str = Field(description="HuggingFace model ID for Whisper")

    # Audio settings
    sample_rate: int = Field(
        default=16000,
        description="Audio sample rate in Hz",
    )

    # VAD settings
    vad_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Speech detection threshold",
    )

    # Recording settings
    chunk_samples: int = Field(
        default=512,
        description="Audio chunk size in samples",
    )
    pre_roll_chunks: int = Field(
        default=10,
        description="Number of chunks to keep before speech detection",
    )
    min_speech_chunks: int = Field(
        default=8,
        description="Minimum number of chunks to consider as speech",
    )
    silence_chunks_to_stop: int = Field(
        default=25,
        description="Number of silence chunks to stop recording",
    )
    max_recording_seconds: int = Field(
        default=30,
        description="Maximum recording duration in seconds",
    )
