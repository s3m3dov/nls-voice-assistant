# Natural Language Systems – Voice Assistant Project

## Project Overview

This project implements a local voice assistant capable of providing weather information and managing calendar entries
through spoken English input and output. The system processes all requests locally without relying on cloud-based
models.

## Team Members

- **Hikmat Samadov** - [@s3m3dov](https://github.com/s3m3dov)
- **Behzod Kamolov** - [@bekhkamolov](https://github.com/bekhkamolov)
- **Muhammad Nasir Sabir** - [@nasirsabir](https://github.com/nasirsabir)
- **Yelizaveta Utenko** - [@utenk0](https://github.com/utenk0)
- **Ali Amrahli** - [@aliamrahli](https://github.com/aliamrahli)

## Project Requirements

### Core Functionality

- **Speech Input/Output**: Accepts spoken English input and produces spoken English output
- **Conversation History**: Maintains context across multiple conversation turns
- **Local Processing**: All NLP processing occurs locally (no cloud models)
- **Weather Information**: Provides access to all weather API data through natural language
- **Calendar Management**: Supports full CRUD operations (Create, Read, Update, Delete) for calendar entries
- **Context Awareness**: Understands references to previous conversation turns

### API Integration

#### Weather API

- **Endpoint**: `https://api.responsible-nlp.net/weather.php`
- **Method**: POST
- **Parameter**: `place` (location name)
- **Response**: 7-day forecast including current day with temperature ranges and weather conditions

**Available Weather Conditions**:

- clear sky
- few clouds
- scattered clouds
- broken clouds
- shower rain
- rain
- thunderstorm
- snow
- mist

#### Calendar API

- **Endpoint**: `https://api.responsible-nlp.net/calendar.php?calenderid=xxx`
- **Important**: Replace `xxx` with a unique ID for your team. This ensures that teams do not interfere with each
  other's data.
- **Operations**:
  - **CREATE** (POST): Add new calendar entries
  - **READ** (GET): List all entries or get a specific entry by ID
  - **UPDATE** (PUT): Modify existing entries
  - **DELETE** (DELETE): Remove entries

### Example Commands

The system must handle commands such as:

- "What will the weather be like today in Marburg?"
- "What will the weather be on Friday in Frankfurt?"
- "Will it rain there on Saturday?"
- "Where is my next appointment?"
- "Add an appointment titled XYZ for the 12th of January."
- "Delete the previously created appointment."
- "Change the place for my appointment tomorrow."

## Project Milestones

| Milestone | Description                                | Deadline   |
|-----------|--------------------------------------------|------------|
| **MS1**   | Working ASR and TTS implementation         | 14.11.2025 |
| **MS2**   | Weather and Calendar API integration       | 28.11.2025 |
| **MS3**   | Functional voice assistant                 | 12.12.2025 |
| **MS4**   | Final Docker container + evaluation report | 30.01.2025 |

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- Docker
- Git

### Installation

This project uses `uv` for dependency management.

**Install UV**

<details>
<summary>macOS</summary>

**Via Homebrew (Recommended):**

```bash
brew install uv
```

**Via Official Installer:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</details>

<details>
<summary>Linux</summary>

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

</details>

<details>
<summary>Windows (PowerShell)</summary>

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

</details>

**Setup Project**

```bash
# Clone the repository
git clone https://github.com/s3m3dov/nls-voice-assistant.git
cd nls-voice-assistant

# Create virtual environment and install dependencies (from `uv.lock`)
uv sync

# Run the application (CLI mode is the default)
uv run python -m src.main --mode cli

# Run the application (Web UI via Gradio)
uv run python -m src.main --mode web
```

### Running the Application

#### Local Development

```bash
# CLI mode (default)
uv run python -m src.main --mode cli

# Web UI (Gradio)
uv run python -m src.main --mode web
# Then open http://localhost:7860
```

#### Docker Container

**Prerequisites**: Docker and Docker Compose installed.

**Quick Start with Docker Compose (Recommended)**:

```bash
# Build and start all services (voice assistant + Ollama LLM)
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f voice-assistant

# Stop all services
docker-compose down
```

> **Note**: First build takes ~10-15 minutes to download models (Whisper ASR, Kokoro TTS, Ollama LLM).
> **Access**: Open **http://localhost:7860** in your browser to use the Voice Assistant.

**Manual Docker Build**:

```bash
# Build the Docker image
docker build -t nls-voice-assistant .

# Run CLI mode (Default)
docker run -it --rm \
    -e OLLAMA_HOST=http://host.docker.internal:11434 \
    nls-voice-assistant

# Run Web UI mode
docker run -it --rm \
    -p 7860:7860 \
    -e OLLAMA_HOST=http://host.docker.internal:11434 \
    nls-voice-assistant --mode web
```

**What Gets Downloaded During Build**:

| Model | Size | Purpose |
|-------|------|---------|
| Whisper (small) | ~480MB | Speech-to-text |
| Kokoro TTS | ~350MB | Text-to-speech |
| Silero VAD | ~5MB | Voice activity detection |
| qwen2.5:7b-instruct | ~4.5GB | LLM (via Ollama) |

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Comment complex logic

### Testing

- Write unit tests for all components
- Test API integrations thoroughly
- Validate conversation flow with multiple test scenarios

### Version Control

- Create feature branches for new functionality
- Use descriptive commit messages
- Submit pull requests for code review before merging to main

## Components

### 1. Automatic Speech Recognition (ASR)

- Converts spoken input to text
- Must run locally (no cloud services)

### 2. Text-to-Speech (TTS)

- Converts system responses to spoken output
- Must run locally (no cloud services)

### 3. Natural Language Understanding (NLU)

- Extracts intent and entities from user input
- Handles weather queries and calendar commands

### 4. Dialogue Management

- Maintains conversation state
- Manages context and references to previous turns
- Coordinates between components

### 5. API Integration

- Weather API client
- Calendar API client with CRUD operations

## Evaluation

The final evaluation report (max 2 pages + title sheet) will include:

- System architecture description
- Evaluation methodology
- Performance metrics
- Results analysis
- Limitations and future improvements

## Resources

- [University of Marburg NLP Group](https://www.uni-marburg.de/)
- Project API Documentation: <https://api.responsible-nlp.net/>
- GitHub Repository: <https://github.com/s3m3dov/nls-voice-assistant>
