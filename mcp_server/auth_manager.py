"""
Authentication manager for the Oprina MCP server.

This module handles authentication with Google services (Gmail, Calendar).
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Import the local config
from mcp_server.config import config

class AuthManager:
    """
    Authentication manager for Google services.
    
    This class handles authentication with Google services (Gmail, Calendar)
    and provides methods to check authentication status and get service instances.
    """
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.gmail_service = None
        self.calendar_service = None
        self.credentials = None
    
    async def check_auth(self) -> bool:
        """
        Check if the user is authenticated with Google services.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return await self.get_credentials() is not None
    
    async def get_credentials(self) -> Optional[Credentials]:
        """
        Get the Google credentials.
        
        Returns:
            Optional[Credentials]: Google credentials if authenticated, None otherwise
        """
        if not self.credentials:
            token_file = config.get("google_token_file", 'credentials/gmail_token.json')
            print(f"[DEBUG] Looking for token file at: {os.path.abspath(token_file)}")
            print(f"[DEBUG] File exists: {os.path.exists(token_file)}")
            if os.path.exists(token_file):
                try:
                    self.credentials = Credentials.from_authorized_user_file(token_file, [
                        'https://www.googleapis.com/auth/gmail.modify',
                        'https://www.googleapis.com/auth/calendar',
                        'https://www.googleapis.com/auth/userinfo.profile',
                        'https://www.googleapis.com/auth/userinfo.email',
                        'openid'
                    ])
                    if self.credentials and self.credentials.valid:
                        return self.credentials
                except Exception as e:
                    print(f"Error loading credentials from {token_file}: {e}")
        return self.credentials
    
    async def get_gmail_service(self):
        """
        Get the Gmail service.
        
        Returns:
            The Gmail service
        """
        if not self.gmail_service:
            credentials = await self.get_credentials()
            if credentials:
                self.gmail_service = build('gmail', 'v1', credentials=credentials)
        return self.gmail_service
    
    async def get_calendar_service(self):
        """
        Get the Calendar service.
        
        Returns:
            The Calendar service
        """
        if not self.calendar_service:
            credentials = await self.get_credentials()
            if credentials:
                self.calendar_service = build('calendar', 'v3', credentials=credentials)
        return self.calendar_service
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the user's Google profile.
        
        Returns:
            Dict[str, Any]: User profile information
        """
        service = await self.get_gmail_service()
        profile = service.users().getProfile(userId='me').execute()
        return profile 