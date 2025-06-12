"""
Message handler for routing messages between users and the deployed agent.
"""

from typing import Dict, Any, AsyncGenerator, Optional
from datetime import datetime
import structlog

from app.core.agent.client import agent_client
from app.core.database.repositories.message_repository import MessageRepository
from app.core.database.repositories.session_repository import SessionRepository

logger = structlog.get_logger(__name__)


class MessageHandler:
    """Handles message routing and processing between users and agent."""
    
    def __init__(
        self, 
        message_repo: MessageRepository,
        session_repo: SessionRepository
    ):
        self.message_repo = message_repo
        self.session_repo = session_repo
        self.agent_client = agent_client
    
    async def send_message(
        self, 
        user_id: str, 
        session_id: str, 
        message_content: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """Send a message to the agent and get response."""
        try:
            # Get session with agent link
            session_data = await self.session_repo.get_session_with_links(session_id)
            
            if not session_data or not session_data.get("vertex_session_id"):
                raise ValueError(f"No agent session found for session {session_id}")
            
            vertex_session_id = session_data["vertex_session_id"]
            
            # Store user message
            user_message = await self.message_repo.create_message({
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": message_content,
                "message_type": message_type,
                "metadata": {
                    "vertex_session_id": vertex_session_id
                }
            })
            
            # Send to agent
            agent_response = await self.agent_client.send_message(
                user_id=user_id,
                session_id=vertex_session_id,
                message=message_content
            )
            
            # Store agent response
            assistant_message = await self.message_repo.create_message({
                "session_id": session_id,
                "user_id": user_id,
                "role": "assistant",
                "content": agent_response["response"],
                "message_type": "text",
                "metadata": {
                    "vertex_session_id": vertex_session_id,
                    "agent_response_data": agent_response
                }
            })
            
            # Update session activity
            await self.session_repo.update_last_activity(session_id)
            
            logger.info(f"Processed message for session {session_id}")
            
            return {
                "user_message": user_message,
                "assistant_message": assistant_message,
                "response": agent_response["response"],
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send message for session {session_id}: {e}")
            raise
    
    async def stream_message(
        self, 
        user_id: str, 
        session_id: str, 
        message_content: str,
        message_type: str = "text"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message to the agent and stream the response."""
        try:
            # Get session with agent link
            session_data = await self.session_repo.get_session_with_links(session_id)
            
            if not session_data or not session_data.get("vertex_session_id"):
                raise ValueError(f"No agent session found for session {session_id}")
            
            vertex_session_id = session_data["vertex_session_id"]
            
            # Store user message
            user_message = await self.message_repo.create_message({
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": message_content,
                "message_type": message_type,
                "metadata": {
                    "vertex_session_id": vertex_session_id
                }
            })
            
            # Yield user message first
            yield {
                "type": "user_message",
                "message": user_message,
                "session_id": session_id
            }
            
            # Stream response from agent
            response_parts = []
            
            async for event in self.agent_client.stream_message(
                user_id=user_id,
                session_id=vertex_session_id,
                message=message_content
            ):
                # Extract content from event
                event_content = self._extract_event_content(event)
                
                if event_content:
                    response_parts.append(event_content)
                    
                    yield {
                        "type": "agent_response_chunk",
                        "content": event_content,
                        "session_id": session_id,
                        "event": event
                    }
            
            # Store complete agent response
            full_response = " ".join(response_parts).strip()
            
            if full_response:
                assistant_message = await self.message_repo.create_message({
                    "session_id": session_id,
                    "user_id": user_id,
                    "role": "assistant",
                    "content": full_response,
                    "message_type": "text",
                    "metadata": {
                        "vertex_session_id": vertex_session_id,
                        "streaming": True
                    }
                })
                
                yield {
                    "type": "agent_response_complete",
                    "message": assistant_message,
                    "session_id": session_id
                }
            
            # Update session activity
            await self.session_repo.update_last_activity(session_id)
            
            logger.info(f"Streamed message for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to stream message for session {session_id}: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 20
    ) -> list[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            messages = await self.message_repo.get_conversation_history(
                session_id=session_id,
                limit=limit
            )
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation history for {session_id}: {e}")
            raise
    
    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message (with user authorization)."""
        try:
            # Get message to verify ownership
            message = await self.message_repo.get_message_by_id(message_id)
            
            if not message:
                return False
            
            if message.get("user_id") != user_id:
                raise ValueError("User not authorized to delete this message")
            
            return await self.message_repo.delete_message(message_id)
            
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            raise
    
    def _extract_event_content(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract content from a streaming event."""
        try:
            if isinstance(event, dict):
                # Try different possible content fields
                if "event" in event:
                    inner_event = event["event"]
                    if hasattr(inner_event, "content"):
                        return str(inner_event.content)
                    elif isinstance(inner_event, dict) and "content" in inner_event:
                        return str(inner_event["content"])
                    elif isinstance(inner_event, str):
                        return inner_event
                
                if "content" in event:
                    return str(event["content"])
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract content from event: {e}")
            return None
