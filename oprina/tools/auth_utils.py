# oprina/tools/auth_utils.py
"""
Simplified authentication utilities - Database-only mode with session state.
Always uses lightweight token service for multi-user support.
Uses session state for reliable user ID extraction.
"""

import json, os
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from oprina.tools.token_service import get_token_service
from oprina.services.logging.logger import setup_logger

# Import session state constants
from oprina.common.session_keys import USER_ID

logger = setup_logger("auth_utils")

# Global services cache to avoid recreating
_user_services = {}


def extract_user_id_from_context(tool_context) -> Optional[str]:
    """
    Extract user_id from tool context session state using session key constants.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        user_id string or None
    """
    try:
        # PRIMARY: Check Vertex AI session.userId (this is where it actually stores it)
        if tool_context and hasattr(tool_context, 'session') and hasattr(tool_context.session, 'userId'):
            user_id = tool_context.session.userId  # ✅ Correct Vertex AI attribute
            print("Found user_id in session.userId: {user_id}")
            if user_id:
                logger.debug(f"Found user_id in session.userId: {user_id}")
                return user_id
        
        # FALLBACK 1: Check session state (using our USER_ID constant)
        if tool_context and hasattr(tool_context, 'state'):
            user_id = tool_context.state.get(USER_ID)
            if user_id:
                logger.debug(f"Found user_id in session state: {user_id}")
                return user_id
        
        # FALLBACK 2: Check session.user_id (alternative naming)
        if tool_context and hasattr(tool_context, 'session') and hasattr(tool_context.session, 'user_id'):
            user_id = tool_context.session.user_id  # ✅ Fixed: consistent naming
            if user_id:
                logger.debug(f"Found user_id in session.user_id: {user_id}")
                return user_id
        
        logger.warning("No user_id found in tool context - multi-user functionality disabled")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting user_id from context: {e}")
        return None

def get_oauth_credentials(user_id: str, service_type: str) -> Optional[Credentials]:
    """Get OAuth credentials for a user and service type."""
    try:
        logger.info(f"Getting {service_type} credentials for user: {user_id}")
        
        token_service = get_token_service()
        user_tokens = token_service.get_user_tokens(user_id)
        
        # Get the appropriate tokens
        if service_type == "gmail":
            encrypted_tokens = user_tokens.get("gmail_tokens")
        elif service_type == "calendar":
            encrypted_tokens = user_tokens.get("calendar_tokens")
        else:
            logger.error(f"Unknown service type: {service_type}")
            return None
        
        if not encrypted_tokens:
            logger.warning(f"No {service_type} tokens found for user {user_id}")
            return None
        
        # Decrypt tokens
        tokens = token_service.decrypt_tokens(encrypted_tokens)
        if not tokens:
            logger.error(f"Failed to decrypt {service_type} tokens for user {user_id}")
            return None
        
        # ✅ FIX: Get client credentials from environment if not in tokens
        client_id = tokens.get('client_id') or os.getenv('GOOGLE_CLIENT_ID')
        client_secret = tokens.get('client_secret') or os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logger.error(f"Missing OAuth client credentials for {service_type}")
            return None
        
        # Validate required token fields
        if not tokens.get('access_token') or not tokens.get('refresh_token'):
            logger.error(f"Missing access_token or refresh_token for {service_type}")
            return None
        
        # Create credentials object
        creds = Credentials(
            token=tokens.get('access_token'),
            refresh_token=tokens.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,  # ✅ Use environment fallback
            client_secret=client_secret,  # ✅ Use environment fallback
            scopes=['https://www.googleapis.com/auth/gmail.readonly',
                   'https://www.googleapis.com/auth/gmail.send',
                   'https://www.googleapis.com/auth/gmail.modify']
        )
        
        logger.info(f"Successfully loaded {service_type} credentials for user {user_id}")
        return creds
        
    except Exception as e:
        logger.error(f"Error loading {service_type} credentials for user {user_id}: {e}")
        return None

