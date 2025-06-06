"""
Direct Gmail Tools for ADK - Complete ADK Integration

Simple ADK-compatible tools that use Gmail API directly through existing auth services.
Now with proper tool_context validation, session state management, and comprehensive logging.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from oprina.tools.auth_utils import ensure_gmail_connection
from services.logging.logger import setup_logger

from oprina.common.utils import (
    validate_tool_context, update_agent_activity, log_tool_execution
)

from oprina.common.session_keys import (
    USER_GMAIL_CONNECTED, USER_EMAIL,
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_LAST_QUERY, 
    EMAIL_RESULTS_COUNT, EMAIL_LAST_SENT_TO, EMAIL_LAST_SENT,
    EMAIL_LAST_MESSAGE_VIEWED, EMAIL_LAST_MESSAGE_VIEWED_AT,
    EMAIL_LAST_SENT_SUBJECT, EMAIL_LAST_SENT_ID,
    EMAIL_LAST_REPLY_SENT, EMAIL_LAST_REPLY_TO, EMAIL_LAST_REPLY_ID, EMAIL_LAST_REPLY_THREAD,
    EMAIL_LAST_MARKED_READ, EMAIL_LAST_MARKED_READ_AT,
    EMAIL_LAST_ARCHIVED, EMAIL_LAST_ARCHIVED_AT,
    EMAIL_LAST_DELETED, EMAIL_LAST_DELETED_AT
)
logger = setup_logger("gmail_tools", console_output=True)


def gmail_check_connection(tool_context=None) -> str:
    """Check Gmail connection status - UPDATED VERSION."""
    if not validate_tool_context(tool_context, "gmail_check_connection"):
        return "Error: No valid tool context provided"
    
    try:
        log_tool_execution(tool_context, "gmail_check_connection", "status_check", True, "Checking Gmail connection")
        update_agent_activity(tool_context, "email_agent", "checking_connection")
        
        # NEW PATTERN - Use central auth utils
        success, message, service = ensure_gmail_connection(tool_context, "gmail_check_connection")
        
        if success:
            
            return f"Gmail connected successfully. {message}"
        else:
            return f"Gmail connection issue: {message}"
            
    except Exception as e:
        logger.error(f"Error checking Gmail connection: {e}")
        return f"Error checking Gmail connection: {str(e)}"

def gmail_authenticate(tool_context=None) -> str:
    """Authenticate with Gmail - UPDATED VERSION."""
    if not validate_tool_context(tool_context, "gmail_authenticate"):
        return "Error: No valid tool context provided"
    
    try:
        log_tool_execution(tool_context, "gmail_authenticate", "authenticate", True, "Starting Gmail authentication")
        update_agent_activity(tool_context, "email_agent", "authenticating")
        
        # NEW PATTERN - Use central auth utils instead of direct service calls
        success, message, service = ensure_gmail_connection(tool_context, "gmail_authenticate")
        
        if success:
            log_tool_execution(tool_context, "gmail_authenticate", "authenticate", True, "Gmail authenticated successfully")
            return f"Gmail authentication successful! {message}"
        else:
            log_tool_execution(tool_context, "gmail_authenticate", "authenticate", False, message)
            return f"Gmail authentication failed: {message}"
            
    except Exception as e:
        logger.error(f"Gmail authentication error: {e}")
        return f"Gmail authentication failed: {str(e)}"


# =============================================================================
# Gmail Email Reading Tools
# =============================================================================

def gmail_list_messages(query: str = "", max_results: int = 10, tool_context=None) -> str:
    """List Gmail messages with optional search query and full ADK integration."""
    if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation start
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", True, 
                         f"Query: '{query}', Max results: {max_results}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "listing_messages")
        
        
        # Get Gmail service
        success, message, service = ensure_gmail_connection(tool_context, "gmail_list_messages")
        if not service:
            log_tool_execution(tool_context, "gmail_list_messages", "list_messages", False, "Gmail service unavailable")
            return "Unable to connect to Gmail service"
        
        # List messages
        result = service.users().messages().list(
            userId='me', 
            q=query, 
            maxResults=max_results
        ).execute()
        
        messages = result.get('messages', [])
        
        if not messages:
            response = f"No messages found{' for query: ' + query if query else ''}"
            
            # Update session state even for empty results
            tool_context.session.state[EMAIL_LAST_FETCH] = datetime.utcnow().isoformat()
            tool_context.session.state[EMAIL_LAST_QUERY] = query
            tool_context.session.state[EMAIL_RESULTS_COUNT] = 0
            tool_context.session.state[EMAIL_CURRENT_RESULTS] = []
            
            return response
        
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
        
        # Update session state with results
        tool_context.session.state[EMAIL_LAST_FETCH] = datetime.utcnow().isoformat()
        tool_context.session.state[EMAIL_LAST_QUERY] = query
        tool_context.session.state[EMAIL_RESULTS_COUNT] = len(message_summaries)
        tool_context.session.state[EMAIL_CURRENT_RESULTS] = message_summaries
        
        # Format response
        response_lines = [f"Found {len(message_summaries)} messages:"]
        for i, msg in enumerate(message_summaries[:5], 1):  # Show first 5
            from_display = msg['from'][:30] + "..." if len(msg['from']) > 30 else msg['from']
            subject_display = msg['subject'][:40] + "..." if len(msg['subject']) > 40 else msg['subject']
            response_lines.append(f"{i}. From: {from_display} | Subject: {subject_display}")
        
        if len(message_summaries) > 5:
            response_lines.append(f"... and {len(message_summaries) - 5} more messages")
        
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", True, 
                         f"Retrieved {len(message_summaries)} messages")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing Gmail messages: {e}")
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", False, str(e))
        return f"Error retrieving emails: {str(e)}"


def gmail_get_message(message_id: str, tool_context=None) -> str:
    """Get detailed content of a specific Gmail message with ADK integration."""
    if not validate_tool_context(tool_context, "gmail_get_message"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_get_message", "get_message", True, f"Message ID: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "getting_message")
        
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        success, message, service = ensure_gmail_connection(tool_context, "gmail_send_messages")
        if not service:
            log_tool_execution(tool_context, "gmail_get_message", "get_message", False, "Gmail service unavailable")
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
        
        # Update session state
        tool_context.session.state[EMAIL_LAST_MESSAGE_VIEWED] = message_id
        tool_context.session.state[EMAIL_LAST_MESSAGE_VIEWED_AT] = datetime.utcnow().isoformat()
        
        # Format response
        response = f"""Email Details:
