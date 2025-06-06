#!/usr/bin/env python3
"""
Gmail Authentication Setup Script for Oprina
This script helps you set up OAuth 2.0 credentials for Gmail integration.
Run this once before using Gmail features in Oprina.
"""

import os
import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose'
]

# Paths
OPRINA_DIR = Path(__file__).parent
CREDENTIALS_PATH = OPRINA_DIR / "credentials.json"
GMAIL_TOKEN_PATH = OPRINA_DIR / "gmail_token.pickle"

def setup_gmail_oauth():
    """Set up OAuth 2.0 for Gmail"""
    print("\n=== Oprina Gmail Setup ===\n")
    
    # Check for credentials.json
    if not CREDENTIALS_PATH.exists():
        print(f"❌ Error: {CREDENTIALS_PATH} not found!")
        print("\nTo set up Gmail integration:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Gmail API")
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
        with open(GMAIL_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
        
        print(f"✅ Successfully saved Gmail credentials to {GMAIL_TOKEN_PATH}")
        
        # Test the API connection
        print("\n🔄 Testing connection to Gmail API...")
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress', 'Unknown')
        messages_total = profile.get('messagesTotal', 0)
        
        print(f"✅ Success! Connected to Gmail as: {user_email}")
        print(f"📧 Total messages in account: {messages_total}")
        
        # Test listing recent messages
        messages_result = service.users().messages().list(userId='me', maxResults=5).execute()
        recent_messages = messages_result.get('messages', [])
        
        if recent_messages:
            print(f"📬 Found {len(recent_messages)} recent messages")
        
        print("\n🎉 Gmail setup complete! You can now use Gmail features in Oprina.")
        print("\nTry saying: 'Check my emails' or 'List my messages'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Gmail setup: {str(e)}")
        
        # Clean up failed token
        if GMAIL_TOKEN_PATH.exists():
            GMAIL_TOKEN_PATH.unlink()
            
        return False

if __name__ == "__main__":
    success = setup_gmail_oauth()
    
    if success:
        print("\n✨ Setup completed successfully!")
    else:
        print("\n💥 Setup failed. Please check the error messages above.")
    
    input("\nPress Enter to exit...")