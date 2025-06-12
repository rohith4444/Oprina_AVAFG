"""
Voice response models for Oprina API.

This module defines Pydantic models for voice-related API responses.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class WordTiming(BaseModel):
    """Model for word-level timing information."""
    
    word: str = Field(..., description="The spoken word")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")


class TranscriptionData(BaseModel):
    """Model for transcription data."""
    
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Transcription confidence score")
    language_code: Optional[str] = Field(None, description="Detected/used language code")
    audio_duration: Optional[float] = Field(None, description="Audio duration in seconds")


class ChatResponseData(BaseModel):
    """Model for chat response data."""
    
    text: str = Field(..., description="Agent response text")
    message_id: Optional[str] = Field(None, description="Message identifier")
    session_id: str = Field(..., description="Session identifier")


class AudioResponseData(BaseModel):
    """Model for audio response data."""
    
    audio_content: str = Field(..., description="Base64 encoded audio content")
    audio_format: str = Field(..., description="Audio format (mp3, wav, etc.)")
    audio_size: int = Field(..., description="Audio size in bytes")
    voice_name: Optional[str] = Field(None, description="Voice used for synthesis")
    speaking_rate: Optional[float] = Field(None, description="Speaking rate used")


class ProcessingTime(BaseModel):
    """Model for processing time breakdown."""
    
    total: float = Field(..., description="Total processing time in seconds")
    transcription: float = Field(default=0.0, description="Transcription time in seconds")
    chat: float = Field(default=0.0, description="Chat processing time in seconds")
    synthesis: float = Field(default=0.0, description="Speech synthesis time in seconds")


class VoiceMessageResponse(BaseModel):
    """Response model for voice message processing."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    transcription: TranscriptionData = Field(..., description="Speech transcription results")
    chat_response: ChatResponseData = Field(..., description="Agent chat response")
    audio_response: Optional[AudioResponseData] = Field(None, description="Audio response (if requested)")
    processing_time: Optional[ProcessingTime] = Field(None, description="Processing time breakdown")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "transcription": {
                    "text": "Hello, how are you today?",
                    "confidence": 0.95,
                    "language_code": "en-US",
                    "audio_duration": 2.5
                },
                "chat_response": {
                    "text": "Hello! I'm doing well, thank you for asking. How can I help you today?",
                    "message_id": "msg-123",
                    "session_id": "session-123"
                },
                "audio_response": {
                    "audio_content": "base64-encoded-audio-data",
                    "audio_format": "mp3",
                    "audio_size": 15420,
                    "voice_name": "en-US-Neural2-F",
                    "speaking_rate": 1.0
                },
                "processing_time": {
                    "total": 3.2,
                    "transcription": 1.1,
                    "chat": 0.8,
                    "synthesis": 1.3
                }
            }
        }


class TranscriptionResponse(BaseModel):
    """Response model for audio transcription."""
    
    success: bool = Field(..., description="Whether the transcription was successful")
    transcript: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Transcription confidence score")
    language_code: Optional[str] = Field(None, description="Language code used")
    audio_duration: Optional[float] = Field(None, description="Audio duration in seconds")
    words: Optional[List[WordTiming]] = Field(None, description="Word-level timing (if requested)")
    service: Optional[str] = Field(None, description="Service used for transcription")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "transcript": "Hello, this is a test message for speech recognition.",
                "confidence": 0.92,
                "language_code": "en-US",
                "audio_duration": 3.5,
                "words": [
                    {"word": "Hello", "start_time": 0.0, "end_time": 0.5},
                    {"word": "this", "start_time": 0.6, "end_time": 0.8}
                ],
                "service": "google_cloud_speech"
            }
        }


class SynthesisResponse(BaseModel):
    """Response model for text-to-speech synthesis."""
    
    success: bool = Field(..., description="Whether the synthesis was successful")
    audio_content: str = Field(..., description="Base64 encoded audio content")
    audio_format: str = Field(..., description="Audio format")
    audio_size: int = Field(..., description="Audio size in bytes")
    text_length: int = Field(..., description="Length of input text")
    voice_name: Optional[str] = Field(None, description="Voice used for synthesis")
    language_code: Optional[str] = Field(None, description="Language code used")
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


