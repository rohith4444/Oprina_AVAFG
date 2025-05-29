# agents/voice/sub_agents/common/__init__.py
"""
Common utilities for Oprina agents.
Simple helpers and constants - no complex abstractions.
"""

# Import session keys for easy access
from .session_keys import *

# Import utilities
from .utils import (
    format_timestamp,
    safe_get_nested_value,
    truncate_string,
    extract_user_info_from_session
)

__all__ = [
    # Session keys (all constants from session_keys.py)
    "USER_ID", "USER_NAME", "USER_EMAIL", "USER_GMAIL_CONNECTED",
    "USER_CALENDAR_CONNECTED", "USER_PREFERENCES", "USER_LAST_ACTIVITY",
    "EMAIL_CURRENT", "EMAIL_LAST_FETCH", "EMAIL_UNREAD_COUNT", "EMAIL_LAST_SENT",
    "CALENDAR_CURRENT", "CALENDAR_LAST_FETCH", "CALENDAR_UPCOMING_COUNT",
    "CONVERSATION_ACTIVE", "CURRENT_TASK", "LAST_AGENT_USED",
    "APP_VERSION", "APP_FEATURES",
    "TEMP_PROCESSING", "TEMP_CURRENT_OPERATION", "TEMP_WORKFLOW_STEP",
    
    # Utilities
    "format_timestamp",
    "safe_get_nested_value", 
    "truncate_string",
    "extract_user_info_from_session"
]