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
# Additional email constants you might need
EMAIL_LAST_MESSAGE_VIEWED = "email:last_message_viewed"
EMAIL_LAST_MESSAGE_VIEWED_AT = "email:last_message_viewed_at"
EMAIL_LAST_SENT_SUBJECT = "email:last_sent_subject"
EMAIL_LAST_SENT_ID = "email:last_sent_id"
EMAIL_LAST_REPLY_SENT = "email:last_reply_sent"
EMAIL_LAST_REPLY_TO = "email:last_reply_to"
EMAIL_LAST_REPLY_ID = "email:last_reply_id"
EMAIL_LAST_REPLY_THREAD = "email:last_reply_thread"
EMAIL_LAST_MARKED_READ = "email:last_marked_read"
EMAIL_LAST_MARKED_READ_AT = "email:last_marked_read_at"
EMAIL_LAST_ARCHIVED = "email:last_archived"
EMAIL_LAST_ARCHIVED_AT = "email:last_archived_at"
EMAIL_LAST_DELETED = "email:last_deleted"
EMAIL_LAST_DELETED_AT = "email:last_deleted_at"

# =============================================================================
# Calendar State (current conversation)
# =============================================================================
CALENDAR_CURRENT = "calendar:current_events"
CALENDAR_LAST_FETCH = "calendar:last_fetch"
CALENDAR_UPCOMING_COUNT = "calendar:upcoming_count"
CALENDAR_LAST_EVENT_CREATED = "calendar:last_event_created"

# Calendar event management
CALENDAR_LAST_QUERY_DAYS = "calendar:last_query_days"
CALENDAR_LAST_EVENT_CREATED_AT = "calendar:last_event_created_at"
CALENDAR_LAST_CREATED_EVENT_ID = "calendar:last_created_event_id"
CALENDAR_LAST_QUICK_EVENT = "calendar:last_quick_event"
CALENDAR_LAST_QUICK_EVENT_AT = "calendar:last_quick_event_at"

# Calendar event updates and deletions
CALENDAR_LAST_UPDATED_EVENT = "calendar:last_updated_event"
CALENDAR_LAST_EVENT_UPDATED_AT = "calendar:last_event_updated_at"
CALENDAR_LAST_DELETED_EVENT = "calendar:last_deleted_event"

# Calendar availability and free time
CALENDAR_LAST_FREE_TIME_SEARCH = "calendar:last_free_time_search"
CALENDAR_LAST_FREE_SLOTS = "calendar:last_free_slots"
CALENDAR_LAST_AVAILABILITY_CHECK = "calendar:last_availability_check"

# Calendar information
CALENDAR_LAST_TIME_REQUEST = "calendar:last_time_request"
CALENDAR_AVAILABLE_CALENDARS = "calendar:available_calendars"
CALENDAR_CALENDARS_LIST_AT = "calendar:calendars_list_at"
CALENDAR_CALENDARS_COUNT = "calendar:calendars_count"

# =============================================================================
# Content State (current conversation)
# =============================================================================
CONTENT_LAST_SUMMARY = "content:last_summary"
CONTENT_LAST_ANALYSIS = "content:last_analysis"
CONTENT_PROCESSING_STATUS = "content:processing_status"
# Content summarization keys
CONTENT_LAST_SUMMARY_AT = "content:last_summary_at"
CONTENT_LAST_SUMMARY_LENGTH = "content:last_summary_length"
CONTENT_LAST_SUMMARY_DETAIL = "content:last_summary_detail"
CONTENT_LAST_LIST_SUMMARY = "content:last_list_summary"
CONTENT_LAST_LIST_SUMMARY_COUNT = "content:last_list_summary_count"
CONTENT_LAST_LIST_SUMMARY_AT = "content:last_list_summary_at"

# Reply generation keys
CONTENT_LAST_REPLY_GENERATED = "content:last_reply_generated"
CONTENT_LAST_REPLY_STYLE = "content:last_reply_style"
CONTENT_LAST_REPLY_AT = "content:last_reply_at"
CONTENT_LAST_REPLY_SENDER = "content:last_reply_sender"
CONTENT_LAST_TEMPLATES_SUGGESTED = "content:last_templates_suggested"
CONTENT_LAST_TEMPLATES_COUNT = "content:last_templates_count"
CONTENT_LAST_TEMPLATES_AT = "content:last_templates_at"

# Analysis keys
CONTENT_LAST_ANALYSIS_DATA = "content:last_analysis_data"
CONTENT_LAST_ANALYSIS_AT = "content:last_analysis_at"
CONTENT_LAST_ACTION_ITEMS = "content:last_action_items"
CONTENT_LAST_ACTION_ITEMS_COUNT = "content:last_action_items_count"
CONTENT_LAST_ACTION_ITEMS_AT = "content:last_action_items_at"

# Voice optimization keys
CONTENT_LAST_VOICE_OPTIMIZATION = "content:last_voice_optimization"
CONTENT_LAST_VOICE_OPTIMIZATION_AT = "content:last_voice_optimization_at"
CONTENT_LAST_VOICE_ORIGINAL_LENGTH = "content:last_voice_original_length"
CONTENT_LAST_VOICE_OPTIMIZED_LENGTH = "content:last_voice_optimized_length"
CONTENT_LAST_VOICE_SUMMARY = "content:last_voice_summary"
CONTENT_LAST_VOICE_SUMMARY_AT = "content:last_voice_summary_at"

 