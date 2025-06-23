# backend/app/services/oauth/google_oauth_service.py
"""
TEMPORARY DEBUG VERSION - NO ENCRYPTION
=========================================
This version stores tokens in PLAIN TEXT for debugging.
⚠️ DO NOT USE IN PRODUCTION!
"""

import secrets
import httpx
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode
from datetime import datetime, timedelta

from app.config import get_settings
from app.core.database.repositories.user_repository import UserRepository
from app.utils.logging import get_logger
from app.utils.errors import OAuthError, ValidationError
# ⚠️ REMOVED: from app.utils.encryption import encrypt_token, decrypt_token

logger = get_logger(__name__)
settings = get_settings()


class GoogleOAuthService:
    """Google OAuth service - DEBUG VERSION WITHOUT ENCRYPTION."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        if not self.client_id or not self.client_secret:
            raise OAuthError("Google OAuth not configured - missing client credentials")
        
        logger.warning("🚨 DEBUG MODE: OAuth service running WITHOUT encryption!")
    
    # Authorization URL methods remain the same...
    def get_gmail_connect_url(self, user_id: str) -> Tuple[str, str]:
        """Get OAuth URL for connecting Gmail."""
        state = self._generate_state(user_id, "gmail_connect")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": settings.GOOGLE_GMAIL_SCOPES,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url, state
    
    # ... (other URL methods same as before)
    
    async def _handle_gmail_connect(self, user_id: str, tokens: Dict, user_info: Dict) -> Dict[str, Any]:
        """Handle Gmail connection - DEBUG VERSION WITHOUT ENCRYPTION."""
        try:
            # ⚠️ STORE TOKENS IN PLAIN TEXT (NO ENCRYPTION)
            plain_text_tokens = {
                "access_token": tokens["access_token"],  # ← NO encrypt_token() call
                "refresh_token": tokens.get("refresh_token", ""),  # ← NO encrypt_token() call
                "expires_at": (datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))).isoformat(),
                "scope": tokens.get("scope", ""),
                "connected_at": datetime.utcnow().isoformat(),
                "user_email": user_info.get("email"),
                "debug_mode": True  # ← Flag to indicate this is debug mode
            }
            
            logger.warning(f"🚨 STORING PLAIN TEXT TOKENS for user {user_id}")
            logger.debug(f"🔍 Token preview: access_token length = {len(plain_text_tokens['access_token'])}")
            
            # Update user with plain text tokens
            await self.user_repository.update_user(user_id, {
                "gmail_tokens": plain_text_tokens,
                "google_profile": user_info,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Gmail connected successfully for user {user_id} (DEBUG MODE)")
            
            return {
                "success": True,
                "service": "gmail",
                "action": "gmail_connect",
                "user_id": user_id,
                "connected_email": user_info.get("email"),
                "debug_mode": True,
                "redirect_url": settings.FRONTEND_SETTINGS_URL
            }
            
        except Exception as e:
            logger.error(f"Failed to connect Gmail for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to connect Gmail: {str(e)}")
    
    async def _handle_calendar_connect(self, user_id: str, tokens: Dict, user_info: Dict) -> Dict[str, Any]:
        """Handle Calendar connection - DEBUG VERSION WITHOUT ENCRYPTION."""
        try:
            # ⚠️ STORE TOKENS IN PLAIN TEXT (NO ENCRYPTION)
            plain_text_tokens = {
                "access_token": tokens["access_token"],  # ← NO encrypt_token() call
                "refresh_token": tokens.get("refresh_token", ""),  # ← NO encrypt_token() call
                "expires_at": (datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))).isoformat(),
                "scope": tokens.get("scope", ""),
                "connected_at": datetime.utcnow().isoformat(),
                "user_email": user_info.get("email"),
                "debug_mode": True  # ← Flag to indicate this is debug mode
            }
            
            logger.warning(f"🚨 STORING PLAIN TEXT TOKENS for user {user_id}")
            
            # Update user with plain text tokens
            await self.user_repository.update_user(user_id, {
                "calendar_tokens": plain_text_tokens,
                "google_profile": user_info,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Calendar connected successfully for user {user_id} (DEBUG MODE)")
            
            return {
                "success": True,
                "service": "calendar",
                "action": "calendar_connect",
                "user_id": user_id,
                "connected_email": user_info.get("email"),
                "debug_mode": True,
                "redirect_url": settings.FRONTEND_SETTINGS_URL
            }
            
        except Exception as e:
            logger.error(f"Failed to connect Calendar for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to connect Calendar: {str(e)}")
    
    # Authentication handlers remain the same (they don't store OAuth tokens)...
    
    async def get_valid_access_token(self, user_id: str, service: str) -> Optional[str]:
        """Get a valid access token - DEBUG VERSION WITHOUT DECRYPTION."""
        try:
            # Get current tokens
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                return None
            
            service_tokens = user.get(f"{service}_tokens")
            if not service_tokens:
                return None
            
            # Check if this is debug mode (plain text tokens)
            if service_tokens.get("debug_mode"):
                logger.info(f"🔍 Reading plain text token for {service}")
                
                # Check if token is expired
                expires_at_str = service_tokens.get("expires_at")
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    now = datetime.utcnow()
                    
                    if expires_at <= now + timedelta(minutes=5):
                        logger.info(f"{service} token expires soon, need refresh...")
                        # TODO: Implement refresh for debug mode
                        return None
                
                # Return plain text access token
                access_token = service_tokens.get("access_token")
                if access_token:
                    logger.info(f"✅ Retrieved plain text {service} token (length: {len(access_token)})")
                    return access_token
            else:
                logger.warning(f"⚠️ Found encrypted tokens, but running in debug mode!")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get valid access token for {service}: {str(e)}")
            return None
    
    # Helper methods remain the same...
    def _generate_state(self, user_id: Optional[str], purpose: str) -> str:
        """Generate OAuth state parameter."""
        random_part = secrets.token_urlsafe(16)
        user_part = user_id or "anonymous"
        return f"{user_part}:{purpose}:{random_part}"
    
    def _parse_state(self, state: str) -> Tuple[Optional[str], str]:
        """Parse OAuth state parameter."""
        try:
            parts = state.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid state format")
            
            user_id = parts[0] if parts[0] != "anonymous" else None
            purpose = parts[1]
            
            return user_id, purpose
            
        except Exception as e:
            raise OAuthError(f"Invalid OAuth state: {str(e)}")
    
    async def _exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": self.redirect_uri,
                    }
                )
                
                if response.status_code != 200:
                    raise OAuthError(f"Token exchange failed: {response.text}")
                
                return response.json()
                
        except httpx.RequestError as e:
            raise OAuthError(f"Token exchange request failed: {str(e)}")
    
    async def _get_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    raise OAuthError(f"Failed to get user info: {response.text}")
                
                return response.json()
                
        except httpx.RequestError as e:
            raise OAuthError(f"User info request failed: {str(e)}")

    # Add callback handling method...
    async def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and process based on state."""
        try:
            # Parse state to understand the purpose
            user_id, purpose = self._parse_state(state)
            
            # Exchange code for tokens
            tokens = await self._exchange_code_for_tokens(code)
            
            # Get user info from Google
            user_info = await self._get_google_user_info(tokens["access_token"])
            
            # Route to appropriate handler based on purpose
            if purpose == "gmail_connect":
                return await self._handle_gmail_connect(user_id, tokens, user_info)
            elif purpose == "calendar_connect":
                return await self._handle_calendar_connect(user_id, tokens, user_info)
            elif purpose == "google_login":
                return await self._handle_google_login(tokens, user_info)
            elif purpose == "google_signup":
                return await self._handle_google_signup(tokens, user_info)
            else:
                raise OAuthError(f"Unknown OAuth purpose: {purpose}")
                
        except Exception as e:
            logger.error(f"OAuth callback failed: {str(e)}")
            raise OAuthError(f"OAuth callback failed: {str(e)}")

    # Placeholder methods for login/signup (don't involve token storage)
    async def _handle_google_login(self, tokens: Dict, user_info: Dict) -> Dict[str, Any]:
        """Handle Google login for existing user."""
        # Implementation same as before...
        return {"success": True, "action": "login", "debug_mode": True}
    
    async def _handle_google_signup(self, tokens: Dict, user_info: Dict) -> Dict[str, Any]:
        """Handle Google signup for new user."""
        # Implementation same as before...
        return {"success": True, "action": "signup", "debug_mode": True}