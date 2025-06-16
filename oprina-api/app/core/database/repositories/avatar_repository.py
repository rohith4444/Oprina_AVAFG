"""
Avatar repository for database operations.
Handles avatar quotas and session tracking in Supabase.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from supabase import Client

from app.utils.logging import get_logger

logger = get_logger(__name__)


class AvatarRepository:
    """Repository for avatar quota and session operations."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    # =============================================================================
    # QUOTA OPERATIONS
    # =============================================================================
    
    async def get_user_quota(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's avatar quota, creating if doesn't exist."""
        try:
            # Use the database function to get or create
            response = self.client.rpc(
                "get_or_create_user_quota", 
                {"p_user_id": user_id}
            ).execute()
            
            if response.data:
                logger.debug(f"Retrieved quota for user {user_id}")
                return response.data
            else:
                logger.warning(f"Failed to get/create quota for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user quota for {user_id}: {str(e)}")
            raise
    
    async def update_quota_usage(self, user_id: str, session_duration: int) -> Optional[Dict[str, Any]]:
        """Update user's quota usage after a session."""
        try:
            # Use the database function to update quota
            response = self.client.rpc(
                "update_quota_usage",
                {
                    "p_user_id": user_id,
                    "p_session_duration": session_duration
                }
            ).execute()
            
            if response.data:
                logger.info(f"Updated quota for user {user_id}: +{session_duration}s")
                return response.data
            else:
                logger.warning(f"Failed to update quota for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating quota for user {user_id}: {str(e)}")
            raise
    
    async def check_quota_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if user can create a new session based on quota."""
        try:
            quota = await self.get_user_quota(user_id)
            
            if not quota:
                # Create default quota if none exists
                return {
                    "can_create_session": True,
                    "total_seconds_used": 0,
                    "remaining_seconds": 1200,
                    "quota_exhausted": False,
                    "quota_percentage": 0.0
                }
            
            total_used = quota.get("total_seconds_used", 0)
            quota_exhausted = quota.get("quota_exhausted", False)
            
            remaining_seconds = max(0, 1200 - total_used)
            quota_percentage = (total_used / 1200.0) * 100.0
            
            return {
                "can_create_session": not quota_exhausted and remaining_seconds > 0,
                "total_seconds_used": total_used,
                "remaining_seconds": remaining_seconds,
                "quota_exhausted": quota_exhausted,
                "quota_percentage": round(quota_percentage, 2)
            }
            
        except Exception as e:
            logger.error(f"Error checking quota limits for user {user_id}: {str(e)}")
            raise
    
    # =============================================================================
    # SESSION OPERATIONS
    # =============================================================================
    
    async def create_session(
        self, 
        user_id: str, 
        heygen_session_id: str, 
        avatar_name: str = "Ann_Therapist_public"
    ) -> Optional[Dict[str, Any]]:
        """Create a new avatar session record."""
        try:
            session_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "heygen_session_id": heygen_session_id,
                "avatar_name": avatar_name,
                "status": "active",
                "started_at": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("avatar_sessions").insert(session_data).execute()
            
            if response.data:
                logger.info(f"Created avatar session {heygen_session_id} for user {user_id}")
                return response.data[0]
            else:
                logger.error(f"Failed to create session {heygen_session_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating session {heygen_session_id}: {str(e)}")
            raise
    
    async def end_session(
        self, 
        heygen_session_id: str, 
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """End an avatar session and calculate duration."""
        try:
            # Use the database function to end session
            response = self.client.rpc(
                "end_avatar_session",
                {
                    "p_heygen_session_id": heygen_session_id,
                    "p_error_message": error_message
                }
            ).execute()
            
            if response.data:
                logger.info(f"Ended avatar session {heygen_session_id}")
                return response.data
            else:
                logger.warning(f"Session {heygen_session_id} not found or already ended")
                return None
                
        except Exception as e:
            logger.error(f"Error ending session {heygen_session_id}: {str(e)}")
            raise
    
    async def get_session_by_heygen_id(self, heygen_session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by HeyGen session ID."""
        try:
            response = self.client.table("avatar_sessions").select("*").eq(
                "heygen_session_id", heygen_session_id
            ).execute()
            
            if response.data:
                return response.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting session {heygen_session_id}: {str(e)}")
            raise
    
    async def get_user_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        try:
            # Use the database function
            response = self.client.rpc(
                "get_user_active_sessions",
                {"p_user_id": user_id}
            ).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting active sessions for user {user_id}: {str(e)}")
            raise
    
    async def get_user_all_sessions(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all sessions for a user (recent first)."""
        try:
            response = self.client.table("avatar_sessions").select("*").eq(
                "user_id", user_id
            ).order("started_at", desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting all sessions for user {user_id}: {str(e)}")
            raise
    
    # =============================================================================
    # MAINTENANCE OPERATIONS
    # =============================================================================
    
    async def cleanup_orphaned_sessions(self) -> int:
        """Clean up sessions that have been active too long."""
        try:
            response = self.client.rpc("cleanup_orphaned_sessions").execute()
            
            cleanup_count = response.data if response.data else 0
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} orphaned sessions")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned sessions: {str(e)}")
            raise
    
    async def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """Get session statistics for a user."""
        try:
            # Get session counts by status
            response = self.client.table("avatar_sessions").select(
                "status", count="exact"
            ).eq("user_id", user_id).execute()
            
            # Get quota info
            quota_info = await self.check_quota_limits(user_id)
            
            # Count sessions by status
            total_sessions = 0
            active_sessions = 0
            completed_sessions = 0
            error_sessions = 0
            
            if response.data:
                # Get actual counts from database
                total_response = self.client.table("avatar_sessions").select(
                    "*", count="exact"
                ).eq("user_id", user_id).execute()
                total_sessions = len(total_response.data) if total_response.data else 0
                
                active_response = self.client.table("avatar_sessions").select(
                    "*", count="exact"
                ).eq("user_id", user_id).eq("status", "active").execute()
                active_sessions = len(active_response.data) if active_response.data else 0
                
                completed_response = self.client.table("avatar_sessions").select(
                    "*", count="exact"
                ).eq("user_id", user_id).eq("status", "completed").execute()
                completed_sessions = len(completed_response.data) if completed_response.data else 0
                
                error_response = self.client.table("avatar_sessions").select(
                    "*", count="exact"
                ).eq("user_id", user_id).in_("status", ["error", "timeout"]).execute()
                error_sessions = len(error_response.data) if error_response.data else 0
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "completed_sessions": completed_sessions,
                "error_sessions": error_sessions,
                "quota_info": quota_info
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats for user {user_id}: {str(e)}")
            raise
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    async def session_exists(self, heygen_session_id: str) -> bool:
        """Check if a session exists by HeyGen session ID."""
        try:
            session = await self.get_session_by_heygen_id(heygen_session_id)
            return session is not None
            
        except Exception as e:
            logger.error(f"Error checking if session exists {heygen_session_id}: {str(e)}")
            return False
    
    async def is_session_active(self, heygen_session_id: str) -> bool:
        """Check if a session is currently active."""
        try:
            session = await self.get_session_by_heygen_id(heygen_session_id)
            return session is not None and session.get("status") == "active"
            
        except Exception as e:
            logger.error(f"Error checking if session is active {heygen_session_id}: {str(e)}")
            return False
    
    async def get_session_duration(self, heygen_session_id: str) -> Optional[int]:
        """Get current duration of a session in seconds."""
        try:
            session = await self.get_session_by_heygen_id(heygen_session_id)
            
            if not session:
                return None
            
            # If session is ended, return stored duration
            if session.get("duration_seconds") is not None:
                return session["duration_seconds"]
            
            # If session is active, calculate current duration
            if session.get("status") == "active" and session.get("started_at"):
                started_at = datetime.fromisoformat(session["started_at"].replace("Z", "+00:00"))
                current_duration = int((datetime.utcnow() - started_at.replace(tzinfo=None)).total_seconds())
                return current_duration
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session duration {heygen_session_id}: {str(e)}")
            return None