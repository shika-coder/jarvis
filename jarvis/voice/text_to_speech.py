"""
Text-to-Speech module using ElevenLabs API.

Converts text to natural-sounding speech audio.
"""

import os
import asyncio
from typing import Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from jarvis.core.logging import get_logger

logger = get_logger(__name__)

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logger.warning("ElevenLabs not installed. Install with: pip install elevenlabs")

try:
    import sounddevice as sd
    AUDIO_OUTPUT_AVAILABLE = True
except ImportError:
    AUDIO_OUTPUT_AVAILABLE = False
    logger.warning("sounddevice not installed. Install with: pip install sounddevice")


@dataclass
class TTSResult:
    """Result from text-to-speech conversion."""
    audio_bytes: Optional[bytes]
    duration: float
    voice_id: str
    text_length: int


class TextToSpeech:
    """
    Converts text to speech using ElevenLabs API.
    
    Supports multiple voices and streaming output.
    """
    
    # Popular ElevenLabs voices
    VOICES = {
        "bella": "EXAVITQu4vr4xnSDxMaL",
        "anton": "ErXwobaYp3GgG7XlIEAw",
        "domi": "AZnzlk1XvdBFFXlLabor",
        "elli": "MF3mGyEYCHltNTjGPEKE",
        "josh": "TxGEqnHWrfWFTfGW9XjX",
        "arnold": "VR6AewLVsfNuhwMmRjzb",
        "adam": "pNInz6obpgDQGcFmaJgB",
        "sam": "yoZ06aMxZJJ28mfd3POQ",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice: str = "bella",
        model: str = "eleven_monolingual_v1"
    ):
        """
        Initialize TextToSpeech.
        
        Args:
            api_key: ElevenLabs API key (uses ELEVENLABS_API_KEY env var if not provided)
            voice: Voice name or ID (see VOICES dict for presets)
            model: ElevenLabs model ID
        """
        self.voice = voice
        self.model = model
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        
        if ELEVENLABS_AVAILABLE and self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
            logger.info(f"ElevenLabs initialized with voice: {voice}")
        else:
            if not ELEVENLABS_AVAILABLE:
                logger.error("ElevenLabs not available")
            if not self.api_key:
                logger.warning("No ElevenLabs API key found. Set ELEVENLABS_API_KEY env var.")
            self.client = None
    
    def _get_voice_id(self, voice: str) -> str:
        """Get voice ID from name or return as-is if already an ID."""
        return self.VOICES.get(voice.lower(), voice)
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        play: bool = False
    ) -> TTSResult:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to convert to speech
            voice: Optional voice override
            play: Whether to play audio immediately
        
        Returns:
            TTSResult with audio bytes and metadata
        """
        if not ELEVENLABS_AVAILABLE or self.client is None:
            logger.error("ElevenLabs not available")
            return TTSResult(audio_bytes=None, duration=0.0, voice_id="", text_length=len(text))
        
        try:
            selected_voice = voice or self.voice
            voice_id = self._get_voice_id(selected_voice)
            
            logger.info(f"Synthesizing: {text[:100]}... (voice: {selected_voice})")
            
            # Run synthesis in thread pool
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(
                self.executor,
                self._synthesize_sync,
                text,
                voice_id
            )
            
            if audio_bytes is None:
                return TTSResult(audio_bytes=None, duration=0.0, voice_id=voice_id, text_length=len(text))
            
            # Estimate duration (rough: ~100ms per word)
            estimated_duration = len(text.split()) * 0.1
            
            result = TTSResult(
                audio_bytes=audio_bytes,
                duration=estimated_duration,
                voice_id=voice_id,
                text_length=len(text)
            )
            
            # Play if requested
            if play and AUDIO_OUTPUT_AVAILABLE:
                await self.play_audio(audio_bytes)
            
            logger.info(f"Synthesis complete ({len(audio_bytes)} bytes)")
            return result
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return TTSResult(audio_bytes=None, duration=0.0, voice_id="", text_length=len(text))
    
    def _synthesize_sync(self, text: str, voice_id: str) -> Optional[bytes]:
        """Synchronous synthesis (runs in thread pool)."""
        try:
            if not self.client:
                logger.error("ElevenLabs client not initialized")
                return None
            
            # Use the correct ElevenLabs API
            audio_bytes = self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id=self.model
            )
            
            # Convert to bytes if needed
            if isinstance(audio_bytes, bytes):
                return audio_bytes
            else:
                # If it's a generator/iterator, consume it
                return b"".join(audio_bytes)
        except Exception as e:
            logger.error(f"Synthesis sync failed: {e}")
            return None
    
    async def play_audio(self, audio_bytes: bytes) -> None:
        """
        Play audio bytes using system audio output.
        
        Args:
            audio_bytes: Audio data in WAV format
        """
        if not AUDIO_OUTPUT_AVAILABLE:
            logger.warning("Audio output not available")
            return
        
        try:
            import soundfile as sf
            import numpy as np
            from io import BytesIO
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._play_audio_sync,
                audio_bytes
            )
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
    
    def _play_audio_sync(self, audio_bytes: bytes) -> None:
        """Synchronous audio playback (runs in thread pool)."""
        try:
            import soundfile as sf
            from io import BytesIO
            
            # Read WAV from bytes
            with BytesIO(audio_bytes) as buffer:
                data, samplerate = sf.read(buffer)
                
                # Play audio
                sd.play(data, samplerate)
                sd.wait()
                logger.info("Audio playback complete")
        except Exception as e:
            logger.error(f"Audio playback sync failed: {e}")
    
    async def save_to_file(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None
    ) -> bool:
        """
        Synthesize text and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file (should be .wav or .mp3)
            voice: Optional voice override
        
        Returns:
            True if successful, False otherwise
        """
        result = await self.synthesize(text, voice)
        
        if result.audio_bytes is None:
            logger.error("Synthesis failed, cannot save file")
            return False
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(result.audio_bytes)
            logger.info(f"Audio saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if TextToSpeech is available."""
        return ELEVENLABS_AVAILABLE and self.client is not None
    
    def list_voices(self) -> list:
        """List available voice presets."""
        return list(self.VOICES.keys())
