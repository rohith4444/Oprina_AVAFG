"""
Simple authentication utilities for Oprina voice assistant.
Provides direct service access for Gmail and Calendar.
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Any
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from oprina.services.logging.logger import setup_logger

# Paths - tokens stored in oprina/ directory
OPRINA_DIR = Path(__file__).parent.parent  # tools/ -> oprina/
GMAIL_TOKEN_PATH = OPRINA_DIR / 'gmail_token.pickle'
CALENDAR_TOKEN_PATH = OPRINA_DIR / 'calendar_token.pickle'

# Setup logger
logger = setup_logger("auth_utils", console_output=True)

def get_gmail_service() -> Optional[Any]:
    """
    Get authenticated Gmail service.
    
    Returns:
        Gmail service object or None if not authenticated
    """
    try:
        logger.debug("Attempting to get Gmail service")
        
        # Check if token file exists
        if not GMAIL_TOKEN_PATH.exists():
            logger.warning(f"Gmail token file not found at {GMAIL_TOKEN_PATH}")
            return None
        
        logger.debug("Loading Gmail credentials from token file")
        # Load credentials
        with open(GMAIL_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh credentials if needed
        if not creds.valid:
            logger.info("Gmail credentials not valid, attempting refresh")
            if creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing Gmail credentials")
                    creds.refresh(Request())
                    
                    # Save refreshed credentials
                    with open(GMAIL_TOKEN_PATH, 'wb') as token:
                        pickle.dump(creds, token)
                    logger.info("Gmail credentials refreshed and saved successfully")
                    
                except Exception as refresh_error:
                    logger.error(f"Failed to refresh Gmail credentials: {refresh_error}")
                    return None
            else:
                # Credentials can't be refreshed
                logger.error("Gmail credentials expired and cannot be refreshed")
                return None
        
        # Create and return service
        logger.debug("Creating Gmail service")
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service created successfully")
        return service
        
    except Exception as e:
        # If anything goes wrong, return None
        logger.error(f"Error getting Gmail service: {e}")
        return None

def get_calendar_service() -> Optional[Any]:
    """
    Get authenticated Calendar service.
    
    Returns:
        Calendar service object or None if not authenticated
    """
    try:
        logger.debug("Attempting to get Calendar service")
        
        # Check if token file exists
        if not CALENDAR_TOKEN_PATH.exists():
            logger.warning(f"Calendar token file not found at {CALENDAR_TOKEN_PATH}")
            return None
        
        logger.debug("Loading Calendar credentials from token file")
        # Load credentials
        with open(CALENDAR_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh credentials if needed
        if not creds.valid:
            logger.info("Calendar credentials not valid, attempting refresh")
            if creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing Calendar credentials")
                    creds.refresh(Request())
                    
                    # Save refreshed credentials
                    with open(CALENDAR_TOKEN_PATH, 'wb') as token:
                        pickle.dump(creds, token)
                    logger.info("Calendar credentials refreshed and saved successfully")
                    
                except Exception as refresh_error:
                    logger.error(f"Failed to refresh Calendar credentials: {refresh_error}")
                    return None
            else:
                # Credentials can't be refreshed
                logger.error("Calendar credentials expired and cannot be refreshed")
                return None
        
        # Create and return service
        logger.debug("Creating Calendar service")
        service = build('calendar', 'v3', credentials=creds)
        logger.info("Calendar service created successfully")
        return service
        
    except Exception as e:
        # If anything goes wrong, return None
        logger.error(f"Error getting Calendar service: {e}")
        return None

def check_gmail_connection() -> bool:
    """
    Check if Gmail is properly set up and accessible.
    
    Returns:
        True if Gmail service is available, False otherwise
    """
    logger.debug("Checking Gmail connection")
    service = get_gmail_service()
    if not service:
        logger.warning("Gmail service not available")
        return False
    
    try:
        # Test connection by getting user profile
        logger.debug("Testing Gmail connection with profile request")
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress', 'unknown')
        logger.info(f"Gmail connection verified for {user_email}")
        return True
    except Exception as e:
        logger.error(f"Gmail connection test failed: {e}")
        return False

def check_calendar_connection() -> bool:
    """
    Check if Calendar is properly set up and accessible.
    
    Returns:
        True if Calendar service is available, False otherwise
    """
    logger.debug("Checking Calendar connection")
    service = get_calendar_service()
    if not service:
        logger.warning("Calendar service not available")
        return False
    
    try:
        # Test connection by listing calendars
        logger.debug("Testing Calendar connection with calendar list request")
        calendar_list = service.calendarList().list().execute()
        calendar_count = len(calendar_list.get('items', []))
        logger.info(f"Calendar connection verified with {calendar_count} calendars")
        return True
    except Exception as e:
        logger.error(f"Calendar connection test failed: {e}")
        return False

# Export main functions
__all__ = [
    "get_gmail_service",
    "get_calendar_service", 
    "check_gmail_connection",
    "check_calendar_connection"
]