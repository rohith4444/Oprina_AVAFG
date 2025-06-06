# services/google_cloud/gmail_auth.py
"""
Enhanced Gmail authentication and service management.
Based on ADK Voice Agent patterns for robust connection handling.
"""

import os
import pickle
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes - comprehensive permissions
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]

# Credentials file paths
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'gmail_token.pickle'
TOKEN_INFO_FILE = 'gmail_token_info.json'

# Connection settings
CONNECTION_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
TOKEN_REFRESH_THRESHOLD = timedelta(minutes=5)

class GmailAuthManager:
    """Manages Gmail authentication and service connections."""
    
    def __init__(self):
        self._service = None
        self._credentials = None
        self._last_check = None
        self._connection_status = {"connected": False, "error": None}
    
    def get_service(self, force_refresh: bool = False) -> Optional[Any]:
        """
        Get authenticated Gmail service with automatic token management.
        
        Args:
            force_refresh: Force credential refresh even if cached
            
        Returns:
            Gmail service object or None if authentication fails
        """
        try:
            # Check if we have a valid cached service
            if not force_refresh and self._service and self._is_service_valid():
                return self._service
            
            # Get or refresh credentials
            creds = self._get_valid_credentials(force_refresh)
            if not creds:
                return None
            
            # Create service
            self._service = build('gmail', 'v1', credentials=creds)
            self._credentials = creds
            self._connection_status = {"connected": True, "error": None}
            
            # Save token info for monitoring
            self._save_token_info(creds)
            
            return self._service
            
        except Exception as e:
            self._connection_status = {"connected": False, "error": str(e)}
            self._service = None
            return None
    
    def check_connection(self) -> Dict[str, Any]:
        """
        Check Gmail connection status with comprehensive validation.
        
        Returns:
            Dict with connection status and user information
        """
        try:
            service = self.get_service()
            if not service:
                return {
                    "connected": False, 
                    "error": self._connection_status.get("error", "Failed to create service")
                }
            
            # Test connection by getting profile
            profile = service.users().getProfile(userId='me').execute()
            
            # Get additional connection info
            user_email = profile.get('emailAddress', '')
            messages_total = profile.get('messagesTotal', 0)
            threads_total = profile.get('threadsTotal', 0)
            
            self._last_check = datetime.utcnow()
            
            return {
                "connected": True,
                "user_email": user_email,
                "messages_total": messages_total,
                "threads_total": threads_total,
                "last_check": self._last_check.isoformat(),
                "token_valid": self._is_token_valid(),
                "scopes": SCOPES
            }
            
        except HttpError as e:
            error_msg = f"Gmail API error: {e.status_code} - {e.reason}"
            self._connection_status = {"connected": False, "error": error_msg}
            return {"connected": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            self._connection_status = {"connected": False, "error": error_msg}
            return {"connected": False, "error": error_msg}
    
    def authenticate(self, force_reauth: bool = False) -> Dict[str, Any]:
        """
        Perform Gmail authentication with enhanced error handling.
        
        Args:
            force_reauth: Force re-authentication even if tokens exist
            
        Returns:
            Dict with authentication result
        """
        try:
            if force_reauth:
                self._clear_stored_credentials()
            
            service = self.get_service(force_refresh=True)
            if service:
                connection_info = self.check_connection()
                if connection_info.get("connected"):
                    return {
                        "success": True,
                        "message": f"Gmail authenticated successfully as {connection_info.get('user_email', 'user')}",
                        "user_email": connection_info.get("user_email"),
                        "connection_info": connection_info
                    }
            
            return {
                "success": False,
                "message": self._connection_status.get("error", "Authentication failed"),
                "error": self._connection_status.get("error")
            }
            
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            return {"success": False, "message": error_msg, "error": error_msg}
    
    def _get_valid_credentials(self, force_refresh: bool = False) -> Optional[Credentials]:
        """Get valid credentials with automatic refresh."""
        creds = None
        
        # Load existing token if not forcing refresh
        if not force_refresh and os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"Error loading token: {e}")
                creds = None
        
        # Check if credentials need refresh
        if creds and not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    creds = None
            else:
                creds = None
        
        # Get new credentials if needed
        if not creds:
            creds = self._get_new_credentials()
        
        # Save valid credentials
        if creds and creds.valid:
            self._save_credentials(creds)
        
        return creds
    
    def _get_new_credentials(self) -> Optional[Credentials]:
        """Get new credentials through OAuth flow."""
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(
                f"Gmail credentials file '{CREDENTIALS_FILE}' not found. "
                "Download from Google Cloud Console."
            )
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            return creds
        except Exception as e:
            print(f"Error in OAuth flow: {e}")
            return None
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to file."""
        try:
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"Error saving credentials: {e}")
    
    def _save_token_info(self, creds: Credentials):
        """Save token metadata for monitoring."""
        try:
            token_info = {
                "valid": creds.valid,
                "expired": creds.expired,
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
                "scopes": creds.scopes,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(TOKEN_INFO_FILE, 'w') as f:
                json.dump(token_info, f, indent=2)
                
        except Exception as e:
            print(f"Error saving token info: {e}")
    
    def _is_service_valid(self) -> bool:
        """Check if current service is still valid."""
        if not self._service or not self._credentials:
            return False
        
        # Check if credentials are still valid
        if not self._credentials.valid:
            return False
        
        # Check if token is expiring soon
        if self._credentials.expiry:
            time_until_expiry = self._credentials.expiry - datetime.utcnow()
            if time_until_expiry < TOKEN_REFRESH_THRESHOLD:
                return False
        
        return True
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid."""
        if not self._credentials:
            return False
        return self._credentials.valid
    
    def _clear_stored_credentials(self):
        """Clear stored credentials for re-authentication."""
        for file_path in [TOKEN_FILE, TOKEN_INFO_FILE]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
        
        self._service = None
        self._credentials = None
        self._connection_status = {"connected": False, "error": None}

# Global instance
_gmail_auth_manager = GmailAuthManager()

# Public API functions
def get_gmail_service(force_refresh: bool = False):
    """Get authenticated Gmail service."""
    return _gmail_auth_manager.get_service(force_refresh)

def check_gmail_connection() -> Dict[str, Any]:
    """Check Gmail connection status."""
    return _gmail_auth_manager.check_connection()

def authenticate_gmail(force_reauth: bool = False) -> Dict[str, Any]:
    """Authenticate with Gmail."""
    return _gmail_auth_manager.authenticate(force_reauth)

def get_gmail_auth_status() -> Dict[str, Any]:
    """Get current authentication status."""
    return {
        "has_service": _gmail_auth_manager._service is not None,
        "has_credentials": _gmail_auth_manager._credentials is not None,
        "connection_status": _gmail_auth_manager._connection_status.copy(),
        "last_check": _gmail_auth_manager._last_check.isoformat() if _gmail_auth_manager._last_check else None,
        "token_files_exist": {
            "credentials": os.path.exists(CREDENTIALS_FILE),
            "token": os.path.exists(TOKEN_FILE),
            "token_info": os.path.exists(TOKEN_INFO_FILE)
        }
    }

# Export for compatibility
__all__ = [
    "get_gmail_service",
    "check_gmail_connection", 
    "authenticate_gmail",
    "get_gmail_auth_status"
]