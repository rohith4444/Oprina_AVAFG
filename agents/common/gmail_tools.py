"""
Gmail Tools for ADK Integration

This module provides direct Gmail API tools that follow the ADK FunctionTool pattern.
These tools replace the MCP client approach with direct API calls.
"""

import os
import sys
import base64
import email
from typing import Optional, List, Dict, Any
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import project modules
from config.settings import settings
from services.google_cloud.gmail_auth import get_gmail_service, check_gmail_connection
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("gmail_tools", console_output=True)

# --- ADK Imports with Fallback ---
try:
    from google.adk.tools import FunctionTool
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    ADK_IMPORT_ERROR = "ADK not available, running in fallback mode"
    
    # Fallback implementation
    class FunctionTool:
        def __init__(self, func=None, **kwargs):
            self.func = func
            self.name = kwargs.get('name', func.__name__ if func else 'unknown')
            self.description = kwargs.get('description', '')
            self.parameters = kwargs.get('parameters', {})
            
        def __call__(self, *args, **kwargs):
            if self.func:
                return self.func(*args, **kwargs)
            return {"error": "Function not implemented"}

def gmail_check_connection(tool_context=None) -> str:
    """
    Check if Gmail is connected and authenticated.
    
    Args:
        tool_context: The tool context containing session information
        
    Returns:
        str: Connection status message
    """
    logger.info("Checking Gmail connection...")
    
    # Check connection using the Gmail auth service
    connection_status = check_gmail_connection()
    
    if connection_status.get("connected", False) and connection_status.get("api_test", False):
        user_email = connection_status.get("user_email", "Unknown")
        return f"Gmail is connected and authenticated for {user_email}."
    else:
        error = connection_status.get("error", "Unknown error")
        return f"Gmail is not connected. Error: {error}"

def gmail_authenticate(tool_context=None) -> str:
    """
    Authenticate with Gmail.
    
    Args:
        tool_context: The tool context containing session information
        
    Returns:
        str: Authentication status message
    """
    logger.info("Authenticating with Gmail...")
    
    # Get Gmail service (this will trigger OAuth flow if needed)
    service = get_gmail_service(force_refresh=True)
    
    if service:
        # Get user profile to confirm authentication
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress', 'Unknown')
        return f"Successfully authenticated with Gmail for {user_email}."
    else:
        return "Failed to authenticate with Gmail. Please try again."

