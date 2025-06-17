"""
Simplified Voice endpoints for Oprina API.

This module provides essential REST API endpoints for voice interactions.
Only includes the endpoints needed for basic voice chat functionality.
"""

import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form

from app.api.dependencies import get_current_user, get_voice_service
from app.core.services.voice_service import VoiceService
from app.api.models.requests.voice import SynthesisRequest
from app.api.models.responses.voice import (
    VoiceMessageResponse,
    TranscriptionResponse,
    SynthesisResponse
)
from app.utils.errors import ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/message", response_model=VoiceMessageResponse)
async def process_voice_message(
    session_id: str = Form(...),
    audio_format: str = Form(default="webm"),
    include_audio_response: bool = Form(default=True),
    audio_file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Process a complete voice message interaction.
    
    ESSENTIAL ENDPOINT for your UI workflow:
    1. Accepts audio input from the user (mic button)
    2. Transcribes speech to text
    3. Processes the text through the agent service
    4. Optionally converts the response back to speech
    5. Returns everything for conversation display
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
        
        # Process voice message
        result = await voice_service.process_voice_message(
            user_id=current_user["id"],
            session_id=session_id,
            audio_data=audio_data,
            audio_format=audio_format,
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
    audio_file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Transcribe audio to text without processing through agent service.
    
    DEBUGGING ENDPOINT - Only performs speech-to-text conversion.
    Useful for testing transcription without full voice workflow.
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
            audio_format=audio_format
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
            language_code=result.get("language_code", "en-US"),
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Convert text to speech audio.
    
    DEBUGGING ENDPOINT - Only performs text-to-speech conversion.
    Useful for testing speech synthesis without full voice workflow.
    """
    try:
        # Validate text input
        if not request.text or len(request.text.strip()) == 0:
            raise ValidationError("Text is required")
        
        if len(request.text) > 5000:
            raise ValidationError("Text too long (max 5000 characters)")
        
        # Use speaking rate if provided, otherwise default to 1.0
        speaking_rate = getattr(request, 'speaking_rate', 1.0) or 1.0
        
        # Synthesize speech
        result = await voice_service.synthesize_text_only(
            text=request.text,
            speaking_rate=speaking_rate
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
            voice_name=result.get("voice_name", "en-US-Neural2-F"),
            language_code="en-US",
            speaking_rate=result.get("speaking_rate", 1.0),
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


# REMOVED ENDPOINTS (Over-engineered):
# ❌ @router.get("/capabilities") - Not needed for basic voice chat
# ❌ @router.post("/validate-settings") - Just use defaults
# ❌ @router.get("/languages") - Hardcoded to en-US
# ❌ @router.get("/voices") - Hardcoded to en-US-Neural2-F
# ❌ @router.get("/health") - Use main health endpoint instead