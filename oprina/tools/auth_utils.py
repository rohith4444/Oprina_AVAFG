"""
Enhanced authentication utilities for Oprina voice assistant.
Supports both production (API-based) and development (pickle file) modes.
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from oprina.services.logging.logger import setup_logger
from oprina.services.token_client import token_client

# Paths - tokens stored in oprina/ directory (fallback for development)
OPRINA_DIR = Path(__file__).parent.parent  # tools/ -> oprina/
GMAIL_TOKEN_PATH = OPRINA_DIR / 'gmail_token.pickle'
CALENDAR_TOKEN_PATH = OPRINA_DIR / 'calendar_token.pickle'

# Setup logger
logger = setup_logger("auth_utils", console_output=True)

def _get_session_id_from_context(tool_context) -> Optional[str]:
    """
    Extract Vertex AI session ID from tool context.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Vertex AI session ID or None
    """
    try:
        # Try multiple ways to extract session ID from tool context
        if tool_context:
            # Method 1: Direct session.id attribute
            if hasattr(tool_context, 'session') and hasattr(tool_context.session, 'id'):
                session_id = tool_context.session.id
                if session_id:
                    logger.debug(f"Found session ID via session.id: {session_id}")
                    return session_id
            
            # Method 2: Session name attribute (sometimes contains session ID)
            if hasattr(tool_context, 'session') and hasattr(tool_context.session, 'name'):
                session_name = tool_context.session.name
                if session_name and 'sessions/' in session_name:
                    # Extract session ID from session name like "projects/.../sessions/SESSION_ID"
                    session_id = session_name.split('sessions/')[-1]
                    logger.debug(f"Found session ID via session.name: {session_id}")
                    return session_id
            
            # Method 3: Direct session_id attribute
            if hasattr(tool_context, 'session_id'):
                session_id = tool_context.session_id
                if session_id:
                    logger.debug(f"Found session ID via session_id: {session_id}")
                    return session_id
            
            # Method 4: Context metadata
            if hasattr(tool_context, 'metadata'):
                metadata = tool_context.metadata
                if isinstance(metadata, dict) and 'session_id' in metadata:
                    session_id = metadata['session_id']
                    logger.debug(f"Found session ID via metadata: {session_id}")
                    return session_id
        
        logger.debug("No session ID found in tool context")
        return None
        
    except Exception as e:
        logger.debug(f"Could not extract session ID: {e}")
        return None

def _get_credentials_from_api(service: str, vertex_session_id: str) -> Optional[Credentials]:
    """
    Get OAuth credentials from backend API for production.
    
    Args:
        service: Service name ('gmail' or 'calendar')
        vertex_session_id: Vertex AI session ID
        
    Returns:
        Google OAuth2 Credentials object or None
    """
    try:
        # Get token from backend API
        if service == "gmail":
            token_data = token_client.get_gmail_token(vertex_session_id)
        elif service == "calendar":
            token_data = token_client.get_calendar_token(vertex_session_id)
        else:
            logger.error(f"Unknown service: {service}")
            return None
        
        if not token_data or not token_client.validate_token(token_data):
            logger.info(f"No valid {service} token found for session {vertex_session_id}")
            return None
        
        # Create credentials object
        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=None,  # Backend handles refresh
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=[]  # Scopes are managed by backend
        )
        
        logger.info(f"Retrieved {service} credentials from API for session {vertex_session_id}")
        return creds
        
    except Exception as e:
        logger.error(f"Failed to get {service} credentials from API: {e}")
        return None

def _get_credentials_from_pickle(service: str) -> Optional[Credentials]:
    """
    Get OAuth credentials from pickle file (fallback for development).
    
    Args:
        service: Service name ('gmail' or 'calendar')
        
    Returns:
        Google OAuth2 Credentials object or None
    """
    token_path = GMAIL_TOKEN_PATH if service == 'gmail' else CALENDAR_TOKEN_PATH
    
    try:
        if not token_path.exists():
            logger.debug(f"{service} token file not found at {token_path}")
            return None
        
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh credentials if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed credentials
                    with open(token_path, 'wb') as token:
                        pickle.dump(creds, token)
                    logger.info(f"{service} credentials refreshed from pickle file")
                except Exception as refresh_error:
                    logger.error(f"Failed to refresh {service} credentials: {refresh_error}")
                    return None
            else:
                logger.error(f"{service} credentials expired and cannot be refreshed")
                return None
        
        logger.info(f"Retrieved {service} credentials from pickle file")
        return creds
        
    except Exception as e:
        logger.error(f"Error getting {service} credentials from pickle: {e}")
        return None

def get_gmail_service(tool_context=None) -> Optional[Any]:
    """
    Get authenticated Gmail service.
    Supports both production (API) and development (pickle) modes.
    
    Args:
        tool_context: ADK tool context (for production mode)
        
    Returns:
        Gmail service object or None if not authenticated
    """
    try:
        logger.debug("Attempting to get Gmail service")
        creds = None
        
        # Try production mode first (API-based) using tool_context
        if tool_context:
            vertex_session_id = _get_session_id_from_context(tool_context)
            if vertex_session_id:
                logger.debug(f"Using production mode for session {vertex_session_id}")
                creds = _get_credentials_from_api("gmail", vertex_session_id)
            else:
                logger.debug("No session ID found in tool_context")
        
        # Fallback to development mode (pickle file)
        if not creds:
            logger.debug("Using development mode (pickle file)")
            creds = _get_credentials_from_pickle("gmail")
        
        if not creds:
            logger.warning("No Gmail credentials available")
            return None
        
        # Create and return service
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service created successfully")
        return service
        
    except Exception as e:
        logger.error(f"Error getting Gmail service: {e}")
        return None

def get_calendar_service(tool_context=None) -> Optional[Any]:
    """
    Get authenticated Calendar service.
    Supports both production (API) and development (pickle) modes.
    
    Args:
        tool_context: ADK tool context (for production mode)
        
    Returns:
        Calendar service object or None if not authenticated
    """
    try:
        logger.debug("Attempting to get Calendar service")
        creds = None
        
        # Try production mode first (API-based) using tool_context
        if tool_context:
            vertex_session_id = _get_session_id_from_context(tool_context)
            if vertex_session_id:
                logger.debug(f"Using production mode for session {vertex_session_id}")
                creds = _get_credentials_from_api("calendar", vertex_session_id)
            else:
                logger.debug("No session ID found in tool_context")
        
        # Fallback to development mode (pickle file)
        if not creds:
            logger.debug("Using development mode (pickle file)")
            creds = _get_credentials_from_pickle("calendar")
        
        if not creds:
            logger.warning("No Calendar credentials available")
            return None
        
        # Create and return service
        service = build('calendar', 'v3', credentials=creds)
        logger.info("Calendar service created successfully")
        return service
        
    except Exception as e:
        logger.error(f"Error getting Calendar service: {e}")
        return None

def check_gmail_connection(tool_context=None) -> bool:
    """
    Check if Gmail is properly set up and accessible.
    
    Args:
        tool_context: ADK tool context (for production mode)
        
    Returns:
        True if Gmail service is available, False otherwise
    """
    logger.debug("Checking Gmail connection")
    service = get_gmail_service(tool_context)
    if not service:
        logger.warning("Gmail service not available")
        return False
    
    try:
        # Test connection by getting user profile
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress', 'unknown')
        logger.info(f"Gmail connection verified for {user_email}")
        return True
    except Exception as e:
        logger.error(f"Gmail connection test failed: {e}")
        return False

def check_calendar_connection(tool_context=None) -> bool:
    """
    Check if Calendar is properly set up and accessible.
    
    Args:
        tool_context: ADK tool context (for production mode)
        
    Returns:
        True if Calendar service is available, False otherwise
    """
    logger.debug("Checking Calendar connection")
    service = get_calendar_service(tool_context)
    if not service:
        logger.warning("Calendar service not available")
        return False
    
    try:
        # Test connection by listing calendars
        calendar_list = service.calendarList().list().execute()
        calendar_count = len(calendar_list.get('items', []))
        logger.info(f"Calendar connection verified with {calendar_count} calendars")
        return True
    except Exception as e:
        logger.error(f"Calendar connection test failed: {e}")
        return False

def get_user_connection_status(tool_context=None) -> dict:
    """
    Get connection status for all services for the current user.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Dict with service connection status
    """
    # Try production mode first (API-based) using tool_context
    if tool_context:
        vertex_session_id = _get_session_id_from_context(tool_context)
        if vertex_session_id:
            try:
                logger.debug(f"Getting connection status for session {vertex_session_id}")
                return token_client.get_connection_status(vertex_session_id)
            except Exception as e:
                logger.error(f"Failed to get connection status from API: {e}")
    
    # Fallback to development mode - check pickle files
    logger.debug("Using development mode for connection status")
    return {
        "gmail": check_gmail_connection(tool_context),
        "calendar": check_calendar_connection(tool_context)
    }

# Removed unreliable session context methods - now using tool_context approach

def is_development_mode() -> bool:
    """
    Check if we're running in development mode.
    
    Returns:
        True if development mode (pickle files), False if production mode (API)
    """
    # Check environment variable first
    env_mode = os.getenv('OPRINA_MODE', '').lower()
    if env_mode == 'development':
        return True
    elif env_mode == 'production':
        return False
    
    # Auto-detect based on available resources
    # Development mode: pickle files exist and no backend URL
    backend_url = os.getenv('BACKEND_API_URL')
    
    # If no backend URL configured, assume development
    if not backend_url:
        return True
    
    # If pickle files exist and backend is localhost, prefer development
    if (GMAIL_TOKEN_PATH.exists() or CALENDAR_TOKEN_PATH.exists()) and 'localhost' in backend_url:
        return True
    
    # Default to production if backend URL is configured
    return False

def get_development_user_context():
    """Get user context for development mode (pickle files)."""
    return {
        'user_id': 'development_user',
        'vertex_session_id': None,
        'mode': 'development'
    }

# Export main functions
__all__ = [
    "get_gmail_service",
    "get_calendar_service", 
    "check_gmail_connection",
    "check_calendar_connection",
    "get_user_connection_status"
]