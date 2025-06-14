"""
Agent service for orchestrating communication with deployed agent.
"""

from typing import Dict, Any, AsyncGenerator, Optional
import structlog

from app.core.integrations.client import agent_client
from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.repositories.message_repository import MessageRepository

logger = structlog.get_logger(__name__)


class AgentError(Exception):
    """Simple agent error for service operations."""
    pass


class AgentService:
    """Service for agent communication and session management."""
    
    def __init__(
        self,
        session_repo: SessionRepository,
        message_repo: MessageRepository
    ):
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.agent_client = agent_client
    
    async def create_agent_session(
        self, 
        user_id: str, 
        user_session_id: str
    ) -> Dict[str, Any]:
        """Create a new agent session and link it to user session."""
        try:
            # Create agent session directly with Vertex AI
            agent_session_data = await self.agent_client.create_session(user_id)
            
            # Update the user session with agent session ID
            await self.session_repo.update_session_links(
                session_id=user_session_id,
                vertex_session_id=agent_session_data["vertex_session_id"]
            )
            
            logger.info(f"Created agent session for user {user_id}")
            return {
                "agent_session_id": agent_session_data["vertex_session_id"],
                "user_session_id": user_session_id,
                "user_id": user_id,
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to create agent session for user {user_id}: {e}")
            raise AgentError(f"Failed to create agent session: {str(e)}")
    
    async def send_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """Send a message to the agent."""
        try:
            # Get session with agent link
            session_data = await self.session_repo.get_session_with_links(session_id)
            
            if not session_data or not session_data.get("vertex_session_id"):
                raise AgentError("No agent session found")
            
            vertex_session_id = session_data["vertex_session_id"]
            
            # Store user message
            user_message = await self.message_repo.create_message({
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": message,
                "message_type": "text"
            })
            
            # Send to agent directly
            agent_response = await self.agent_client.send_message(
                user_id=user_id,
                session_id=vertex_session_id,
                message=message
            )
            
            # Store agent response
            assistant_message = await self.message_repo.create_message({
                "session_id": session_id,
                "user_id": user_id,
                "role": "assistant",
                "content": agent_response["response"],
                "message_type": "text"
            })
            
            # Update session activity
            await self.session_repo.update_last_activity(session_id)
            
            logger.info(f"Sent message to agent for session {session_id}")
            return {
                "user_message": user_message,
                "assistant_message": assistant_message,
                "response": agent_response["response"],
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send message for session {session_id}: {e}", 
                        extra={"user_id": user_id, "session_id": session_id})
            raise AgentError(f"Failed to send message: {str(e)}")
    
    async def stream_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message to the agent and stream the response."""
        try:
            # Get session with agent link
            session_data = await self.session_repo.get_session_with_links(session_id)
            
            if not session_data or not session_data.get("vertex_session_id"):
                yield {"type": "error", "error": "No agent session found"}
                return
            
            vertex_session_id = session_data["vertex_session_id"]
            
            # Store user message
            user_message = await self.message_repo.create_message({
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": message,
                "message_type": "text"
            })
            
            yield {
                "type": "user_message",
                "message": user_message,
                "session_id": session_id
            }
            
            # Stream from agent directly
            response_parts = []
            
            async for event in self.agent_client.stream_message(
                user_id=user_id,
                session_id=vertex_session_id,
                message=message
            ):
                # Extract content from event
                if event.get("content"):
                    response_parts.append(event["content"])
                    
                    yield {
                        "type": "agent_response_chunk",
                        "content": event["content"],
                        "session_id": session_id
                    }
            
            # Store complete response
            full_response = " ".join(response_parts).strip()
            
            if full_response:
                assistant_message = await self.message_repo.create_message({
                    "session_id": session_id,
                    "user_id": user_id,
                    "role": "assistant",
                    "content": full_response,
                    "message_type": "text"
                })
                
                yield {
                    "type": "agent_response_complete",
                    "message": assistant_message,
                    "session_id": session_id
                }
            
            # Update session activity
            await self.session_repo.update_last_activity(session_id)
            
            logger.info(f"Streamed message to agent for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to stream message for session {session_id}: {e}",
                        extra={"user_id": user_id, "session_id": session_id})
            yield {
                "type": "error",
                "error": f"Failed to stream message: {str(e)}",
                "session_id": session_id
            }

    async def get_user_sessions(self, user_id: str) -> list[Dict[str, Any]]:
        """Get all sessions for a user from database."""
        try:
            # Get sessions directly from database - no need to query Vertex AI
            sessions = await self.session_repo.get_user_sessions(user_id)
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            raise AgentError(f"Failed to get user sessions: {str(e)}")

    async def get_conversation_history(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 20
    ) -> list[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            # Get conversation history directly from message repository
            messages = await self.message_repo.get_conversation_history(
                session_id=session_id,
                limit=limit
            )
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation history for session {session_id}: {e}",
                        extra={"user_id": user_id, "session_id": session_id})
            raise AgentError(f"Failed to get conversation history: {str(e)}")
