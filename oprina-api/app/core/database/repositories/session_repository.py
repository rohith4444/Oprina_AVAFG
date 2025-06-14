"""
Session repository for managing user sessions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client
import structlog

from app.core.database.models import BaseDBModel, RecordNotFoundError, serialize_for_db, handle_supabase_response
from app.core.database.schema_validator import TableNames

logger = structlog.get_logger(__name__)


class SessionRepository:
    """Repository for session data operations."""
    
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table_name = TableNames.SESSIONS  # Fixed: was "user_sessions"
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new session."""
        try:
            # Add timestamp
            session_data["created_at"] = datetime.utcnow().isoformat()
            session_data["updated_at"] = datetime.utcnow().isoformat()
            session_data["last_activity_at"] = datetime.utcnow().isoformat()
            
            # Default values
            if "status" not in session_data:
                session_data["status"] = "active"
            
            # Serialize data
            serialized_data = serialize_for_db(session_data)
            
            # Insert session
            response = self.db.table(self.table_name).insert(serialized_data).execute()
            
            result = handle_supabase_response(response)
            logger.info(f"Created session with ID: {result.get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        try:
            response = self.db.table(self.table_name).select("*").eq("id", session_id).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise
    
    async def get_session_with_links(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session with all linked session IDs."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*, vertex_session_id, avatar_session_id")
                .eq("id", session_id)
                .execute()
            )
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get session with links {session_id}: {e}")
            raise
    
    async def update_session_links(
        self, 
        session_id: str, 
        vertex_session_id: Optional[str] = None,
        avatar_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update session with linked session IDs."""
        try:
            update_data = {
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if vertex_session_id:
                update_data["vertex_session_id"] = vertex_session_id
            if avatar_session_id:
                update_data["avatar_session_id"] = avatar_session_id
            
            # Serialize data
            serialized_data = serialize_for_db(update_data)
            
            # Update session
            response = (
                self.db.table(self.table_name)
                .update(serialized_data)
                .eq("id", session_id)
                .execute()
            )
            
            if not response.data:
                raise RecordNotFoundError(f"Session {session_id} not found")
            
            result = handle_supabase_response(response)
            logger.info(f"Updated session links for {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update session links {session_id}: {e}")
            raise
    
    async def update_last_activity(self, session_id: str) -> Dict[str, Any]:
        """Update session last activity timestamp."""
        try:
            update_data = {
                "last_activity_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Serialize data
            serialized_data = serialize_for_db(update_data)
            
            # Update session
            response = (
                self.db.table(self.table_name)
                .update(serialized_data)
                .eq("id", session_id)
                .execute()
            )
            
            if not response.data:
                raise RecordNotFoundError(f"Session {session_id} not found")
            
            result = handle_supabase_response(response)
            return result
            
        except Exception as e:
            logger.error(f"Failed to update last activity {session_id}: {e}")
            raise
    
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        try:
            query = self.db.table(self.table_name).select("*").eq("user_id", user_id)
            
            if active_only:
                query = query.eq("status", "active")
            
            response = query.execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get user sessions {user_id}: {e}")
            raise
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a session by setting status to inactive."""
        try:
            update_data = {
                "status": "inactive",
                "ended_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Serialize data
            serialized_data = serialize_for_db(update_data)
            
            # Update session
            response = (
                self.db.table(self.table_name)
                .update(serialized_data)
                .eq("id", session_id)
                .execute()
            )
            
            if not response.data:
                raise RecordNotFoundError(f"Session {session_id} not found")
            
            result = handle_supabase_response(response)
            logger.info(f"Ended session {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            raise 