"""Gradio Web UI for the Voice Assistant - Refactored."""

import base64
import io
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


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def audio_to_base64_wav(samples: np.ndarray, sample_rate: int) -> str:
    """Convert audio samples to base64-encoded WAV string for browser playback."""
    import wave

    # Ensure samples are in the right format
    if samples.dtype == np.float32 or samples.dtype == np.float64:
        # Convert float [-1, 1] to int16
        samples = (samples * 32767).astype(np.int16)

    # Create WAV in memory
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())

    # Encode to base64
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


class StatusIcon(str, Enum):
    """UI status indicators."""

    INACTIVE = "🔴 Inactive"
    WAITING = "💤 Waiting..."
    LISTENING = "👂 Listening..."
    THINKING = "🤔 Thinking..."
    SPEAKING = "🗣️ Speaking..."
    ERROR = "❌ Error"


# ============================================================================
# TTS Buffering & Synthesis
# ============================================================================


class TTSBuffer:
    """Handles text-to-speech buffering and synthesis for streaming."""

    def __init__(self, assistant: VoiceAssistant):
        self.assistant = assistant

    def process_buffer(
        self, text_buffer: str
    ) -> tuple[str, list[tuple[int, np.ndarray]]]:
        """
        Synthesize complete sentences from buffer.
        Returns (remaining_text, list_of_audio_chunks).
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
            # Gradio expects (sample_rate, numpy_array)
            return (sample_rate, samples)
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None


# ============================================================================
# Main Stream Handler
# ============================================================================


class AudioStreamHandler:
    """Handles the main audio streaming pipeline."""

    def __init__(self, assistant: VoiceAssistant):
        self.assistant = assistant
        self.tts = TTSBuffer(assistant)
        # Use shared VAD processor (DRY)
        self.vad_processor = VADStreamProcessor()
        # Track processing state to block input during playback
        self.is_processing = False

    def process_stream(
        self,
        audio_chunk: tuple[int, np.ndarray] | None,
        history: list,
    ) -> Generator[tuple[list, str, tuple[int, np.ndarray] | None], None, None]:
        """
        Main streaming handler: VAD -> ASR -> LLM -> TTS pipeline.

        Yields:
            Tuple of (chat_history, status_text, audio_output)
        """
        # Handle empty/None input
        if audio_chunk is None:
            yield history, StatusIcon.INACTIVE.value, None
            return

        # Block input during processing to prevent echo
        if self.is_processing:
            yield history, StatusIcon.SPEAKING.value, None
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
            yield history, StatusIcon.WAITING.value, None

        elif state == StreamState.LISTENING:
            yield history, StatusIcon.LISTENING.value, None

        elif state == StreamState.FINISHED and full_audio is not None:
            # Utterance complete - Trigger Pipeline
            yield from self._process_utterance(full_audio, history)

            # Reset for next turn
            self.vad_processor.reset()

    def _process_utterance(
        self,
        audio_tensor: torch.Tensor,
        history: list,
    ) -> Generator[tuple[list, str, tuple[int, np.ndarray] | None], None, None]:
        """Process a complete user utterance: ASR -> LLM -> TTS."""
        self.is_processing = True
        yield history, StatusIcon.THINKING.value, None

        try:
            # Transcribe audio
            user_text = self.assistant.transcribe_audio(audio_tensor)

            if not user_text.strip():
                return

            # Add user message to history
            history.append([user_text, None])
            yield history, StatusIcon.THINKING.value, None

            # Stream LLM response with concurrent TTS
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

        # Stream LLM chunks
        for chunk in self.assistant.get_response_stream(user_text):
            full_response += chunk
            text_buffer += chunk

            # Process buffer for complete sentences
            text_buffer, audio_chunks = self.tts.process_buffer(text_buffer)

            # Update UI
            history[-1][1] = full_response

            # Yield any generated audio chunks
            if audio_chunks:
                for audio_chunk in audio_chunks:
                    yield history, StatusIcon.SPEAKING.value, audio_chunk
            else:
                yield history, StatusIcon.SPEAKING.value, None

        # Play any remaining text
        audio_chunks = self.tts.process_remaining(text_buffer)

        # Final update
        history[-1][1] = full_response

        if audio_chunks:
            for audio_chunk in audio_chunks:
                yield history, StatusIcon.SPEAKING.value, audio_chunk
        else:
            yield history, StatusIcon.SPEAKING.value, None


# ============================================================================
# Application
# ============================================================================


class VoiceAssistantApp:
    """Main application controller."""

    # Class-level counter for unique audio chunk IDs
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
            head=self._get_audio_player_js(),
        ) as demo:
            # No persistent state needed in UI anymore, managed by handler class
            state = gr.State()

            # Create a fixed status label outside the main column so it stays mounted
            status_label = gr.HTML(
                value=f'<div class="status-display">{StatusIcon.WAITING.value}</div>',
                elem_classes=["status-container"],
                elem_id="status_label",
            )

            # Hidden element to trigger audio playback via JavaScript
            audio_data = gr.HTML(
                value="",
                visible=False,
                elem_id="audio_data",
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

            # Track audio chunks across the session
            audio_chunks_html = gr.State(value="")

            # Wire up events
            def process_with_audio(audio_input, chat_history, accumulated_audio):
                """Process stream and convert audio to base64 for JS playback."""
                if accumulated_audio is None:
                    accumulated_audio = ""

                for history, status, audio_chunk in self.handler.process_stream(
                    audio_input, chat_history
                ):
                    # Convert audio chunk to base64 for JavaScript playback
                    if audio_chunk is not None:
                        sample_rate, samples = audio_chunk
                        audio_b64 = audio_to_base64_wav(samples, sample_rate)
                        # Append new chunk with unique ID
                        VoiceAssistantApp._audio_chunk_counter += 1
                        chunk_id = VoiceAssistantApp._audio_chunk_counter
                        accumulated_audio += f'<div class="audio-chunk" data-audio="{audio_b64}" data-chunk-id="{chunk_id}"></div>'
                        logger.debug(f"Sending audio chunk {chunk_id} to browser")

                    yield (
                        history,
                        f'<div class="status-display">{status}</div>',
                        accumulated_audio,
                        accumulated_audio,
                    )

            audio_input.stream(
                fn=process_with_audio,
                inputs=[audio_input, chatbot, audio_chunks_html],
                outputs=[chatbot, status_label, audio_data, audio_chunks_html],
                show_progress=False,
            )

            def clear_all():
                """Clear conversation and reset audio state."""
                if self.assistant is not None:
                    self.assistant.reset_conversation()
                return [], ""

            clear_btn.click(fn=clear_all, outputs=[chatbot, audio_data])

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

    @staticmethod
    def _get_audio_player_js() -> str:
        """Return JavaScript for Web Audio API playback."""
        return """
        <script>
        (function() {
            // Audio queue for sequential playback
            const audioQueue = [];
            let isPlaying = false;
            let lastProcessedChunkId = 0;
            let audioContext = null;
            
            // Get or create audio context
            function getAudioContext() {
                if (!audioContext || audioContext.state === 'closed') {
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }
                if (audioContext.state === 'suspended') {
                    audioContext.resume();
                }
                return audioContext;
            }
            
            // Play next audio in queue
            async function playNext() {
                if (audioQueue.length === 0) {
                    isPlaying = false;
                    return;
                }
                
                isPlaying = true;
                const {audioData, chunkId} = audioQueue.shift();
                console.log('Playing chunk:', chunkId, 'queue:', audioQueue.length);
                
                try {
                    const binaryString = atob(audioData);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    
                    const ctx = getAudioContext();
                    const audioBuffer = await ctx.decodeAudioData(bytes.buffer.slice(0));
                    
                    const source = ctx.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(ctx.destination);
                    source.onended = playNext;
                    source.start(0);
                } catch (e) {
                    console.error('Playback error:', e);
                    playNext();
                }
            }
            
            // Scan for all unprocessed audio chunks
            function scanForAudio() {
                const container = document.getElementById('audio_data');
                if (!container) return;
                
                const chunks = container.querySelectorAll('.audio-chunk[data-chunk-id]');
                chunks.forEach(chunk => {
                    const chunkId = parseInt(chunk.getAttribute('data-chunk-id'), 10);
                    if (chunkId > lastProcessedChunkId) {
                        const audioData = chunk.getAttribute('data-audio');
                        if (audioData) {
                            lastProcessedChunkId = chunkId;
                            audioQueue.push({audioData, chunkId});
                            console.log('Queued chunk:', chunkId);
                        }
                    }
                });
                
                if (audioQueue.length > 0 && !isPlaying) {
                    playNext();
                }
            }
            
            // Watch for changes
            const observer = new MutationObserver(scanForAudio);
            
            function startObserver() {
                const target = document.getElementById('audio_data');
                if (target) {
                    observer.observe(target, {childList: true, subtree: true, characterData: true});
                    console.log('Audio observer started');
                    setInterval(scanForAudio, 50);
                } else {
                    setTimeout(startObserver, 100);
                }
            }
            
            document.addEventListener('click', () => getAudioContext(), {once: true});
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', startObserver);
            } else {
                startObserver();
            }
        })();
        </script>
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
