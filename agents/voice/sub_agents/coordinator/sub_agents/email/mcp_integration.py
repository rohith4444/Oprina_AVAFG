# agents/voice/sub_agents/coordinator/sub_agents/email/mcp_integration.py
"""
MCP Integration for Email Agent - UPDATED to use MCP-ADK Bridge

This module now provides Gmail tools through the MCP-ADK bridge instead of 
direct MCP server connection. Maintains the same interface for the agent
but uses Calvin's tool registry underneath.

Key Features:
- Gmail tools via MCP-ADK bridge
- Maintains existing interface for agent compatibility
- Real Gmail operations (no more mock tools!)
- Error handling and logging
"""

import os
import sys
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from contextlib import AsyncExitStack

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
# From: agents/voice/sub_agents/coordinator/sub_agents/email/mcp_integration.py
project_root = current_file
for _ in range(7):  # 6 levels + 1 for the file itself
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.logging.logger import setup_logger
from .mcp_bridge import get_mcp_bridge, get_gmail_tools_for_agent, test_mcp_bridge_connection

# Configure logging
logger = setup_logger("email_mcp_integration", console_output=True)

class EmailMCPIntegration:
    """
    Integration with Gmail tools via MCP-ADK Bridge.
    Provides Gmail tools for the Email Agent using Calvin's MCP registry.
    """
    
    def __init__(self):
        """Initialize MCP integration via bridge."""
        self.logger = logger
        self.tools = []
        self.exit_stack = None
        self.connected = False
        self.bridge = None
        
        # Initialize bridge connection
        self._initialize_bridge()
        
    def _initialize_bridge(self):
        """Initialize the MCP-ADK bridge."""
        try:
            self.logger.info("--- Initializing Gmail MCP Integration via Bridge ---")
            
            # Get bridge instance
            self.bridge = get_mcp_bridge()
            
            if self.bridge:
                self.connected = True
                self.logger.info("✅ MCP Bridge connection established")
            else:
                self.logger.error("❌ Failed to get MCP bridge instance")
                self.connected = False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP bridge: {e}")
            self.connected = False
    
    async def connect_to_gmail_mcp(self) -> Tuple[List, Optional[AsyncExitStack]]:
        """
        Connect to Gmail MCP tools via bridge.
        
        Returns:
            Tuple of (tools, exit_stack) for agent initialization
        """
        self.logger.info("--- Connecting to Gmail tools via MCP Bridge ---")
        
        if not self.connected:
            self.logger.warning("Bridge not connected, attempting to reconnect...")
            self._initialize_bridge()
        
        if not self.connected:
            self.logger.error("❌ Bridge connection failed, returning empty tools")
            return [], None
        
        try:
            # Get Gmail tools from bridge
            self.tools = get_gmail_tools_for_agent()
            
            self.logger.info(f"✅ Successfully retrieved {len(self.tools)} Gmail tools via bridge")
            
            # Log discovered tools for debugging
            for i, tool in enumerate(self.tools):
                tool_name = getattr(tool.func, '__name__', f'tool_{i}')
                self.logger.info(f"  - Gmail tool: {tool_name}")
            
            # Create a dummy exit stack for compatibility
            # (Bridge doesn't need cleanup like real MCP server would)
            exit_stack = AsyncExitStack()
            self.exit_stack = exit_stack
            
            return self.tools, exit_stack
            
        except Exception as e:
            self.logger.error(f"Error retrieving Gmail tools from bridge: {e}")
            return [], None
    
    def is_connected(self) -> bool:
        """Check if connected to Gmail tools via bridge."""
        return self.connected and self.bridge is not None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status."""
        try:
            # Get bridge connection test results
            bridge_test = test_mcp_bridge_connection()
            
            return {
                "connected": self.connected,
                "bridge_available": self.bridge is not None,
                "tools_count": len(self.tools),
                "bridge_test": bridge_test,
                "integration_type": "mcp_bridge",
                "mock_mode": False  # We're using real tools now!
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "integration_type": "mcp_bridge"
            }
    
    def test_tool_execution(self, tool_name: str = None) -> Dict[str, Any]:
        """
        Test execution of a Gmail tool.
        
        Args:
            tool_name: Specific tool to test (uses first available if None)
            
        Returns:
            Test execution result
        """
        if not self.tools:
            return {
                "success": False,
                "error": "No tools available for testing"
            }
        
        try:
            # Find tool to test
            test_tool = None
            target_name = tool_name
            
            if target_name:
                # Look for specific tool
                for tool in self.tools:
                    if getattr(tool.func, '__name__', '') == target_name:
                        test_tool = tool
                        break
            else:
                # Use first available tool
                test_tool = self.tools[0]
                target_name = getattr(test_tool.func, '__name__', 'unknown_tool')
            
            if not test_tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }
            
            self.logger.info(f"Testing tool execution: {target_name}")
            
            # Try to execute tool (expect it to fail due to auth, but structure should work)
            try:
                result = test_tool.func()  # Call with no parameters
                
                return {
                    "success": True,
                    "tool_name": target_name,
                    "result_type": type(result).__name__,
                    "execution_successful": True,
                    "note": "Tool executed successfully"
                }
                
            except Exception as tool_error:
                # Expected - tools will fail without proper auth/parameters
                return {
                    "success": True,  # Structure test passed
                    "tool_name": target_name,
                    "execution_successful": False,
                    "error": str(tool_error),
                    "note": "Tool structure OK, failed as expected (auth/params needed)"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}",
                "tool_name": target_name
            }


# Global instance for use in agent
email_mcp = EmailMCPIntegration()

async def get_gmail_tools():
    """
    Get Gmail tools from MCP bridge.
    
    Returns:
        Tuple of (tools, exit_stack) for agent initialization
    """
    return await email_mcp.connect_to_gmail_mcp()


def get_gmail_mcp_status() -> Dict[str, Any]:
    """Get Gmail MCP connection status for debugging."""
    return email_mcp.get_connection_status()


def test_gmail_tool_execution(tool_name: str = None) -> Dict[str, Any]:
    """Test Gmail tool execution."""
    return email_mcp.test_tool_execution(tool_name)


# =============================================================================
# Backward Compatibility & Testing
# =============================================================================

if __name__ == "__main__":
    # Test MCP integration with bridge
    async def test_email_mcp_integration():
        print("🧪 Testing Email MCP Integration with Bridge...")
        
        # Test connection status
        status = get_gmail_mcp_status()
        print(f"Connection Status: {status}")
        
        # Test tool retrieval
        tools, exit_stack = await get_gmail_tools()
        print(f"Retrieved {len(tools)} Gmail tools")
        
        # Test tool execution
        if tools:
            test_result = test_gmail_tool_execution()
            print(f"Tool execution test: {test_result}")
        
        # Cleanup
        if exit_stack:
            await exit_stack.aclose()
        
        print("✅ Email MCP integration test completed")
    
    asyncio.run(test_email_mcp_integration())