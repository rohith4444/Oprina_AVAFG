"""
Simplified Speech-to-Text service for Oprina API.

This module provides basic speech recognition capabilities using ElevenLabs
Speech-to-Text API for converting audio input to text.
"""

import base64
import io
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

# try:
#     from google.cloud import speech
#     from google.cloud.speech import RecognitionConfig, RecognitionAudio
#     GOOGLE_SPEECH_AVAILABLE = True
# except ImportError:
#     GOOGLE_SPEECH_AVAILABLE = False

# New with Eleven Lab
try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

from app.config import get_settings
from app.utils.errors import ValidationError, OprinaError
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SpeechToTextService:
    """Simplified service for converting speech audio to text using ElevenLabs Speech-to-Text."""
    
    def __init__(self):
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_client()
    
    # def _initialize_client(self):
    #     """Initialize the Google Cloud Speech client."""
    #     if not GOOGLE_SPEECH_AVAILABLE:
    #         logger.warning("Google Cloud Speech library not available")
    #         return
        
    #     try:
    #         self.client = speech.SpeechClient()
    #         logger.info("Google Cloud Speech-to-Text client initialized")
    #     except Exception as e:
    #         logger.error(f"Failed to initialize Speech-to-Text client: {str(e)}")
    #         self.client = None
    
    # New Eleven Labs
    def _initialize_client(self):
        """Initialize the ElevenLabs Speech-to-Text client."""
        if not ELEVENLABS_AVAILABLE:
            logger.warning("ElevenLabs library not available")
            return
        
        try:
            if not settings.ELEVENLABS_API_KEY:
                raise ValueError("ELEVENLABS_API_KEY not configured")
            
            self.client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
            logger.info("ElevenLabs Speech-to-Text client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs STT client: {str(e)}")
            self.client = None
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "webm"
    ) -> Dict[str, Any]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, mp3, etc.)
            
        Returns:
            Dictionary with transcription results
        """
        if not self.client:
            return await self._fallback_transcription(audio_data)
        
        try:
            # Validate audio data
            if not audio_data or len(audio_data) == 0:
                raise ValidationError("Audio data is empty")
            
            # if len(audio_data) > 10 * 1024 * 1024:  # 10MB limit
            if len(audio_data) > 25 * 1024 * 1024:  # 25MB limit (ElevenLabs max)
                raise ValidationError("Audio file too large (max 25MB)")
            
            # FIXED: Dynamic configuration based on audio format
            # config_params = {
            #     "encoding": self._get_encoding_from_format(audio_format),
            #     "language_code": "en-US",
            #     "enable_automatic_punctuation": True,
            #     "model": "latest_long",
            #     "use_enhanced": True,
            # }
            
            # Only specify sample rate for non-WebM formats
            # WebM OPUS should auto-detect sample rate to avoid mismatch
            # if audio_format.lower() not in ["webm", "ogg"]:
            #     config_params["sample_rate_hertz"] = 16000
            
            # config = RecognitionConfig(**config_params)
            
            # Create audio object
            # audio = RecognitionAudio(content=audio_data)
            
            # FIXED: Perform transcription with correct API call format
            # loop = asyncio.get_event_loop()
            # response = await loop.run_in_executor(
            #     self.executor,
            #     lambda: self.client.recognize(request={"config": config, "audio": audio})
            # )
            
            # # Process results - simplified
            # if response.results:
            #     best_result = response.results[0].alternatives[0]
            #     return {
            #         "success": True,
            #         "transcript": best_result.transcript,
            #         "confidence": best_result.confidence,
            #         "language_code": "en-US",
            #         "service": "google_cloud_speech"
            #     }
            # else:
            #     return {
            #         "success": True,
            #         "transcript": "",
            #         "confidence": 0.0,
            #         "language_code": "en-US",
            #         "service": "google_cloud_speech"
            #     }
            
            
            # Perform transcription using ElevenLabs
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                lambda: self.client.speech_to_text.convert(
                    file=audio_data,
                    model_id="scribe_v1"  # ElevenLabs STT model
                )
            )

            # Process results
            if response and hasattr(response, 'text') and response.text:
                return {
                    "success": True,
                    "transcript": response.text,
                    "confidence": 1.0,  # ElevenLabs doesn't provide confidence scores
                    "language_code": "en-US",
                    "service": "elevenlabs_stt"
                }
            else:
                return {
                    "success": True,
                    "transcript": "",
                    "confidence": 0.0,
                    "language_code": "en-US",
                    "service": "elevenlabs_stt"
                }
            
        except Exception as e:
            logger.error(f"Speech transcription failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "transcript": "",
                "confidence": 0.0,
                "service": "elevenlabs_stt"
            }
            
    # Not needed for Eleven Labs    
    # def _get_encoding_from_format(self, audio_format: str) -> speech.RecognitionConfig.AudioEncoding:
    #     """Get Google Cloud Speech encoding from audio format."""
    #     format_mapping = {
    #         "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
    #         "mp3": speech.RecognitionConfig.AudioEncoding.MP3,
    #         "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
    #         "webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
    #         "ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
    #     }
        
    #     return format_mapping.get(
    #         audio_format.lower(),
    #         speech.RecognitionConfig.AudioEncoding.LINEAR16
    #     )
    
    async def _fallback_transcription(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Fallback transcription when ElevenLabs Speech is not available.
        """
        logger.warning("Using fallback transcription - ElevenLabs Speech not available")
        
        return {
            "success": True,
            "transcript": "[Speech transcription not available - please configure ElevenLabs STT]",
            "confidence": 0.0,
            "service": "elevenlabs_stt_fallback"
        }
    
    def is_available(self) -> bool:
        """Check if the speech-to-text service is available."""
        return self.client is not None
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)