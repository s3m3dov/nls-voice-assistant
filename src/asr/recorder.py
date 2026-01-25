"""Microphone recording with Voice Activity Detection."""
import numpy as np
import pyaudio
import torch

from src.asr.stream import VADStreamProcessor, StreamState
from src.config import settings

# Audio constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
MAX_INT16 = 32768.0


class VoiceRecorder:
    """Records audio from a microphone using the shared VADStreamProcessor."""

    def __init__(self):
        """Initialize the voice recorder."""
        self.processor = VADStreamProcessor()
        self.sample_rate = settings.asr.sample_rate
        self._pyaudio: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None

    def _init_audio(self) -> None:
        """Initialize PyAudio stream."""
        if self._pyaudio is None:
            self._pyaudio = pyaudio.PyAudio()
            self._stream = self._pyaudio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=settings.asr.chunk_samples,
            )

    def _close_audio(self) -> None:
        """Close PyAudio stream."""
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._pyaudio is not None:
            self._pyaudio.terminate()
            self._pyaudio = None

    def _read_chunk(self) -> torch.Tensor:
        """Read and convert one audio chunk from microphone."""
        assert self._stream is not None
        # PyAudio reads bytes
        data = self._stream.read(settings.asr.chunk_samples, exception_on_overflow=False)
        # Convert int16 bytes to a numpy array
        audio_int16 = np.frombuffer(data, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / MAX_INT16
        return torch.from_numpy(audio_float)

    def record_until_silence(self) -> torch.Tensor:
        """
        Record audio from the microphone until silence is detected.
        Delegates VAD logic to the shared VADStreamProcessor.

        Returns:
            Audio tensor (16kHz, mono, float32, normalized to [-1, 1]).
        """
        self._init_audio()
        self.processor.reset()

        max_chunks = int(settings.asr.max_recording_seconds * self.sample_rate / settings.asr.chunk_samples)

        try:
            for _ in range(max_chunks):
                chunk = self._read_chunk()
                
                # Feed chunk to the processor
                state, result_audio = self.processor.process(chunk, self.sample_rate)

                if state == StreamState.FINISHED and result_audio is not None:
                    return result_audio

            # Timeout reached without valid speech segment
            return torch.tensor([], dtype=torch.float32)

        finally:
            self._close_audio()

    def __del__(self):
        """Cleanup on deletion."""
        self._close_audio()
