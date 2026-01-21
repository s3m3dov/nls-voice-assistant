"""Shared Voice Assistant core logic used by both CLI and UI interfaces."""

from typing import Generator

from src.asr.transcriber import WhisperTranscriber
from src.config import settings
from src.dialogue.chat import build_system_prompt, chat_stream
from src.logger import logger
from src.tts.kokoro_engine import KokoroTTS
from src.tts.sanitizer import sanitize_for_tts


class VoiceAssistant:
    """Core voice assistant that manages models and conversation state."""

    def __init__(self):
        """Initialize the voice assistant with ASR and TTS models."""
        self.transcriber: WhisperTranscriber | None = None
        self.tts: KokoroTTS | None = None
        self.messages: list[dict[str, str]] = []
        self._initialized = False

    def initialize(self) -> None:
        """Initialize ASR and TTS models."""
        if self._initialized:
            logger.warning("Models already initialized")
            return

        logger.info("Loading Whisper model for ASR...")
        self.transcriber = WhisperTranscriber(model_name=settings.asr.model_name)

        logger.info("Loading Kokoro TTS...")
        self.tts = KokoroTTS(
            model_path=settings.tts.model_path,
            voices_path=settings.tts.voices_path,
            voice=settings.tts.voice,
        )

        # Initialize conversation with system prompt
        self.messages = [{"role": "system", "content": build_system_prompt()}]
        self._initialized = True
        logger.info("Models loaded successfully!")

    def is_initialized(self) -> bool:
        """Check if models are initialized."""
        return self._initialized

    def reset_conversation(self) -> None:
        """Reset conversation history to initial state."""
        self.messages = [{"role": "system", "content": build_system_prompt()}]
        logger.debug("Conversation reset")

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def get_response_stream(self, user_input: str) -> Generator[str, None, None]:
        """
        Get streaming LLM response for user input.

        Args:
            user_input: The user's message

        Yields:
            Chunks of the assistant's response
        """
        if not self._initialized:
            raise RuntimeError("Assistant not initialized. Call initialize() first.")

        logger.info(f"User: {user_input}")

        # Stream response from LLM (chat_stream handles message appending internally)
        logger.debug("Getting LLM response...")
        full_response = ""

        for chunk in chat_stream(user_input, self.messages):
            full_response += chunk
            yield chunk

        logger.info(f"Assistant: {full_response}")

    def synthesize_speech(self, text: str) -> tuple[any, int]:
        """
        Generate speech audio from text.

        Args:
            text: Text to synthesize

        Returns:
            Tuple of (audio_samples, sample_rate)
        """
        if not self._initialized or self.tts is None:
            raise RuntimeError("TTS not initialized. Call initialize() first.")

        clean_text = sanitize_for_tts(text)
        if not clean_text:
            raise ValueError("No valid text to synthesize after sanitization")

        return self.tts.synthesize(clean_text)

    def transcribe_audio(self, audio_tensor) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_tensor: Audio tensor to transcribe

        Returns:
            Transcribed text
        """
        if not self._initialized or self.transcriber is None:
            raise RuntimeError("Transcriber not initialized. Call initialize() first.")

        logger.debug("Transcribing audio...")
        return self.transcriber.transcribe(audio_tensor)
