"""
Wake-word detection module.

Detects the "Jarvis" wake word to activate voice input.
"""

import asyncio
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass
import time

from jarvis.core.logging import get_logger

logger = get_logger(__name__)

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    logger.warning("Porcupine not installed. Will use fallback energy-based detection.")

try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("Audio libraries not available for wake-word detection")


@dataclass
class WakeWordResult:
    """Result from wake-word detection."""
    detected: bool
    confidence: float
    timestamp: float
    audio_duration: float


class WakeWordDetector:
    """
    Detects wake word ("Jarvis") to activate voice input.
    
    Uses Porcupine if available, falls back to energy-based detection.
    """
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        sensitivity: float = 0.5,
        use_porcupine: bool = True
    ):
        """
        Initialize WakeWordDetector.
        
        Args:
            access_key: Porcupine access key (optional, for Porcupine mode)
            sensitivity: Detection sensitivity (0.0-1.0), higher = more sensitive
            use_porcupine: Whether to use Porcupine (if available)
        """
        self.access_key = access_key
        self.sensitivity = sensitivity
        self.use_porcupine = use_porcupine and PORCUPINE_AVAILABLE
        self.detector = None
        self.is_listening = False
        
        if self.use_porcupine:
            self._init_porcupine()
        else:
            logger.info("Using energy-based wake-word detection")
    
    def _init_porcupine(self) -> None:
        """Initialize Porcupine detector."""
        try:
            if self.access_key:
                self.detector = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=["jarvis"],
                    sensitivities=[self.sensitivity]
                )
                logger.info("Porcupine wake-word detector initialized")
            else:
                logger.warning("No Porcupine access key provided, falling back to energy detection")
                self.use_porcupine = False
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            self.use_porcupine = False
    
    async def listen_for_wake_word(
        self,
        timeout: float = 60.0,
        on_detected: Optional[Callable[[], Awaitable[None]]] = None
    ) -> WakeWordResult:
        """
        Listen for wake word.
        
        Args:
            timeout: Maximum listening duration in seconds
            on_detected: Optional callback when wake word is detected
        
        Returns:
            WakeWordResult with detection status
        """
        if not AUDIO_AVAILABLE:
            logger.error("Audio not available for wake-word detection")
            return WakeWordResult(
                detected=False,
                confidence=0.0,
                timestamp=time.time(),
                audio_duration=0.0
            )
        
        self.is_listening = True
        start_time = time.time()
        
        try:
            if self.use_porcupine and self.detector:
                result = await self._listen_porcupine(timeout, on_detected)
            else:
                result = await self._listen_energy_based(timeout, on_detected)
            
            return result
        except Exception as e:
            logger.error(f"Wake-word detection failed: {e}")
            return WakeWordResult(
                detected=False,
                confidence=0.0,
                timestamp=start_time,
                audio_duration=time.time() - start_time
            )
        finally:
            self.is_listening = False
    
    async def _listen_porcupine(
        self,
        timeout: float,
        on_detected: Optional[Callable[[], Awaitable[None]]]
    ) -> WakeWordResult:
        """Listen using Porcupine detector."""
        if not self.detector or not AUDIO_AVAILABLE:
            return WakeWordResult(detected=False, confidence=0.0, timestamp=time.time(), audio_duration=0.0)
        
        start_time = time.time()
        frame_length = self.detector.frame_length
        sample_rate = self.detector.sample_rate
        
        logger.info("Listening for 'Jarvis'...")
        
        loop = asyncio.get_event_loop()
        
        while (time.time() - start_time) < timeout:
            try:
                # Record frame
                audio_frame = await loop.run_in_executor(
                    None,
                    lambda: sd.rec(frame_length, samplerate=sample_rate, channels=1, dtype="int16").flatten()
                )
                sd.wait()
                
                # Check for wake word
                keyword_index = self.detector.process(audio_frame)
                
                if keyword_index >= 0:
                    logger.info("✓ Wake word detected!")
                    
                    if on_detected:
                        await on_detected()
                    
                    return WakeWordResult(
                        detected=True,
                        confidence=0.95,  # Porcupine doesn't provide confidence directly
                        timestamp=time.time(),
                        audio_duration=frame_length / sample_rate
                    )
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.debug(f"Error during Porcupine detection: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Wake-word detection timeout")
        return WakeWordResult(
            detected=False,
            confidence=0.0,
            timestamp=start_time,
            audio_duration=time.time() - start_time
        )
    
    async def _listen_energy_based(
        self,
        timeout: float,
        on_detected: Optional[Callable[[], Awaitable[None]]]
    ) -> WakeWordResult:
        """
        Fallback energy-based wake-word detection.
        
        Simple approach: listen for quiet, then loud sound (approximating speech patterns).
        """
        if not AUDIO_AVAILABLE:
            return WakeWordResult(detected=False, confidence=0.0, timestamp=time.time(), audio_duration=0.0)
        
        start_time = time.time()
        sample_rate = 16000
        frame_size = 2048
        
        logger.info("Listening for speech patterns (energy-based)...")
        
        loop = asyncio.get_event_loop()
        
        # Energy thresholds
        quiet_threshold = 100
        speech_threshold = 500
        
        silence_duration = 0
        
        while (time.time() - start_time) < timeout:
            try:
                # Record frame
                audio_frame = await loop.run_in_executor(
                    None,
                    lambda: sd.rec(frame_size, samplerate=sample_rate, channels=1, dtype="float32").flatten()
                )
                sd.wait()
                
                # Calculate energy
                energy = float(np.sum(np.abs(audio_frame)))
                
                if energy < quiet_threshold:
                    silence_duration += frame_size / sample_rate
                else:
                    silence_duration = 0
                
                # Detect speech pattern: quiet -> loud transition
                if silence_duration > 0.5 and energy > speech_threshold:
                    logger.info("✓ Speech detected!")
                    
                    if on_detected:
                        await on_detected()
                    
                    return WakeWordResult(
                        detected=True,
                        confidence=0.7,  # Lower confidence for energy-based
                        timestamp=time.time(),
                        audio_duration=frame_size / sample_rate
                    )
                
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.debug(f"Error during energy detection: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Wake-word detection timeout")
        return WakeWordResult(
            detected=False,
            confidence=0.0,
            timestamp=start_time,
            audio_duration=time.time() - start_time
        )
    
    def stop_listening(self) -> None:
        """Stop listening for wake word."""
        self.is_listening = False
        logger.info("Stopped listening for wake word")
    
    def is_available(self) -> bool:
        """Check if wake-word detection is available."""
        return AUDIO_AVAILABLE and (self.use_porcupine or True)  # Always available (falls back to energy)
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.detector:
            try:
                self.detector.delete()
            except Exception:
                pass
