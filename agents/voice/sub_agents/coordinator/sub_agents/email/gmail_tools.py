"""
Direct Gmail Tools for ADK - Replaces MCP Integration

Simple ADK-compatible tools that use Gmail API directly through existing auth services.
No MCP bridge complexity - just direct function tools.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(7):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from services.google_cloud.gmail_auth import get_gmail_service, check_gmail_connection
from agents.voice.sub_agents.common import (
    USER_GMAIL_CONNECTED, USER_EMAIL 
)
from services.logging.logger import setup_logger

logger = setup_logger("gmail_tools", console_output=True)


# =============================================================================
# Gmail Connection Tools
# =============================================================================

def gmail_check_connection(tool_context=None) -> str:
    """Check Gmail connection status."""
    try:
        if not tool_context or not hasattr(tool_context, 'session'):
            return "Unable to check Gmail connection - no session context"
        
        # Check session state first
        gmail_connected = tool_context.session.state.get(USER_GMAIL_CONNECTED, False)
        
        if gmail_connected:
            # Verify actual connection
            connection_status = check_gmail_connection()
            if connection_status.get("connected", False):
                user_email = connection_status.get("user_email", "unknown")
                return f"Gmail connected as {user_email}"
            else:
                return f"Gmail connection issue: {connection_status.get('error', 'Unknown error')}"
        else:
            return "Gmail not connected. Please authenticate with Gmail first."
            
    except Exception as e:
        logger.error(f"Error checking Gmail connection: {e}")
        return f"Error checking Gmail connection: {str(e)}"


def gmail_authenticate(tool_context=None) -> str:
    """Authenticate with Gmail."""
    try:
        # Test Gmail service creation
        service = get_gmail_service()
        
        if service:
            # Get user profile to confirm connection
            profile = service.users().getProfile(userId='me').execute()
            user_email = profile.get('emailAddress', 'unknown')
            
            return f"Gmail authentication successful for {user_email}"
        else:
            return "Gmail authentication failed. Please check your credentials."
            
    except Exception as e:
        logger.error(f"Gmail authentication error: {e}")
        return f"Gmail authentication failed: {str(e)}"


# =============================================================================
# Gmail Email Reading Tools
# =============================================================================

def gmail_list_messages(query: str = "", max_results: int = 10, tool_context=None) -> str:
    """List Gmail messages with optional search query."""
    try:
        # Check Gmail connection
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Unable to connect to Gmail service"
        
        # List messages
        result = service.users().messages().list(
            userId='me', 
            q=query, 
            maxResults=max_results
        ).execute()
        
        messages = result.get('messages', [])
        
        if not messages:
            return f"No messages found{' for query: ' + query if query else ''}"
        
        # Get basic info for each message
        message_summaries = []
        for msg in messages[:max_results]:
            try:
                msg_data = service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='metadata'
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                
                summary = {
                    "id": msg['id'],
                    "from": headers.get('From', 'Unknown'),
                    "subject": headers.get('Subject', 'No Subject'),
                    "date": headers.get('Date', 'Unknown')
                }
                message_summaries.append(summary)
                
            except Exception as e:
                logger.warning(f"Error getting message {msg['id']}: {e}")
                continue
        
        # Format response
        response_lines = [f"Found {len(message_summaries)} messages:"]
        for i, msg in enumerate(message_summaries[:5], 1):  # Show first 5
            response_lines.append(f"{i}. From: {msg['from'][:30]} | Subject: {msg['subject'][:40]}")
        
        if len(message_summaries) > 5:
            response_lines.append(f"... and {len(message_summaries) - 5} more messages")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing Gmail messages: {e}")
        return f"Error retrieving emails: {str(e)}"


def gmail_get_message(message_id: str, tool_context=None) -> str:
    """Get detailed content of a specific Gmail message."""
    try:
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        service = get_gmail_service()
        if not service:
            return "Unable to connect to Gmail service"
        
        # Get full message
        message = service.users().messages().get(
            userId='me', 
            id=message_id, 
            format='full'
        ).execute()
        
        # Extract headers
        headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
        
        # Extract body
        body = _extract_message_body(message.get('payload', {}))
        
        # Format response
        response = f"""Email Details:
From: {headers.get('From', 'Unknown')}
To: {headers.get('To', 'Unknown')}
Subject: {headers.get('Subject', 'No Subject')}
Date: {headers.get('Date', 'Unknown')}

