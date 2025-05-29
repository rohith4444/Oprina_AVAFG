"""
Integration tests for the Oprina MCP server.
"""

import os
import sys
import json
import asyncio
import unittest
import websockets
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the server and client
from mcp_server.server import MCPServer
from mcp_server.client import MCPClient

# Load environment variables
load_dotenv()

class TestMCPServer(unittest.TestCase):
    """Integration tests for the MCP server."""
    
    def setUp(self):
        """Set up the test environment."""
        self.host = os.getenv("MCP_HOST", "localhost")
        self.port = int(os.getenv("MCP_PORT", "8765"))
        self.server = MCPServer(self.host, self.port)
        self.client = MCPClient(self.host, self.port)
    
    async def asyncSetUp(self):
        """Set up the test environment asynchronously."""
        # Start the server
        self.server_task = asyncio.create_task(self.server.start())
        # Wait for the server to start
        await asyncio.sleep(1)
        # Connect the client
        await self.client.connect()
    
    async def asyncTearDown(self):
        """Tear down the test environment asynchronously."""
        # Disconnect the client
        await self.client.disconnect()
        # Stop the server
        self.server_task.cancel()
        try:
            await self.server_task
        except asyncio.CancelledError:
            pass
    
    def test_gmail_list_messages(self):
        """Test listing Gmail messages."""
        async def run_test():
            await self.asyncSetUp()
            response = await self.client.list_gmail_messages("is:unread", 5)
            self.assertEqual(response["status"], "success")
            self.assertIn("data", response)
            await self.asyncTearDown()
        
        asyncio.run(run_test())
    
    def test_calendar_list_events(self):
        """Test listing Calendar events."""
        async def run_test():
            await self.asyncSetUp()
            response = await self.client.list_calendar_events(max_results=5)
            self.assertEqual(response["status"], "success")
            self.assertIn("data", response)
            await self.asyncTearDown()
        
        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main() 