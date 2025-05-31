"""
Common Agent Utilities

Shared utilities and constants used across all agents in the system.
Provides consistent patterns for tool context validation, session state
management, and cross-agent coordination.
"""

from .utils import (
    # Core validation
    validate_tool_context,
    update_agent_activity,
    log_tool_execution,
    
    # User preferences
    get_user_preferences,
    update_user_preferences,
    
    # Service status
    get_service_connection_status,
    update_service_connection_status,
    
    # Session management
    get_session_summary,
    extract_user_info_from_session,
    
    # Utilities
    format_timestamp,
    safe_get_nested_value,
    truncate_string
)

from .session_keys import *  # All session key constants

__all__ = [
    # Utils
    "validate_tool_context", "update_agent_activity", "log_tool_execution",
    "get_user_preferences", "update_user_preferences",
    "get_service_connection_status", "update_service_connection_status", 
    "get_session_summary", "extract_user_info_from_session",
    "format_timestamp", "safe_get_nested_value", "truncate_string",
]