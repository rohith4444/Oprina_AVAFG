"""
Enhanced authentication utilities for Oprina voice assistant.
Direct database access - eliminates circular dependency.
Supports both production (Supabase) and development (pickle file) modes.
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from supabase import create_client, Client
from oprina.services.logging.logger import setup_logger

# Paths - tokens stored in oprina/ directory (fallback for development)
OPRINA_DIR = Path(__file__).parent.parent  # tools/ -> oprina/
GMAIL_TOKEN_PATH = OPRINA_DIR / 'gmail_token.pickle'
CALENDAR_TOKEN_PATH = OPRINA_DIR / 'calendar_token.pickle'

# Setup logger
logger = setup_logger("auth_utils", console_output=True)

# Global database client for production mode
_db_client: Optional[Client] = None

def _get_database_client() -> Optional[Client]:
    """
    Get Supabase database client for production mode.
    
    Returns:
        Supabase client or None if not configured
    """
    global _db_client
    
    if _db_client is not None:
        return _db_client
    
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.debug("Supabase credentials not configured - using development mode")
            return None
        
        _db_client = create_client(supabase_url, supabase_key)
        logger.debug("Database client initialized for production mode")
        return _db_client
        
    except Exception as e:
        logger.error(f"Failed to initialize database client: {e}")
        return None

def _use_database() -> bool:
    """Simple check: use database if available, otherwise use pickle files."""
    return _get_database_client() is not None

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

def _decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt token using the same method as backend.
    Simple implementation - in production, tokens are stored encrypted.
    
    Args:
        encrypted_token: Encrypted token string
        
    Returns:
        Decrypted token
    """
    # Note: In your backend, tokens are encrypted with bcrypt/encryption utils
    # For now, this is a placeholder - you might need to import the decrypt function
    # from your backend or implement a simple version here
    
    # If tokens are stored as plain text in JSONB for simplicity, return as-is
    return encrypted_token

async def _get_user_tokens_from_db(user_id: str, service: str) -> Optional[Dict[str, Any]]:
    """
    Get OAuth tokens directly from database.
    
    Args:
        user_id: User identifier
        service: Service name ('gmail' or 'calendar')
        
    Returns:
        Token data dict or None
    """
    try:
        db_client = _get_database_client()
        if not db_client:
            logger.debug("Database client not available")
            return None
        
        # Query user tokens directly from database
        result = db_client.table("users").select(f"{service}_tokens").eq("id", user_id).execute()
        
        if not result.data:
            logger.debug(f"No user found for ID: {user_id}")
            return None
        
        user_data = result.data[0]
        tokens = user_data.get(f"{service}_tokens")
        
        if not tokens:
            logger.debug(f"No {service} tokens found for user {user_id}")
            return None
        
        # Check if tokens are expired
        if tokens.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(tokens["expires_at"].replace('Z', '+00:00'))
                if expires_at <= datetime.utcnow():
                    logger.warning(f"{service} tokens expired for user {user_id}")
                    return None
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid expires_at format: {e}")
        
        logger.info(f"Retrieved {service} tokens for user {user_id}")
        return tokens
        
    except Exception as e:
        logger.error(f"Error getting {service} tokens from database: {e}")
        return None

def _get_credentials_from_db_tokens(tokens: Dict[str, Any]) -> Optional[Credentials]:
    """
    Convert database token data to Google Credentials object.
    
    Args:
        tokens: Token data from database
        
    Returns:
        Google Credentials object or None
    """
    try:
        # Decrypt tokens (implement decryption if needed)
        access_token = _decrypt_token(tokens.get("access_token", ""))
        refresh_token = _decrypt_token(tokens.get("refresh_token", ""))
        
        if not access_token:
            logger.error("No access token in database tokens")
            return None
        
        # Create Google Credentials object
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            id_token=tokens.get("id_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=tokens.get("scope", "").split() if tokens.get("scope") else []
        )
        
        return credentials
        
    except Exception as e:
        logger.error(f"Error creating credentials from database tokens: {e}")
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

async def _get_credentials_for_service(service: str, user_id: Optional[str]) -> Optional[Credentials]:
    """
    Get credentials for a service - database first, then pickle fallback.
    
    Args:
        service: Service name ('gmail' or 'calendar')
        user_id: User identifier (None for development mode)
        
    Returns:
        Google Credentials object or None
    """
    # Try database first if available and we have a user_id
    if user_id and _use_database():
        logger.debug(f"Using database for {service} service")
        tokens = await _get_user_tokens_from_db(user_id, service)
        if tokens:
            credentials = _get_credentials_from_db_tokens(tokens)
            if credentials:
                return credentials
    
    # Fallback to pickle files
    logger.debug(f"Using pickle files for {service} service")
    return _get_credentials_from_pickle(service)

def get_gmail_service(tool_context=None):
    """
    Get Gmail service with multi-user support via direct database access.
    
    Args:
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        Gmail service object or None
    """
    try:
        # Extract user_id from context for production mode
        user_id = _extract_user_id_from_context(tool_context)
        
        # Get credentials using async call (wrap in sync for compatibility)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        credentials = loop.run_until_complete(_get_credentials_for_service('gmail', user_id))
        
        if not credentials:
            logger.warning("No Gmail authentication available")
            return None
        
        # Mark Gmail as connected in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state["gmail:connected"] = True
        
        # Refresh token if needed
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        
        logger.info(f"Gmail service created for user: {user_id or 'development'}")
        return build('gmail', 'v1', credentials=credentials)
        
    except Exception as e:
        logger.error(f"Error creating Gmail service: {e}")
        return None

def get_calendar_service(tool_context=None):
    """
    Get Calendar service with multi-user support via direct database access.
    
    Args:
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        Calendar service object or None
    """
    try:
        # Extract user_id from context for production mode
        user_id = _extract_user_id_from_context(tool_context)
        
        # Get credentials using async call (wrap in sync for compatibility)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        credentials = loop.run_until_complete(_get_credentials_for_service('calendar', user_id))
        
        if not credentials:
            logger.warning("No Calendar authentication available")
            return None
        
        # Mark Calendar as connected in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state["calendar:connected"] = True
        
        # Refresh token if needed
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        
        logger.info(f"Calendar service created for user: {user_id or 'development'}")
        return build('calendar', 'v3', credentials=credentials)
        
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

def get_user_connection_status(tool_context=None) -> Dict[str, bool]:
    """
    Get connection status for all services for the current user.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Dict with service connection status
    """
    return {
        "gmail": check_gmail_connection(tool_context),
        "calendar": check_calendar_connection(tool_context)
    }

# Export main functions
__all__ = [
    "get_gmail_service",
    "get_calendar_service", 
    "check_gmail_connection",
    "check_calendar_connection",
    "get_user_connection_status"
]