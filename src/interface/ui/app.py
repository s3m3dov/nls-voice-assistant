"""Gradio Web UI for the Voice Assistant - Refactored."""

import os
import re
from enum import Enum
from typing import Generator
import numpy as np
import torch

# Disable Gradio analytics/telemetry
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr

# Monkey-patch to fix Gradio's JSON schema parsing bug
def _patched_get_api_info(self):
    return {"named_endpoints": {}, "unnamed_endpoints": {}}

gr.Blocks.get_api_info = _patched_get_api_info

from src.assistant import VoiceAssistant
from src.asr.stream import VADStreamProcessor, StreamState
from src.logger import logger, setup_logging
from src.interface.ui.config import UISettings
from src.tts.audio_player import play_samples
from src.tts.sanitizer import sanitize_for_tts


SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


class StatusIcon(str, Enum):
    """UI status indicators."""
    INACTIVE = "🔴 Inactive"
    WAITING = "💤 Waiting..."
    LISTENING = "👂 Listening..."
    THINKING = "🤔 Thinking..."
    SPEAKING = "🗣️ Speaking..."
    ERROR = "❌ Error"


# ============================================================================
# TTS Playback
# ============================================================================

class TTSPlayer:
    """Handles text-to-speech playback with sentence buffering."""

    def __init__(self, assistant: VoiceAssistant):
        self.assistant = assistant

    def play_sentence_buffer(self, text_buffer: str) -> str:
        """
        Synthesize and play complete sentences from buffer.
        Returns remaining incomplete text.
        """
        if not text_buffer.strip():
            return text_buffer

        sentences = SENTENCE_SPLIT_RE.split(text_buffer)

        # Play all complete sentences (all but last)
        if len(sentences) > 1:
            for sentence in sentences[:-1]:
                self._play_text(sentence.strip())
            return sentences[-1]

        return text_buffer

    def play_remaining(self, text_buffer: str) -> None:
        """Play any remaining text in buffer."""
        if text_buffer.strip():
            self._play_text(text_buffer.strip())

    def _play_text(self, text: str) -> None:
        """Synthesize and play a single text segment."""
        clean_text = sanitize_for_tts(text)
        if not clean_text:
            return

        try:
            samples, sample_rate = self.assistant.synthesize_speech(clean_text)
            play_samples(samples, sample_rate)
        except Exception as e:
            logger.error(f"TTS playback error: {e}")


# ============================================================================
# Main Stream Handler
# ============================================================================

class AudioStreamHandler:
    """Handles the main audio streaming pipeline."""

    def __init__(self, assistant: VoiceAssistant):
        self.assistant = assistant
        self.tts_player = TTSPlayer(assistant)
        # Use shared VAD processor (DRY)
        self.vad_processor = VADStreamProcessor()
        # Track processing state to block input during playback
        self.is_processing = False

    def process_stream(
        self,
        audio_chunk: tuple[int, np.ndarray] | None,
        history: list,
    ) -> Generator[tuple[list, str], None, None]:
        """
        Main streaming handler: VAD -> ASR -> LLM -> TTS pipeline.

        Yields:
            Tuple of (chat_history, status_text)
        """
        # Handle empty/None input
        if audio_chunk is None:
            yield history, StatusIcon.INACTIVE.value
            return

        # Block input during processing to prevent echo
        if self.is_processing:
            yield history, StatusIcon.SPEAKING.value
            return

        # 1. Normalize Input (Basic type conversion only)
        # Resampling is now handled by the shared VADStreamProcessor
        sample_rate, audio_data = audio_chunk
        
        # Normalize to float32
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        
        # Mono conversion
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        chunk_tensor = torch.from_numpy(audio_data).float()

        # 2. Process via Shared VAD Logic
        state, full_audio = self.vad_processor.process(chunk_tensor, sample_rate)

        # 3. Handle VAD State Changes
        if state == StreamState.WAITING:
            yield history, StatusIcon.WAITING.value
            
        elif state == StreamState.LISTENING:
            yield history, StatusIcon.LISTENING.value
            
        elif state == StreamState.FINISHED and full_audio is not None:
            # Utterance complete - Trigger Pipeline
            yield from self._process_utterance(full_audio, history)
            
            # Reset for next turn
            self.vad_processor.reset()

    def _process_utterance(
        self,
        audio_tensor: torch.Tensor,
        history: list,
    ) -> Generator[tuple[list, str], None, None]:
        """Process a complete user utterance: ASR -> LLM -> TTS."""
        self.is_processing = True
        yield history, StatusIcon.THINKING.value

        try:
            # Transcribe audio
            user_text = self.assistant.transcribe_audio(audio_tensor)

            if not user_text.strip():
                return

            # Add user message to history
            history.append([user_text, None])
            yield history, StatusIcon.THINKING.value

            # Stream LLM response with concurrent TTS
            yield from self._stream_response(user_text, history)

        except Exception as e:
            logger.error(f"Processing error: {e}")
            yield history, StatusIcon.ERROR.value

        finally:
            self.is_processing = False
            yield history, StatusIcon.WAITING.value

    def _stream_response(
        self,
        user_text: str,
        history: list,
    ) -> Generator[tuple[list, str], None, None]:
        """Stream LLM response with sentence-by-sentence TTS."""
        full_response = ""
        text_buffer = ""

        yield history, StatusIcon.SPEAKING.value

        # Stream LLM chunks
        for chunk in self.assistant.get_response_stream(user_text):
            full_response += chunk
            text_buffer += chunk

            # Play completed sentences
            text_buffer = self.tts_player.play_sentence_buffer(text_buffer)

            # Update UI
            history[-1][1] = full_response
            yield history, StatusIcon.SPEAKING.value

        # Play any remaining text
        self.tts_player.play_remaining(text_buffer)

        # Final update
        history[-1][1] = full_response
        yield history, StatusIcon.SPEAKING.value


