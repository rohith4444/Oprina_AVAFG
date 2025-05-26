"""
Modular Gmail MCP Tools
----------------------
This file defines all modular Gmail tools for the MCP system. Each tool is a class registered with the MCP tool registry, covering all major Gmail API capabilities:

- Email reading & searching
- Email composition & sending
- Draft management
- Label & folder management
- Thread management
- Attachment handling
- Email status management
- Spam & trash
- User profile & history
- Push notifications

Each tool class includes a summary, consistent docstring (Args, Returns, Raises), and is grouped by capability for clarity.
"""

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import base64
from mcp.mcp_tool import Tool, register_tool
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CLIENT_SECRET_FILE = 'client_secret_7774023189-5ga9j3epn8nja2aumfnmf09mh10osquh.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.json'

def get_gmail_service():
    """
    Returns an authenticated Gmail API service instance.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

# =========================================================
# 1. Email Reading & Searching
# =========================================================

@register_tool
class GmailListMessagesTool(Tool):
    """List Gmail messages with optional query/filter."""
    name = "gmail_list_messages"
    description = "List Gmail messages with optional query/filter."
    def run(self, query=""):
        """
        Args:
            query (str): Gmail search query string (optional)
        Returns:
            dict: List of message IDs and thread IDs
        """
        service = get_gmail_service()
        result = service.users().messages().list(userId='me', q=query).execute()
        return result

@register_tool
class GmailGetMessageTool(Tool):
    """Get a specific Gmail message by ID."""
    name = "gmail_get_message"
    description = "Get a specific Gmail message by ID."
    def run(self, msg_id):
        """
        Args:
            msg_id (str): Gmail message ID
        Returns:
            dict: Full message JSON
        """
        service = get_gmail_service()
        return service.users().messages().get(userId='me', id=msg_id, format='full').execute()

@register_tool
class GmailSearchTool(Tool):
    """Search Gmail messages by query."""
    name = "gmail_search"
    description = "Search Gmail messages by query."
    def run(self, query):
        """
        Args:
            query (str): Gmail search query string
        Returns:
            dict: List of matching message IDs
        """
        service = get_gmail_service()
        return service.users().messages().list(userId='me', q=query).execute()

@register_tool
class GmailReadThreadTool(Tool):
    """Get a Gmail thread by thread ID."""
    name = "gmail_read_thread"
    description = "Get a Gmail thread by thread ID."
    def run(self, thread_id):
        """
        Args:
            thread_id (str): Gmail thread ID
        Returns:
            dict: Thread details
        """
        service = get_gmail_service()
        return service.users().threads().get(userId='me', id=thread_id).execute()

@register_tool
class GmailGetAttachmentsTool(Tool):
    """Get attachments from a Gmail message by message ID."""
    name = "gmail_get_attachments"
    description = "Get attachments from a Gmail message by message ID."
    def run(self, msg_id):
        """
        Args:
            msg_id (str): Gmail message ID
        Returns:
            list: List of attachment info dicts (filename, mimeType, size, data)
        """
        service = get_gmail_service()
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        attachments = []
        for part in message.get('payload', {}).get('parts', []):
            if part.get('filename') and part.get('body') and part['body'].get('attachmentId'):
                attachment_id = part['body']['attachmentId']
                attachment = service.users().messages().attachments().get(
                    userId='me', messageId=msg_id, id=attachment_id).execute()
                data = attachment['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                attachments.append({
                    'filename': part['filename'],
                    'mimeType': part['mimeType'],
                    'size': part['body'].get('size', 0),
                    'data': file_data
                })
        return attachments

# =========================================================
# 2. Email Composition & Sending
# =========================================================

@register_tool
class GmailSendMessageTool(Tool):
    """Compose and send a new Gmail message."""
    name = "gmail_send_message"
    description = "Compose and send a new Gmail message. Args: to, subject, body, (optional) cc, bcc, attachments."
    def run(self, to, subject, body, cc=None, bcc=None, attachments=None):
        """
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            cc (str, optional): CC addresses
            bcc (str, optional): BCC addresses
            attachments (list, optional): List of dicts with keys 'filename' and 'data' (bytes)
        Returns:
            dict: Sent message metadata
        Raises:
            Exception: If sending fails
        """
        service = get_gmail_service()
        # Get the authenticated user's email address
        try:
            profile = service.users().getProfile(userId='me').execute()
            from_email = profile.get('emailAddress', '')
        except Exception as e:
            raise Exception(f"Failed to get sender email: {e}")
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        message['from'] = from_email
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        message.attach(MIMEText(body, 'plain'))
        # Attach files if provided
        if attachments:
            for att in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(att['data'])
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{att['filename']}"')
                message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            sent = service.users().messages().send(userId='me', body={'raw': raw}).execute()
            return sent
        except Exception as e:
            raise Exception(f"Failed to send email: {e}")

@register_tool
class GmailReplyMessageTool(Tool):
    """Send a reply to an existing Gmail message."""
    name = "gmail_reply_message"
    description = "Send a reply to an existing Gmail message. Args: msg_id, body, (optional) attachments."
    def run(self, msg_id, body, attachments=None):
        """
        Args:
            msg_id (str): Message ID to reply to
            body (str): Reply body
            attachments (list, optional): List of dicts with keys 'filename' and 'data' (bytes)
        Returns:
            dict: Sent message metadata
        Raises:
            Exception: If sending fails
        """
        service = get_gmail_service()
        # Get the original message to reply to
        original = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}
        thread_id = original.get('threadId')
        to = headers.get('From')
        subject = headers.get('Subject', '')
        if not subject.lower().startswith('re:'):
            subject = 'Re: ' + subject
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        message['In-Reply-To'] = headers.get('Message-ID', '')
        message['References'] = headers.get('Message-ID', '')
        message.attach(MIMEText(body, 'plain'))
        if attachments:
            for att in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(att['data'])
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{att['filename']}"')
                message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            sent = service.users().messages().send(userId='me', body={'raw': raw, 'threadId': thread_id}).execute()
            return sent
        except Exception as e:
            raise Exception(f"Failed to send reply: {e}")

@register_tool
class GmailSendDraftTool(Tool):
    """Send a draft email by draft ID."""
    name = "gmail_send_draft"
    description = "Send a draft email by draft ID."
    def run(self, draft_id):
        """
        Args:
            draft_id (str): Draft ID
        Returns:
            dict: Sent message metadata
        Raises:
            Exception: If sending fails
        """
        service = get_gmail_service()
        try:
            sent = service.users().drafts().send(userId='me', body={'id': draft_id}).execute()
            return sent
        except Exception as e:
            raise Exception(f"Failed to send draft: {e}")

# =========================================================
# 3. Draft Management
# =========================================================

@register_tool
class GmailCreateDraftTool(Tool):
    """Create a new draft email."""
    name = "gmail_create_draft"
    description = "Create a new draft email. Args: to, subject, body, (optional) cc, bcc, attachments."
    def run(self, to, subject, body, cc=None, bcc=None, attachments=None):
        """
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            cc (str, optional): CC addresses
            bcc (str, optional): BCC addresses
            attachments (list, optional): List of dicts with keys 'filename' and 'data' (bytes)
        Returns:
            dict: Created draft metadata
        Raises:
            Exception: If creation fails
        """
        service = get_gmail_service()
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        message.attach(MIMEText(body, 'plain'))
        if attachments:
            for att in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(att['data'])
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{att['filename']}"')
                message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            draft = service.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
            return draft
        except Exception as e:
            raise Exception(f"Failed to create draft: {e}")

@register_tool
class GmailListDraftsTool(Tool):
    """List all draft emails."""
    name = "gmail_list_drafts"
    description = "List all draft emails."
    def run(self):
        """
        Returns:
            list: List of draft metadata
        Raises:
            Exception: If listing fails
        """
        service = get_gmail_service()
        try:
            drafts = service.users().drafts().list(userId='me').execute()
            return drafts.get('drafts', [])
        except Exception as e:
            raise Exception(f"Failed to list drafts: {e}")

@register_tool
class GmailUpdateDraftTool(Tool):
    """Update a draft email by draft ID."""
    name = "gmail_update_draft"
    description = "Update a draft email by draft ID. Args: draft_id, subject, body, etc."
    def run(self, draft_id, subject=None, body=None, to=None, cc=None, bcc=None, attachments=None):
        """
        Args:
            draft_id (str): Draft ID
            subject (str, optional): New subject
            body (str, optional): New body
            to (str, optional): New recipient
            cc (str, optional): New CC
            bcc (str, optional): New BCC
            attachments (list, optional): List of dicts with keys 'filename' and 'data' (bytes)
        Returns:
            dict: Updated draft metadata
        Raises:
            Exception: If update fails
        """
        service = get_gmail_service()
        # Get the existing draft
        try:
            draft = service.users().drafts().get(userId='me', id=draft_id).execute()
            msg_payload = draft['message']['payload']
            headers = {h['name']: h['value'] for h in msg_payload.get('headers', [])}
        except Exception as e:
            raise Exception(f"Failed to fetch draft: {e}")
        # Build new message
        message = MIMEMultipart()
        message['to'] = to or headers.get('To', '')
        message['subject'] = subject or headers.get('Subject', '')
        if cc or headers.get('Cc'):
            message['cc'] = cc or headers.get('Cc', '')
        if bcc or headers.get('Bcc'):
            message['bcc'] = bcc or headers.get('Bcc', '')
        message.attach(MIMEText(body or '', 'plain'))
        if attachments:
            for att in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(att['data'])
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{att['filename']}"')
                message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            updated = service.users().drafts().update(userId='me', id=draft_id, body={'message': {'raw': raw}}).execute()
            return updated
        except Exception as e:
            raise Exception(f"Failed to update draft: {e}")

@register_tool
class GmailDeleteDraftTool(Tool):
    """Delete a draft email by draft ID."""
    name = "gmail_delete_draft"
    description = "Delete a draft email by draft ID."
    def run(self, draft_id):
        """
        Args:
            draft_id (str): Draft ID
        Returns:
            dict: Result of deletion
        Raises:
            Exception: If deletion fails
        """
        service = get_gmail_service()
        try:
            service.users().drafts().delete(userId='me', id=draft_id).execute()
            return {"status": "success", "message": f"Draft {draft_id} deleted."}
        except Exception as e:
            raise Exception(f"Failed to delete draft: {e}")

# =========================================================
# 4. Label & Folder Management
# =========================================================

@register_tool
class GmailListLabelsTool(Tool):
    """Retrieve all Gmail labels."""
    name = "gmail_list_labels"
    description = "Retrieve all Gmail labels."
    def run(self):
        """
        Returns:
            list: List of label metadata
        Raises:
            Exception: If listing fails
        """
        service = get_gmail_service()
        try:
            labels = service.users().labels().list(userId='me').execute()
            return labels.get('labels', [])
        except Exception as e:
            raise Exception(f"Failed to list labels: {e}")

@register_tool
class GmailCreateLabelTool(Tool):
    """Create a new Gmail label."""
    name = "gmail_create_label"
    description = "Create a new Gmail label. Args: label_name."
    def run(self, label_name):
        """
        Args:
            label_name (str): Name of the new label
        Returns:
            dict: Created label metadata
        Raises:
            Exception: If creation fails
        """
        service = get_gmail_service()
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show',
        }
        try:
            label = service.users().labels().create(userId='me', body=label_body).execute()
            return label
        except Exception as e:
            raise Exception(f"Failed to create label: {e}")

@register_tool
class GmailModifyLabelsTool(Tool):
    """Apply or remove labels to/from a message."""
    name = "gmail_modify_labels"
    description = "Apply or remove labels to/from a message. Args: msg_id, add_labels, remove_labels."
    def run(self, msg_id, add_labels=None, remove_labels=None):
        """
        Args:
            msg_id (str): Message ID
            add_labels (list, optional): List of label IDs to add
            remove_labels (list, optional): List of label IDs to remove
        Returns:
            dict: Modified message metadata
        Raises:
            Exception: If modification fails
        """
        service = get_gmail_service()
        mods = {}
        if add_labels:
            mods['addLabelIds'] = add_labels
        if remove_labels:
            mods['removeLabelIds'] = remove_labels
        try:
            result = service.users().messages().modify(userId='me', id=msg_id, body=mods).execute()
            return result
        except Exception as e:
            raise Exception(f"Failed to modify labels: {e}")

# =========================================================
# 5. Thread Management
# =========================================================

@register_tool
class GmailModifyThreadLabelsTool(Tool):
    """Apply or remove labels to/from a thread."""
    name = "gmail_modify_thread_labels"
    description = "Apply or remove labels to/from a thread. Args: thread_id, add_labels, remove_labels."
    def run(self, thread_id, add_labels=None, remove_labels=None):
        """
        Args:
            thread_id (str): Thread ID
            add_labels (list, optional): List of label IDs to add
            remove_labels (list, optional): List of label IDs to remove
        Returns:
            dict: Modified thread metadata
        Raises:
            Exception: If modification fails
        """
        service = get_gmail_service()
        mods = {}
        if add_labels:
            mods['addLabelIds'] = add_labels
        if remove_labels:
            mods['removeLabelIds'] = remove_labels
        try:
            result = service.users().threads().modify(userId='me', id=thread_id, body=mods).execute()
            return result
        except Exception as e:
            raise Exception(f"Failed to modify thread labels: {e}")

# =========================================================
# 6. Email Status Management
# =========================================================

@register_tool
class GmailMarkMessageStatusTool(Tool):
    """Mark a message as read/unread/starred/important/etc."""
    name = "gmail_mark_message_status"
    description = "Mark a message as read/unread/starred/important/etc. Args: msg_id, status_type, value."
    def run(self, msg_id, status_type, value):
        """
        Args:
            msg_id (str): Message ID
            status_type (str): Status type ('read', 'starred', 'important')
            value (bool): True to set, False to unset
        Returns:
            dict: Modified message metadata
        Raises:
            Exception: If modification fails
        """
        service = get_gmail_service()
        label_map = {
            'read': 'UNREAD',
            'starred': 'STARRED',
            'important': 'IMPORTANT',
        }
        if status_type not in label_map:
            raise Exception(f"Unsupported status_type: {status_type}")
        label_id = label_map[status_type]
        mods = {'addLabelIds': [], 'removeLabelIds': []}
        if value:
            if status_type == 'read':
                mods['removeLabelIds'].append(label_id)
            else:
                mods['addLabelIds'].append(label_id)
        else:
            if status_type == 'read':
                mods['addLabelIds'].append(label_id)
            else:
                mods['removeLabelIds'].append(label_id)
        try:
            result = service.users().messages().modify(userId='me', id=msg_id, body=mods).execute()
            return result
        except Exception as e:
            raise Exception(f"Failed to mark message status: {e}")

@register_tool
class GmailArchiveMessageTool(Tool):
    """Archive a message (remove INBOX label)."""
    name = "gmail_archive_message"
    description = "Archive a message (remove INBOX label). Args: msg_id."
    def run(self, msg_id):
        """
        Args:
            msg_id (str): Message ID
        Returns:
            dict: Modified message metadata
        Raises:
            Exception: If modification fails
        """
        service = get_gmail_service()
        mods = {'removeLabelIds': ['INBOX']}
        try:
            result = service.users().messages().modify(userId='me', id=msg_id, body=mods).execute()
            return result
        except Exception as e:
            raise Exception(f"Failed to archive message: {e}")

@register_tool
class GmailTrashMessageTool(Tool):
    """Move a message to trash."""
    name = "gmail_trash_message"
    description = "Move a message to trash. Args: msg_id."
    def run(self, msg_id):
        """
        Args:
            msg_id (str): Message ID
        Returns:
            dict: Trashed message metadata
        Raises:
            Exception: If trashing fails
        """
        service = get_gmail_service()
        try:
            result = service.users().messages().trash(userId='me', id=msg_id).execute()
            return result
        except Exception as e:
            raise Exception(f"Failed to trash message: {e}")

@register_tool
class GmailDeleteMessageTool(Tool):
    """Permanently delete a message."""
    name = "gmail_delete_message"
    description = "Permanently delete a message. Args: msg_id."
    def run(self, msg_id):
        """
        Args:
            msg_id (str): Message ID
        Returns:
            dict: Deletion result
        Raises:
            Exception: If deletion fails
        """
        service = get_gmail_service()
        try:
            service.users().messages().delete(userId='me', id=msg_id).execute()
            return {"status": "success", "message": f"Message {msg_id} deleted."}
        except Exception as e:
            raise Exception(f"Failed to delete message: {e}")

# =========================================================
# 7. Spam & Trash
# =========================================================

@register_tool
class GmailMoveToSpamTool(Tool):
    """Move a message to spam."""
    name = "gmail_move_to_spam"
    description = "Move a message to spam. Args: msg_id."
    def run(self, msg_id):
        """
        Args:
            msg_id (str): Message ID
        Returns:
            dict: Modified message metadata
        Raises:
            Exception: If operation fails
        """
        service = get_gmail_service()
        mods = {'addLabelIds': ['SPAM']}
        try:
            result = service.users().messages().modify(userId='me', id=msg_id, body=mods).execute()
            return result
        except Exception as e:
            raise Exception(f"Failed to move message to spam: {e}")

@register_tool
class GmailRemoveFromSpamTool(Tool):
    """Remove a message from spam."""
    name = "gmail_remove_from_spam"
    description = "Remove a message from spam. Args: msg_id."
    def run(self, msg_id):
        """
        Args:
            msg_id (str): Message ID
        Returns:
            dict: Modified message metadata
        Raises:
            Exception: If operation fails
        """
        service = get_gmail_service()
        mods = {'removeLabelIds': ['SPAM']}
        try:
            result = service.users().messages().modify(userId='me', id=msg_id, body=mods).execute()
            return result
        except Exception as e:
            raise Exception(f"Failed to remove message from spam: {e}")

# =========================================================
# 8. User Profile & History
# =========================================================

@register_tool
class GmailGetUserProfileTool(Tool):
    """Get the user's Gmail profile (email address, etc)."""
    name = "gmail_get_user_profile"
    description = "Get the user's Gmail profile (email address, etc)."
    def run(self):
        """
        Returns:
            dict: User profile info
        Raises:
            Exception: If operation fails
        """
        service = get_gmail_service()
        try:
            profile = service.users().getProfile(userId='me').execute()
            return profile
        except Exception as e:
            raise Exception(f"Failed to get user profile: {e}")

