"""
Enhanced token service for Oprina API.

This module provides comprehensive token management including OAuth tokens,
API keys, session tokens, and integration with external services.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import httpx
from fastapi import HTTPException, status

from app.core.database.repositories.token_repository import TokenRepository
from app.core.services.oauth_service import OAuthService
from app.models.database.token import ServiceToken
from app.utils.errors import TokenError, OAuthError, ValidationError
from app.utils.logging import get_logger
from app.utils.auth import AuthManager
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class TokenService:
    """Enhanced token service with OAuth integration and token management."""
    
    def __init__(self, token_repository: TokenRepository, oauth_service: OAuthService):
        self.token_repository = token_repository
        self.oauth_service = oauth_service
        self.auth_manager = AuthManager()
    
    # HeyGen Avatar Token Management (existing functionality)
    
    async def create_heygen_token(self, user_id: str) -> Optional[str]:
        """
        Create a HeyGen streaming avatar token.
        Enhanced with validation and error handling.
        """
        if not settings.HEYGEN_API_KEY:
            logger.error("HeyGen API key not configured")
            raise TokenError("HeyGen API key not configured")
        
        url = "https://api.heygen.com/v1/streaming.create_token"
        headers = {
            "X-Api-Key": settings.HEYGEN_API_KEY,
            "Content-Type": "application/json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json={})
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("data", {}).get("token")
                    
                    if token:
                        logger.info(f"Successfully created HeyGen token for user {user_id}")
                        return token
                    else:
                        logger.error("HeyGen API returned success but no token")
                        raise TokenError("HeyGen API returned no token")
                else:
                    error_detail = response.text
                    logger.error(f"HeyGen API error: {response.status_code} - {error_detail}")
                    raise TokenError(f"HeyGen API error: {response.status_code}")
        
        except httpx.RequestError as e:
            logger.error(f"Network error calling HeyGen API: {str(e)}")
            raise TokenError("Network error calling HeyGen API")
        except Exception as e:
            logger.error(f"Unexpected error creating HeyGen token: {str(e)}")
            raise TokenError("Failed to create HeyGen token")
    
    # OAuth Token Management
    
    async def initiate_oauth_flow(
        self,
        user_id: str,
        provider: str,
        service_type: str = "default",
        additional_scopes: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Initiate OAuth authorization flow.
        
        Args:
            user_id: User identifier
            provider: OAuth provider (google, microsoft, etc.)
            service_type: Type of service being authorized
            additional_scopes: Additional OAuth scopes to request
            
        Returns:
            Dictionary with authorization_url and state
        """
        if not self.oauth_service.validate_provider(provider):
            raise ValidationError(f"Provider {provider} is not available")
        
        try:
            auth_url, state = self.oauth_service.get_authorization_url(
                provider_name=provider,
                user_id=user_id,
                service_type=service_type,
                additional_scopes=additional_scopes
            )
            
            logger.info(f"Initiated OAuth flow for user {user_id}, provider {provider}")
            return {
                "authorization_url": auth_url,
                "state": state,
                "provider": provider,
                "service_type": service_type
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow: {str(e)}")
            raise TokenError(f"Failed to initiate OAuth flow: {str(e)}")
    
    async def complete_oauth_flow(
        self,
        provider: str,
        code: str,
        state: str,
        error: Optional[str] = None
    ) -> ServiceToken:
        """
        Complete OAuth authorization flow and create service token.
        
        Args:
            provider: OAuth provider name
            code: Authorization code from provider
            state: State parameter for validation
            error: Error from OAuth provider
            
        Returns:
            Created ServiceToken instance
        """
        try:
            service_token = await self.oauth_service.handle_callback(
                provider_name=provider,
                code=code,
                state=state,
                error=error
            )
            
            logger.info(f"Completed OAuth flow for provider {provider}")
            return service_token
            
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {str(e)}")
            raise TokenError(f"Failed to complete OAuth flow: {str(e)}")
    
    async def refresh_service_token(self, token_id: str) -> ServiceToken:
        """
        Refresh an expired or expiring service token.
        
        Args:
            token_id: Service token ID to refresh
            
        Returns:
            Updated ServiceToken instance
        """
        try:
            service_token = await self.token_repository.get_service_token(token_id)
            if not service_token:
                raise TokenError("Service token not found")
            
            updated_token = await self.oauth_service.refresh_token(service_token)
            
            logger.info(f"Successfully refreshed service token {token_id}")
            return updated_token
            
        except Exception as e:
            logger.error(f"Failed to refresh service token {token_id}: {str(e)}")
            raise TokenError(f"Failed to refresh service token: {str(e)}")
    
    async def revoke_service_token(self, token_id: str) -> bool:
        """
        Revoke a service token.
        
        Args:
            token_id: Service token ID to revoke
            
        Returns:
            True if revocation successful
        """
        try:
            service_token = await self.token_repository.get_service_token(token_id)
            if not service_token:
                return False
            
            success = await self.oauth_service.revoke_token(service_token)
            
            if success:
                logger.info(f"Successfully revoked service token {token_id}")
            else:
                logger.warning(f"Failed to revoke service token {token_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error revoking service token {token_id}: {str(e)}")
            return False
    
    async def get_user_service_tokens(
        self,
        user_id: str,
        service_type: Optional[str] = None,
        provider: Optional[str] = None,
        active_only: bool = True
    ) -> List[ServiceToken]:
        """
        Get all service tokens for a user.
        
        Args:
            user_id: User identifier
            service_type: Filter by service type
            provider: Filter by OAuth provider
            active_only: Only return active tokens
            
        Returns:
            List of ServiceToken instances
        """
        try:
            tokens = await self.oauth_service.get_user_tokens(
                user_id=user_id,
                service_type=service_type,
                provider=provider,
                active_only=active_only
            )
            
            logger.debug(f"Retrieved {len(tokens)} service tokens for user {user_id}")
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to get user service tokens: {str(e)}")
            raise TokenError(f"Failed to get user service tokens: {str(e)}")
    
    async def get_active_service_token(
        self,
        user_id: str,
        service_type: str,
        provider: str
    ) -> Optional[ServiceToken]:
        """
        Get the active service token for a specific service and provider.
        
        Args:
            user_id: User identifier
            service_type: Type of service
            provider: OAuth provider
            
        Returns:
            ServiceToken instance if found and active
        """
        try:
            token = await self.oauth_service.get_active_token(
                user_id=user_id,
                service_type=service_type,
                provider=provider
            )
            
            if token and token.is_valid:
                # Auto-refresh if token is expiring soon
                if token.expires_soon(minutes_ahead=10):
                    logger.info(f"Auto-refreshing expiring token {token.id}")
                    token = await self.oauth_service.refresh_token(token)
                
                return token
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get active service token: {str(e)}")
            return None
    
    async def get_decrypted_access_token(
        self,
        user_id: str,
        service_type: str,
        provider: str
    ) -> Optional[str]:
        """
        Get decrypted access token for immediate use.
        
        Args:
            user_id: User identifier
            service_type: Type of service
            provider: OAuth provider
            
        Returns:
            Decrypted access token if available
        """
        try:
            service_token = await self.get_active_service_token(
                user_id=user_id,
                service_type=service_type,
                provider=provider
            )
            
            if not service_token:
                return None
            
            access_token = await self.token_repository.get_decrypted_access_token(
                service_token.id
            )
            
            return access_token
            
        except Exception as e:
            logger.error(f"Failed to get decrypted access token: {str(e)}")
            return None
    
    # API Key Management
    
    async def generate_api_key(
        self,
        user_id: str,
        key_name: str,
        permissions: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a new API key for a user.
        
        Args:
            user_id: User identifier
            key_name: Human-readable name for the key
            permissions: List of permissions/scopes
            expires_in_days: Expiry in days (None for no expiry)
            
        Returns:
            Dictionary with API key details
        """
        try:
            # Generate secure API key
            api_key = f"oprina_{secrets.token_urlsafe(32)}"
            
            # Calculate expiry
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create service token for API key
            service_token = await self.token_repository.create_service_token(
                user_id=user_id,
                service_type="api_key",
                provider="oprina",
                access_token=api_key,
                expires_at=expires_at,
                scope=" ".join(permissions) if permissions else "default",
                service_name=key_name,
                token_metadata={
                    "key_name": key_name,
                    "permissions": permissions or [],
                    "token_type": "api_key"
                }
            )
            
            logger.info(f"Generated API key for user {user_id}: {key_name}")
            
            return {
                "api_key": api_key,
                "token_id": service_token.id,
                "key_name": key_name,
                "permissions": permissions or [],
                "expires_at": expires_at.isoformat() if expires_at else None,
                "created_at": service_token.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate API key: {str(e)}")
            raise TokenError(f"Failed to generate API key: {str(e)}")
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return associated user information.
        
        Args:
            api_key: API key to validate
            
        Returns:
            Dictionary with user and token information if valid
        """
        try:
            # In production, this would use a more efficient lookup
            # For now, we'll search through service tokens
            from sqlalchemy.orm import sessionmaker
            from app.core.database.connection import get_db
            
            # This is a simplified implementation
            # In production, consider indexing API keys or using Redis cache
            
            return None  # Placeholder implementation
            
        except Exception as e:
            logger.error(f"Failed to validate API key: {str(e)}")
            return None
    
    # Token Maintenance
    
    async def cleanup_expired_tokens(self) -> Dict[str, int]:
        """
        Clean up expired tokens and perform maintenance.
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            # Clean up expired OAuth tokens
            oauth_cleaned = await self.oauth_service.cleanup_expired_tokens()
            
            # Auto-refresh expiring tokens
            refresh_results = await self.oauth_service.auto_refresh_expiring_tokens()
            
            logger.info(f"Token maintenance completed: {oauth_cleaned} expired, {refresh_results}")
            
            return {
                "expired_cleaned": oauth_cleaned,
                "auto_refresh_results": refresh_results
            }
            
        except Exception as e:
            logger.error(f"Token maintenance failed: {str(e)}")
            return {"error": str(e)}
    
    async def get_token_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get token statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with token statistics
        """
        try:
            all_tokens = await self.get_user_service_tokens(
                user_id=user_id,
                active_only=False
            )
            
            active_tokens = [t for t in all_tokens if t.is_active and not t.is_revoked]
            expiring_tokens = [t for t in active_tokens if t.expires_soon(minutes_ahead=60)]
            
            stats = {
                "total_tokens": len(all_tokens),
                "active_tokens": len(active_tokens),
                "expiring_soon": len(expiring_tokens),
                "by_provider": {},
                "by_service_type": {}
            }
            
            # Group by provider and service type
            for token in all_tokens:
                # By provider
                provider = token.provider
                if provider not in stats["by_provider"]:
                    stats["by_provider"][provider] = {"total": 0, "active": 0}
                stats["by_provider"][provider]["total"] += 1
                if token.is_active and not token.is_revoked:
                    stats["by_provider"][provider]["active"] += 1
                
                # By service type
                service_type = token.service_type
                if service_type not in stats["by_service_type"]:
                    stats["by_service_type"][service_type] = {"total": 0, "active": 0}
                stats["by_service_type"][service_type]["total"] += 1
                if token.is_active and not token.is_revoked:
                    stats["by_service_type"][service_type]["active"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get token statistics: {str(e)}")
            return {"error": str(e)}
    
    def get_available_providers(self) -> List[str]:
        """Get list of available OAuth providers."""
        return self.oauth_service.get_available_providers()


def get_token_service(
    token_repository: TokenRepository,
    oauth_service: OAuthService
) -> TokenService:
    """Get a token service instance."""
    return TokenService(token_repository, oauth_service)
