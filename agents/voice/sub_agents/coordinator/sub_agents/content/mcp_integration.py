"""
MCP Integration for Content Agent.

This module provides utilities for integrating the Content Agent with the MCP server.
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

async def get_content_mcp_tools() -> List[Any]:
    """
    Get the content MCP tools.
    
    Returns:
        List[Any]: The content MCP tools
    """
    try:
        # Load the MCP toolset
        mcp_toolset = await load_mcp_toolset()
        
        if not mcp_toolset:
            logger.warning("Failed to load MCP toolset")
            return []
        
        # Filter the tools to only include content-related tools
        content_tools = []
        for tool in mcp_toolset.tools:
            if tool.name in [
                "summarize_email_content",
                "generate_email_reply",
                "analyze_email_sentiment",
                "extract_action_items",
                "optimize_for_voice",
                "create_voice_summary"
            ]:
                content_tools.append(tool)
        
        logger.info(f"Loaded {len(content_tools)} content MCP tools")
        return content_tools
    except Exception as e:
        logger.error(f"Error getting content MCP tools: {e}")
        return []

def get_content_mcp_tools_sync() -> List[Any]:
    """
    Get the content MCP tools synchronously.
    
    Returns:
        List[Any]: The content MCP tools
    """
    try:
        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get the content MCP tools
        content_tools = loop.run_until_complete(get_content_mcp_tools())
        
        # Close the event loop
        loop.close()
        
        return content_tools
    except Exception as e:
        logger.error(f"Error getting content MCP tools synchronously: {e}")
        return [] 