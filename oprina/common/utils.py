"""
Enhanced utility functions for ADK integration across all agents.
Cleaned up version with auth-related functions removed and proper session key usage.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Import session key constants
from oprina.common.session_keys import (
    USER_ID, USER_NAME, USER_EMAIL, USER_PREFERENCES, USER_LAST_ACTIVITY
)

# Configure logger
logger = logging.getLogger(__name__)

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO string."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()

def safe_get_nested_value(data: Dict[str, Any], keys: list, default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    try:
        value = data
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_user_info_from_session(tool_context) -> Dict[str, Any]:
    """Extract comprehensive user info from ADK session using session key constants."""
    if not tool_context or not hasattr(tool_context, 'session'):
        return {
            "user_id": "unknown", 
            "session_id": "unknown",
            "error": "No tool context or session available"
        }
    
    state = tool_context.session.state
    return {
        # Core identification - using session key constants
        "user_id": state.get(USER_ID, "unknown"),
        "session_id": getattr(tool_context.session, 'id', 'unknown'),
        "invocation_id": getattr(tool_context, 'invocation_id', 'unknown'),
        
        # User information - using session key constants
        "user_name": state.get(USER_NAME, ""),
        "user_email": state.get(USER_EMAIL, ""),
        
        # User preferences - using session key constants
        "preferences": state.get(USER_PREFERENCES, {}),
        
        # Session metadata
        "conversation_active": state.get("conversation_active", False),
        "last_agent_used": state.get("last_agent_used", ""),
        "app_version": state.get("app:version", "unknown"),
        
        # Last activity - using session key constants
        "last_activity": state.get(USER_LAST_ACTIVITY, "")
    }

# =============================================================================
# ADK-Specific Utility Functions
# =============================================================================

def validate_tool_context(tool_context, function_name: str = "unknown") -> bool:
    """
    Validate that tool_context is properly provided by ADK.
    
    Args:
        tool_context: ADK tool context (should be automatically provided)
        function_name: Name of calling function for error logging
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not tool_context:
        logger.error(f"{function_name}: No tool context provided by ADK")
        return False
    
    if not hasattr(tool_context, 'session'):
        logger.error(f"{function_name}: Tool context missing session")
        return False
    
    if not hasattr(tool_context.session, 'state'):
        logger.error(f"{function_name}: Session missing state")
        return False
    
    return True

def update_agent_activity(tool_context, agent_name: str, activity: str) -> bool:
    """
    Update session state with agent activity tracking.
    
    Args:
        tool_context: ADK tool context
        agent_name: Name of the agent (e.g., 'email_agent')
        activity: Description of activity (e.g., 'listing_messages')
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not validate_tool_context(tool_context, "update_agent_activity"):
        return False
    
    try:
        # Update last agent used
        tool_context.session.state["last_agent_used"] = agent_name
        
        # Update agent-specific activity (remove '_agent' suffix for cleaner keys)
        service_name = agent_name.replace('_agent', '')
        tool_context.session.state[f"{service_name}:last_activity"] = activity
        tool_context.session.state[f"{service_name}:last_activity_time"] = format_timestamp()
        
        # Update user's last activity timestamp using session key constant
        tool_context.session.state[USER_LAST_ACTIVITY] = format_timestamp()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update agent activity: {e}")
        return False

def get_user_preferences(tool_context, default_prefs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get user preferences from session state with defaults.
    
    Args:
        tool_context: ADK tool context
        default_prefs: Default preferences if none exist
        
    Returns:
        Dict containing user preferences
    """
    if not validate_tool_context(tool_context, "get_user_preferences"):
        return default_prefs or {}
    
    # Use session key constant
    return tool_context.session.state.get(USER_PREFERENCES, default_prefs or {})

def update_user_preferences(tool_context, preferences: Dict[str, Any]) -> bool:
    """
    Update user preferences in session state.
    
    Args:
        tool_context: ADK tool context
        preferences: Dictionary of preferences to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not validate_tool_context(tool_context, "update_user_preferences"):
        return False
    
    try:
        # Use session key constant
        current_prefs = tool_context.session.state.get(USER_PREFERENCES, {})
        current_prefs.update(preferences)
        tool_context.session.state[USER_PREFERENCES] = current_prefs
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        return False

def log_tool_execution(tool_context, tool_name: str, operation: str, 
                      success: bool, details: str = "") -> None:
    """
    Log tool execution for debugging and monitoring.
    
    Args:
        tool_context: ADK tool context
        tool_name: Name of the tool being executed
        operation: Type of operation being performed
        success: Whether the operation was successful
        details: Additional details about the operation
    """
    if not validate_tool_context(tool_context, "log_tool_execution"):
        return
    
    user_info = extract_user_info_from_session(tool_context)
    
    log_data = {
        "tool": tool_name,
        "operation": operation,
        "success": success,
        "user_id": user_info.get("user_id", "unknown"),
        "session_id": user_info.get("session_id", "unknown"),
        "timestamp": format_timestamp(),
        "details": details
    }
    
    if success:
        logger.info(f"Tool execution successful: {tool_name}.{operation}")
    else:
        logger.warning(f"Tool execution failed: {tool_name}.{operation} - {details}")
    
    # Store execution log in temporary session state for debugging
    execution_logs = tool_context.session.state.get("temp:tool_execution_log", [])
    execution_logs.append(log_data)
    
    # Keep only last 10 executions to avoid memory bloat
    if len(execution_logs) > 10:
        execution_logs = execution_logs[-10:]
    
    tool_context.session.state["temp:tool_execution_log"] = execution_logs