"""
Internal API endpoints for agent-to-backend communication.
These endpoints are used by the deployed Vertex AI agent to access user data.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
import structlog

from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.repositories.token_repository import TokenRepository
from app.core.database.connection import get_db_connection
from app.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

# Internal API key for agent authentication
INTERNAL_API_KEY = "agent-internal-key-change-in-production"  # TODO: Move to env

class TokenRequest(BaseModel):
    vertex_session_id: str

class TokenResponse(BaseModel):
    access_token: str
    expires_at: str
    service: str
    user_id: str

class ConnectionStatusResponse(BaseModel):
    gmail: bool
    calendar: bool
    user_id: str

def verify_internal_api_key(x_api_key: str = Header(...)):
    """Verify internal API key for agent authentication."""
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@router.post("/tokens/gmail", response_model=TokenResponse)
async def get_gmail_token(
    request: TokenRequest,
    _: bool = Depends(verify_internal_api_key),
    db = Depends(get_db_connection)
) -> TokenResponse:
    """Get Gmail token for user by Vertex AI session ID."""
    try:
        session_repo = SessionRepository(db)
        token_repo = TokenRepository(db)
        
        # 1. Look up vertex_session_id → user_session_id → user_id
        session_data = await session_repo.get_session_by_vertex_id(request.vertex_session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        user_id = session_data["user_id"]
        
        # 2. Get Gmail token for user
        token_data = await token_repo.get_active_token_data(user_id, "gmail")
        
        if not token_data:
            raise HTTPException(status_code=404, detail="Gmail not connected")
        
        # 3. Return decrypted token
        return TokenResponse(
            access_token=token_data["access_token"],
            expires_at=token_data["expires_at"].isoformat(),
            service="gmail",
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Gmail token for session {request.vertex_session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/tokens/calendar", response_model=TokenResponse)
async def get_calendar_token(
    request: TokenRequest,
    _: bool = Depends(verify_internal_api_key),
    db = Depends(get_db_connection)
) -> TokenResponse:
    """Get Calendar token for user by Vertex AI session ID."""
    try:
        session_repo = SessionRepository(db)
        token_repo = TokenRepository(db)
        
        # 1. Look up vertex_session_id → user_session_id → user_id
        session_data = await session_repo.get_session_by_vertex_id(request.vertex_session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        user_id = session_data["user_id"]
        
        # 2. Get Calendar token for user
        token_data = await token_repo.get_active_token_data(user_id, "calendar")
        
        if not token_data:
            raise HTTPException(status_code=404, detail="Calendar not connected")
        
        # 3. Return decrypted token
        return TokenResponse(
            access_token=token_data["access_token"],
            expires_at=token_data["expires_at"].isoformat(),
            service="calendar",
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Calendar token for session {request.vertex_session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/connection-status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    request: TokenRequest,
    _: bool = Depends(verify_internal_api_key),
    db = Depends(get_db_connection)
) -> ConnectionStatusResponse:
    """Get connection status for all services by Vertex AI session ID."""
    try:
        session_repo = SessionRepository(db)
        token_repo = TokenRepository(db)
        
        # 1. Look up vertex_session_id → user_session_id → user_id
        session_data = await session_repo.get_session_by_vertex_id(request.vertex_session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        user_id = session_data["user_id"]
        
        # 2. Check connection status for all services
        gmail_connected = await token_repo.is_service_connected(user_id, "gmail")
        calendar_connected = await token_repo.is_service_connected(user_id, "calendar")
        
        return ConnectionStatusResponse(
            gmail=gmail_connected,
            calendar=calendar_connected,
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get connection status for session {request.vertex_session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """Health check for internal API."""
    return {"status": "healthy", "service": "internal-api"} 