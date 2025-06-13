"""
Admin endpoints for Oprina API.

This module provides administrative endpoints for managing
background tasks, OAuth tokens, and system maintenance.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.core.database.repositories.token_repository import TokenRepository
from app.core.services.oauth_service import get_oauth_service
from app.core.services.background_tasks import (
    get_background_service, trigger_token_refresh, trigger_cleanup
)
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()
security = HTTPBearer()

router = APIRouter()


def verify_admin_token(token: str = Depends(security)) -> bool:
    """Verify admin access token."""
    # In production, implement proper admin authentication
    # For now, use a simple token check
    admin_token = getattr(settings, 'ADMIN_TOKEN', 'admin-token-change-in-production')
    
    if token.credentials != admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )
    
    return True


@router.get("/background-tasks/status")
async def get_background_task_status(
    _: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """Get status of background tasks."""
    try:
        # Get OAuth service
        token_repo = TokenRepository()
        oauth_service = get_oauth_service(token_repo)
        
        # Get background service
        background_service = get_background_service(oauth_service)
        
        return background_service.get_task_status()
        
    except Exception as e:
        logger.error(f"Error getting background task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get background task status"
        )


@router.post("/background-tasks/refresh-tokens")
async def manual_token_refresh(
    _: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """Manually trigger token refresh."""
    try:
        # Get OAuth service
        token_repo = TokenRepository()
        oauth_service = get_oauth_service(token_repo)
        
        # Trigger refresh
        results = await trigger_token_refresh(oauth_service)
        
        return {
            "message": "Token refresh completed",
            "results": results,
            "total_refreshed": sum(results.values())
        }
        
    except Exception as e:
        logger.error(f"Error in manual token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh tokens"
        )


@router.post("/background-tasks/cleanup")
async def manual_cleanup(
    _: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """Manually trigger cleanup."""
    try:
        # Get OAuth service
        token_repo = TokenRepository()
        oauth_service = get_oauth_service(token_repo)
        
        # Trigger cleanup
        expired_count = await trigger_cleanup(oauth_service)
        
        return {
            "message": "Cleanup completed",
            "expired_tokens_removed": expired_count
        }
        
    except Exception as e:
        logger.error(f"Error in manual cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform cleanup"
        )


@router.get("/oauth/providers")
async def get_oauth_providers(
    _: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """Get available OAuth providers and their configuration."""
    try:
        # Get OAuth service
        token_repo = TokenRepository()
        oauth_service = get_oauth_service(token_repo)
        
        providers = oauth_service.get_available_providers()
        
        # Get provider details
        provider_details = {}
        for provider_name in providers:
            if provider_name in oauth_service.providers:
                provider = oauth_service.providers[provider_name]
                provider_details[provider_name] = {
                    "name": provider.name,
                    "auth_url": provider.auth_url,
                    "token_url": provider.token_url,
                    "scope": provider.scope,
                    "service_type": getattr(provider, 'service_type', 'default')
                }
        
        return {
            "available_providers": providers,
            "provider_details": provider_details
        }
        
    except Exception as e:
        logger.error(f"Error getting OAuth providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get OAuth providers"
        )


@router.get("/oauth/tokens/stats")
async def get_token_stats(
    _: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """Get OAuth token statistics."""
    try:
        # Get token repository
        token_repo = TokenRepository()
        
        # Get all tokens (this would need to be implemented in the repository)
        # For now, return placeholder stats
        return {
            "message": "Token statistics endpoint",
            "note": "Implementation needed in TokenRepository",
            "suggested_stats": [
                "total_tokens",
                "active_tokens", 
                "expired_tokens",
                "tokens_by_provider",
                "tokens_by_service_type",
                "tokens_expiring_soon"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting token stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get token statistics"
        )


@router.get("/system/health")
async def system_health(
    _: bool = Depends(verify_admin_token)
) -> Dict[str, Any]:
    """Get system health status."""
    try:
        # Check database connection
        token_repo = TokenRepository()
        db_healthy = True
        try:
            # This would need a health check method in the repository
            pass
        except Exception:
            db_healthy = False
        
        # Check OAuth service
        oauth_service = get_oauth_service(token_repo)
        oauth_healthy = len(oauth_service.get_available_providers()) > 0
        
        # Check background tasks
        background_service = get_background_service(oauth_service)
        background_status = background_service.get_task_status()
        background_healthy = background_status.get("running", False)
        
        overall_healthy = db_healthy and oauth_healthy and background_healthy
        
        return {
            "overall_healthy": overall_healthy,
            "components": {
                "database": {"healthy": db_healthy},
                "oauth_service": {
                    "healthy": oauth_healthy,
                    "providers": oauth_service.get_available_providers()
                },
                "background_tasks": {
                    "healthy": background_healthy,
                    "status": background_status
                }
            },
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system health"
        ) 