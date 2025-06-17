"""
Simplified Voice response models for Oprina API.

This module defines simplified Pydantic models for voice-related API responses.
Removed over-engineered models and complex data structures.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class TranscriptionData(BaseModel):
    """Simplified model for transcription data."""
    
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Transcription confidence score")
    service: Optional[str] = Field(None, description="Service used for transcription")


class ChatResponseData(BaseModel):
    """Model for chat response data."""
    
    text: str = Field(..., description="Agent response text")
    message_id: Optional[str] = Field(None, description="Message identifier")
    session_id: str = Field(..., description="Session identifier")


class AudioResponseData(BaseModel):
    """Simplified model for audio response data."""
    
    audio_content: str = Field(..., description="Base64 encoded audio content")
    audio_format: str = Field(..., description="Audio format (always mp3)")
    audio_size: int = Field(..., description="Audio size in bytes")


class VoiceMessageResponse(BaseModel):
    """Simplified response model for voice message processing."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    transcription: TranscriptionData = Field(..., description="Speech transcription results")
    chat_response: ChatResponseData = Field(..., description="Agent chat response")
    audio_response: Optional[AudioResponseData] = Field(None, description="Audio response (if requested)")
    processing_time: Optional[Dict[str, Any]] = Field(None, description="Processing time info")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "transcription": {
                    "text": "Hello, how are you today?",
                    "confidence": 0.95,
                    "service": "google_cloud_speech"
                },
                "chat_response": {
                    "text": "Hello! I'm doing well, thank you for asking. How can I help you today?",
                    "message_id": "msg-123",
                    "session_id": "session-123"
                },
                "audio_response": {
                    "audio_content": "base64-encoded-audio-data",
                    "audio_format": "mp3",
                    "audio_size": 15420
                }
            }
        }


class TranscriptionResponse(BaseModel):
    """Simplified response model for audio transcription."""
    
    success: bool = Field(..., description="Whether the transcription was successful")
    transcript: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Transcription confidence score")
    language_code: Optional[str] = Field("en-US", description="Language code (always en-US)")
    service: Optional[str] = Field(None, description="Service used for transcription")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "transcript": "Hello, this is a test message for speech recognition.",
                "confidence": 0.92,
                "language_code": "en-US",
                "service": "google_cloud_speech"
            }
        }


class SynthesisResponse(BaseModel):
    """Simplified response model for text-to-speech synthesis."""
    
    success: bool = Field(..., description="Whether the synthesis was successful")
    audio_content: str = Field(..., description="Base64 encoded audio content")
    audio_format: str = Field(..., description="Audio format (always mp3)")
    audio_size: int = Field(..., description="Audio size in bytes")
    text_length: int = Field(..., description="Length of input text")
    voice_name: Optional[str] = Field("en-US-Neural2-F", description="Voice used (always en-US-Neural2-F)")
    language_code: Optional[str] = Field("en-US", description="Language code (always en-US)")
    speaking_rate: Optional[float] = Field(None, description="Speaking rate used")
    service: Optional[str] = Field(None, description="Service used for synthesis")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "audio_content": "base64-encoded-audio-data",
                "audio_format": "mp3",
                "audio_size": 12340,
                "text_length": 45,
                "voice_name": "en-US-Neural2-F",
                "language_code": "en-US",
                "speaking_rate": 1.0,
                "service": "google_cloud_tts"
            }
        }


class VoiceErrorResponse(BaseModel):
    """Response model for voice operation errors."""
    
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error message")
    stage: Optional[str] = Field(None, description="Processing stage where error occurred")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Speech transcription failed",
                "stage": "transcription"
            }
        }

