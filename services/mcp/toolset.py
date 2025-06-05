"""
MCP Toolset.

This module provides utilities for loading and managing MCP toolsets.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the MCP client
from mcp_server.client import MCPClient

# Import the connection manager
from .connection_manager import MCPConnectionManager

class MCPToolset:
    """
    MCP Toolset.
    
    This class represents a set of MCP tools.
    """
    
    def __init__(self, tools: List[Any]):
        """
        Initialize the MCPToolset.
        
        Args:
            tools (List[Any]): The tools in the toolset
        """
        self.tools = tools
        
    def get_tool(self, name: str) -> Optional[Any]:
        """
        Get a tool by name.
        
        Args:
            name (str): The name of the tool
            
        Returns:
            Optional[Any]: The tool, or None if not found
        """
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
        
    def get_tools_by_category(self, category: str) -> List[Any]:
        """
        Get tools by category.
        
        Args:
            category (str): The category of the tools
            
        Returns:
            List[Any]: The tools in the category
        """
        return [tool for tool in self.tools if tool.category == category]

async def load_mcp_toolset() -> Optional[MCPToolset]:
    """
    Load the MCP toolset.
    
    Returns:
        Optional[MCPToolset]: The MCP toolset, or None if loading failed
    """
    try:
        # Create the connection manager
        connection_manager = MCPConnectionManager()
        
        # Connect to the MCP server
        connected = await connection_manager.connect()
        
        if not connected:
            logger.warning("Failed to connect to MCP server")
            return None
        
        # Get the tools from the MCP server
        tools = connection_manager.get_tools()
        
        if not tools:
            logger.warning("Failed to get tools from MCP server")
            return None
        
        # Create the toolset
        toolset = MCPToolset(tools)
        
        logger.info(f"Loaded {len(tools)} tools from MCP server")
        return toolset
    except Exception as e:
        logger.error(f"Error loading MCP toolset: {e}")
        return None

def load_mcp_toolset_sync() -> Optional[MCPToolset]:
    """
    Load the MCP toolset synchronously.
    
    Returns:
        Optional[MCPToolset]: The MCP toolset, or None if loading failed
    """
    try:
        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Load the MCP toolset
        toolset = loop.run_until_complete(load_mcp_toolset())
        
        # Close the event loop
        loop.close()
        
        return toolset
    except Exception as e:
        logger.error(f"Error loading MCP toolset synchronously: {e}")
        return None 