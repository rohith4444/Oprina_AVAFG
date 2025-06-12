"""
Authentication utilities for Oprina API.

This module provides authentication functions for:
- Token generation and verification
- User session management
- Authentication decorators
- Security utilities
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import wraps

from app.utils.errors import AuthenticationError, AuthorizationError, TokenError
from app.utils.encryption import create_jwt_token, verify_jwt_token, generate_secure_token
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AuthManager:
    """Manages authentication operations for the application."""
    
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'development-secret-key')
        self.token_expiry_hours = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
        self.refresh_token_expiry_days = int(os.getenv('REFRESH_TOKEN_EXPIRY_DAYS', '30'))
    
    def create_access_token(self, user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """Create an access token for user authentication."""
        try:
            return create_jwt_token(
                user_id=user_id,
                expiry_hours=self.token_expiry_hours,
                secret_key=self.jwt_secret
            )
        except Exception as e:
            logger.error(f"Access token creation failed for user {user_id}: {str(e)}")
            raise TokenError(f"Failed to create access token: {str(e)}")
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token for token renewal."""
        try:
            # Refresh tokens have longer expiry
            from app.utils.encryption import jwt
            
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(days=self.refresh_token_expiry_days),
                'iat': datetime.utcnow(),
                'type': 'refresh_token',
                'jti': str(uuid.uuid4())  # Unique token ID for tracking
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            return token
        except Exception as e:
            logger.error(f"Refresh token creation failed for user {user_id}: {str(e)}")
            raise TokenError(f"Failed to create refresh token: {str(e)}")
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify an access token and return payload."""
        try:
            payload = verify_jwt_token(token, self.jwt_secret)
            
            # Check token type
            if payload.get('type') != 'access_token':
                raise TokenError("Invalid token type")
            
            return payload
        except TokenError:
            raise
        except Exception as e:
            logger.error(f"Access token verification failed: {str(e)}")
            raise TokenError(f"Token verification failed: {str(e)}")
    
    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verify a refresh token and return payload."""
        try:
            payload = verify_jwt_token(token, self.jwt_secret)
            
            # Check token type
            if payload.get('type') != 'refresh_token':
                raise TokenError("Invalid token type for refresh")
            
            return payload
        except TokenError:
            raise
        except Exception as e:
            logger.error(f"Refresh token verification failed: {str(e)}")
            raise TokenError(f"Refresh token verification failed: {str(e)}")


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get or create the global auth manager."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def generate_token(user_id: str, token_type: str = "access") -> str:
    """
    Generate an authentication token for a user.
    
    Args:
        user_id: User identifier
        token_type: Type of token ('access' or 'refresh')
        
    Returns:
        Generated token string
    """
    auth_manager = get_auth_manager()
    
    if token_type == "access":
        return auth_manager.create_access_token(user_id)
    elif token_type == "refresh":
        return auth_manager.create_refresh_token(user_id)
    else:
        raise ValidationError(f"Invalid token type: {token_type}")


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify an authentication token.
    
    Args:
        token: Token string to verify
        token_type: Type of token ('access' or 'refresh')
        
    Returns:
        Token payload dictionary
    """
    auth_manager = get_auth_manager()
    
    if token_type == "access":
        return auth_manager.verify_access_token(token)
    elif token_type == "refresh":
        return auth_manager.verify_refresh_token(token)
    else:
        raise ValidationError(f"Invalid token type: {token_type}")


def get_user_from_token(token: str) -> str:
    """
    Extract user ID from an access token.
    
    Args:
        token: Access token string
        
    Returns:
        User ID string
    """
    try:
        payload = verify_token(token, "access")
        return payload.get('user_id')
    except Exception as e:
        logger.error(f"Failed to extract user from token: {str(e)}")
        raise AuthenticationError("Invalid or expired token")


def create_session_token(user_id: str, session_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a session-specific token with additional data.
    
    Args:
        user_id: User identifier
        session_data: Additional session information
        
    Returns:
        Session token string
    """
    try:
        from app.utils.encryption import jwt
        
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'type': 'session_token',
            'session_id': str(uuid.uuid4()),
            'session_data': session_data or {}
        }
        
        auth_manager = get_auth_manager()
        token = jwt.encode(payload, auth_manager.jwt_secret, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f"Session token creation failed for user {user_id}: {str(e)}")
        raise TokenError(f"Failed to create session token: {str(e)}")


