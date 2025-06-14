"""Avatar session management API endpoints."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
import structlog

from app.core.services.avatar_session_service import AvatarSessionService
from app.core.database.repositories.avatar_usage_repository import UsageRepository
from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.connection import get_db_connection
from app.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

# Internal API key for agent authentication
INTERNAL_API_KEY = "agent-internal-key-change-in-production"  # TODO: Move to env

class StartAvatarSessionRequest(BaseModel):
    vertex_session_id: str
    avatar_session_id: str  # HeyGen session ID
    avatar_name: str = "Ann_Therapist_public"

class EndAvatarSessionRequest(BaseModel):
    avatar_session_id: str
    words_spoken: int = 0
    error_message: Optional[str] = None

class SessionStatusRequest(BaseModel):
    avatar_session_id: str

class UserSessionsRequest(BaseModel):
    vertex_session_id: str

class AvatarSessionResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    usage_record_id: Optional[str] = None
    timeout_minutes: Optional[int] = None
    quota_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    switch_to_static: bool = False

class SessionStatusResponse(BaseModel):
    active: bool
    elapsed_seconds: Optional[int] = None
    remaining_seconds: Optional[int] = None
    remaining_minutes: Optional[float] = None
    timeout_approaching: bool = False
    user_id: Optional[str] = None
    avatar_name: Optional[str] = None
    error: Optional[str] = None

class EndSessionResponse(BaseModel):
    success: bool
    session_ended: bool = False
    duration_seconds: int = 0
    estimated_cost: float = 0.0
    forced_timeout: bool = False
    switch_to_static: bool = False
    error: Optional[str] = None
    message: Optional[str] = None

def verify_internal_api_key(x_api_key: str = Header(...)):
    """Verify internal API key for agent authentication."""
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

async def get_avatar_session_service(db = Depends(get_db_connection)) -> AvatarSessionService:
    """Get avatar session service with dependencies."""
    usage_repo = UsageRepository(db)
    return AvatarSessionService(usage_repo)

async def get_user_id_from_vertex_session(vertex_session_id: str, db) -> str:
    """Get user ID from Vertex AI session ID."""
    session_repo = SessionRepository(db)
    session_data = await session_repo.get_session_by_vertex_id(vertex_session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_data["user_id"]

@router.post("/sessions/start", response_model=AvatarSessionResponse)
async def start_avatar_session(
    request: StartAvatarSessionRequest,
    _: bool = Depends(verify_internal_api_key),
    avatar_service: AvatarSessionService = Depends(get_avatar_session_service),
    db = Depends(get_db_connection)
) -> AvatarSessionResponse:
    """Start a new avatar streaming session with quota checking."""
    try:
        # Get user ID from vertex session
        user_id = await get_user_id_from_vertex_session(request.vertex_session_id, db)
        
        # Start avatar session with monitoring
        result = await avatar_service.start_avatar_session(
            user_id=user_id,
            session_id=request.vertex_session_id,
            avatar_session_id=request.avatar_session_id,
            avatar_name=request.avatar_name
        )
        
        return AvatarSessionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start avatar session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions/end", response_model=EndSessionResponse)
async def end_avatar_session(
    request: EndAvatarSessionRequest,
    _: bool = Depends(verify_internal_api_key),
    avatar_service: AvatarSessionService = Depends(get_avatar_session_service)
) -> EndSessionResponse:
    """End an avatar streaming session and update usage records."""
    try:
        result = await avatar_service.end_avatar_session(
            avatar_session_id=request.avatar_session_id,
            words_spoken=request.words_spoken,
            error_message=request.error_message
        )
        
        return EndSessionResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to end avatar session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions/status", response_model=SessionStatusResponse)
async def get_session_status(
    request: SessionStatusRequest,
    _: bool = Depends(verify_internal_api_key),
    avatar_service: AvatarSessionService = Depends(get_avatar_session_service)
) -> SessionStatusResponse:
    """Get current status of an avatar session including remaining time."""
    try:
        result = await avatar_service.get_session_status(request.avatar_session_id)
        return SessionStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions/user", response_model=Dict[str, Any])
async def get_user_active_sessions(
    request: UserSessionsRequest,
    _: bool = Depends(verify_internal_api_key),
    avatar_service: AvatarSessionService = Depends(get_avatar_session_service),
    db = Depends(get_db_connection)
) -> Dict[str, Any]:
    """Get all active avatar sessions for a user."""
    try:
        # Get user ID from vertex session
        user_id = await get_user_id_from_vertex_session(request.vertex_session_id, db)
        
        sessions = await avatar_service.get_user_active_sessions(user_id)
        
        return {
            "user_id": user_id,
            "active_sessions": sessions,
            "session_count": len(sessions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/quota/check")
async def check_quota_status(
    request: UserSessionsRequest,
    _: bool = Depends(verify_internal_api_key),
    db = Depends(get_db_connection)
) -> Dict[str, Any]:
    """Check user's avatar streaming quota status."""
    try:
        # Get user ID from vertex session
        user_id = await get_user_id_from_vertex_session(request.vertex_session_id, db)
        
        usage_repo = UsageRepository(db)
        quota_check = await usage_repo.check_quota_limits(user_id)
        
        return {
            "user_id": user_id,
            **quota_check
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check quota status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions/cleanup")
async def cleanup_inactive_sessions(
    _: bool = Depends(verify_internal_api_key),
    avatar_service: AvatarSessionService = Depends(get_avatar_session_service)
) -> Dict[str, Any]:
    """Clean up inactive or orphaned avatar sessions."""
    try:
        await avatar_service.cleanup_inactive_sessions()
        return {"status": "cleanup_completed"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """Health check for avatar API."""
    return {"status": "healthy", "service": "avatar-api"} 