Content:
{body[:500]}{'...' if len(body) > 500 else ''}"""
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting Gmail message {message_id}: {e}")
        return f"Error retrieving email: {str(e)}"


def gmail_search_messages(search_query: str, max_results: int = 10, tool_context=None) -> str:
    """Search Gmail messages using Gmail search syntax."""
    try:
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        return gmail_list_messages(query=search_query, max_results=max_results, tool_context=tool_context)
        
    except Exception as e:
        logger.error(f"Error searching Gmail: {e}")
        return f"Error searching emails: {str(e)}"


# =============================================================================
# Gmail Sending Tools
# =============================================================================

def gmail_send_message(to: str, subject: str, body: str, cc: str = "", bcc: str = "", tool_context=None) -> str:
    """Send a Gmail message."""
    try:
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        service = get_gmail_service()
        if not service:
            return "Unable to connect to Gmail service"
        
        # Get sender email from session or profile
        sender_email = tool_context.session.state.get(USER_EMAIL, "")
        if not sender_email:
            try:
                profile = service.users().getProfile(userId='me').execute()
                sender_email = profile.get('emailAddress', '')
            except:
                sender_email = "me"
        
        # Create message
        from email.mime.text import MIMEText
        import base64
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        message['from'] = sender_email
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return f"Email sent successfully to {to}. Subject: {subject}"
        
    except Exception as e:
        logger.error(f"Error sending Gmail message: {e}")
        return f"Error sending email: {str(e)}"


def gmail_reply_to_message(message_id: str, reply_body: str, tool_context=None) -> str:
    """Reply to a specific Gmail message."""
    try:
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        service = get_gmail_service()
        if not service:
            return "Unable to connect to Gmail service"
        
        # Get original message
        original = service.users().messages().get(
            userId='me', 
            id=message_id, 
            format='full'
        ).execute()
        
        # Extract reply information
        headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}
        thread_id = original.get('threadId')
        
        from_email = headers.get('From', '')
        subject = headers.get('Subject', '')
        if not subject.lower().startswith('re:'):
            subject = 'Re: ' + subject
        
        # Create reply
        from email.mime.text import MIMEText
        import base64
        
        message = MIMEText(reply_body)
        message['to'] = from_email
        message['subject'] = subject
        message['In-Reply-To'] = headers.get('Message-ID', '')
        message['References'] = headers.get('Message-ID', '')
        
        # Send reply
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent_reply = service.users().messages().send(
            userId='me',
            body={'raw': raw_message, 'threadId': thread_id}
        ).execute()
        
        return f"Reply sent to {from_email}"
        
    except Exception as e:
        logger.error(f"Error replying to message {message_id}: {e}")
        return f"Error sending reply: {str(e)}"


# =============================================================================
# Gmail Organization Tools
# =============================================================================

def gmail_mark_as_read(message_id: str, tool_context=None) -> str:
    """Mark a Gmail message as read."""
    try:
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        service = get_gmail_service()
        if not service:
            return "Unable to connect to Gmail service"
        
        # Remove UNREAD label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        return f"Message marked as read"
        
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")
        return f"Error marking as read: {str(e)}"


def gmail_archive_message(message_id: str, tool_context=None) -> str:
    """Archive a Gmail message."""
    try:
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        service = get_gmail_service()
        if not service:
            return "Unable to connect to Gmail service"
        
        # Remove INBOX label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        
        return f"Message archived successfully"
        
    except Exception as e:
        logger.error(f"Error archiving message: {e}")
        return f"Error archiving message: {str(e)}"


def gmail_delete_message(message_id: str, tool_context=None) -> str:
    """Delete a Gmail message."""
    try:
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        service = get_gmail_service()
        if not service:
            return "Unable to connect to Gmail service"
        
        # Move to trash
        service.users().messages().trash(
            userId='me',
            id=message_id
        ).execute()
        
        return f"Message moved to trash"
        
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        return f"Error deleting message: {str(e)}"


# =============================================================================
# Helper Functions
# =============================================================================

def _extract_message_body(payload: Dict[str, Any]) -> str:
    """Extract text body from Gmail message payload."""
    try:
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        import base64
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        
        # Handle single part messages
        elif payload['mimeType'] == 'text/plain':
            data = payload['body'].get('data', '')
            if data:
                import base64
                return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return "Unable to extract message content"
        
    except Exception as e:
        logger.warning(f"Error extracting message body: {e}")
        return "Error reading message content"


# =============================================================================
# Create ADK Function Tools
# =============================================================================

# Connection tools
gmail_check_connection_tool = FunctionTool(func=gmail_check_connection)
gmail_authenticate_tool = FunctionTool(func=gmail_authenticate)

# Reading tools
gmail_list_messages_tool = FunctionTool(func=gmail_list_messages)
gmail_get_message_tool = FunctionTool(func=gmail_get_message)
gmail_search_messages_tool = FunctionTool(func=gmail_search_messages)

# Sending tools
gmail_send_message_tool = FunctionTool(func=gmail_send_message)
gmail_reply_to_message_tool = FunctionTool(func=gmail_reply_to_message)

# Organization tools
gmail_mark_as_read_tool = FunctionTool(func=gmail_mark_as_read)
gmail_archive_message_tool = FunctionTool(func=gmail_archive_message)
gmail_delete_message_tool = FunctionTool(func=gmail_delete_message)

# Gmail tools collection
GMAIL_TOOLS = [
    gmail_check_connection_tool,
    gmail_authenticate_tool,
    gmail_list_messages_tool,
    gmail_get_message_tool,
    gmail_search_messages_tool,
    gmail_send_message_tool,
    gmail_reply_to_message_tool,
    gmail_mark_as_read_tool,
    gmail_archive_message_tool,
    gmail_delete_message_tool
]

# Export for easy access
__all__ = [
    "gmail_check_connection",
    "gmail_authenticate", 
    "gmail_list_messages",
    "gmail_get_message",
    "gmail_search_messages",
    "gmail_send_message",
    "gmail_reply_to_message",
    "gmail_mark_as_read",
    "gmail_archive_message",
    "gmail_delete_message",
    "GMAIL_TOOLS"
]


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing Direct Gmail Tools...")
    
    # Mock tool context for testing
    class MockSession:
        def __init__(self):
            self.state = {USER_GMAIL_CONNECTED: False}
    
    class MockToolContext:
        def __init__(self):
            self.session = MockSession()
    
    mock_context = MockToolContext()
    
    # Test connection check
    result = gmail_check_connection(mock_context)
    print(f"Connection check: {result}")
    
    print("✅ Direct Gmail tools created successfully!")