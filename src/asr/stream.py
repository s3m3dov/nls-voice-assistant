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
    """
    def __init__(self):
        # Dependencies
        self.vad = SileroVAD(threshold=settings.asr.vad_threshold)
        
        # Configuration from global settings
        self.sample_rate = settings.asr.sample_rate
        self.min_speech_chunks = settings.asr.min_speech_chunks
        self.silence_chunks_to_stop = settings.asr.silence_chunks_to_stop
        
        # State
        self.buffer: list[torch.Tensor] = []
        # Pre-roll buffer (deque handles a sliding window automatically)
        self.pre_roll_buffer: deque[torch.Tensor] = deque(maxlen=settings.asr.pre_roll_chunks)
        self.silence_counter: int = 0
        self.state = StreamState.WAITING

    def reset(self):
        """Reset the processor for a new turn."""
        self.buffer = []
        self.pre_roll_buffer.clear()
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
            AudioTensor is returned only when state is FINISHED.
        """
        # 1. Resample if necessary (Standardize input to model expectations)
        if sample_rate != self.sample_rate:
            chunk = torchaudio.functional.resample(
                chunk, 
                orig_freq=sample_rate, 
                new_freq=self.sample_rate
            )
        
        chunk_size = settings.asr.chunk_samples # 512
        split_chunks = torch.split(chunk, chunk_size)
        
        result_audio = None
        
        for sub_chunk in split_chunks:
            if sub_chunk.numel() < chunk_size:
                continue
                
            is_speech = self.vad.is_speech(sub_chunk)
            
            if self.state == StreamState.WAITING:
                if is_speech:
                    # Transition to LISTENING
                    self.state = StreamState.LISTENING
                    self.silence_counter = 0
                    
                    # Dump pre-roll into main buffer
                    self.buffer.extend(self.pre_roll_buffer)
                    self.pre_roll_buffer.clear()
                    self.buffer.append(sub_chunk)
                else:
                    # Keep waiting, update pre-roll
                    self.pre_roll_buffer.append(sub_chunk)
                    
            elif self.state == StreamState.LISTENING:
                self.buffer.append(sub_chunk)
                
                if is_speech:
                    self.silence_counter = 0
                else:
                    self.silence_counter += 1
                    
                # Check for silence timeout
                if self.silence_counter >= self.silence_chunks_to_stop:
                    # Check minimum speech duration
                    if len(self.buffer) >= self.min_speech_chunks + self.silence_chunks_to_stop:
                        self.state = StreamState.FINISHED
                        result_audio = torch.cat(self.buffer)
                        # We stop processing the rest of the input chunk if finished
                        break 
                    else:
                        # False start / noise
                        self.reset()
        
        return self.state, result_audio
