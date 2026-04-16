"""
Speech-to-Text module using OpenAI Whisper.

Converts audio input to text with error handling and confidence scoring.
"""

import io
import os
from typing import Optional, Tuple
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

from jarvis.core.logging import get_logger

logger = get_logger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not installed. Install with: pip install openai-whisper")

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("Audio libraries not installed. Install with: pip install sounddevice soundfile")


@dataclass
class SpeechResult:
    """Result from speech-to-text conversion."""
    text: str
    confidence: float
    language: str
    duration: float


class SpeechToText:
    """
    Converts speech audio to text using OpenAI Whisper.
    
    Supports both file-based and streaming input.
    """
    
    def __init__(
        self,
        model_size: str = "base",
        language: Optional[str] = None,
        device: str = "cpu"
    ):
        """
        Initialize SpeechToText.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            language: Language code (e.g., "en" for English), auto-detect if None
            device: "cpu" or "cuda"
        """
        self.model_size = model_size
        self.language = language
        self.device = device
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        if WHISPER_AVAILABLE:
            self._load_model()
        else:
            logger.error("Whisper not available. Cannot initialize SpeechToText.")
    
    def _load_model(self) -> None:
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model ({self.model_size})...")
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def transcribe_file(self, audio_path: str) -> SpeechResult:
        """
        Transcribe audio from a file.
        
        Args:
            audio_path: Path to audio file (wav, mp3, m4a, etc.)
        
        Returns:
            SpeechResult with transcribed text and metadata
        """
        if not WHISPER_AVAILABLE or self.model is None:
            logger.error("Whisper model not available")
            return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
        
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
        
        try:
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._transcribe_sync,
                audio_path
            )
            return result
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
    
    def _transcribe_sync(self, audio_path: str) -> SpeechResult:
        """Synchronous transcription (runs in thread pool)."""
        try:
            result = self.model.transcribe(
                audio_path,
                language=self.language,
                verbose=False
            )
            
            text = result.get("text", "").strip()
            confidence = result.get("confidence", 0.0) if "confidence" in result else 0.8
            language = result.get("language", self.language or "unknown")
            duration = 0.0
            
            # Try to get audio duration
            try:
                import soundfile as sf
                with sf.SoundFile(audio_path) as f:
                    duration = len(f) / f.samplerate
            except Exception:
                pass
            
            logger.info(f"Transcribed: {text[:100]}... (confidence: {confidence:.2f})")
            
            return SpeechResult(
                text=text,
                confidence=confidence,
                language=language,
                duration=duration
            )
        except Exception as e:
            logger.error(f"Transcription sync failed: {e}")
            return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
    
    async def transcribe_buffer(
        self,
        audio_buffer: bytes,
        sample_rate: int = 16000
    ) -> SpeechResult:
        """
        Transcribe audio from bytes buffer.
        
        Args:
            audio_buffer: Raw audio bytes
            sample_rate: Sample rate of audio (default 16000 Hz)
        
        Returns:
            SpeechResult with transcribed text
        """
        if not WHISPER_AVAILABLE or self.model is None:
            logger.error("Whisper model not available")
            return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
        
        try:
            # Save buffer to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_buffer)
                tmp_path = tmp.name
            
            try:
                result = await self.transcribe_file(tmp_path)
                return result
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Buffer transcription failed: {e}")
            return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
    
    async def record_and_transcribe(
        self,
        duration: float = 5.0,
        sample_rate: int = 16000
    ) -> SpeechResult:
        """
        Record audio from microphone and transcribe.
        
        Args:
            duration: Recording duration in seconds
            sample_rate: Sample rate in Hz (default 16000)
        
        Returns:
            SpeechResult with transcribed text
        """
        if not AUDIO_AVAILABLE:
            logger.error("Audio libraries not available")
            return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
        
        try:
            logger.info(f"Recording for {duration} seconds...")
            
            # Record audio
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                self.executor,
                self._record_sync,
                duration,
                sample_rate
            )
            
            if audio_data is None:
                return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
            
            # Save and transcribe
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio_data, sample_rate)
                tmp_path = tmp.name
            
            try:
                result = await self.transcribe_file(tmp_path)
                return result
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Record and transcribe failed: {e}")
            return SpeechResult(text="", confidence=0.0, language="unknown", duration=0.0)
    
    def _record_sync(self, duration: float, sample_rate: int):
        """Synchronous recording (runs in thread pool)."""
        try:
            audio_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="float32"
            )
            sd.wait()
            return audio_data
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if SpeechToText is available."""
        return WHISPER_AVAILABLE and self.model is not None
