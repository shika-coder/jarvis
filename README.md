# JARVIS AI Agent

Autonomous AI agent designed to build and evolve a system similar to JARVIS, with voice interaction and semantic memory.

## Core Capabilities

- **Coding Agent**: Create, edit, debug and deploy full-stack applications
- **Research Agent**: Search the web and extract actionable insights
- **Task Executor**: Run scripts, automate workflows, and control local environment
- **Voice System**: Speech-to-text (Whisper), Text-to-speech (ElevenLabs), Wake-word detection
- **Vector Memory**: Semantic memory storage with FAISS for intelligent retrieval
- **Logging System**: Comprehensive logging of all actions and decisions
- **Memory System**: Store user preferences, past projects, and learned improvements
- **CLI + Voice Interface**: Natural language command parsing in text or speech

## Quick Start

### Prerequisites

- Python 3.10+
- pip or poetry

### Installation

```bash
pip install -e .
```

### Running JARVIS

```bash
# CLI mode (default)
python -m jarvis.main

# Voice mode (requires API keys)
python -m jarvis.main --voice
```

**CLI Mode** - Try commands like:
```
Jarvis> build a Python REST API with FastAPI
Jarvis> research machine learning trends
Jarvis> run daily backup script
```

**Voice Mode** - Say commands after wake word:
```
"Jarvis, build a web application"
"Jarvis, research AI safety"
"Jarvis, execute backup"
```

## Project Structure

```
jarvis/
├── core/                     # Core engine, logging, and utilities
│   ├── engine.py            # Main reasoning and execution loop
│   ├── logging.py           # Comprehensive logging system
│   └── __init__.py
├── modules/                  # Agent modules
│   ├── coding_agent.py       # Coding tasks
│   ├── research_agent.py     # Research and web search
│   ├── task_executor.py      # Task execution and automation
│   └── __init__.py
├── memory/                   # Memory system
│   ├── memory.py             # Short-term and long-term memory (JSON)
│   ├── vector_memory.py      # Vector-based semantic memory (FAISS)
│   └── __init__.py
├── voice/                    # Voice system (Phase 2) ✅
│   ├── speech_to_text.py     # Whisper-based STT
│   ├── text_to_speech.py     # ElevenLabs-based TTS
│   ├── wake_word.py          # Wake-word detection
│   ├── voice_engine.py       # Voice pipeline orchestration
│   └── __init__.py
├── self_improvement/         # Self-improvement system (Phase 3)
│   └── __init__.py
├── main.py                   # Entry point with CLI/voice modes
├── __init__.py
├── tests/                    # Test suite
│   ├── test_voice.py         # Voice system tests
│   ├── test_memory.py        # Memory system tests
│   └── __init__.py
└── logs/                     # Log files
```

## Phases

### Phase 1 (MVP) - ✅ Complete

✅ CLI-based agent  
✅ Basic command parsing  
✅ Coding + research + task execution  
✅ Comprehensive logging  
✅ JSON-based memory system  
✅ Git workflow established  

### Phase 2 (Voice & Memory) - ✅ Complete

✅ **Speech-to-Text**: OpenAI Whisper integration for audio transcription  
✅ **Text-to-Speech**: ElevenLabs integration with 8+ voice options  
✅ **Wake-word Detection**: "Jarvis" detection with fallback energy-based method  
✅ **Voice Engine**: Orchestrates STT → Intent → Agent → TTS pipeline  
✅ **Vector Memory**: FAISS-based semantic memory with JSON fallback  
✅ **CLI/Voice Integration**: Seamless switching between modes  
✅ **Comprehensive Tests**: Voice and memory system test suites  

### Phase 3 - Planned

- [ ] Self-improvement module
- [ ] Advanced automation workflows
- [ ] Deployment abilities
- [ ] Multi-agent coordination

### Phase 4 (Advanced) - Planned

- [ ] Multi-agent system
- [ ] Web UI/Dashboard
- [ ] Real-time monitoring
- [ ] Distributed execution

## Voice System (Phase 2)

### Installation

Voice features require additional dependencies:

```bash
# Install voice support
pip install -e ".[voice]"

# Install ML features (for vector memory with embeddings)
pip install -e ".[ml]"
```

### Configuration

Set up environment variables for voice features:

```bash
# For ElevenLabs TTS
export ELEVENLABS_API_KEY=your_api_key_here

# For Porcupine wake-word detection (optional, uses fallback if not set)
export PORCUPINE_ACCESS_KEY=your_access_key_here

# For OpenAI (if using Whisper API)
export OPENAI_API_KEY=your_key_here
```

