"""
Simplified Gmail Tools for ADK - Direct Service Access

Simple ADK-compatible tools that use Gmail API directly through auth_utils.
No complex connection state management - each tool checks service availability directly.
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
from oprina.services.logging.logger import setup_logger
from google import genai

# Import simplified auth utils
from oprina.tools.auth_utils import get_gmail_service

# Import ADK utility functions
from oprina.common.utils import (
    validate_tool_context, update_agent_activity, log_tool_execution
)

# Import session state constants
from oprina.common.session_keys import (
    USER_EMAIL,
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_LAST_QUERY, 
    EMAIL_RESULTS_COUNT, EMAIL_LAST_SENT_TO, EMAIL_LAST_SENT,
    EMAIL_LAST_MESSAGE_VIEWED, EMAIL_LAST_MESSAGE_VIEWED_AT,
    EMAIL_LAST_SENT_SUBJECT, EMAIL_LAST_SENT_ID,
    EMAIL_LAST_REPLY_SENT, EMAIL_LAST_REPLY_TO, EMAIL_LAST_REPLY_ID, EMAIL_LAST_REPLY_THREAD,
    EMAIL_LAST_MARKED_READ, EMAIL_LAST_MARKED_READ_AT,
    EMAIL_LAST_ARCHIVED, EMAIL_LAST_ARCHIVED_AT,
    EMAIL_LAST_DELETED, EMAIL_LAST_DELETED_AT,
    # AI keys
    EMAIL_LAST_AI_SUMMARY, EMAIL_LAST_AI_SUMMARY_AT,
    EMAIL_LAST_SENTIMENT_ANALYSIS, EMAIL_LAST_SENTIMENT_ANALYSIS_AT,
    EMAIL_LAST_EXTRACTED_TASKS, EMAIL_LAST_TASK_EXTRACTION_AT,
    EMAIL_LAST_GENERATED_REPLY, EMAIL_LAST_REPLY_GENERATION_AT,
    EMAIL_PENDING_SEND, EMAIL_PENDING_REPLY,
    EMAIL_LAST_GENERATED_EMAIL, EMAIL_LAST_EMAIL_GENERATION_AT, EMAIL_LAST_GENERATED_EMAIL_TO,
    EMAIL_LAST_LISTED_MESSAGES, EMAIL_MESSAGE_INDEX_MAP
)

logger = setup_logger("gmail_tools", console_output=True)

# =============================================================================
# Gmail Email Reading Tools
# =============================================================================

def gmail_list_messages(query: str = "", max_results: int = 10, tool_context=None) -> str:
    """List Gmail messages with optional search query."""
    validate_tool_context(tool_context, "gmail_list_message")
    
    try:
        # Log operation start
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", True, 
                         f"Query: '{query}', Max results: {max_results}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "listing_messages")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
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
            tool_context.state[EMAIL_LAST_FETCH] = datetime.utcnow().isoformat()
            tool_context.state[EMAIL_LAST_QUERY] = query
            tool_context.state[EMAIL_RESULTS_COUNT] = 0
            tool_context.state[EMAIL_CURRENT_RESULTS] = []
            
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
        
        # Update session state with results including message ID mapping
        tool_context.state[EMAIL_LAST_FETCH] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_QUERY] = query
        tool_context.state[EMAIL_RESULTS_COUNT] = len(message_summaries)
        tool_context.state[EMAIL_CURRENT_RESULTS] = message_summaries
        
        # Store message ID mapping for easy reference by agents
        message_index_map = {}
        for i, msg in enumerate(message_summaries, 1):
            message_index_map[str(i)] = msg['id']
        
        tool_context.state[EMAIL_MESSAGE_INDEX_MAP] = message_index_map
        tool_context.state[EMAIL_LAST_LISTED_MESSAGES] = message_summaries
        
        # Format response with clear position indicators
        response_lines = [f"Found {len(message_summaries)} messages:"]
        for i, msg in enumerate(message_summaries[:5], 1):  # Show first 5
            from_display = msg['from'][:30] + "..." if len(msg['from']) > 30 else msg['from']
            subject_display = msg['subject'][:40] + "..." if len(msg['subject']) > 40 else msg['subject']
            response_lines.append(f"{i}. From: {from_display} | Subject: {subject_display}")
        
        if len(message_summaries) > 5:
            response_lines.append(f"... and {len(message_summaries) - 5} more messages")
        
        response_lines.append("\nTo read any email, say 'read email 1' or 'read the email from [sender name]'")
        
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", True, 
                         f"Retrieved {len(message_summaries)} messages")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing Gmail messages: {e}")
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", False, str(e))
        return f"Error retrieving emails: {str(e)}"


def gmail_get_message(message_id: str, tool_context=None) -> str:
    """Get detailed content of a specific Gmail message."""
    validate_tool_context(tool_context, "gmail_get_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_get_message", "get_message", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "getting_message")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(
                userId='me', 
                id=actual_message_id, 
                format='full'
            ).execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        # Extract headers
        headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
        
        # Extract body
        body = _extract_message_body(message.get('payload', {}))
        
        # Update session state
        tool_context.state[EMAIL_LAST_MESSAGE_VIEWED] = actual_message_id
        tool_context.state[EMAIL_LAST_MESSAGE_VIEWED_AT] = datetime.utcnow().isoformat()
        
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
    """Search Gmail messages using Gmail search syntax."""
    validate_tool_context(tool_context, "gmail_search_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_search_messages", "search_messages", True, f"Search: '{search_query}'")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "searching_messages")
        
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
    """Send a Gmail message."""
    validate_tool_context(tool_context, "gmail_send_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_send_message", "send_message", True, 
                         f"To: {to}, Subject: '{subject}', CC: {cc}, BCC: {bcc}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "sending_message")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Get sender email from session or profile
        sender_email = tool_context.state.get(USER_EMAIL, "")
        if not sender_email:
            try:
                profile = service.users().getProfile(userId='me').execute()
                sender_email = profile.get('emailAddress', '')
                tool_context.state[USER_EMAIL] = sender_email
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
        tool_context.state[EMAIL_LAST_SENT] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_SENT_TO] = to
        tool_context.state[EMAIL_LAST_SENT_SUBJECT] = subject
        tool_context.state[EMAIL_LAST_SENT_ID] = sent_message.get('id', '')
        
        log_tool_execution(tool_context, "gmail_send_message", "send_message", True, "Email sent successfully")
        return f"Email sent successfully to {to}. Subject: {subject}"
        
    except Exception as e:
        logger.error(f"Error sending Gmail message: {e}")
        log_tool_execution(tool_context, "gmail_send_message", "send_message", False, str(e))
        return f"Error sending email: {str(e)}"


def gmail_reply_to_message(message_id: str, reply_body: str, tool_context=None) -> str:
    """Reply to a specific Gmail message."""
    validate_tool_context(tool_context, "gmail_reply_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", True, 
                         f"Reply to message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "replying_to_message")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            original = service.users().messages().get(
                userId='me', 
                id=actual_message_id, 
                format='full'
            ).execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
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
        tool_context.state[EMAIL_LAST_REPLY_SENT] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_REPLY_TO] = from_email
        tool_context.state[EMAIL_LAST_REPLY_ID] = sent_reply.get('id', '')
        tool_context.state[EMAIL_LAST_REPLY_THREAD] = thread_id
        
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", True, f"Reply sent to {from_email}")
        return f"Reply sent to {from_email}"
        
    except Exception as e:
        logger.error(f"Error replying to message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", False, str(e))
        return f"Error sending reply: {str(e)}"

def gmail_confirm_and_send(to: str, subject: str, body: str, cc: str = "", bcc: str = "", 
                          tool_context=None) -> str:
    """Prepare email for confirmation before sending."""
    validate_tool_context(tool_context, "gmail_confirm_and_send")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_confirm_and_send", "prepare_send", True, f"To: {to}")
        
        # Store pending email in session state for agent to handle confirmation
        pending_email = {
            'to': to,
            'subject': subject, 
            'body': body,
            'cc': cc,
            'bcc': bcc,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        tool_context.state[EMAIL_PENDING_SEND] = pending_email
        
        # Format confirmation message for agent
        confirmation_text = f"""Ready to send email:
