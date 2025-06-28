"""
Agent service for orchestrating communication with deployed agent.
"""

from typing import Dict, Any, AsyncGenerator, Optional
import structlog
import asyncio

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
        """
        Create a new Vertex AI agent session and link it to user session.
        Gracefully handles Vertex AI failures - session creation still succeeds.
        """
        try:
            # Try to create Vertex AI session
            try:
                agent_session_data = await self.agent_client.create_session(user_id)
                vertex_session_id = agent_session_data["vertex_session_id"]
                
                # Update the user session with Vertex AI session ID
                await self.session_repo.update_session_links(
                    session_id=user_session_id,
                    vertex_session_id=vertex_session_id
                )
                
                logger.info(f"Created Vertex AI session {vertex_session_id} for user {user_id}")
                
                return {
                    "agent_session_id": vertex_session_id,
                    "user_session_id": user_session_id,
                    "user_id": user_id,
                    "status": "active",
                    "vertex_integration": True
                }
                
            except Exception as vertex_error:
                # Log the error but don't fail session creation
                logger.warning(f"Vertex AI session creation failed for user {user_id}: {vertex_error}")
                
                # Session creation still succeeds without Vertex AI
                return {
                    "agent_session_id": None,
                    "user_session_id": user_session_id,
                    "user_id": user_id,
                    "status": "active",
                    "vertex_integration": False,
                    "vertex_error": str(vertex_error)
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
        """Send a message to the agent with intelligent fallback."""
        try:
            # Get session with agent link
            session_data = await self.session_repo.get_session_with_links(session_id)
            
            # Try Vertex AI first if available
            if session_data and session_data.get("vertex_session_id"):
                try:
                    vertex_session_id = session_data["vertex_session_id"]
                    
                    # Store user message
                    user_message = await self.message_repo.create_message({
                        "session_id": session_id,
                        "user_id": user_id,
                        "role": "user",
                        "content": message,
                        "message_type": "text"
                    })

                    # Auto-generate title for first message
                    if user_message.get("message_index") == 1:
                        try:
                            await self.session_repo.auto_generate_title_from_message(session_id, message)
                            logger.info(f"Auto-generated title for session {session_id} from first message")
                        except Exception as title_error:
                            logger.warning(f"Failed to auto-generate title for session {session_id}: {title_error}")
                    
                    # Send to Vertex AI agent
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
                    
                    logger.info(f"Sent message to Vertex AI agent for session {session_id}")
                    return {
                        "user_message": user_message,
                        "assistant_message": assistant_message,
                        "response": agent_response["response"],
                        "session_id": session_id
                    }
                    
                except Exception as vertex_error:
                    logger.warning(f"Vertex AI failed for session {session_id}: {vertex_error}")
                    # Fall through to fallback response
            
            # Fallback response when Vertex AI is not available
            fallback_response = await self._generate_fallback_response(message, user_id)
            
            # Store user message for fallback case
            user_message = await self.message_repo.create_message({
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": message,
                "message_type": "text"
            })
            
            # Store fallback response
            assistant_message = await self.message_repo.create_message({
                "session_id": session_id,
                "user_id": user_id,
                "role": "assistant",
                "content": fallback_response,
                "message_type": "text"
            })
            
            # Update session activity
            await self.session_repo.update_last_activity(session_id)
            
            logger.info(f"Used fallback response for session {session_id}")
            return {
                "user_message": user_message,
                "assistant_message": assistant_message,
                "response": fallback_response,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to send message for session {session_id}: {e}", 
                        extra={"user_id": user_id, "session_id": session_id})
            raise AgentError(f"Failed to send message: {str(e)}")
    
    async def _generate_fallback_response(self, message: str, user_id: Optional[str] = None) -> str:
        """Generate intelligent fallback response with connection status awareness."""
        try:
            # Check if user has Gmail/Calendar connected
            connection_status = await self._check_connection_status(user_id)
            
            # Email-related requests
            if any(word in message.lower() for word in ["email", "gmail", "mail", "inbox", "send", "reply"]):
                if connection_status.get("gmail_connected"):
                    return "I can see your Gmail is connected! I'm currently running in simplified mode due to Vertex AI being unavailable. Your Gmail integration is working, but I need the full agent system to access your emails. You can try asking about your connection status or other general questions."
                else:
                    return "I'd be happy to help you with your emails! First, you'll need to connect Gmail. Please go to Settings → Connected Apps and click 'Connect' for Gmail to set up access."
            
            # Calendar-related requests
            elif any(word in message.lower() for word in ["calendar", "schedule", "meeting", "appointment", "event"]):
                if connection_status.get("calendar_connected"):
                    return "I can see your Google Calendar is connected! I'm currently running in simplified mode due to Vertex AI being unavailable. Your Calendar integration is working, but I need the full agent system to access your calendar. You can try asking about your connection status or other general questions."
                else:
                    return "I'd be happy to help you with your calendar! First, you'll need to connect Google Calendar. Please go to Settings → Connected Apps and click 'Connect' for Google Calendar to set up access."
            
            # Connected apps requests
            elif any(word in message.lower() for word in ["connected apps", "connect", "setup", "configure", "status", "connection"]):
                gmail_status = "✅ Connected" if connection_status.get("gmail_connected") else "❌ Not connected"
                calendar_status = "✅ Connected" if connection_status.get("calendar_connected") else "❌ Not connected"
                return f"Here's your current connection status:\n\nGmail: {gmail_status}\nGoogle Calendar: {calendar_status}\n\nGreat news! Your connected services are working properly. I'm currently in simplified mode due to Vertex AI being unavailable, but your integrations are ready to go once the full system is restored."
            
            # General greetings or unclear requests
            elif any(word in message.lower() for word in ['hello', 'hi', 'hey']) or len(message.strip()) < 10:
                gmail_status = "✅ Connected" if connection_status.get("gmail_connected") else "❌ Not connected"
                calendar_status = "✅ Connected" if connection_status.get("calendar_connected") else "❌ Not connected"
                
                if connection_status.get("gmail_connected") or connection_status.get("calendar_connected"):
                    return f"Hello! I'm Oprina, your voice assistant. I can see your services are connected:\n\nGmail: {gmail_status}\nGoogle Calendar: {calendar_status}\n\nI'm currently in simplified mode, but your integrations are working! How can I help you today?"
                else:
                    return "Hello! I'm Oprina, your voice assistant for Gmail and Calendar management. I'm currently running in simplified mode. To get started, please connect your accounts in Settings → Connected Apps. How can I help you today?"
            
            # Default response for other requests
            else:
                if connection_status.get("gmail_connected") or connection_status.get("calendar_connected"):
                    return "I'm Oprina, your voice assistant. Your account connections are working properly, but I'm currently in simplified mode due to system limitations. For full functionality, the Vertex AI agent system needs to be available. Is there anything else I can help you with?"
                else:
                    return "Hello! I'm Oprina, your voice assistant for Gmail and Calendar management. I'm currently running in simplified mode. To get started, please connect your accounts in Settings → Connected Apps. How can I help you today?"
                
        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            return "Hello! I'm Oprina, your voice assistant. I'm currently running in simplified mode. How can I help you today?"
    
    async def _check_connection_status(self, user_id: Optional[str] = None) -> Dict[str, bool]:
        """Check Gmail and Calendar connection status for the user."""
        status = {
            "gmail_connected": False,
            "calendar_connected": False
        }
        
        if not user_id:
            return status
            
        try:
            # Import the backend OAuth service to check user tokens
            from app.core.services.google_oauth_service import GoogleOAuthService
            from app.core.database.repositories.user_repository import UserRepository
            from app.core.database.connection import get_database_client
            
            # Create OAuth service to check user's connection status
            db_client = get_database_client()
            user_repo = UserRepository(db_client)
            oauth_service = GoogleOAuthService(user_repo)
            
            # Get user's connection status from database
            user_status = await oauth_service.get_service_connection_status(user_id)
            
            status["gmail_connected"] = user_status.get("gmail", {}).get("connected", False)
            status["calendar_connected"] = user_status.get("calendar", {}).get("connected", False)
            
            logger.debug(f"Connection status for user {user_id}: {status}")
            
        except Exception as e:
            logger.warning(f"Failed to check connection status for user {user_id}: {e}")
        
        return status
    
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