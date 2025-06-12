"""
OAuth service for Oprina API.

This module handles OAuth 2.0 authorization flows, token management,
and integration with various service providers like Google, Microsoft, etc.
"""

import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlencode, parse_qs

import httpx
from fastapi import HTTPException, status

from app.core.database.repositories.token_repository import TokenRepository
from app.models.database.token import ServiceToken
from app.utils.errors import OAuthError, TokenError, ValidationError
from app.utils.logging import get_logger
from app.utils.validation import validate_email, validate_url
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class OAuthProvider:
    """Base OAuth provider configuration."""
    
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        auth_url: str,
        token_url: str,
        scope: str,
        redirect_uri: str
    ):
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.scope = scope
        self.redirect_uri = redirect_uri


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 provider configuration."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scope="openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.readonly",
            redirect_uri=redirect_uri
        )
    
    def get_user_info_url(self) -> str:
        return "https://www.googleapis.com/oauth2/v2/userinfo"


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth 2.0 provider configuration."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(
            name="microsoft",
            client_id=client_id,
            client_secret=client_secret,
            auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            scope="openid email profile offline_access https://graph.microsoft.com/mail.read https://graph.microsoft.com/calendars.read",
            redirect_uri=redirect_uri
        )
    
    def get_user_info_url(self) -> str:
        return "https://graph.microsoft.com/v1.0/me"


