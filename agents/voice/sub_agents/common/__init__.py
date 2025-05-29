# agents/voice/sub_agents/common/__init__.py
"""
Common utilities for Oprina agents.
Enhanced with ADK-specific helpers and session management utilities.
"""

# Import session keys for easy access
from .session_keys import *

# Import utilities (original + new ADK utilities)
from .utils import (
    # Original utilities
    format_timestamp,
    safe_get_nested_value,
    truncate_string,
    extract_user_info_from_session,
    
    # NEW ADK-specific utilities
    validate_tool_context,
    update_agent_activity,
    get_user_preferences,
    update_user_preferences,
    get_service_connection_status,
    update_service_connection_status,
    get_session_summary,
    log_tool_execution
)

__all__ = [
    # Session keys (all constants from session_keys.py)
    "USER_ID", "USER_NAME", "USER_EMAIL", "USER_GMAIL_CONNECTED",
    "USER_CALENDAR_CONNECTED", "USER_PREFERENCES", "USER_LAST_ACTIVITY",
    "EMAIL_CURRENT_RESULTS", "EMAIL_LAST_FETCH", "EMAIL_LAST_QUERY", "EMAIL_RESULTS_COUNT",
    "EMAIL_LAST_SENT", "EMAIL_LAST_SENT_TO", "EMAIL_CONNECTION_STATUS",
    "CALENDAR_CURRENT_EVENTS", "CALENDAR_LAST_FETCH", "CALENDAR_UPCOMING_COUNT",
    "CALENDAR_LAST_EVENT_CREATED",
    "CONTENT_LAST_SUMMARY", "CONTENT_LAST_ANALYSIS", "CONTENT_PROCESSING_STATUS",
    "CONVERSATION_ACTIVE", "CURRENT_TASK", "LAST_AGENT_USED", "CURRENT_WORKFLOW",
    "APP_VERSION", "APP_FEATURES", "APP_NAME",
    "TEMP_PROCESSING", "TEMP_CURRENT_OPERATION", "TEMP_WORKFLOW_STEP", "TEMP_ERROR_STATE",
    
    # Original utilities
    "format_timestamp",
    "safe_get_nested_value", 
    "truncate_string",
    "extract_user_info_from_session",
    
    # NEW ADK utilities
    "validate_tool_context",
    "update_agent_activity",
    "get_user_preferences",
    "update_user_preferences",
    "get_service_connection_status",
    "update_service_connection_status",
    "get_session_summary",
    "log_tool_execution"
]