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

EMAIL_MESSAGE_INDEX_MAP = "email:message_index_map"  # Maps position to message_id
EMAIL_LAST_LISTED_MESSAGES = "email:last_listed_messages"  # Full message data with IDs
EMAIL_LAST_SINGLE_RESULT = "email:last_single_result"  # Single email context for "yes" responses
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

EMAIL_PENDING_SEND = "email:pending_send"
EMAIL_PENDING_REPLY = "email:pending_reply"
EMAIL_LAST_GENERATED_EMAIL = "email:last_generated_email"
EMAIL_LAST_EMAIL_GENERATION_AT = "email:last_email_generation_at"
EMAIL_LAST_GENERATED_EMAIL_TO = "email:last_generated_email_to"

# Draft management
EMAIL_LAST_DRAFT_CREATED = "email:last_draft_created"
EMAIL_LAST_DRAFT_CREATED_AT = "email:last_draft_created_at"
EMAIL_DRAFTS_COUNT = "email:drafts_count"
EMAIL_LAST_DRAFTS_FETCH = "email:last_drafts_fetch"
EMAIL_LAST_DRAFT_SENT = "email:last_draft_sent"
EMAIL_LAST_DRAFT_SENT_AT = "email:last_draft_sent_at"
EMAIL_LAST_SENT_MESSAGE_ID = "email:last_sent_message_id"
EMAIL_LAST_DRAFT_DELETED = "email:last_draft_deleted"
EMAIL_LAST_DRAFT_DELETED_AT = "email:last_draft_deleted_at"

# Label management
EMAIL_LABELS_COUNT = "email:labels_count"
EMAIL_LAST_LABELS_FETCH = "email:last_labels_fetch"
EMAIL_LAST_LABEL_CREATED = "email:last_label_created"
EMAIL_LAST_LABEL_CREATED_AT = "email:last_label_created_at"
EMAIL_LAST_LABEL_CREATED_NAME = "email:last_label_created_name"
EMAIL_LAST_LABEL_APPLIED = "email:last_label_applied"
EMAIL_LAST_LABEL_APPLIED_AT = "email:last_label_applied_at"
EMAIL_LAST_LABEL_APPLIED_TO = "email:last_label_applied_to"
EMAIL_LAST_LABEL_REMOVED = "email:last_label_removed"
EMAIL_LAST_LABEL_REMOVED_AT = "email:last_label_removed_at"
EMAIL_LAST_LABEL_REMOVED_FROM = "email:last_label_removed_from"

# Enhanced status management
EMAIL_LAST_STARRED = "email:last_starred"
EMAIL_LAST_STARRED_AT = "email:last_starred_at"
EMAIL_LAST_UNSTARRED = "email:last_unstarred"
EMAIL_LAST_UNSTARRED_AT = "email:last_unstarred_at"
EMAIL_LAST_MARKED_IMPORTANT = "email:last_marked_important"
EMAIL_LAST_MARKED_IMPORTANT_AT = "email:last_marked_important_at"
EMAIL_LAST_MARKED_NOT_IMPORTANT = "email:last_marked_not_important"
EMAIL_LAST_MARKED_NOT_IMPORTANT_AT = "email:last_marked_not_important_at"

# Spam management
EMAIL_LAST_MARKED_SPAM = "email:last_marked_spam"
EMAIL_LAST_MARKED_SPAM_AT = "email:last_marked_spam_at"
EMAIL_LAST_UNMARKED_SPAM = "email:last_unmarked_spam"
EMAIL_LAST_UNMARKED_SPAM_AT = "email:last_unmarked_spam_at"

# Thread management
EMAIL_LAST_THREAD_VIEWED = "email:last_thread_viewed"
EMAIL_LAST_THREAD_VIEWED_AT = "email:last_thread_viewed_at"
EMAIL_LAST_THREAD_MESSAGE_COUNT = "email:last_thread_message_count"
EMAIL_LAST_THREAD_MODIFIED = "email:last_thread_modified"
EMAIL_LAST_THREAD_MODIFIED_AT = "email:last_thread_modified_at"

# Attachment management
EMAIL_LAST_ATTACHMENTS_LISTED = "email:last_attachments_listed"
EMAIL_LAST_ATTACHMENTS_COUNT = "email:last_attachments_count"
EMAIL_LAST_ATTACHMENTS_DATA = "email:last_attachments_data"

# User profile
EMAIL_USER_EMAIL = "email:user_email"
EMAIL_PROFILE_FETCHED_AT = "email:profile_fetched_at"
EMAIL_MESSAGES_TOTAL = "email:messages_total"
EMAIL_THREADS_TOTAL = "email:threads_total"
EMAIL_LAST_MESSAGE_ID = "email:last_message_id"

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
# Cross-Agent Workflow Keys
# =============================================================================

# Workflow management
ACTIVE_WORKFLOW = "workflow:active"
WORKFLOW_HISTORY = "workflow:history"
LAST_AGENT_TRANSFER = "workflow:last_transfer"

# Meeting coordination workflows
MEETING_COORDINATION_ACTIVE = "workflow:meeting_coordination"
MEETING_INVITES_PENDING = "workflow:meeting_invites"
MEETING_CONFLICTS_FOUND = "workflow:meeting_conflicts"

# Email processing workflows  
EMAIL_PROCESSING_BATCH = "workflow:email_batch"
EMAIL_DEADLINES_FOUND = "workflow:email_deadlines"
EMAIL_FOLLOW_UPS_NEEDED = "workflow:email_followups"

# Calendar integration workflows
CALENDAR_EMAIL_SYNC = "workflow:calendar_email_sync"
AVAILABILITY_CHECK_RESULTS = "workflow:availability_results"

# Follow-up action tracking
EMAIL_LAST_OPERATED_MESSAGE = "email:last_operated_message"
EMAIL_LAST_OPERATED_MESSAGE_AT = "email:last_operated_message_at"
EMAIL_LAST_OPERATION_TYPE = "email:last_operation_type"