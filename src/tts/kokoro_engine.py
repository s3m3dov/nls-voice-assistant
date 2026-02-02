"""
Kokoro TTS Engine

Requirements:
    pip install kokoro-onnx soundfile 'misaki[en]'

Model files needed (download to project root or specify paths):
    https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
    https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
"""

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from misaki import en, espeak

from src.logger import logger


class KokoroTTS:
    def __init__(
        self,
        model_path: str,
        voices_path: str,
        voice: str,
    ):
        self.voice = voice

        # Initialize G2P with espeak-ng fallback
        fallback = espeak.EspeakFallback(british=False)
        self.g2p = en.G2P(trf=False, british=False, fallback=fallback)

        # Initialize Kokoro
        self.kokoro = Kokoro(model_path, voices_path)

    def speak(self, text: str, output_path: str = "output.wav") -> str:
        """Convert text to speech and save to file."""
        phonemes, _ = self.g2p(text)
        samples, sample_rate = self.kokoro.create(
            phonemes, self.voice, is_phonemes=True
        )
        sf.write(output_path, samples, sample_rate)
        return output_path

    def synthesize(self, text: str) -> tuple:
        """Convert text to audio samples without saving to file.

        Returns:
            Tuple of (samples, sample_rate) for playback.
            samples is a numpy array of float32 audio data.
        """
        phonemes, _ = self.g2p(text)
        samples, sample_rate = self.kokoro.create(
            phonemes, self.voice, is_phonemes=True
        )
        # Ensure samples are numpy float32 for Gradio compatibility
        if not isinstance(samples, np.ndarray):
            samples = np.array(samples, dtype=np.float32)
        elif samples.dtype != np.float32:
            samples = samples.astype(np.float32)
        return samples, sample_rate


if __name__ == "__main__":
    from src.logger import setup_logging
    from src.config import settings

    setup_logging()
    tts = KokoroTTS(
        model_path=settings.tts.model_path,
        voices_path=settings.tts.voices_path,
        voice=settings.tts.voice,
    )
    tts.speak("Hello! This is a test of the Kokoro text to speech system.", "audio.wav")
    logger.info("Created audio.wav")
