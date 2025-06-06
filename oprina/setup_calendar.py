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

def setup_calendar_oauth():
    """Set up OAuth 2.0 for Google Calendar"""
    print("\n=== Oprina Calendar Setup ===\n")
    
    # Check for credentials.json
    if not CREDENTIALS_PATH.exists():
        print(f"❌ Error: {CREDENTIALS_PATH} not found!")
        print("\nTo set up Calendar integration:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Google Calendar API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the credentials and save them as 'credentials.json' in the oprina/ directory")
        print("\nThen run this script again.")
        return False
    
    print(f"✅ Found credentials.json. Starting OAuth flow...")
    
    try:
        # Run the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save the credentials
        with open(CALENDAR_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
        
        print(f"✅ Successfully saved Calendar credentials to {CALENDAR_TOKEN_PATH}")
        
        # Test the API connection
        print("\n🔄 Testing connection to Google Calendar API...")
        service = build('calendar', 'v3', credentials=creds)
        
        # Get calendar list
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        # Find primary calendar
        primary_calendar = next(
            (cal for cal in calendars if cal.get('primary')), 
            None
        )
        
        print(f"✅ Success! Connected to Google Calendar")
        print(f"📅 Found {len(calendars)} calendars:")
        
        for calendar in calendars[:5]:  # Show first 5 calendars
            summary = calendar.get('summary', 'Unnamed Calendar')
            primary_marker = " (Primary)" if calendar.get('primary') else ""
            access_role = calendar.get('accessRole', 'reader')
            print(f"   • {summary}{primary_marker} - {access_role}")
        
        if len(calendars) > 5:
            print(f"   ... and {len(calendars) - 5} more calendars")
        
        # Test getting recent events from primary calendar
        if primary_calendar:
            try:
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                time_min = now.isoformat() + 'Z'
                time_max = (now + timedelta(days=7)).isoformat() + 'Z'
                
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=5,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                print(f"📆 Found {len(events)} upcoming events in the next 7 days")
                
            except Exception as e:
                print(f"⚠️  Could not fetch events (but authentication is working): {str(e)}")
        
        print("\n🎉 Calendar setup complete! You can now use Calendar features in Oprina.")
        print("\nTry saying: 'What's on my calendar today?' or 'List my events'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Calendar setup: {str(e)}")
        
        # Clean up failed token
        if CALENDAR_TOKEN_PATH.exists():
            CALENDAR_TOKEN_PATH.unlink()
            
        return False

if __name__ == "__main__":
    success = setup_calendar_oauth()
    
    if success:
        print("\n✨ Setup completed successfully!")
    else:
        print("\n💥 Setup failed. Please check the error messages above.")
    
    input("\nPress Enter to exit...")