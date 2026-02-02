# NLS Voice Assistant - Docker Image Quick Start

This guide is for users who have received the pre-built Docker image (`nls-voice-assistant_backup.tar`).

## Prerequisites

- **Docker** installed on your system
- The Docker image file: `nls-voice-assistant_backup.tar`

## Quick Start

### Step 1: Load the Docker Image

```bash
docker load -i nls-voice-assistant_backup.tar
```

This will import the pre-built image into your local Docker registry.

### Step 2: Verify the Image

```bash
docker images | grep nls-voice-assistant
```

You should see `nls-voice-assistant:backup` in the list.

### Step 3: Run the Voice Assistant

```bash
docker run --rm nls-voice-assistant:backup
```

That's it! The image includes everything needed:
- Ollama LLM server
- All required AI models
- The voice assistant application

### Accessing the Web UI

If running in web mode, open **http://localhost:7860** in your browser.

To explicitly run in web mode with port mapping:

```bash
docker run --rm -p 7860:7860 nls-voice-assistant:backup --mode web
```

## Features

The Voice Assistant supports:

- **Weather Queries**: "What will the weather be like today in Marburg?"
- **Calendar Management**: Create, read, update, and delete appointments
- **Context Awareness**: References to previous conversation turns
- **Voice Input/Output**: Speak naturally and receive spoken responses

## Run Modes

### Web UI Mode (Recommended)

```bash
docker run --rm -p 7860:7860 nls-voice-assistant:backup --mode web
```

Access via **http://localhost:7860**

### CLI Mode (No Audio Availability)

```bash
docker run --rm -it nls-voice-assistant:backup --mode cli
```

## Included Models

The Docker image comes pre-loaded with all required models:

| Model | Purpose |
|-------|---------|
| Whisper (small) | Speech-to-text (ASR) |
| Kokoro TTS | Text-to-speech |
| Silero VAD | Voice activity detection |
| qwen3-vl:4b-instruct | LLM (via Ollama) |

## Support

For issues or questions, please refer to the main project repository or contact the development team.
