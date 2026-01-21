#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.tts.kokoro_engine import KokoroTTS
from src.config import settings
from src.logger import setup_logging

def generate_samples():
    setup_logging()
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent / "samples"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize TTS
    # Check if models are in root (as per ls command)
    model_path = project_root / settings.tts.model_path
    voices_path = project_root / settings.tts.voices_path
    
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        return

    print(f"Loading TTS model from {model_path}...")
    tts = KokoroTTS(
        model_path=str(model_path),
        voices_path=str(voices_path),
        voice=settings.tts.voice
    )
    
    test_sentences = [
        {
            "id": "greeting",
            "text": "Hello! How can I help you today?"
        },
        {
            "id": "weather",
            "text": "The weather in Marburg today is rainy with a high of 12 degrees and a low of 8."
        },
        {
            "id": "calendar",
            "text": "I have scheduled a meeting with the marketing team for next Tuesday at 2 PM."
        },
        {
            "id": "complex",
            "text": "I can't find that event. Did you mean the one on Friday, or the new appointment you just added?"
        },
        {
            "id": "long",
            "text": "To create a new event, please tell me the title, the date, and the time. For example, add a team meeting for tomorrow at 10 AM."
        }
    ]
    
    print(f"Generating {len(test_sentences)} samples...")
    
    for item in test_sentences:
        filename = output_dir / f"{item['id']}.wav"
        print(f"Generating {filename.name}...")
        tts.speak(item['text'], str(filename))
        
    print(f"Done! Samples saved to {output_dir}")

if __name__ == "__main__":
    generate_samples()