class OAuthService:
    """OAuth service for handling authorization flows and token management."""
    
    def __init__(self, token_repository: TokenRepository):
        self.token_repository = token_repository
        self.providers = self._initialize_providers()
        self.state_storage: Dict[str, Dict[str, Any]] = {}  # In production, use Redis
    
    def _initialize_providers(self) -> Dict[str, OAuthProvider]:
        """Initialize OAuth providers based on configuration."""
        providers = {}
        
        # Google OAuth
        if settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET:
            providers["google"] = GoogleOAuthProvider(
                client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
                redirect_uri=f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/oauth/callback/google"
            )
        
        # Microsoft OAuth
        if settings.MICROSOFT_OAUTH_CLIENT_ID and settings.MICROSOFT_OAUTH_CLIENT_SECRET:
            providers["microsoft"] = MicrosoftOAuthProvider(
                client_id=settings.MICROSOFT_OAUTH_CLIENT_ID,
                client_secret=settings.MICROSOFT_OAUTH_CLIENT_SECRET,
                redirect_uri=f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/oauth/callback/microsoft"
            )
        
        return providers
    
    def get_authorization_url(
        self,
        provider_name: str,
        user_id: str,
        service_type: str = "default",
        additional_scopes: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Generate OAuth authorization URL and state.
        
        Args:
            provider_name: OAuth provider (google, microsoft, etc.)
            user_id: User identifier
            service_type: Type of service being authorized
            additional_scopes: Additional OAuth scopes to request
            
        Returns:
            Tuple of (authorization_url, state)
        """
        if provider_name not in self.providers:
            raise OAuthError(f"Provider {provider_name} not configured")
        
        provider = self.providers[provider_name]
        
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        
        # Store state information
        self.state_storage[state] = {
            "user_id": user_id,
            "provider": provider_name,
            "service_type": service_type,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        # Build scope string
        scopes = provider.scope
        if additional_scopes:
            scopes += " " + " ".join(additional_scopes)
        
        # Build authorization URL
        auth_params = {
            "client_id": provider.client_id,
            "redirect_uri": provider.redirect_uri,
            "scope": scopes,
            "response_type": "code",
            "state": state,
            "access_type": "offline",  # For refresh tokens
            "prompt": "consent"  # Force consent to get refresh token
        }
        
        auth_url = f"{provider.auth_url}?{urlencode(auth_params)}"
        
        logger.info(f"Generated OAuth URL for user {user_id}, provider {provider_name}")
        return auth_url, state
    
    async def handle_callback(
        self,
        provider_name: str,
        code: str,
        state: str,
        error: Optional[str] = None
    ) -> ServiceToken:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            provider_name: OAuth provider name
            code: Authorization code from provider
            state: State parameter for validation
            error: Error from OAuth provider
            
        Returns:
            Created ServiceToken instance
        """
        if error:
            logger.error(f"OAuth error from {provider_name}: {error}")
            raise OAuthError(f"OAuth authorization failed: {error}")
        
        # Validate state
        if state not in self.state_storage:
            raise OAuthError("Invalid or expired state parameter")
        
        state_data = self.state_storage[state]
        
        # Check state expiration
        if datetime.utcnow() > state_data["expires_at"]:
            del self.state_storage[state]
            raise OAuthError("Authorization state has expired")
        
        # Validate provider
        if state_data["provider"] != provider_name:
            raise OAuthError("Provider mismatch in state")
        
        if provider_name not in self.providers:
            raise OAuthError(f"Provider {provider_name} not configured")
        
        provider = self.providers[provider_name]
        
        try:
            # Exchange code for tokens
            token_data = await self._exchange_code_for_tokens(provider, code)
            
            # Get user information
            user_info = await self._get_user_info(provider, token_data["access_token"])
            
            # Create service token
            service_token = await self.token_repository.create_service_token(
                user_id=state_data["user_id"],
                service_type=state_data["service_type"],
                provider=provider_name,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                id_token=token_data.get("id_token"),
                expires_at=self._calculate_expiry(token_data.get("expires_in")),
                scope=token_data.get("scope", provider.scope),
                provider_user_id=user_info.get("id"),
                provider_email=user_info.get("email"),
                service_name=f"{provider_name.title()} {state_data['service_type'].title()}",
                token_metadata={
                    "user_info": user_info,
                    "token_type": token_data.get("token_type", "Bearer")
                }
            )
            
            # Clean up state
            del self.state_storage[state]
            
            logger.info(f"Successfully created OAuth token for user {state_data['user_id']}, provider {provider_name}")
            return service_token
            
        except Exception as e:
            # Clean up state on error
            if state in self.state_storage:
                del self.state_storage[state]
            
            logger.error(f"OAuth callback failed for {provider_name}: {str(e)}")
            raise OAuthError(f"Failed to complete OAuth flow: {str(e)}")
    
    async def _exchange_code_for_tokens(
        self,
        provider: OAuthProvider,
        code: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access/refresh tokens."""
        token_data = {
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": provider.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.token_url,
                data=token_data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Token exchange failed: {error_detail}")
                raise OAuthError(f"Failed to exchange code for tokens: {error_detail}")
            
            return response.json()
    
    async def _get_user_info(
        self,
        provider: OAuthProvider,
        access_token: str
    ) -> Dict[str, Any]:
        """Get user information from OAuth provider."""
        if isinstance(provider, GoogleOAuthProvider):
            user_info_url = provider.get_user_info_url()
        elif isinstance(provider, MicrosoftOAuthProvider):
            user_info_url = provider.get_user_info_url()
        else:
            return {}
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get user info from {provider.name}: {response.text}")
                return {}
            
            user_data = response.json()
            
            # Normalize user info across providers
            normalized_info = {
                "id": user_data.get("id") or user_data.get("sub"),
                "email": user_data.get("email"),
                "name": user_data.get("name") or user_data.get("displayName"),
                "given_name": user_data.get("given_name") or user_data.get("givenName"),
                "family_name": user_data.get("family_name") or user_data.get("surname"),
                "picture": user_data.get("picture") or user_data.get("photo", {}).get("url"),
                "verified_email": user_data.get("verified_email", True),
                "locale": user_data.get("locale"),
                "raw_data": user_data
            }
            
            return normalized_info
    
    def _calculate_expiry(self, expires_in: Optional[int]) -> Optional[datetime]:
        """Calculate token expiry datetime."""
        if not expires_in:
            return None
        return datetime.utcnow() + timedelta(seconds=expires_in)
    
    async def refresh_token(self, service_token: ServiceToken) -> ServiceToken:
        """
        Refresh an expired or expiring access token.
        
        Args:
            service_token: ServiceToken instance to refresh
            
        Returns:
            Updated ServiceToken instance
        """
        if not service_token.refresh_token_encrypted:
            raise TokenError("No refresh token available for this service token")
        
        if service_token.provider not in self.providers:
            raise TokenError(f"Provider {service_token.provider} not configured")
        
        provider = self.providers[service_token.provider]
        
        # Create refresh log
        refresh_log = await self.token_repository.create_refresh_log(
            service_token_id=service_token.id,
            refresh_type="manual"
        )
        
        try:
            # Get encrypted refresh token
            refresh_token = await self.token_repository.get_decrypted_refresh_token(
                service_token.id
            )
            
            if not refresh_token:
                raise TokenError("Failed to decrypt refresh token")
            
            # Refresh the token
            token_data = await self._refresh_access_token(provider, refresh_token)
            
            # Update service token
            updated_token = await self.token_repository.update_token(
                token_id=service_token.id,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", refresh_token),
                expires_at=self._calculate_expiry(token_data.get("expires_in")),
                scope=token_data.get("scope")
            )
            
            # Update refresh log
            await self.token_repository.update_refresh_log(
                log_id=refresh_log.id,
                success=True,
                new_expires_at=updated_token.expires_at
            )
            
            logger.info(f"Successfully refreshed token {service_token.id}")
            return updated_token
            
        except Exception as e:
            # Update refresh log with error
            await self.token_repository.update_refresh_log(
                log_id=refresh_log.id,
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Failed to refresh token {service_token.id}: {str(e)}")
            raise TokenError(f"Failed to refresh token: {str(e)}")
    
    async def _refresh_access_token(
        self,
        provider: OAuthProvider,
        refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        refresh_data = {
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider.token_url,
                data=refresh_data,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Token refresh failed: {error_detail}")
                raise TokenError(f"Failed to refresh access token: {error_detail}")
            
            return response.json()
    
    async def revoke_token(self, service_token: ServiceToken) -> bool:
        """
        Revoke a service token with the OAuth provider.
        
        Args:
            service_token: ServiceToken to revoke
            
        Returns:
            True if revocation successful
        """
        try:
            # Get provider-specific revoke URL
            revoke_url = None
            if service_token.provider == "google":
                revoke_url = "https://oauth2.googleapis.com/revoke"
            elif service_token.provider == "microsoft":
                # Microsoft doesn't have a standard revoke endpoint
                # Token will be revoked when deleted from our system
                pass
            
            if revoke_url:
                access_token = await self.token_repository.get_decrypted_access_token(
                    service_token.id
                )
                
                if access_token:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            revoke_url,
                            data={"token": access_token}
                        )
                        
                        if response.status_code not in [200, 204]:
                            logger.warning(f"Failed to revoke token with provider: {response.text}")
            
            # Revoke in our system
            await self.token_repository.revoke_token(service_token.id)
            
            logger.info(f"Successfully revoked token {service_token.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke token {service_token.id}: {str(e)}")
            return False
    
    async def get_user_tokens(
        self,
        user_id: str,
        service_type: Optional[str] = None,
        provider: Optional[str] = None,
        active_only: bool = True
    ) -> List[ServiceToken]:
        """Get all service tokens for a user."""
        return await self.token_repository.get_user_service_tokens(
            user_id=user_id,
            service_type=service_type,
            provider=provider,
            active_only=active_only
        )
    
    async def get_active_token(
        self,
        user_id: str,
        service_type: str,
        provider: str
    ) -> Optional[ServiceToken]:
        """Get the active token for a specific service and provider."""
        return await self.token_repository.get_active_token(
            user_id=user_id,
            service_type=service_type,
            provider=provider
        )
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens."""
        return await self.token_repository.cleanup_expired_tokens()
    
    async def auto_refresh_expiring_tokens(self) -> Dict[str, int]:
        """Automatically refresh tokens that are expiring soon."""
        expiring_tokens = await self.token_repository.get_expiring_tokens(
            minutes_ahead=30
        )
        
        results = {
            "total": len(expiring_tokens),
            "refreshed": 0,
            "failed": 0,
            "skipped": 0
        }
        
        for token in expiring_tokens:
            try:
                await self.refresh_token(token)
                results["refreshed"] += 1
            except Exception as e:
                logger.error(f"Auto-refresh failed for token {token.id}: {str(e)}")
                results["failed"] += 1
        
        logger.info(f"Auto-refresh completed: {results}")
        return results
    
    def validate_provider(self, provider_name: str) -> bool:
        """Validate if a provider is configured and available."""
        return provider_name in self.providers
    
    def get_available_providers(self) -> List[str]:
        """Get list of available OAuth providers."""
        return list(self.providers.keys())


def get_oauth_service(token_repository: TokenRepository) -> OAuthService:
    """Get an OAuth service instance."""
    return OAuthService(token_repository) 