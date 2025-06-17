"""
Speech services integration package for Oprina API.

This package provides speech-to-text and text-to-speech capabilities
for voice interaction with the AI agent.
"""

from .speech_to_text import SpeechToTextService
from .text_to_speech import TextToSpeechService

__all__ = [
    "SpeechToTextService",
    "TextToSpeechService"
]
