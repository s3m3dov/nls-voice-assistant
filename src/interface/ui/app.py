"""Gradio Web UI for the Voice Assistant."""

import base64
import io
import os
import re
import wave
from enum import Enum
from pathlib import Path
from typing import Generator

import gradio as gr
import numpy as np
import torch

from src.assistant import VoiceAssistant
from src.asr.stream import StreamState, VADStreamProcessor
from src.interface.ui.config import UISettings
from src.logger import logger, setup_logging

# Disable Gradio analytics/telemetry
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

# Directory containing static assets
STATIC_DIR = Path(__file__).parent / "static"

# Regex to split text on sentence boundaries
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


# Monkey-patch to fix Gradio's JSON schema parsing bug
def _patched_get_api_info(self):
    return {"named_endpoints": {}, "unnamed_endpoints": {}}


gr.Blocks.get_api_info = _patched_get_api_info


# =============================================================================
# Enums
# =============================================================================


class StatusIcon(str, Enum):
    """UI status indicators."""

    INACTIVE = "🔴 Inactive"
    WAITING = "💤 Waiting..."
    LISTENING = "👂 Listening..."
    THINKING = "🤔 Thinking..."
    SPEAKING = "🗣️ Speaking..."
    ERROR = "❌ Error"


# =============================================================================
# Audio Utilities
# =============================================================================


def audio_to_base64_wav(samples: np.ndarray, sample_rate: int) -> str:
    """Convert audio samples to base64-encoded WAV string for browser playback."""
    # Convert float samples to int16
    if samples.dtype in (np.float32, np.float64):
        samples = (samples * 32767).astype(np.int16)

    # Create WAV in memory
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())

    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


# =============================================================================
# TTS Buffer
# =============================================================================


class TTSBuffer:
    """Handles text-to-speech buffering and synthesis for streaming."""

    def __init__(self, assistant: VoiceAssistant):
        self.assistant = assistant

    def process_buffer(
        self, text_buffer: str
    ) -> tuple[str, list[tuple[int, np.ndarray]]]:
        """
        Synthesize complete sentences from buffer.

        Returns:
            Tuple of (remaining_text, list_of_audio_chunks)
        """
        audio_chunks = []
        if not text_buffer.strip():
            return text_buffer, audio_chunks

        sentences = SENTENCE_SPLIT_RE.split(text_buffer)

        # Process all complete sentences (all but last)
        if len(sentences) > 1:
            for sentence in sentences[:-1]:
                chunk = self._synthesize_text(sentence.strip())
                if chunk:
                    audio_chunks.append(chunk)
            return sentences[-1], audio_chunks

        return text_buffer, audio_chunks

    def process_remaining(self, text_buffer: str) -> list[tuple[int, np.ndarray]]:
        """Synthesize any remaining text in buffer."""
        audio_chunks = []
        if text_buffer.strip():
            chunk = self._synthesize_text(text_buffer.strip())
            if chunk:
                audio_chunks.append(chunk)
        return audio_chunks

    def _synthesize_text(self, text: str) -> tuple[int, np.ndarray] | None:
        """Synthesize a single text segment."""
        try:
            samples, sample_rate = self.assistant.synthesize_speech(text)
            if samples is None:
                return None
            return (sample_rate, samples)
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None


# =============================================================================
# Stream Handler
# =============================================================================