To: {to}
{f'CC: {cc}' if cc else ''}
{f'BCC: {bcc}' if bcc else ''}
Subject: {subject}

Body:
{body}

[Agent should ask user for confirmation before calling gmail_send_message]"""
        
        log_tool_execution(tool_context, "gmail_confirm_and_send", "prepare_send", True, "Email prepared for confirmation")
        return confirmation_text
        
    except Exception as e:
        logger.error(f"Error preparing email for confirmation: {e}")
        log_tool_execution(tool_context, "gmail_confirm_and_send", "prepare_send", False, str(e))
        return f"Error preparing email: {str(e)}"


def gmail_confirm_and_reply(message_id: str, reply_body: str, tool_context=None) -> str:
    """Prepare reply for confirmation before sending."""
    validate_tool_context(tool_context, "gmail_confirm_and_reply")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_confirm_and_reply", "prepare_reply", True, f"Message: {message_id}")
        
        # Get original message info for context
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
            
        original = service.users().messages().get(userId='me', id=message_id, format='metadata').execute()
        headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}
        
        # Store pending reply in session state
        pending_reply = {
            'message_id': message_id,
            'reply_body': reply_body,
            'original_from': headers.get('From', 'Unknown'),
            'original_subject': headers.get('Subject', 'No Subject'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        tool_context.state[EMAIL_PENDING_REPLY] = pending_reply
        
        # Format confirmation message for agent
        confirmation_text = f"""Ready to send reply:
