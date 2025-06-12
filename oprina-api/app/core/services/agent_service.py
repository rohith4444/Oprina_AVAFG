"""
Agent service for orchestrating communication with deployed agent.
"""

from typing import Dict, Any, AsyncGenerator, Optional
import structlog

from app.core.agent.client import agent_client
from app.core.agent.session_manager import AgentSessionManager
from app.core.agent.message_handler import MessageHandler
from app.core.agent.error_handler import agent_error_handler, AgentError
from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.repositories.message_repository import MessageRepository

logger = structlog.get_logger(__name__)


class AgentService:
    """Service for agent communication and session management."""
    
    def __init__(
        self,
        session_repo: SessionRepository,
        message_repo: MessageRepository
    ):
        self.session_repo = session_repo
        self.message_repo = message_repo
        
        # Initialize agent components
        self.session_manager = AgentSessionManager(session_repo)
        self.message_handler = MessageHandler(message_repo, session_repo)
        self.agent_client = agent_client
        self.error_handler = agent_error_handler
    
    async def create_agent_session(
        self, 
        user_id: str, 
        user_session_id: str
    ) -> Dict[str, Any]:
        """Create a new agent session."""
        try:
            session_data = await self.session_manager.create_agent_session(
                user_id=user_id,
                user_session_id=user_session_id
            )
            
            logger.info(f"Created agent session for user {user_id}")
            return session_data
            
        except Exception as e:
            context = {"user_id": user_id, "user_session_id": user_session_id}
            error_response = self.error_handler.handle_error(e, context)
            raise AgentError(
                error_response["message"],
                details=error_response
            )
    
    async def send_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """Send a message to the agent."""
        try:
            # Validate session
            if not await self.session_manager.validate_session(user_id, session_id):
                raise AgentError("Invalid or expired session")
            
            # Send message through handler
            result = await self.message_handler.send_message(
                user_id=user_id,
                session_id=session_id,
                message_content=message
            )
            
            # Reset error count on successful message
            self.error_handler.reset_error_count({"user_id": user_id, "session_id": session_id})
            
            logger.info(f"Sent message to agent for session {session_id}")
            return result
            
        except Exception as e:
            context = {"user_id": user_id, "session_id": session_id, "message": message}
            error_response = self.error_handler.handle_error(e, context)
            
            # Increment error count
            self.error_handler.increment_error_count(context)
            
            raise AgentError(
                error_response["message"],
                details=error_response
            )
    
    async def stream_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message to the agent and stream the response."""
        try:
            # Validate session
            if not await self.session_manager.validate_session(user_id, session_id):
                yield {"type": "error", "error": "Invalid or expired session"}
                return
            
            # Stream message through handler
            async for event in self.message_handler.stream_message(
                user_id=user_id,
                session_id=session_id,
                message_content=message
            ):
                yield event
            
            # Reset error count on successful stream
            self.error_handler.reset_error_count({"user_id": user_id, "session_id": session_id})
            
            logger.info(f"Streamed message to agent for session {session_id}")
            
        except Exception as e:
            context = {"user_id": user_id, "session_id": session_id, "message": message}
            error_response = self.error_handler.handle_error(e, context)
            
            # Increment error count
            self.error_handler.increment_error_count(context)
            
            yield {
                "type": "error", 
                "error": error_response["message"],
                "details": error_response
            }
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 20
    ) -> list[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            # Validate session ownership
            if not await self.session_manager.validate_session(user_id, session_id):
                raise AgentError("Invalid or expired session")
            
            messages = await self.message_handler.get_conversation_history(
                session_id=session_id,
                limit=limit
            )
            
            return messages
            
        except Exception as e:
            context = {"user_id": user_id, "session_id": session_id}
            error_response = self.error_handler.handle_error(e, context)
            raise AgentError(
                error_response["message"],
                details=error_response
            )
    
    async def get_user_sessions(self, user_id: str) -> list[Dict[str, Any]]:
        """Get all agent sessions for a user."""
        try:
            sessions = await self.session_manager.list_user_agent_sessions(user_id)
            return sessions
            
        except Exception as e:
            context = {"user_id": user_id}
            error_response = self.error_handler.handle_error(e, context)
            raise AgentError(
                error_response["message"],
                details=error_response
            )
    
    async def end_session(self, user_id: str, session_id: str) -> bool:
        """End an agent session."""
        try:
            # Validate session ownership
            if not await self.session_manager.validate_session(user_id, session_id):
                raise AgentError("Invalid or expired session")
            
            # End session in database
            await self.session_repo.end_session(session_id)
            
            # Clean up error counts
            self.error_handler.reset_error_count({"user_id": user_id, "session_id": session_id})
            
            logger.info(f"Ended agent session {session_id}")
            return True
            
        except Exception as e:
            context = {"user_id": user_id, "session_id": session_id}
            error_response = self.error_handler.handle_error(e, context)
            raise AgentError(
                error_response["message"],
                details=error_response
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health and connectivity."""
        try:
            is_healthy = await self.agent_client.health_check()
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "agent_available": is_healthy,
                "timestamp": logger._structlog_kwargs.get("timestamp", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Agent health check failed: {e}")
            return {
                "status": "unhealthy",
                "agent_available": False,
                "error": str(e)
            }
