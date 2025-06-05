"""
Additional Gmail Tools for ADK Integration

This module provides additional Gmail API tools that follow the ADK FunctionTool pattern.
These tools complement the existing gmail_tools.py file.
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
from services.google_cloud.gmail_auth import get_gmail_service
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("gmail_tools_additional", console_output=True)

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

def gmail_mark_as_important(message_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Mark a Gmail message as important.
    
    Args:
        message_id: Message ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Marking Gmail message as important: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Add IMPORTANT label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['IMPORTANT']}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error marking Gmail message as important: {e}")
        return {"error": f"Failed to mark Gmail message as important: {str(e)}"}

def gmail_mark_as_not_important(message_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Mark a Gmail message as not important.
    
    Args:
        message_id: Message ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Marking Gmail message as not important: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Remove IMPORTANT label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['IMPORTANT']}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error marking Gmail message as not important: {e}")
        return {"error": f"Failed to mark Gmail message as not important: {str(e)}"}

def gmail_star_message(message_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Star a Gmail message.
    
    Args:
        message_id: Message ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Starring Gmail message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Add STARRED label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['STARRED']}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error starring Gmail message: {e}")
        return {"error": f"Failed to star Gmail message: {str(e)}"}

def gmail_unstar_message(message_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Unstar a Gmail message.
    
    Args:
        message_id: Message ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Unstarring Gmail message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Remove STARRED label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['STARRED']}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error unstarring Gmail message: {e}")
        return {"error": f"Failed to unstar Gmail message: {str(e)}"}

def gmail_move_to_spam(message_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Move a Gmail message to spam.
    
    Args:
        message_id: Message ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Moving Gmail message to spam: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Add SPAM label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['SPAM']}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error moving Gmail message to spam: {e}")
        return {"error": f"Failed to move Gmail message to spam: {str(e)}"}

def gmail_remove_from_spam(message_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Remove a Gmail message from spam.
    
    Args:
        message_id: Message ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Removing Gmail message from spam: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Remove SPAM label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['SPAM']}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error removing Gmail message from spam: {e}")
        return {"error": f"Failed to remove Gmail message from spam: {str(e)}"}

def gmail_get_user_profile(tool_context=None) -> Dict[str, Any]:
    """
    Get Gmail user profile.
    
    Args:
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: User profile
    """
    logger.info("Getting Gmail user profile")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        
        return {
            "email_address": profile.get('emailAddress', ''),
            "messages_total": profile.get('messagesTotal', 0),
            "threads_total": profile.get('threadsTotal', 0),
            "history_id": profile.get('historyId', '')
        }
        
    except Exception as e:
        logger.error(f"Error getting Gmail user profile: {e}")
        return {"error": f"Failed to get Gmail user profile: {str(e)}"}

def gmail_get_labels(tool_context=None) -> Dict[str, Any]:
    """
    Get Gmail labels.
    
    Args:
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: List of labels
    """
    logger.info("Getting Gmail labels")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Get labels
        results = service.users().labels().list(userId='me').execute()
        
        labels = results.get('labels', [])
        
        return {
            "labels": labels,
            "count": len(labels)
        }
        
    except Exception as e:
        logger.error(f"Error getting Gmail labels: {e}")
        return {"error": f"Failed to get Gmail labels: {str(e)}"}

def gmail_create_label(label_name: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Create a Gmail label.
    
    Args:
        label_name: Label name
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Created label details
    """
    logger.info(f"Creating Gmail label: {label_name}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Create label
        label = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        
        created_label = service.users().labels().create(
            userId='me',
            body=label
        ).execute()
        
        return created_label
        
    except Exception as e:
        logger.error(f"Error creating Gmail label: {e}")
        return {"error": f"Failed to create Gmail label: {str(e)}"}

def gmail_apply_label(message_id: str = "", label_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Apply a label to a Gmail message.
    
    Args:
        message_id: Message ID
        label_id: Label ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Applying Gmail label {label_id} to message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Apply label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error applying Gmail label: {e}")
        return {"error": f"Failed to apply Gmail label: {str(e)}"}

def gmail_remove_label(message_id: str = "", label_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Remove a label from a Gmail message.
    
    Args:
        message_id: Message ID
        label_id: Label ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Removing Gmail label {label_id} from message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Remove label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': [label_id]}
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error removing Gmail label: {e}")
        return {"error": f"Failed to remove Gmail label: {str(e)}"}

def gmail_get_thread(thread_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Get a Gmail thread.
    
    Args:
        thread_id: Thread ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Thread details
    """
    logger.info(f"Getting Gmail thread: {thread_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Get thread
        thread = service.users().threads().get(
            userId='me',
            id=thread_id,
            format='full'
        ).execute()
        
        # Extract messages
        messages = thread.get('messages', [])
        
        # Process messages
        message_list = []
        for msg in messages:
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
                'snippet': msg.get('snippet', ''),
                'from': headers_dict.get('From', ''),
                'to': headers_dict.get('To', ''),
                'subject': headers_dict.get('Subject', ''),
                'date': headers_dict.get('Date', ''),
                'body': body,
                'is_read': 'UNREAD' not in msg.get('labelIds', [])
            }
            
            message_list.append(message_obj)
        
        return {
            'id': thread['id'],
            'snippet': thread.get('snippet', ''),
            'history_id': thread.get('historyId', ''),
            'messages': message_list,
            'message_count': len(message_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting Gmail thread: {e}")
        return {"error": f"Failed to get Gmail thread: {str(e)}"}

def gmail_modify_thread(thread_id: str = "", label_ids_to_add: List[str] = None, label_ids_to_remove: List[str] = None, tool_context=None) -> Dict[str, Any]:
    """
    Modify a Gmail thread.
    
    Args:
        thread_id: Thread ID
        label_ids_to_add: List of label IDs to add
        label_ids_to_remove: List of label IDs to remove
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Modifying Gmail thread: {thread_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Prepare modify request
        modify_request = {}
        
        if label_ids_to_add:
            modify_request['addLabelIds'] = label_ids_to_add
        
        if label_ids_to_remove:
            modify_request['removeLabelIds'] = label_ids_to_remove
        
        # Modify thread
        service.users().threads().modify(
            userId='me',
            id=thread_id,
            body=modify_request
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error modifying Gmail thread: {e}")
        return {"error": f"Failed to modify Gmail thread: {str(e)}"}

def gmail_get_attachment(message_id: str = "", attachment_id: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Get a Gmail attachment.
    
    Args:
        message_id: Message ID
        attachment_id: Attachment ID
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Attachment details
    """
    logger.info(f"Getting Gmail attachment: {attachment_id} from message: {message_id}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Get attachment
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=attachment_id
        ).execute()
        
        # Decode attachment data
        attachment_data = base64.urlsafe_b64decode(attachment['data'])
        
        return {
            'id': attachment['id'],
            'size': attachment['size'],
            'data': attachment_data
        }
        
    except Exception as e:
        logger.error(f"Error getting Gmail attachment: {e}")
        return {"error": f"Failed to get Gmail attachment: {str(e)}"}

def gmail_save_attachment(message_id: str = "", attachment_id: str = "", storage_path: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Save a Gmail attachment.
    
    Args:
        message_id: Message ID
        attachment_id: Attachment ID
        storage_path: Path to save the attachment
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Saving Gmail attachment: {attachment_id} from message: {message_id} to: {storage_path}")
    
    # Get Gmail service
    service = get_gmail_service()
    
    if not service:
        return {"error": "Gmail service not available. Please authenticate first."}
    
    try:
        # Get attachment
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=attachment_id
        ).execute()
        
        # Decode attachment data
        attachment_data = base64.urlsafe_b64decode(attachment['data'])
        
        # Save attachment
        with open(storage_path, 'wb') as f:
            f.write(attachment_data)
        
        return {
            'success': True,
            'path': storage_path,
            'size': len(attachment_data)
        }
        
    except Exception as e:
        logger.error(f"Error saving Gmail attachment: {e}")
        return {"error": f"Failed to save Gmail attachment: {str(e)}"}

# Create ADK FunctionTools
if ADK_AVAILABLE:
    gmail_mark_as_important_tool = FunctionTool(
        func=gmail_mark_as_important,
        name="gmail_mark_as_important",
        description="Mark a Gmail message as important.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_mark_as_not_important_tool = FunctionTool(
        func=gmail_mark_as_not_important,
        name="gmail_mark_as_not_important",
        description="Mark a Gmail message as not important.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_star_message_tool = FunctionTool(
        func=gmail_star_message,
        name="gmail_star_message",
        description="Star a Gmail message.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_unstar_message_tool = FunctionTool(
        func=gmail_unstar_message,
        name="gmail_unstar_message",
        description="Unstar a Gmail message.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_move_to_spam_tool = FunctionTool(
        func=gmail_move_to_spam,
        name="gmail_move_to_spam",
        description="Move a Gmail message to spam.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_remove_from_spam_tool = FunctionTool(
        func=gmail_remove_from_spam,
        name="gmail_remove_from_spam",
        description="Remove a Gmail message from spam.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"}
        }
    )
    
    gmail_get_user_profile_tool = FunctionTool(
        func=gmail_get_user_profile,
        name="gmail_get_user_profile",
        description="Get Gmail user profile."
    )
    
    gmail_get_labels_tool = FunctionTool(
        func=gmail_get_labels,
        name="gmail_get_labels",
        description="Get Gmail labels."
    )
    
    gmail_create_label_tool = FunctionTool(
        func=gmail_create_label,
        name="gmail_create_label",
        description="Create a Gmail label.",
        parameters={
            "label_name": {"type": "string", "description": "Label name"}
        }
    )
    
    gmail_apply_label_tool = FunctionTool(
        func=gmail_apply_label,
        name="gmail_apply_label",
        description="Apply a Gmail label to a message.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"},
            "label_id": {"type": "string", "description": "Label ID"}
        }
    )
    
    gmail_remove_label_tool = FunctionTool(
        func=gmail_remove_label,
        name="gmail_remove_label",
        description="Remove a Gmail label from a message.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"},
            "label_id": {"type": "string", "description": "Label ID"}
        }
    )
    
    gmail_get_thread_tool = FunctionTool(
        func=gmail_get_thread,
        name="gmail_get_thread",
        description="Get a Gmail thread.",
        parameters={
            "thread_id": {"type": "string", "description": "Thread ID"}
        }
    )
    
    gmail_modify_thread_tool = FunctionTool(
        func=gmail_modify_thread,
        name="gmail_modify_thread",
        description="Modify a Gmail thread.",
        parameters={
            "thread_id": {"type": "string", "description": "Thread ID"},
            "label_ids_to_add": {"type": "array", "items": {"type": "string"}, "description": "Label IDs to add"},
            "label_ids_to_remove": {"type": "array", "items": {"type": "string"}, "description": "Label IDs to remove"}
        }
    )
    
    gmail_get_attachment_tool = FunctionTool(
        func=gmail_get_attachment,
        name="gmail_get_attachment",
        description="Get a Gmail attachment.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"},
            "attachment_id": {"type": "string", "description": "Attachment ID"}
        }
    )
    
    gmail_save_attachment_tool = FunctionTool(
        func=gmail_save_attachment,
        name="gmail_save_attachment",
        description="Save a Gmail attachment to storage.",
        parameters={
            "message_id": {"type": "string", "description": "Message ID"},
            "attachment_id": {"type": "string", "description": "Attachment ID"},
            "storage_path": {"type": "string", "description": "Path to save the attachment"}
        }
    )
    
    # List of all additional Gmail tools
    gmail_additional_tools = [
        gmail_mark_as_important_tool,
        gmail_mark_as_not_important_tool,
        gmail_star_message_tool,
        gmail_unstar_message_tool,
        gmail_move_to_spam_tool,
        gmail_remove_from_spam_tool,
        gmail_get_user_profile_tool,
        gmail_get_labels_tool,
        gmail_create_label_tool,
        gmail_apply_label_tool,
        gmail_remove_label_tool,
        gmail_get_thread_tool,
        gmail_modify_thread_tool,
        gmail_get_attachment_tool,
        gmail_save_attachment_tool
    ]
else:
    # Fallback tools
    gmail_additional_tools = [
        gmail_mark_as_important,
        gmail_mark_as_not_important,
        gmail_star_message,
        gmail_unstar_message,
        gmail_move_to_spam,
        gmail_remove_from_spam,
        gmail_get_user_profile,
        gmail_get_labels,
        gmail_create_label,
        gmail_apply_label,
        gmail_remove_label,
        gmail_get_thread,
        gmail_modify_thread,
        gmail_get_attachment,
        gmail_save_attachment
    ] 