To: {headers.get('From', 'Unknown')}
Subject: Re: {headers.get('Subject', 'No Subject')}

Reply:
{reply_body}

[Agent should ask user for confirmation before calling gmail_reply_to_message]"""
        
        log_tool_execution(tool_context, "gmail_confirm_and_reply", "prepare_reply", True, "Reply prepared for confirmation")
        return confirmation_text
        
    except Exception as e:
        logger.error(f"Error preparing reply for confirmation: {e}")
        log_tool_execution(tool_context, "gmail_confirm_and_reply", "prepare_reply", False, str(e))
        return f"Error preparing reply: {str(e)}"

# =============================================================================
# Gmail Organization Tools
# =============================================================================

def gmail_mark_as_read(message_id: str, tool_context=None) -> str:
    """Mark a Gmail message as read."""
    validate_tool_context(tool_context, "gmail_markread_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "marking_read")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # First try to use message_id directly (for actual Gmail IDs)
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            service.users().messages().modify(
                userId='me',
                id=actual_message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        # Update session state
        tool_context.state[EMAIL_LAST_MARKED_READ] = actual_message_id
        tool_context.state[EMAIL_LAST_MARKED_READ_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", True, "Message marked as read")
        return f"Message marked as read"
        
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", False, str(e))
        return f"Error marking as read: {str(e)}"


def gmail_archive_message(message_id: str, tool_context=None) -> str:
    """Archive a Gmail message."""
    validate_tool_context(tool_context, "gmail_archive_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_archive_message", "archive", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "archiving_message")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # First try to use message_id directly (for actual Gmail IDs)
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            service.users().messages().modify(
                userId='me',
                id=actual_message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        # Update session state
        tool_context.state[EMAIL_LAST_ARCHIVED] = actual_message_id
        tool_context.state[EMAIL_LAST_ARCHIVED_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_archive_message", "archive", True, "Message archived")
        return f"Message archived successfully"
        
    except Exception as e:
        logger.error(f"Error archiving message: {e}")
        log_tool_execution(tool_context, "gmail_archive_message", "archive", False, str(e))
        return f"Error archiving message: {str(e)}"

def gmail_delete_message(message_id: str, tool_context=None) -> str:
    """Delete a Gmail message."""
    validate_tool_context(tool_context, "gmail_delete_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_delete_message", "delete", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "deleting_message")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # First try to use message_id directly (for actual Gmail IDs)
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            service.users().messages().trash(
                userId='me',
                id=actual_message_id
            ).execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        # Update session state
        tool_context.state[EMAIL_LAST_DELETED] = actual_message_id
        tool_context.state[EMAIL_LAST_DELETED_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_delete_message", "delete", True, "Message moved to trash")
        return f"Message moved to trash"
        
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        log_tool_execution(tool_context, "gmail_delete_message", "delete", False, str(e))
        return f"Error deleting message: {str(e)}"

# =============================================================================
# AI Shared tools Functions
# =============================================================================

def _process_with_ai(content: str, task_type: str, **kwargs) -> str:
    """Shared AI processing function for all email content tasks"""
    try:
        # Initialize Gemini client
        client = genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        )
        
        # Build prompt based on task type
        prompts = {
            "summarize": f"Summarize this email content in a clear, concise way:\n\n{content}",
            "sentiment": f"Analyze the sentiment and tone of this email. Identify if it's positive, negative, or neutral, and note the formality level:\n\n{content}",
            "tasks": f"Extract any action items, tasks, or follow-ups mentioned in this email. List them clearly:\n\n{content}",
            "reply": f"Generate a {kwargs.get('style', 'professional')} email reply to this message. Reply intent: {kwargs.get('intent', '')}\n\nOriginal email:\n{content}",
            "compose": f"Generate a {kwargs.get('style', 'professional')} email with the following requirements:\n\n{content}\n\nPlease provide both a subject line and email body. Format as:\nSubject: [subject line]\n\n[email body]"
        }
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompts.get(task_type, f"Process this email content:\n{content}")
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"AI processing failed for task {task_type}: {e}")
        return f"AI processing temporarily unavailable. Error: {str(e)}"


def gmail_generate_email(to: str, subject_intent: str, email_intent: str, 
                        style: str = "professional", context: str = "", tool_context=None) -> str:
    """Generate a complete email using AI for composition (not replies)."""
    validate_tool_context(tool_context, "gmail_generate_email")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_generate_email", "ai_compose_email", True, 
                         f"To: {to}, Intent: {email_intent}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_composing_email")
        
        # Build composition requirements for AI
        composition_requirements = f"""
        Recipient: {to}
        Subject intent: {subject_intent}
        Email purpose: {email_intent}
        {f'Additional context: {context}' if context else ''}
        
        Create an appropriate email for this communication.
        """
        
        # Use AI to generate email with "compose" task type
        email_content = _process_with_ai(composition_requirements, "compose", style=style)
        
        # Update session state
        tool_context.state[EMAIL_LAST_GENERATED_EMAIL] = email_content
        tool_context.state[EMAIL_LAST_EMAIL_GENERATION_AT] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_GENERATED_EMAIL_TO] = to
        
        log_tool_execution(tool_context, "gmail_generate_email", "ai_compose_email", True, "Email composition completed")
        return email_content
        
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        log_tool_execution(tool_context, "gmail_generate_email", "ai_compose_email", False, str(e))
        return f"Error generating email: {str(e)}"

def gmail_summarize_message(message_id: str, detail_level: str = "moderate", tool_context=None) -> str:
    """Summarize a specific Gmail message using AI."""
    validate_tool_context(tool_context, "gmail_summarize_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_summarize_message", "ai_summarize", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_summarizing_message")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(userId='me', id=actual_message_id, format='full').execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        body = _extract_message_body(message.get('payload', {}))
        
        if not body:
            return "Could not extract message content for summarization"
        
        # Use AI to summarize
        summary = _process_with_ai(body, "summarize")
        
        # Update session state using proper keys
        tool_context.state[EMAIL_LAST_AI_SUMMARY] = summary
        tool_context.state[EMAIL_LAST_AI_SUMMARY_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_summarize_message", "ai_summarize", True, "AI summary completed")
        return summary
        
    except Exception as e:
        logger.error(f"Error summarizing message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_summarize_message", "ai_summarize", False, str(e))
        return f"Error summarizing message: {str(e)}"


def gmail_analyze_sentiment(message_id: str, tool_context=None) -> str:
    """Analyze sentiment of a Gmail message using AI."""
    validate_tool_context(tool_context, "gmail_analyze_sentiment")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_analyze_sentiment", "ai_sentiment", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_analyzing_sentiment")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # First try to use message_id directly (for actual Gmail IDs)
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(userId='me', id=actual_message_id, format='full').execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        body = _extract_message_body(message.get('payload', {}))
        
        if not body:
            return "Could not extract message content for sentiment analysis"
        
        # Use AI to analyze sentiment
        analysis = _process_with_ai(body, "sentiment")
        
        # Update session state using proper keys
        tool_context.state[EMAIL_LAST_SENTIMENT_ANALYSIS] = analysis
        tool_context.state[EMAIL_LAST_SENTIMENT_ANALYSIS_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_analyze_sentiment", "ai_sentiment", True, "AI sentiment analysis completed")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment for message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_analyze_sentiment", "ai_sentiment", False, str(e))
        return f"Error analyzing sentiment: {str(e)}"


def gmail_extract_action_items(message_id: str, tool_context=None) -> str:
    """Extract action items from a Gmail message using AI."""
    validate_tool_context(tool_context, "gmail_extract_action_items")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_extract_action_items", "ai_extract_tasks", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_extracting_tasks")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(userId='me', id=actual_message_id, format='full').execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        body = _extract_message_body(message.get('payload', {}))
        
        if not body:
            return "Could not extract message content for task extraction"
        
        # Use AI to extract tasks
        tasks = _process_with_ai(body, "tasks")
        
        # Update session state using proper keys
        tool_context.state[EMAIL_LAST_EXTRACTED_TASKS] = tasks
        tool_context.state[EMAIL_LAST_TASK_EXTRACTION_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_extract_action_items", "ai_extract_tasks", True, "AI task extraction completed")
        return tasks
        
    except Exception as e:
        logger.error(f"Error extracting tasks from message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_extract_action_items", "ai_extract_tasks", False, str(e))
        return f"Error extracting action items: {str(e)}"


def gmail_generate_reply(message_id: str, reply_intent: str, style: str = "professional", tool_context=None) -> str:
    """Generate AI reply to a Gmail message."""
    validate_tool_context(tool_context, "gmail_generate_reply")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_generate_reply", "ai_generate_reply", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_generating_reply")
        
        # Get Gmail service
        service = get_gmail_service(tool_context)
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(userId='me', id=actual_message_id, format='full').execute()
        except Exception as e:
            return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        body = _extract_message_body(message.get('payload', {}))
        
        if not body:
            return "Could not extract message content for reply generation"
        
        # Use AI to generate reply
        reply = _process_with_ai(body, "reply", intent=reply_intent, style=style)
        
        # Update session state using proper keys
        tool_context.state[EMAIL_LAST_GENERATED_REPLY] = reply
        tool_context.state[EMAIL_LAST_REPLY_GENERATION_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_generate_reply", "ai_generate_reply", True, "AI reply generation completed")
        return reply
        
    except Exception as e:
        logger.error(f"Error generating reply for message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_generate_reply", "ai_generate_reply", False, str(e))
        return f"Error generating reply: {str(e)}"
    
# =============================================================================
# Helper Functions
# =============================================================================

def _get_message_id_by_reference(reference: str, tool_context=None) -> Optional[str]:
    """Get message ID by user reference (position, sender, subject partial match)."""
    # Follow the same validation pattern as other functions
    validate_tool_context(tool_context, "_get_message_id_by_reference")
    
    try:
        # Log operation start (following your logging pattern)
        log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True, 
                         f"Reference: '{reference}'")
        
        # Check if tool_context and state are available (following your safety pattern)
        if not tool_context or not hasattr(tool_context, 'state'):
            logger.warning("No tool context or state available for message ID lookup")
            log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", False, 
                             "No tool context or state available")
            return None
            
        # Get stored message data from session state (using your session key constants)
        message_index_map = tool_context.state.get(EMAIL_MESSAGE_INDEX_MAP, {})
        last_listed_messages = tool_context.state.get(EMAIL_LAST_LISTED_MESSAGES, [])
        
        if not message_index_map or not last_listed_messages:
            logger.warning("No message index map or listed messages found in session state")
            log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", False,
                             "No message data in session state")
            return None
        
        # Try to parse as position number (1, 2, 3, etc.)
        try:
            position = int(reference)
            if str(position) in message_index_map:
                resolved_id = message_index_map[str(position)]
                logger.debug(f"Found message ID by position {position}: {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved position {position} to ID {resolved_id}")
                return resolved_id
        except ValueError:
            pass  # Not a number, continue with other methods
        
        # Try to match by sender (partial match, case insensitive)
        reference_lower = reference.lower()
        for msg in last_listed_messages:
            sender = msg.get('from', '').lower()
            if reference_lower in sender:
                resolved_id = msg.get('id')
                logger.debug(f"Found message ID by sender match: {reference} -> {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved sender '{reference}' to ID {resolved_id}")
                return resolved_id
        
        # Try to match by subject (partial match, case insensitive)
        for msg in last_listed_messages:
            subject = msg.get('subject', '').lower()
            if reference_lower in subject:
                resolved_id = msg.get('id')
                logger.debug(f"Found message ID by subject match: {reference} -> {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved subject '{reference}' to ID {resolved_id}")
                return resolved_id
        
        # No match found
        logger.warning(f"Could not resolve message reference: {reference}")
        log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", False,
                         f"Could not resolve reference: {reference}")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving message reference '{reference}': {e}")
        log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", False, str(e))
        return None

def gmail_parse_subject_and_body(ai_generated_content: str, tool_context=None) -> str:
    """Parse AI-generated email content into subject and body components and return formatted result."""
    validate_tool_context(tool_context, "gmail_parse_email_content")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_parse_subject_and_body", "parse_content", True, "Parsing AI content")
        
        lines = ai_generated_content.strip().split('\n')
        subject = ""
        body = ""
        
        # Look for subject line
        for i, line in enumerate(lines):
            if line.lower().startswith('subject:'):
                subject = line[8:].strip()  # Remove "Subject:" prefix
                # Body starts after subject line (skip empty lines)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():  # First non-empty line after subject
                        body = '\n'.join(lines[j:]).strip()
                        break
                break
        
        # Fallback if no "Subject:" found - treat first line as subject
        if not subject and lines:
            subject = lines[0].strip()
            if len(lines) > 1:
                body = '\n'.join(lines[1:]).strip()
        
        # Clean up subject and body
        subject = subject.strip('"\'')  # Remove quotes if present
        
        # Return parsed content as formatted string instead of tuple
        parsed_result = f"PARSED_SUBJECT: {subject}\nPARSED_BODY: {body}"
        
        log_tool_execution(tool_context, "gmail_parse_subject_and_body", "parse_content", True, 
                         f"Parsed - Subject: '{subject[:50]}...', Body length: {len(body)}")
        
        return parsed_result
        
    except Exception as e:
        logger.error(f"Error parsing AI content: {e}")
        log_tool_execution(tool_context, "gmail_parse_subject_and_body", "parse_content", False, str(e))
        return f"PARSED_SUBJECT: Email Subject\nPARSED_BODY: {ai_generated_content}"  # Fallback


def _extract_message_body(payload: Dict[str, Any]) -> str:
    """Extract text body from Gmail message payload."""
    try:
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':  # Added .get() for safety
                    data = part.get('body', {}).get('data', '')
                    if data:
                        import base64
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        
        # Handle single part messages
        elif payload.get('mimeType') == 'text/plain':  # Added .get() for safety
            data = payload.get('body', {}).get('data', '')
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

# AI-powered content tools
gmail_summarize_message_tool = FunctionTool(func=gmail_summarize_message)
gmail_analyze_sentiment_tool = FunctionTool(func=gmail_analyze_sentiment)
gmail_extract_action_items_tool = FunctionTool(func=gmail_extract_action_items)
gmail_generate_reply_tool = FunctionTool(func=gmail_generate_reply)

# NEW AI composition and workflow tools
gmail_generate_email_tool = FunctionTool(func=gmail_generate_email)
gmail_parse_subject_and_body_tool = FunctionTool(func=gmail_parse_subject_and_body)
gmail_confirm_and_send_tool = FunctionTool(func=gmail_confirm_and_send)
gmail_confirm_and_reply_tool = FunctionTool(func=gmail_confirm_and_reply)

# Gmail tools collection
GMAIL_TOOLS = [
    # Reading tools
    gmail_list_messages_tool,
    gmail_get_message_tool,
    gmail_search_messages_tool,
    
    # Sending tools
    gmail_send_message_tool,
    gmail_reply_to_message_tool,
    
    # Organization tools
    gmail_mark_as_read_tool,
    gmail_archive_message_tool,
    gmail_delete_message_tool,
    
    # AI-powered content tools
    gmail_summarize_message_tool,
    gmail_analyze_sentiment_tool,
    gmail_extract_action_items_tool,
    gmail_generate_reply_tool,
    
    # NEW AI composition and workflow tools
    gmail_generate_email_tool,
    gmail_parse_subject_and_body_tool,
    gmail_confirm_and_send_tool,
    gmail_confirm_and_reply_tool
]

# Export for easy access
__all__ = [
    # Reading functions
    "gmail_list_messages",
    "gmail_get_message",
    "gmail_search_messages",
    
    # Sending functions
    "gmail_send_message",
    "gmail_reply_to_message",
    
    # Organization functions
    "gmail_mark_as_read",
    "gmail_archive_message",
    "gmail_delete_message",
    
    # AI content processing functions
    "gmail_summarize_message",
    "gmail_analyze_sentiment", 
    "gmail_extract_action_items",
    "gmail_generate_reply",
    
    # NEW AI composition and workflow functions
    "gmail_generate_email",
    "gmail_parse_subject_and_body",
    "gmail_confirm_and_send",
    "gmail_confirm_and_reply",
    
    # Tools collection
    "GMAIL_TOOLS"
]