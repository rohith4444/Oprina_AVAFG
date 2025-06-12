"""
Speech-to-Text service for Oprina API.

This module provides speech recognition capabilities using Google Cloud
Speech-to-Text API for converting audio input to text.
"""

import base64
import io
from typing import Optional, Dict, Any, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from google.cloud import speech
    from google.cloud.speech import RecognitionConfig, RecognitionAudio
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False

from app.config import get_settings
from app.utils.errors import ValidationError, OprinaError
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SpeechToTextService:
    """Service for converting speech audio to text using Google Cloud Speech-to-Text."""
    
    def __init__(self):
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Cloud Speech client."""
        if not GOOGLE_SPEECH_AVAILABLE:
            logger.warning("Google Cloud Speech library not available")
            return
        
        try:
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech-to-Text client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Speech-to-Text client: {str(e)}")
            self.client = None
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "webm",
        sample_rate: int = 16000,
        language_code: str = "en-US",
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, mp3, etc.)
            sample_rate: Audio sample rate in Hz
            language_code: Language code for recognition
            enable_automatic_punctuation: Whether to add punctuation
            enable_word_time_offsets: Whether to include word timing
            
        Returns:
            Dictionary with transcription results
        """
        if not self.client:
            return await self._fallback_transcription(audio_data)
        
        try:
            # Validate audio data
            if not audio_data or len(audio_data) == 0:
                raise ValidationError("Audio data is empty")
            
            if len(audio_data) > 10 * 1024 * 1024:  # 10MB limit
                raise ValidationError("Audio file too large (max 10MB)")
            
            # Configure recognition settings
            config = RecognitionConfig(
                encoding=self._get_encoding_from_format(audio_format),
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                enable_automatic_punctuation=enable_automatic_punctuation,
                enable_word_time_offsets=enable_word_time_offsets,
                model="latest_long",  # Use latest model for better accuracy
                use_enhanced=True,    # Use enhanced model if available
            )
            
            # Create audio object
            audio = RecognitionAudio(content=audio_data)
            
            # Perform transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self.client.recognize,
                config,
                audio
            )
            
            # Process results
            results = []
            for result in response.results:
                alternative = result.alternatives[0]
                
                result_data = {
                    "transcript": alternative.transcript,
                    "confidence": alternative.confidence,
                    "is_final": True
                }
                
                # Add word timing if requested
                if enable_word_time_offsets and alternative.words:
                    result_data["words"] = [
                        {
                            "word": word.word,
                            "start_time": word.start_time.total_seconds(),
                            "end_time": word.end_time.total_seconds()
                        }
                        for word in alternative.words
                    ]
                
                results.append(result_data)
            
            # Return transcription results
            transcription_result = {
                "success": True,
                "results": results,
                "language_code": language_code,
                "audio_duration": self._estimate_audio_duration(audio_data, sample_rate),
                "service": "google_cloud_speech"
            }
            
            if results:
                # Get the best result
                best_result = max(results, key=lambda x: x.get("confidence", 0))
                transcription_result["transcript"] = best_result["transcript"]
                transcription_result["confidence"] = best_result["confidence"]
            else:
                transcription_result["transcript"] = ""
                transcription_result["confidence"] = 0.0
            
            logger.info(f"Speech transcription completed: {len(results)} results")
            return transcription_result
            
        except Exception as e:
            logger.error(f"Speech transcription failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "transcript": "",
                "confidence": 0.0,
                "service": "google_cloud_speech"
            }
    
    async def transcribe_streaming(
        self,
        audio_stream,
        audio_format: str = "webm",
        sample_rate: int = 16000,
        language_code: str = "en-US"
    ):
        """
        Transcribe streaming audio data.
        
        This is a placeholder for streaming transcription.
        In production, this would handle real-time audio streams.
        """
        # Placeholder implementation
        logger.warning("Streaming transcription not yet implemented")
        yield {
            "success": False,
            "error": "Streaming transcription not implemented",
            "transcript": "",
            "is_final": False
        }
    
    def _get_encoding_from_format(self, audio_format: str) -> speech.RecognitionConfig.AudioEncoding:
        """Get Google Cloud Speech encoding from audio format."""
        format_mapping = {
            "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "mp3": speech.RecognitionConfig.AudioEncoding.MP3,
            "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
            "webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            "ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        }
        
        return format_mapping.get(
            audio_format.lower(),
            speech.RecognitionConfig.AudioEncoding.LINEAR16
        )
    
    def _estimate_audio_duration(self, audio_data: bytes, sample_rate: int) -> float:
        """Estimate audio duration in seconds."""
        # This is a rough estimation
        # In production, you'd use proper audio analysis
        bytes_per_sample = 2  # 16-bit audio
        channels = 1  # Mono
        duration = len(audio_data) / (sample_rate * bytes_per_sample * channels)
        return max(0.1, duration)  # Minimum 0.1 seconds
    
    async def _fallback_transcription(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Fallback transcription when Google Cloud Speech is not available.
        
        This could integrate with other speech services or return a mock response.
        """
        logger.warning("Using fallback transcription - Google Cloud Speech not available")
        
        # Mock response for development/testing
        return {
            "success": True,
            "transcript": "[Speech transcription not available - please configure Google Cloud Speech]",
            "confidence": 0.0,
            "results": [],
            "service": "fallback",
            "audio_duration": self._estimate_audio_duration(audio_data, 16000)
        }
    
    def is_available(self) -> bool:
        """Check if the speech-to-text service is available."""
        return self.client is not None
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        # Common language codes supported by Google Cloud Speech
        return [
            "en-US", "en-GB", "en-AU", "en-CA", "en-IN",
            "es-ES", "es-US", "fr-FR", "fr-CA", "de-DE",
            "it-IT", "pt-BR", "pt-PT", "ru-RU", "ja-JP",
            "ko-KR", "zh-CN", "zh-TW", "ar-SA", "hi-IN"
        ]
    
    async def validate_audio_format(self, audio_format: str) -> bool:
        """Validate if the audio format is supported."""
        supported_formats = ["wav", "mp3", "flac", "webm", "ogg"]
        return audio_format.lower() in supported_formats
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
