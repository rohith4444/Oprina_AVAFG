"""
User repository for managing user data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client
import structlog

from app.core.database.models import RecordNotFoundError, serialize_for_db, handle_supabase_response

logger = structlog.get_logger(__name__)


class UserRepository:
    """Repository for user data operations."""
    
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table_name = "users"
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        try:
            # Add timestamp
            user_data["created_at"] = datetime.utcnow().isoformat()
            user_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Serialize data
            serialized_data = serialize_for_db(user_data)
            
            # Insert user
            response = self.db.table(self.table_name).insert(serialized_data).execute()
            
            result = handle_supabase_response(response)
            logger.info(f"Created user with ID: {result.get('id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = self.db.table(self.table_name).select("*").eq("id", user_id).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            response = self.db.table(self.table_name).select("*").eq("email", email).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data."""
        try:
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Serialize data
            serialized_data = serialize_for_db(update_data)
            
            # Update user
            response = (
                self.db.table(self.table_name)
                .update(serialized_data)
                .eq("id", user_id)
                .execute()
            )
            
            if not response.data:
                raise RecordNotFoundError(f"User {user_id} not found")
            
            result = handle_supabase_response(response)
            logger.info(f"Updated user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        try:
            response = self.db.table(self.table_name).delete().eq("id", user_id).execute()
            
            if not response.data:
                raise RecordNotFoundError(f"User {user_id} not found")
            
            logger.info(f"Deleted user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    async def list_users(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List users with pagination."""
        try:
            response = (
                self.db.table(self.table_name)
                .select("*")
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise 