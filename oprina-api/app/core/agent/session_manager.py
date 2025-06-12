"""
Agent session manager for handling session lifecycle with deployed agent.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import structlog

from app.core.agent.client import agent_client
from app.core.database.repositories.session_repository import SessionRepository

logger = structlog.get_logger(__name__)


class AgentSessionManager:
    """Manages agent sessions and their lifecycle."""
    
    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo
        self.agent_client = agent_client
    
    async def create_agent_session(
        self, 
        user_id: str, 
        user_session_id: str
    ) -> Dict[str, Any]:
        """Create a new agent session linked to a user session."""
        try:
            # Create agent session with Vertex AI
            agent_session_data = await self.agent_client.create_session(user_id)
            
            # Update the user session with agent session ID
            await self.session_repo.update_session_links(
                session_id=user_session_id,
                vertex_session_id=agent_session_data["vertex_session_id"]
            )
            
            logger.info(
                f"Created agent session {agent_session_data['vertex_session_id']} "
                f"linked to user session {user_session_id}"
            )
            
            return {
                "agent_session_id": agent_session_data["vertex_session_id"],
                "user_session_id": user_session_id,
                "user_id": user_id,
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create agent session for user {user_id}: {e}")
            raise
    
    async def get_agent_session(
        self, 
        user_id: str, 
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get agent session information."""
        try:
            # Get session with links from database
            session_data = await self.session_repo.get_session_with_links(session_id)
            
            if not session_data or not session_data.get("vertex_session_id"):
                return None
            
            # Get agent session info from Vertex AI
            agent_session = await self.agent_client.get_session(
                user_id=user_id,
                session_id=session_data["vertex_session_id"]
            )
            
            return {
                "agent_session_id": agent_session["session_id"],
                "user_session_id": session_id,
                "user_id": user_id,
                "status": agent_session["status"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent session {session_id}: {e}")
            return None
    
    async def list_user_agent_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """List all agent sessions for a user."""
        try:
            # Get user sessions from database
            user_sessions = await self.session_repo.get_user_sessions(user_id)
            
            agent_sessions = []
            
            for session in user_sessions:
                if session.get("vertex_session_id"):
                    try:
                        agent_session = await self.agent_client.get_session(
                            user_id=user_id,
                            session_id=session["vertex_session_id"]
                        )
                        
                        agent_sessions.append({
                            "agent_session_id": agent_session["session_id"],
                            "user_session_id": session["id"],
                            "user_id": user_id,
                            "status": agent_session["status"],
                            "created_at": session.get("created_at"),
                            "last_activity_at": session.get("last_activity_at")
                        })
                        
                    except Exception as e:
                        # Skip sessions that can't be retrieved
                        logger.warning(f"Could not retrieve agent session for {session['id']}: {e}")
                        continue
            
            return agent_sessions
            
        except Exception as e:
            logger.error(f"Failed to list agent sessions for user {user_id}: {e}")
            raise
    
    async def update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp."""
        try:
            await self.session_repo.update_last_activity(session_id)
            
        except Exception as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            # Don't raise - this is not critical
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up inactive agent sessions older than specified hours."""
        try:
            # This would typically involve:
            # 1. Finding sessions older than max_age_hours
            # 2. Checking if they're still active with the agent
            # 3. Marking inactive ones as ended
            
            # For now, just return 0 as placeholder
            # TODO: Implement actual cleanup logic
            
            logger.info(f"Session cleanup completed")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup inactive sessions: {e}")
            raise
    
    async def validate_session(self, user_id: str, session_id: str) -> bool:
        """Validate that a session exists and is active."""
        try:
            session_data = await self.get_agent_session(user_id, session_id)
            
            return (
                session_data is not None and 
                session_data.get("status") == "active" and
                session_data.get("user_id") == user_id
            )
            
        except Exception as e:
            logger.error(f"Failed to validate session {session_id}: {e}")
            return False
