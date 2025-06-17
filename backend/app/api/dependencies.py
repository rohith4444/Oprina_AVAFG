"""
Clean dependencies.py - ONLY health, auth, user, and avatar endpoints support.
Added avatar service dependencies while keeping existing structure.
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
from app.core.database.repositories.avatar_repository import AvatarRepository  # Added avatar repository
from app.core.services.user_service import UserService
from app.core.services.agent_service import AgentService
from app.core.services.voice_service import VoiceService
from app.core.services.google_oauth_service import GoogleOAuthService
from app.core.services.avatar_service import AvatarService  # Added avatar service
from app.utils.auth import AuthManager
from app.utils.errors import AuthenticationError
from app.utils.logging import get_logger
from app.utils.supabase_auth import validate_supabase_token, extract_user_profile, SupabaseAuthError
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Security scheme for Bearer token authentication
security = HTTPBearer()

# Database Dependencies
def get_db() -> Client:
    """Get database client dependency."""
    return get_database_client()

# Repository Dependencies
def get_user_repository(db: Client = Depends(get_db)) -> UserRepository:
    """Get user repository dependency."""
    return UserRepository(db)

def get_session_repository(db: Client = Depends(get_db)) -> SessionRepository:
    """Get session repository dependency."""
    return SessionRepository(db)

def get_message_repository(db: Client = Depends(get_db)) -> MessageRepository:
    """Get message repository dependency."""
    return MessageRepository(db)

def get_avatar_repository(db: Client = Depends(get_db)) -> AvatarRepository:
    """Get avatar repository dependency."""
    return AvatarRepository(db)

# Service Dependencies
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

def get_avatar_service(
    avatar_repository: AvatarRepository = Depends(get_avatar_repository)
) -> AvatarService:
    """Get avatar service dependency."""
    return AvatarService(avatar_repository)

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

async def get_current_user_supabase(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository)
) -> dict:
    """
    Get current user from Supabase token and sync with backend.
    This is the main auth dependency for Supabase frontend integration.
    """
    try:
        logger.debug("Validating Supabase token for user authentication")
        
        # Validate Supabase token
        supabase_user = validate_supabase_token(credentials.credentials)
        
        # Extract profile information
        user_profile = extract_user_profile(supabase_user)
        
        # Try to get existing backend user
        backend_user = await user_repository.get_user_by_id(supabase_user["id"])
        
        if not backend_user:
            logger.info(f"Creating new backend user for Supabase user: {user_profile['email']}")
            # Create new backend user with Supabase data
            backend_user = await user_repository.create_user({
                "id": user_profile["id"],  # Use Supabase UUID
                "email": user_profile["email"],
                "full_name": user_profile.get("full_name"),
                "preferred_name": user_profile.get("preferred_name"),
                "display_name": user_profile.get("display_name"),
                "avatar_url": user_profile.get("avatar_url"),
                "work_type": user_profile.get("work_type"),
                "ai_preferences": user_profile.get("ai_preferences"),
                "is_active": True,
                "is_verified": user_profile.get("email_verified", False),
                "created_at": user_profile.get("created_at")
            })
        else:
            # Update last activity for existing user
            await user_repository.update_last_login(backend_user["id"])
            logger.debug(f"Updated activity for existing user: {backend_user['email']}")
        
        # Return backend user format
        return backend_user
        
    except SupabaseAuthError as e:
        logger.warning(f"Supabase authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Supabase authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in Supabase authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_user_supabase_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository)
) -> Optional[dict]:
    """
    Optional Supabase user authentication.
    Returns None if no credentials provided, raises exception if credentials invalid.
    """
    if not credentials:
        return None
    
    # Use the main Supabase auth function
    return await get_current_user_supabase(credentials, user_repository)


async def get_current_user_flexible(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository)
) -> dict:
    """
    Flexible authentication that tries both Supabase and JWT tokens.
    Useful during transition period.
    """
    try:
        # First try Supabase authentication
        return await get_current_user_supabase(credentials, user_repository)
    except HTTPException as supabase_error:
        logger.debug("Supabase auth failed, trying JWT auth")
        
        try:
            # Fall back to original JWT authentication
            return await get_current_user(credentials, user_repository)
        except HTTPException as jwt_error:
            logger.warning("Both Supabase and JWT authentication failed")
            # Return the more specific Supabase error
            raise supabase_error
        
        
# Alias for compatibility with your auth endpoints
get_optional_current_user = get_current_user_optional