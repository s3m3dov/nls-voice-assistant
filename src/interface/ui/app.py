"""Gradio Web UI for the Voice Assistant."""

import os
import tempfile
from typing import Generator

# Disable Gradio analytics/telemetry
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr

# Monkey-patch to fix Gradio's JSON schema parsing bug
# This prevents the TypeError in gradio_client.utils.json_schema_to_python_type
def _patched_get_api_info(self):
    """Patched version that returns minimal API info to avoid schema parsing errors."""
    return {"named_endpoints": {}, "unnamed_endpoints": {}}

# Apply the patch before creating any Gradio blocks
gr.Blocks.get_api_info = _patched_get_api_info
import numpy as np
import soundfile as sf
import torch

from src.assistant import VoiceAssistant
from src.logger import logger, setup_logging
from src.interface.ui.config import UISettings

# Global instances (initialized once)
assistant: VoiceAssistant | None = None
ui_settings = UISettings()


def initialize_models() -> None:
    """Initialize ASR and TTS models (called once at startup)."""
    global assistant

    logger.info("Initializing Voice Assistant...")
    assistant = VoiceAssistant()
    assistant.initialize()


def process_audio(
    audio: tuple[int, np.ndarray] | None,
    history: list,
) -> Generator[tuple[list, str | None], None, None]:
    """
    Process audio input and generate response.

    Args:
        audio: Tuple of (sample_rate, audio_data) from Gradio microphone
        history: Conversation history as list of message dicts

    Yields:
        Tuple of (updated_history, audio_path or None)
    """
    if audio is None:
        yield history, None
        return

    if assistant is None or not assistant.is_initialized():
        yield history + [(None, "Models not initialized. Please wait...")], None
        return

    sample_rate, audio_data = audio

    # Convert to float32 and normalize
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 2147483648.0

    # Handle stereo audio - convert to mono
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    # Resample to 16kHz if needed (Whisper expects 16kHz)
    target_sample_rate = 16000
    if sample_rate != target_sample_rate:
        import librosa
        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=target_sample_rate)

    # Convert to torch tensor
    audio_tensor = torch.from_numpy(audio_data).float()

    # Transcribe
    user_input = assistant.transcribe_audio(audio_tensor)

    if not user_input or user_input.strip() == "":
        yield history + [(None, "Could not transcribe. Please try again.")], None
        return

    # Add user message to history
    history = history + [(user_input, None)]
    yield history, None

    # Get streaming LLM response
    full_response = ""

    for chunk in assistant.get_response_stream(user_input):
        full_response += chunk
        # Update history with partial response - update last tuple
        updated_history = history[:-1] + [(user_input, full_response)]
        yield updated_history, None

    # Generate TTS audio for full response
    try:
        samples, sample_rate = assistant.synthesize_speech(full_response)
        # Save as temporary file for Gradio to play
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, samples, sample_rate)
            yield history[:-1] + [(user_input, full_response)], f.name
    except ValueError:
        # No valid text to synthesize
        yield history[:-1] + [(user_input, full_response)], None


def process_text(
    text_input: str,
    history: list,
) -> Generator[tuple[list, str | None, str], None, None]:
    """
    Process text input and generate response.

    Args:
        text_input: User's text message
        history: Conversation history as list of message dicts

    Yields:
        Tuple of (updated_history, audio_path or None, empty string for text box)
    """
    if not text_input or text_input.strip() == "":
        yield history, None, ""
        return

    if assistant is None or not assistant.is_initialized():
        yield history + [(None, " Models not initialized.")], None, ""
        return

    # Add user message to history
    history = history + [(text_input, None)]
    yield history, None, ""

    # Get streaming LLM response
    full_response = ""
    for chunk in assistant.get_response_stream(text_input):
        full_response += chunk
        updated_history = history[:-1] + [(text_input, full_response)]
        yield updated_history, None, ""

    # Generate TTS audio
    try:
        samples, sample_rate = assistant.synthesize_speech(full_response)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, samples, sample_rate)
            yield history[:-1] + [(text_input, full_response)], f.name, ""
    except ValueError:
        # No valid text to synthesize
        yield history[:-1] + [(text_input, full_response)], None, ""


def clear_conversation() -> tuple[list, None]:
    """Clear conversation history."""
    if assistant is not None:
        assistant.reset_conversation()
    return [], None


def create_ui() -> gr.Blocks:
    """Create the Gradio UI."""
    with gr.Blocks(
        title=ui_settings.title,
        theme=gr.themes.Soft(),
        css="""
        .chatbot { min-height: 400px; }
        .audio-input { margin-bottom: 10px; }
        """
    ) as demo:
        gr.Markdown(
            """
            # Voice Assistant
            
            **Speak or type** to interact with the assistant. It can help you with:
            - Weather information for any location
            - Calendar management (create, view, update, delete events)
            - General questions and conversations
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    elem_classes=["chatbot"],
                    bubble_full_width=False,
                )

                with gr.Row():
                    with gr.Column(scale=4):
                        text_input = gr.Textbox(
                            placeholder="Type a message or use the microphone...",
                            show_label=False,
                            container=False,
                        )
                    with gr.Column(scale=1, min_width=100):
                        send_btn = gr.Button("Send", variant="primary")

                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="numpy",
                    label="Click to record",
                    elem_classes=["audio-input"],
                )

            with gr.Column(scale=1):
                gr.Markdown("### Response Audio")
                audio_output = gr.Audio(
                    label="Assistant's Response",
                    autoplay=True,
                    type="filepath",
                )
                clear_btn = gr.Button("🗑Clear Chat", variant="secondary")

        # Event handlers
        audio_input.stop_recording(
            fn=process_audio,
            inputs=[audio_input, chatbot],
            outputs=[chatbot, audio_output],
        )

        text_input.submit(
            fn=process_text,
            inputs=[text_input, chatbot],
            outputs=[chatbot, audio_output, text_input],
        )

        send_btn.click(
            fn=process_text,
            inputs=[text_input, chatbot],
            outputs=[chatbot, audio_output, text_input],
        )

        clear_btn.click(
            fn=clear_conversation,
            outputs=[chatbot, audio_output],
        )

    return demo


def run() -> None:
    """Initialize models and launch the Gradio UI."""
    setup_logging()
    logger.info("Starting Voice Assistant Web UI...")

    initialize_models()

    demo = create_ui()
    demo.launch(
        server_name=ui_settings.host,
        server_port=ui_settings.port,
        share=ui_settings.share,
        show_api=False,  # Disable API docs to avoid JSON schema parsing errors
    )


if __name__ == "__main__":
    run()
