"""
JARVIS Core Engine

Main reasoning and execution loop that coordinates module execution.
Handles command parsing, intent detection, task breakdown, and orchestration.
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from jarvis.core.logging import get_logger

logger = get_logger(__name__)


class IntentType(Enum):
    """Types of intents the agent can handle."""
    CODING = "coding"
    RESEARCH = "research"
    TASK = "task"
    SELF_IMPROVEMENT = "self_improvement"
    UNKNOWN = "unknown"


@dataclass
class Command:
    """Represents a parsed user command."""
    raw_text: str
    intent: IntentType
    action: str
    parameters: Dict[str, Any]
    confidence: float


class CommandParser:
    """Parse natural language commands into structured tasks."""

    # Intent keywords mapping
    INTENT_KEYWORDS = {
        IntentType.CODING: ["build", "create", "code", "write", "develop", "implement", "fix", "debug"],
        IntentType.RESEARCH: ["research", "search", "find", "look up", "investigate", "analyze"],
        IntentType.TASK: ["execute", "run", "automate", "script", "workflow", "process"],
        IntentType.SELF_IMPROVEMENT: ["optimize", "improve", "refactor", "enhance", "analyze yourself"],
    }

    def parse(self, text: str) -> Command:
        """
        Parse raw user input into a structured command.
        
        Args:
            text: Raw user input
            
        Returns:
            Command object with parsed intent and parameters
        """
        logger.debug(f"Parsing command: {text}")
        
        text_lower = text.lower()
        
        # Detect intent
        intent = IntentType.UNKNOWN
        confidence = 0.0
        
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    intent = intent_type
                    confidence = 0.8
                    break
        
        # Extract action (simplified - just take first verb-like word after keywords)
        action = self._extract_action(text)
        
        # Extract parameters (simplified)
        parameters = self._extract_parameters(text)
        
        command = Command(
            raw_text=text,
            intent=intent,
            action=action,
            parameters=parameters,
            confidence=confidence
        )
        
        logger.log_decision(
            f"Intent detection: {intent.value}",
            f"Confidence: {confidence}",
            [IntentType.CODING, IntentType.RESEARCH, IntentType.TASK]
        )
        
        return command

    def _extract_action(self, text: str) -> str:
        """Extract primary action from text."""
        for intent_keywords in self.INTENT_KEYWORDS.values():
            for keyword in intent_keywords:
                if keyword in text.lower():
                    return keyword
        return "unknown"

    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract parameters from text (simplified)."""
        # This is a placeholder - real implementation would use NLP
        words = text.split()
        return {
            "raw_words": words,
            "word_count": len(words),
        }


class JarvisEngine:
    """
    Main JARVIS AI Agent Engine.
    
    Coordinates command parsing, intent detection, task planning, and execution.
    """

    def __init__(self):
        """Initialize the JARVIS engine."""
        self.parser = CommandParser()
        self.running = False
        self.modules = {}
        
        logger.info("JARVIS Engine initialized")

    async def initialize_modules(self, modules: Dict[str, Any]):
        """
        Initialize agent modules.
        
        Args:
            modules: Dictionary of module_name -> module_instance
        """
        self.modules = modules
        logger.info(f"Modules initialized: {list(modules.keys())}")

    async def execute_command(self, raw_command: str) -> Dict[str, Any]:
        """
        Execute a user command end-to-end.
        
        Args:
            raw_command: Raw user input
            
        Returns:
            Execution result with status, output, and metadata
        """
        start_time = time.time()
        
        logger.log_action("execute_command", {"command": raw_command})
        
        # Parse command
        command = self.parser.parse(raw_command)
        
        # Route to appropriate module based on intent
        result = await self._route_to_module(command)
        
        # Log performance
        duration_ms = (time.time() - start_time) * 1000
        logger.log_performance(
            f"command_execution:{command.intent.value}",
            duration_ms,
            result.get("success", False),
            {"action": command.action}
        )
        
        return result

    async def _route_to_module(self, command: Command) -> Dict[str, Any]:
        """Route command to appropriate module based on intent."""
        
        if command.intent == IntentType.CODING:
            if "coding_agent" in self.modules:
                return await self.modules["coding_agent"].execute(command)
            else:
                logger.warning("Coding agent not available")
                return {"success": False, "error": "Coding agent not initialized"}
                
        elif command.intent == IntentType.RESEARCH:
            if "research_agent" in self.modules:
                return await self.modules["research_agent"].execute(command)
            else:
                logger.warning("Research agent not available")
                return {"success": False, "error": "Research agent not initialized"}
                
        elif command.intent == IntentType.TASK:
            if "task_executor" in self.modules:
                return await self.modules["task_executor"].execute(command)
            else:
                logger.warning("Task executor not available")
                return {"success": False, "error": "Task executor not initialized"}
        
        else:
            logger.warning(f"Unknown intent: {command.intent}")
            return {"success": False, "error": f"Cannot handle intent: {command.intent}"}

    async def start_repl(self):
        """Start interactive REPL for agent interaction."""
        logger.info("Starting JARVIS REPL")
        self.running = True
        
        print("\n" + "="*60)
        print("JARVIS AI Agent - Interactive Mode")
        print("="*60)
        print("Type 'help' for commands, 'exit' to quit\n")
        
        while self.running:
            try:
                user_input = input("Jarvis> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == "exit":
                    self.running = False
                    logger.info("REPL shutdown requested")
                    print("Goodbye!")
                    break
                    
                if user_input.lower() == "help":
                    self._print_help()
                    continue
                
                # Execute command
                result = await self.execute_command(user_input)
                
                # Print result
                print("\n" + "-"*60)
                if result.get("success"):
                    print(f"✓ Success: {result.get('output', 'Command executed')}")
                else:
                    print(f"✗ Failed: {result.get('error', 'Unknown error')}")
                if "details" in result:
                    print(f"Details: {result['details']}")
                print("-"*60 + "\n")
                
            except KeyboardInterrupt:
                self.running = False
                logger.info("REPL interrupted by user")
                print("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"REPL error: {e}")
                print(f"Error: {e}\n")

    def _print_help(self):
        """Print help information."""
        help_text = """
Available Commands:
  Coding:     "build a Python API", "create a website", "write a test"
  Research:   "research machine learning", "find information about X"
  Tasks:      "run a deployment", "automate backup process"
  
Examples:
  > Jarvis, build a REST API with FastAPI
  > Research the latest trends in AI
  > Run daily backup script
  
Type 'exit' to quit
        """
        print(help_text)


async def main():
    """Main entry point for JARVIS."""
    engine = JarvisEngine()
    await engine.start_repl()


if __name__ == "__main__":
    asyncio.run(main())
