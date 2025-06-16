"""
Production authentication utilities for Oprina voice assistant.
Direct database access for multi-user OAuth token management.
Eliminates circular dependency - agent connects directly to database.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from supabase import create_client, Client
from oprina.services.logging.logger import setup_logger

# Import session key constants
from oprina.common.session_keys import USER_ID

# Setup logger
logger = setup_logger("auth_utils", console_output=True)

# Global database client
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
            logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured for production")
            return None
        
        _db_client = create_client(supabase_url, supabase_key)
        logger.debug("Database client initialized for production mode")
        return _db_client
        
    except Exception as e:
        logger.error(f"Failed to initialize database client: {e}")
        return None

def _extract_user_id_from_context(tool_context) -> Optional[str]:
    """
    Extract user_id from tool context session state using session key constants.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        user_id string or None
    """
    try:
        if tool_context and hasattr(tool_context, 'state'):
            # Use USER_ID constant from session_keys
            user_id = tool_context.state.get(USER_ID)
            if user_id:
                logger.debug(f"Found user_id in session state: {user_id}")
                return user_id
        
        # Fallback: Try session.user_id (ADK built-in)
        if tool_context and hasattr(tool_context, 'session'):
            if hasattr(tool_context.session, 'user_id'):
                user_id = tool_context.session.user_id
                logger.debug(f"Found user_id in session.user_id: {user_id}")
                return user_id
        
        logger.warning("No user_id found in tool context - multi-user functionality disabled")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting user_id from context: {e}")
        return None

def _get_user_tokens_from_db(user_id: str, service: str) -> Optional[Dict[str, Any]]:
    """
    Get OAuth tokens directly from database JSONB columns.
    
    Args:
        user_id: User identifier
        service: Service name ('gmail' or 'calendar')
        
    Returns:
        Token data dict or None
    """
    try:
        db_client = _get_database_client()
        if not db_client:
            logger.error("Database client not available")
            return None
        
        # Query user tokens directly from JSONB columns
        column_name = f"{service}_tokens"
        result = db_client.table("users").select(column_name).eq("id", user_id).execute()
        
        if not result.data:
            logger.warning(f"No user found for ID: {user_id}")
            return None
        
        user_data = result.data[0]
        tokens = user_data.get(column_name)
        
        if not tokens:
            logger.warning(f"No {service} tokens found for user {user_id}")
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

def _decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt token - placeholder for actual decryption.
    
    Args:
        encrypted_token: Encrypted token string
        
    Returns:
        Decrypted token
    """
    # TODO: Implement actual decryption if tokens are encrypted in database
    # For now, assume tokens are stored as plain text in JSONB
    return encrypted_token

def _get_credentials_from_db_tokens(tokens: Dict[str, Any]) -> Optional[Credentials]:
    """
    Convert database token data to Google Credentials object.
    
    Args:
        tokens: Token data from database
        
    Returns:
        Google Credentials object or None
    """
    try:
        # Decrypt tokens if needed
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

def get_gmail_service(tool_context=None) -> Optional[Any]:
    """
    Get Gmail service with multi-user support via direct database access.
    
    Args:
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        Gmail service object or None if not authenticated
    """
    try:
        # Extract user_id from context for multi-user support
        user_id = _extract_user_id_from_context(tool_context)
        
        if not user_id:
            logger.error("No user_id found - cannot retrieve Gmail tokens for multi-user system")
            return None
        
        # Get tokens from database
        tokens = _get_user_tokens_from_db(user_id, 'gmail')
        if not tokens:
            logger.warning(f"No Gmail tokens available for user {user_id}")
            return None
        
        # Convert to Google Credentials
        credentials = _get_credentials_from_db_tokens(tokens)
        if not credentials:
            logger.error(f"Failed to create Gmail credentials for user {user_id}")
            return None
        
        # Mark Gmail as connected in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state["gmail:connected"] = True
        
        # Refresh token if needed
        if credentials.expired and credentials.refresh_token:
            try:
                logger.info(f"Refreshing Gmail credentials for user {user_id}")
                credentials.refresh(Request())
            except Exception as refresh_error:
                logger.error(f"Failed to refresh Gmail credentials for user {user_id}: {refresh_error}")
                return None
        
        # Create and return service
        service = build('gmail', 'v1', credentials=credentials)
        logger.info(f"Gmail service created successfully for user {user_id}")
        return service
        
    except Exception as e:
        logger.error(f"Error creating Gmail service: {e}")
        return None

def get_calendar_service(tool_context=None) -> Optional[Any]:
    """
    Get Calendar service with multi-user support via direct database access.
    
    Args:
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        Calendar service object or None if not authenticated
    """
    try:
        # Extract user_id from context for multi-user support
        user_id = _extract_user_id_from_context(tool_context)
        
        if not user_id:
            logger.error("No user_id found - cannot retrieve Calendar tokens for multi-user system")
            return None
        
        # Get tokens from database
        tokens = _get_user_tokens_from_db(user_id, 'calendar')
        if not tokens:
            logger.warning(f"No Calendar tokens available for user {user_id}")
            return None
        
        # Convert to Google Credentials
        credentials = _get_credentials_from_db_tokens(tokens)
        if not credentials:
            logger.error(f"Failed to create Calendar credentials for user {user_id}")
            return None
        
        # Mark Calendar as connected in session state
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state["calendar:connected"] = True
        
        # Refresh token if needed
        if credentials.expired and credentials.refresh_token:
            try:
                logger.info(f"Refreshing Calendar credentials for user {user_id}")
                credentials.refresh(Request())
            except Exception as refresh_error:
                logger.error(f"Failed to refresh Calendar credentials for user {user_id}: {refresh_error}")
                return None
        
        # Create and return service
        service = build('calendar', 'v3', credentials=credentials)
        logger.info(f"Calendar service created successfully for user {user_id}")
        return service
        
    except Exception as e:
        logger.error(f"Error creating Calendar service: {e}")
        return None

def check_gmail_connection(tool_context=None) -> bool:
    """
    Check if Gmail is properly set up and accessible.
    
    Args:
        tool_context: ADK tool context (for multi-user mode)
        
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
        tool_context: ADK tool context (for multi-user mode)
        
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

# Export main functions
__all__ = [
    "get_gmail_service",
    "get_calendar_service", 
    "check_gmail_connection",
    "check_calendar_connection"
]