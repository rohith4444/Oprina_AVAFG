"""
Session state key constants for consistent access across all agents.
Defines the standard session.state structure for Oprina.
"""

# User persistent data (survives across sessions)
USER_ID = "user:id"
USER_NAME = "user:name"
USER_EMAIL = "user:email"
USER_GMAIL_CONNECTED = "user:gmail_connected"
USER_CALENDAR_CONNECTED = "user:calendar_connected"
USER_PREFERENCES = "user:preferences"
USER_LAST_ACTIVITY = "user:last_activity"

# Email state (current conversation)
EMAIL_CURRENT = "email:current_emails"
EMAIL_LAST_FETCH = "email:last_fetch"
EMAIL_UNREAD_COUNT = "email:unread_count"
EMAIL_LAST_SENT = "email:last_sent"

# Calendar state (current conversation)
CALENDAR_CURRENT = "calendar:current_events"
CALENDAR_LAST_FETCH = "calendar:last_fetch"
CALENDAR_UPCOMING_COUNT = "calendar:upcoming_count"
CALENDAR_LAST_EVENT_CREATED = "calendar:last_event_created"

# Conversation state (current session only)
CONVERSATION_ACTIVE = "conversation_active"
CURRENT_TASK = "current_task"
LAST_AGENT_USED = "last_agent_used"
CURRENT_WORKFLOW = "current_workflow"

# App global state
APP_VERSION = "app:version"
APP_FEATURES = "app:features"

# Temporary state (not persistent)
TEMP_PROCESSING = "temp:processing"
TEMP_CURRENT_OPERATION = "temp:current_operation"
TEMP_WORKFLOW_STEP = "temp:workflow_step"