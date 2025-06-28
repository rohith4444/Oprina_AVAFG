"""
Simple Google OAuth service for Oprina API.

Handles all 4 OAuth use cases:
1. Connect Gmail (settings)
2. Connect Calendar (settings) 
3. Google Login (auth)
4. Google Signup (auth)
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
from app.utils.encryption import encrypt_token, decrypt_token

logger = get_logger(__name__)
settings = get_settings()


class GoogleOAuthService:
    """Simple Google OAuth service for all Oprina OAuth needs."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        if not self.client_id or not self.client_secret:
            raise OAuthError("Google OAuth not configured - missing client credentials")
    
    # =============================================================================
    # AUTHORIZATION URL GENERATION
    # =============================================================================
    
    def get_gmail_connect_url(self, user_id: str) -> Tuple[str, str]:
        """Get OAuth URL for connecting Gmail."""
        state = self._generate_state(user_id, "gmail_connect")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": settings.GOOGLE_GMAIL_SCOPES,
            "response_type": "code",
            "access_type": "offline",  # Get refresh token
            "prompt": "consent",       # Force consent screen for refresh token
            "state": state
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url, state
    
    def get_calendar_connect_url(self, user_id: str) -> Tuple[str, str]:
        """Get OAuth URL for connecting Calendar."""
        state = self._generate_state(user_id, "calendar_connect")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": settings.GOOGLE_CALENDAR_SCOPES,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url, state
    
    def get_google_login_url(self) -> Tuple[str, str]:
        """Get OAuth URL for Google login."""
        state = self._generate_state(None, "google_login")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": settings.GOOGLE_AUTH_SCOPES,
            "response_type": "code",
            "access_type": "offline",
            "state": state
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url, state
    
    def get_google_signup_url(self) -> Tuple[str, str]:
        """Get OAuth URL for Google signup."""
        state = self._generate_state(None, "google_signup")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": settings.GOOGLE_AUTH_SCOPES,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return auth_url, state
    
    # =============================================================================
    # CALLBACK HANDLING
    # =============================================================================
    
    async def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and process based on state."""
        try:
            logger.info(f"🔄 Starting OAuth callback processing...")
            logger.info(f"📝 State received: {state}")
            
            # Parse state to understand the purpose
            logger.info(f"🔍 Parsing OAuth state...")
            user_id, purpose = self._parse_state(state)
            logger.info(f"✅ State parsed - User ID: {user_id}, Purpose: {purpose}")
            
            # Exchange code for tokens
            logger.info(f"🔄 Exchanging authorization code for tokens...")
            tokens = await self._exchange_code_for_tokens(code)
            logger.info(f"✅ Tokens received - Access token: {'✅' if tokens.get('access_token') else '❌'}, Refresh token: {'✅' if tokens.get('refresh_token') else '❌'}")
            
            # Get user info from Google
            logger.info(f"🔄 Getting user info from Google...")
            user_info = await self._get_google_user_info(tokens["access_token"])
            logger.info(f"✅ User info received - Email: {user_info.get('email')}, Name: {user_info.get('name')}")
            
            # Route to appropriate handler based on purpose
            logger.info(f"🔄 Routing to handler for purpose: {purpose}")
            if purpose == "gmail_connect":
                result = await self._handle_gmail_connect(user_id, tokens, user_info)
            elif purpose == "calendar_connect":
                result = await self._handle_calendar_connect(user_id, tokens, user_info)
            elif purpose == "google_login":
                result = await self._handle_google_login(tokens, user_info)
            elif purpose == "google_signup":
                result = await self._handle_google_signup(tokens, user_info)
            else:
                raise OAuthError(f"Unknown OAuth purpose: {purpose}")
            
            logger.info(f"✅ OAuth callback completed successfully: {result.get('action')}")
            return result
                
        except Exception as e:
            logger.error(f"❌ OAuth callback failed at step: {str(e)}", exc_info=True)
            raise OAuthError(f"OAuth callback failed: {str(e)}")
    
    # =============================================================================
    # SERVICE CONNECTION HANDLERS
    # =============================================================================
    
    async def _handle_gmail_connect(self, user_id: str, tokens: Dict, user_info: Dict) -> Dict[str, Any]:
        """Handle Gmail connection for existing user."""
        try:
            # Encrypt and store Gmail tokens
            encrypted_tokens = {
                "access_token": encrypt_token(tokens["access_token"]),
                "refresh_token": encrypt_token(tokens.get("refresh_token", "")),
                "expires_at": (datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))).isoformat(),
                "scope": tokens.get("scope", ""),
                "connected_at": datetime.utcnow().isoformat(),
                "user_email": user_info.get("email")
            }
            
            # Update user with Gmail tokens
            await self.user_repository.update_user(user_id, {
                "gmail_tokens": encrypted_tokens,
                "google_profile": user_info,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Gmail connected successfully for user {user_id}")
            
            return {
                "success": True,
                "service": "gmail",
                "action": "gmail_connect",
                "user_id": user_id,
                "connected_email": user_info.get("email"),
                "redirect_url": settings.FRONTEND_SETTINGS_URL
            }
            
        except Exception as e:
            logger.error(f"Failed to connect Gmail for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to connect Gmail: {str(e)}")
    
    async def _handle_calendar_connect(self, user_id: str, tokens: Dict, user_info: Dict) -> Dict[str, Any]:
        """Handle Calendar connection for existing user."""
        try:
            # Encrypt and store Calendar tokens
            encrypted_tokens = {
                "access_token": encrypt_token(tokens["access_token"]),
                "refresh_token": encrypt_token(tokens.get("refresh_token", "")),
                "expires_at": (datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))).isoformat(),
                "scope": tokens.get("scope", ""),
                "connected_at": datetime.utcnow().isoformat(),
                "user_email": user_info.get("email")
            }
            
            # Update user with Calendar tokens
            await self.user_repository.update_user(user_id, {
                "calendar_tokens": encrypted_tokens,
                "google_profile": user_info,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Calendar connected successfully for user {user_id}")
            
            return {
                "success": True,
                "service": "calendar",
                "action": "calendar_connect",
                "user_id": user_id,
                "connected_email": user_info.get("email"),
                "redirect_url": settings.FRONTEND_SETTINGS_URL
            }
            
        except Exception as e:
            logger.error(f"Failed to connect Calendar for user {user_id}: {str(e)}")
            raise OAuthError(f"Failed to connect Calendar: {str(e)}")
    
    # =============================================================================
    # AUTHENTICATION HANDLERS
    # =============================================================================
    
    async def _handle_google_login(self, tokens: Dict, user_info: Dict) -> Dict[str, Any]:
        """Handle Google login for existing user."""
        try:
            google_user_id = user_info.get("id")
            email = user_info.get("email")
            
            if not google_user_id or not email:
                raise OAuthError("Invalid Google user information")
            
            # Find existing user by Google ID or email
            user = await self.user_repository.get_user_by_email(email)
            
            if not user:
                raise OAuthError("User not found. Please sign up first.")
            
            # Update user with Google profile and last login
            await self.user_repository.update_user(user["id"], {
                "google_user_id": google_user_id,
                "google_profile": user_info,
                "last_login_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Google login successful for user {user['id']}")
            
            return {
                "success": True,
                "action": "login",
                "user": user,
                "google_profile": user_info,
                "redirect_url": settings.FRONTEND_DASHBOARD_URL
            }
            
        except Exception as e:
            logger.error(f"Google login failed: {str(e)}")
            raise OAuthError(f"Google login failed: {str(e)}")
    
    async def _handle_google_signup(self, tokens: Dict, user_info: Dict) -> Dict[str, Any]:
        """Handle Google signup for new user."""
        try:
            google_user_id = user_info.get("id")
            email = user_info.get("email")
            name = user_info.get("name", "")
            
            if not google_user_id or not email:
                raise OAuthError("Invalid Google user information")
            
            # Check if user already exists
            existing_user = await self.user_repository.get_user_by_email(email)
            if existing_user:
                raise OAuthError("User already exists. Please log in instead.")
            
            # Create new user with Google information
            user_data = {
                "email": email,
                "full_name": name,
                "preferred_name": user_info.get("given_name", name.split()[0] if name else ""),
                "avatar_url": user_info.get("picture"),
                "google_user_id": google_user_id,
                "google_profile": user_info,
                "is_verified": True,  # Google emails are verified
                "created_at": datetime.utcnow().isoformat(),
                "last_login_at": datetime.utcnow().isoformat()
            }
            
            # Create user (no password needed for Google signup)
            new_user = await self.user_repository.create_user(user_data)
            
            logger.info(f"Google signup successful for new user {new_user['id']}")
            
            return {
                "success": True,
                "action": "signup",
                "user": new_user,
                "google_profile": user_info,
                "redirect_url": settings.FRONTEND_DASHBOARD_URL
            }
            
        except Exception as e:
            logger.error(f"Google signup failed: {str(e)}")
            raise OAuthError(f"Google signup failed: {str(e)}")
    
    # =============================================================================
    # TOKEN MANAGEMENT
    # =============================================================================
    
    async def disconnect_service(self, user_id: str, service: str) -> Dict[str, Any]:
        """Disconnect a service (Gmail or Calendar)."""
        try:
            if service not in ["gmail", "calendar"]:
                raise ValidationError("Service must be 'gmail' or 'calendar'")
            
            # Get current user to verify they exist
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise ValidationError("User not found")
            
            # Log current state
            current_tokens = user.get(f"{service}_tokens")
            logger.info(f"🔄 Disconnecting {service} for user {user_id}")
            logger.debug(f"Current {service}_tokens exists: {bool(current_tokens)}")
            
            # Clear service tokens - use empty dict instead of None
            update_data = {
                f"{service}_tokens": {},  # ← Use empty dict instead of None
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.user_repository.update_user(user_id, update_data)
            
            # Verify the disconnect worked
            updated_user = await self.user_repository.get_user_by_id(user_id)
            updated_tokens = updated_user.get(f"{service}_tokens")
            
            logger.info(f"✅ {service.title()} disconnected for user {user_id}")
            logger.debug(f"After disconnect - {service}_tokens: {updated_tokens}")
            
            return {
                "success": True,
                "service": service,
                "action": "disconnect",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to disconnect {service} for user {user_id}: {str(e)}")
            raise

    async def get_service_connection_status(self, user_id: str) -> Dict[str, Any]:
        """Get connection status for Gmail and Calendar."""
        try:
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise ValidationError("User not found")
            
            # Get tokens safely
            gmail_tokens = user.get("gmail_tokens") or {}
            calendar_tokens = user.get("calendar_tokens") or {}
            
            # Check if tokens exist and have access token
            gmail_connected = bool(gmail_tokens and gmail_tokens.get("access_token"))
            calendar_connected = bool(calendar_tokens and calendar_tokens.get("access_token"))
            
            # Check if tokens are expired (only if connected)
            if gmail_connected and gmail_tokens.get("expires_at"):
                try:
                    expires_at = datetime.fromisoformat(gmail_tokens["expires_at"])
                    gmail_connected = expires_at > datetime.utcnow()
                except (ValueError, TypeError):
                    gmail_connected = False
            
            if calendar_connected and calendar_tokens.get("expires_at"):
                try:
                    expires_at = datetime.fromisoformat(calendar_tokens["expires_at"])
                    calendar_connected = expires_at > datetime.utcnow()
                except (ValueError, TypeError):
                    calendar_connected = False
            
            logger.debug(f"Status check - Gmail: {gmail_connected}, Calendar: {calendar_connected}")
            
            return {
                "gmail": {
                    "connected": gmail_connected,
                    "email": gmail_tokens.get("user_email") if gmail_connected else None
                },
                "calendar": {
                    "connected": calendar_connected,
                    "email": calendar_tokens.get("user_email") if calendar_connected else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection status for user {user_id}: {str(e)}")
            raise
        
    # =============================================================================
    # PRIVATE HELPER METHODS
    # =============================================================================
    
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
        
    # Add these methods to GoogleOAuthService class

    async def refresh_access_token(self, user_id: str, service: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using the refresh token.
        
        Args:
            user_id: User identifier
            service: Service name ('gmail' or 'calendar')
            
        Returns:
            New token data
        """
        try:
            # Get current tokens from database
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                raise OAuthError("User not found")
            
            # Get the service tokens
            service_tokens = user.get(f"{service}_tokens")
            if not service_tokens:
                raise OAuthError(f"No {service} tokens found for user")
            
            # Get encrypted refresh token
            encrypted_refresh_token = service_tokens.get("refresh_token")
            if not encrypted_refresh_token:
                raise OAuthError(f"No refresh token found for {service}")
            
            # Decrypt refresh token
            refresh_token = decrypt_token(encrypted_refresh_token)
            
            # Call Google to refresh the token
            new_tokens = await self._refresh_token_with_google(refresh_token)
            
            # Update tokens in database
            updated_tokens = {
                **service_tokens,  # Keep existing data
                "access_token": encrypt_token(new_tokens["access_token"]),
                "expires_at": (datetime.utcnow() + timedelta(seconds=new_tokens.get("expires_in", 3600))).isoformat(),
                "refreshed_at": datetime.utcnow().isoformat()
            }
            
            # If Google gives us a new refresh token, update it
            if "refresh_token" in new_tokens:
                updated_tokens["refresh_token"] = encrypt_token(new_tokens["refresh_token"])
            
            # Save to database
            await self.user_repository.update_user(user_id, {
                f"{service}_tokens": updated_tokens,
                "updated_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Successfully refreshed {service} token for user {user_id}")
            
            return {
                "success": True,
                "service": service,
                "new_expires_at": updated_tokens["expires_at"],
                "access_token": new_tokens["access_token"]  # Return unencrypted for immediate use
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh {service} token for user {user_id}: {str(e)}")
            raise OAuthError(f"Token refresh failed: {str(e)}")


    async def _refresh_token_with_google(self, refresh_token: str) -> Dict[str, Any]:
        """Call Google's token refresh endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code != 200:
                    raise OAuthError(f"Token refresh failed: {response.text}")
                
                return response.json()
                
        except httpx.RequestError as e:
            raise OAuthError(f"Token refresh request failed: {str(e)}")


    async def get_valid_access_token(self, user_id: str, service: str) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        This is the main method other services should call.
        """
        try:
            # Get current tokens
            user = await self.user_repository.get_user_by_id(user_id)
            if not user:
                return None
            
            service_tokens = user.get(f"{service}_tokens")
            if not service_tokens:
                return None
            
            # Check if token is expired
            expires_at_str = service_tokens.get("expires_at")
            if not expires_at_str:
                # No expiry info, assume expired
                logger.warning(f"No expiry info for {service} token, attempting refresh")
                refresh_result = await self.refresh_access_token(user_id, service)
                return refresh_result["access_token"]
            
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.utcnow()
            
            # Add 5 minute buffer (refresh 5 minutes before expiry)
            if expires_at <= now + timedelta(minutes=5):
                logger.info(f"{service} token expires soon, refreshing...")
                refresh_result = await self.refresh_access_token(user_id, service)
                return refresh_result["access_token"]
            
            # Token is still valid, return it
            encrypted_access_token = service_tokens.get("access_token")
            if encrypted_access_token:
                return decrypt_token(encrypted_access_token)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get valid access token for {service}: {str(e)}")
            return None


    async def check_and_refresh_expired_tokens(self, user_id: str) -> Dict[str, Any]:
        """
        Check all tokens for a user and refresh any that are expired.
        This can be called periodically or on-demand.
        """
        results = {
            "gmail": {"checked": False, "refreshed": False, "error": None},
            "calendar": {"checked": False, "refreshed": False, "error": None}
        }
        
        for service in ["gmail", "calendar"]:
            try:
                results[service]["checked"] = True
                
                # Try to get valid token (this will refresh if needed)
                token = await self.get_valid_access_token(user_id, service)
                
                if token:
                    results[service]["refreshed"] = True
                    logger.info(f"Successfully ensured valid {service} token for user {user_id}")
                else:
                    logger.warning(f"No {service} token available for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Error checking {service} token for user {user_id}: {str(e)}")
                results[service]["error"] = str(e)
        
        return results