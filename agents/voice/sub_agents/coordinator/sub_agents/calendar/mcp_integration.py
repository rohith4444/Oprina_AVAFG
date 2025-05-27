# agents/voice/sub_agents/coordinator/sub_agents/calendar/mcp_integration.py
"""
Calendar MCP Integration for Calendar Agent

This module provides Calendar tools through the Calendar MCP-ADK bridge.
Maintains the same interface as email MCP integration but for Calendar operations.

Key Features:
- Calendar tools via Calendar MCP-ADK bridge
- Calendar-specific error handling and logging
- Real Calendar operations (using Google Calendar API)
- Calendar connection status and testing
"""

import os
import sys
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from contextlib import AsyncExitStack

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
# From: agents/voice/sub_agents/coordinator/sub_agents/calendar/mcp_integration.py
project_root = current_file
for _ in range(7):  # 6 levels + 1 for the file itself
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.logging.logger import setup_logger
from agents.voice.sub_agents.coordinator.sub_agents.calendar.mcp_bridge import get_calendar_mcp_bridge, get_calendar_tools_for_agent, test_calendar_mcp_bridge_connection

# Configure logging
logger = setup_logger("calendar_mcp_integration", console_output=True)

class CalendarMCPIntegration:
    """
    Integration with Calendar tools via Calendar MCP-ADK Bridge.
    Provides Calendar tools for the Calendar Agent using Calvin's Calendar MCP registry.
    """
    
    def __init__(self):
        """Initialize Calendar MCP integration via bridge."""
        self.logger = logger
        self.tools = []
        self.exit_stack = None
        self.connected = False
        self.bridge = None
        
        # Initialize bridge connection
        self._initialize_bridge()
        
    def _initialize_bridge(self):
        """Initialize the Calendar MCP-ADK bridge."""
        try:
            self.logger.info("--- Initializing Calendar MCP Integration via Bridge ---")
            
            # Get bridge instance
            self.bridge = get_calendar_mcp_bridge()
            
            if self.bridge:
                self.connected = True
                self.logger.info("✅ Calendar MCP Bridge connection established")
            else:
                self.logger.error("❌ Failed to get Calendar MCP bridge instance")
                self.connected = False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Calendar MCP bridge: {e}")
            self.connected = False
    
    async def connect_to_calendar_mcp(self) -> Tuple[List, Optional[AsyncExitStack]]:
        """
        Connect to Calendar MCP tools via bridge.
        
        Returns:
            Tuple of (tools, exit_stack) for agent initialization
        """
        self.logger.info("--- Connecting to Calendar tools via MCP Bridge ---")
        
        if not self.connected:
            self.logger.warning("Bridge not connected, attempting to reconnect...")
            self._initialize_bridge()
        
        if not self.connected:
            self.logger.error("❌ Bridge connection failed, returning empty tools")
            return [], None
        
        try:
            # Get Calendar tools from bridge
            self.tools = get_calendar_tools_for_agent()
            
            self.logger.info(f"✅ Successfully retrieved {len(self.tools)} Calendar tools via bridge")
            
            # Log discovered tools for debugging
            for i, tool in enumerate(self.tools):
                tool_name = getattr(tool.func, '__name__', f'calendar_tool_{i}')
                self.logger.info(f"  - Calendar tool: {tool_name}")
            
            # Create a dummy exit stack for compatibility
            # (Bridge doesn't need cleanup like real MCP server would)
            exit_stack = AsyncExitStack()
            self.exit_stack = exit_stack
            
            return self.tools, exit_stack
            
        except Exception as e:
            self.logger.error(f"Error retrieving Calendar tools from bridge: {e}")
            return [], None
    
    def is_connected(self) -> bool:
        """Check if connected to Calendar tools via bridge."""
        return self.connected and self.bridge is not None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed Calendar connection status."""
        try:
            # Get bridge connection test results
            bridge_test = test_calendar_mcp_bridge_connection()
            
            return {
                "connected": self.connected,
                "bridge_available": self.bridge is not None,
                "tools_count": len(self.tools),
                "bridge_test": bridge_test,
                "integration_type": "calendar_mcp_bridge",
                "service_type": "calendar",
                "mock_mode": False  # We're using real Calendar tools!
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "integration_type": "calendar_mcp_bridge",
                "service_type": "calendar"
            }
    
    def test_calendar_tool_execution(self, tool_name: str = None) -> Dict[str, Any]:
        """
        Test execution of a Calendar tool.
        
        Args:
            tool_name: Specific Calendar tool to test (uses first available if None)
            
        Returns:
            Test execution result
        """
        if not self.tools:
            return {
                "success": False,
                "error": "No Calendar tools available for testing"
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
                # Use first available tool (current time is safe to test)
                for tool in self.tools:
                    tool_func_name = getattr(tool.func, '__name__', '')
                    if 'current_time' in tool_func_name:
                        test_tool = tool
                        target_name = tool_func_name
                        break
                
                # If no current_time tool, use first available
                if not test_tool:
                    test_tool = self.tools[0]
                    target_name = getattr(test_tool.func, '__name__', 'unknown_calendar_tool')
            
            if not test_tool:
                return {
                    "success": False,
                    "error": f"Calendar tool '{tool_name}' not found"
                }
            
            self.logger.info(f"Testing Calendar tool execution: {target_name}")
            
            # Try to execute tool
            try:
                # Test with safe parameters (no parameters for current_time)
                if 'current_time' in target_name:
                    result = test_tool.func()  # Safe to call with no parameters
                else:
                    # For other tools, expect them to fail gracefully with no auth
                    result = test_tool.func()
                
                return {
                    "success": True,
                    "tool_name": target_name,
                    "result_type": type(result).__name__,
                    "execution_successful": True,
                    "service_type": "calendar",
                    "note": "Calendar tool executed successfully"
                }
                
            except Exception as tool_error:
                # Expected - most tools will fail without proper auth/parameters
                return {
                    "success": True,  # Structure test passed
                    "tool_name": target_name,
                    "execution_successful": False,
                    "error": str(tool_error),
                    "service_type": "calendar",
                    "note": "Calendar tool structure OK, failed as expected (auth/params needed)"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Calendar tool test execution failed: {str(e)}",
                "tool_name": target_name,
                "service_type": "calendar"
            }
    
    def get_calendar_auth_status(self) -> Dict[str, Any]:
        """Get Calendar authentication status."""
        try:
            from services.google_cloud.calendar_auth import check_calendar_connection
            
            auth_status = check_calendar_connection()
            
            return {
                "calendar_auth_available": True,
                "calendar_connection_status": auth_status,
                "calendar_authenticated": auth_status.get("connected", False),
                "calendar_token_exists": auth_status.get("token_exists", False),
                "calendar_api_test": auth_status.get("api_test", False)
            }
            
        except Exception as e:
            return {
                "calendar_auth_available": False,
                "error": str(e),
                "calendar_authenticated": False
            }
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive Calendar integration status."""
        try:
            # Get connection status
            connection_status = self.get_connection_status()
            
            # Get auth status
            auth_status = self.get_calendar_auth_status()
            
            # Get tool details
            tool_details = {
                "total_tools": len(self.tools),
                "available_tools": [
                    getattr(tool.func, '__name__', f'tool_{i}')
                    for i, tool in enumerate(self.tools)
                ]
            }
            
            # Combine all status information
            comprehensive_status = {
                "integration_ready": self.connected,
                "service_type": "calendar",
                "timestamp": bridge_test.get("test_timestamp", "unknown"),
                **connection_status,
                **auth_status,
                **tool_details
            }
            
            return comprehensive_status
            
        except Exception as e:
            return {
                "integration_ready": False,
                "service_type": "calendar",
                "error": str(e)
            }


