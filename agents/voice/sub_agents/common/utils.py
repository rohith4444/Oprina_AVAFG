"""
Simple utility functions used across agents.
No ADK abstractions - just basic helpers.
"""

from datetime import datetime
from typing import Dict, Any, Optional

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
    """Extract user info from ADK session for logging purposes."""
    if not tool_context or not hasattr(tool_context, 'session'):
        return {"user_id": "unknown", "session_id": "unknown"}
    
    state = tool_context.session.state
    return {
        "user_id": state.get("user:id", "unknown"),
        "session_id": getattr(tool_context.session, 'id', 'unknown'),
        "user_name": state.get("user:name", ""),
        "user_email": state.get("user:email", "")
    }