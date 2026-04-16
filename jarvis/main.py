#!/usr/bin/env python3
"""
JARVIS AI Agent - Main Entry Point

Interactive CLI for the JARVIS autonomous AI agent.
Supports both CLI and voice modes.
Usage: python -m jarvis.main [--voice]
"""

import asyncio
import sys
from pathlib import Path

from jarvis.core.logging import get_logger
from jarvis.core.engine import JarvisEngine
from jarvis.modules.coding_agent import CodingAgent
from jarvis.modules.research_agent import ResearchAgent
from jarvis.modules.task_executor import TaskExecutor
from jarvis.memory.memory import Memory
from jarvis.voice import VoiceEngine, VoiceMode

logger = get_logger(__name__)


async def run_voice_mode(engine: JarvisEngine, voice_engine: VoiceEngine) -> None:
    """Run JARVIS in voice interaction mode."""
    logger.info("="*60)
    logger.info("JARVIS Voice Mode")
    logger.info("="*60)
    print("\nVoice mode active. Say 'Jarvis' followed by your command.")
    print("Type 'help' for voice commands, 'exit' to return to CLI\n")
    
    # Register agent handlers
    async def handle_coding(action: str, params: dict) -> str:
        result = await engine.execute_command(f"build {action}")
        return result.get("output", "Coding task executed")
    
    async def handle_research(action: str, params: dict) -> str:
        result = await engine.execute_command(f"research {action}")
        return result.get("output", "Research completed")
    
    async def handle_task(action: str, params: dict) -> str:
        result = await engine.execute_command(f"execute {action}")
        return result.get("output", "Task executed")
    
    from jarvis.core.engine import IntentType
    voice_engine.register_agent_handler(IntentType.CODING, handle_coding)
    voice_engine.register_agent_handler(IntentType.RESEARCH, handle_research)
    voice_engine.register_agent_handler(IntentType.TASK, handle_task)
    
    try:
        # Run in interactive voice mode (single commands)
        while True:
            user_input = input("Voice> ").strip().lower()
            
            if user_input == "exit":
                print("Returning to CLI mode...")
                break
            elif user_input == "help":
                print("""
Voice Commands:
  "Jarvis, build a Python API"
  "Jarvis, research machine learning"
  "Jarvis, run backup"
  "voice status" - Show voice engine status
  "exit" - Return to CLI mode
                """)
            elif user_input == "voice status":
                status = voice_engine.get_status()
                print(f"\nVoice Engine Status:")
                print(f"  Active: {status['is_active']}")
                print(f"  STT Available: {status['stt_available']}")
                print(f"  TTS Available: {status['tts_available']}")
                print(f"  Wake Word: {status['wake_word_enabled']}\n")
            else:
                print("Voice mode: Use 'voice file:/path/to/audio' to process audio, or 'exit' to return to CLI")
    except KeyboardInterrupt:
        print("\nReturning to CLI mode...")


async def main():
    """Main entry point for JARVIS."""
    
    # Parse command line arguments
    voice_mode = "--voice" in sys.argv or "-v" in sys.argv
    
    logger.info("="*60)
    logger.info("JARVIS AI Agent - Initializing")
    logger.info("="*60)
    
    try:
        # Initialize engine
        engine = JarvisEngine()
        
        # Initialize modules
        workspace = Path.cwd()
        modules = {
            "coding_agent": CodingAgent(workspace),
            "research_agent": ResearchAgent(),
            "task_executor": TaskExecutor(workspace),
        }
        
        # Initialize research agent async session
        await modules["research_agent"].initialize()
        
        # Initialize memory system
        memory = Memory()
        
        # Initialize voice engine
        voice_engine = VoiceEngine(voice_mode=VoiceMode.INTERACTIVE)
        
        # Register modules with engine
        await engine.initialize_modules(modules)
        
        logger.success("JARVIS initialized successfully")
        
        # Start in appropriate mode
        if voice_mode:
            await run_voice_mode(engine, voice_engine)
        
        # Start REPL (CLI mode or after voice mode)
        await engine.start_repl()
        
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Initialization failed: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if modules and "research_agent" in modules:
            await modules["research_agent"].cleanup()
        logger.info("JARVIS shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
