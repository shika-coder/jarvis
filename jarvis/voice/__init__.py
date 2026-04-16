"""
JARVIS Voice System (Phase 2)

Speech-to-Text and Text-to-Speech integration with wake-word detection.
"""

from jarvis.voice.speech_to_text import SpeechToText, SpeechResult
from jarvis.voice.text_to_speech import TextToSpeech, TTSResult
from jarvis.voice.wake_word import WakeWordDetector, WakeWordResult

__all__ = [
    "SpeechToText",
    "SpeechResult",
    "TextToSpeech",
    "TTSResult",
    "WakeWordDetector",
    "WakeWordResult",
]
