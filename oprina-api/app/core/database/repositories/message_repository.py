"""
Message repository for managing chat messages.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client
import structlog

from app.core.database.models import BaseDBModel, RecordNotFoundError, serialize_for_db, handle_supabase_response

logger = structlog.get_logger(__name__)


class MessageRepository:
    """Repository for message data operations."""
    
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table_name = "messages"
    
    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new message."""
        try:
            # Add timestamp
            message_data["created_at"] = datetime.utcnow().isoformat()
            message_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Serialize data
            serialized_data = serialize_for_db(message_data)
            
            # Insert message
            response = self.db.table(self.table_name).insert(serialized_data).execute()
            
            result = handle_supabase_response(response)
            logger.info(f"Created message with ID: {result.get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create message: {e}")
            raise
    
    async def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get message by ID."""
        try:
            response = self.db.table(self.table_name).select("*").eq("id", message_id).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {e}")
            raise
    
    async def get_session_messages(
        self, 
        session_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a session with pagination."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=False)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get session messages {session_id}: {e}")
            raise
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history for a session."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            # Reverse to get chronological order
            messages = response.data or []
            return list(reversed(messages))
            
        except Exception as e:
            logger.error(f"Failed to get conversation history {session_id}: {e}")
            raise
    
    async def update_message(self, message_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update message data."""
        try:
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Serialize data
            serialized_data = serialize_for_db(update_data)
            
            # Update message
            response = (
                self.db.table(self.table_name)
                .update(serialized_data)
                .eq("id", message_id)
                .execute()
            )
            
            if not response.data:
                raise RecordNotFoundError(f"Message {message_id} not found")
            
            result = handle_supabase_response(response)
            logger.info(f"Updated message {message_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update message {message_id}: {e}")
            raise
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete message."""
        try:
            response = self.db.table(self.table_name).delete().eq("id", message_id).execute()
            
            if not response.data:
                raise RecordNotFoundError(f"Message {message_id} not found")
            
            logger.info(f"Deleted message {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            raise
    
    async def get_user_message_count(self, user_id: str, session_id: Optional[str] = None) -> int:
        """Get total message count for a user."""
        try:
            query = self.db.table(self.table_name).select("id", count="exact").eq("user_id", user_id)
            
            if session_id:
                query = query.eq("session_id", session_id)
            
            response = query.execute()
            
            return response.count or 0
            
        except Exception as e:
            logger.error(f"Failed to get message count for user {user_id}: {e}")
            raise 