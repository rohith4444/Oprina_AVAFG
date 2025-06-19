"""
Session repository for managing user sessions.
Updated for simplified schema and proper field alignment.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client
import re

from app.core.database.models import BaseDBModel, RecordNotFoundError, serialize_for_db, handle_supabase_response
from app.core.database.schema_validator import TableNames
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SessionRepository:
    """Repository for session data operations."""
    
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table_name = TableNames.SESSIONS
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new session."""
        try:
            # Add timestamps
            session_data["created_at"] = datetime.utcnow().isoformat()
            session_data["updated_at"] = datetime.utcnow().isoformat()
            session_data["last_activity_at"] = datetime.utcnow().isoformat()
            
            # Set default values
            if "status" not in session_data:
                session_data["status"] = "active"
            if "title" not in session_data:
                session_data["title"] = "New Chat"
            
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
        """Get session with vertex session ID (removed avatar references)."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*")  # vertex_session_id already included
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
        vertex_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update session with vertex session ID."""
        try:
            update_data = {
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if vertex_session_id:
                update_data["vertex_session_id"] = vertex_session_id
            
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

    async def update_session_title(self, session_id: str, new_title: str) -> Dict[str, Any]:
        """Update session title with validation."""
        try:
            # Validate title length (15-20 chars as per your requirement)
            if len(new_title) < 1 or len(new_title) > 20:
                raise ValueError("Title must be between 1 and 20 characters")
            
            # Clean the title (remove extra spaces, etc.)
            cleaned_title = new_title.strip()
            
            update_data = {
                "title": cleaned_title,
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
            logger.info(f"Updated session title for {session_id}: '{cleaned_title}'")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update session title {session_id}: {e}")
            raise
    

    async def auto_generate_title_from_message(self, session_id: str, message_content: str) -> Dict[str, Any]:
        """Auto-generate session title from first message content."""
        try:
            # Generate title from message content (15-20 chars)
            title = self._generate_title_from_content(message_content)
            
            # Update session title
            return await self.update_session_title(session_id, title)
            
        except Exception as e:
            logger.error(f"Failed to auto-generate title for session {session_id}: {e}")
            raise

    def _generate_title_from_content(self, content: str) -> str:
        """Generate a 15-20 character title from message content."""
        if not content or not content.strip():
            return "New Chat"
        
        # Clean the content
        cleaned = content.strip()
        
        # Remove common voice patterns
        patterns_to_remove = [
            r'^(hi|hello|hey)\s+',
            r'^(can you|could you|please)\s+',
            r'^(i need|i want)\s+(to|help with)\s+',
            r'[.!?]+$'  # Remove ending punctuation
        ]
        
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = cleaned.strip()
        
        # If too short after cleaning, use original
        if len(cleaned) < 3:
            cleaned = content.strip()
        
        # Truncate to 15-20 characters
        if len(cleaned) <= 20:
            return cleaned
        
        # Smart truncation - try to break at word boundaries
        if len(cleaned) > 20:
            # Find last space before 18 chars to leave room for "..."
            truncate_pos = 17
            last_space = cleaned.rfind(' ', 0, truncate_pos)
            
            if last_space > 10:  # Only use space if it's not too early
                return cleaned[:last_space] + "..."
            else:
                return cleaned[:17] + "..."
        
        return cleaned


    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all sessions for a user, ordered by recent activity."""
        try:
            query = self.db.table(self.table_name).select("*").eq("user_id", user_id)
            
            if active_only:
                query = query.eq("status", "active")
            else:
                # Don't show deleted sessions even when active_only=False
                query = query.neq("status", "deleted")
            
            # Order by last_activity_at DESC for recent sessions first
            response = query.order("last_activity_at", desc=True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get user sessions {user_id}: {e}")
            raise
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a session by setting status to ended."""
        try:
            update_data = {
                "status": "ended",
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
    
    async def delete_session(self, session_id: str) -> bool:
        """Soft delete a session by setting status to deleted."""
        try:
            update_data = {
                "status": "deleted",
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
                logger.warning(f"Session {session_id} not found for deletion")
                return False
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
    
    async def get_session_by_vertex_id(self, vertex_session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by Vertex AI session ID (useful for voice service integration)."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*")
                .eq("vertex_session_id", vertex_session_id)
                .execute()
            )
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get session by vertex ID {vertex_session_id}: {e}")
            raise