"""
Test script to verify the connection between the ADK web server and the MCP server.
"""

import asyncio
import sys
import os
from mcp_server.client import MCPClient
from config.settings import settings

async def test_mcp_connection():
    """Test the connection to the MCP server."""
    print("Testing connection to MCP server...")
    
    # Create MCP client with correct port (8765 instead of settings.MCP_PORT)
    mcp_client = MCPClient(
        host=settings.MCP_HOST,
        port=8765  # Use the correct port where the MCP server is running
    )
    
    try:
        # Connect to the MCP server
        await mcp_client.connect()
        print(f"✅ Successfully connected to MCP server at {settings.MCP_HOST}:8765")
        
        # Test Gmail authentication
        print("\nTesting Gmail authentication...")
        response = await mcp_client.authenticate_gmail()
        print(f"Gmail authentication response: {response}")
        
        # Test Calendar authentication
        print("\nTesting Calendar authentication...")
        response = await mcp_client.authenticate_calendar()
        print(f"Calendar authentication response: {response}")
        
        # Test listing Gmail messages
        print("\nTesting Gmail message listing...")
        response = await mcp_client.list_gmail_messages(query="is:unread", max_results=5)
        print(f"Gmail message listing response: {response}")
        
        # Test listing Calendar events
        print("\nTesting Calendar event listing...")
        response = await mcp_client.list_calendar_events(max_results=5)
        print(f"Calendar event listing response: {response}")
        
        # Disconnect from the MCP server
        await mcp_client.disconnect()
        print("\n✅ Successfully disconnected from MCP server")
        
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_connection()) 