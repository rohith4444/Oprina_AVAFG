"""
Session state key constants for consistent access across all agents.
Enhanced with coordination-specific keys for multi-agent workflow management.
"""

# =============================================================================
# User Persistent Data (survives across sessions)
# =============================================================================
USER_ID = "user:id"
USER_NAME = "user:name"
USER_EMAIL = "user:email"
USER_GMAIL_CONNECTED = "user:gmail_connected"
USER_CALENDAR_CONNECTED = "user:calendar_connected"
USER_PREFERENCES = "user:preferences"
USER_LAST_ACTIVITY = "user:last_activity"

# =============================================================================
# Email State (current conversation)
# =============================================================================
EMAIL_CURRENT = "email:current_emails"
EMAIL_LAST_FETCH = "email:last_fetch"
EMAIL_UNREAD_COUNT = "email:unread_count"
EMAIL_LAST_SENT = "email:last_sent"
EMAIL_CURRENT_RESULTS = "email:current_results"
EMAIL_LAST_QUERY = "email:last_query"
EMAIL_RESULTS_COUNT = "email:results_count"
EMAIL_LAST_SENT_TO = "email:last_sent_to"
EMAIL_CONNECTION_STATUS = "email:connection_status"

# =============================================================================
# Calendar State (current conversation)
# =============================================================================
CALENDAR_CURRENT = "calendar:current_events"
CALENDAR_LAST_FETCH = "calendar:last_fetch"
CALENDAR_UPCOMING_COUNT = "calendar:upcoming_count"
CALENDAR_LAST_EVENT_CREATED = "calendar:last_event_created"

# =============================================================================
# Content State (current conversation)
# =============================================================================
CONTENT_LAST_SUMMARY = "content:last_summary"
CONTENT_LAST_ANALYSIS = "content:last_analysis"
CONTENT_PROCESSING_STATUS = "content:processing_status"

# =============================================================================
# NEW: Coordination State (current conversation)
# =============================================================================

# Core coordination tracking
COORDINATION_ACTIVE = "coordination:active"
COORDINATION_WORKFLOW_TYPE = "coordination:workflow_type"
COORDINATION_CURRENT_STEP = "coordination:current_step"
COORDINATION_REQUIRED_AGENTS = "coordination:required_agents"
COORDINATION_COMPLETED_AGENTS = "coordination:completed_agents"

# Workflow progress tracking
COORDINATION_WORKFLOW_PROGRESS = "coordination:workflow_progress"
COORDINATION_WORKFLOW_RESULTS = "coordination:workflow_results"
COORDINATION_WORKFLOW_ERRORS = "coordination:workflow_errors"
COORDINATION_WORKFLOW_START_TIME = "coordination:workflow_start_time"

# Agent delegation tracking
COORDINATION_LAST_DELEGATED_AGENT = "coordination:last_delegated_agent"
COORDINATION_DELEGATION_HISTORY = "coordination:delegation_history"
COORDINATION_AGENT_EXECUTION_TIMES = "coordination:agent_execution_times"
COORDINATION_DELEGATION_COUNT = "coordination:delegation_count"

# Multi-agent workflow patterns
COORDINATION_PATTERN_TYPE = "coordination:pattern_type"  # sequential, parallel, conditional
COORDINATION_PATTERN_SUCCESS_RATE = "coordination:pattern_success_rate"
COORDINATION_LAST_SUCCESSFUL_PATTERN = "coordination:last_successful_pattern"

# Cross-agent context sharing
COORDINATION_SHARED_CONTEXT = "coordination:shared_context"
COORDINATION_AGENT_OUTPUTS = "coordination:agent_outputs"
COORDINATION_CROSS_AGENT_DATA = "coordination:cross_agent_data"

# Performance and optimization
COORDINATION_TOTAL_EXECUTION_TIME = "coordination:total_execution_time"
COORDINATION_AVERAGE_DELEGATION_TIME = "coordination:average_delegation_time"
COORDINATION_OPTIMIZATION_SUGGESTIONS = "coordination:optimization_suggestions"

