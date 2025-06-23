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
    Extract user_id from ADK tool context.
    ADK stores user_id when stream_query(user_id=...) is called.
    """
    try:
        logger.info("🔍 DEBUGGING: Starting user_id extraction")
        
        if not tool_context:
            logger.error("🔍 No tool_context provided")
            return None
        
        # Log the entire tool_context structure for debugging
        logger.info(f"🔍 tool_context type: {type(tool_context)}")
        logger.info(f"🔍 tool_context attributes: {[attr for attr in dir(tool_context) if not attr.startswith('_')]}")
        
        # Method 1: Check ADK invocation context (where stream_query params are stored)
        if hasattr(tool_context, '_invocation_context'):
            invocation_context = tool_context._invocation_context
            logger.info(f"🔍 invocation_context type: {type(invocation_context)}")
            logger.info(f"🔍 invocation_context attributes: {[attr for attr in dir(invocation_context) if not attr.startswith('_')]}")
            
            # Try to get user_id from invocation context
            if hasattr(invocation_context, 'user_id'):
                user_id = invocation_context.user_id
                logger.info(f"🔍 Found user_id in invocation_context: {user_id}")
                if user_id:
                    return str(user_id)
            
            # Try userId (alternative naming)
            if hasattr(invocation_context, 'userId'):
                user_id = invocation_context.userId
                logger.info(f"🔍 Found userId in invocation_context: {user_id}")
                if user_id:
                    return str(user_id)
        
        # Method 2: Check tool_context.state (YOUR MISSING METHOD 1)
        if tool_context and hasattr(tool_context, 'state'):
            logger.info(f"🔍 state type: {type(tool_context.state)}")
            logger.info(f"🔍 state attributes: {[attr for attr in dir(tool_context.state) if not attr.startswith('_')]}")
            
            # Try to get from state as dict
            if hasattr(tool_context.state, 'get'):
                user_id = tool_context.state.get(USER_ID)
                if user_id:
                    logger.info(f"🔍 Found user_id in state.get(USER_ID): {user_id}")
                    return str(user_id)
                    
                # Try other key formats
                for key in ['user_id', 'userId', 'user:id']:
                    user_id = tool_context.state.get(key)
                    if user_id:
                        logger.info(f"🔍 Found user_id in state.get({key}): {user_id}")
                        return str(user_id)
            
            # Try state as object with attributes
            if hasattr(tool_context.state, 'user_id'):
                user_id = tool_context.state.user_id
                logger.info(f"🔍 Found user_id in state.user_id: {user_id}")
                if user_id:
                    return str(user_id)
                    
            if hasattr(tool_context.state, 'userId'):
                user_id = tool_context.state.userId
                logger.info(f"🔍 Found userId in state.userId: {user_id}")
                if user_id:
                    return str(user_id)
        
        # Method 3: Check direct attributes on tool_context
        if hasattr(tool_context, 'user_id'):
            user_id = tool_context.user_id
            logger.info(f"🔍 Found user_id on tool_context: {user_id}")
            if user_id:
                return str(user_id)
                
        if hasattr(tool_context, 'userId'):
            user_id = tool_context.userId
            logger.info(f"🔍 Found userId on tool_context: {user_id}")
            if user_id:
                return str(user_id)
        
        # Method 4: Try to access session through ADK session management
        # Since there's no direct session attribute, let's check user_content
        if hasattr(tool_context, 'user_content'):
            logger.info(f"🔍 user_content type: {type(tool_context.user_content)}")
            logger.info(f"🔍 user_content: {tool_context.user_content}")
        
        # Method 5: YOUR MISSING METHOD 2 - Modified for ADK structure
        # ADK doesn't have tool_context.session, but we'll check for session data
        if hasattr(tool_context, '_state') and hasattr(tool_context._state, 'user_id'):
            user_id = tool_context._state.user_id
            logger.info(f"🔍 Found user_id in _state.user_id: {user_id}")
            if user_id:
                return str(user_id)
        
        # Method 6: Last resort - check all attributes for anything containing user
        logger.info("🔍 Checking all attributes for user-related data:")
        for attr_name in dir(tool_context):
            if not attr_name.startswith('__'):
                try:
                    attr_value = getattr(tool_context, attr_name)
                    if 'user' in str(attr_name).lower() or 'user' in str(attr_value).lower():
                        logger.info(f"🔍 Found user-related attribute {attr_name}: {attr_value}")
                except Exception:
                    pass
        
        logger.warning("🔍 No user_id found in any location")
        return None
        
    except Exception as e:
        logger.error(f"🔍 Error extracting user_id: {e}")
        import traceback
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
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
            # 🔍 ADD DEBUG HERE:
            debug_result = debug_user_tokens(user_id)
            logger.error(f"🔍 DEBUG: {debug_result}")
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

def debug_user_tokens(user_id: str) -> str:
    """Debug function to check token availability."""
    try:
        logger.info(f"🔍 DEBUGGING: Checking tokens for user {user_id}")
        
        token_service = get_token_service()
        user_tokens = token_service.get_user_tokens(user_id)
        
        gmail_tokens = user_tokens.get('gmail_tokens')
        logger.info(f"🔍 Gmail tokens present: {gmail_tokens is not None}")
        
        if gmail_tokens:
            tokens = token_service.decrypt_tokens(gmail_tokens)
            logger.info(f"🔍 Decrypted tokens: {tokens is not None}")
            
            if tokens:
                has_access = 'access_token' in tokens
                has_refresh = 'refresh_token' in tokens
                has_client_id = 'client_id' in tokens
                has_client_secret = 'client_secret' in tokens
                
                logger.info(f"🔍 Token fields - access: {has_access}, refresh: {has_refresh}, client_id: {has_client_id}, client_secret: {has_client_secret}")
                
                return f"User {user_id}: Gmail tokens found, access: {has_access}, refresh: {has_refresh}, client_id: {has_client_id}, client_secret: {has_client_secret}"
        
        return f"User {user_id}: No Gmail tokens found"
        
    except Exception as e:
        logger.error(f"🔍 Debug failed: {e}")
        return f"Debug failed: {e}"