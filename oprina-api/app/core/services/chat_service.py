"""
Chat service for orchestrating complete chat experience.
"""

from typing import Dict, Any, AsyncGenerator, Optional
import structlog

from app.core.services.agent_service import AgentService
from app.core.services.user_service import UserService
from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.repositories.message_repository import MessageRepository
from app.core.database.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class ChatService:
    """Main service for orchestrating chat functionality."""
    
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        message_repo: MessageRepository
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.message_repo = message_repo
        
        # Initialize dependent services
        self.agent_service = AgentService(session_repo, message_repo)
        self.user_service = UserService(user_repo)
    
    async def create_chat_session(
        self, 
        user_id: str, 
        session_type: str = "chat"
    ) -> Dict[str, Any]:
        """Create a new chat session with agent integration."""
        try:
            # Verify user exists
            user = await self.user_service.get_user(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Create user session in database
            session_data = {
                "user_id": user_id,
                "session_type": session_type,
                "status": "active"
            }
            
            user_session = await self.session_repo.create_session(session_data)
            session_id = user_session["id"]
            
            # Create corresponding agent session
            agent_session = await self.agent_service.create_agent_session(
                user_id=user_id,
                user_session_id=session_id
            )
            
            logger.info(f"Created chat session {session_id} for user {user_id}")
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "agent_session_id": agent_session["agent_session_id"],
                "status": "active",
                "created_at": user_session["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create chat session for user {user_id}: {e}")
            raise
    
    async def send_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """Send a message in a chat session."""
        try:
            # Validate session ownership
            session = await self.session_repo.get_session_by_id(session_id)
            if not session or session.get("user_id") != user_id:
                raise ValueError("Invalid session or unauthorized access")
            
            if session.get("status") != "active":
                raise ValueError("Session is not active")
            
            # Send message through agent service
            result = await self.agent_service.send_message(
                user_id=user_id,
                session_id=session_id,
                message=message
            )
            
            logger.info(f"Sent message in session {session_id}")
            
            return {
                "session_id": session_id,
                "user_message": result["user_message"],
                "assistant_response": result["assistant_message"],
                "response_text": result["response"]
            }
            
        except Exception as e:
            logger.error(f"Failed to send message in session {session_id}: {e}")
            raise
    
    async def stream_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str,
        message_type: str = "text"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message and stream the response."""
        try:
            # Validate session ownership
            session = await self.session_repo.get_session_by_id(session_id)
            if not session or session.get("user_id") != user_id:
                yield {"type": "error", "error": "Invalid session or unauthorized access"}
                return
            
            if session.get("status") != "active":
                yield {"type": "error", "error": "Session is not active"}
                return
            
            # Stream message through agent service
            async for event in self.agent_service.stream_message(
                user_id=user_id,
                session_id=session_id,
                message=message
            ):
                yield event
            
            logger.info(f"Streamed message in session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to stream message in session {session_id}: {e}")
            yield {"type": "error", "error": str(e)}
    
    async def get_chat_history(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get chat history for a session."""
        try:
            # Validate session ownership
            session = await self.session_repo.get_session_by_id(session_id)
            if not session or session.get("user_id") != user_id:
                raise ValueError("Invalid session or unauthorized access")
            
            # Get conversation history
            messages = await self.agent_service.get_conversation_history(
                user_id=user_id,
                session_id=session_id,
                limit=limit
            )
            
            return {
                "session_id": session_id,
                "messages": messages,
                "total_messages": len(messages),
                "session_info": {
                    "status": session.get("status"),
                    "created_at": session.get("created_at"),
                    "last_activity_at": session.get("last_activity_at")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat history for session {session_id}: {e}")
            raise
    
    async def get_user_sessions(
        self, 
        user_id: str, 
        active_only: bool = True
    ) -> list[Dict[str, Any]]:
        """Get all chat sessions for a user."""
        try:
            # Get sessions from database
            sessions = await self.session_repo.get_user_sessions(
                user_id=user_id,
                active_only=active_only
            )
            
            # Enrich with message counts
            enriched_sessions = []
            for session in sessions:
                session_id = session["id"]
                
                # Get message count
                message_count = await self.message_repo.get_user_message_count(
                    user_id=user_id,
                    session_id=session_id
                )
                
                enriched_sessions.append({
                    "session_id": session_id,
                    "status": session.get("status"),
                    "created_at": session.get("created_at"),
                    "last_activity_at": session.get("last_activity_at"),
                    "message_count": message_count,
                    "has_agent_session": bool(session.get("vertex_session_id"))
                })
            
            return enriched_sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            raise
    
    async def end_chat_session(self, user_id: str, session_id: str) -> bool:
        """End a chat session."""
        try:
            # Validate session ownership
            session = await self.session_repo.get_session_by_id(session_id)
            if not session or session.get("user_id") != user_id:
                raise ValueError("Invalid session or unauthorized access")
            
            # End agent session
            await self.agent_service.end_session(user_id, session_id)
            
            logger.info(f"Ended chat session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            raise
    
    async def delete_message(
        self, 
        user_id: str, 
        message_id: str
    ) -> bool:
        """Delete a message from chat history."""
        try:
            # Validate through agent service (includes ownership check)
            result = await self.agent_service.message_handler.delete_message(
                message_id=message_id,
                user_id=user_id
            )
            
            logger.info(f"Deleted message {message_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            raise
    
    async def get_session_stats(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Get statistics for a chat session."""
        try:
            # Validate session ownership
            session = await self.session_repo.get_session_by_id(session_id)
            if not session or session.get("user_id") != user_id:
                raise ValueError("Invalid session or unauthorized access")
            
            # Get message count
            total_messages = await self.message_repo.get_user_message_count(
                user_id=user_id,
                session_id=session_id
            )
            
            # Get recent messages for analysis
            recent_messages = await self.message_repo.get_conversation_history(
                session_id=session_id,
                limit=10
            )
            
            user_messages = [msg for msg in recent_messages if msg.get("role") == "user"]
            assistant_messages = [msg for msg in recent_messages if msg.get("role") == "assistant"]
            
            return {
                "session_id": session_id,
                "total_messages": total_messages,
                "user_messages_count": len(user_messages),
                "assistant_messages_count": len(assistant_messages),
                "session_duration": None,  # TODO: Calculate from created_at to last_activity_at
                "last_activity": session.get("last_activity_at"),
                "status": session.get("status")
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats for {session_id}: {e}")
            raise
