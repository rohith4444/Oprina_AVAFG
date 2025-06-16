"""
Simplified Voice request models for Oprina API.

This module defines simplified Pydantic models for voice-related API requests.
Removed over-engineered validation and complex parameters.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class VoiceMessageRequest(BaseModel):
    """Simplified request model for processing voice messages."""
    
    session_id: str = Field(
        ...,
        description="Chat session identifier",
        min_length=1,
        max_length=100
    )
    
    audio_format: str = Field(
        default="webm",
        description="Audio format (webm, wav, mp3, flac, ogg)"
    )
    
    include_audio_response: bool = Field(
        default=True,
        description="Whether to generate audio response"
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
                "include_audio_response": True
            }
        }


class TranscriptionRequest(BaseModel):
    """Simplified request model for audio transcription."""
    
    audio_format: str = Field(
        default="webm",
        description="Audio format (webm, wav, mp3, flac, ogg)"
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
                "audio_format": "webm"
            }
        }


class SynthesisRequest(BaseModel):
    """Simplified request model for text-to-speech synthesis."""
    
    text: str = Field(
        ...,
        description="Text to convert to speech",
        min_length=1,
        max_length=5000
    )
    
    speaking_rate: Optional[float] = Field(
        default=1.0,
        description="Speech rate (0.25 to 4.0)",
        ge=0.25,
        le=4.0
    )
    
    @validator('text')
    def validate_text(cls, v):
        """Validate text content."""
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Hello, this is a test message for text-to-speech synthesis.",
                "speaking_rate": 1.0
            }
        }
