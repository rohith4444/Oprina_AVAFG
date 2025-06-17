"""
Avatar endpoints for Oprina API.
Simple REST endpoints for avatar session management and quota tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.api.dependencies import get_current_user, get_avatar_service
from app.core.services.avatar_service import AvatarService
from app.api.models.requests.avatar import (
    StartSessionRequest, 
    EndSessionRequest, 
    SessionStatusRequest
)
from app.api.models.responses.avatar import (
    QuotaStatusResponse,
    SessionResponse,
    SessionStatusResponse,
    UserSessionsResponse,
    AvatarErrorResponse
)
from app.utils.errors import ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# =============================================================================
# QUOTA MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/quota", response_model=QuotaStatusResponse)
async def get_quota_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service)
):
    """
    Get user's current avatar quota status.
    
    Returns remaining time, usage percentage, and whether user can create new sessions.
    Essential for frontend to check before creating HeyGen sessions.
    """
    try:
        user_id = current_user["id"]
        quota_status = await avatar_service.get_user_quota_status(user_id)
        
        return QuotaStatusResponse(
            can_create_session=quota_status["can_create_session"],
            total_seconds_used=quota_status["total_seconds_used"],
            remaining_seconds=quota_status["remaining_seconds"],
            quota_exhausted=quota_status["quota_exhausted"],
            quota_percentage=quota_status["quota_percentage"]
        )
        
    except Exception as e:
        logger.error(f"Error getting quota status for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quota status"
        )


@router.post("/check-quota")
async def check_quota(
    current_user: Dict[str, Any] = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service)
):
    """
    Check if user can create a new avatar session.
    
    Simple endpoint that returns true/false with quota info.
    Frontend calls this before attempting to create HeyGen session.
    """
    try:
        user_id = current_user["id"]
        quota_check = await avatar_service.can_user_create_session(user_id)
        
        if not quota_check["can_create"]:
            return AvatarErrorResponse(
                success=False,
                error_code="QUOTA_EXHAUSTED",
                error_message="20-minute avatar streaming quota has been exhausted",
                quota_status=QuotaStatusResponse(**quota_check["quota_status"])
            )
        
        return {
            "success": True,
            "can_create_session": True,
            "quota_status": quota_check["quota_status"],
            "message": "Session creation allowed"
        }
        
    except Exception as e:
        logger.error(f"Error checking quota for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check quota"
        )


# =============================================================================
# SESSION MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/sessions/start", response_model=SessionResponse)
async def start_avatar_session(
    request: StartSessionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service)
):
    """
    Start tracking a HeyGen avatar session.
    
    Call this AFTER successfully creating a HeyGen session in frontend.
    This starts the quota tracking and session monitoring.
    """
    try:
        user_id = current_user["id"]
        
        result = await avatar_service.start_session(
            user_id=user_id,
            heygen_session_id=request.heygen_session_id,
            avatar_name=request.avatar_name
        )
        
        if not result["success"]:
            # Return appropriate error response
            error_code = result.get("error_code", "SESSION_START_FAILED")
            
            if error_code == "QUOTA_EXHAUSTED":
                return AvatarErrorResponse(
                    success=False,
                    error_code=error_code,
                    error_message=result["message"],
                    quota_status=QuotaStatusResponse(**result["quota_status"])
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return SessionResponse(
            success=True,
            session_id=result["session_id"],
            heygen_session_id=result["heygen_session_id"],
            status=result["status"],
            quota_info=QuotaStatusResponse(**result["quota_status"]),
            message=result["message"]
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error starting session for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start avatar session"
        )


@router.post("/sessions/end", response_model=SessionResponse)
async def end_avatar_session(
    request: EndSessionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service)
):
    """
    End a HeyGen avatar session and update quota.
    
    Call this when:
    - User manually stops the session
    - Session times out (20 minutes)
    - Error occurs in HeyGen session
    - Browser is closed/refreshed
    """
    try:
        result = await avatar_service.end_session(
            heygen_session_id=request.heygen_session_id,
            error_message=request.error_message
        )
        
        if not result["success"]:
            error_code = result.get("error_code", "SESSION_END_FAILED")
            
            if error_code == "SESSION_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["message"]
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return SessionResponse(
            success=True,
            session_id=result["session_id"],
            heygen_session_id=result["heygen_session_id"],
            status=result["status"],
            duration_seconds=result["duration_seconds"],
            quota_info=QuotaStatusResponse(**result["quota_status"]),
            message=result["message"]
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end avatar session"
        )


# =============================================================================
# SESSION STATUS & MONITORING ENDPOINTS
# =============================================================================

@router.post("/sessions/status", response_model=SessionStatusResponse)
async def get_session_status(
    request: SessionStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service)
):
    """
    Get current status of an avatar session.
    
    Returns session info, duration, remaining time, and whether timeout is approaching.
    Frontend can poll this endpoint to show real-time session info.
    """
    try:
        status_info = await avatar_service.get_session_status(request.heygen_session_id)
        
        return SessionStatusResponse(
            exists=status_info["exists"],
            active=status_info["active"],
            heygen_session_id=status_info["heygen_session_id"],
            status=status_info["status"],
            started_at=status_info.get("started_at"),
            duration_seconds=status_info.get("duration_seconds"),
            remaining_seconds=status_info.get("remaining_seconds"),
            avatar_name=status_info.get("avatar_name")
        )
        
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session status"
        )


@router.get("/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    active_only: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service)
):
    """
    Get all sessions for the current user.
    
    Parameters:
    - active_only: If True, only return currently active sessions
    
    Returns session history, quota status, and statistics.
    """
    try:
        user_id = current_user["id"]
        
        sessions_info = await avatar_service.get_user_sessions(
            user_id=user_id,
            include_inactive=not active_only
        )
        
        # Convert sessions to response format
        session_responses = []
        for session in sessions_info["sessions"]:
            session_responses.append(SessionStatusResponse(
                exists=session["exists"],
                active=session["active"],
                heygen_session_id=session["heygen_session_id"],
                status=session["status"],
                started_at=session.get("started_at"),
                duration_seconds=session.get("duration_seconds"),
                remaining_seconds=session.get("remaining_seconds"),
                avatar_name=session.get("avatar_name")
            ))
        
        return UserSessionsResponse(
            total_sessions=sessions_info["total_sessions"],
            active_sessions=sessions_info["active_sessions"],
            sessions=session_responses,
            quota_status=QuotaStatusResponse(**sessions_info["quota_status"])
        )
        
    except Exception as e:
        logger.error(f"Error getting user sessions for {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user sessions"
        )


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.post("/admin/cleanup")
async def cleanup_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user),
    avatar_service: AvatarService = Depends(get_avatar_service)
):
    """
    Clean up orphaned or stuck sessions.
    
    Administrative endpoint to clean up sessions that may be stuck
    due to browser crashes, network issues, etc.
    """
    try:
        # Simple check - in a real app you might want admin role checking here
        logger.info(f"Session cleanup requested by user {current_user['id']}")
        
        result = await avatar_service.cleanup_orphaned_sessions()
        
        return {
            "success": True,
            "sessions_cleaned": result["sessions_cleaned"],
            "message": result["message"]
        }
        
    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup sessions"
        )


@router.get("/health")
async def avatar_health_check():
    """Health check for avatar service."""
    return {
        "status": "healthy",
        "service": "avatar-api",
        "features": [
            "quota_tracking",
            "session_management", 
            "20_minute_limit_enforcement"
        ]
    }