"""
Enhanced authentication utilities for Oprina voice assistant.
Supports both production (API-based) and development (pickle file) modes.
"""

import os
import pickle, requests
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
    
def _extract_user_id_from_context(tool_context) -> Optional[str]:
    """
    Extract user_id from tool context session state.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        user_id string or None
    """
    try:
        if tool_context and hasattr(tool_context, 'state'):
            # Method 1: From session state (our preferred method)
            user_id = tool_context.state.get("user:id")
            if user_id:
                logger.debug(f"Found user_id in session state: {user_id}")
                return user_id
        
        # Method 2: Try session.user_id (ADK built-in)
        if tool_context and hasattr(tool_context, 'session'):
            if hasattr(tool_context.session, 'user_id'):
                user_id = tool_context.session.user_id
                logger.debug(f"Found user_id in session.user_id: {user_id}")
                return user_id
        
        logger.debug("No user_id found in tool context")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting user_id from context: {e}")
        return None

def _get_credentials_from_api(service: str, user_id: str) -> Optional[Credentials]:
    """
    Get OAuth credentials from backend API using user_id.
    
    Args:
        service: Service name (gmail, calendar)
        user_id: User identifier
        
    Returns:
        Google Credentials object or None
    """
    try:
        backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        api_key = os.getenv("INTERNAL_API_KEY")
        
        if not backend_url or not api_key:
            logger.error("Backend API URL or API key not configured")
            return None
        
        # Call your existing backend API endpoint
        url = f"{backend_url}/api/v1/internal/tokens/{service}/{user_id}"
        headers = {
            "X-Internal-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Getting {service} token for user {user_id} from {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Create Google Credentials object
            credentials = Credentials(
                token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                id_token=token_data.get("id_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes", [])
            )
            
            logger.info(f"Successfully retrieved {service} credentials for user {user_id}")
            return credentials
            
        elif response.status_code == 404:
            logger.info(f"No {service} token found for user {user_id}")
            return None
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Network error accessing token API: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting credentials from API: {e}")
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

def get_gmail_service(tool_context=None):
    """
    Get Gmail service with multi-user support via session state.
    
    Args:
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        Gmail service object or None
    """
    try:
        # Method 1: Try to get user_id from session state
        user_id = _extract_user_id_from_context(tool_context)
        
        if user_id:
            logger.info(f"Getting Gmail service for user: {user_id}")
            credentials = _get_credentials_from_api('gmail', user_id)
            
            if credentials:
                # Mark Gmail as connected in session state
                if tool_context and hasattr(tool_context, 'state'):
                    tool_context.state["gmail:connected"] = True
                
                # Refresh token if needed
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                
                return build('gmail', 'v1', credentials=credentials)
        
        # Method 2: Fallback to pickle files (development mode)
        logger.info("Falling back to pickle file authentication")
        credentials = _get_credentials_from_pickle('gmail')
        
        if credentials:
            return build('gmail', 'v1', credentials=credentials)
        
        logger.warning("No Gmail authentication available")
        return None
        
    except Exception as e:
        logger.error(f"Error creating Gmail service: {e}")
        return None

def get_calendar_service(tool_context=None):
    """
    Get Calendar service with multi-user support via session state.
    
    Args:
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        Calendar service object or None
    """
    try:
        # Method 1: Try to get user_id from session state
        user_id = _extract_user_id_from_context(tool_context)
        
        if user_id:
            logger.info(f"Getting Calendar service for user: {user_id}")
            credentials = _get_credentials_from_api('calendar', user_id)
            
            if credentials:
                # Mark Calendar as connected in session state
                if tool_context and hasattr(tool_context, 'state'):
                    tool_context.state["calendar:connected"] = True
                
                # Refresh token if needed
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                
                return build('calendar', 'v3', credentials=credentials)
        
        # Method 2: Fallback to pickle files (development mode)
        logger.info("Falling back to pickle file authentication")
        credentials = _get_credentials_from_pickle('calendar')
        
        if credentials:
            return build('calendar', 'v3', credentials=credentials)
        
        logger.warning("No Calendar authentication available")
        return None
        
    except Exception as e:
        logger.error(f"Error creating Calendar service: {e}")
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