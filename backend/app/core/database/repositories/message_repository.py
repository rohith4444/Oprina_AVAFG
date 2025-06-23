"""
Message repository for managing chat messages.
Updated for simplified schema and voice integration.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client

from app.core.database.models import BaseDBModel, RecordNotFoundError, serialize_for_db, handle_supabase_response
from app.core.database.schema_validator import TableNames
from app.utils.logging import get_logger

logger = get_logger(__name__)


class MessageRepository:
    """Repository for message data operations."""
    
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table_name = TableNames.MESSAGES
    
    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new message (voice or text)."""
        try:
            # Add timestamp (only created_at, no updated_at in schema)
            message_data["created_at"] = datetime.utcnow().isoformat()
            
            # Set defaults for voice integration
            if "message_type" not in message_data:
                message_data["message_type"] = "text"
            if "voice_metadata" not in message_data:
                message_data["voice_metadata"] = {}
            
            # Note: message_index will be auto-set by database trigger
            # Don't set it manually unless specifically needed
            
            # Validate required fields
            required_fields = ["session_id", "user_id", "role", "content"]
            for field in required_fields:
                if field not in message_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate role
            if message_data["role"] not in ["user", "assistant"]:
                raise ValueError(f"Invalid role: {message_data['role']}")
            
            # Serialize data
            serialized_data = serialize_for_db(message_data)
            
            # Insert message
            response = self.db.table(self.table_name).insert(serialized_data).execute()
            
            result = handle_supabase_response(response)
            logger.info(f"Created message with ID: {result.get('id')} for session: {message_data.get('session_id')}")
            
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

    async def get_first_user_message(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the first user message in a session for title generation."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .eq("role", "user")
                .order("message_index", desc=False)  # First message first
                .limit(1)
                .execute()
            )
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get first user message {session_id}: {e}")
            raise
    
    async def get_session_messages(
        self, 
        session_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages for a session in chronological order."""
        try:
            query = (
                self.db.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("message_index", desc=False)  # Chronological order
            )
            
            # Apply limit if specified
            if limit > 0:
                query = query.limit(limit)
            
            response = query.execute()
            
            messages = response.data or []
            logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
            
            return messages
            
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
                .order("message_index", desc=False)  # Chronological order
                .limit(limit)
                .execute()
            )
            
            messages = response.data or []
            logger.debug(f"Retrieved {len(messages)} conversation messages for session {session_id}")
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation history {session_id}: {e}")
            raise
    
    async def get_latest_messages(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get the most recent messages for a session (useful for UI)."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("message_index", desc=True)  # Most recent first
                .limit(limit)
                .execute()
            )
            
            # Reverse to get chronological order
            messages = response.data or []
            return list(reversed(messages))
            
        except Exception as e:
            logger.error(f"Failed to get latest messages {session_id}: {e}")
            raise
    
    async def get_messages_by_role(
        self, 
        session_id: str, 
        role: str
    ) -> List[Dict[str, Any]]:
        """Get messages by role (user or assistant) for a session."""
        try:
            if role not in ["user", "assistant"]:
                raise ValueError(f"Invalid role: {role}")
            
            response = (
                self.db.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .eq("role", role)
                .order("message_index", desc=False)
                .execute()
            )
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get {role} messages for session {session_id}: {e}")
            raise
    
    async def get_voice_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all voice messages for a session."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .eq("message_type", "voice")
                .order("message_index", desc=False)
                .execute()
            )
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get voice messages for session {session_id}: {e}")
            raise
    
    async def count_session_messages(self, session_id: str) -> int:
        """Count total messages in a session."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("id", count="exact")
                .eq("session_id", session_id)
                .execute()
            )
            
            return response.count or 0
            
        except Exception as e:
            logger.error(f"Failed to count messages for session {session_id}: {e}")
            raise
    
    async def get_message_context(
        self, 
        session_id: str, 
        around_message_index: int, 
        context_size: int = 5
    ) -> List[Dict[str, Any]]:
        """Get messages around a specific message index (useful for context)."""
        try:
            start_index = max(1, around_message_index - context_size)
            end_index = around_message_index + context_size
            
            response = (
                self.db.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .gte("message_index", start_index)
                .lte("message_index", end_index)
                .order("message_index", desc=False)
                .execute()
            )
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get message context for session {session_id}: {e}")
            raise

    async def update_message_metadata(
        self, 
        message_id: str, 
        metadata_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update message metadata (e.g., voice processing data)."""
        try:
            update_data = {
                "voice_metadata": metadata_update,
                "updated_at": datetime.utcnow().isoformat()
            }
            
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
            logger.debug(f"Updated metadata for message {message_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update message metadata {message_id}: {e}")
            raise