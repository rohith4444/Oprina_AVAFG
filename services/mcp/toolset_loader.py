"""
MCP Toolset Loader for Oprina.

This module provides utilities for loading MCP toolsets from the MCP server.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import ADK MCP tools
try:
    from google.adk.tools.mcp import MCPToolset
    from google.adk.tools.mcp.server_parameters import StdioServerParameters
    ADK_MCP_AVAILABLE = True
except ImportError:
    ADK_MCP_AVAILABLE = False
    logger.warning("ADK MCP tools not available, running in fallback mode")

async def load_mcp_toolset() -> Optional[MCPToolset]:
    """
    Load the MCP toolset from the MCP server.
    
    Returns:
        Optional[MCPToolset]: The MCP toolset, or None if not available
    """
    if not ADK_MCP_AVAILABLE:
        logger.warning("ADK MCP tools not available, cannot load MCP toolset")
        return None
    
    try:
        # Create the MCP toolset
        mcp_toolset = await MCPToolset.from_server(
            StdioServerParameters(
                command="python",
                args=["mcp_server/run_server.py"],
                env=os.environ.copy()
            )
        )
        
        logger.info(f"Loaded MCP toolset with {len(mcp_toolset.tools)} tools")
        return mcp_toolset
    except Exception as e:
        logger.error(f"Error loading MCP toolset: {e}")
        return None

def get_mcp_tools() -> List[Any]:
    """
    Get the MCP tools.
    
    Returns:
        List[Any]: The MCP tools
    """
    if not ADK_MCP_AVAILABLE:
        logger.warning("ADK MCP tools not available, cannot get MCP tools")
        return []
    
    try:
        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Load the MCP toolset
        mcp_toolset = loop.run_until_complete(load_mcp_toolset())
        
        # Close the event loop
        loop.close()
        
        if mcp_toolset:
            return mcp_toolset.tools
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting MCP tools: {e}")
        return [] 