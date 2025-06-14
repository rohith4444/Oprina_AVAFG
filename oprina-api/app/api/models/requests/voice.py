"""
Voice request models for Oprina API.

This module defines Pydantic models for voice-related API requests.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class VoiceMessageRequest(BaseModel):
    """Request model for processing voice messages."""
    
    session_id: str = Field(
        ...,
        description="Chat session identifier",
        min_length=1,
        max_length=100
    )
    
    audio_format: str = Field(
        default="webm",
        description="Audio format (webm, wav, mp3, etc.)"
    )
    
    sample_rate: int = Field(
        default=16000,
        description="Audio sample rate in Hz",
        ge=8000,
        le=48000
    )
    
    include_audio_response: bool = Field(
        default=True,
        description="Whether to generate audio response"
    )
    
    voice_settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Voice synthesis settings"
    )
    
    @validator('audio_format')
    def validate_audio_format(cls, v):
        """Validate audio format."""
        supported_formats = ["webm", "wav", "mp3", "flac", "ogg"]
        if v.lower() not in supported_formats:
            raise ValueError(f"Audio format must be one of: {', '.join(supported_formats)}")
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "audio_format": "webm",
                "sample_rate": 16000,
                "include_audio_response": True,
                "voice_settings": {
                    "language_code": "en-US",
                    "voice_name": "en-US-Neural2-F",
                    "speaking_rate": 1.0
                }
            }
        }


class TranscriptionRequest(BaseModel):
    """Request model for audio transcription."""
    
    audio_format: str = Field(
        default="webm",
        description="Audio format (webm, wav, mp3, etc.)"
    )
    
    sample_rate: int = Field(
        default=16000,
        description="Audio sample rate in Hz",
        ge=8000,
        le=48000
    )
    
    language_code: str = Field(
        default="en-US",
        description="Language code for transcription"
    )
    
    include_word_timing: bool = Field(
        default=False,
        description="Whether to include word-level timing information"
    )
    
    @validator('audio_format')
    def validate_audio_format(cls, v):
        """Validate audio format."""
        supported_formats = ["webm", "wav", "mp3", "flac", "ogg"]
        if v.lower() not in supported_formats:
            raise ValueError(f"Audio format must be one of: {', '.join(supported_formats)}")
        return v.lower()
    
    @validator('language_code')
    def validate_language_code(cls, v):
        """Validate language code format."""
        if not v or len(v) < 2:
            raise ValueError("Language code must be at least 2 characters")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "audio_format": "webm",
                "sample_rate": 16000,
                "language_code": "en-US",
                "include_word_timing": False
            }
        }


class SynthesisRequest(BaseModel):
    """Request model for text-to-speech synthesis."""
    
    text: str = Field(
        ...,
        description="Text to convert to speech",
        min_length=1,
        max_length=5000
    )
    
    voice_name: Optional[str] = Field(
        default=None,
        description="Specific voice to use for synthesis"
    )
    
    language_code: Optional[str] = Field(
        default=None,
        description="Language code for the voice"
    )
    
    audio_format: Optional[str] = Field(
        default="mp3",
        description="Output audio format (mp3, wav, ogg)"
    )
    
    speaking_rate: Optional[float] = Field(
        default=None,
        description="Speech rate (0.25 to 4.0)",
        ge=0.25,
        le=4.0
    )
    
    pitch: Optional[float] = Field(
        default=None,
        description="Voice pitch (-20.0 to 20.0)",
        ge=-20.0,
        le=20.0
    )
    
    volume_gain_db: Optional[float] = Field(
        default=None,
        description="Volume gain in dB (-96.0 to 16.0)",
        ge=-96.0,
        le=16.0
    )
    
    use_ssml: bool = Field(
        default=False,
        description="Whether text contains SSML markup"
    )
    
    @validator('text')
    def validate_text(cls, v):
        """Validate text content."""
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v
    
    @validator('audio_format')
    def validate_audio_format(cls, v):
        """Validate audio format."""
        if v is not None:
            supported_formats = ["mp3", "wav", "ogg"]
            if v.lower() not in supported_formats:
                raise ValueError(f"Audio format must be one of: {', '.join(supported_formats)}")
            return v.lower()
        return v
    
    @validator('language_code')
    def validate_language_code(cls, v):
        """Validate language code format."""
        if v is not None and (not v or len(v) < 2):
            raise ValueError("Language code must be at least 2 characters")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Hello, this is a test message for text-to-speech synthesis.",
                "voice_name": "en-US-Neural2-F",
                "language_code": "en-US",
                "audio_format": "mp3",
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "volume_gain_db": 0.0,
                "use_ssml": False
            }
        }


class VoiceSettingsRequest(BaseModel):
    """Request model for voice settings validation."""
    
    language_code: Optional[str] = Field(
        default=None,
        description="Language code for voice services"
    )
    
    voice_name: Optional[str] = Field(
        default=None,
        description="Specific voice name for TTS"
    )
    
    speaking_rate: Optional[float] = Field(
        default=None,
        description="Speech rate (0.25 to 4.0)",
        ge=0.25,
        le=4.0
    )
    
    pitch: Optional[float] = Field(
        default=None,
        description="Voice pitch (-20.0 to 20.0)",
        ge=-20.0,
        le=20.0
    )
    
    audio_format: Optional[str] = Field(
        default=None,
        description="Audio format (mp3, wav, ogg)"
    )
    
    @validator('language_code')
    def validate_language_code(cls, v):
        """Validate language code format."""
        if v is not None and (not v or len(v) < 2):
            raise ValueError("Language code must be at least 2 characters")
        return v
    
    @validator('audio_format')
    def validate_audio_format(cls, v):
        """Validate audio format."""
        if v is not None:
            supported_formats = ["mp3", "wav", "ogg"]
            if v.lower() not in supported_formats:
                raise ValueError(f"Audio format must be one of: {', '.join(supported_formats)}")
            return v.lower()
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "language_code": "en-US",
                "voice_name": "en-US-Neural2-F",
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "audio_format": "mp3"
            }
        }


class VoiceStreamRequest(BaseModel):
    """Request model for streaming voice interactions (future use)."""
    
    session_id: str = Field(
        ...,
        description="Chat session identifier"
    )
    
    stream_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Streaming configuration settings"
    )
    
    voice_settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Voice synthesis settings"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "stream_settings": {
                    "chunk_size": 1024,
                    "sample_rate": 16000
                },
                "voice_settings": {
                    "language_code": "en-US",
                    "voice_name": "en-US-Neural2-F"
                }
            }
        }
