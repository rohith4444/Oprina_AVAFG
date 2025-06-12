"""
Text-to-Speech service for Oprina API.

This module provides text-to-speech capabilities using Google Cloud
Text-to-Speech API for converting text responses to audio.
"""

import base64
from typing import Optional, Dict, Any, List
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
    """Service for converting text to speech using Google Cloud Text-to-Speech."""
    
    def __init__(self):
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_client()
        
        # Default voice settings
        self.default_voice_settings = {
            "language_code": "en-US",
            "voice_name": "en-US-Neural2-F",  # Female neural voice
            "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE if GOOGLE_TTS_AVAILABLE else None,
            "audio_encoding": texttospeech.AudioEncoding.MP3 if GOOGLE_TTS_AVAILABLE else None,
            "speaking_rate": 1.0,
            "pitch": 0.0,
            "volume_gain_db": 0.0
        }
    
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
        voice_name: Optional[str] = None,
        language_code: Optional[str] = None,
        audio_encoding: str = "mp3",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0,
        use_ssml: bool = False
    ) -> Dict[str, Any]:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert to speech
            voice_name: Specific voice to use
            language_code: Language code for the voice
            audio_encoding: Output audio format (mp3, wav, ogg)
            speaking_rate: Speech rate (0.25 to 4.0)
            pitch: Voice pitch (-20.0 to 20.0)
            volume_gain_db: Volume gain (-96.0 to 16.0)
            use_ssml: Whether text contains SSML markup
            
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
            
            # Validate parameters
            speaking_rate = max(0.25, min(4.0, speaking_rate))
            pitch = max(-20.0, min(20.0, pitch))
            volume_gain_db = max(-96.0, min(16.0, volume_gain_db))
            
            # Set up synthesis input
            if use_ssml:
                synthesis_input = texttospeech.SynthesisInput(ssml=text)
            else:
                synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure voice
            voice_config = self._get_voice_config(
                voice_name or self.default_voice_settings["voice_name"],
                language_code or self.default_voice_settings["language_code"]
            )
            
            # Configure audio
            audio_config = texttospeech.AudioConfig(
                audio_encoding=self._get_audio_encoding(audio_encoding),
                speaking_rate=speaking_rate,
                pitch=pitch,
                volume_gain_db=volume_gain_db,
                effects_profile_id=["telephony-class-application"]  # Optimize for voice calls
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
            
            synthesis_result = {
                "success": True,
                "audio_content": audio_base64,
                "audio_format": audio_encoding,
                "audio_size": len(response.audio_content),
                "text_length": len(text),
                "voice_name": voice_name or self.default_voice_settings["voice_name"],
                "language_code": language_code or self.default_voice_settings["language_code"],
                "speaking_rate": speaking_rate,
                "pitch": pitch,
                "volume_gain_db": volume_gain_db,
                "service": "google_cloud_tts"
            }
            
            logger.info(f"Text-to-speech synthesis completed: {len(text)} chars -> {len(response.audio_content)} bytes")
            return synthesis_result
            
        except Exception as e:
            logger.error(f"Text-to-speech synthesis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_content": "",
                "audio_format": audio_encoding,
                "service": "google_cloud_tts"
            }
    
    async def synthesize_streaming(
        self,
        text_stream,
        voice_name: Optional[str] = None,
        language_code: Optional[str] = None,
        audio_encoding: str = "mp3"
    ):
        """
        Synthesize streaming text to speech.
        
        This is a placeholder for streaming synthesis.
        In production, this would handle real-time text streams.
        """
        # Placeholder implementation
        logger.warning("Streaming synthesis not yet implemented")
        yield {
            "success": False,
            "error": "Streaming synthesis not implemented",
            "audio_content": "",
            "is_final": False
        }
    
    def _get_voice_config(self, voice_name: str, language_code: str) -> 'texttospeech.VoiceSelectionParams':
        """Get voice configuration for synthesis."""
        # Determine gender from voice name
        gender = texttospeech.SsmlVoiceGender.FEMALE
        if any(indicator in voice_name.lower() for indicator in ['male', '-m-', 'man']):
            gender = texttospeech.SsmlVoiceGender.MALE
        elif any(indicator in voice_name.lower() for indicator in ['neutral', 'neut']):
            gender = texttospeech.SsmlVoiceGender.NEUTRAL
        
        return texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=gender
        )
    
    def _get_audio_encoding(self, audio_format: str) -> 'texttospeech.AudioEncoding':
        """Get audio encoding from format string."""
        format_mapping = {
            "mp3": texttospeech.AudioEncoding.MP3,
            "wav": texttospeech.AudioEncoding.LINEAR16,
            "ogg": texttospeech.AudioEncoding.OGG_OPUS,
            "mulaw": texttospeech.AudioEncoding.MULAW,
            "alaw": texttospeech.AudioEncoding.ALAW
        }
        
        return format_mapping.get(
            audio_format.lower(),
            texttospeech.AudioEncoding.MP3
        )
    
    async def _fallback_synthesis(self, text: str) -> Dict[str, Any]:
        """
        Fallback synthesis when Google Cloud TTS is not available.
        
        This could integrate with other TTS services or return a mock response.
        """
        logger.warning("Using fallback synthesis - Google Cloud TTS not available")
        
        # Mock response for development/testing
        return {
            "success": True,
            "audio_content": "",  # Empty audio content
            "audio_format": "mp3",
            "audio_size": 0,
            "text_length": len(text),
            "voice_name": "fallback-voice",
            "language_code": "en-US",
            "service": "fallback",
            "message": "TTS not available - please configure Google Cloud Text-to-Speech"
        }
    
    async def get_available_voices(self, language_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        if not self.client:
            return await self._get_fallback_voices()
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self.client.list_voices,
                {"language_code": language_code} if language_code else {}
            )
            
            voices = []
            for voice in response.voices:
                voice_info = {
                    "name": voice.name,
                    "language_codes": list(voice.language_codes),
                    "gender": voice.ssml_gender.name,
                    "natural_sample_rate": voice.natural_sample_rate_hertz
                }
                voices.append(voice_info)
            
            return voices
            
        except Exception as e:
            logger.error(f"Failed to get available voices: {str(e)}")
            return await self._get_fallback_voices()
    
    async def _get_fallback_voices(self) -> List[Dict[str, Any]]:
        """Get fallback voice list when service is not available."""
        return [
            {
                "name": "en-US-Neural2-F",
                "language_codes": ["en-US"],
                "gender": "FEMALE",
                "natural_sample_rate": 24000
            },
            {
                "name": "en-US-Neural2-M",
                "language_codes": ["en-US"],
                "gender": "MALE",
                "natural_sample_rate": 24000
            }
        ]
    
    async def validate_voice(self, voice_name: str, language_code: str) -> bool:
        """Validate if a voice is available for the given language."""
        voices = await self.get_available_voices(language_code)
        return any(
            voice["name"] == voice_name and language_code in voice["language_codes"]
            for voice in voices
        )
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        voices = await self.get_available_voices()
        languages = set()
        for voice in voices:
            languages.update(voice["language_codes"])
        return sorted(list(languages))
    
    def is_available(self) -> bool:
        """Check if the text-to-speech service is available."""
        return self.client is not None
    
    async def estimate_audio_duration(self, text: str, speaking_rate: float = 1.0) -> float:
        """Estimate audio duration for given text."""
        # Rough estimation: average speaking rate is about 150 words per minute
        words = len(text.split())
        base_duration = (words / 150) * 60  # seconds
        adjusted_duration = base_duration / speaking_rate
        return max(0.1, adjusted_duration)  # Minimum 0.1 seconds
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
