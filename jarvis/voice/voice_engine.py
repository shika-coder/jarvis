"""
Voice Engine - Coordinates voice interaction pipeline.

Manages the flow: Audio Input → STT → Intent Detection → Agent Execution → TTS → Audio Output
"""

import asyncio
from typing import Optional, Callable, Awaitable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from jarvis.core.logging import get_logger
from jarvis.core.engine import CommandParser, IntentType
from jarvis.voice.speech_to_text import SpeechToText, SpeechResult
from jarvis.voice.text_to_speech import TextToSpeech, TTSResult
from jarvis.voice.wake_word import WakeWordDetector, WakeWordResult
from jarvis.memory import VectorMemory

logger = get_logger(__name__)


class VoiceMode(Enum):
    """Voice interaction modes."""
    INTERACTIVE = "interactive"  # Single command
    CONTINUOUS = "continuous"  # Continuous listening with wake word
    OFFLINE = "offline"  # No TTS output


@dataclass
class VoiceCommand:
    """Represents a voice command with all processing stages."""
    raw_audio: str  # Source (file path or "microphone")
    speech_text: str
    intent: IntentType
    action: str
    parameters: Dict[str, Any]
    response: str
    confidence: float
    processing_time: float


class VoiceEngine:
    """
    Coordinates voice-based interaction pipeline.
    
    Manages speech-to-text, intent detection, agent execution, and text-to-speech.
    """
    
    def __init__(
        self,
        stt: Optional[SpeechToText] = None,
        tts: Optional[TextToSpeech] = None,
        wake_word_detector: Optional[WakeWordDetector] = None,
        memory: Optional[VectorMemory] = None,
        enable_wake_word: bool = True,
        voice_mode: VoiceMode = VoiceMode.INTERACTIVE
    ):
        """
        Initialize VoiceEngine.
        
        Args:
            stt: SpeechToText instance (creates default if not provided)
            tts: TextToSpeech instance (creates default if not provided)
            wake_word_detector: WakeWordDetector instance (creates default if not provided)
            memory: VectorMemory instance for context awareness
            enable_wake_word: Whether to use wake-word detection
            voice_mode: Voice interaction mode
        """
        self.stt = stt or SpeechToText()
        self.tts = tts or TextToSpeech()
        self.wake_word_detector = wake_word_detector or WakeWordDetector()
        self.memory = memory or VectorMemory()
        self.command_parser = CommandParser()
        
        self.enable_wake_word = (
            enable_wake_word 
            and self.wake_word_detector is not None 
            and self.wake_word_detector.is_available()
        )
        self.voice_mode = voice_mode
        self.is_active = False
        
        self.agent_handlers: Dict[IntentType, Callable[[str, Dict[str, Any]], Awaitable[str]]] = {}
        
        logger.info(f"VoiceEngine initialized (mode: {voice_mode.value}, wake-word: {self.enable_wake_word})")
    
    def register_agent_handler(
        self,
        intent: IntentType,
        handler: Callable[[str, Dict[str, Any]], Awaitable[str]]
    ) -> None:
        """
        Register a handler for a specific intent type.
        
        Args:
            intent: Intent type to handle
            handler: Async function that takes (action, parameters) and returns response text
        """
        self.agent_handlers[intent] = handler
        logger.info(f"Registered handler for intent: {intent.value}")
    
    async def process_voice_command(
        self,
        audio_source: str = "microphone",
        duration: float = 5.0,
        play_response: bool = True
    ) -> Optional[VoiceCommand]:
        """
        Process a complete voice command from audio to response.
        
        Args:
            audio_source: "microphone" or path to audio file
            duration: Recording duration in seconds (for microphone input)
            play_response: Whether to play TTS response
        
        Returns:
            VoiceCommand with all processing details, or None on error
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Processing voice command from: {audio_source}")
            
            # Step 1: Speech-to-Text
            logger.debug("Step 1: Converting speech to text...")
            if audio_source == "microphone":
                speech_result = await self.stt.record_and_transcribe(duration=duration)
            else:
                speech_result = await self.stt.transcribe_file(audio_source)
            
            if not speech_result.text:
                logger.warning("No speech detected")
                return None
            
            logger.info(f"Transcribed: {speech_result.text}")
            
            # Step 2: Intent Detection
            logger.debug("Step 2: Detecting intent...")
            command = self.command_parser.parse(speech_result.text)
            
            # Step 3: Store in memory
            logger.debug("Step 3: Storing command in memory...")
            await self.memory.add_memory(
                content=speech_result.text,
                category="command",
                metadata={
                    "intent": command.intent.value,
                    "action": command.action,
                    "confidence": command.confidence,
                }
            )
            
            # Step 4: Execute Agent
            logger.debug("Step 4: Executing agent...")
            response = await self._execute_agent(command.intent, command.action, command.parameters)
            
            # Step 5: Text-to-Speech
            logger.debug("Step 5: Converting response to speech...")
            if play_response and self.tts.is_available():
                await self.tts.synthesize(response, play=True)
            
            # Store response in memory
            await self.memory.add_memory(
                content=response,
                category="response",
                metadata={
                    "command_id": command.raw_text[:50],
                    "intent": command.intent.value,
                }
            )
            
            processing_time = time.time() - start_time
            
            voice_command = VoiceCommand(
                raw_audio=audio_source,
                speech_text=speech_result.text,
                intent=command.intent,
                action=command.action,
                parameters=command.parameters,
                response=response,
                confidence=command.confidence,
                processing_time=processing_time
            )
            
            logger.info(f"Voice command processed in {processing_time:.2f}s")
            return voice_command
        
        except Exception as e:
            logger.error(f"Voice command processing failed: {e}")
            return None
    
    async def _execute_agent(
        self,
        intent: IntentType,
        action: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Execute the appropriate agent handler.
        
        Args:
            intent: Intent type
            action: Action to perform
            parameters: Action parameters
        
        Returns:
            Response string
        """
        if intent not in self.agent_handlers:
            return f"I don't have a handler for {intent.value} intents yet."
        
        try:
            handler = self.agent_handlers[intent]
            response = await handler(action, parameters)
            return response
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return f"An error occurred while processing your request: {str(e)}"
    
    async def listen_and_respond(
        self,
        timeout: float = 60.0,
        max_iterations: int = 5,
        on_command: Optional[Callable[[VoiceCommand], Awaitable[None]]] = None
    ) -> None:
        """
        Continuous voice listening mode.
        
        Args:
            timeout: Total timeout for listening session
            max_iterations: Maximum commands to process
            on_command: Optional callback for each processed command
        """
        self.is_active = True
        iterations = 0
        
        logger.info("Starting voice listening mode...")
        
        try:
            while self.is_active and iterations < max_iterations:
                try:
                    if self.enable_wake_word:
                        logger.info("Listening for wake word...")
                        wake_result = await self.wake_word_detector.listen_for_wake_word(
                            timeout=timeout,
                            on_detected=self._on_wake_word_detected
                        )
                        
                        if not wake_result.detected:
                            logger.info("Wake word detection timed out")
                            break
                    
                    # Process command
                    voice_command = await self.process_voice_command(
                        audio_source="microphone",
                        duration=5.0,
                        play_response=True
                    )
                    
                    if voice_command and on_command:
                        await on_command(voice_command)
                    
                    iterations += 1
                    
                except Exception as e:
                    logger.error(f"Error in listen loop: {e}")
                    continue
        
        finally:
            self.is_active = False
            logger.info("Voice listening mode ended")
    
    async def _on_wake_word_detected(self) -> None:
        """Callback when wake word is detected."""
        logger.info("✓ Wake word detected! Ready for command...")
        try:
            # Play a subtle sound or TTS indication
            await self.tts.synthesize("I'm listening", play=True)
        except Exception:
            pass  # Silent if TTS fails
    
    def stop_listening(self) -> None:
        """Stop listening for voice commands."""
        self.is_active = False
        if self.wake_word_detector:
            self.wake_word_detector.stop_listening()
        logger.info("Stopped listening for voice commands")
    
    async def get_context_summary(self, num_memories: int = 5) -> str:
        """
        Get a summary of recent conversation context.
        
        Args:
            num_memories: Number of recent memories to include
        
        Returns:
            Context summary string
        """
        try:
            recent = await self.memory.list_memories(limit=num_memories)
            
            if not recent:
                return "No recent context available."
            
            summary_parts = []
            for mem in recent:
                summary_parts.append(f"- {mem.content[:100]}...")
            
            return "Recent context:\n" + "\n".join(summary_parts)
        except Exception as e:
            logger.error(f"Failed to get context summary: {e}")
            return "Could not retrieve context."
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of voice engine."""
        return {
            "is_active": self.is_active,
            "voice_mode": self.voice_mode.value,
            "wake_word_enabled": self.enable_wake_word,
            "stt_available": self.stt.is_available(),
            "tts_available": self.tts.is_available(),
            "memory_available": self.memory.is_available(),
            "memory_stats": self.memory.get_stats(),
            "handlers_registered": list(self.agent_handlers.keys()),
        }
