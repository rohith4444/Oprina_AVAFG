#!/usr/bin/env python3
"""
Script to set up authentication with Google services for the Oprina MCP server.
"""

import os
import sys
import json
import asyncio
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define the scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

async def authenticate():
    """Authenticate with Google services."""
    creds = None
    token_file = 'credentials/gmail_token.json'
    
    # Check if token file exists
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
    
    # If credentials are not valid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                creds = None
        
        if not creds:
            try:
                # Check if client_secrets.json exists
                if not os.path.exists('client_secrets.json'):
                    logger.error("client_secrets.json not found. Please download it from the Google Cloud Console.")
                    return False
                
                # Create flow instance
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', SCOPES)
                
                # Run the local server
                creds = flow.run_local_server(port=0)
                
                # Save the credentials
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
                
                logger.info("Authentication successful!")
                return True
            except Exception as e:
                logger.error(f"Error during authentication: {e}")
                return False
    
    logger.info("Already authenticated!")
    return True

async def main():
    """Main entry point for the authentication script."""
    try:
        logger.info("Setting up authentication with Google services...")
        success = await authenticate()
        if success:
            logger.info("Authentication setup complete!")
        else:
            logger.error("Authentication setup failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during authentication setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 