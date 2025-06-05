#!/usr/bin/env python3
"""
Simple test client for the MCP server.

This script tests the MCP server by sending messages to stdin and reading from stdout.
It verifies that the server correctly implements the MCP protocol.
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPTestClient:
    """Simple test client for the MCP server."""
    
    def __init__(self):
        """Initialize the test client."""
        self.process = None
        self.stdin = None
        self.stdout = None
        self.stderr = None
    
    async def start_server(self):
        """Start the MCP server as a subprocess."""
        logger.info("Starting MCP server...")
        
        # Start the server as a subprocess
        self.process = subprocess.Popen(
            [sys.executable, "mcp_server/run_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        self.stdin = self.process.stdin
        self.stdout = self.process.stdout
        self.stderr = self.process.stderr
        
        logger.info("MCP server started")
    
    async def stop_server(self):
        """Stop the MCP server."""
        if self.process:
            logger.info("Stopping MCP server...")
            self.process.terminate()
            await asyncio.sleep(1)
            if self.process.poll() is None:
                self.process.kill()
            logger.info("MCP server stopped")
    
    async def send_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a message to the MCP server and read the response."""
        if not self.stdin or not self.stdout:
            logger.error("Server not started")
            return None
        
        # Send the message
        logger.info(f"Sending message: {message}")
        self.stdin.write(json.dumps(message) + "\n")
        self.stdin.flush()
        
        # Read the response
        response_line = self.stdout.readline()
        if not response_line:
            logger.error("No response from server")
            return None
        
        try:
            response = json.loads(response_line)
            logger.info(f"Received response: {response}")
            return response
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response_line}")
            return None
    
    async def test_hello(self) -> bool:
        """Test the HELLO message."""
        logger.info("Testing HELLO message...")
        
        response = await self.send_message({
            "type": "hello"
        })
        
        if not response:
            logger.error("No response to HELLO message")
            return False
        
        if response.get("type") != "hello":
            logger.error(f"Invalid response type: {response.get('type')}")
            return False
        
        if "version" not in response:
            logger.error("No version in response")
            return False
        
        if "capabilities" not in response:
            logger.error("No capabilities in response")
            return False
        
        logger.info("HELLO message test passed")
        return True
    
    async def test_tool_discovery(self) -> bool:
        """Test the TOOL_DISCOVERY message."""
        logger.info("Testing TOOL_DISCOVERY message...")
        
        response = await self.send_message({
            "type": "tool_discovery"
        })
        
        if not response:
            logger.error("No response to TOOL_DISCOVERY message")
            return False
        
        if response.get("type") != "tool_discovery":
            logger.error(f"Invalid response type: {response.get('type')}")
            return False
        
        if "version" not in response:
            logger.error("No version in response")
            return False
        
        if "tools" not in response:
            logger.error("No tools in response")
            return False
        
        logger.info(f"TOOL_DISCOVERY message test passed. Found {len(response['tools'])} tools")
        return True
    
    async def test_tool_call(self, tool_name: str, params: Dict[str, Any]) -> bool:
        """Test the TOOL_CALL message."""
        logger.info(f"Testing TOOL_CALL message for {tool_name}...")
        
        response = await self.send_message({
            "type": "tool_call",
            "tool": tool_name,
            "params": params
        })
        
        if not response:
            logger.error(f"No response to TOOL_CALL message for {tool_name}")
            return False
        
        if response.get("type") != "tool_result":
            logger.error(f"Invalid response type: {response.get('type')}")
            return False
        
        if response.get("tool") != tool_name:
            logger.error(f"Invalid tool in response: {response.get('tool')}")
            return False
        
        if "result" not in response:
            logger.error("No result in response")
            return False
        
        logger.info(f"TOOL_CALL message test for {tool_name} passed")
        return True

async def main():
    """Run the test client."""
    client = MCPTestClient()
    
    try:
        # Start the server
        await client.start_server()
        
        # Test the HELLO message
        if not await client.test_hello():
            logger.error("HELLO message test failed")
            return
        
        # Test the TOOL_DISCOVERY message
        if not await client.test_tool_discovery():
            logger.error("TOOL_DISCOVERY message test failed")
            return
        
        # Test the TOOL_CALL message for gmail_check_connection
        if not await client.test_tool_call("gmail_check_connection", {}):
            logger.error("TOOL_CALL message test for gmail_check_connection failed")
            return
        
        logger.info("All tests passed!")
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
    finally:
        # Stop the server
        await client.stop_server()

if __name__ == "__main__":
    asyncio.run(main()) 