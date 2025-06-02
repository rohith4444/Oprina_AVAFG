#!/usr/bin/env python3
"""
Script to run the Oprina MCP client.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the client
from mcp_server.client import main, MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main():
    client = MCPClient()
    await client.connect()
    try:
        # Authenticate with Gmail and Calendar first
        await client.authenticate_gmail()
        await client.authenticate_calendar()
        # Now list messages/events
        await client.list_gmail_messages()
        await client.list_calendar_events()
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        logger.info("Starting Oprina MCP client...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Client stopped by user")
    except Exception as e:
        logger.error(f"Error running client: {e}")
        sys.exit(1) 