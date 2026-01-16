"""Silero VAD (Voice Activity Detection) wrapper."""
import torch
from silero_vad import get_speech_timestamps, load_silero_vad

from src.config import settings


class SileroVAD:
    """Voice Activity Detection using Silero VAD model."""

    def __init__(self, threshold: float = 0.5):
        """
        Initialize Silero VAD.

        Args:
            threshold: Speech probability threshold (0.0-1.0).
        """
        self.threshold = threshold
        self.model = load_silero_vad()
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset the model's internal state."""
        self.model.reset_states()

    def get_speech_probability(self, audio_chunk: torch.Tensor) -> float:
        """
        Get speech probability for an audio chunk.

        Args:
            audio_chunk: Audio tensor (16kHz, mono, float32, normalized to [-1, 1]).

        Returns:
            Speech probability (0.0-1.0).
        """
        if audio_chunk.dim() == 1:
            audio_chunk = audio_chunk.unsqueeze(0)
        prob = self.model(audio_chunk, settings.asr.sample_rate).item()
        return prob

    def is_speech(self, audio_chunk: torch.Tensor) -> bool:
        """
        Check if audio chunk contains speech.

        Args:
            audio_chunk: Audio tensor (16kHz, mono, float32).

        Returns:
            True if speech detected, False otherwise.
        """
        return self.get_speech_probability(audio_chunk) >= self.threshold

    def get_speech_timestamps(
        self,
        audio: torch.Tensor,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 100,
    ) -> list[dict]:
        """
        Get speech timestamps from full audio.

        Args:
            audio: Full audio tensor (16kHz, mono, float32).
            min_speech_duration_ms: Minimum speech segment duration in ms.
            min_silence_duration_ms: Minimum silence duration to split segments.

        Returns:
            List of dicts with 'start' and 'end' sample indices.
        """
        self._reset_state()
        return get_speech_timestamps(
            audio,
            self.model,
            threshold=self.threshold,
            sampling_rate=settings.asr.sample_rate,
            min_speech_duration_ms=min_speech_duration_ms,
            min_silence_duration_ms=min_silence_duration_ms,
        )

    def reset(self) -> None:
        """Reset VAD state for new audio stream."""
        self._reset_state()
