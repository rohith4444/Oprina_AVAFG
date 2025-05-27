"""
Calendar MCP-ADK Bridge

This module bridges Calvin's Calendar MCP tools with ADK's agent system.
Converts Calendar MCP tool classes into ADK FunctionTools that can be used by the calendar agent.

Key Features:
- Convert Calendar MCP tool registry to ADK FunctionTools
- Handle tool execution and error management specific to Calendar operations
- Provide clean interface for calendar agent
- Support for Calendar API operations
"""

import os
import sys
import inspect
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
# From: agents/voice/sub_agents/coordinator/sub_agents/calendar/mcp_bridge.py
# Need to go up 7 levels to reach project root
project_root = current_file
for _ in range(7):  # 7 levels + 1 for the file itself
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("calendar_mcp_bridge", console_output=True)


class CalendarMCPBridge:
    """
    Bridge between Calvin's Calendar MCP tools and ADK agent system.
    Converts Calendar MCP tool classes into ADK FunctionTools for agent use.
    """
    
    def __init__(self):
        """Initialize the Calendar MCP-ADK bridge."""
        self.logger = logger
        self.logger.info("--- Initializing Calendar MCP-ADK Bridge ---")
        
        # Track converted tools and performance
        self.converted_tools = {}
        self.tool_execution_stats = {}
        
        # Import MCP modules
        try:
            from google_mcp import mcp_discovery
            from google_mcp.mcp_tool import TOOL_REGISTRY
            
            self.mcp_discovery = mcp_discovery
            self.tool_registry = TOOL_REGISTRY
            
            # Count calendar tools
            calendar_tools = [name for name in TOOL_REGISTRY.keys() if 'calendar' in name.lower()]
            self.logger.info(f"--- Calendar MCP Bridge initialized with {len(calendar_tools)} calendar tools ---")
            
        except ImportError as e:
            self.logger.error(f"Failed to import MCP modules: {e}")
            self.mcp_discovery = None
            self.tool_registry = {}
    
    def get_calendar_tools(self) -> List[FunctionTool]:
        """
        Convert Calendar MCP tools to ADK FunctionTools.
        
        Returns:
            List of Calendar-specific ADK FunctionTools
        """
        if not self.mcp_discovery:
            self.logger.warning("MCP discovery not available, returning empty tool list")
            return []
        
        try:
            # Get all available tools from MCP registry
            available_tools = self.mcp_discovery.list_tools()
            calendar_tools = []
            
            # Filter for calendar tools only
            for tool_info in available_tools:
                tool_name = tool_info["name"]
                tool_description = tool_info["description"]
                
                # Only include calendar tools
                if 'calendar' in tool_name.lower():
                    # Create ADK-compatible function
                    adk_function = self._create_calendar_adk_function(tool_name, tool_description)
                    
                    # Create ADK FunctionTool
                    adk_tool = FunctionTool(func=adk_function)
                    calendar_tools.append(adk_tool)
                    
                    # Track converted tool
                    self.converted_tools[tool_name] = {
                        "description": tool_description,
                        "adk_tool": adk_tool,
                        "converted_at": datetime.utcnow().isoformat(),
                        "type": "calendar"
                    }
                    
                    self.logger.debug(f"  ✅ Converted Calendar tool: {tool_name}")
            
            self.logger.info(f"--- Successfully converted {len(calendar_tools)} Calendar tools ---")
            return calendar_tools
            
        except Exception as e:
            self.logger.error(f"Error converting Calendar MCP tools to ADK: {e}")
            return []
    
    def _create_calendar_adk_function(self, tool_name: str, tool_description: str) -> Callable:
        """
        Create an ADK-compatible function wrapper for a Calendar MCP tool.
        
        Args:
            tool_name: Name of the Calendar MCP tool
            tool_description: Description of the tool
            
        Returns:
            Function that can be used by ADK FunctionTool
        """
        def calendar_adk_tool_wrapper(**kwargs) -> Dict[str, Any]:
            """
            ADK-compatible wrapper for Calendar MCP tool execution.
            
            Args:
                **kwargs: Tool parameters
                
            Returns:
                Tool execution result with metadata
            """
            start_time = datetime.utcnow()
            
            try:
                self.logger.debug(f"Executing Calendar MCP tool: {tool_name} with args: {list(kwargs.keys())}")
                
                # Execute the Calendar MCP tool
                result = self.mcp_discovery.run_tool(tool_name, **kwargs)
                
                # Calculate execution time
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds() * 1000  # ms
                
                # Track execution stats
                self._update_execution_stats(tool_name, execution_time, True)
                
                # Wrap result with metadata for ADK
                wrapped_result = {
                    "success": True,
                    "result": result,
                    "tool_name": tool_name,
                    "tool_type": "calendar",
                    "execution_time_ms": execution_time,
                    "timestamp": end_time.isoformat()
                }
                
                self.logger.debug(f"Calendar tool {tool_name} executed successfully in {execution_time:.2f}ms")
                return wrapped_result
                
            except Exception as e:
                # Calculate execution time even for errors
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds() * 1000  # ms
                
                # Track execution stats
                self._update_execution_stats(tool_name, execution_time, False)
                
                self.logger.error(f"Error executing Calendar MCP tool {tool_name}: {e}")
                
                # Return error result in consistent format
                error_result = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "tool_name": tool_name,
                    "tool_type": "calendar",
                    "execution_time_ms": execution_time,
                    "timestamp": end_time.isoformat()
                }
                
                return error_result
        
        # Set function metadata for ADK
        calendar_adk_tool_wrapper.__name__ = tool_name
        calendar_adk_tool_wrapper.__doc__ = f"Calendar Tool: {tool_description}"
        
        # Add tool signature inspection for better ADK integration
        if tool_name in self.tool_registry:
            try:
                tool_class = self.tool_registry[tool_name]
                if hasattr(tool_class, 'run'):
                    # Copy signature from original run method
                    original_signature = inspect.signature(tool_class.run)
                    calendar_adk_tool_wrapper.__signature__ = original_signature
            except Exception as e:
                self.logger.warning(f"Could not copy signature for Calendar tool {tool_name}: {e}")
        
        return calendar_adk_tool_wrapper
    
    def _update_execution_stats(self, tool_name: str, execution_time: float, success: bool):
        """Update execution statistics for Calendar tool performance tracking."""
        if tool_name not in self.tool_execution_stats:
            self.tool_execution_stats[tool_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_time_ms": 0,
                "avg_time_ms": 0,
                "last_execution": None,
                "tool_type": "calendar"
            }
        
        stats = self.tool_execution_stats[tool_name]
        stats["total_executions"] += 1
        stats["total_time_ms"] += execution_time
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["total_executions"]
        stats["last_execution"] = datetime.utcnow().isoformat()
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
    
    def get_calendar_tool_info(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about converted Calendar tools and their performance.
        
        Args:
            tool_name: Specific tool name to get info for (None for all)
            
        Returns:
            Calendar tool information and statistics
        """
        if tool_name:
            return {
                "tool_info": self.converted_tools.get(tool_name, {}),
                "execution_stats": self.tool_execution_stats.get(tool_name, {})
            }
        
        # Filter for calendar tools only
        calendar_tools = {k: v for k, v in self.converted_tools.items() if v.get("type") == "calendar"}
        calendar_stats = {k: v for k, v in self.tool_execution_stats.items() if v.get("tool_type") == "calendar"}
        
        return {
            "total_calendar_tools_converted": len(calendar_tools),
            "calendar_tools_available": list(calendar_tools.keys()),
            "calendar_execution_stats": calendar_stats,
            "bridge_status": {
                "mcp_available": self.mcp_discovery is not None,
                "calendar_tools_in_registry": len([k for k in self.tool_registry.keys() if 'calendar' in k.lower()])
            }
        }
    
    def test_calendar_tool_execution(self, tool_name: str, **test_kwargs) -> Dict[str, Any]:
        """
        Test execution of a specific Calendar tool with given parameters.
        
        Args:
            tool_name: Name of Calendar tool to test
            **test_kwargs: Test parameters
            
        Returns:
            Test execution result
        """
        if tool_name not in self.converted_tools:
            return {
                "success": False,
                "error": f"Calendar tool {tool_name} not found in converted tools"
            }
        
        if not tool_name.lower().startswith('calendar'):
            return {
                "success": False,
                "error": f"Tool {tool_name} is not a Calendar tool"
            }
        
        try:
            adk_tool = self.converted_tools[tool_name]["adk_tool"]
            result = adk_tool.func(**test_kwargs)
            
            return {
                "success": True,
                "test_result": result,
                "tool_name": tool_name,
                "tool_type": "calendar",
                "test_parameters": test_kwargs
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "tool_type": "calendar",
                "test_parameters": test_kwargs
            }


# =============================================================================
# Singleton Bridge Instance for Calendar
# =============================================================================

# Global calendar bridge instance for use across calendar agent
_calendar_mcp_bridge_instance = None


def get_calendar_mcp_bridge() -> CalendarMCPBridge:
    """Get singleton Calendar MCP-ADK bridge instance."""
    global _calendar_mcp_bridge_instance
    if _calendar_mcp_bridge_instance is None:
        _calendar_mcp_bridge_instance = CalendarMCPBridge()
    return _calendar_mcp_bridge_instance


# =============================================================================
# Convenience Functions for Calendar Agent
# =============================================================================

def get_calendar_tools_for_agent() -> List[FunctionTool]:
    """
    Convenience function to get Calendar tools for calendar agent.
    
    Returns:
        List of Calendar ADK FunctionTools ready for agent use
    """
    bridge = get_calendar_mcp_bridge()
    return bridge.get_calendar_tools()


def test_calendar_mcp_bridge_connection() -> Dict[str, Any]:
    """
    Test the Calendar MCP bridge connection and tool availability.
    
    Returns:
        Calendar bridge connection test results
    """
    bridge = get_calendar_mcp_bridge()
    
    test_results = {
        "bridge_initialized": bridge is not None,
        "mcp_discovery_available": bridge.mcp_discovery is not None,
        "calendar_tools_count": len(bridge.get_calendar_tools()),
        "test_timestamp": datetime.utcnow().isoformat(),
        "bridge_type": "calendar_specific"
    }
    
    # Get detailed calendar tool info
    calendar_info = bridge.get_calendar_tool_info()
    test_results.update(calendar_info)
    
    return test_results


# =============================================================================
# Export Key Components
# =============================================================================

__all__ = [
    "CalendarMCPBridge",
    "get_calendar_mcp_bridge",
    "get_calendar_tools_for_agent",
    "test_calendar_mcp_bridge_connection"
]


# =============================================================================
# Testing and Development
# =============================================================================

if __name__ == "__main__":
    def test_calendar_bridge():
        """Test the Calendar MCP-ADK bridge functionality."""
        print("📅 Testing Calendar MCP-ADK Bridge...")
        
        # Test bridge initialization
        bridge = get_calendar_mcp_bridge()
        print(f"✅ Calendar Bridge initialized: {bridge is not None}")
        
        # Test tool conversion
        calendar_tools = bridge.get_calendar_tools()
        print(f"📅 Calendar tools converted: {len(calendar_tools)}")
        
        # Test tool info
        tool_info = bridge.get_calendar_tool_info()
        print(f"📊 Total Calendar tools converted: {tool_info['total_calendar_tools_converted']}")
        
        # Test connection
        connection_test = test_calendar_mcp_bridge_connection()
        print(f"🔗 Connection test: {connection_test['bridge_initialized']}")
        
        # List some converted tools
        print("\n🔧 Available Calendar Tools:")
        for i, tool in enumerate(calendar_tools[:5]):  # Show first 5
            tool_name = getattr(tool.func, '__name__', f'tool_{i}')
            print(f"  - {tool_name}")
        
        if len(calendar_tools) > 5:
            print(f"  ... and {len(calendar_tools) - 5} more calendar tools")
        
        print("\n✅ Calendar MCP-ADK Bridge test completed!")
    
    test_calendar_bridge()