class VoiceCapability(BaseModel):
    """Model for voice service capability information."""
    
    available: bool = Field(..., description="Whether the service is available")
    supported_languages: List[str] = Field(default_factory=list, description="Supported language codes")
    supported_formats: Optional[List[str]] = Field(None, description="Supported audio formats")


class VoiceInfo(BaseModel):
    """Model for voice information."""
    
    name: str = Field(..., description="Voice name")
    language_codes: List[str] = Field(..., description="Supported language codes")
    gender: str = Field(..., description="Voice gender")
    natural_sample_rate: Optional[int] = Field(None, description="Natural sample rate")


class TTSCapability(VoiceCapability):
    """Model for text-to-speech capability information."""
    
    available_voices: List[VoiceInfo] = Field(default_factory=list, description="Available voices")


class VoiceInteractionCapability(BaseModel):
    """Model for voice interaction capability."""
    
    available: bool = Field(..., description="Whether voice interaction is available")
    default_settings: Dict[str, Any] = Field(default_factory=dict, description="Default voice settings")


class VoiceCapabilitiesResponse(BaseModel):
    """Response model for voice capabilities."""
    
    speech_to_text: VoiceCapability = Field(..., description="Speech-to-text capabilities")
    text_to_speech: TTSCapability = Field(..., description="Text-to-speech capabilities")
    voice_interaction: VoiceInteractionCapability = Field(..., description="Voice interaction capabilities")
    
    class Config:
        schema_extra = {
            "example": {
                "speech_to_text": {
                    "available": True,
                    "supported_languages": ["en-US", "en-GB", "es-ES", "fr-FR"],
                    "supported_formats": ["wav", "mp3", "flac", "webm", "ogg"]
                },
                "text_to_speech": {
                    "available": True,
                    "supported_languages": ["en-US", "en-GB", "es-ES", "fr-FR"],
                    "supported_formats": ["mp3", "wav", "ogg"],
                    "available_voices": [
                        {
                            "name": "en-US-Neural2-F",
                            "language_codes": ["en-US"],
                            "gender": "FEMALE",
                            "natural_sample_rate": 24000
                        }
                    ]
                },
                "voice_interaction": {
                    "available": True,
                    "default_settings": {
                        "language_code": "en-US",
                        "voice_name": "en-US-Neural2-F",
                        "speaking_rate": 1.0,
                        "pitch": 0.0,
                        "audio_format": "mp3"
                    }
                }
            }
        }


class VoiceSettingsValidationResponse(BaseModel):
    """Response model for voice settings validation."""
    
    valid: bool = Field(..., description="Whether the settings are valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    validated_settings: Dict[str, Any] = Field(default_factory=dict, description="Validated and normalized settings")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "errors": [],
                "validated_settings": {
                    "language_code": "en-US",
                    "voice_name": "en-US-Neural2-F",
                    "speaking_rate": 1.0,
                    "pitch": 0.0,
                    "audio_format": "mp3"
                }
            }
        }


class VoiceErrorResponse(BaseModel):
    """Response model for voice operation errors."""
    
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    stage: Optional[str] = Field(None, description="Processing stage where error occurred")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Speech transcription failed",
                "error_code": "TRANSCRIPTION_ERROR",
                "stage": "transcription",
                "details": {
                    "service": "google_cloud_speech",
                    "audio_format": "webm",
                    "audio_size": 1024000
                }
            }
        }


class VoiceStreamResponse(BaseModel):
    """Response model for streaming voice interactions (future use)."""
    
    success: bool = Field(..., description="Whether the stream operation was successful")
    stream_id: str = Field(..., description="Stream identifier")
    status: str = Field(..., description="Stream status")
    message: Optional[str] = Field(None, description="Status message")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "stream_id": "stream-123",
                "status": "active",
                "message": "Voice stream established successfully"
            }
        }
