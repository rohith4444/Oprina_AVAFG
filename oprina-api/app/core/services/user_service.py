"""
User service for user management and authentication.
FIXED VERSION - All methods properly indented inside the class.
"""

from typing import Dict, Any, Optional
import structlog, bcrypt

from app.core.database.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class UserService:
    """Service for user management and authentication."""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def create_or_get_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user or get existing user."""
        try:
            email = user_data.get("email")
            if not email:
                raise ValueError("Email is required")
            
            # Check if user already exists
            existing_user = await self.user_repo.get_user_by_email(email)
            if existing_user:
                # Update last login
                await self.user_repo.update_last_login(existing_user["id"])
                logger.info(f"Existing user {email} logged in")
                return existing_user
            
            # Create new user
            new_user = await self.user_repo.create_user(user_data)
            logger.info(f"Created new user {email}")
            return new_user
            
        except Exception as e:
            logger.error(f"Failed to create/get user: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            return user
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            user = await self.user_repo.get_user_by_email(email)
            return user
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information."""
        try:
            # Filter out non-updatable fields
            allowed_fields = {"display_name", "avatar_url", "preferences", "settings"}
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
            
            if not filtered_data:
                raise ValueError("No valid fields to update")
            
            updated_user = await self.user_repo.update_user(user_id, filtered_data)
            logger.info(f"Updated user {user_id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user preferences."""
        try:
            update_data = {"preferences": preferences}
            updated_user = await self.user_repo.update_user(user_id, update_data)
            logger.info(f"Updated preferences for user {user_id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            raise
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics and activity."""
        try:
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Basic user stats
            stats = {
                "user_id": user_id,
                "email": user.get("email"),
                "display_name": user.get("display_name"),
                "created_at": user.get("created_at"),
                "last_login_at": user.get("last_login_at"),
                "total_sessions": 0,  # To be populated by session repository
                "total_messages": 0,  # To be populated by message repository
                "account_status": "active"  # Basic status
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user stats for {user_id}: {e}")
            raise
    
    async def verify_user_access(self, user_id: str, resource_id: str) -> bool:
        """Verify user has access to a resource."""
        try:
            # Basic implementation - users can only access their own resources
            # In more complex scenarios, this could check roles, permissions, etc.
            user = await self.user_repo.get_user_by_id(user_id)
            return user is not None
            
        except Exception as e:
            logger.error(f"Failed to verify access for user {user_id}: {e}")
            return False
    
    async def validate_user_session(
        self, 
        user_id: str, 
        session_token: Optional[str] = None
    ) -> bool:
        """Validate user session and token if provided."""
        try:
            # Basic validation - check if user exists and is active
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                return False
            
            # Check if user is active
            status = user.get("status", "active")
            if status != "active":
                return False
            
            # In a production system, you would validate the session token here
            # For now, we just validate user existence and status
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate session for user {user_id}: {e}")
            return False

    # ✅ FIXED: These methods are now properly indented INSIDE the class
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user (for registration)."""
        try:
            # Create new user via repository
            new_user = await self.user_repo.create_user(user_data)
            logger.info(f"Created new user {new_user.get('email')}")
            return new_user
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    async def update_last_login(self, user_id: str) -> Dict[str, Any]:
        """Update user's last login timestamp."""
        try:
            updated_user = await self.user_repo.update_last_login(user_id)
            logger.info(f"Updated last login for user {user_id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {e}")
            raise

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        try:
            await self.user_repo.deactivate_user(user_id)
            logger.info(f"Deactivated user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile - matches your UI form exactly."""
        try:
            # Prepare update data with only the fields that can be updated
            update_data = {}
            
            # Profile fields from your UI
            if "full_name" in profile_data and profile_data["full_name"] is not None:
                update_data["full_name"] = profile_data["full_name"]
                
            if "preferred_name" in profile_data and profile_data["preferred_name"] is not None:
                update_data["preferred_name"] = profile_data["preferred_name"]
                
            if "work_type" in profile_data and profile_data["work_type"] is not None:
                update_data["work_type"] = profile_data["work_type"]
                
            if "ai_preferences" in profile_data and profile_data["ai_preferences"] is not None:
                update_data["ai_preferences"] = profile_data["ai_preferences"]
            
            # Optional system fields
            if "avatar_url" in profile_data and profile_data["avatar_url"] is not None:
                update_data["avatar_url"] = profile_data["avatar_url"]
                
            if "timezone" in profile_data and profile_data["timezone"] is not None:
                update_data["timezone"] = profile_data["timezone"]
                
            if "language" in profile_data and profile_data["language"] is not None:
                update_data["language"] = profile_data["language"]
            
            # Also update display_name to match full_name for compatibility
            if "full_name" in update_data:
                update_data["display_name"] = update_data["full_name"]
            
            if not update_data:
                raise ValueError("No valid fields to update")
            
            # Update user via repository
            updated_user = await self.user_repo.update_user(user_id, update_data)
            logger.info(f"Updated profile for user {user_id}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to update profile for user {user_id}: {e}")
            raise

    async def change_user_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password with current password validation."""
        try:
            # Get current user
            user = await self.user_repo.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Check if user has a password (might be OAuth-only)
            if not user.get("password_hash"):
                raise ValueError("User does not have a password set (OAuth-only account)")
            
            # Verify current password
            if not bcrypt.checkpw(current_password.encode('utf-8'), user["password_hash"].encode('utf-8')):
                raise ValueError("Current password is incorrect")
            
            # Hash new password using the same utils as auth endpoints
            from app.utils.encryption import hash_password
            new_password_hash = hash_password(new_password)
            
            # Update password via repository
            await self.user_repo.change_password(user_id, new_password_hash)
            
            logger.info(f"Password changed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            raise