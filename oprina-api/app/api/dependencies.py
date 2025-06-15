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
from app.core.services.user_service import UserService
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

# Service Dependencies - ONLY USER
def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service dependency."""
    return UserService(user_repository)

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


# REMOVED ALL COMPLEX DEPENDENCIES:
# - No ChatService (imports AgentService)
# - No AgentService (imports client.py which fails)
# - No TokenService (imports complex dependencies)
# - No OAuthService (imports complex dependencies)
# - No VoiceService (imports complex dependencies)
# - No SessionRepository (might have dependencies)
# - No MessageRepository (might have dependencies)
# - No admin/API key authentication (complex)
# - No rate limiting (complex)
# - No pagination validation (not needed for basic endpoints)
# - No health checks (not needed for basic endpoints)
# - No request context (not needed for basic endpoints)

# This minimal version should only support:
# ✅ Health endpoints (no dependencies needed)
# ✅ Auth endpoints (user repository + auth manager)
# ✅ User endpoints (user repository + user service)