def verify_session_token(token: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Verify a session token and return user ID, session ID, and data.
    
    Args:
        token: Session token string
        
    Returns:
        Tuple of (user_id, session_id, session_data)
    """
    try:
        auth_manager = get_auth_manager()
        payload = verify_jwt_token(token, auth_manager.jwt_secret)
        
        # Check token type
        if payload.get('type') != 'session_token':
            raise TokenError("Invalid token type for session")
        
        return (
            payload.get('user_id'),
            payload.get('session_id'),
            payload.get('session_data', {})
        )
    except TokenError:
        raise
    except Exception as e:
        logger.error(f"Session token verification failed: {str(e)}")
        raise TokenError(f"Session token verification failed: {str(e)}")


def generate_api_key(user_id: str, name: Optional[str] = None) -> str:
    """
    Generate an API key for a user.
    
    Args:
        user_id: User identifier
        name: Optional name for the API key
        
    Returns:
        API key string
    """
    try:
        # Create a long-lived token for API access
        from app.utils.encryption import jwt
        
        payload = {
            'user_id': user_id,
            'type': 'api_key',
            'key_id': str(uuid.uuid4()),
            'name': name,
            'created_at': datetime.utcnow().isoformat()
        }
        
        auth_manager = get_auth_manager()
        token = jwt.encode(payload, auth_manager.jwt_secret, algorithm='HS256')
        
        # Format as API key
        key_prefix = f"oprina_ak_{user_id[:8]}"
        key_suffix = generate_secure_token(16)
        
        return f"{key_prefix}_{key_suffix}_{token}"
        
    except Exception as e:
        logger.error(f"API key generation failed for user {user_id}: {str(e)}")
        raise TokenError(f"Failed to generate API key: {str(e)}")


def verify_api_key(api_key: str) -> Dict[str, Any]:
    """
    Verify an API key and return payload.
    
    Args:
        api_key: API key string
        
    Returns:
        API key payload dictionary
    """
    try:
        # Parse API key format: oprina_ak_{user_id}_{suffix}_{token}
        parts = api_key.split('_')
        if len(parts) < 4 or parts[0] != 'oprina' or parts[1] != 'ak':
            raise TokenError("Invalid API key format")
        
        # Extract JWT token (last part)
        token = parts[-1]
        
        auth_manager = get_auth_manager()
        payload = verify_jwt_token(token, auth_manager.jwt_secret)
        
        # Check token type
        if payload.get('type') != 'api_key':
            raise TokenError("Invalid token type for API key")
        
        return payload
        
    except TokenError:
        raise
    except Exception as e:
        logger.error(f"API key verification failed: {str(e)}")
        raise TokenError(f"API key verification failed: {str(e)}")


def require_auth(func):
    """
    Decorator to require authentication for a function.
    
    The decorated function should accept a 'current_user' parameter.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # This is a placeholder decorator
        # In FastAPI, authentication is handled by dependencies
        # This decorator is for non-FastAPI functions
        
        token = kwargs.get('token') or (args[0] if args else None)
        if not token:
            raise AuthenticationError("Authentication token required")
        
        try:
            user_id = get_user_from_token(token)
            kwargs['current_user_id'] = user_id
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication failed in decorator: {str(e)}")
            raise AuthenticationError("Invalid authentication token")
    
    return wrapper


def require_permission(permission: str):
    """
    Decorator to require specific permission for a function.
    
    Args:
        permission: Required permission string
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This is a placeholder for permission checking
            # In a full implementation, this would check user permissions
            
            current_user_id = kwargs.get('current_user_id')
            if not current_user_id:
                raise AuthorizationError("User context required for permission check")
            
            # TODO: Implement actual permission checking logic
            # For now, just log the permission check
            logger.info(f"Permission check: {permission} for user {current_user_id}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def hash_session_id(user_id: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate a session ID hash for a user.
    
    Args:
        user_id: User identifier
        timestamp: Optional timestamp (uses current time if not provided)
        
    Returns:
        Session ID string
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Create deterministic session ID based on user and time
    import hashlib
    
    data = f"{user_id}_{timestamp.isoformat()}_{generate_secure_token(8)}"
    session_hash = hashlib.sha256(data.encode()).hexdigest()
    
    return f"sess_{user_id[:8]}_{session_hash[:16]}"


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired without raising exceptions.
    
    Args:
        token: Token string to check
        
    Returns:
        True if token is expired, False otherwise
    """
    try:
        verify_token(token)
        return False
    except TokenError as e:
        if "expired" in str(e).lower():
            return True
        return False
    except Exception:
        return True