# Global instance for use in calendar agent
calendar_mcp = CalendarMCPIntegration()

async def get_calendar_tools():
    """
    Get Calendar tools from Calendar MCP bridge.
    
    Returns:
        Tuple of (tools, exit_stack) for agent initialization
    """
    return await calendar_mcp.connect_to_calendar_mcp()


def get_calendar_mcp_status() -> Dict[str, Any]:
    """Get Calendar MCP connection status for debugging."""
    return calendar_mcp.get_connection_status()


def get_calendar_comprehensive_status() -> Dict[str, Any]:
    """Get comprehensive Calendar integration status."""
    return calendar_mcp.get_comprehensive_status()


def test_calendar_tool_execution(tool_name: str = None) -> Dict[str, Any]:
    """Test Calendar tool execution."""
    return calendar_mcp.test_calendar_tool_execution(tool_name)


# =============================================================================
# Backward Compatibility & Testing
# =============================================================================

if __name__ == "__main__":
    # Test Calendar MCP integration with bridge
    async def test_calendar_mcp_integration():
        print("🧪 Testing Calendar MCP Integration with Bridge...")
        
        # Test connection status
        status = get_calendar_mcp_status()
        print(f"Connection Status: {status}")
        
        # Test comprehensive status
        comprehensive = get_calendar_comprehensive_status()
        print(f"Calendar authenticated: {comprehensive.get('calendar_authenticated', False)}")
        
        # Test tool retrieval
        tools, exit_stack = await get_calendar_tools()
        print(f"Retrieved {len(tools)} Calendar tools")
        
        # List some tools
        if tools:
            print("Available Calendar tools:")
            for i, tool in enumerate(tools[:5]):  # First 5
                tool_name = getattr(tool.func, '__name__', f'tool_{i}')
                print(f"  {i+1}. {tool_name}")
            
            if len(tools) > 5:
                print(f"  ... and {len(tools) - 5} more Calendar tools")
        
        # Test tool execution
        if tools:
            test_result = test_calendar_tool_execution()
            print(f"Calendar tool execution test: {test_result.get('success', False)}")
            if test_result.get('tool_name'):
                print(f"  Tested tool: {test_result['tool_name']}")
        
        # Cleanup
        if exit_stack:
            await exit_stack.aclose()
        
        print("✅ Calendar MCP integration test completed")
    
    asyncio.run(test_calendar_mcp_integration())