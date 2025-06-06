# oprina/services/google_cloud/gmail_auth.py
"""
Enhanced Gmail authentication and service management.
Based on ADK Voice Agent patterns for robust connection handling.
"""

import os
import pickle
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# FIXED: Import logging system
from oprina.services.logging.logger import setup_logger

# Gmail API scopes - comprehensive permissions
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]

# Credentials file paths
OPRINA_DIR = Path(__file__).parent.parent.parent   # services/google_cloud -> services -> oprina
CREDENTIALS_FILE = OPRINA_DIR / 'credentials.json'

# Gmail-specific files
TOKEN_FILE = OPRINA_DIR / 'gmail_token.pickle'
TOKEN_INFO_FILE = OPRINA_DIR / 'gmail_token_info.json'

# Connection settings
CONNECTION_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
TOKEN_REFRESH_THRESHOLD = timedelta(minutes=5)

# FIXED: Initialize logger
logger = setup_logger("gmail_auth", console_output=True)

class GmailAuthManager:
    """Manages Gmail authentication and service connections."""
    
    def __init__(self):
        self._service = None
        self._credentials = None
        self._last_check = None
        self._connection_status = {"connected": False, "error": None}
        
        # FIXED: Ensure directory exists for token storage
        try:
            OPRINA_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Gmail auth directory ready: {OPRINA_DIR}")
        except Exception as e:
            logger.error(f"Failed to create auth directory: {e}")
    
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
                logger.debug("Using cached Gmail service")
                return self._service
            
            # Get or refresh credentials
            creds = self._get_valid_credentials(force_refresh)
            if not creds:
                logger.error("Failed to get valid credentials")
                return None
            
            # Create service
            self._service = build('gmail', 'v1', credentials=creds)
            self._credentials = creds
            self._connection_status = {"connected": True, "error": None}
            
            # Save token info for monitoring
            self._save_token_info(creds)
            
            logger.info("Gmail service created successfully")
            return self._service
            
        except Exception as e:
            error_msg = f"Failed to create Gmail service: {str(e)}"
            logger.error(error_msg)
            self._connection_status = {"connected": False, "error": error_msg}
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
                error_msg = self._connection_status.get("error", "Failed to create service")
                logger.warning(f"Gmail connection check failed: {error_msg}")
                return {"connected": False, "error": error_msg}
            
            # Test connection by getting profile
            profile = service.users().getProfile(userId='me').execute()
            
            # Get additional connection info
            user_email = profile.get('emailAddress', '')
            messages_total = profile.get('messagesTotal', 0)
            threads_total = profile.get('threadsTotal', 0)
            
            self._last_check = datetime.utcnow()
            
            connection_info = {
                "connected": True,
                "user_email": user_email,
                "messages_total": messages_total,
                "threads_total": threads_total,
                "last_check": self._last_check.isoformat(),
                "token_valid": self._is_token_valid(),
                "scopes": SCOPES
            }
            
            logger.info(f"Gmail connection verified for {user_email}")
            return connection_info
            
        except HttpError as e:
            error_msg = f"Gmail API error: {e.status_code} - {e.reason}"
            logger.error(error_msg)
            self._connection_status = {"connected": False, "error": error_msg}
            return {"connected": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
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
            logger.info(f"Starting Gmail authentication (force_reauth={force_reauth})")
            
            if force_reauth:
                logger.info("Clearing stored credentials for re-authentication")
                self._clear_stored_credentials()
            
            service = self.get_service(force_refresh=True)
            if service:
                connection_info = self.check_connection()
                if connection_info.get("connected"):
                    user_email = connection_info.get('user_email', 'user')
                    success_msg = f"Gmail authenticated successfully as {user_email}"
                    logger.info(success_msg)
                    
                    return {
                        "success": True,
                        "message": success_msg,
                        "user_email": user_email,
                        "connection_info": connection_info
                    }
            
            error_msg = self._connection_status.get("error", "Authentication failed")
            logger.error(f"Gmail authentication failed: {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg, "error": error_msg}
    
    def _get_valid_credentials(self, force_refresh: bool = False) -> Optional[Credentials]:
        """Get valid credentials with automatic refresh."""
        creds = None
        
        # Load existing token if not forcing refresh
        if not force_refresh and TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
                logger.debug("Loaded existing Gmail credentials")
            except Exception as e:
                logger.warning(f"Error loading Gmail token: {e}")
                creds = None
        
        # Check if credentials need refresh
        if creds and not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing Gmail credentials")
                    creds.refresh(Request())
                    logger.info("Gmail credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing Gmail token: {e}")
                    creds = None
            else:
                logger.warning("Gmail credentials invalid and cannot be refreshed")
                creds = None
        
        # Get new credentials if needed
        if not creds:
            logger.info("Getting new Gmail credentials")
            creds = self._get_new_credentials()
        
        # Save valid credentials
        if creds and creds.valid:
            self._save_credentials(creds)
        
        return creds
    
    def _get_new_credentials(self) -> Optional[Credentials]:
        """Get new credentials through OAuth flow."""
        if not CREDENTIALS_FILE.exists():
            error_msg = f"Gmail credentials file '{CREDENTIALS_FILE}' not found. Download from Google Cloud Console."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            logger.info("Starting Gmail OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("Gmail OAuth flow completed successfully")
            return creds
        except Exception as e:
            logger.error(f"Error in Gmail OAuth flow: {e}")
            return None
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to file."""
        try:
            # FIXED: Ensure directory exists before saving
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            logger.debug("Gmail credentials saved successfully")
        except Exception as e:
            logger.error(f"Error saving Gmail credentials: {e}")
    
    def _save_token_info(self, creds: Credentials):
        """Save token metadata for monitoring."""
        try:
            # FIXED: Ensure directory exists before saving
            TOKEN_INFO_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            token_info = {
                "valid": creds.valid,
                "expired": creds.expired,
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
                "scopes": creds.scopes,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(TOKEN_INFO_FILE, 'w') as f:
                json.dump(token_info, f, indent=2)
            
            logger.debug("Gmail token info saved successfully")
                
        except Exception as e:
            logger.warning(f"Error saving Gmail token info: {e}")
    
    def _is_service_valid(self) -> bool:
        """Check if current service is still valid."""
        if not self._service or not self._credentials:
            return False
        
        # Check if credentials are still valid
        if not self._credentials.valid:
            logger.debug("Gmail credentials no longer valid")
            return False
        
        # Check if token is expiring soon
        if self._credentials.expiry:
            time_until_expiry = self._credentials.expiry - datetime.utcnow()
            if time_until_expiry < TOKEN_REFRESH_THRESHOLD:
                logger.debug("Gmail token expiring soon, will refresh")
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
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.debug(f"Removed {file_path}")
                except Exception as e:
                    logger.warning(f"Error removing {file_path}: {e}")
        
        self._service = None
        self._credentials = None
        self._connection_status = {"connected": False, "error": None}
        logger.info("Gmail stored credentials cleared")

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
            "credentials": CREDENTIALS_FILE.exists(),
            "token": TOKEN_FILE.exists(),
            "token_info": TOKEN_INFO_FILE.exists()
        }
    }

# Export for compatibility
__all__ = [
    "get_gmail_service",
    "check_gmail_connection", 
    "authenticate_gmail",
    "get_gmail_auth_status"
]