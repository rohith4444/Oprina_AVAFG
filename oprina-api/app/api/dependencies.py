"""
Clean dependencies.py - ONLY health, auth, and user endpoints support.
Removed all complex service chains that cause import errors.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client

# Core imports that should work
from app.core.database.connection import get_database_client
from app.core.database.repositories.user_repository import UserRepository
from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.repositories.message_repository import MessageRepository
from app.core.services.user_service import UserService
from app.core.services.agent_service import AgentService
from app.core.services.voice_service import VoiceService
from app.core.services.google_oauth_service import GoogleOAuthService
from app.utils.auth import AuthManager
from app.utils.errors import AuthenticationError
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Security scheme for Bearer token authentication
security = HTTPBearer()

# Database Dependencies
def get_db() -> Client:
    """Get database client dependency."""
    return get_database_client()

# Repository Dependencies - ONLY USER
def get_user_repository(db: Client = Depends(get_db)) -> UserRepository:
    """Get user repository dependency."""
    return UserRepository(db)

def get_session_repository(db: Client = Depends(get_db)) -> SessionRepository:
    """Get session repository dependency."""
    return SessionRepository(db)

def get_message_repository(db: Client = Depends(get_db)) -> MessageRepository:
    """Get message repository dependency."""
    return MessageRepository(db)

# Service Dependencies - ONLY USER
def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service dependency."""
    return UserService(user_repository)

def get_agent_service(
    session_repository: SessionRepository = Depends(get_session_repository),
    message_repository: MessageRepository = Depends(get_message_repository)
) -> AgentService:
    """Get agent service dependency."""
    return AgentService(session_repository, message_repository)

def get_voice_service(
    session_repository: SessionRepository = Depends(get_session_repository),
    message_repository: MessageRepository = Depends(get_message_repository),
    agent_service: AgentService = Depends(get_agent_service)
) -> VoiceService:
    """Get voice service dependency."""
    return VoiceService(session_repository, message_repository, agent_service)

def get_oauth_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> GoogleOAuthService:
    """Get OAuth service dependency."""
    return GoogleOAuthService(user_repository)

def get_auth_manager() -> AuthManager:
    """Get AuthManager instance."""
    return AuthManager()

# Authentication Dependencies
async def _authenticate_jwt_token(
    credentials: HTTPAuthorizationCredentials,
    user_repository: UserRepository,
    auth_manager: AuthManager,
    update_activity: bool = False
) -> Optional[dict]:
    """Helper function to authenticate JWT token and return user."""
    try:
        payload = auth_manager.decode_jwt_token(credentials.credentials)
        
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        user = await user_repository.get_user_by_id(user_id)
        if not user:
            return None
        
        if not user.get("is_active", True):
            return None
        
        # Update last activity if requested
        if update_activity:
            await user_repository.update_last_login(user_id)
            logger.debug(f"Authenticated user: {user.get('email')}")
        
        return user
        
    except Exception as e:
        logger.warning(f"JWT authentication failed: {str(e)}")
        return None

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository)
) -> Optional[dict]:
    """Get current user from JWT token (optional)."""
    if not credentials:
        return None
    
    auth_manager = AuthManager()
    return await _authenticate_jwt_token(credentials, user_repository, auth_manager)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository)
) -> dict:
    """Get current user from JWT token (required)."""
    auth_manager = AuthManager()
    user = await _authenticate_jwt_token(credentials, user_repository, auth_manager, update_activity=True)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Alias for compatibility with your auth endpoints
get_optional_current_user = get_current_user_optional

