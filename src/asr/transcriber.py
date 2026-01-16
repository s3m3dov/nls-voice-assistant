"""Distil-Whisper ASR transcriber."""
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from src.config import settings


class WhisperTranscriber:
    """Speech-to-text transcription using Distil-Whisper."""

    def __init__(self, model_name: str = settings.asr.model_name, device: str | None = None):
        """
        Initialize the Whisper transcriber.

        Args:
            model_name: HuggingFace model ID.
            device: Device to run on ('cuda', 'cpu', or None for auto).
        """
        self.model_name = model_name

        # Auto-select device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # Load model and processor
        torch_dtype = torch.float16 if device == "cuda" else torch.float32

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_name,
            dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
        ).to(device)

        self.processor = AutoProcessor.from_pretrained(model_name)

        # Create pipeline
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            dtype=torch_dtype,
            device=device,
        )

    def transcribe(self, audio: torch.Tensor | list[float]) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Audio tensor or list (16kHz, mono, float32, normalized to [-1, 1]).

        Returns:
            Transcribed text.
        """
        # Convert tensor to numpy if needed
        if isinstance(audio, torch.Tensor):
            audio_np = audio.squeeze().cpu().numpy()
        else:
            import numpy as np
            audio_np = np.array(audio, dtype=np.float32)

        # Run transcription
        result = self.pipe(
            {"array": audio_np, "sampling_rate": settings.asr.sample_rate},
            return_timestamps=False,
        )
        return result["text"].strip()