class AudioStreamHandler:
    """Handles the main audio streaming pipeline: VAD -> ASR -> LLM -> TTS."""

    def __init__(self, assistant: VoiceAssistant):
        self.assistant = assistant
        self.tts = TTSBuffer(assistant)
        self.vad_processor = VADStreamProcessor()
        self.is_processing = False

    def process_stream(
        self,
        audio_chunk: tuple[int, np.ndarray] | None,
        history: list,
    ) -> Generator[tuple[list, str, tuple[int, np.ndarray] | None], None, None]:
        """
        Main streaming handler.

        Yields:
            Tuple of (chat_history, status_text, audio_output)
        """
        if audio_chunk is None:
            yield history, StatusIcon.INACTIVE.value, None
            return

        if self.is_processing:
            yield history, StatusIcon.SPEAKING.value, None
            return

        # Normalize input audio
        sample_rate, audio_data = audio_chunk
        audio_data = self._normalize_audio(audio_data)
        chunk_tensor = torch.from_numpy(audio_data).float()

        # Process through VAD
        state, full_audio = self.vad_processor.process(chunk_tensor, sample_rate)

        if state == StreamState.WAITING:
            yield history, StatusIcon.WAITING.value, None
        elif state == StreamState.LISTENING:
            yield history, StatusIcon.LISTENING.value, None
        elif state == StreamState.FINISHED and full_audio is not None:
            yield from self._process_utterance(full_audio, history)
            self.vad_processor.reset()

    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to float32 mono."""
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0

        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        return audio_data

    def _process_utterance(
        self,
        audio_tensor: torch.Tensor,
        history: list,
    ) -> Generator[tuple[list, str, tuple[int, np.ndarray] | None], None, None]:
        """Process a complete user utterance: ASR -> LLM -> TTS."""
        self.is_processing = True
        yield history, StatusIcon.THINKING.value, None

        try:
            user_text = self.assistant.transcribe_audio(audio_tensor)

            if not user_text.strip():
                return

            history.append([user_text, None])
            yield history, StatusIcon.THINKING.value, None

            yield from self._stream_response(user_text, history)

        except Exception as e:
            logger.error(f"Processing error: {e}")
            yield history, StatusIcon.ERROR.value, None

        finally:
            self.is_processing = False
            yield history, StatusIcon.WAITING.value, None

    def _stream_response(
        self,
        user_text: str,
        history: list,
    ) -> Generator[tuple[list, str, tuple[int, np.ndarray] | None], None, None]:
        """Stream LLM response with sentence-by-sentence TTS."""
        full_response = ""
        text_buffer = ""

        yield history, StatusIcon.SPEAKING.value, None

        for chunk in self.assistant.get_response_stream(user_text):
            full_response += chunk
            text_buffer += chunk

            text_buffer, audio_chunks = self.tts.process_buffer(text_buffer)
            history[-1][1] = full_response

            if audio_chunks:
                for audio_chunk in audio_chunks:
                    yield history, StatusIcon.SPEAKING.value, audio_chunk
            else:
                yield history, StatusIcon.SPEAKING.value, None

        # Process remaining text
        audio_chunks = self.tts.process_remaining(text_buffer)
        history[-1][1] = full_response

        if audio_chunks:
            for audio_chunk in audio_chunks:
                yield history, StatusIcon.SPEAKING.value, audio_chunk
        else:
            yield history, StatusIcon.SPEAKING.value, None


# =============================================================================
# Application
# =============================================================================


class VoiceAssistantApp:
    """Main application controller."""

    _audio_chunk_counter = 0

    def __init__(self):
        self.assistant: VoiceAssistant | None = None
        self.handler: AudioStreamHandler | None = None
        self.ui_settings = UISettings()

    def initialize(self) -> None:
        """Initialize models and handlers."""
        logger.info("Initializing Voice Assistant...")
        self.assistant = VoiceAssistant()
        self.assistant.initialize()
        self.handler = AudioStreamHandler(self.assistant)
        logger.info("Initialization complete")

    def create_ui(self) -> gr.Blocks:
        """Create the Gradio UI."""
        with gr.Blocks(
            title=self.ui_settings.title,
            theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate"),
            css=self._load_css(),
            head=self._load_js(),
        ) as demo:
            # Status indicator
            status_label = gr.HTML(
                value=f'<div class="status-display">{StatusIcon.WAITING.value}</div>',
                elem_classes=["status-container"],
                elem_id="status_label",
            )

            # Hidden container for audio data (used by JavaScript)
            audio_data = gr.HTML(value="", visible=False, elem_id="audio_data")

            with gr.Column(elem_classes=["main-container"]):
                gr.Markdown("# 🎙️ Voice Chat")

                chatbot = gr.Chatbot(
                    label="Conversation",
                    elem_classes=["chatbot"],
                    bubble_full_width=False,
                    avatar_images=(
                        None,
                        "https://api.dicebear.com/7.x/bottts/svg?seed=assistant",
                    ),
                )

                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="numpy",
                    streaming=True,
                    visible=True,
                    label="Microphone Stream",
                    show_label=False,
                )

                with gr.Accordion("Controls", open=False):
                    clear_btn = gr.Button("Clear Chat", variant="secondary")

            # State for accumulated audio chunks
            audio_chunks_state = gr.State(value="")

            # Event handlers
            audio_input.stream(
                fn=self._process_audio_stream,
                inputs=[audio_input, chatbot, audio_chunks_state],
                outputs=[chatbot, status_label, audio_data, audio_chunks_state],
                show_progress=False,
            )

            clear_btn.click(
                fn=self._clear_conversation,
                outputs=[chatbot, audio_data],
            )

        return demo

    def _process_audio_stream(
        self,
        audio_input: tuple[int, np.ndarray] | None,
        chat_history: list,
        accumulated_audio: str,
    ) -> Generator[tuple[list, str, str, str], None, None]:
        """Process audio stream and convert TTS output to base64 for browser playback."""
        if accumulated_audio is None:
            accumulated_audio = ""

        for history, status, audio_chunk in self.handler.process_stream(
            audio_input, chat_history
        ):
            if audio_chunk is not None:
                sample_rate, samples = audio_chunk
                audio_b64 = audio_to_base64_wav(samples, sample_rate)

                VoiceAssistantApp._audio_chunk_counter += 1
                chunk_id = VoiceAssistantApp._audio_chunk_counter
                accumulated_audio += (
                    f'<div class="audio-chunk" '
                    f'data-audio="{audio_b64}" '
                    f'data-chunk-id="{chunk_id}"></div>'
                )
                logger.debug(f"Sending audio chunk {chunk_id} to browser")

            yield (
                history,
                f'<div class="status-display">{status}</div>',
                accumulated_audio,
                accumulated_audio,
            )

    def _clear_conversation(self) -> tuple[list, str]:
        """Clear conversation history and audio state."""
        if self.assistant is not None:
            self.assistant.reset_conversation()
        return [], ""

    @staticmethod
    def _load_css() -> str:
        """Load CSS from external file."""
        css_path = STATIC_DIR / "styles.css"
        if css_path.exists():
            return css_path.read_text()
        logger.warning(f"CSS file not found: {css_path}")
        return ""

    @staticmethod
    def _load_js() -> str:
        """Load JavaScript from external file and wrap in script tag."""
        js_path = STATIC_DIR / "audio_player.js"
        if js_path.exists():
            js_content = js_path.read_text()
            return f"<script>\n{js_content}\n</script>"
        logger.warning(f"JavaScript file not found: {js_path}")
        return ""

    def run(self) -> None:
        """Start the application."""
        setup_logging()
        logger.info("Starting Voice Assistant UI...")

        self.initialize()
        demo = self.create_ui()

        demo.launch(
            server_name=self.ui_settings.host,
            server_port=self.ui_settings.port,
            share=self.ui_settings.share,
            show_api=False,
        )


# =============================================================================
# Entry Point
# =============================================================================


def run() -> None:
    """Application entry point."""
    app = VoiceAssistantApp()
    app.run()


if __name__ == "__main__":
    run()
