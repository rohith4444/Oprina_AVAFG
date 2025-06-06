# oprina/services/google_cloud/calendar_auth.py
"""
Enhanced Google Calendar authentication and service management.
Based on ADK Voice Agent patterns for robust connection handling.
"""

import os
import pickle
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# FIXED: Import logging system
from oprina.services.logging.logger import setup_logger

# Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

# Credentials file paths (shared with Gmail)
OPRINA_DIR = Path(__file__).parent.parent.parent  # services/google_cloud -> services -> oprina
CREDENTIALS_FILE = OPRINA_DIR / 'credentials.json'
CALENDAR_TOKEN_FILE = OPRINA_DIR / 'calendar_token.pickle'
CALENDAR_TOKEN_INFO_FILE = OPRINA_DIR / 'calendar_token_info.json'

# Connection settings
CONNECTION_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3
TOKEN_REFRESH_THRESHOLD = timedelta(minutes=5)

# FIXED: Initialize logger
logger = setup_logger("calendar_auth", console_output=True)

class CalendarAuthManager:
    """Manages Calendar authentication and service connections."""
    
    def __init__(self):
        self._service = None
        self._credentials = None
        self._last_check = None
        self._connection_status = {"connected": False, "error": None}
        self._calendar_cache = {}
        
        # FIXED: Ensure directory exists for token storage
        try:
            OPRINA_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Calendar auth directory ready: {OPRINA_DIR}")
        except Exception as e:
            logger.error(f"Failed to create auth directory: {e}")
    
    def get_service(self, force_refresh: bool = False) -> Optional[Any]:
        """
        Get authenticated Calendar service with automatic token management.
        
        Args:
            force_refresh: Force credential refresh even if cached
            
        Returns:
            Calendar service object or None if authentication fails
        """
        try:
            # Check if we have a valid cached service
            if not force_refresh and self._service and self._is_service_valid():
                logger.debug("Using cached Calendar service")
                return self._service
            
            # Get or refresh credentials
            creds = self._get_valid_credentials(force_refresh)
            if not creds:
                logger.error("Failed to get valid credentials")
                return None
            
            # Create service
            self._service = build('calendar', 'v3', credentials=creds)
            self._credentials = creds
            self._connection_status = {"connected": True, "error": None}
            
            # Save token info for monitoring
            self._save_token_info(creds)
            
            logger.info("Calendar service created successfully")
            return self._service
            
        except Exception as e:
            error_msg = f"Failed to create Calendar service: {str(e)}"
            logger.error(error_msg)
            self._connection_status = {"connected": False, "error": error_msg}
            self._service = None
            return None
    
    def check_connection(self) -> Dict[str, Any]:
        """
        Check Calendar connection status with comprehensive validation.
        
        Returns:
            Dict with connection status and calendar information
        """
        try:
            service = self.get_service()
            if not service:
                error_msg = self._connection_status.get("error", "Failed to create service")
                logger.warning(f"Calendar connection check failed: {error_msg}")
                return {"connected": False, "error": error_msg}
            
            # Test connection by listing calendars
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            # Find primary calendar
            primary_calendar = next(
                (cal for cal in calendars if cal.get('primary')), 
                None
            )
            
            # Get calendar summaries
            calendar_summaries = []
            for cal in calendars[:10]:  # Limit to first 10
                calendar_summaries.append({
                    "id": cal.get('id'),
                    "summary": cal.get('summary', 'Unnamed Calendar'),
                    "primary": cal.get('primary', False),
                    "access_role": cal.get('accessRole', 'reader')
                })
            
            self._calendar_cache = {
                "calendars": calendar_summaries,
                "primary": primary_calendar,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            self._last_check = datetime.utcnow()
            
            connection_info = {
                "connected": True,
                "calendar_count": len(calendars),
                "primary_calendar": primary_calendar.get('summary', '') if primary_calendar else '',
                "calendars": [cal.get('summary', '') for cal in calendars[:5]],  # First 5 names
                "calendar_details": calendar_summaries,
                "last_check": self._last_check.isoformat(),
                "token_valid": self._is_token_valid(),
                "scopes": SCOPES
            }
            
            primary_name = primary_calendar.get('summary', 'Primary') if primary_calendar else 'None'
            logger.info(f"Calendar connection verified: {len(calendars)} calendars, Primary: {primary_name}")
            return connection_info
            
        except HttpError as e:
            error_msg = f"Calendar API error: {e.status_code} - {e.reason}"
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
        Perform Calendar authentication with enhanced error handling.
        
        Args:
            force_reauth: Force re-authentication even if tokens exist
            
        Returns:
            Dict with authentication result
        """
        try:
            logger.info(f"Starting Calendar authentication (force_reauth={force_reauth})")
            
            if force_reauth:
                logger.info("Clearing stored credentials for re-authentication")
                self._clear_stored_credentials()
            
            service = self.get_service(force_refresh=True)
            if service:
                connection_info = self.check_connection()
                if connection_info.get("connected"):
                    calendar_count = connection_info.get("calendar_count", 0)
                    primary_calendar = connection_info.get("primary_calendar", "")
                    
                    success_msg = f"Calendar authenticated successfully with {calendar_count} calendars"
                    logger.info(success_msg)
                    
                    return {
                        "success": True,
                        "message": success_msg,
                        "calendar_count": calendar_count,
                        "primary_calendar": primary_calendar,
                        "connection_info": connection_info
                    }
            
            error_msg = self._connection_status.get("error", "Authentication failed")
            logger.error(f"Calendar authentication failed: {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg, "error": error_msg}
    
    def get_cached_calendars(self) -> List[Dict[str, Any]]:
        """Get cached calendar information."""
        return self._calendar_cache.get("calendars", [])
    
    def get_primary_calendar(self) -> Optional[Dict[str, Any]]:
        """Get primary calendar information."""
        return self._calendar_cache.get("primary")
    
    def _get_valid_credentials(self, force_refresh: bool = False) -> Optional[Credentials]:
        """Get valid credentials with automatic refresh."""
        creds = None
        
        # Load existing token if not forcing refresh
        if not force_refresh and CALENDAR_TOKEN_FILE.exists():
            try:
                with open(CALENDAR_TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
                logger.debug("Loaded existing Calendar credentials")
            except Exception as e:
                logger.warning(f"Error loading Calendar token: {e}")
                creds = None
        
        # Check if credentials need refresh
        if creds and not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing Calendar credentials")
                    creds.refresh(Request())
                    logger.info("Calendar credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing Calendar token: {e}")
                    creds = None
            else:
                logger.warning("Calendar credentials invalid and cannot be refreshed")
                creds = None
        
        # Get new credentials if needed
        if not creds:
            logger.info("Getting new Calendar credentials")
            creds = self._get_new_credentials()
        
        # Save valid credentials
        if creds and creds.valid:
            self._save_credentials(creds)
        
        return creds
    
    def _get_new_credentials(self) -> Optional[Credentials]:
        """Get new credentials through OAuth flow."""
        if not CREDENTIALS_FILE.exists():
            error_msg = f"Calendar credentials file '{CREDENTIALS_FILE}' not found. Download from Google Cloud Console."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            logger.info("Starting Calendar OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("Calendar OAuth flow completed successfully")
            return creds
        except Exception as e:
            logger.error(f"Error in Calendar OAuth flow: {e}")
            return None
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to file."""
        try:
            # FIXED: Ensure directory exists before saving
            CALENDAR_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(CALENDAR_TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            logger.debug("Calendar credentials saved successfully")
        except Exception as e:
            logger.error(f"Error saving Calendar credentials: {e}")
    
    def _save_token_info(self, creds: Credentials):
        """Save token metadata for monitoring."""
        try:
            # FIXED: Ensure directory exists before saving
            CALENDAR_TOKEN_INFO_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            token_info = {
                "valid": creds.valid,
                "expired": creds.expired,
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
                "scopes": creds.scopes,
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(CALENDAR_TOKEN_INFO_FILE, 'w') as f:
                json.dump(token_info, f, indent=2)
            
            logger.debug("Calendar token info saved successfully")
                
        except Exception as e:
            logger.warning(f"Error saving Calendar token info: {e}")
    
    def _is_service_valid(self) -> bool:
        """Check if current service is still valid."""
        if not self._service or not self._credentials:
            return False
        
        # Check if credentials are still valid
        if not self._credentials.valid:
            logger.debug("Calendar credentials no longer valid")
            return False
        
        # Check if token is expiring soon
        if self._credentials.expiry:
            time_until_expiry = self._credentials.expiry - datetime.utcnow()
            if time_until_expiry < TOKEN_REFRESH_THRESHOLD:
                logger.debug("Calendar token expiring soon, will refresh")
                return False
        
        return True
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid."""
        if not self._credentials:
            return False
        return self._credentials.valid
    
    def _clear_stored_credentials(self):
        """Clear stored credentials for re-authentication."""
        for file_path in [CALENDAR_TOKEN_FILE, CALENDAR_TOKEN_INFO_FILE]:
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.debug(f"Removed {file_path}")
                except Exception as e:
                    logger.warning(f"Error removing {file_path}: {e}")
        
        self._service = None
        self._credentials = None
        self._connection_status = {"connected": False, "error": None}
        self._calendar_cache = {}
        logger.info("Calendar stored credentials cleared")

# Global instance
_calendar_auth_manager = CalendarAuthManager()

# Public API functions
def get_calendar_service(force_refresh: bool = False):
    """Get authenticated Calendar service."""
    return _calendar_auth_manager.get_service(force_refresh)

def check_calendar_connection() -> Dict[str, Any]:
    """Check Calendar connection status."""
    return _calendar_auth_manager.check_connection()

def authenticate_calendar(force_reauth: bool = False) -> Dict[str, Any]:
    """Authenticate with Calendar."""
    return _calendar_auth_manager.authenticate(force_reauth)

def get_calendar_auth_status() -> Dict[str, Any]:
    """Get current authentication status."""
    return {
        "has_service": _calendar_auth_manager._service is not None,
        "has_credentials": _calendar_auth_manager._credentials is not None,
        "connection_status": _calendar_auth_manager._connection_status.copy(),
        "last_check": _calendar_auth_manager._last_check.isoformat() if _calendar_auth_manager._last_check else None,
        "cached_calendars": len(_calendar_auth_manager._calendar_cache.get("calendars", [])),
        "token_files_exist": {
            "credentials": CREDENTIALS_FILE.exists(),
            "token": CALENDAR_TOKEN_FILE.exists(),
            "token_info": CALENDAR_TOKEN_INFO_FILE.exists()
        }
    }

def get_cached_calendars() -> List[Dict[str, Any]]:
    """Get cached calendar list."""
    return _calendar_auth_manager.get_cached_calendars()

def get_primary_calendar() -> Optional[Dict[str, Any]]:
    """Get primary calendar info."""
    return _calendar_auth_manager.get_primary_calendar()

# Export for compatibility
__all__ = [
    "get_calendar_service",
    "check_calendar_connection", 
    "authenticate_calendar",
    "get_calendar_auth_status",
    "get_cached_calendars",
    "get_primary_calendar"
]