"""
Test data for end-to-end tests.

This module contains sample data for testing various workflows.
"""
import json
from datetime import datetime, timedelta

# Sample session data
SAMPLE_SESSION_DATA = {
    "session_id": "test-session-123",
    "user_id": "test-user",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "events": []
}

# Sample audio data (base64 encoded)
SAMPLE_AUDIO_DATA = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="

# Sample email content
SAMPLE_EMAIL_CONTENT = {
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email for testing purposes.",
    "cc": None,
    "bcc": None
}

# Sample calendar event
SAMPLE_CALENDAR_EVENT = {
    "summary": "Test Meeting",
    "description": "This is a test meeting for testing purposes.",
    "start": {
        "dateTime": (datetime.now() + timedelta(days=1)).isoformat(),
        "timeZone": "America/Los_Angeles"
    },
    "end": {
        "dateTime": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
        "timeZone": "America/Los_Angeles"
    },
    "attendees": [
        {"email": "attendee1@example.com"},
        {"email": "attendee2@example.com"}
    ]
}

# Sample content for summarization
SAMPLE_CONTENT = """
# Sample Document for Testing

This is a sample document for testing content summarization.

## Section 1

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies tincidunt, nisl nisl aliquam nisl, eget aliquam nisl nisl eget nisl.

## Section 2

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

## Section 3

Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.
"""

# Sample voice commands
VOICE_COMMANDS = {
    "email": "Check my emails",
    "calendar": "Schedule a meeting tomorrow at 2 PM",
    "content": "Summarize this document",
    "complex": "Schedule a meeting with John tomorrow at 3 PM and send him an email with the agenda"
}

# Sample MCP client responses
MCP_RESPONSES = {
    "email": {
        "content": "I've checked your emails. You have 3 new messages.",
        "tool_results": [
            {
                "tool_name": "gmail_list_messages",
                "result": json.dumps([
                    {"id": "msg1", "subject": "Test Email 1", "from": "sender1@example.com"},
                    {"id": "msg2", "subject": "Test Email 2", "from": "sender2@example.com"},
                    {"id": "msg3", "subject": "Test Email 3", "from": "sender3@example.com"}
                ])
            }
        ]
    },
    "calendar": {
        "content": "I've scheduled a meeting for tomorrow at 2 PM.",
        "tool_results": [
            {
                "tool_name": "calendar_create_event",
                "result": json.dumps({"event_id": "event123", "htmlLink": "https://calendar.google.com/event?id=event123"})
            }
        ]
    },
    "content": {
        "content": "Here's a summary of the document: This document discusses three main topics: Section 1 covers basic concepts, Section 2 explores advanced topics, and Section 3 provides conclusions.",
        "tool_results": [
            {
                "tool_name": "content_summarize",
                "result": json.dumps({"summary": "This document discusses three main topics: Section 1 covers basic concepts, Section 2 explores advanced topics, and Section 3 provides conclusions."})
            }
        ]
    },
    "complex": {
        "content": "I've scheduled a meeting with John tomorrow at 3 PM and sent him an email with the agenda.",
        "tool_results": [
            {
                "tool_name": "calendar_create_event",
                "result": json.dumps({"event_id": "event456", "htmlLink": "https://calendar.google.com/event?id=event456"})
            },
            {
                "tool_name": "gmail_send_message",
                "result": json.dumps({"message_id": "msg456", "thread_id": "thread456"})
            }
        ]
    },
    "error": {
        "content": "I'm sorry, I couldn't process your request. There was an error with the speech recognition service.",
        "tool_results": []
    }
} 