def get_gmail_service(tool_context=None, user_id: str = None):
    """Get Gmail service for a specific user."""
    
    # Determine user ID
    if not user_id:
        if tool_context:
            user_id = extract_user_id_from_context(tool_context)
            if not user_id:
                logger.error("No user_id found in tool context - cannot create Gmail service")
                return None
        else:
            logger.error("Either user_id or tool_context must be provided")
            return None
    
    logger.info(f"Creating Gmail service for user: {user_id}")
    
    # Check cache
    cache_key = f"gmail_{user_id}"
    if cache_key in _user_services:
        logger.debug(f"Using cached Gmail service for user {user_id}")
        return _user_services[cache_key]
    
    try:
        # Get credentials
        creds = get_oauth_credentials(user_id, "gmail")
        if not creds:
            logger.warning(f"No Gmail credentials available for user {user_id}")
            return None
        
        # Build service
        service = build('gmail', 'v1', credentials=creds)
        
        # Cache the service
        _user_services[cache_key] = service
        
        logger.info(f"Gmail service created successfully for user {user_id}")
        return service
        
    except Exception as e:
        logger.error(f"Error creating Gmail service for user {user_id}: {e}")
        return None


def get_calendar_service(tool_context=None, user_id: str = None):
    """Get Calendar service for a specific user."""
    
    # Determine user ID
    if not user_id:
        if tool_context:
            user_id = extract_user_id_from_context(tool_context)
            if not user_id:
                logger.error("No user_id found in tool context - cannot create Calendar service")
                return None
        else:
            logger.error("Either user_id or tool_context must be provided")
            return None
    
    logger.info(f"Creating Calendar service for user: {user_id}")
    
    # Check cache
    cache_key = f"calendar_{user_id}"
    if cache_key in _user_services:
        logger.debug(f"Using cached Calendar service for user {user_id}")
        return _user_services[cache_key]
    
    try:
        # Get credentials
        creds = get_oauth_credentials(user_id, "calendar")
        if not creds:
            logger.warning(f"No Calendar credentials available for user {user_id}")
            return None
        
        # Build service
        service = build('calendar', 'v3', credentials=creds)
        
        # Cache the service
        _user_services[cache_key] = service
        
        logger.info(f"Calendar service created successfully for user {user_id}")
        return service
        
    except Exception as e:
        logger.error(f"Error creating Calendar service for user {user_id}: {e}")
        return None


def clear_user_cache(user_id: str = None):
    """Clear cached services for a user or all users."""
    global _user_services
    
    if user_id:
        # Clear specific user's cache
        keys_to_remove = [key for key in _user_services.keys() if key.endswith(f"_{user_id}")]
        for key in keys_to_remove:
            del _user_services[key]
        logger.info(f"Cleared cache for user {user_id}")
    else:
        # Clear all cache
        _user_services.clear()
        logger.info("Cleared all user service cache")


def get_user_info(tool_context) -> Dict[str, Any]:
    """Get user information from context."""
    user_id = extract_user_id_from_context(tool_context)
    
    if not user_id:
        return {
            "error": "No user_id found in session context",
            "user_id": None,
            "has_gmail": False,
            "has_calendar": False
        }
    
    return {
        "user_id": user_id,
        "has_gmail": get_oauth_credentials(user_id, "gmail") is not None,
        "has_calendar": get_oauth_credentials(user_id, "calendar") is not None
    }


def test_user_authentication(user_id: str) -> Dict[str, Any]:
    """Test authentication for a specific user."""
    logger.info(f"Testing authentication for user: {user_id}")
    
    result = {
        "user_id": user_id,
        "gmail_service": False,
        "calendar_service": False,
        "errors": []
    }
    
    # Test Gmail service
    try:
        gmail_service = get_gmail_service(user_id=user_id)
        result["gmail_service"] = gmail_service is not None
        if gmail_service:
            logger.info(f"✅ Gmail service working for user {user_id}")
        else:
            logger.warning(f"❌ Gmail service not available for user {user_id}")
    except Exception as e:
        error_msg = f"Gmail service error: {e}"
        result["errors"].append(error_msg)
        logger.error(error_msg)
    
    # Test Calendar service
    try:
        calendar_service = get_calendar_service(user_id=user_id)
        result["calendar_service"] = calendar_service is not None
        if calendar_service:
            logger.info(f"✅ Calendar service working for user {user_id}")
        else:
            logger.warning(f"❌ Calendar service not available for user {user_id}")
    except Exception as e:
        error_msg = f"Calendar service error: {e}"
        result["errors"].append(error_msg)
        logger.error(error_msg)
    
    return result


def validate_user_context(tool_context) -> bool:
    """Validate that tool context has proper user information."""
    user_id = extract_user_id_from_context(tool_context)
    
    if not user_id:
        logger.error("Tool context validation failed: No user_id in session state")
        logger.debug("This indicates the session was not properly initialized with user context")
        return False
    
    logger.debug(f"Tool context validation passed for user: {user_id}")
    return True