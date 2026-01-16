"""Microphone recording with Voice Activity Detection."""
import numpy as np
import pyaudio
import torch

from src.asr.vad import SileroVAD
from src.config import settings

# Audio constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
MAX_INT16 = 32768.0


class VoiceRecorder:
    """Records audio from a microphone with VAD-based start/stop."""

    def __init__(self, vad_threshold: float = settings.asr.vad_threshold):
        """
        Initialize the voice recorder.

        Args:
            vad_threshold: Speech detection threshold (0.0-1.0).
        """
        self.vad = SileroVAD(threshold=vad_threshold)
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
        data = self._stream.read(settings.asr.chunk_samples, exception_on_overflow=False)
        # Convert int16 to float32 tensor
        audio_int16 = np.frombuffer(data, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / MAX_INT16
        return torch.from_numpy(audio_float)

    def record_until_silence(self) -> torch.Tensor:
        """
        Record audio from microphone until silence is detected.

        Waits for speech to begin, then records until silence.

        Returns:
            Audio tensor (16kHz, mono, float32, normalized to [-1, 1]).
        """
        self._init_audio()
        self.vad.reset()

        pre_roll_buffer: list[torch.Tensor] = []
        recorded_chunks: list[torch.Tensor] = []
        is_recording = False
        speech_chunk_count = 0
        silence_chunk_count = 0
        max_chunks = int(settings.asr.max_recording_seconds * self.sample_rate / settings.asr.chunk_samples)

        try:
            for _ in range(max_chunks):
                chunk = self._read_chunk()

                if not is_recording:
                    # Waiting for speech - maintain pre-roll buffer
                    pre_roll_buffer.append(chunk)
                    if len(pre_roll_buffer) > settings.asr.pre_roll_chunks:
                        pre_roll_buffer.pop(0)

                    if self.vad.is_speech(chunk):
                        speech_chunk_count += 1
                        if speech_chunk_count >= 2:  # Confirm speech
                            is_recording = True
                            recorded_chunks = list(pre_roll_buffer)
                            recorded_chunks.append(chunk)
                    else:
                        speech_chunk_count = 0
                else:
                    # Recording speech
                    recorded_chunks.append(chunk)

                    if self.vad.is_speech(chunk):
                        silence_chunk_count = 0
                    else:
                        silence_chunk_count += 1
                        if silence_chunk_count >= settings.asr.silence_chunks_to_stop:
                            # Check we have enough speech
                            if len(recorded_chunks) >= settings.asr.min_speech_chunks:
                                break
                            # Not enough speech, keep waiting
                            silence_chunk_count = 0

            # Combine all chunks
            if recorded_chunks:
                return torch.cat(recorded_chunks)
            return torch.tensor([], dtype=torch.float32)

        finally:
            self._close_audio()

    def __del__(self):
        """Cleanup on deletion."""
        self._close_audio()
