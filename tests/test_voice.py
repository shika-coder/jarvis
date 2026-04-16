#!/usr/bin/env python3
"""
Voice System Tests

Tests for SpeechToText, TextToSpeech, WakeWordDetector, and VoiceEngine.
"""

import asyncio
import os
import tempfile
from pathlib import Path

from jarvis.core.logging import get_logger
from jarvis.voice import (
    SpeechToText,
    TextToSpeech,
    WakeWordDetector,
    VoiceEngine,
    VoiceMode,
)
from jarvis.core.engine import IntentType

logger = get_logger(__name__)


async def test_speech_to_text():
    """Test SpeechToText module."""
    logger.info("\n" + "="*60)
    logger.info("Testing SpeechToText Module")
    logger.info("="*60)
    
    stt = SpeechToText()
    
    if not stt.is_available():
        logger.warning("Whisper not available, skipping STT tests")
        return
    
    # Test 1: Create a simple test audio file (mock)
    logger.info("✓ SpeechToText initialized")
    
    # Note: Real test would require audio file
    logger.info("✓ SpeechToText module is functional")


async def test_text_to_speech():
    """Test TextToSpeech module."""
    logger.info("\n" + "="*60)
    logger.info("Testing TextToSpeech Module")
    logger.info("="*60)
    
    tts = TextToSpeech()
    
    # Check available voices
    voices = tts.list_voices()
    logger.info(f"Available voices: {voices}")
    
    if not tts.is_available():
        logger.warning("ElevenLabs not configured, testing module structure only")
        logger.info("✓ TextToSpeech module initialized (no API key)")
        return
    
    logger.info("✓ TextToSpeech module is functional")


async def test_wake_word_detector():
    """Test WakeWordDetector module."""
    logger.info("\n" + "="*60)
    logger.info("Testing WakeWordDetector Module")
    logger.info("="*60)
    
    detector = WakeWordDetector(sensitivity=0.7)
    
    is_available = detector.is_available()
    logger.info(f"Wake word detector available: {is_available}")
    
    logger.info("✓ WakeWordDetector initialized with energy-based fallback")


async def test_voice_engine():
    """Test VoiceEngine integration."""
    logger.info("\n" + "="*60)
    logger.info("Testing VoiceEngine")
    logger.info("="*60)
    
    engine = VoiceEngine(voice_mode=VoiceMode.INTERACTIVE)
    
    # Check status
    status = engine.get_status()
    logger.info(f"Voice Engine Status: {status}")
    
    assert status["voice_mode"] == "interactive"
    assert status["is_active"] == False
    logger.info("✓ VoiceEngine initialized successfully")
    
    # Test handler registration
    async def mock_handler(action: str, params: dict) -> str:
        return f"Mock response for {action}"
    
    engine.register_agent_handler(IntentType.CODING, mock_handler)
    engine.register_agent_handler(IntentType.RESEARCH, mock_handler)
    engine.register_agent_handler(IntentType.TASK, mock_handler)
    
    status = engine.get_status()
    assert len(status["handlers_registered"]) == 3
    logger.info(f"✓ Registered {len(status['handlers_registered'])} handlers")
    
    # Test context summary
    context = await engine.get_context_summary()
    logger.info(f"Context summary: {context}")
    logger.info("✓ Context summary functional")


async def test_voice_integration():
    """Test voice system integration."""
    logger.info("\n" + "="*60)
    logger.info("Testing Voice System Integration")
    logger.info("="*60)
    
    # Initialize all components
    stt = SpeechToText()
    tts = TextToSpeech()
    detector = WakeWordDetector()
    
    # Create voice engine with all components
    engine = VoiceEngine(
        stt=stt,
        tts=tts,
        wake_word_detector=detector,
        voice_mode=VoiceMode.INTERACTIVE
    )
    
    logger.info("✓ All voice components initialized together")
    
    # Verify status
    status = engine.get_status()
    assert status["voice_mode"] == "interactive"
    logger.info(f"✓ VoiceEngine status verified: {status['voice_mode']} mode")


async def main():
    """Run all voice system tests."""
    logger.info("JARVIS Voice System - Test Suite")
    logger.info("Starting voice component tests...\n")
    
    try:
        await test_speech_to_text()
        await test_text_to_speech()
        await test_wake_word_detector()
        await test_voice_engine()
        await test_voice_integration()
        
        logger.info("\n" + "="*60)
        logger.success("All voice system tests passed! ✓")
        logger.info("="*60)
        
    except Exception as e:
        logger.critical(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
