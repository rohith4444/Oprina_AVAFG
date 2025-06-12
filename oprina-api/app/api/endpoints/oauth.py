"""
OAuth endpoints for Oprina API.

This module provides REST API endpoints for OAuth authorization flows,
token management, and service integrations.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    get_current_user,
    get_token_service,
    get_oauth_service
)
from app.core.services.token_service import TokenService
from app.core.services.oauth_service import OAuthService
from app.models.requests.oauth import (
    OAuthInitiateRequest,
    TokenRefreshRequest,
    TokenRevokeRequest
)
from app.models.responses.oauth import (
    OAuthInitiateResponse,
    TokenResponse,
    TokenListResponse,
    TokenStatsResponse,
    ProviderListResponse
)
from app.models.database.user import User
from app.utils.errors import OAuthError, TokenError, ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/providers", response_model=ProviderListResponse)
async def get_available_providers(
    token_service: TokenService = Depends(get_token_service)
):
    """Get list of available OAuth providers."""
    try:
        providers = token_service.get_available_providers()
        
        return ProviderListResponse(
            providers=providers,
            count=len(providers)
        )
        
    except Exception as e:
        logger.error(f"Failed to get providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available providers"
        )


@router.post("/authorize", response_model=OAuthInitiateResponse)
async def initiate_oauth_authorization(
    request: OAuthInitiateRequest,
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service)
):
    """Initiate OAuth authorization flow for a service provider."""
    try:
        auth_data = await token_service.initiate_oauth_flow(
            user_id=current_user.id,
            provider=request.provider,
            service_type=request.service_type,
            additional_scopes=request.additional_scopes
        )
        
        return OAuthInitiateResponse(
            authorization_url=auth_data["authorization_url"],
            state=auth_data["state"],
            provider=auth_data["provider"],
            service_type=auth_data["service_type"],
            expires_in=600  # State expires in 10 minutes
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to initiate OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth authorization"
        )


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    token_service: TokenService = Depends(get_token_service)
):
    """
    Handle OAuth callback from service providers.
    
    This endpoint receives the authorization code from OAuth providers
    and completes the token exchange process.
    """
    try:
        if error:
            logger.warning(f"OAuth error from {provider}: {error} - {error_description}")
            # In production, redirect to frontend with error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth authorization failed: {error}"
            )
        
        if not code or not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing authorization code or state parameter"
            )
        
        # Complete OAuth flow
        service_token = await token_service.complete_oauth_flow(
            provider=provider,
            code=code,
            state=state,
            error=error
        )
        
        # In production, redirect to frontend with success
        # For now, return token information
        return {
            "message": "OAuth authorization completed successfully",
            "token_id": service_token.id,
            "provider": service_token.provider,
            "service_type": service_token.service_type,
            "expires_at": service_token.expires_at.isoformat() if service_token.expires_at else None
        }
        
    except OAuthError as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth callback processing failed"
        )


@router.get("/tokens", response_model=TokenListResponse)
async def get_user_tokens(
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    provider: Optional[str] = Query(None, description="Filter by OAuth provider"),
    active_only: bool = Query(True, description="Only return active tokens"),
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service)
):
    """Get all service tokens for the current user."""
    try:
        service_tokens = await token_service.get_user_service_tokens(
            user_id=current_user.id,
            service_type=service_type,
            provider=provider,
            active_only=active_only
        )
        
        # Convert to response format (without sensitive data)
        tokens = []
        for token in service_tokens:
            tokens.append({
                "id": token.id,
                "service_type": token.service_type,
                "provider": token.provider,
                "service_name": token.service_name,
                "scope": token.scope,
                "is_active": token.is_active,
                "is_revoked": token.is_revoked,
                "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                "created_at": token.created_at.isoformat(),
                "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
                "provider_email": token.provider_email
            })
        
        return TokenListResponse(
            tokens=tokens,
            count=len(tokens)
        )
        
    except Exception as e:
        logger.error(f"Failed to get user tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user tokens"
        )


@router.get("/tokens/{token_id}", response_model=TokenResponse)
async def get_token_details(
    token_id: str,
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service)
):
    """Get details for a specific service token."""
    try:
        # Get user tokens to verify ownership
        user_tokens = await token_service.get_user_service_tokens(
            user_id=current_user.id,
            active_only=False
        )
        
        # Find the requested token
        service_token = None
        for token in user_tokens:
            if token.id == token_id:
                service_token = token
                break
        
        if not service_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service token not found"
            )
        
        return TokenResponse(
            id=service_token.id,
            service_type=service_token.service_type,
            provider=service_token.provider,
            service_name=service_token.service_name,
            scope=service_token.scope,
            is_active=service_token.is_active,
            is_revoked=service_token.is_revoked,
            expires_at=service_token.expires_at.isoformat() if service_token.expires_at else None,
            created_at=service_token.created_at.isoformat(),
            last_used_at=service_token.last_used_at.isoformat() if service_token.last_used_at else None,
            provider_email=service_token.provider_email,
            token_metadata=service_token.token_metadata or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get token details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token details"
        )


@router.post("/tokens/{token_id}/refresh", response_model=TokenResponse)
async def refresh_token(
    token_id: str,
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service)
):
    """Refresh an expired or expiring service token."""
    try:
        # Verify token ownership
        user_tokens = await token_service.get_user_service_tokens(
            user_id=current_user.id,
            active_only=False
        )
        
        token_exists = any(token.id == token_id for token in user_tokens)
        if not token_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service token not found"
            )
        
        # Refresh the token
        updated_token = await token_service.refresh_service_token(token_id)
        
        return TokenResponse(
            id=updated_token.id,
            service_type=updated_token.service_type,
            provider=updated_token.provider,
            service_name=updated_token.service_name,
            scope=updated_token.scope,
            is_active=updated_token.is_active,
            is_revoked=updated_token.is_revoked,
            expires_at=updated_token.expires_at.isoformat() if updated_token.expires_at else None,
            created_at=updated_token.created_at.isoformat(),
            last_used_at=updated_token.last_used_at.isoformat() if updated_token.last_used_at else None,
            provider_email=updated_token.provider_email,
            token_metadata=updated_token.token_metadata or {}
        )
        
    except HTTPException:
        raise
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.delete("/tokens/{token_id}")
async def revoke_token(
    token_id: str,
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service)
):
    """Revoke a service token."""
    try:
        # Verify token ownership
        user_tokens = await token_service.get_user_service_tokens(
            user_id=current_user.id,
            active_only=False
        )
        
        token_exists = any(token.id == token_id for token in user_tokens)
        if not token_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service token not found"
            )
        
        # Revoke the token
        success = await token_service.revoke_service_token(token_id)
        
        if success:
            return {"message": "Token revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to revoke token"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke token"
        )


@router.get("/tokens/stats", response_model=TokenStatsResponse)
async def get_token_statistics(
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service)
):
    """Get token statistics for the current user."""
    try:
        stats = await token_service.get_token_statistics(current_user.id)
        
        return TokenStatsResponse(
            total_tokens=stats.get("total_tokens", 0),
            active_tokens=stats.get("active_tokens", 0),
            expiring_soon=stats.get("expiring_soon", 0),
            by_provider=stats.get("by_provider", {}),
            by_service_type=stats.get("by_service_type", {})
        )
        
    except Exception as e:
        logger.error(f"Failed to get token statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token statistics"
        )


@router.post("/tokens/cleanup")
async def cleanup_tokens(
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service)
):
    """
    Cleanup expired tokens and perform maintenance.
    
    This endpoint is typically called by administrators or scheduled tasks.
    """
    try:
        cleanup_results = await token_service.cleanup_expired_tokens()
        
        return {
            "message": "Token cleanup completed",
            "results": cleanup_results
        }
        
    except Exception as e:
        logger.error(f"Token cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token cleanup failed"
        ) 