"""Avatar session management with real-time quota monitoring."""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass

from app.core.database.repositories.avatar_usage_repository import UsageRepository
from app.models.database.avatar_usage import AvatarUsageRecord
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ActiveSession:
    """Active avatar session tracking."""
    session_id: str
    user_id: str
    avatar_session_id: str
    avatar_name: str
    started_at: datetime
    usage_record_id: str
    monitor_task: Optional[asyncio.Task] = None
    is_active: bool = True


class AvatarSessionService:
    """Service for managing avatar sessions with real-time quota enforcement."""
    
    def __init__(self, usage_repository: UsageRepository):
        self.usage_repo = usage_repository
        self.active_sessions: Dict[str, ActiveSession] = {}
        self.session_timeout_minutes = 20  # HeyGen streaming limit
        
    async def start_avatar_session(
        self, 
        user_id: str, 
        session_id: str, 
        avatar_session_id: str,
        avatar_name: str = "Ann_Therapist_public"
    ) -> Dict[str, Any]:
        """Start a new avatar session with quota checking and monitoring."""
        try:
            # Check quota limits before starting
            quota_check = await self.usage_repo.check_quota_limits(user_id)
            
            if not quota_check["can_create_session"]:
                logger.warning(f"User {user_id} has exhausted their 20-minute quota")
                return {
                    "success": False,
                    "error": "quota_exhausted",
                    "message": "20-minute avatar streaming quota exhausted",
                    "quota_info": quota_check["limits"],
                    "switch_to_static": True
                }
            
            # Create usage record
            usage_record = AvatarUsageRecord(
                user_id=user_id,
                session_id=session_id,
                avatar_session_id=avatar_session_id,
                avatar_name=avatar_name,
                session_started_at=datetime.utcnow(),
                status="active"
            )
            
            created_record = await self.usage_repo.create_usage_record(usage_record)
            
            # Create active session tracking
            active_session = ActiveSession(
                session_id=session_id,
                user_id=user_id,
                avatar_session_id=avatar_session_id,
                avatar_name=avatar_name,
                started_at=datetime.utcnow(),
                usage_record_id=created_record.id
            )
            
            # Start monitoring task
            active_session.monitor_task = asyncio.create_task(
                self._monitor_session(active_session)
            )
            
            self.active_sessions[avatar_session_id] = active_session
            
            logger.info(f"Started avatar session {avatar_session_id} for user {user_id}")
            
            return {
                "success": True,
                "session_id": avatar_session_id,
                "usage_record_id": created_record.id,
                "quota_info": quota_check["limits"],
                "timeout_minutes": self.session_timeout_minutes
            }
            
        except Exception as e:
            logger.error(f"Error starting avatar session: {str(e)}")
            return {
                "success": False,
                "error": "session_start_failed",
                "message": str(e)
            }
    
    async def _monitor_session(self, session: ActiveSession):
        """Monitor session and enforce 20-minute timeout."""
        try:
            # Wait for timeout period
            await asyncio.sleep(self.session_timeout_minutes * 60)  # Convert to seconds
            
            if session.is_active:
                logger.warning(f"Session {session.avatar_session_id} reached 20-minute limit")
                
                # Force end the session
                await self.end_avatar_session(
                    session.avatar_session_id,
                    force_timeout=True,
                    timeout_reason="20_minute_limit_reached"
                )
                
        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for session {session.avatar_session_id}")
        except Exception as e:
            logger.error(f"Error monitoring session {session.avatar_session_id}: {str(e)}")
    
    async def end_avatar_session(
        self, 
        avatar_session_id: str, 
        words_spoken: int = 0,
        error_message: Optional[str] = None,
        force_timeout: bool = False,
        timeout_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """End an avatar session and update usage records."""
        try:
            # Get active session
            active_session = self.active_sessions.get(avatar_session_id)
            if not active_session:
                logger.warning(f"No active session found for {avatar_session_id}")
                return {"success": False, "error": "session_not_found"}
            
            # Cancel monitoring task
            if active_session.monitor_task and not active_session.monitor_task.done():
                active_session.monitor_task.cancel()
            
            # Mark session as inactive
            active_session.is_active = False
            
            # Calculate final error message
            final_error = error_message
            if force_timeout and timeout_reason:
                final_error = f"Session timeout: {timeout_reason}"
            
            # End session in database
            updated_record = await self.usage_repo.end_session(
                avatar_session_id=avatar_session_id,
                words_spoken=words_spoken,
                error_message=final_error
            )
            
            if updated_record:
                # Update user quota (20-minute total limit)
                await self.usage_repo.update_quota_usage(
                    user_id=active_session.user_id,
                    duration_seconds=updated_record.duration_seconds
                )
                
                logger.info(f"Ended avatar session {avatar_session_id} - Duration: {duration_minutes:.1f} minutes")
            
            # Remove from active sessions
            del self.active_sessions[avatar_session_id]
            
            return {
                "success": True,
                "session_ended": True,
                "duration_seconds": updated_record.duration_seconds if updated_record else 0,
                "estimated_cost": updated_record.estimated_cost if updated_record else 0.0,
                "forced_timeout": force_timeout,
                "switch_to_static": force_timeout  # Signal frontend to switch
            }
            
        except Exception as e:
            logger.error(f"Error ending avatar session {avatar_session_id}: {str(e)}")
            return {
                "success": False,
                "error": "session_end_failed",
                "message": str(e)
            }
    
    async def get_session_status(self, avatar_session_id: str) -> Dict[str, Any]:
        """Get current session status and remaining time."""
        active_session = self.active_sessions.get(avatar_session_id)
        if not active_session:
            return {"active": False, "error": "session_not_found"}
        
        elapsed_seconds = (datetime.utcnow() - active_session.started_at).total_seconds()
        remaining_seconds = max(0, (self.session_timeout_minutes * 60) - elapsed_seconds)
        
        return {
            "active": active_session.is_active,
            "elapsed_seconds": int(elapsed_seconds),
            "remaining_seconds": int(remaining_seconds),
            "remaining_minutes": round(remaining_seconds / 60.0, 1),
            "timeout_approaching": remaining_seconds < 300,  # 5 minutes warning
            "user_id": active_session.user_id,
            "avatar_name": active_session.avatar_name
        }
    
    async def get_user_active_sessions(self, user_id: str) -> list:
        """Get all active sessions for a user."""
        user_sessions = []
        for session in self.active_sessions.values():
            if session.user_id == user_id and session.is_active:
                status = await self.get_session_status(session.avatar_session_id)
                user_sessions.append({
                    "avatar_session_id": session.avatar_session_id,
                    "session_id": session.session_id,
                    "avatar_name": session.avatar_name,
                    "started_at": session.started_at.isoformat(),
                    **status
                })
        return user_sessions
    
    async def cleanup_inactive_sessions(self):
        """Clean up any inactive or orphaned sessions."""
        inactive_sessions = []
        for session_id, session in self.active_sessions.items():
            if not session.is_active or (
                datetime.utcnow() - session.started_at
            ).total_seconds() > (self.session_timeout_minutes * 60 + 300):  # 5 min grace period
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            logger.info(f"Cleaning up inactive session: {session_id}")
            await self.end_avatar_session(session_id, force_timeout=True, timeout_reason="cleanup") 