"""
Simplified Voice service for Oprina API.

This module orchestrates speech-to-text and text-to-speech operations,
providing a unified interface for voice interactions with the AI agent.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from app.core.integrations.speech import SpeechToTextService, TextToSpeechService
from app.core.services.agent_service import AgentService
from app.core.database.repositories.message_repository import MessageRepository
from app.core.database.repositories.session_repository import SessionRepository
from app.utils.errors import ValidationError, OprinaError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class VoiceService:
    """
    Simplified service for handling voice interactions with the AI agent.
    
    This service coordinates:
    1. Speech-to-text conversion of user audio
    2. Text processing through the agent service
    3. Text-to-speech conversion of agent responses
    """
    
    def __init__(
        self,
        message_repository: MessageRepository,
        session_repository: SessionRepository,
        agent_service: AgentService
    ):
        self.message_repository = message_repository
        self.session_repository = session_repository
        self.agent_service = agent_service
        
        # Initialize speech services
        self.stt_service = SpeechToTextService()
        self.tts_service = TextToSpeechService()
    
    async def process_voice_message(
        self,
        user_id: str,
        session_id: str,
        audio_data: bytes,
        audio_format: str = "webm",
        include_audio_response: bool = True
    ) -> Dict[str, Any]:
        """
        Process a complete voice interaction: audio input -> text -> agent response -> audio output.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            audio_data: Raw audio bytes from user
            audio_format: Input audio format
            include_audio_response: Whether to generate audio response
            
        Returns:
            Dictionary with transcription, agent response, and optional audio
        """
        try:
            logger.info(f"Processing voice message for user {user_id}, session {session_id}")
            
            # Step 1: Convert speech to text
            transcription_result = await self.stt_service.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format
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
            
            # Step 2: Process text through agent service
            try:
                agent_response = await self.agent_service.send_message(
                    user_id=user_id,
                    session_id=session_id,
                    message=user_text
                )
                
                if not agent_response.get("response"):
                    return {
                        "success": False,
                        "error": "Agent processing failed",
                        "stage": "agent_processing",
                        "transcription": {
                            "text": user_text,
                            "confidence": transcription_result.get("confidence")
                        }
                    }
                
                agent_text = agent_response["response"]

                #Auto-generate title if this is the first user message
                try:
                    # Check if this is the first user message (message_index = 1)
                    if agent_response.get("user_message", {}).get("message_index") == 1:
                        # Auto-generate title from first voice message
                        await self.session_repository.auto_generate_title_from_message(
                            session_id, 
                            user_text
                        )
                        logger.info(f"Auto-generated title for voice session {session_id} from first message")
                except Exception as title_error:
                    # Don't fail the voice processing if title generation fails
                    logger.warning(f"Failed to auto-generate title for voice session {session_id}: {title_error}")
                
            except Exception as agent_error:
                logger.error(f"Agent service failed: {agent_error}")
                return {
                    "success": False,
                    "error": f"Agent processing failed: {str(agent_error)}",
                    "stage": "agent_processing",
                    "transcription": {
                        "text": user_text,
                        "confidence": transcription_result.get("confidence")
                    }
                }
            
            # Step 3: Convert agent response to speech (if requested)
            audio_response = None
            if include_audio_response and agent_text.strip():
                synthesis_result = await self.tts_service.synthesize_speech(
                    text=agent_text
                )
                
                if synthesis_result["success"]:
                    audio_response = {
                        "audio_content": synthesis_result["audio_content"],
                        "audio_format": synthesis_result["audio_format"],
                        "audio_size": synthesis_result["audio_size"]
                    }
                else:
                    logger.warning(f"TTS synthesis failed: {synthesis_result.get('error')}")
            
            # Step 4: Store voice metadata in the messages (already stored by agent_service)
            # The agent_service already stores both user and assistant messages
            # We just need to update the user message with voice metadata
            try:
                if agent_response.get("user_message", {}).get("id"):
                    user_message_id = agent_response["user_message"]["id"]
                    await self._update_message_voice_metadata(
                        message_id=user_message_id,
                        transcription_data=transcription_result,
                        synthesis_data=synthesis_result if include_audio_response else None
                    )
            except Exception as metadata_error:
                logger.warning(f"Failed to update voice metadata: {metadata_error}")
            
            # Return complete voice interaction result
            result = {
                "success": True,
                "transcription": {
                    "text": user_text,
                    "confidence": transcription_result.get("confidence", 0.0),
                    "service": transcription_result.get("service")
                },
                "chat_response": {
                    "text": agent_text,
                    "message_id": agent_response.get("assistant_message", {}).get("id"),
                    "session_id": session_id
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
        audio_format: str = "webm"
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text without processing through agent service.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format
            
        Returns:
            Transcription results
        """
        try:
            result = await self.stt_service.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format
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
        speaking_rate: float = 1.0
    ) -> Dict[str, Any]:
        """
        Convert text to speech without agent processing.
        
        Args:
            text: Text to convert to speech
            speaking_rate: Speech rate (0.25 to 4.0)
            
        Returns:
            Audio synthesis results
        """
        try:
            result = await self.tts_service.synthesize_speech(
                text=text,
                speaking_rate=speaking_rate
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
                    "service": transcription_data.get("service")
                }
            }
            
            if synthesis_data:
                voice_metadata["synthesis"] = {
                    "audio_size": synthesis_data.get("audio_size"),
                    "service": synthesis_data.get("service")
                }
            
            # Update the message with voice metadata
            # Note: This assumes your message repository has an update method
            await self.message_repository.update_message_metadata(
                message_id=message_id,
                metadata_update={"voice": voice_metadata}
            )
            
        except Exception as e:
            logger.warning(f"Failed to update message voice metadata: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if voice services are available."""
        return self.stt_service.is_available() and self.tts_service.is_available()