# ============================================================================
# Application
# ============================================================================

class VoiceAssistantApp:
    """Main application controller."""

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

    def clear_conversation(self) -> list:
        """Reset conversation history."""
        if self.assistant is not None:
            self.assistant.reset_conversation()
        return []

    def create_ui(self) -> gr.Blocks:
        """Create the Gradio UI."""
        with gr.Blocks(
            title=self.ui_settings.title,
            theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate"),
            css=self._get_custom_css(),
        ) as demo:
            # No persistent state needed in UI anymore, managed by handler class
            state = gr.State()

            # Create a fixed status label outside the main column so it stays mounted
            status_label = gr.HTML(
                value=f'<div class="status-display">{StatusIcon.WAITING.value}</div>',
                elem_classes=["status-container"],
                elem_id="status_label"
            )

            with gr.Column(elem_classes=["main-container"]):
                gr.Markdown("# 🎙️ Voice Chat")

                # Keep the chatbot inside the column
                chatbot = gr.Chatbot(
                    label="Conversation",
                    elem_classes=["chatbot"],
                    bubble_full_width=False,
                    avatar_images=(
                        None,
                        "https://api.dicebear.com/7.x/bottts/svg?seed=assistant"
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

            # Wire up events - wrapper still yields HTML for the status element
            def process_with_html_status(*args):
                """Wrapper to convert status text to HTML."""
                for history, status in self.handler.process_stream(*args):
                    yield history, f'<div class="status-display">{status}</div>'

            audio_input.stream(
                fn=process_with_html_status,
                inputs=[audio_input, chatbot],
                outputs=[chatbot, status_label],
                show_progress=False,
            )

            clear_btn.click(
                fn=self.clear_conversation,
                outputs=[chatbot]
            )

        return demo

    @staticmethod
    def _get_custom_css() -> str:
        """Return custom CSS for the UI."""
        return """
            .chatbot {
                border: none !important;
            }
            
            .chatbot {
                min-height: 400px;
                flex-grow: 1;
                border-radius: 15px;
                border: 1px solid #e2e8f0;
            }
    
            .status-container {
                min-height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: transparent !important;
                visibility: visible !important;
                pointer-events: none;
            }
    
            .status-display {
                font-size: 1.2rem;
                font-weight: bold;
                text-align: center;
                padding: 10px 20px;
                background: rgba(99, 102, 241, 0.1);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 10px;
                display: inline-block;
                min-width: 200px;
                transition: opacity 120ms ease-in-out;
                opacity: 1 !important;
            }
    
            .main-container {
                max-width: 850px;
                margin: 0 auto;
                padding: 20px;
            }
        """


    def run(self) -> None:
        """Start the application."""
        setup_logging()
        logger.info("Starting Continuous Voice UI...")

        self.initialize()
        demo = self.create_ui()

        demo.launch(
            server_name=self.ui_settings.host,
            server_port=self.ui_settings.port,
            share=self.ui_settings.share,
            show_api=False,
        )


# ============================================================================
# Entry Point
# ============================================================================

def run() -> None:
    """Application entry point."""
    app = VoiceAssistantApp()
    app.run()


if __name__ == "__main__":
    run()