# syntax=docker/dockerfile:1
# ============================================================================
# Multi-stage Dockerfile for NLS Voice Assistant
# ============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and download models
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python -r pyproject.toml

# Download Kokoro TTS model files
RUN mkdir -p /app/models && \
    curl -L -o /app/models/kokoro-v1.0.onnx \
    https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx && \
    curl -L -o /app/models/voices-v1.0.bin \
    https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

# Pre-download Faster-Whisper model to cache it in the image
RUN /app/.venv/bin/python -c "\
from faster_whisper import WhisperModel; \
WhisperModel('small', device='cpu', compute_type='int8'); \
print('Faster-Whisper small model downloaded successfully')"

# Pre-download Silero VAD model
RUN /app/.venv/bin/python -c "\
import torch; \
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False); \
print('Silero VAD downloaded successfully')"


# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal image for running the application
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Audio libraries \
    portaudio19-dev \
    libsndfile1 \
    libasound2-dev \
    # For Whisper audio processing \
    ffmpeg \
    # For alternative TTS (pyttsx3) \
    espeak-ng \
    libespeak-ng1 \
    # For spaCy \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy pre-downloaded models from builder
COPY --from=builder /app/models/kokoro-v1.0.onnx /app/kokoro-v1.0.onnx
COPY --from=builder /app/models/voices-v1.0.bin /app/voices-v1.0.bin
COPY --from=builder /root/.cache /root/.cache

# Copy application source code
COPY src/ /app/src/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

# Ollama host - connects to the ollama service in docker-compose
ENV OLLAMA_HOST=http://ollama:11434

# Expose Web UI port
EXPOSE 7860

# Default command
CMD ["python", "src/main.py"]
