# JARVIS AI Agent

Autonomous coding AI agent designed to build and evolve a system similar to JARVIS.

## Core Capabilities

- **Coding Agent**: Create, edit, debug and deploy full-stack applications
- **Research Agent**: Search the web and extract actionable insights
- **Task Executor**: Run scripts, automate workflows, and control local environment
- **Logging System**: Comprehensive logging of all actions and decisions
- **Memory System**: Store user preferences, past projects, and learned improvements
- **CLI Interface**: Natural language command parsing and interactive REPL

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
python -m jarvis.main
```

This will start the interactive REPL. Try commands like:

```
Jarvis> build a Python REST API with FastAPI
Jarvis> research machine learning trends
Jarvis> run daily backup script
```

## Project Structure

```
jarvis/
├── core/                 # Core engine, logging, and utilities
│   ├── engine.py        # Main reasoning and execution loop
│   ├── logging.py       # Comprehensive logging system
│   └── __init__.py
├── modules/              # Agent modules
│   ├── coding_agent.py   # Coding tasks
│   ├── research_agent.py # Research and web search
│   ├── task_executor.py  # Task execution and automation
│   └── __init__.py
├── memory/               # Memory system
│   ├── memory.py         # Short-term and long-term memory
│   └── __init__.py
├── voice/                # Voice system (Phase 2)
│   └── __init__.py
├── self_improvement/     # Self-improvement system (Phase 3)
│   └── __init__.py
├── main.py              # Entry point
└── __init__.py
```

## Phase 1 (MVP) - Current

✅ CLI-based agent  
✅ Basic command parsing  
✅ Simple coding + research + task execution ability  
✅ Comprehensive logging  
✅ Memory system (JSON-based)  

## Phase 2 - Planned

- [ ] Voice integration (Whisper + ElevenLabs)
- [ ] Vector database for memory
- [ ] Enhanced module capabilities

## Phase 3 - Planned

- [ ] Self-improvement system
- [ ] Advanced automation workflows
- [ ] Deployment abilities

## Phase 4 (Advanced) - Planned

- [ ] Multi-agent system
- [ ] Web UI/Dashboard
- [ ] Real-time monitoring

## Development

### Running Tests

```bash
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

Configuration via environment variables (see `.env.example`):

```
OPENAI_API_KEY=your_key_here
LOG_LEVEL=INFO
```

## License

MIT

## Contact

JARVIS AI Team