From: {headers.get('From', 'Unknown')}
To: {headers.get('To', 'Unknown')}
Subject: {headers.get('Subject', 'No Subject')}
Date: {headers.get('Date', 'Unknown')}

Content:
{body[:500]}{'...' if len(body) > 500 else ''}"""
        
        log_tool_execution(tool_context, "gmail_get_message", "get_message", True, "Message retrieved successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error getting Gmail message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_get_message", "get_message", False, str(e))
        return f"Error retrieving email: {str(e)}"


def gmail_search_messages(search_query: str, max_results: int = 10, tool_context=None) -> str:
    """Search Gmail messages using Gmail search syntax with ADK integration."""
    if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_search_messages", "search_messages", True, f"Search: '{search_query}'")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "searching_messages")
        
        success, message, service = ensure_gmail_connection(tool_context, "gmail_search_messages")
        
        # Use the list_messages function with search query
        return gmail_list_messages(query=search_query, max_results=max_results, tool_context=tool_context)
        
    except Exception as e:
        logger.error(f"Error searching Gmail: {e}")
        log_tool_execution(tool_context, "gmail_search_messages", "search_messages", False, str(e))
        return f"Error searching emails: {str(e)}"


# =============================================================================
# Gmail Sending Tools
# =============================================================================

def gmail_send_message(to: str, subject: str, body: str, cc: str = "", bcc: str = "", tool_context=None) -> str:
    """Send a Gmail message with comprehensive ADK integration."""
    if not validate_tool_context(tool_context, "gmail_send_message"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_send_message", "send_message", True, 
                         f"To: {to}, Subject: '{subject}', CC: {cc}, BCC: {bcc}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "sending_message")
        
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        success, message1, service = ensure_gmail_connection(tool_context, "gmail_send_messages")
        if not service:
            log_tool_execution(tool_context, "gmail_send_message", "send_message", False, "Gmail service unavailable")
            return "Unable to connect to Gmail service"
        
        # Get sender email from session or profile
        sender_email = tool_context.session.state.get(USER_EMAIL, "")
        if not sender_email:
            try:
                profile = service.users().getProfile(userId='me').execute()
                sender_email = profile.get('emailAddress', '')
                tool_context.session.state["user:email"] = sender_email
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
        
        # Update session state after successful send
        tool_context.session.state[EMAIL_LAST_SENT] = datetime.utcnow().isoformat()
        tool_context.session.state[EMAIL_LAST_SENT_TO] = to
        tool_context.session.state[EMAIL_LAST_SENT_SUBJECT] = subject
        tool_context.session.state[EMAIL_LAST_SENT_ID] = sent_message.get('id', '')
        
        log_tool_execution(tool_context, "gmail_send_message", "send_message", True, "Email sent successfully")
        return f"Email sent successfully to {to}. Subject: {subject}"
        
    except Exception as e:
        logger.error(f"Error sending Gmail message: {e}")
        log_tool_execution(tool_context, "gmail_send_message", "send_message", False, str(e))
        return f"Error sending email: {str(e)}"


def gmail_reply_to_message(message_id: str, reply_body: str, tool_context=None) -> str:
    """Reply to a specific Gmail message with ADK integration."""
    if not validate_tool_context(tool_context, "gmail_reply_to_message"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", True, 
                         f"Reply to message: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "replying_to_message")
        
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        success, message1, service = ensure_gmail_connection(tool_context, "gmail_list_messages")
        if not service:
            log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", False, "Gmail service unavailable")
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
        
        # Update session state
        tool_context.session.state[EMAIL_LAST_REPLY_SENT] = datetime.utcnow().isoformat()
        tool_context.session.state[EMAIL_LAST_REPLY_TO] = from_email
        tool_context.session.state[EMAIL_LAST_REPLY_ID] = sent_reply.get('id', '')
        tool_context.session.state[EMAIL_LAST_REPLY_THREAD] = thread_id
        
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", True, f"Reply sent to {from_email}")
        return f"Reply sent to {from_email}"
        
    except Exception as e:
        logger.error(f"Error replying to message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", False, str(e))
        return f"Error sending reply: {str(e)}"


# =============================================================================
# Gmail Organization Tools
# =============================================================================

def gmail_mark_as_read(message_id: str, tool_context=None) -> str:
    """Mark a Gmail message as read with ADK integration."""
    if not validate_tool_context(tool_context, "gmail_mark_as_read"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", True, f"Message: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "marking_read")
        
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        success, message, service = ensure_gmail_connection(tool_context, "gmail_list_messages")
        if not service:
            log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", False, "Gmail service unavailable")
            return "Unable to connect to Gmail service"
        
        # Remove UNREAD label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        # Update session state
        tool_context.session.state[EMAIL_LAST_MARKED_READ] = message_id
        tool_context.session.state[EMAIL_LAST_MARKED_READ_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", True, "Message marked as read")
        return f"Message marked as read"
        
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", False, str(e))
        return f"Error marking as read: {str(e)}"


def gmail_archive_message(message_id: str, tool_context=None) -> str:
    """Archive a Gmail message with ADK integration."""
    if not validate_tool_context(tool_context, "gmail_archive_message"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_archive_message", "archive", True, f"Message: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "archiving_message")
        
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        success, message, service = ensure_gmail_connection(tool_context, "gmail_list_messages")
        if not service:
            log_tool_execution(tool_context, "gmail_archive_message", "archive", False, "Gmail service unavailable")
            return "Unable to connect to Gmail service"
        
        # Remove INBOX label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        
        # Update session state
        tool_context.session.state[EMAIL_LAST_ARCHIVED] = message_id
        tool_context.session.state[EMAIL_LAST_ARCHIVED_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_archive_message", "archive", True, "Message archived")
        return f"Message archived successfully"
        
    except Exception as e:
        logger.error(f"Error archiving message: {e}")
        log_tool_execution(tool_context, "gmail_archive_message", "archive", False, str(e))
        return f"Error archiving message: {str(e)}"


def gmail_delete_message(message_id: str, tool_context=None) -> str:
    """Delete a Gmail message with ADK integration."""
    if not validate_tool_context(tool_context, "gmail_delete_message"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_delete_message", "delete", True, f"Message: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "deleting_message")
        
        if not tool_context.session.state.get(USER_GMAIL_CONNECTED, False):
            return "Gmail not connected. Please authenticate first."
        
        success, message, service = ensure_gmail_connection(tool_context, "gmail_list_messages")
        if not service:
            log_tool_execution(tool_context, "gmail_delete_message", "delete", False, "Gmail service unavailable")
            return "Unable to connect to Gmail service"
        
        # Move to trash
        service.users().messages().trash(
            userId='me',
            id=message_id
        ).execute()
        
        # Update session state
        tool_context.session.state[EMAIL_LAST_DELETED] = message_id
        tool_context.session.state[EMAIL_LAST_DELETED_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_delete_message", "delete", True, "Message moved to trash")
        return f"Message moved to trash"
        
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        log_tool_execution(tool_context, "gmail_delete_message", "delete", False, str(e))
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
