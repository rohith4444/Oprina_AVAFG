"""
Voice service for Oprina API.

This module orchestrates speech-to-text and text-to-speech operations,
providing a unified interface for voice interactions with the AI agent.
"""

import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime

from app.core.integrations.speech import SpeechToTextService, TextToSpeechService
from app.core.services.chat_service import ChatService
from app.core.database.repositories.message_repository import MessageRepository
from app.core.database.repositories.session_repository import SessionRepository
from app.utils.errors import ValidationError, OprinaError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class VoiceService:
    """
    Service for handling voice interactions with the AI agent.
    
    This service coordinates:
    1. Speech-to-text conversion of user audio
    2. Text processing through the chat service
    3. Text-to-speech conversion of agent responses
    4. Voice interaction session management
    """
    
    def __init__(
        self,
        message_repository: MessageRepository,
        session_repository: SessionRepository,
        chat_service: ChatService
    ):
        self.message_repository = message_repository
        self.session_repository = session_repository
        self.chat_service = chat_service
        
        # Initialize speech services
        self.stt_service = SpeechToTextService()
        self.tts_service = TextToSpeechService()
        
        # Voice interaction settings
        self.default_voice_settings = {
            "language_code": "en-US",
            "voice_name": "en-US-Neural2-F",
            "speaking_rate": 1.0,
            "pitch": 0.0,
            "audio_format": "mp3"
        }
    
    async def process_voice_message(
        self,
        user_id: str,
        session_id: str,
        audio_data: bytes,
        audio_format: str = "webm",
        sample_rate: int = 16000,
        voice_settings: Optional[Dict[str, Any]] = None,
        include_audio_response: bool = True
    ) -> Dict[str, Any]:
        """
        Process a complete voice interaction: audio input -> text -> agent response -> audio output.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            audio_data: Raw audio bytes from user
            audio_format: Input audio format
            sample_rate: Audio sample rate
            voice_settings: Voice synthesis settings
            include_audio_response: Whether to generate audio response
            
        Returns:
            Dictionary with transcription, agent response, and optional audio
        """
        try:
            # Step 1: Convert speech to text
            logger.info(f"Processing voice message for user {user_id}, session {session_id}")
            
            transcription_result = await self.stt_service.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format,
                sample_rate=sample_rate,
                language_code=voice_settings.get("language_code", "en-US") if voice_settings else "en-US",
                enable_automatic_punctuation=True,
                enable_word_time_offsets=False
            )
            
            if not transcription_result["success"]:
                return {
                    "success": False,
                    "error": "Speech transcription failed",
                    "transcription_error": transcription_result.get("error"),
                    "stage": "transcription"
                }
            
            user_text = transcription_result["transcript"]
            if not user_text.strip():
                return {
                    "success": False,
                    "error": "No speech detected in audio",
                    "stage": "transcription"
                }
            
            # Step 2: Process text through chat service
            chat_response = await self.chat_service.send_message(
                user_id=user_id,
                session_id=session_id,
                message=user_text,
                message_type="voice",
                metadata={
                    "audio_duration": transcription_result.get("audio_duration"),
                    "transcription_confidence": transcription_result.get("confidence"),
                    "audio_format": audio_format,
                    "sample_rate": sample_rate
                }
            )
            
            if not chat_response.get("success"):
                return {
                    "success": False,
                    "error": "Chat processing failed",
                    "chat_error": chat_response.get("error"),
                    "stage": "chat_processing",
                    "transcription": {
                        "text": user_text,
                        "confidence": transcription_result.get("confidence")
                    }
                }
            
            agent_text = chat_response["response"]
            
            # Step 3: Convert agent response to speech (if requested)
            audio_response = None
            if include_audio_response and agent_text.strip():
                synthesis_settings = {**self.default_voice_settings}
                if voice_settings:
                    synthesis_settings.update(voice_settings)
                
                synthesis_result = await self.tts_service.synthesize_speech(
                    text=agent_text,
                    voice_name=synthesis_settings.get("voice_name"),
                    language_code=synthesis_settings.get("language_code"),
                    audio_encoding=synthesis_settings.get("audio_format", "mp3"),
                    speaking_rate=synthesis_settings.get("speaking_rate", 1.0),
                    pitch=synthesis_settings.get("pitch", 0.0),
                    volume_gain_db=synthesis_settings.get("volume_gain_db", 0.0)
                )
                
                if synthesis_result["success"]:
                    audio_response = {
                        "audio_content": synthesis_result["audio_content"],
                        "audio_format": synthesis_result["audio_format"],
                        "audio_size": synthesis_result["audio_size"],
                        "voice_name": synthesis_result["voice_name"],
                        "speaking_rate": synthesis_result["speaking_rate"]
                    }
                else:
                    logger.warning(f"TTS synthesis failed: {synthesis_result.get('error')}")
            
            # Step 4: Update message with voice metadata
            if chat_response.get("message_id"):
                await self._update_message_voice_metadata(
                    message_id=chat_response["message_id"],
                    transcription_data=transcription_result,
                    synthesis_data=synthesis_result if include_audio_response else None
                )
            
            # Return complete voice interaction result
            result = {
                "success": True,
                "transcription": {
                    "text": user_text,
                    "confidence": transcription_result.get("confidence", 0.0),
                    "language_code": transcription_result.get("language_code"),
                    "audio_duration": transcription_result.get("audio_duration")
                },
                "chat_response": {
                    "text": agent_text,
                    "message_id": chat_response.get("message_id"),
                    "session_id": session_id
                },
                "processing_time": {
                    "total": datetime.utcnow().timestamp() - datetime.utcnow().timestamp(),  # Placeholder
                    "transcription": 0.0,  # Would be measured in production
                    "chat": 0.0,
                    "synthesis": 0.0
                }
            }
            
            if audio_response:
                result["audio_response"] = audio_response
            
            logger.info(f"Voice message processed successfully for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Voice message processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "stage": "processing"
            }
    
    async def transcribe_audio_only(
        self,
        audio_data: bytes,
        audio_format: str = "webm",
        sample_rate: int = 16000,
        language_code: str = "en-US",
        include_word_timing: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text without processing through chat service.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format
            sample_rate: Audio sample rate
            language_code: Language for transcription
            include_word_timing: Whether to include word-level timing
            
        Returns:
            Transcription results
        """
        try:
            result = await self.stt_service.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format,
                sample_rate=sample_rate,
                language_code=language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=include_word_timing
            )
            
            logger.info(f"Audio transcription completed: {result.get('transcript', '')[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "transcript": "",
                "confidence": 0.0
            }
    
    async def synthesize_text_only(
        self,
        text: str,
        voice_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert text to speech without chat processing.
        
        Args:
            text: Text to convert to speech
            voice_settings: Voice synthesis settings
            
        Returns:
            Audio synthesis results
        """
        try:
            settings = {**self.default_voice_settings}
            if voice_settings:
                settings.update(voice_settings)
            
            result = await self.tts_service.synthesize_speech(
                text=text,
                voice_name=settings.get("voice_name"),
                language_code=settings.get("language_code"),
                audio_encoding=settings.get("audio_format", "mp3"),
                speaking_rate=settings.get("speaking_rate", 1.0),
                pitch=settings.get("pitch", 0.0),
                volume_gain_db=settings.get("volume_gain_db", 0.0)
            )
            
            logger.info(f"Text synthesis completed: {len(text)} chars -> {result.get('audio_size', 0)} bytes")
            return result
            
        except Exception as e:
            logger.error(f"Text synthesis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_content": "",
                "audio_format": "mp3"
            }
    
    async def get_voice_capabilities(self) -> Dict[str, Any]:
        """Get information about available voice capabilities."""
        try:
            # Get STT capabilities
            stt_available = self.stt_service.is_available()
            stt_languages = await self.stt_service.get_supported_languages() if stt_available else []
            
            # Get TTS capabilities
            tts_available = self.tts_service.is_available()
            tts_voices = await self.tts_service.get_available_voices() if tts_available else []
            tts_languages = await self.tts_service.get_supported_languages() if tts_available else []
            
            return {
                "speech_to_text": {
                    "available": stt_available,
                    "supported_languages": stt_languages,
                    "supported_formats": ["wav", "mp3", "flac", "webm", "ogg"]
                },
                "text_to_speech": {
                    "available": tts_available,
                    "supported_languages": tts_languages,
                    "available_voices": tts_voices,
                    "supported_formats": ["mp3", "wav", "ogg"]
                },
                "voice_interaction": {
                    "available": stt_available and tts_available,
                    "default_settings": self.default_voice_settings
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get voice capabilities: {str(e)}")
            return {
                "speech_to_text": {"available": False},
                "text_to_speech": {"available": False},
                "voice_interaction": {"available": False},
                "error": str(e)
            }
    
    async def validate_voice_settings(self, voice_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate voice settings and return normalized values.
        
        Args:
            voice_settings: Voice settings to validate
            
        Returns:
            Validation results with normalized settings
        """
        try:
            validated_settings = {}
            errors = []
            
            # Validate language code
            language_code = voice_settings.get("language_code", "en-US")
            stt_languages = await self.stt_service.get_supported_languages()
            if language_code not in stt_languages:
                errors.append(f"Language code '{language_code}' not supported for speech recognition")
            else:
                validated_settings["language_code"] = language_code
            
            # Validate voice name
            voice_name = voice_settings.get("voice_name")
            if voice_name:
                is_valid = await self.tts_service.validate_voice(voice_name, language_code)
                if not is_valid:
                    errors.append(f"Voice '{voice_name}' not available for language '{language_code}'")
                else:
                    validated_settings["voice_name"] = voice_name
            
            # Validate speaking rate
            speaking_rate = voice_settings.get("speaking_rate", 1.0)
            if not isinstance(speaking_rate, (int, float)) or not (0.25 <= speaking_rate <= 4.0):
                errors.append("Speaking rate must be between 0.25 and 4.0")
            else:
                validated_settings["speaking_rate"] = float(speaking_rate)
            
            # Validate pitch
            pitch = voice_settings.get("pitch", 0.0)
            if not isinstance(pitch, (int, float)) or not (-20.0 <= pitch <= 20.0):
                errors.append("Pitch must be between -20.0 and 20.0")
            else:
                validated_settings["pitch"] = float(pitch)
            
            # Validate audio format
            audio_format = voice_settings.get("audio_format", "mp3")
            if audio_format not in ["mp3", "wav", "ogg"]:
                errors.append("Audio format must be one of: mp3, wav, ogg")
            else:
                validated_settings["audio_format"] = audio_format
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "validated_settings": validated_settings
            }
            
        except Exception as e:
            logger.error(f"Voice settings validation failed: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)],
                "validated_settings": {}
            }
    
    async def _update_message_voice_metadata(
        self,
        message_id: str,
        transcription_data: Dict[str, Any],
        synthesis_data: Optional[Dict[str, Any]] = None
    ):
        """Update message with voice interaction metadata."""
        try:
            voice_metadata = {
                "transcription": {
                    "confidence": transcription_data.get("confidence"),
                    "language_code": transcription_data.get("language_code"),
                    "audio_duration": transcription_data.get("audio_duration"),
                    "service": transcription_data.get("service")
                }
            }
            
            if synthesis_data:
                voice_metadata["synthesis"] = {
                    "voice_name": synthesis_data.get("voice_name"),
                    "audio_size": synthesis_data.get("audio_size"),
                    "speaking_rate": synthesis_data.get("speaking_rate"),
                    "service": synthesis_data.get("service")
                }
            
            await self.message_repository.update_message_metadata(
                message_id=message_id,
                metadata_update={"voice": voice_metadata}
            )
            
        except Exception as e:
            logger.warning(f"Failed to update message voice metadata: {str(e)}")


def get_voice_service(
    message_repository: MessageRepository,
    session_repository: SessionRepository,
    chat_service: ChatService
) -> VoiceService:
    """Get a voice service instance."""
    return VoiceService(message_repository, session_repository, chat_service)
