"""
Stateful VAD Processor for streaming audio.

This module extracts the recording logic (pre-roll, silence detection, buffering)
into a reusable class that can be driven by either PyAudio (CLI) or Gradio (Web).
"""
import torch
import torchaudio
from collections import deque
from enum import Enum, auto

from src.asr.vad import SileroVAD
from src.config import settings


class StreamState(Enum):
    WAITING = auto()    # Waiting for speech to start
    LISTENING = auto()  # Speech detected, recording
    FINISHED = auto()   # Silence threshold reached, utterance complete


class VADStreamProcessor:
    """
    Processes audio chunks to detect speech segments using the shared ASR configuration.
    Buffers raw audio to ensure high-quality resampling at the end of the utterance.
    """
    def __init__(self):
        # Dependencies
        self.vad = SileroVAD(threshold=settings.asr.vad_threshold)
        
        # Configuration
        self.target_rate = settings.asr.sample_rate
        self.min_speech_chunks = settings.asr.min_speech_chunks
        self.silence_chunks_to_stop = settings.asr.silence_chunks_to_stop
        
        # State
        # We keep the raw audio (original sample rate) to avoid chunk-boundary artifacts during resampling
        self.raw_buffer: list[torch.Tensor] = []
        self.raw_pre_roll: deque[torch.Tensor] = deque(maxlen=settings.asr.pre_roll_chunks)
        
        # VAD counting state
        self.silence_counter: int = 0
        self.state = StreamState.WAITING
        self.current_sample_rate = self.target_rate # Default, updated on first chunk

    def reset(self):
        """Reset the processor for a new turn."""
        self.raw_buffer = []
        self.raw_pre_roll.clear()
        self.silence_counter = 0
        self.state = StreamState.WAITING
        self.vad.reset()

    def process(self, chunk: torch.Tensor, sample_rate: int) -> tuple[StreamState, torch.Tensor | None]:
        """
        Process a single audio chunk.
        
        Args:
            chunk: Audio tensor (arbitrary size/sample rate).
            sample_rate: The sample rate of the input chunk.
            
        Returns:
            Tuple of (CurrentState, AudioTensor | None).
            AudioTensor is 16kHz resampled audio, returned only when state is FINISHED.
        """
        self.current_sample_rate = sample_rate

        # Decimate input for VAD detection
        if sample_rate != self.target_rate:
            step = int(sample_rate / self.target_rate)
            if step > 0:
                vad_chunk = chunk[::step]
            else:
                vad_chunk = chunk
        else:
            vad_chunk = chunk

        # Split into windows for VAD model
        chunk_size = settings.asr.chunk_samples
        split_chunks = torch.split(vad_chunk, chunk_size)
        
        result_audio = None
        utterance_finished = False
        
        # State machine detection loop
        for sub_chunk in split_chunks:
            if sub_chunk.numel() < chunk_size:
                continue
                
            is_speech = self.vad.is_speech(sub_chunk)
            
            if self.state == StreamState.WAITING:
                if is_speech:
                    self.state = StreamState.LISTENING
                    self.silence_counter = 0
                    self.raw_buffer.extend(self.raw_pre_roll)
                    self.raw_pre_roll.clear()
                
            elif self.state == StreamState.LISTENING:
                if is_speech:
                    self.silence_counter = 0
                else:
                    self.silence_counter += 1
                    
                # Threshold check for end of speech
                if self.silence_counter >= self.silence_chunks_to_stop:
                    if len(self.raw_buffer) >= self.min_speech_chunks:
                        self.state = StreamState.FINISHED
                        utterance_finished = True
                        break 
                    else:
                        self.reset()
                        break

        # Manage raw audio buffers
        if self.state == StreamState.WAITING:
            self.raw_pre_roll.append(chunk)
        elif self.state == StreamState.LISTENING:
            self.raw_buffer.append(chunk)
        elif self.state == StreamState.FINISHED and utterance_finished:
            self.raw_buffer.append(chunk)
            
            # High-quality resampling of complete utterance
            full_raw = torch.cat(self.raw_buffer)
            
            if self.current_sample_rate != self.target_rate:
                result_audio = torchaudio.functional.resample(
                    full_raw, 
                    orig_freq=self.current_sample_rate, 
                    new_freq=self.target_rate
                )
            else:
                result_audio = full_raw

        return self.state, result_audio
