"""
MCP Integration for Calendar Agent.

This module provides utilities for integrating the Calendar Agent with the MCP server.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../../"))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the MCP integration layer
from services.mcp import load_mcp_toolset, MCPConnectionManager

async def get_calendar_mcp_tools() -> List[Any]:
    """
    Get the calendar MCP tools.
    
    Returns:
        List[Any]: The calendar MCP tools
    """
    try:
        # Load the MCP toolset
        mcp_toolset = await load_mcp_toolset()
        
        if not mcp_toolset:
            logger.warning("Failed to load MCP toolset")
            return []
        
        # Filter the tools to only include calendar-related tools
        calendar_tools = []
        for tool in mcp_toolset.tools:
            if tool.name.startswith("calendar_"):
                calendar_tools.append(tool)
        
        logger.info(f"Loaded {len(calendar_tools)} calendar MCP tools")
        return calendar_tools
    except Exception as e:
        logger.error(f"Error getting calendar MCP tools: {e}")
        return []

def get_calendar_mcp_tools_sync() -> List[Any]:
    """
    Get the calendar MCP tools synchronously.
    
    Returns:
        List[Any]: The calendar MCP tools
    """
    try:
        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get the calendar MCP tools
        calendar_tools = loop.run_until_complete(get_calendar_mcp_tools())
        
        # Close the event loop
        loop.close()
        
        return calendar_tools
    except Exception as e:
        logger.error(f"Error getting calendar MCP tools synchronously: {e}")
        return [] 