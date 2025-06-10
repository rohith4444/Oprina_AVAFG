#!/usr/bin/env python3
"""
Calendar Authentication Setup Script for Oprina
This script helps you set up OAuth 2.0 credentials for Google Calendar integration.
Run this once before using Calendar features in Oprina.
"""

import os
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Import logging system
from services.logging.logger import setup_logger

# Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

# Paths
OPRINA_DIR = Path(__file__).parent
CREDENTIALS_PATH = OPRINA_DIR / "credentials.json"
CALENDAR_TOKEN_PATH = OPRINA_DIR / "calendar_token.pickle"

# Setup logger
logger = setup_logger("calendar_setup", console_output=True)

def setup_calendar_oauth():
    """Set up OAuth 2.0 for Google Calendar"""
    print("\n=== Oprina Calendar Setup ===\n")
    logger.info("Starting Calendar setup process")
    
    # Check for credentials.json
    if not CREDENTIALS_PATH.exists():
        error_msg = f"Error: {CREDENTIALS_PATH} not found!"
        print(f"❌ {error_msg}")
        logger.error(f"Calendar setup failed: {error_msg}")
        
        print("\nTo set up Calendar integration:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Google Calendar API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the credentials and save them as 'credentials.json' in the oprina/ directory")
        print("\nThen run this script again.")
        
        logger.info("Provided setup instructions to user")
        return False
    
    print(f"✅ Found credentials.json. Starting OAuth flow...")
    logger.info(f"Found credentials file at {CREDENTIALS_PATH}")
    
    try:
        logger.info("Initiating Calendar OAuth flow")
        # Run the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        
        logger.info("OAuth flow completed successfully")
        
        # Save the credentials
        with open(CALENDAR_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
        
        success_msg = f"Successfully saved Calendar credentials to {CALENDAR_TOKEN_PATH}"
        print(f"✅ {success_msg}")
        logger.info(success_msg)
        
        # Test the API connection
        print("\n🔄 Testing connection to Google Calendar API...")
        logger.info("Testing Calendar API connection")
        service = build('calendar', 'v3', credentials=creds)
        
        # Get calendar list
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        # Find primary calendar
        primary_calendar = next(
            (cal for cal in calendars if cal.get('primary')), 
            None
        )
        
        success_msg = f"Success! Connected to Google Calendar"
        print(f"✅ {success_msg}")
        logger.info("Calendar API connection successful")
        
        calendar_count = len(calendars)
        print(f"📅 Found {calendar_count} calendars:")
        logger.info(f"Found {calendar_count} calendars in account")
        
        for calendar in calendars[:5]:  # Show first 5 calendars
            summary = calendar.get('summary', 'Unnamed Calendar')
            primary_marker = " (Primary)" if calendar.get('primary') else ""
            access_role = calendar.get('accessRole', 'reader')
            print(f"   • {summary}{primary_marker} - {access_role}")
            logger.debug(f"Calendar: {summary}, Role: {access_role}, Primary: {calendar.get('primary', False)}")
        
        if len(calendars) > 5:
            remaining = len(calendars) - 5
            print(f"   ... and {remaining} more calendars")
            logger.info(f"Additional {remaining} calendars not displayed")
        
        # Test getting recent events from primary calendar
        if primary_calendar:
            try:
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                time_min = now.isoformat() + 'Z'
                time_max = (now + timedelta(days=7)).isoformat() + 'Z'
                
                logger.info("Testing event retrieval from primary calendar")
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=5,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                event_count = len(events)
                print(f"📆 Found {event_count} upcoming events in the next 7 days")
                logger.info(f"Successfully retrieved {event_count} upcoming events")
                
            except Exception as e:
                warning_msg = f"Could not fetch events (but authentication is working): {str(e)}"
                print(f"⚠️  {warning_msg}")
                logger.warning(f"Event retrieval test failed: {str(e)}")
        
        print("\n🎉 Calendar setup complete! You can now use Calendar features in Oprina.")
        print("\nTry saying: 'What's on my calendar today?' or 'List my events'")
        logger.info("Calendar setup completed successfully")
        
        return True
        
    except Exception as e:
        error_msg = f"Error during Calendar setup: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(f"Calendar setup failed: {error_msg}")
        
        # Clean up failed token
        if CALENDAR_TOKEN_PATH.exists():
            try:
                CALENDAR_TOKEN_PATH.unlink()
                logger.info("Cleaned up failed token file")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup token file: {cleanup_error}")
            
        return False

if __name__ == "__main__":
    logger.info("Calendar setup script started")
    success = setup_calendar_oauth()
    
    if success:
        print("\n✨ Setup completed successfully!")
        logger.info("Calendar setup process completed successfully")
    else:
        print("\n💥 Setup failed. Please check the error messages above.")
        logger.error("Calendar setup process failed")
    
    print("\nPress Enter to exit...")
    input()
    logger.info("Calendar setup script ended")