@register_tool
class GmailGetHistoryTool(Tool):
    """Get mailbox history (message IDs, label changes, etc)."""
    name = "gmail_get_history"
    description = "Get mailbox history (message IDs, label changes, etc). Args: start_history_id."
    def run(self, start_history_id):
        """
        Args:
            start_history_id (str): History ID to start from
        Returns:
            dict: History info
        Raises:
            Exception: If operation fails
        """
        service = get_gmail_service()
        try:
            history = service.users().history().list(userId='me', startHistoryId=start_history_id).execute()
            return history
        except Exception as e:
            raise Exception(f"Failed to get mailbox history: {e}")

# =========================================================
# 9. Push Notifications
# =========================================================

@register_tool
class GmailWatchMailboxTool(Tool):
    """Set up push notifications for mailbox changes (Pub/Sub)."""
    name = "gmail_watch_mailbox"
    description = "Set up push notifications for mailbox changes (Pub/Sub). Args: topic_name, label_ids, etc."
    def run(self, topic_name, label_ids=None):
        """
        Args:
            topic_name (str): Pub/Sub topic name
            label_ids (list, optional): List of label IDs to monitor
        Raises:
            NotImplementedError: This requires Google Cloud Pub/Sub setup and is not implemented here.
        """
        raise NotImplementedError("Push notifications require Google Cloud Pub/Sub setup. See Gmail API docs for details.") 