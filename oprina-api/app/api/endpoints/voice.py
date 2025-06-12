"""
Voice endpoints for Oprina API.

This module provides REST API endpoints for voice interactions including
speech-to-text, text-to-speech, and complete voice conversations.
"""

import base64
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_current_user,
    get_voice_service,
    validate_pagination
)
from app.core.services.voice_service import VoiceService
from app.models.requests.voice import (
    VoiceMessageRequest,
    TranscriptionRequest,
    SynthesisRequest,
    VoiceSettingsRequest
)
from app.models.responses.voice import (
    VoiceMessageResponse,
    TranscriptionResponse,
    SynthesisResponse,
    VoiceCapabilitiesResponse,
    VoiceSettingsValidationResponse
)
from app.models.database.user import User
from app.utils.errors import ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/message", response_model=VoiceMessageResponse)
async def process_voice_message(
    session_id: str = Form(...),
    audio_format: str = Form(default="webm"),
    sample_rate: int = Form(default=16000),
    include_audio_response: bool = Form(default=True),
    voice_settings: Optional[str] = Form(default=None),  # JSON string
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Process a complete voice message interaction.
    
    This endpoint:
    1. Accepts audio input from the user
    2. Transcribes speech to text
    3. Processes the text through the chat service
    4. Optionally converts the response back to speech
    """
    try:
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise ValidationError("File must be an audio file")
        
        # Read audio data
        audio_data = await audio_file.read()
        if len(audio_data) == 0:
            raise ValidationError("Audio file is empty")
        
        if len(audio_data) > 10 * 1024 * 1024:  # 10MB limit
            raise ValidationError("Audio file too large (max 10MB)")
        
        # Parse voice settings if provided
        parsed_voice_settings = None
        if voice_settings:
            try:
                import json
                parsed_voice_settings = json.loads(voice_settings)
            except json.JSONDecodeError:
                raise ValidationError("Invalid voice_settings JSON format")
        
        # Process voice message
        result = await voice_service.process_voice_message(
            user_id=current_user.id,
            session_id=session_id,
            audio_data=audio_data,
            audio_format=audio_format,
            sample_rate=sample_rate,
            voice_settings=parsed_voice_settings,
            include_audio_response=include_audio_response
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Voice processing failed: {result.get('error')}"
            )
        
        return VoiceMessageResponse(
            success=True,
            transcription=result["transcription"],
            chat_response=result["chat_response"],
            audio_response=result.get("audio_response"),
            processing_time=result.get("processing_time", {})
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Voice message processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice message processing failed"
        )


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_format: str = Form(default="webm"),
    sample_rate: int = Form(default=16000),
    language_code: str = Form(default="en-US"),
    include_word_timing: bool = Form(default=False),
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Transcribe audio to text without processing through chat service.
    
    This endpoint only performs speech-to-text conversion.
    """
    try:
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise ValidationError("File must be an audio file")
        
        # Read audio data
        audio_data = await audio_file.read()
        if len(audio_data) == 0:
            raise ValidationError("Audio file is empty")
        
        if len(audio_data) > 10 * 1024 * 1024:  # 10MB limit
            raise ValidationError("Audio file too large (max 10MB)")
        
        # Transcribe audio
        result = await voice_service.transcribe_audio_only(
            audio_data=audio_data,
            audio_format=audio_format,
            sample_rate=sample_rate,
            language_code=language_code,
            include_word_timing=include_word_timing
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transcription failed: {result.get('error')}"
            )
        
        return TranscriptionResponse(
            success=True,
            transcript=result["transcript"],
            confidence=result.get("confidence", 0.0),
            language_code=result.get("language_code"),
            audio_duration=result.get("audio_duration"),
            words=result.get("words"),
            service=result.get("service")
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Audio transcription failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audio transcription failed"
        )


@router.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(
    request: SynthesisRequest,
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Convert text to speech audio.
    
    This endpoint only performs text-to-speech conversion.
    """
    try:
        # Validate text input
        if not request.text or len(request.text.strip()) == 0:
            raise ValidationError("Text is required")
        
        if len(request.text) > 5000:
            raise ValidationError("Text too long (max 5000 characters)")
        
        # Prepare voice settings
        voice_settings = {}
        if request.voice_name:
            voice_settings["voice_name"] = request.voice_name
        if request.language_code:
            voice_settings["language_code"] = request.language_code
        if request.audio_format:
            voice_settings["audio_format"] = request.audio_format
        if request.speaking_rate is not None:
            voice_settings["speaking_rate"] = request.speaking_rate
        if request.pitch is not None:
            voice_settings["pitch"] = request.pitch
        if request.volume_gain_db is not None:
            voice_settings["volume_gain_db"] = request.volume_gain_db
        
        # Synthesize speech
        result = await voice_service.synthesize_text_only(
            text=request.text,
            voice_settings=voice_settings
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Speech synthesis failed: {result.get('error')}"
            )
        
        return SynthesisResponse(
            success=True,
            audio_content=result["audio_content"],
            audio_format=result["audio_format"],
            audio_size=result.get("audio_size", 0),
            text_length=len(request.text),
            voice_name=result.get("voice_name"),
            language_code=result.get("language_code"),
            speaking_rate=result.get("speaking_rate"),
            service=result.get("service")
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Speech synthesis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech synthesis failed"
        )


@router.get("/capabilities", response_model=VoiceCapabilitiesResponse)
async def get_voice_capabilities(
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Get information about available voice capabilities.
    
    Returns supported languages, voices, and formats for both
    speech-to-text and text-to-speech services.
    """
    try:
        capabilities = await voice_service.get_voice_capabilities()
        
        return VoiceCapabilitiesResponse(
            speech_to_text=capabilities["speech_to_text"],
            text_to_speech=capabilities["text_to_speech"],
            voice_interaction=capabilities["voice_interaction"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get voice capabilities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voice capabilities"
        )


@router.post("/validate-settings", response_model=VoiceSettingsValidationResponse)
async def validate_voice_settings(
    request: VoiceSettingsRequest,
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Validate voice settings and return normalized values.
    
    This endpoint helps clients validate voice settings before
    making actual voice requests.
    """
    try:
        # Convert request to dictionary
        voice_settings = {}
        if request.language_code:
            voice_settings["language_code"] = request.language_code
        if request.voice_name:
            voice_settings["voice_name"] = request.voice_name
        if request.speaking_rate is not None:
            voice_settings["speaking_rate"] = request.speaking_rate
        if request.pitch is not None:
            voice_settings["pitch"] = request.pitch
        if request.audio_format:
            voice_settings["audio_format"] = request.audio_format
        
        # Validate settings
        validation_result = await voice_service.validate_voice_settings(voice_settings)
        
        return VoiceSettingsValidationResponse(
            valid=validation_result["valid"],
            errors=validation_result["errors"],
            validated_settings=validation_result["validated_settings"]
        )
        
    except Exception as e:
        logger.error(f"Voice settings validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice settings validation failed"
        )


@router.get("/languages")
async def get_supported_languages(
    service: str = "both",  # "stt", "tts", or "both"
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Get list of supported language codes.
    
    Args:
        service: Which service to get languages for ("stt", "tts", or "both")
    """
    try:
        capabilities = await voice_service.get_voice_capabilities()
        
        result = {}
        
        if service in ["stt", "both"]:
            result["speech_to_text"] = capabilities["speech_to_text"]["supported_languages"]
        
        if service in ["tts", "both"]:
            result["text_to_speech"] = capabilities["text_to_speech"]["supported_languages"]
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get supported languages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supported languages"
        )


@router.get("/voices")
async def get_available_voices(
    language_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Get list of available voices for text-to-speech.
    
    Args:
        language_code: Optional language code to filter voices
    """
    try:
        voices = await voice_service.tts_service.get_available_voices(language_code)
        
        return {
            "voices": voices,
            "count": len(voices),
            "language_filter": language_code
        }
        
    except Exception as e:
        logger.error(f"Failed to get available voices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available voices"
        )


@router.get("/health")
async def voice_service_health(
    current_user: User = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Check the health status of voice services.
    
    Returns the availability status of speech-to-text and text-to-speech services.
    """
    try:
        stt_available = voice_service.stt_service.is_available()
        tts_available = voice_service.tts_service.is_available()
        
        return {
            "status": "healthy" if (stt_available and tts_available) else "degraded",
            "services": {
                "speech_to_text": {
                    "available": stt_available,
                    "status": "healthy" if stt_available else "unavailable"
                },
                "text_to_speech": {
                    "available": tts_available,
                    "status": "healthy" if tts_available else "unavailable"
                }
            },
            "voice_interaction": {
                "available": stt_available and tts_available,
                "status": "healthy" if (stt_available and tts_available) else "degraded"
            }
        }
        
    except Exception as e:
        logger.error(f"Voice service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "services": {
                "speech_to_text": {"available": False, "status": "error"},
                "text_to_speech": {"available": False, "status": "error"}
            }
        }
