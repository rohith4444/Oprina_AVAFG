"""
MCP-ADK Bridge for Email Agent

This module bridges Calvin's MCP tool registry with ADK's agent system.
Converts Calvin's tool classes into ADK FunctionTools that can be used by agents.

Key Features:
- Convert MCP tool registry to ADK FunctionTools
- Handle tool execution and error management
- Provide clean interface for agents
- Support for both Gmail and future Calendar tools
"""

import os
import sys
import inspect
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
# From: agents/voice/sub_agents/coordinator/sub_agents/email/mcp_bridge.py
# Need to go up 6 levels to reach project root
project_root = current_file
for _ in range(7):  # 6 levels + 1 for the file itself
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("mcp_adk_bridge", console_output=True)


class MCPADKBridge:
    """
    Bridge between Calvin's MCP tools and ADK agent system.
    Converts MCP tool classes into ADK FunctionTools for agent use.
    """
    
    def __init__(self):
        """Initialize the MCP-ADK bridge."""
        self.logger = logger
        self.logger.info("--- Initializing MCP-ADK Bridge ---")
        
        # Track converted tools and performance
        self.converted_tools = {}
        self.tool_execution_stats = {}
        
        # Import MCP modules
        try:
            from google_mcp import mcp_discovery
            from google_mcp.mcp_tool import TOOL_REGISTRY
            
            self.mcp_discovery = mcp_discovery
            self.tool_registry = TOOL_REGISTRY
            
            self.logger.info(f"--- MCP Bridge initialized with {len(TOOL_REGISTRY)} tools ---")
            
        except ImportError as e:
            self.logger.error(f"Failed to import MCP modules: {e}")
            self.mcp_discovery = None
            self.tool_registry = {}
    
    def get_all_tools(self) -> List[FunctionTool]:
        """
        Convert all MCP tools to ADK FunctionTools.
        
        Returns:
            List of ADK FunctionTools ready for agent use
        """
        if not self.mcp_discovery:
            self.logger.warning("MCP discovery not available, returning empty tool list")
            return []
        
        try:
            # Get all available tools from MCP registry
            available_tools = self.mcp_discovery.list_tools()
            adk_tools = []
            
            self.logger.info(f"Converting {len(available_tools)} MCP tools to ADK format...")
            
            for tool_info in available_tools:
                tool_name = tool_info["name"]
                tool_description = tool_info["description"]
                
                # Create ADK-compatible function
                adk_function = self._create_adk_function(tool_name, tool_description)
                
                # Create ADK FunctionTool
                adk_tool = FunctionTool(func=adk_function)
                adk_tools.append(adk_tool)
                
                # Track converted tool
                self.converted_tools[tool_name] = {
                    "description": tool_description,
                    "adk_tool": adk_tool,
                    "converted_at": datetime.utcnow().isoformat()
                }
                
                self.logger.debug(f"  ✅ Converted: {tool_name}")
            
            self.logger.info(f"--- Successfully converted {len(adk_tools)} tools ---")
            return adk_tools
            
        except Exception as e:
            self.logger.error(f"Error converting MCP tools to ADK: {e}")
            return []
    
    def get_gmail_tools(self) -> List[FunctionTool]:
        """
        Get only Gmail-related tools as ADK FunctionTools.
        
        Returns:
            List of Gmail-specific ADK FunctionTools
        """
        all_tools = self.get_all_tools()
        
        # Filter for Gmail tools
        gmail_tools = []
        for tool in all_tools:
            tool_name = getattr(tool.func, '__name__', '')
            if 'gmail' in tool_name.lower():
                gmail_tools.append(tool)
        
        self.logger.info(f"Filtered {len(gmail_tools)} Gmail tools from {len(all_tools)} total tools")
        return gmail_tools
    
    def get_calendar_tools(self) -> List[FunctionTool]:
        """
        Get only Calendar-related tools as ADK FunctionTools.
        
        Returns:
            List of Calendar-specific ADK FunctionTools (future implementation)
        """
        all_tools = self.get_all_tools()
        
        # Filter for Calendar tools
        calendar_tools = []
        for tool in all_tools:
            tool_name = getattr(tool.func, '__name__', '')
            if 'calendar' in tool_name.lower():
                calendar_tools.append(tool)
        
        self.logger.info(f"Filtered {len(calendar_tools)} Calendar tools from {len(all_tools)} total tools")
        return calendar_tools
    
    def _create_adk_function(self, tool_name: str, tool_description: str) -> Callable:
        """
        Create an ADK-compatible function wrapper for an MCP tool.
        
        Args:
            tool_name: Name of the MCP tool
            tool_description: Description of the tool
            
        Returns:
            Function that can be used by ADK FunctionTool
        """
        def adk_tool_wrapper(**kwargs) -> Dict[str, Any]:
            """
            ADK-compatible wrapper for MCP tool execution.
            
            Args:
                **kwargs: Tool parameters
                
            Returns:
                Tool execution result with metadata
            """
            start_time = datetime.utcnow()
            
            try:
                self.logger.debug(f"Executing MCP tool: {tool_name} with args: {list(kwargs.keys())}")
                
                # Execute the MCP tool
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
                    "execution_time_ms": execution_time,
                    "timestamp": end_time.isoformat()
                }
                
                self.logger.debug(f"Tool {tool_name} executed successfully in {execution_time:.2f}ms")
                return wrapped_result
                
            except Exception as e:
                # Calculate execution time even for errors
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds() * 1000  # ms
                
                # Track execution stats
                self._update_execution_stats(tool_name, execution_time, False)
                
                self.logger.error(f"Error executing MCP tool {tool_name}: {e}")
                
                # Return error result in consistent format
                error_result = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "tool_name": tool_name,
                    "execution_time_ms": execution_time,
                    "timestamp": end_time.isoformat()
                }
                
                return error_result
        
        # Set function metadata for ADK
        adk_tool_wrapper.__name__ = tool_name
        adk_tool_wrapper.__doc__ = tool_description
        
        # Add tool signature inspection for better ADK integration
        if tool_name in self.tool_registry:
            try:
                tool_class = self.tool_registry[tool_name]
                if hasattr(tool_class, 'run'):
                    # Copy signature from original run method
                    original_signature = inspect.signature(tool_class.run)
                    adk_tool_wrapper.__signature__ = original_signature
            except Exception as e:
                self.logger.warning(f"Could not copy signature for {tool_name}: {e}")
        
        return adk_tool_wrapper
    
    def _update_execution_stats(self, tool_name: str, execution_time: float, success: bool):
        """Update execution statistics for tool performance tracking."""
        if tool_name not in self.tool_execution_stats:
            self.tool_execution_stats[tool_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_time_ms": 0,
                "avg_time_ms": 0,
                "last_execution": None
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
    
    def get_tool_info(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about converted tools and their performance.
        
        Args:
            tool_name: Specific tool name to get info for (None for all)
            
        Returns:
            Tool information and statistics
        """
        if tool_name:
            return {
                "tool_info": self.converted_tools.get(tool_name, {}),
                "execution_stats": self.tool_execution_stats.get(tool_name, {})
            }
        
        return {
            "total_tools_converted": len(self.converted_tools),
            "tools_available": list(self.converted_tools.keys()),
            "execution_stats": self.tool_execution_stats,
            "bridge_status": {
                "mcp_available": self.mcp_discovery is not None,
                "tools_in_registry": len(self.tool_registry)
            }
        }
    
    def test_tool_execution(self, tool_name: str, **test_kwargs) -> Dict[str, Any]:
        """
        Test execution of a specific tool with given parameters.
        
        Args:
            tool_name: Name of tool to test
            **test_kwargs: Test parameters
            
        Returns:
            Test execution result
        """
        if tool_name not in self.converted_tools:
            return {
                "success": False,
                "error": f"Tool {tool_name} not found in converted tools"
            }
        
        try:
            adk_tool = self.converted_tools[tool_name]["adk_tool"]
            result = adk_tool.func(**test_kwargs)
            
            return {
                "success": True,
                "test_result": result,
                "tool_name": tool_name,
                "test_parameters": test_kwargs
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "test_parameters": test_kwargs
            }


# =============================================================================
# Singleton Bridge Instance
# =============================================================================

# Global bridge instance for use across agents
_mcp_bridge_instance = None


def get_mcp_bridge() -> MCPADKBridge:
    """Get singleton MCP-ADK bridge instance."""
    global _mcp_bridge_instance
    if _mcp_bridge_instance is None:
        _mcp_bridge_instance = MCPADKBridge()
    return _mcp_bridge_instance


# =============================================================================
# Convenience Functions for Agents
# =============================================================================

def get_gmail_tools_for_agent() -> List[FunctionTool]:
    """
    Convenience function to get Gmail tools for email agent.
    
    Returns:
        List of Gmail ADK FunctionTools ready for agent use
    """
    bridge = get_mcp_bridge()
    return bridge.get_gmail_tools()


def get_calendar_tools_for_agent() -> List[FunctionTool]:
    """
    Convenience function to get Calendar tools for calendar agent.
    
    Returns:
        List of Calendar ADK FunctionTools ready for agent use
    """
    bridge = get_mcp_bridge()
    return bridge.get_calendar_tools()


def test_mcp_bridge_connection() -> Dict[str, Any]:
    """
    Test the MCP bridge connection and tool availability.
    
    Returns:
        Bridge connection test results
    """
    bridge = get_mcp_bridge()
    
    test_results = {
        "bridge_initialized": bridge is not None,
        "mcp_discovery_available": bridge.mcp_discovery is not None,
        "total_tools_available": len(bridge.tool_registry),
        "gmail_tools_count": len(bridge.get_gmail_tools()),
        "calendar_tools_count": len(bridge.get_calendar_tools()),
        "test_timestamp": datetime.utcnow().isoformat()
    }
    
    return test_results


# =============================================================================
# Export Key Components
# =============================================================================

__all__ = [
    "MCPADKBridge",
    "get_mcp_bridge",
    "get_gmail_tools_for_agent",
    "get_calendar_tools_for_agent", 
    "test_mcp_bridge_connection"
]


# =============================================================================
# Testing and Development
# =============================================================================

if __name__ == "__main__":
    def test_bridge():
        """Test the MCP-ADK bridge functionality."""
        print("🌉 Testing MCP-ADK Bridge...")
        
        # Test bridge initialization
        bridge = get_mcp_bridge()
        print(f"✅ Bridge initialized: {bridge is not None}")
        
        # Test tool conversion
        gmail_tools = bridge.get_gmail_tools()
        print(f"📧 Gmail tools converted: {len(gmail_tools)}")
        
        # Test tool info
        tool_info = bridge.get_tool_info()
        print(f"📊 Total tools converted: {tool_info['total_tools_converted']}")
        
        # Test connection
        connection_test = test_mcp_bridge_connection()
        print(f"🔗 Connection test: {connection_test}")
        
        # List some converted tools
        print("\n🔧 Available Gmail Tools:")
        for i, tool in enumerate(gmail_tools[:5]):  # Show first 5
            tool_name = getattr(tool.func, '__name__', f'tool_{i}')
            print(f"  - {tool_name}")
        
        print("\n✅ MCP-ADK Bridge test completed!")
    
    test_bridge()