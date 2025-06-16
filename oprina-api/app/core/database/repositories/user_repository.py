"""
User repository for managing user data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client
import structlog

from app.core.database.models import RecordNotFoundError, serialize_for_db, handle_supabase_response
from app.core.database.schema_validator import TableNames

logger = structlog.get_logger(__name__)


class UserRepository:
    """Repository for user data operations."""
    
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table_name = TableNames.USERS
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with support for new UI fields."""
        try:
            # Set defaults and add timestamps
            user_data["created_at"] = datetime.utcnow().isoformat()
            user_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Set default values for new fields if not provided
            if "is_active" not in user_data:
                user_data["is_active"] = True
            if "is_verified" not in user_data:
                user_data["is_verified"] = False
            if "preferences" not in user_data:
                user_data["preferences"] = {}
            if "timezone" not in user_data:
                user_data["timezone"] = "UTC"
            if "language" not in user_data:
                user_data["language"] = "en"
            
            # Support new UI fields
            # full_name, preferred_name, work_type, ai_preferences
            # These will be included if present in user_data
            
            # Serialize data
            serialized_data = serialize_for_db(user_data)
            
            # Insert user
            response = self.db.table(self.table_name).insert(serialized_data).execute()
            
            result = handle_supabase_response(response)
            logger.info(f"Created user with ID: {result.get('id')} and email: {result.get('email')}")
            
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
        """Update user data with support for new UI fields."""
        try:
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # The method now supports all fields including:
            # - full_name, preferred_name (profile fields)
            # - work_type, ai_preferences (UI specific fields)  
            # - display_name, avatar_url (existing fields)
            # - Any other user fields
            
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

    # 1. ADD: Missing method referenced in dependencies.py
    async def update_last_login(self, user_id: str) -> Dict[str, Any]:
        """Update user's last login timestamp."""
        try:
            update_data = {
                "last_login_at": datetime.utcnow().isoformat(),
                "last_activity_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
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
            logger.info(f"Updated last login for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {e}")
            raise

    # 2. ADD: Change password method
    async def change_password(self, user_id: str, password_hash: str) -> Dict[str, Any]:
        """Change user's password."""
        try:
            update_data = {
                "password_hash": password_hash,
                "updated_at": datetime.utcnow().isoformat()
            }
            
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
            logger.info(f"Password changed for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            raise

    # 3. ADD: Deactivate user method (soft delete)
    async def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate user account (soft delete)."""
        try:
            update_data = {
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }
            
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
            logger.info(f"Deactivated user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise

    # 4. ADD: Update preferences method (for your UI)
    async def update_preferences(self, user_id: str, preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences (work_type, ai_preferences, etc.)."""
        try:
            update_data = {
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add preference fields if provided
            if "work_type" in preferences_data:
                update_data["work_type"] = preferences_data["work_type"]
            if "ai_preferences" in preferences_data:
                update_data["ai_preferences"] = preferences_data["ai_preferences"]
            if "preferences" in preferences_data:
                update_data["preferences"] = preferences_data["preferences"]
            if "timezone" in preferences_data:
                update_data["timezone"] = preferences_data["timezone"]
            if "language" in preferences_data:
                update_data["language"] = preferences_data["language"]
            
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
            logger.info(f"Updated preferences for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            raise

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile with fields from your UI form."""
        try:
            # Add updated timestamp
            update_data = profile_data.copy()
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
            logger.info(f"Updated profile for user {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update profile for user {user_id}: {e}")
            raise


    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with all fields needed for the UI."""
        try:
            response = self.db.table(self.table_name).select(
                "id, email, full_name, preferred_name, work_type, ai_preferences, "
                "display_name, avatar_url, timezone, language, is_active, is_verified, "
                "has_google_oauth, has_microsoft_oauth, created_at, updated_at, "
                "last_login_at, last_activity_at, email_verified_at, preferences"
            ).eq("id", user_id).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get user profile {user_id}: {e}")
            raise
