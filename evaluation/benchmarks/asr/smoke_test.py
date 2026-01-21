#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import librosa

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.asr.transcriber import WhisperTranscriber
from src.config import settings
from src.logger import setup_logging

def run_smoke_test():
    setup_logging()
    
    print("Initializing Whisper Transcriber...")
    # This will trigger model download/loading
    transcriber = WhisperTranscriber()
    
    data_dir = Path(__file__).parent / "data" / "group_5"
    if not data_dir.exists():
        print(f"Data directory {data_dir} not found.")
        return

    audio_files = list(data_dir.glob("*.mp3"))
    if not audio_files:
        print("No .mp3 files found in data directory.")
        return
        
    print(f"Found {len(audio_files)} audio files.")
    
    for audio_file in audio_files:
        print(f"\nProcessing {audio_file.name}...")
        
        # Load audio with librosa (resample to 16kHz)
        audio, _ = librosa.load(str(audio_file), sr=settings.asr.sample_rate)
        
        # Transcribe
        text = transcriber.transcribe(audio)
        
        print(f"Transcription: {text}")

if __name__ == "__main__":
    run_smoke_test()
