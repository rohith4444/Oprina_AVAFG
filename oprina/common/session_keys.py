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
# AI-powered email processing keys
EMAIL_LAST_AI_SUMMARY = "email:last_ai_summary"
EMAIL_LAST_AI_SUMMARY_AT = "email:last_ai_summary_at"
EMAIL_LAST_SENTIMENT_ANALYSIS = "email:last_sentiment_analysis"
EMAIL_LAST_SENTIMENT_ANALYSIS_AT = "email:last_sentiment_analysis_at"
EMAIL_LAST_EXTRACTED_TASKS = "email:last_extracted_tasks"
EMAIL_LAST_TASK_EXTRACTION_AT = "email:last_task_extraction_at"
EMAIL_LAST_GENERATED_REPLY = "email:last_generated_reply"
EMAIL_LAST_REPLY_GENERATION_AT = "email:last_reply_generation_at"

EMAIL_PENDING_SEND = "email_pending_send"
EMAIL_PENDING_REPLY = "email_pending_reply"
EMAIL_LAST_GENERATED_EMAIL = "email_last_generated_email"
EMAIL_LAST_EMAIL_GENERATION_AT = "email_last_email_generation_at"
EMAIL_LAST_GENERATED_EMAIL_TO = "email_last_generated_email_to"

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
