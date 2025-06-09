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

# Import logging system
from services.logging.logger import setup_logger

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

# Setup logger
logger = setup_logger("gmail_setup", console_output=True)

def setup_gmail_oauth():
    """Set up OAuth 2.0 for Gmail"""
    print("\n=== Oprina Gmail Setup ===\n")
    logger.info("Starting Gmail setup process")
    
    # Check for credentials.json
    if not CREDENTIALS_PATH.exists():
        error_msg = f"Error: {CREDENTIALS_PATH} not found!"
        print(f"❌ {error_msg}")
        logger.error(f"Gmail setup failed: {error_msg}")
        
        print("\nTo set up Gmail integration:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the credentials and save them as 'credentials.json' in the oprina/ directory")
        print("\nThen run this script again.")
        
        logger.info("Provided setup instructions to user")
        return False
    
    print(f"✅ Found credentials.json. Starting OAuth flow...")
    logger.info(f"Found credentials file at {CREDENTIALS_PATH}")
    
    try:
        logger.info("Initiating Gmail OAuth flow")
        # Run the OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        
        logger.info("OAuth flow completed successfully")
        
        # Save the credentials
        with open(GMAIL_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
        
        success_msg = f"Successfully saved Gmail credentials to {GMAIL_TOKEN_PATH}"
        print(f"✅ {success_msg}")
        logger.info(success_msg)
        
        # Test the API connection
        print("\n🔄 Testing connection to Gmail API...")
        logger.info("Testing Gmail API connection")
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile.get('emailAddress', 'Unknown')
        messages_total = profile.get('messagesTotal', 0)
        
        success_msg = f"Success! Connected to Gmail as: {user_email}"
        print(f"✅ {success_msg}")
        logger.info(f"Gmail API connection successful: {user_email}")
        
        print(f"📧 Total messages in account: {messages_total}")
        logger.info(f"Account info - Total messages: {messages_total}")
        
        # Test listing recent messages
        messages_result = service.users().messages().list(userId='me', maxResults=5).execute()
        recent_messages = messages_result.get('messages', [])
        
        if recent_messages:
            message_count = len(recent_messages)
            print(f"📬 Found {message_count} recent messages")
            logger.info(f"Successfully retrieved {message_count} recent messages")
        
        print("\n🎉 Gmail setup complete! You can now use Gmail features in Oprina.")
        print("\nTry saying: 'Check my emails' or 'List my messages'")
        logger.info("Gmail setup completed successfully")
        
        return True
        
    except Exception as e:
        error_msg = f"Error during Gmail setup: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(f"Gmail setup failed: {error_msg}")
        
        # Clean up failed token
        if GMAIL_TOKEN_PATH.exists():
            try:
                GMAIL_TOKEN_PATH.unlink()
                logger.info("Cleaned up failed token file")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup token file: {cleanup_error}")
            
        return False

if __name__ == "__main__":
    logger.info("Gmail setup script started")
    success = setup_gmail_oauth()
    
    if success:
        print("\n✨ Setup completed successfully!")
        logger.info("Gmail setup process completed successfully")
    else:
        print("\n💥 Setup failed. Please check the error messages above.")
        logger.error("Gmail setup process failed")
    
    print("\nPress Enter to exit...")
    input()
    logger.info("Gmail setup script ended")