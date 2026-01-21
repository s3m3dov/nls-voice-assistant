"""CLI mode for the voice assistant with microphone input."""

import re

from src.assistant import VoiceAssistant
from src.asr.recorder import VoiceRecorder
from src.config import settings
from src.logger import logger
from src.tts.audio_player import play_samples
from src.tts.sanitizer import sanitize_for_tts

# Regex to split on sentence boundaries while keeping the delimiter
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def run() -> None:
    """Run the voice assistant in CLI mode with microphone input."""
    logger.info("Voice Assistant - Initializing (CLI Mode)...")

    # Initialize shared assistant
    assistant = VoiceAssistant()
    assistant.initialize()

    # Initialize CLI-specific components (voice recorder)
    recorder = VoiceRecorder(vad_threshold=settings.asr.vad_threshold)
    logger.info("Voice Assistant is ready!")

    # Assistant speaks first with a greeting
    greeting = "Hello! How can I help you today?"
    logger.info(f"Assistant: {greeting}")
    samples, sample_rate = assistant.synthesize_speech(greeting)
    play_samples(samples, sample_rate)
    assistant.add_message("assistant", greeting)

    while True:
        try:
            logger.info("Listening... (speak now)")
            audio = recorder.record_until_silence()

            if audio.numel() == 0:
                logger.warn("No speech detected. Try again.")
                continue

            user_input = assistant.transcribe_audio(audio)

            if not user_input:
                logger.warn("Could not transcribe. Try again.")
                continue

            # Get streaming LLM response with sentence-by-sentence TTS
            full_response = ""
            text_buffer = ""

            for chunk in assistant.get_response_stream(user_input):
                full_response += chunk
                text_buffer += chunk

                # Check for complete sentences in buffer
                sentences = SENTENCE_SPLIT_RE.split(text_buffer)

                # If we have more than one element, we have complete sentences
                if len(sentences) > 1:
                    # Speak all complete sentences
                    for sentence in sentences[:-1]:
                        clean_text = sanitize_for_tts(sentence.strip())
                        if clean_text:
                            samples, sample_rate = assistant.synthesize_speech(clean_text)
                            play_samples(samples, sample_rate)

                    # Keep the incomplete sentence in buffer
                    text_buffer = sentences[-1]

            # Speak any remaining text in buffer
            if text_buffer.strip():
                clean_text = sanitize_for_tts(text_buffer.strip())
                if clean_text:
                    samples, sample_rate = assistant.synthesize_speech(clean_text)
                    play_samples(samples, sample_rate)

        except KeyboardInterrupt:
            logger.info("Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
