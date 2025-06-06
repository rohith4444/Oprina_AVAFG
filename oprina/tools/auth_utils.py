# oprina/tools/auth_utils.py
"""
Simple authentication utilities for Oprina voice assistant.
Provides direct service access for Gmail and Calendar.
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths - tokens stored in oprina/ directory
OPRINA_DIR = Path(__file__).parent.parent  # tools/ -> oprina/
GMAIL_TOKEN_PATH = OPRINA_DIR / 'gmail_token.pickle'
CALENDAR_TOKEN_PATH = OPRINA_DIR / 'calendar_token.pickle'

def get_gmail_service() -> Optional[Any]:
    """
    Get authenticated Gmail service.
    
    Returns:
        Gmail service object or None if not authenticated
    """
    try:
        # Check if token file exists
        if not GMAIL_TOKEN_PATH.exists():
            return None
        
        # Load credentials
        with open(GMAIL_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh credentials if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(GMAIL_TOKEN_PATH, 'wb') as token:
                    pickle.dump(creds, token)
            else:
                # Credentials can't be refreshed
                return None
        
        # Create and return service
        return build('gmail', 'v1', credentials=creds)
        
    except Exception as e:
        # If anything goes wrong, return None
        return None

def get_calendar_service() -> Optional[Any]:
    """
    Get authenticated Calendar service.
    
    Returns:
        Calendar service object or None if not authenticated
    """
    try:
        # Check if token file exists
        if not CALENDAR_TOKEN_PATH.exists():
            return None
        
        # Load credentials
        with open(CALENDAR_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh credentials if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(CALENDAR_TOKEN_PATH, 'wb') as token:
                    pickle.dump(creds, token)
            else:
                # Credentials can't be refreshed
                return None
        
        # Create and return service
        return build('calendar', 'v3', credentials=creds)
        
    except Exception as e:
        # If anything goes wrong, return None
        return None

def check_gmail_connection() -> bool:
    """
    Check if Gmail is properly set up and accessible.
    
    Returns:
        True if Gmail service is available, False otherwise
    """
    service = get_gmail_service()
    if not service:
        return False
    
    try:
        # Test connection by getting user profile
        service.users().getProfile(userId='me').execute()
        return True
    except:
        return False

def check_calendar_connection() -> bool:
    """
    Check if Calendar is properly set up and accessible.
    
    Returns:
        True if Calendar service is available, False otherwise
    """
    service = get_calendar_service()
    if not service:
        return False
    
    try:
        # Test connection by listing calendars
        service.calendarList().list().execute()
        return True
    except:
        return False

# Export main functions
__all__ = [
    "get_gmail_service",
    "get_calendar_service", 
    "check_gmail_connection",
    "check_calendar_connection"
]