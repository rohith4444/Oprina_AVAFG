"""
Simple OAuth endpoints for Oprina API.

Supports 4 OAuth flows:
1. Connect Gmail (authenticated users)
2. Connect Calendar (authenticated users) 
3. Google Login (public)
4. Google Signup (public)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional

from app.api.dependencies import get_current_user, get_user_repository, get_current_user_supabase, get_current_user_supabase_optional
from app.core.database.repositories.user_repository import UserRepository
from app.core.services.google_oauth_service import GoogleOAuthService
from app.core.services.background_tasks import get_background_token_service
from app.api.models.requests.oauth import OAuthConnectRequest, OAuthDisconnectRequest
from app.api.models.responses.oauth import (
    OAuthUrlResponse, 
    OAuthCallbackResponse, 
    ConnectionStatusResponse, 
    DisconnectResponse,
    GoogleAuthResponse
)
from app.utils.logging import get_logger
from app.utils.errors import OAuthError, ValidationError
from app.utils.auth import AuthManager
from app.config import get_settings

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


def get_oauth_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> GoogleOAuthService:
    """Get OAuth service dependency."""
    return GoogleOAuthService(user_repository)


# =============================================================================
# SERVICE CONNECTION ENDPOINTS (Authenticated)
# =============================================================================

@router.get("/connect/{service}")
async def connect_service(
    service: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase),
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
):
    """
    Get OAuth URL to connect a service (Gmail or Calendar).
    Returns the URL instead of redirecting directly.
    """
    try:
        if service not in ["gmail", "calendar"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service must be 'gmail' or 'calendar'"
            )
        
        user_id = current_user["id"]
        
        # Get appropriate OAuth URL
        if service == "gmail":
            auth_url, state = oauth_service.get_gmail_connect_url(user_id)
        else:  # calendar
            auth_url, state = oauth_service.get_calendar_connect_url(user_id)
        
        logger.info(f"Generated {service} connect URL for user {user_id}")
        
        # Return the URL instead of redirecting
        return {
            "auth_url": auth_url,
            "service": service,
            "user_id": user_id,
            "state": state
        }
        
    except Exception as e:
        logger.error(f"Failed to connect {service} for user {current_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate {service} connection"
        )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_service(
    request: OAuthDisconnectRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase),
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
):
    """Disconnect a service (remove stored tokens)."""
    try:
        user_id = current_user["id"]
        result = await oauth_service.disconnect_service(user_id, request.service)
        
        return DisconnectResponse(**result)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to disconnect {request.service} for user {current_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect {request.service}"
        )


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase),
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
):
    """Get connection status for all services."""
    try:
        user_id = current_user["id"]
        status = await oauth_service.get_service_connection_status(user_id)
        
        return ConnectionStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Failed to get connection status for user {current_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get connection status"
        )


# =============================================================================
# GOOGLE AUTHENTICATION ENDPOINTS (Public)
# =============================================================================

@router.get("/google/login")
async def google_login(
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
):
    """
    Initiate Google login flow.
    Used by Login page "Log in with Google" button.
    """
    try:
        auth_url, state = oauth_service.get_google_login_url()
        
        logger.info("Generated Google login URL")
        
        # Redirect user to Google OAuth
        return RedirectResponse(url=auth_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Failed to initiate Google login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Google login"
        )


@router.get("/google/signup")
async def google_signup(
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
):
    """
    Initiate Google signup flow.
    Used by Signup page "Sign up with Google" button.
    """
    try:
        auth_url, state = oauth_service.get_google_signup_url()
        
        logger.info("Generated Google signup URL")
        
        # Redirect user to Google OAuth
        return RedirectResponse(url=auth_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Failed to initiate Google signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Google signup"
        )


# =============================================================================
# OAUTH CALLBACK ENDPOINT (Public)
# =============================================================================

@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    oauth_service: GoogleOAuthService = Depends(get_oauth_service)
):
    """Handle OAuth callback from Google."""
    try:
        if error:
            logger.warning(f"OAuth error: {error} - {error_description}")
            # For now, default to settings page for errors
            return RedirectResponse(
                url=f"{settings.FRONTEND_SETTINGS_URL}?error={error}",
                status_code=302
            )
        
        if not code or not state:
            logger.warning("OAuth callback missing code or state")
            return RedirectResponse(
                url=f"{settings.FRONTEND_SETTINGS_URL}?error=missing_parameters",
                status_code=302
            )
        
        # Process the OAuth callback
        result = await oauth_service.handle_callback(code, state)
        
        # 🎯 KEY CHANGE: Use the redirect_url from the service result
        if result["action"] in ["gmail_connect", "calendar_connect"]:
            # Service connections - use the redirect_url from service
            frontend_url = f"{result['redirect_url']}?service={result['service']}&status=connected"
            
        elif result["action"] in ["google_login", "google_signup"]:
            # Authentication flows (unused for now, but keep the code)
            frontend_url = f"{result['redirect_url']}?action={result['action']}&status=success"
            
        else:
            # Fallback - shouldn't happen but be safe
            logger.warning(f"Unknown OAuth action: {result['action']}")
            frontend_url = f"{settings.FRONTEND_SETTINGS_URL}?status=unknown"
        
        logger.info(f"OAuth callback successful: {result['action']}")
        return RedirectResponse(url=frontend_url, status_code=302)
        
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_SETTINGS_URL}?error=callback_failed",
            status_code=302
        )


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/config")
async def get_oauth_config():
    """Get OAuth configuration status (for frontend)."""
    try:
        oauth_service = GoogleOAuthService(None)  # Just for config check
        
        return {
            "configured": bool(oauth_service.client_id and oauth_service.client_secret),
            "google_client_id": oauth_service.client_id,  # Frontend needs this
            "redirect_uri": oauth_service.redirect_uri
        }
        
    except Exception as e:
        return {
            "configured": False,
            "error": "OAuth not configured"
        }


@router.get("/health")
async def oauth_health_check():
    """Health check for OAuth service."""
    try:
        oauth_service = GoogleOAuthService(None)
        
        return {
            "status": "healthy",
            "oauth_configured": bool(oauth_service.client_id and oauth_service.client_secret),
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
@router.get("/background-status")
async def get_background_service_status():
    """Get background token refresh service status."""
    try:
        bg_service = get_background_token_service()
        return bg_service.get_stats()
    except Exception as e:
        logger.error(f"Failed to get background service status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get background service status"
        )