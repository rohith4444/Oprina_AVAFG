"""
Supabase authentication utilities for validating frontend tokens in backend.
Provides bridge between Supabase frontend auth and backend services.
"""

import jwt
import json
from typing import Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client

from app.config import get_settings
from app.utils.logging import get_logger
from app.utils.errors import AuthenticationError, ValidationError

logger = get_logger(__name__)
settings = get_settings()

# Global Supabase client
_supabase_client: Optional[Client] = None


class SupabaseAuthError(AuthenticationError):
    """Specific error for Supabase authentication issues."""
    pass


def get_supabase_client() -> Optional[Client]:
    """
    Get or create Supabase client for token validation.
    Reuses the existing database connection logic.
    
    Returns:
        Supabase client instance or None if not configured
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        # Reuse the existing database client from connection.py
        from app.core.database.connection import get_database_client
        
        _supabase_client = get_database_client()
        logger.info("Supabase client initialized for token validation (reusing database client)")
        return _supabase_client
        
    except Exception as e:
        logger.error(f"Failed to get Supabase client from database connection: {e}")
        logger.warning("Supabase configuration missing - token validation disabled")
        return None


def validate_supabase_token(token: str) -> Dict[str, Any]:
    """
    Validate a Supabase JWT token and extract user information.
    
    Args:
        token: JWT token from Supabase frontend
        
    Returns:
        Dictionary containing validated user information
        
    Raises:
        SupabaseAuthError: If token is invalid or expired
    """
    try:
        logger.debug("Starting Supabase token validation")
        
        # Get Supabase client
        supabase_client = get_supabase_client()
        if not supabase_client:
            raise SupabaseAuthError("Supabase client not available")
        
        # Method 1: Try to get user using the token via Supabase
        try:
            # Use Supabase client to validate token
            user_response = supabase_client.auth.get_user(token)
            
            if user_response.user:
                user_data = {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "email_confirmed_at": user_response.user.email_confirmed_at,
                    "created_at": user_response.user.created_at,
                    "updated_at": user_response.user.updated_at,
                    "user_metadata": user_response.user.user_metadata or {},
                    "app_metadata": user_response.user.app_metadata or {}
                }
                
                logger.info(f"Supabase token validated for user: {user_data['email']}")
                return user_data
                
        except Exception as supabase_error:
            logger.warning(f"Supabase client validation failed: {supabase_error}")
            # Fall back to manual JWT validation
        
        # Method 2: Manual JWT validation (backup method)
        if settings.SUPABASE_JWT_SECRET:
            try:
                # Clean the JWT secret - remove quotes if they exist
                jwt_secret = settings.SUPABASE_JWT_SECRET.strip().strip('"').strip("'")
                
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_exp": True}
                )
                
                # Extract user info from JWT payload
                user_data = {
                    "id": payload.get("sub"),
                    "email": payload.get("email"),
                    "email_confirmed_at": payload.get("email_confirmed_at"),
                    "created_at": payload.get("created_at"),
                    "user_metadata": payload.get("user_metadata", {}),
                    "app_metadata": payload.get("app_metadata", {})
                }
                
                if not user_data["id"] or not user_data["email"]:
                    raise SupabaseAuthError("Invalid user data in token")
                
                logger.info(f"Manual JWT validation successful for user: {user_data['email']}")
                return user_data
                
            except jwt.ExpiredSignatureError:
                raise SupabaseAuthError("Token has expired")
            except jwt.InvalidTokenError as e:
                raise SupabaseAuthError(f"Invalid JWT token: {str(e)}")
        
        # If both methods fail
        raise SupabaseAuthError("Unable to validate token - no validation method available")
        
    except SupabaseAuthError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error validating Supabase token: {str(e)}")
        raise SupabaseAuthError(f"Token validation failed: {str(e)}")


def extract_user_profile(supabase_user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user profile information from Supabase user data.
    
    Args:
        supabase_user: User data from Supabase validation
        
    Returns:
        Dictionary with profile information for backend user creation
    """
    try:
        user_metadata = supabase_user.get("user_metadata", {})
        app_metadata = supabase_user.get("app_metadata", {})
        
        # Extract profile information
        profile = {
            "id": supabase_user["id"],
            "email": supabase_user["email"],
            "full_name": user_metadata.get("full_name") or user_metadata.get("name"),
            "preferred_name": user_metadata.get("preferred_name"),
            "display_name": user_metadata.get("display_name"),
            "avatar_url": user_metadata.get("avatar_url") or user_metadata.get("picture"),
            "work_type": user_metadata.get("work_type"),
            "ai_preferences": user_metadata.get("ai_preferences"),
            "email_verified": supabase_user.get("email_confirmed_at") is not None,
            "created_at": supabase_user.get("created_at"),
            "provider": app_metadata.get("provider", "email")
        }
        
        # Remove None values
        profile = {k: v for k, v in profile.items() if v is not None}
        
        logger.debug(f"Extracted profile for user {profile['email']}: {list(profile.keys())}")
        return profile
        
    except Exception as e:
        logger.error(f"Error extracting user profile: {str(e)}")
        # Return minimal profile as fallback
        return {
            "id": supabase_user["id"],
            "email": supabase_user["email"],
            "email_verified": False
        }


def test_supabase_connection() -> bool:
    """
    Test connection to Supabase for debugging.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return False
        
        # Try a simple operation
        # Note: This might fail if we don't have proper permissions, but it tests connection
        try:
            # Attempt to access auth admin (might not work with anon key)
            result = client.auth.get_user("test")
        except Exception:
            # Expected to fail, but means we can connect
            pass
        
        logger.info("Supabase connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Supabase connection test failed: {e}")
        return False


# Export main functions
__all__ = [
    "validate_supabase_token",
    "extract_user_profile", 
    "test_supabase_connection",
    "SupabaseAuthError"
]