### Voice Components

#### 1. **SpeechToText** (Whisper)
Converts audio input to text using OpenAI Whisper.

```python
from jarvis.voice import SpeechToText

stt = SpeechToText(model_size="base")

# From microphone
result = await stt.record_and_transcribe(duration=5.0)
print(f"Transcribed: {result.text}")

# From file
result = await stt.transcribe_file("audio.wav")
```

**Features:**
- Multiple model sizes (tiny, base, small, medium, large)
- Language detection and specification
- Error handling with confidence scores
- Async streaming support

#### 2. **TextToSpeech** (ElevenLabs)
Converts text to natural-sounding speech.

```python
from jarvis.voice import TextToSpeech

tts = TextToSpeech()

# Synthesize and play
result = await tts.synthesize("Hello, how can I help?", play=True)

# Save to file
await tts.save_to_file("Hello world", "output.wav")

# Available voices
print(tts.list_voices())  # ['bella', 'anton', 'domi', ...]
```

**Features:**
- 8+ pre-configured voices
- Custom voice IDs support
- Stream audio playback
- File saving

#### 3. **WakeWordDetector**
Detects "Jarvis" wake word using Porcupine or energy-based fallback.

```python
from jarvis.voice import WakeWordDetector

detector = WakeWordDetector(sensitivity=0.5)

# Listen for wake word (with timeout)
result = await detector.listen_for_wake_word(timeout=60.0)
if result.detected:
    print("Wake word detected!")
```

**Features:**
- Porcupine-based detection (accurate)
- Energy-based fallback (no extra dependencies)
- Configurable sensitivity
- Async continuous listening

#### 4. **VoiceEngine**
Orchestrates the complete voice pipeline: Audio → STT → Intent → Agent → TTS

```python
from jarvis.voice import VoiceEngine, VoiceMode
from jarvis.core.engine import IntentType

engine = VoiceEngine(voice_mode=VoiceMode.INTERACTIVE)

# Register agent handlers
async def handle_coding(action: str, params: dict) -> str:
    return "Building your application..."

engine.register_agent_handler(IntentType.CODING, handle_coding)

# Process a voice command
result = await engine.process_voice_command(
    audio_source="microphone",
    play_response=True
)
```

### Vector Memory (FAISS)

Semantic memory with intelligent retrieval:

```python
from jarvis.memory import VectorMemory

memory = VectorMemory()

# Add memory
mem_id = await memory.add_memory(
    content="Python is great for data science",
    category="programming",
    metadata={"language": "python"}
)

# Semantic search
results = await memory.search("data analysis libraries", top_k=5)
for mem, similarity in results:
    print(f"{mem.content} (similarity: {similarity:.2f})")

# Category operations
all_programming = await memory.list_memories(category="programming")
await memory.clear_category("old_notes")
```

**Features:**
- FAISS index for efficient similarity search
- JSON fallback when embeddings unavailable
- Category filtering
- Metadata support
- Persistent storage

### Running Tests

```bash
# Test voice components
python tests/test_voice.py

# Test memory system
python tests/test_memory.py

# Run with pytest
pytest tests/ -v
```

### Code Style

```bash
# Format code
black jarvis/

# Sort imports
isort jarvis/

# Lint code
ruff check jarvis/

# Type checking
mypy jarvis/
```

## Architecture Principles

1. **Modularity**: Every feature is a separate service/module
2. **Scalability**: Design for growth from day one
3. **Logging**: Log every action and decision
4. **Safety**: Confirm before destructive operations
5. **Continuous Improvement**: Evaluate performance and suggest improvements

## Git Workflow

- `main`: Stable, production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes
- `refactor/*`: Code improvements

Commit messages follow the format:
- `feat: description`
- `fix: description`
- `refactor: description`
- `docs: description`
- `chore: description`

## Logging

JARVIS maintains comprehensive logs in the `logs/` directory:

- `jarvis-YYYY-MM-DD.log`: All operations
- `jarvis-critical-YYYY-MM-DD.log`: Errors and critical events

Logs rotate automatically based on file size.

## Configuration

Configuration via environment variables. See `.env.example` for examples:

```bash
# Core
OPENAI_API_KEY=your_key_here
LOG_LEVEL=INFO

# Voice System (Phase 2)
ELEVENLABS_API_KEY=your_key_here  # For TTS
PORCUPINE_ACCESS_KEY=your_key_here  # For wake-word detection (optional)
```

## License

MIT

## Contact

JARVIS AI Team
