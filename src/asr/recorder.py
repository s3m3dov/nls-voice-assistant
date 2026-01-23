"""Microphone recording with Voice Activity Detection (sounddevice)."""
import numpy as np
import sounddevice as sd
import torch

from src.asr.vad import SileroVAD
from src.config import settings

CHANNELS = 1


class VoiceRecorder:
    """Records audio from a microphone with VAD-based start/stop."""

    def __init__(self, vad_threshold: float = settings.asr.vad_threshold):
        self.vad = SileroVAD(threshold=vad_threshold)
        self.sample_rate = settings.asr.sample_rate
        self._stream: sd.InputStream | None = None
        self._buffer: list[torch.Tensor] = []

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)

        # indata: float32 in [-1, 1]
        audio = torch.from_numpy(indata.copy()).squeeze()
        self._buffer.append(audio)

    def record_until_silence(self) -> torch.Tensor:
        self.vad.reset()
        self._buffer.clear()

        pre_roll_buffer: list[torch.Tensor] = []
        recorded_chunks: list[torch.Tensor] = []

        is_recording = False
        speech_chunk_count = 0
        silence_chunk_count = 0

        max_chunks = int(
            settings.asr.max_recording_seconds
            * self.sample_rate
            / settings.asr.chunk_samples
        )

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=CHANNELS,
            blocksize=settings.asr.chunk_samples,
            dtype="float32",
            callback=self._audio_callback,
        ):
            for _ in range(max_chunks):
                if not self._buffer:
                    continue

                chunk = self._buffer.pop(0)

                if not is_recording:
                    pre_roll_buffer.append(chunk)
                    if len(pre_roll_buffer) > settings.asr.pre_roll_chunks:
                        pre_roll_buffer.pop(0)

                    if self.vad.is_speech(chunk):
                        speech_chunk_count += 1
                        if speech_chunk_count >= 2:
                            is_recording = True
                            recorded_chunks = list(pre_roll_buffer)
                            recorded_chunks.append(chunk)
                    else:
                        speech_chunk_count = 0
                else:
                    recorded_chunks.append(chunk)

                    if self.vad.is_speech(chunk):
                        silence_chunk_count = 0
                    else:
                        silence_chunk_count += 1
                        if silence_chunk_count >= settings.asr.silence_chunks_to_stop:
                            if len(recorded_chunks) >= settings.asr.min_speech_chunks:
                                break
                            silence_chunk_count = 0

        if recorded_chunks:
            return torch.cat(recorded_chunks)

        return torch.tensor([], dtype=torch.float32)
