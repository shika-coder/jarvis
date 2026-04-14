#!/usr/bin/env python3
"""
JARVIS AI Agent - Main Entry Point

Interactive CLI for the JARVIS autonomous AI agent.
Usage: python -m jarvis.main
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

logger = get_logger(__name__)


async def main():
    """Main entry point for JARVIS."""
    
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
        
        # Register modules with engine
        await engine.initialize_modules(modules)
        
        logger.success("JARVIS initialized successfully")
        
        # Start REPL
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
