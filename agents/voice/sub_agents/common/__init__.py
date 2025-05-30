"""
Common utilities for Oprina agents with enhanced ADK integration.
Provides session state constants and utility functions for all agents.
"""

# Import session keys individually to avoid conflicts
from .session_keys import (
    # User persistent data
    USER_ID, USER_NAME, USER_EMAIL, USER_GMAIL_CONNECTED,
    USER_CALENDAR_CONNECTED, USER_PREFERENCES, USER_LAST_ACTIVITY,
    
    # Email state (current conversation)
    EMAIL_CURRENT, EMAIL_LAST_FETCH, EMAIL_UNREAD_COUNT, EMAIL_LAST_SENT,
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_QUERY, EMAIL_RESULTS_COUNT, 
    EMAIL_LAST_SENT_TO, EMAIL_CONNECTION_STATUS,
    
    # Calendar state (current conversation)
    CALENDAR_CURRENT, CALENDAR_LAST_FETCH, CALENDAR_UPCOMING_COUNT,
    CALENDAR_LAST_EVENT_CREATED,
    
    # Content state (current conversation)
    CONTENT_LAST_SUMMARY, CONTENT_LAST_ANALYSIS, CONTENT_PROCESSING_STATUS,
    
    # Coordination state (current conversation)
    COORDINATION_ACTIVE, COORDINATION_WORKFLOW_TYPE, COORDINATION_CURRENT_STEP,
    COORDINATION_REQUIRED_AGENTS, COORDINATION_COMPLETED_AGENTS,
    COORDINATION_LAST_DELEGATED_AGENT, COORDINATION_DELEGATION_HISTORY,
    COORDINATION_AGENT_OUTPUTS, COORDINATION_WORKFLOW_PROGRESS,
    
    # Conversation state
    CONVERSATION_ACTIVE, CURRENT_TASK, LAST_AGENT_USED, CURRENT_WORKFLOW,
    
    # App global state
    APP_VERSION, APP_FEATURES, APP_NAME,
    
    # Temporary state
    TEMP_PROCESSING, TEMP_CURRENT_OPERATION, TEMP_WORKFLOW_STEP, TEMP_ERROR_STATE,
    
    # Workflow type constants
    WORKFLOW_EMAIL_ONLY, WORKFLOW_CALENDAR_ONLY, WORKFLOW_CONTENT_ONLY,
    WORKFLOW_EMAIL_CONTENT, WORKFLOW_CALENDAR_CONTENT, WORKFLOW_EMAIL_CALENDAR, 
    WORKFLOW_ALL_AGENTS,
    
    # Pattern type constants
    PATTERN_SEQUENTIAL, PATTERN_PARALLEL, PATTERN_CONDITIONAL, 
    PATTERN_ITERATIVE, PATTERN_MIXED,
    
    # Agent status constants
    AGENT_STATUS_READY, AGENT_STATUS_BUSY, AGENT_STATUS_ERROR, AGENT_STATUS_UNAVAILABLE
)

# Import utility functions
from .utils import (
    # Original utilities
    format_timestamp, safe_get_nested_value, truncate_string,
    extract_user_info_from_session,
    
    # ADK-specific utilities
    validate_tool_context, update_agent_activity, get_user_preferences,
    update_user_preferences, get_service_connection_status,
    update_service_connection_status, get_session_summary, log_tool_execution
)

# Export everything explicitly
__all__ = [
    # Session keys - User persistent data
    "USER_ID", "USER_NAME", "USER_EMAIL", "USER_GMAIL_CONNECTED",
    "USER_CALENDAR_CONNECTED", "USER_PREFERENCES", "USER_LAST_ACTIVITY",
    
    # Session keys - Email state
    "EMAIL_CURRENT", "EMAIL_LAST_FETCH", "EMAIL_UNREAD_COUNT", "EMAIL_LAST_SENT",
    "EMAIL_CURRENT_RESULTS", "EMAIL_LAST_QUERY", "EMAIL_RESULTS_COUNT",
    "EMAIL_LAST_SENT_TO", "EMAIL_CONNECTION_STATUS",
    
    # Session keys - Calendar state
    "CALENDAR_CURRENT", "CALENDAR_LAST_FETCH", "CALENDAR_UPCOMING_COUNT",
    "CALENDAR_LAST_EVENT_CREATED",
    
    # Session keys - Content state
    "CONTENT_LAST_SUMMARY", "CONTENT_LAST_ANALYSIS", "CONTENT_PROCESSING_STATUS",
    
    # Session keys - Coordination state
    "COORDINATION_ACTIVE", "COORDINATION_WORKFLOW_TYPE", "COORDINATION_CURRENT_STEP",
    "COORDINATION_REQUIRED_AGENTS", "COORDINATION_COMPLETED_AGENTS",
    "COORDINATION_LAST_DELEGATED_AGENT", "COORDINATION_DELEGATION_HISTORY",
    "COORDINATION_AGENT_OUTPUTS", "COORDINATION_WORKFLOW_PROGRESS",
    
    # Session keys - Conversation state
    "CONVERSATION_ACTIVE", "CURRENT_TASK", "LAST_AGENT_USED", "CURRENT_WORKFLOW",
    
    # Session keys - App global state
    "APP_VERSION", "APP_FEATURES", "APP_NAME",
    
    # Session keys - Temporary state
    "TEMP_PROCESSING", "TEMP_CURRENT_OPERATION", "TEMP_WORKFLOW_STEP", "TEMP_ERROR_STATE",
    
    # Workflow type constants
    "WORKFLOW_EMAIL_ONLY", "WORKFLOW_CALENDAR_ONLY", "WORKFLOW_CONTENT_ONLY",
    "WORKFLOW_EMAIL_CONTENT", "WORKFLOW_CALENDAR_CONTENT", "WORKFLOW_EMAIL_CALENDAR",
    "WORKFLOW_ALL_AGENTS",
    
    # Pattern type constants
    "PATTERN_SEQUENTIAL", "PATTERN_PARALLEL", "PATTERN_CONDITIONAL",
    "PATTERN_ITERATIVE", "PATTERN_MIXED",
    
    # Agent status constants
    "AGENT_STATUS_READY", "AGENT_STATUS_BUSY", "AGENT_STATUS_ERROR", "AGENT_STATUS_UNAVAILABLE",
    
    # Utility functions - Original
    "format_timestamp", "safe_get_nested_value", "truncate_string",
    "extract_user_info_from_session",
    
    # Utility functions - ADK-specific
    "validate_tool_context", "update_agent_activity", "get_user_preferences",
    "update_user_preferences", "get_service_connection_status",
    "update_service_connection_status", "get_session_summary", "log_tool_execution"
]

# Package metadata
__version__ = "2.0.0"
__description__ = "Common utilities and constants for ADK-integrated Oprina agents"
