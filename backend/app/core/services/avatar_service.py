"""
Avatar service for business logic operations.
Handles avatar quota management and session lifecycle.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from app.core.database.repositories.avatar_repository import AvatarRepository
from app.utils.logging import get_logger
from app.utils.errors import ValidationError

logger = get_logger(__name__)


class AvatarService:
    """Service for avatar session management and quota enforcement."""
    
    def __init__(self, avatar_repository: AvatarRepository):
        self.avatar_repo = avatar_repository
        self.max_quota_seconds = 900  # 15 minutes
    
    # =============================================================================
    # QUOTA MANAGEMENT
    # =============================================================================
    
    async def can_user_create_session(self, user_id: str) -> Dict[str, Any]:
        """Check if user can create a new avatar session."""
        try:
            logger.debug(f"Checking quota for user {user_id}")
            
            quota_status = await self.avatar_repo.check_quota_limits(user_id)
            
            return {
                "can_create": quota_status["can_create_session"],
                "quota_status": quota_status,
                "reason": "quota_exhausted" if quota_status["quota_exhausted"] else "quota_available"
            }
            
        except Exception as e:
            logger.error(f"Error checking user quota for {user_id}: {str(e)}")
            raise
    
    async def get_user_quota_status(self, user_id: str) -> Dict[str, Any]:
        """Get detailed quota status for a user."""
        try:
            quota_status = await self.avatar_repo.check_quota_limits(user_id)
            
            # Add additional calculated fields
            minutes_used = quota_status["total_seconds_used"] / 60.0
            minutes_remaining = quota_status["remaining_seconds"] / 60.0
            
            return {
                **quota_status,
                "minutes_used": round(minutes_used, 2),
                "minutes_remaining": round(minutes_remaining, 2),
                "max_quota_minutes": 15,
                "max_quota_seconds": self.max_quota_seconds
            }
            
        except Exception as e:
            logger.error(f"Error getting quota status for user {user_id}: {str(e)}")
            raise
    
    # =============================================================================
    # SESSION LIFECYCLE
    # =============================================================================
    
    async def start_session(
        self, 
        user_id: str, 
        heygen_session_id: str, 
        avatar_name: str = "Ann_Therapist_public"
    ) -> Dict[str, Any]:
        """Start tracking a new avatar session."""
        try:
            # Validate inputs
            if not heygen_session_id or not heygen_session_id.strip():
                raise ValidationError("HeyGen session ID is required")
            
            if not avatar_name or not avatar_name.strip():
                avatar_name = "Ann_Therapist_public"
            
            # Check if user can create session
            quota_check = await self.can_user_create_session(user_id)
            
            if not quota_check["can_create"]:
                logger.warning(f"User {user_id} cannot create session - quota exhausted")
                return {
                    "success": False,
                    "error_code": "QUOTA_EXHAUSTED",
                    "message": "20-minute avatar streaming quota has been exhausted",
                    "quota_status": quota_check["quota_status"]
                }
            
            # Check if session already exists
            existing_session = await self.avatar_repo.get_session_by_heygen_id(heygen_session_id)
            if existing_session:
                logger.warning(f"Session {heygen_session_id} already exists")
                return {
                    "success": False,
                    "error_code": "SESSION_EXISTS",
                    "message": f"Session {heygen_session_id} already exists",
                    "existing_session": existing_session
                }
            
            # Create the session
            session = await self.avatar_repo.create_session(user_id, heygen_session_id, avatar_name)
            
            if not session:
                logger.error(f"Failed to create session {heygen_session_id}")
                return {
                    "success": False,
                    "error_code": "SESSION_CREATION_FAILED",
                    "message": "Failed to create avatar session"
                }
            
            # Get updated quota status
            updated_quota = await self.get_user_quota_status(user_id)
            
            logger.info(f"Started avatar session {heygen_session_id} for user {user_id}")
            
            return {
                "success": True,
                "session_id": session["id"],
                "heygen_session_id": heygen_session_id,
                "status": session["status"],
                "avatar_name": avatar_name,
                "started_at": session["started_at"],
                "quota_status": updated_quota,
                "message": "Session started successfully"
            }
            
        except ValidationError as e:
            logger.warning(f"Validation error starting session: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error starting session {heygen_session_id}: {str(e)}")
            raise
    
    async def end_session(
        self, 
        heygen_session_id: str, 
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """End an avatar session and update quota."""
        try:
            # Validate input
            if not heygen_session_id or not heygen_session_id.strip():
                raise ValidationError("HeyGen session ID is required")
            
            # Check if session exists and is active
            existing_session = await self.avatar_repo.get_session_by_heygen_id(heygen_session_id)
            if not existing_session:
                logger.warning(f"Session {heygen_session_id} not found")
                return {
                    "success": False,
                    "error_code": "SESSION_NOT_FOUND",
                    "message": f"Session {heygen_session_id} not found"
                }
            
            if existing_session["status"] != "active":
                logger.warning(f"Session {heygen_session_id} is not active (status: {existing_session['status']})")
                return {
                    "success": False,
                    "error_code": "SESSION_NOT_ACTIVE",
                    "message": f"Session is not active (current status: {existing_session['status']})",
                    "current_session": existing_session
                }
            
            # End the session (this also updates quota via database function)
            ended_session = await self.avatar_repo.end_session(heygen_session_id, error_message)
            
            if not ended_session:
                logger.error(f"Failed to end session {heygen_session_id}")
                return {
                    "success": False,
                    "error_code": "SESSION_END_FAILED",
                    "message": "Failed to end avatar session"
                }
            
            # Get updated quota status
            user_id = existing_session["user_id"]
            updated_quota = await self.get_user_quota_status(user_id)
            
            # Check if quota is now exhausted
            quota_exhausted = updated_quota["quota_exhausted"]
            
            logger.info(f"Ended avatar session {heygen_session_id} - Duration: {ended_session['duration_seconds']}s")
            
            return {
                "success": True,
                "session_id": ended_session["id"],
                "heygen_session_id": heygen_session_id,
                "status": ended_session["status"],
                "duration_seconds": ended_session["duration_seconds"],
                "quota_status": updated_quota,
                "quota_exhausted": quota_exhausted,
                "switch_to_static": quota_exhausted,  # Signal frontend to switch
                "message": f"Session ended successfully ({ended_session['duration_seconds']}s duration)"
            }
            
        except ValidationError as e:
            logger.warning(f"Validation error ending session: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error ending session {heygen_session_id}: {str(e)}")
            raise
    
    # =============================================================================
    # SESSION STATUS & MONITORING
    # =============================================================================
    
    async def get_session_status(self, heygen_session_id: str) -> Dict[str, Any]:
        """Get current status of an avatar session."""
        try:
            session = await self.avatar_repo.get_session_by_heygen_id(heygen_session_id)
            
            if not session:
                return {
                    "exists": False,
                    "active": False,
                    "heygen_session_id": heygen_session_id,
                    "status": "not_found",
                    "message": "Session not found"
                }
            
            # Calculate current duration
            current_duration = await self.avatar_repo.get_session_duration(heygen_session_id)
            
            # Calculate remaining time for active sessions
            remaining_seconds = None
            if session["status"] == "active" and current_duration is not None:
                remaining_seconds = max(0, self.max_quota_seconds - current_duration)
            
            return {
                "exists": True,
                "active": session["status"] == "active",
                "heygen_session_id": heygen_session_id,
                "status": session["status"],
                "started_at": session["started_at"],
                "ended_at": session.get("ended_at"),
                "duration_seconds": current_duration,
                "remaining_seconds": remaining_seconds,
                "avatar_name": session.get("avatar_name"),
                "timeout_approaching": (
                    remaining_seconds is not None and remaining_seconds <= 300  # 5 minutes warning
                ) if session["status"] == "active" else False
            }
            
        except Exception as e:
            logger.error(f"Error getting session status {heygen_session_id}: {str(e)}")
            raise
    
    async def get_user_sessions(self, user_id: str, include_inactive: bool = True) -> Dict[str, Any]:
        """Get all sessions for a user with quota information."""
        try:
            # Get sessions
            if include_inactive:
                sessions = await self.avatar_repo.get_user_all_sessions(user_id, limit=50)
            else:
                sessions = await self.avatar_repo.get_user_active_sessions(user_id)
            
            # Get session details
            session_details = []
            for session in sessions:
                session_status = await self.get_session_status(session["heygen_session_id"])
                session_details.append(session_status)
            
            # Get quota status
            quota_status = await self.get_user_quota_status(user_id)
            
            # Get session stats
            stats = await self.avatar_repo.get_session_stats(user_id)
            
            return {
                "total_sessions": stats["total_sessions"],
                "active_sessions": stats["active_sessions"],
                "completed_sessions": stats["completed_sessions"],
                "error_sessions": stats["error_sessions"],
                "sessions": session_details,
                "quota_status": quota_status
            }
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {str(e)}")
            raise
    
    # =============================================================================
    # MAINTENANCE & UTILITIES
    # =============================================================================
    
    async def cleanup_orphaned_sessions(self) -> Dict[str, Any]:
        """Clean up orphaned or stuck sessions."""
        try:
            cleanup_count = await self.avatar_repo.cleanup_orphaned_sessions()
            
            logger.info(f"Avatar cleanup completed: {cleanup_count} sessions cleaned")
            
            return {
                "success": True,
                "sessions_cleaned": cleanup_count,
                "message": f"Cleaned up {cleanup_count} orphaned sessions"
            }
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
            raise
    
    async def force_end_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """Force end all active sessions for a user (admin function)."""
        try:
            active_sessions = await self.avatar_repo.get_user_active_sessions(user_id)
            
            ended_count = 0
            for session in active_sessions:
                try:
                    await self.end_session(
                        session["heygen_session_id"], 
                        "Force ended by system"
                    )
                    ended_count += 1
                except Exception as e:
                    logger.warning(f"Failed to force end session {session['heygen_session_id']}: {str(e)}")
            
            logger.info(f"Force ended {ended_count} sessions for user {user_id}")
            
            return {
                "success": True,
                "sessions_ended": ended_count,
                "message": f"Force ended {ended_count} active sessions"
            }
            
        except Exception as e:
            logger.error(f"Error force ending sessions for user {user_id}: {str(e)}")
            raise