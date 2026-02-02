# NLS Voice Assistant

This guide is for users who have received the pre-built Docker image (`nls-voice-assistant_backup.tar`).

## Prerequisites

- **Docker** installed on your system
- The Docker image file: `nls-voice-assistant_backup.tar`

## Quick Start

### Step 1: Load the Docker Image

```bash
docker load -i nls-stack-images.tar
```

This will import the pre-built image into your local Docker registry.

Verify the Image:

```bash
docker images | grep -E "nls-voice-assistant|ollama"
```

You should see `nls-voice-assistant:backup` in the list.

### Step 2: Create a Docker network

```bash
docker network create nls-net
```

### Step 3: Run Ollama

```bash
docker run -d \
  --name nls-ollama \
  --network nls-net \
  -p 11434:11434 \
  ollama/ollama:latest
```

To verify:

```bash
curl http://localhost:11434/api/tags
```

Pull the model:

```bash
docker exec -it nls-ollama ollama pull qwen3-vl:4b-instruct
```


### Step 4: Run the assistant system

```bash
docker run -d \
  --name nls-voice-assistant \
  --network nls-net \
  -p 7860:7860 \
  -e OLLAMA_BASE_URL=http://nls-ollama:11434 \
  nls-voice-assistant-voice-assistant:latest
```


### Step 5: Access the Web UI

Open **http://localhost:7860** in your browser.

Note: Monitor loading process in docker, the initial request may take longer.
Additional Note: First 2-3 requests via gradio may not reach the back-end because of initialization.

## Included Models

The Docker image comes pre-loaded with all required models:

| Model | Purpose |
|-------|---------|
| Whisper (small) | Speech-to-text (ASR) |
| Kokoro TTS | Text-to-speech |
| Silero VAD | Voice activity detection |
| qwen3-vl:4b-instruct | LLM (via Ollama) |
