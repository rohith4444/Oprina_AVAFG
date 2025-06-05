"""
Gmail Service Module

This module provides services for interacting with the Gmail API.
It handles authentication, message retrieval, and message operations.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Union
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add the parent directory to the path to import from mcp_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_server.auth_manager import AuthManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GmailService:
    """Service for interacting with the Gmail API."""
    
    def __init__(self, auth_manager: Optional[AuthManager] = None):
        """Initialize the Gmail service.
        
        Args:
            auth_manager: Optional AuthManager instance. If not provided, a new one will be created.
        """
        self.auth_manager = auth_manager or AuthManager()
        self.service = None
        
    def _get_service(self) -> Any:
        """Get the Gmail API service.
        
        Returns:
            The Gmail API service.
        """
        if self.service is None:
            credentials = self.auth_manager.get_credentials()
            self.service = build('gmail', 'v1', credentials=credentials)
        return self.service
    
    def list_messages(self, query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """List Gmail messages.
        
        Args:
            query: The search query to filter messages.
            max_results: The maximum number of messages to return.
            
        Returns:
            A list of message metadata.
        """
        try:
            service = self._get_service()
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info('No messages found.')
                return []
                
            # Get full message details for each message
            message_details = []
            for message in messages:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()
                
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                
                message_details.append({
                    'id': msg['id'],
                    'threadId': msg['threadId'],
                    'snippet': msg['snippet'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'labels': msg['labelIds']
                })
                
            return message_details
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise
    
    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get a Gmail message by ID.
        
        Args:
            message_id: The ID of the message to retrieve.
            
        Returns:
            The message details.
        """
        try:
            service = self._get_service()
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            to = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown Recipient')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            # Extract body
            body = self._get_message_body(message)
            
            return {
                'id': message['id'],
                'threadId': message['threadId'],
                'subject': subject,
                'sender': sender,
                'to': to,
                'date': date,
                'body': body,
                'labels': message['labelIds']
            }
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise
    
    def _get_message_body(self, message: Dict[str, Any]) -> str:
        """Extract the message body from a Gmail message.
        
        Args:
            message: The Gmail message.
            
        Returns:
            The message body as a string.
        """
        if 'parts' in message['payload']:
            parts = message['payload']['parts']
            body = ''
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        import base64
                        body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            return body
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            import base64
            return base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        else:
            return 'No body content'
    
    def send_message(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send a Gmail message.
        
        Args:
            to: The recipient email address.
            subject: The email subject.
            body: The email body.
            
        Returns:
            The sent message details.
        """
        try:
            service = self._get_service()
            
            # Create message
            message = {
                'raw': self._create_message(to, subject, body)
            }
            
            # Send message
            sent_message = service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            logger.info(f'Message sent. Message Id: {sent_message["id"]}')
            return sent_message
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise
    
    def _create_message(self, to: str, subject: str, body: str) -> str:
        """Create a Gmail message.
        
        Args:
            to: The recipient email address.
            subject: The email subject.
            body: The email body.
            
        Returns:
            The encoded message.
        """
        import base64
        from email.mime.text import MIMEText
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        return base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    def delete_message(self, message_id: str) -> None:
        """Delete a Gmail message.
        
        Args:
            message_id: The ID of the message to delete.
        """
        try:
            service = self._get_service()
            service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()
            
            logger.info(f'Message {message_id} deleted.')
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise 