"""
API dependencies for Oprina API.

This module provides dependency injection for database connections,
authentication, and service instances.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.database.connection import get_db_session
from app.core.database.repositories.user_repository import UserRepository
from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.repositories.message_repository import MessageRepository
from app.core.database.repositories.token_repository import TokenRepository
from app.core.services.user_service import UserService
from app.core.services.chat_service import ChatService
from app.core.services.agent_service import AgentService
from app.core.services.token_service import TokenService
from app.core.services.oauth_service import OAuthService
from app.core.services.voice_service import VoiceService
from app.models.database.user import User
from app.utils.auth import AuthManager
from app.utils.errors import AuthenticationError
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Security scheme for Bearer token authentication
security = HTTPBearer()


# Database Dependencies

def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


# Repository Dependencies

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository dependency."""
    return UserRepository(db)


def get_session_repository(db: Session = Depends(get_db)) -> SessionRepository:
    """Get session repository dependency."""
    return SessionRepository(db)


def get_message_repository(db: Session = Depends(get_db)) -> MessageRepository:
    """Get message repository dependency."""
    return MessageRepository(db)


def get_token_repository(db: Session = Depends(get_db)) -> TokenRepository:
    """Get token repository dependency."""
    return TokenRepository(db)


# Service Dependencies

def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Get user service dependency."""
    return UserService(user_repository)


def get_chat_service(
    message_repository: MessageRepository = Depends(get_message_repository),
    session_repository: SessionRepository = Depends(get_session_repository)
) -> ChatService:
    """Get chat service dependency."""
    return ChatService(message_repository, session_repository)


def get_agent_service() -> AgentService:
    """Get agent service dependency."""
    return AgentService()


def get_oauth_service(
    token_repository: TokenRepository = Depends(get_token_repository)
) -> OAuthService:
    """Get OAuth service dependency."""
    return OAuthService(token_repository)


def get_token_service(
    token_repository: TokenRepository = Depends(get_token_repository),
    oauth_service: OAuthService = Depends(get_oauth_service)
) -> TokenService:
    """Get enhanced token service dependency."""
    return TokenService(token_repository, oauth_service)


def get_voice_service(
    message_repository: MessageRepository = Depends(get_message_repository),
    session_repository: SessionRepository = Depends(get_session_repository),
    chat_service: ChatService = Depends(get_chat_service)
) -> VoiceService:
    """Get voice service dependency."""
    return VoiceService(message_repository, session_repository, chat_service)


# Authentication Dependencies

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    """
    Get current user from JWT token (optional).
    Returns None if no valid token is provided.
    """
    if not credentials:
        return None
    
    try:
        auth_manager = AuthManager()
        payload = auth_manager.decode_jwt_token(credentials.credentials)
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = await user_repository.get_user_by_id(user_id)
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception as e:
        logger.warning(f"Failed to authenticate user: {str(e)}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Get current user from JWT token (required).
    Raises HTTP 401 if no valid token is provided.
    """
    try:
        auth_manager = AuthManager()
        payload = auth_manager.decode_jwt_token(credentials.credentials)
        
        if not payload:
            raise AuthenticationError("Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        user = await user_repository.get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")
        
        # Update last activity
        await user_repository.update_last_activity(user_id)
        
        logger.debug(f"Authenticated user: {user.email}")
        return user
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    Ensures user is both authenticated and active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify admin permissions.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# API Key Authentication

async def get_api_key_user(
    request: Request,
    db: Session = Depends(get_db),
    user_repository: UserRepository = Depends(get_user_repository),
    token_service: TokenService = Depends(get_token_service)
) -> Optional[User]:
    """
    Authenticate user via API key.
    Checks for API key in headers and validates it.
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    try:
        # Validate API key and get user info
        key_info = await token_service.validate_api_key(api_key)
        if not key_info:
            return None
        
        user = await user_repository.get_user_by_id(key_info["user_id"])
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception as e:
        logger.warning(f"API key validation failed: {str(e)}")
        return None


async def get_user_from_token_or_api_key(
    jwt_user: Optional[User] = Depends(get_current_user_optional),
    api_key_user: Optional[User] = Depends(get_api_key_user)
) -> Optional[User]:
    """
    Get user from either JWT token or API key.
    Prefers JWT token if both are provided.
    """
    return jwt_user or api_key_user


async def require_authentication(
    user: Optional[User] = Depends(get_user_from_token_or_api_key)
) -> User:
    """
    Require authentication via either JWT token or API key.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Rate Limiting Dependencies (placeholder for future implementation)

async def rate_limit_per_user(
    current_user: User = Depends(get_current_user),
    request: Request = None
) -> User:
    """
    Apply rate limiting per user.
    Currently a placeholder - implement with Redis in production.
    """
    # TODO: Implement rate limiting with Redis
    # For now, just pass through the user
    return current_user


async def rate_limit_per_ip(request: Request) -> Request:
    """
    Apply rate limiting per IP address.
    Currently a placeholder - implement with Redis in production.
    """
    # TODO: Implement IP-based rate limiting with Redis
    # For now, just pass through the request
    return request


# Request Validation Dependencies

def validate_pagination(
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> dict:
    """
    Validate and normalize pagination parameters.
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be greater than 0"
        )
    
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be greater than 0"
        )
    
    if limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit cannot exceed {max_limit}"
        )
    
    offset = (page - 1) * limit
    
    return {
        "page": page,
        "limit": limit,
        "offset": offset
    }


# Service Health Dependencies

async def check_database_health(db: Session = Depends(get_db)) -> bool:
    """
    Check database connectivity for health endpoints.
    """
    try:
        # Simple query to test database connection
        db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


async def check_oauth_service_health(
    oauth_service: OAuthService = Depends(get_oauth_service)
) -> bool:
    """
    Check OAuth service health.
    """
    try:
        # Check if OAuth providers are configured
        providers = oauth_service.get_available_providers()
        return len(providers) > 0
    except Exception as e:
        logger.error(f"OAuth service health check failed: {str(e)}")
        return False


# Request Context Dependencies

async def get_request_context(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> dict:
    """
    Get request context information for logging and analytics.
    """
    return {
        "request_id": request.headers.get("X-Request-ID"),
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.client.host if request.client else None,
        "user_id": current_user.id if current_user else None,
        "method": request.method,
        "path": str(request.url.path),
        "query_params": dict(request.query_params)
    }
