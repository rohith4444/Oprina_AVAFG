"""
Enhanced utility functions for ADK integration across all agents.
No ADK abstractions - just improved helpers with proper ADK support.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging

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
    """Extract comprehensive user info from ADK session."""
    if not tool_context or not hasattr(tool_context, 'session'):
        return {
            "user_id": "unknown", 
            "session_id": "unknown",
            "error": "No tool context or session available"
        }
    
    state = tool_context.session.state
    return {
        # Core identification
        "user_id": state.get("user:id", "unknown"),
        "session_id": getattr(tool_context.session, 'id', 'unknown'),
        "invocation_id": getattr(tool_context, 'invocation_id', 'unknown'),
        
        # User information
        "user_name": state.get("user:name", ""),
        "user_email": state.get("user:email", ""),
        
        # Connection status
        "gmail_connected": state.get("user:gmail_connected", False),
        "calendar_connected": state.get("user:calendar_connected", False),
        
        # User preferences
        "preferences": state.get("user:preferences", {}),
        
        # Session metadata
        "conversation_active": state.get("conversation_active", False),
        "last_agent_used": state.get("last_agent_used", ""),
        "app_version": state.get("app:version", "unknown")
    }

# =============================================================================
# NEW ADK-Specific Utility Functions
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
    
    # Ensure session state is initialized
    if not tool_context.session.state:
        tool_context.session.state = {}
        logger.warning(f"{function_name}: Initialized empty session state")
    
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
        
        # Update user's last activity timestamp
        tool_context.session.state["user:last_activity"] = format_timestamp()
        
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
    
    return tool_context.session.state.get("user:preferences", default_prefs or {})

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
        current_prefs = tool_context.session.state.get("user:preferences", {})
        current_prefs.update(preferences)
        tool_context.session.state["user:preferences"] = current_prefs
        tool_context.session.state["user:preferences_updated"] = format_timestamp()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        return False

def get_service_connection_status(tool_context, service_name: str) -> Dict[str, Any]:
    """
    Get connection status for a specific service (gmail, calendar, etc.).
    
    Args:
        tool_context: ADK tool context
        service_name: Service name ('gmail', 'calendar', etc.)
        
    Returns:
        Dict with connection status information
    """
    if not validate_tool_context(tool_context, "get_service_connection_status"):
        return {"connected": False, "error": "No tool context"}
    
    state = tool_context.session.state
    
    return {
        "connected": state.get(f"user:{service_name}_connected", False),
        "user_email": state.get("user:email", ""),
        "last_activity": state.get(f"{service_name}:last_activity_time", ""),
        "last_check": state.get(f"{service_name}:last_connection_check", "")
    }

def update_service_connection_status(tool_context, service_name: str, connected: bool, 
                                   user_email: str = "", additional_info: Dict[str, Any] = None) -> bool:
    """
    Update connection status for a service.
    
    Args:
        tool_context: ADK tool context
        service_name: Service name ('gmail', 'calendar', etc.)
        connected: Whether service is connected
        user_email: User's email for this service
        additional_info: Additional service-specific information
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not validate_tool_context(tool_context, "update_service_connection_status"):
        return False
    
    try:
        # Update connection status
        tool_context.session.state[f"user:{service_name}_connected"] = connected
        tool_context.session.state[f"{service_name}:last_connection_check"] = format_timestamp()
        
        # Update user email if provided
        if user_email:
            tool_context.session.state["user:email"] = user_email
        
        # Update additional service-specific info
        if additional_info:
            for key, value in additional_info.items():
                tool_context.session.state[f"{service_name}:{key}"] = value
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update {service_name} connection status: {e}")
        return False

def get_session_summary(tool_context) -> Dict[str, Any]:
    """
    Get a comprehensive summary of the current session state.
    Useful for debugging and monitoring.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Dict with session summary
    """
    if not validate_tool_context(tool_context, "get_session_summary"):
        return {"error": "No valid tool context"}
    
    state = tool_context.session.state
    
    # Count state keys by prefix
    prefixes = {"user": 0, "email": 0, "calendar": 0, "content": 0, "app": 0, "temp": 0, "other": 0}
    
    for key in state.keys():
        if ":" in key:
            prefix = key.split(":")[0]
            if prefix in prefixes:
                prefixes[prefix] += 1
            else:
                prefixes["other"] += 1
        else:
            prefixes["other"] += 1
    
    return {
        "session_id": getattr(tool_context.session, 'id', 'unknown'),
        "user_id": state.get("user:id", "unknown"),
        "conversation_active": state.get("conversation_active", False),
        "last_agent_used": state.get("last_agent_used", ""),
        "service_connections": {
            "gmail": state.get("user:gmail_connected", False),
            "calendar": state.get("user:calendar_connected", False)
        },
        "state_key_counts": prefixes,
        "total_state_keys": len(state),
        "last_activity": state.get("user:last_activity", "")
    }

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