# =============================================================================
# Conversation State (current session only)
# =============================================================================
CONVERSATION_ACTIVE = "conversation_active"
CURRENT_TASK = "current_task"
LAST_AGENT_USED = "last_agent_used"
CURRENT_WORKFLOW = "current_workflow"

# =============================================================================
# App Global State
# =============================================================================
APP_VERSION = "app:version"
APP_FEATURES = "app:features"
APP_NAME = "app:name"

# =============================================================================
# Temporary State (not persistent)
# =============================================================================
TEMP_PROCESSING = "temp:processing"
TEMP_CURRENT_OPERATION = "temp:current_operation"
TEMP_WORKFLOW_STEP = "temp:workflow_step"
TEMP_ERROR_STATE = "temp:error_state"

# NEW: Temporary coordination data
TEMP_COORDINATION_CONTEXT = "temp:coordination_context"
TEMP_DELEGATION_TARGET = "temp:delegation_target"
TEMP_WORKFLOW_VALIDATION = "temp:workflow_validation"
TEMP_AGENT_READINESS = "temp:agent_readiness"

# =============================================================================
# ADK State Prefix Documentation
# =============================================================================
"""
ADK State Prefix Guide:
- user: - User-specific data, persistent across sessions
- app: - Application-wide data, shared across all users  
- temp: - Temporary data, never persisted
- (no prefix) - Session-specific data, persists with session
- email: - Email agent specific data
- calendar: - Calendar agent specific data
- content: - Content agent specific data  
- coordination: - Coordinator agent specific data (NEW)

Coordination State Usage Patterns:
- workflow_type: "email_only", "calendar_only", "email_content", "email_calendar", "all_agents"
- pattern_type: "sequential", "parallel", "conditional", "iterative"
- delegation_history: List of agent names in order of execution
- agent_outputs: Dictionary mapping agent names to their results
- shared_context: Data that needs to be accessible to multiple agents
"""

# =============================================================================
# Coordination Workflow Types (Constants)
# =============================================================================
WORKFLOW_EMAIL_ONLY = "email_only"
WORKFLOW_CALENDAR_ONLY = "calendar_only"
WORKFLOW_CONTENT_ONLY = "content_only"
WORKFLOW_EMAIL_CONTENT = "email_content"
WORKFLOW_CALENDAR_CONTENT = "calendar_content"
WORKFLOW_EMAIL_CALENDAR = "email_calendar"
WORKFLOW_ALL_AGENTS = "all_agents"

# Coordination Pattern Types
PATTERN_SEQUENTIAL = "sequential"
PATTERN_PARALLEL = "parallel"
PATTERN_CONDITIONAL = "conditional"
PATTERN_ITERATIVE = "iterative"
PATTERN_MIXED = "mixed"

# Agent Status Constants
AGENT_STATUS_READY = "ready"
AGENT_STATUS_BUSY = "busy"
AGENT_STATUS_ERROR = "error"
AGENT_STATUS_UNAVAILABLE = "unavailable"

# =============================================================================
# Voice State (current conversation)
# =============================================================================
VOICE_LAST_TRANSCRIPT = "voice:last_transcript"
VOICE_LAST_CONFIDENCE = "voice:last_confidence"
VOICE_LAST_STT_AT = "voice:last_stt_at"
VOICE_LAST_TTS_TEXT = "voice:last_tts_text"
VOICE_LAST_TTS_VOICE = "voice:last_tts_voice"
VOICE_LAST_TTS_AT = "voice:last_tts_at"
VOICE_LAST_AUDIO_SIZE = "voice:last_audio_size"
VOICE_QUALITY_CHECK_AT = "voice:quality_check_at"
VOICE_PREFERENCES_UPDATED_AT = "voice:preferences_updated_at"
VOICE_ACTIVE_PREFERENCES = "voice:active_preferences"