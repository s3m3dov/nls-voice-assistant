# Natural Language Systems - Voice Assistant Project

## Project Overview

This project implements a local voice assistant capable of providing weather information and managing calendar entries through spoken English input and output. The system processes all requests locally without relying on cloud-based models.

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
- **Endpoint**: `https://api.responsible-nlp.net/calendar.php`
- **Operations**:
  - **CREATE** (POST): Add new calendar entries
  - **READ** (GET): List all entries or get specific entry by ID
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

| Milestone | Description | Deadline |
|-----------|-------------|----------|
| **MS1** | Working ASR and TTS implementation | 14.11.2025 |
| **MS2** | Weather and Calendar API integration | 28.11.2025 |
| **MS3** | Functional voice assistant | 12.12.2025 |
| **MS4** | Final Docker container + evaluation report | 30.01.2025 |

## Project Structure

```
.
├── README.md
├── Dockerfile
├── pyproject.toml        # Poetry configuration
├── requirements.txt      # pip/uv requirements
├── src/
│   ├── asr/              # Automatic Speech Recognition
│   ├── tts/              # Text-to-Speech
│   ├── nlu/              # Natural Language Understanding
│   ├── dialogue/         # Dialogue Management
│   ├── api/              # API Integration (Weather & Calendar)
│   └── main.py           # Main application entry point
├── tests/                # Unit and integration tests
├── evaluation/           # Evaluation scripts and results
└── docs/                 # Additional documentation
```

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- Docker
- Git

### Installation

Choose one of the following package managers based on your preference:

#### Option 1: Using UV (Fastest & Recommended)

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

# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Activate the virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Run the application
python src/main.py
```

#### Option 2: Using Poetry

**Install Poetry**

<details>
<summary>macOS</summary>

**Via Homebrew (Recommended):**
```bash
brew install poetry
```

**Via Official Installer:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add Poetry to your PATH (add to `~/.zshrc` or `~/.bash_profile`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```
</details>

<details>
<summary>Linux</summary>

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add Poetry to your PATH (add to `~/.bashrc` or `~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```
</details>

<details>
<summary>Windows (PowerShell)</summary>

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Add Poetry to your PATH through System Environment Variables or add to PowerShell profile.
</details>

**Setup Project**

```bash
# Clone the repository
git clone https://github.com/s3m3dov/nls-voice-assistant.git
cd nls-voice-assistant

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Run the application
poetry run python src/main.py
```

#### Option 3: Using venv (Built-in)

<details>
<summary>macOS/Linux</summary>

```bash
# Clone the repository
git clone https://github.com/s3m3dov/nls-voice-assistant.git
cd nls-voice-assistant

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```
</details>

<details>
<summary>Windows (Command Prompt)</summary>

```cmd
# Clone the repository
git clone https://github.com/s3m3dov/nls-voice-assistant.git
cd nls-voice-assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```
</details>

<details>
<summary>Windows (PowerShell)</summary>

```powershell
# Clone the repository
git clone https://github.com/s3m3dov/nls-voice-assistant.git
cd nls-voice-assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment (may need to enable script execution first)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```
</details>

### Deactivating Virtual Environment

For all options, simply run:
```bash
deactivate
```

### Running the Application

#### Local Development
```bash
python src/main.py
```

#### Docker Container
```bash
# Build the Docker image
docker build -t nls-voice-assistant .

# Run the container
docker run -it nls-voice-assistant
```

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

## Troubleshooting

### Common Issues
- [To be added as issues arise]

## Resources

- [University of Marburg NLP Group](https://www.uni-marburg.de/)
- Project API Documentation: https://api.responsible-nlp.net/
- GitHub Repository: https://github.com/s3m3dov/nls-voice-assistant

## Contact

For questions regarding the project, contact:
- Course Instructor: Daniel Braun
- Teaching Assistant: Lucas Fonseca Lage
