import numpy as np
import torch
from faster_whisper import WhisperModel

from src.config import settings


class WhisperTranscriber:
    """Speech-to-text transcription using Faster-Whisper."""

    def __init__(self, model_name: str = settings.asr.model_name, device: str | None = None):
        """
        Initialize the Whisper transcriber.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large-v3).
            device: Device to run on ('cuda', 'cpu', or None for auto).
        """
        self.model_name = model_name

        # Auto-select device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # Load model with appropriate compute type
        compute_type = "float16" if device == "cuda" else "int8"
        self.model = WhisperModel(model_name, device=device, compute_type=compute_type)

    def transcribe(self, audio: torch.Tensor | list[float]) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Audio tensor or list (16kHz, mono, float32, normalized to [-1, 1]).

        Returns:
            Transcribed text.
        """
        # Convert to numpy array if needed
        if isinstance(audio, torch.Tensor):
            audio_np = audio.squeeze().cpu().numpy()
        else:
            audio_np = np.array(audio, dtype=np.float32)

        # Run transcription
        segments, _ = self.model.transcribe(audio_np, beam_size=5)

        # Collect all segment texts
        text = " ".join(segment.text for segment in segments)
        return text.strip()