def gmail_list_messages(tool_context=None, query: str = "", max_results: int = 10) -> Dict[str, Any]:
    """
    List Gmail messages.
    
    Args:
        tool_context: The tool context containing session information
        query: Gmail search query
        max_results: Maximum number of results to return
        
    Returns:
        Dict[str, Any]: List of messages
    """
    logger.info(f"Listing Gmail messages with query: {query}, max_results: {max_results}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # List messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {"messages": [], "count": 0}
        
        # Get message details
        message_list = []
        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            # Extract headers
            headers = msg.get('payload', {}).get('headers', [])
            headers_dict = {header['name']: header['value'] for header in headers}
            
            # Create message object
            message_obj = {
                'id': msg['id'],
                'threadId': msg['threadId'],
                'snippet': msg.get('snippet', ''),
                'from': headers_dict.get('From', ''),
                'to': headers_dict.get('To', ''),
                'subject': headers_dict.get('Subject', ''),
                'date': headers_dict.get('Date', ''),
                'is_read': 'UNREAD' not in msg.get('labelIds', [])
            }
            
            message_list.append(message_obj)
        
        return {
            "messages": message_list,
            "count": len(message_list)
        }
        
    except Exception as e:
        logger.error(f"Error listing Gmail messages: {e}")
        return {"error": f"Failed to list Gmail messages: {str(e)}"}

def gmail_get_message(tool_context=None, message_id: str) -> Dict[str, Any]:
    """
    Get a Gmail message.
    
    Args:
        tool_context: The tool context containing session information
        message_id: Message ID
        
    Returns:
        Dict[str, Any]: Message details
    """
    logger.info(f"Getting Gmail message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Get message
        msg = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = msg.get('payload', {}).get('headers', [])
        headers_dict = {header['name']: header['value'] for header in headers}
        
        # Extract body
        body = ""
        if 'parts' in msg.get('payload', {}):
            for part in msg['payload']['parts']:
                if part.get('mimeType') == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8')
                    break
        elif 'body' in msg.get('payload', {}) and 'data' in msg['payload']['body']:
            body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
        
        # Create message object
        message_obj = {
            'id': msg['id'],
            'threadId': msg['threadId'],
            'snippet': msg.get('snippet', ''),
            'from': headers_dict.get('From', ''),
            'to': headers_dict.get('To', ''),
            'subject': headers_dict.get('Subject', ''),
            'date': headers_dict.get('Date', ''),
            'body': body,
            'is_read': 'UNREAD' not in msg.get('labelIds', [])
        }
        
        return message_obj
        
    except Exception as e:
        logger.error(f"Error getting Gmail message: {e}")
        return {"error": f"Failed to get Gmail message: {str(e)}"}

def gmail_search_messages(tool_context=None, query: str = "", max_results: int = 10) -> Dict[str, Any]:
    """
    Search Gmail messages.
    
    Args:
        tool_context: The tool context containing session information
        query: Gmail search query
        max_results: Maximum number of results to return
        
    Returns:
        Dict[str, Any]: List of messages
    """
    logger.info(f"Searching Gmail messages with query: {query}, max_results: {max_results}")
    
    # This is essentially the same as list_messages with a query
    return gmail_list_messages(tool_context, query, max_results)

def gmail_send_message(tool_context=None, to: str = "", subject: str = "", body: str = "", 
                      cc: Optional[str] = None, bcc: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a Gmail message.
    
    Args:
        tool_context: The tool context containing session information
        to: Recipient email address
        subject: Email subject
        body: Email body
        cc: CC recipients (comma-separated)
        bcc: BCC recipients (comma-separated)
        
    Returns:
        Dict[str, Any]: Send status
    """
    logger.info(f"Sending Gmail message to: {to}, subject: {subject}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Create message
        message = email.mime.text.MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            "success": True,
            "message_id": sent_message['id'],
            "thread_id": sent_message['threadId']
        }
        
    except Exception as e:
        logger.error(f"Error sending Gmail message: {e}")
        return {"error": f"Failed to send Gmail message: {str(e)}"}

def gmail_reply_to_message(tool_context=None, message_id: str = "", reply_text: str = "") -> Dict[str, Any]:
    """
    Reply to a Gmail message.
    
    Args:
        tool_context: The tool context containing session information
        message_id: Message ID to reply to
        reply_text: Reply text
        
    Returns:
        Dict[str, Any]: Reply status
    """
    logger.info(f"Replying to Gmail message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Get original message
        original_msg = service.users().messages().get(
            userId='me',
            id=message_id,
            format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']
        ).execute()
        
        # Extract headers
        headers = original_msg.get('payload', {}).get('headers', [])
        headers_dict = {header['name']: header['value'] for header in headers}
        
        # Get subject and from
        subject = headers_dict.get('Subject', '')
        from_email = headers_dict.get('From', '')
        
        # Create reply subject
        if not subject.startswith('Re:'):
            reply_subject = f"Re: {subject}"
        else:
            reply_subject = subject
        
        # Create message
        message = email.mime.text.MIMEText(reply_text)
        message['to'] = from_email
        message['subject'] = reply_subject
        
        # Set In-Reply-To and References headers for threading
        message['In-Reply-To'] = f"<{message_id}@gmail.com>"
        message['References'] = f"<{message_id}@gmail.com>"
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            "success": True,
            "message_id": sent_message['id'],
            "thread_id": sent_message['threadId']
        }
        
    except Exception as e:
        logger.error(f"Error replying to Gmail message: {e}")
        return {"error": f"Failed to reply to Gmail message: {str(e)}"}

def gmail_mark_as_read(tool_context=None, message_id: str = "") -> Dict[str, Any]:
    """
    Mark a Gmail message as read.
    
    Args:
        tool_context: The tool context containing session information
        message_id: Message ID
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Marking Gmail message as read: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Remove UNREAD label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error marking Gmail message as read: {e}")
        return {"error": f"Failed to mark Gmail message as read: {str(e)}"}

def gmail_archive_message(tool_context=None, message_id: str = "") -> Dict[str, Any]:
    """
    Archive a Gmail message.
    
    Args:
        tool_context: The tool context containing session information
        message_id: Message ID
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Archiving Gmail message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Remove INBOX label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error archiving Gmail message: {e}")
        return {"error": f"Failed to archive Gmail message: {str(e)}"}

def gmail_delete_message(tool_context=None, message_id: str = "") -> Dict[str, Any]:
    """
    Delete a Gmail message.
    
    Args:
        tool_context: The tool context containing session information
        message_id: Message ID
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Deleting Gmail message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Delete message
        service.users().messages().trash(
            userId='me',
            id=message_id
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error deleting Gmail message: {e}")
        return {"error": f"Failed to delete Gmail message: {str(e)}"}

# Create ADK FunctionTools
if ADK_AVAILABLE:
    gmail_check_connection_tool = FunctionTool(
        func=gmail_check_connection,
        name="gmail_check_connection",
        description="Check if Gmail is connected and authenticated."
    )
    
    gmail_authenticate_tool = FunctionTool(
        func=gmail_authenticate,
        name="gmail_authenticate",
        description="Authenticate with Gmail."
    )
    
    gmail_list_messages_tool = FunctionTool(
        func=gmail_list_messages,
        name="gmail_list_messages",
        description="List Gmail messages.",
        parameters={
            "query": {"type": "string", "description": "Gmail search query"},
            "max_results": {"type": "integer", "description": "Maximum number of results to return"}
        }
    )
    
    gmail_get_message_tool = FunctionTool(
        func=gmail_get_message,
        name="gmail_get_message",
        description="Get a Gmail message.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_search_messages_tool = FunctionTool(
        func=gmail_search_messages,
        name="gmail_search_messages",
        description="Search Gmail messages.",
        parameters={
            "query": {"type": "string", "description": "Gmail search query"},
            "max_results": {"type": "integer", "description": "Maximum number of results to return"}
        }
    )
    
    gmail_send_message_tool = FunctionTool(
        func=gmail_send_message,
        name="gmail_send_message",
        description="Send a Gmail message.",
        parameters={
            "to": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject"},
            "body": {"type": "string", "description": "Email body"},
            "cc": {"type": "string", "description": "CC recipients (comma-separated)"},
            "bcc": {"type": "string", "description": "BCC recipients (comma-separated)"}
        }
    )
    
    gmail_reply_to_message_tool = FunctionTool(
        func=gmail_reply_to_message,
        name="gmail_reply_to_message",
        description="Reply to a Gmail message.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID to reply to"},
            "reply_text": {"type": "string", "description": "Reply text"}
        }
    )
    
    gmail_mark_as_read_tool = FunctionTool(
        func=gmail_mark_as_read,
        name="gmail_mark_as_read",
        description="Mark a Gmail message as read.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_archive_message_tool = FunctionTool(
        func=gmail_archive_message,
        name="gmail_archive_message",
        description="Archive a Gmail message.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_delete_message_tool = FunctionTool(
        func=gmail_delete_message,
        name="gmail_delete_message",
        description="Delete a Gmail message.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    # List of all Gmail tools
    gmail_tools = [
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
else:
    # Fallback tools
    gmail_tools = [
        gmail_check_connection,
        gmail_authenticate,
        gmail_list_messages,
        gmail_get_message,
        gmail_search_messages,
        gmail_send_message,
        gmail_reply_to_message,
        gmail_mark_as_read,
        gmail_archive_message,
        gmail_delete_message
    ] 