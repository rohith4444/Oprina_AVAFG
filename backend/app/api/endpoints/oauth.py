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

logger = get_logger(__name__)
router = APIRouter()


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
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Handle OAuth callback from Google.
    This endpoint receives the authorization code and processes it.
    """
    try:
        # Check for OAuth errors
        if error:
            logger.warning(f"OAuth error: {error} - {error_description}")
            # Redirect to frontend with error
            frontend_url = f"{oauth_service.settings.FRONTEND_LOGIN_URL}?error={error}"
            return RedirectResponse(url=frontend_url, status_code=302)
        
        if not code or not state:
            logger.warning("OAuth callback missing code or state")
            frontend_url = f"{oauth_service.settings.FRONTEND_LOGIN_URL}?error=missing_parameters"
            return RedirectResponse(url=frontend_url, status_code=302)
        
        # Process the OAuth callback
        result = await oauth_service.handle_callback(code, state)
        
        # Handle different types of results
        if result["action"] in ["login", "signup"]:
            # Authentication flow - generate JWT token
            auth_manager = AuthManager()
            user = result["user"]
            jwt_token = auth_manager.create_jwt_token(user["id"])
            
            # Redirect to frontend with token
            frontend_url = f"{result['redirect_url']}?token={jwt_token}&action={result['action']}"
            
        else:
            # Service connection flow - redirect to settings
            frontend_url = f"{result['redirect_url']}?service={result.get('service')}&status=connected"
        
        logger.info(f"OAuth callback successful: {result['action']}")
        return RedirectResponse(url=frontend_url, status_code=302)
        
    except OAuthError as e:
        logger.error(f"OAuth callback error: {str(e)}")
        frontend_url = f"{oauth_service.settings.FRONTEND_LOGIN_URL}?error=oauth_failed"
        return RedirectResponse(url=frontend_url, status_code=302)
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        frontend_url = f"{oauth_service.settings.FRONTEND_LOGIN_URL}?error=internal_error"
        return RedirectResponse(url=frontend_url, status_code=302)


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