"""
Session state key constants for consistent access across all agents.
Cleaned up version with connection state management removed.
"""

# =============================================================================
# User Persistent Data (survives across sessions)
# =============================================================================
USER_ID = "user:id"
USER_NAME = "user:name"
USER_EMAIL = "user:email"
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

# Email message operations
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
# Event listing
CALENDAR_CURRENT = "calendar:current_events"           
CALENDAR_LAST_FETCH = "calendar:last_fetch"
CALENDAR_LAST_LIST_START_DATE = "calendar:last_list_start_date"   # NEW
CALENDAR_LAST_LIST_DAYS = "calendar:last_list_days"              # NEW  
CALENDAR_LAST_LIST_COUNT = "calendar:last_list_count"            # NEW

# Event creation
CALENDAR_LAST_EVENT_CREATED = "calendar:last_event_created"
CALENDAR_LAST_EVENT_CREATED_AT = "calendar:last_event_created_at"
CALENDAR_LAST_CREATED_EVENT_ID = "calendar:last_created_event_id"

# Event updates
CALENDAR_LAST_UPDATED_EVENT = "calendar:last_updated_event"
CALENDAR_LAST_EVENT_UPDATED_AT = "calendar:last_event_updated_at"

# Event deletion  
CALENDAR_LAST_DELETED_EVENT = "calendar:last_deleted_event"
CALENDAR_LAST_DELETED_ID = "calendar:last_deleted_id"            # NEW
CALENDAR_LAST_DELETED_AT = "calendar:last_deleted_at"            # NEW
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