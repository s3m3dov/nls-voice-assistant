"""Voice assistant main entry point."""
import re

from src.asr.recorder import VoiceRecorder
from src.asr.transcriber import WhisperTranscriber
from src.config import settings
from src.dialogue.chat import build_system_prompt, chat_stream
from src.logger import logger, setup_logging
from src.tts.audio_player import play_samples
from src.tts.kokoro_engine import KokoroTTS
from src.tts.sanitizer import sanitize_for_tts

# Regex to split on sentence boundaries while keeping the delimiter
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def main():
    """Main conversation loop with voice input and output."""
    # Initialize logging
    setup_logging()

    logger.info("Voice Assistant - Initializing...")

    # Initialize ASR components
    logger.info("Loading Whisper model...")
    transcriber = WhisperTranscriber(
        model_name=settings.asr.model_name,
    )
    recorder = VoiceRecorder(vad_threshold=settings.asr.vad_threshold)

    # Initialize TTS
    logger.info("Loading Kokoro TTS...")
    tts = KokoroTTS(
        model_path=settings.tts.model_path,
        voices_path=settings.tts.voices_path,
        voice=settings.tts.voice,
    )
    logger.info("Voice Assistant is ready!")

    messages = [{"role": "system", "content": build_system_prompt()}]

    # Assistant speaks first with a greeting
    greeting = "Hello! How can I help you today?"
    logger.info(f"Assistant: {greeting}")
    samples, sample_rate = tts.synthesize(greeting)
    play_samples(samples, sample_rate)
    messages.append({"role": "assistant", "content": greeting})

    while True:
        try:
            logger.info("Listening... (speak now)")
            audio = recorder.record_until_silence()

            if audio.numel() == 0:
                logger.warn("No speech detected. Try again.")
                continue

            logger.debug("Transcribing...")
            user_input = transcriber.transcribe(audio)

            if not user_input:
                logger.warn("Could not transcribe. Try again.")
                continue

            logger.info(f"You: {user_input}")

            # Get LLM response (streaming with TTS)
            logger.debug("Getting LLM response...")
            full_response = ""
            text_buffer = ""

            for chunk in chat_stream(user_input, messages):
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
                            samples, sample_rate = tts.synthesize(clean_text)
                            play_samples(samples, sample_rate)

                    # Keep the incomplete sentence in buffer
                    text_buffer = sentences[-1]

            # Speak any remaining text in buffer
            if text_buffer.strip():
                clean_text = sanitize_for_tts(text_buffer.strip())
                if clean_text:
                    samples, sample_rate = tts.synthesize(clean_text)
                    play_samples(samples, sample_rate)

            logger.info(f"Assistant: {full_response}")

        except KeyboardInterrupt:
            logger.info("Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
