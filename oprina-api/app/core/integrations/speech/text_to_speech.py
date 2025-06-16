"""
Simplified Text-to-Speech service for Oprina API.

This module provides basic text-to-speech capabilities using Google Cloud
Text-to-Speech API for converting text responses to audio.
"""

import base64
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False

from app.config import get_settings
from app.utils.errors import ValidationError, OprinaError
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TextToSpeechService:
    """Simplified service for converting text to speech using Google Cloud Text-to-Speech."""
    
    def __init__(self):
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Cloud Text-to-Speech client."""
        if not GOOGLE_TTS_AVAILABLE:
            logger.warning("Google Cloud Text-to-Speech library not available")
            return
        
        try:
            self.client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud Text-to-Speech client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Text-to-Speech client: {str(e)}")
            self.client = None
    
    async def synthesize_speech(
        self,
        text: str,
        speaking_rate: float = 1.0
    ) -> Dict[str, Any]:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert to speech
            speaking_rate: Speech rate (0.25 to 4.0)
            
        Returns:
            Dictionary with audio data and metadata
        """
        if not self.client:
            return await self._fallback_synthesis(text)
        
        try:
            # Validate input
            if not text or len(text.strip()) == 0:
                raise ValidationError("Text is empty")
            
            if len(text) > 5000:  # Google TTS limit
                raise ValidationError("Text too long (max 5000 characters)")
            
            # Validate speaking rate
            speaking_rate = max(0.25, min(4.0, speaking_rate))
            
            # Simple synthesis input - no SSML
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Fixed voice configuration - hardcoded defaults
            voice_config = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Neural2-F",  # Fixed female voice
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            
            # Simple audio configuration - fixed defaults
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate
            )
            
            # Perform synthesis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self.client.synthesize_speech,
                {
                    "input": synthesis_input,
                    "voice": voice_config,
                    "audio_config": audio_config
                }
            )
            
            # Encode audio data
            audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
            
            return {
                "success": True,
                "audio_content": audio_base64,
                "audio_format": "mp3",
                "audio_size": len(response.audio_content),
                "text_length": len(text),
                "voice_name": "en-US-Neural2-F",
                "speaking_rate": speaking_rate,
                "service": "google_cloud_tts"
            }
            
        except Exception as e:
            logger.error(f"Text-to-speech synthesis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_content": "",
                "audio_format": "mp3",
                "service": "google_cloud_tts"
            }
    
    async def _fallback_synthesis(self, text: str) -> Dict[str, Any]:
        """
        Fallback synthesis when Google Cloud TTS is not available.
        """
        logger.warning("Using fallback synthesis - Google Cloud TTS not available")
        
        return {
            "success": True,
            "audio_content": "",  # Empty audio content
            "audio_format": "mp3",
            "audio_size": 0,
            "text_length": len(text),
            "voice_name": "fallback-voice",
            "service": "fallback",
            "message": "TTS not available - please configure Google Cloud Text-to-Speech"
        }
    
    def is_available(self) -> bool:
        """Check if the text-to-speech service is available."""
        return self.client is not None
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)