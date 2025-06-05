"""
MCP Connection Manager for Oprina.

This module provides utilities for managing connections to the MCP server.
"""

import os
import sys
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    from google.adk.tools.mcp.server_parameters import StdioServerParameters, SSEServerParameters
    ADK_MCP_AVAILABLE = True
except ImportError:
    ADK_MCP_AVAILABLE = False
    logger.warning("ADK MCP tools not available, running in fallback mode")

class MCPConnectionManager:
    """
    MCP Connection Manager.
    
    This class manages connections to the MCP server.
    """
    
    def __init__(self, connection_type: str = None, url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the MCP Connection Manager.
        
        Args:
            connection_type: Connection type ("stdio" or "sse")
            url: URL for SSE connection
            api_key: API key for SSE connection
        """
        # Use environment variables if not provided
        self.connection_type = connection_type or os.environ.get("MCP_CONNECTION_TYPE", "stdio")
        self.url = url or os.environ.get("MCP_SERVER_URL")
        self.api_key = api_key or os.environ.get("MCP_SERVER_API_KEY")
        self.mcp_toolset = None
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds
    
    async def connect(self) -> bool:
        """
        Connect to the MCP server.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not ADK_MCP_AVAILABLE:
            logger.warning("ADK MCP tools not available, cannot connect to MCP server")
            return False
        
        try:
            if self.connection_type == "stdio":
                # Create the MCP toolset with StdioServerParameters
                self.mcp_toolset = await MCPToolset.from_server(
                    StdioServerParameters(
                        command="python",
                        args=["mcp_server/run_server.py"],
                        env=os.environ.copy()
                    )
                )
            elif self.connection_type == "sse":
                # Create the MCP toolset with SSEServerParameters
                if not self.url:
                    logger.error("URL is required for SSE connection")
                    return False
                
                self.mcp_toolset = await MCPToolset.from_server(
                    SSEServerParameters(
                        url=self.url,
                        api_key=self.api_key
                    )
                )
            else:
                logger.error(f"Unknown connection type: {self.connection_type}")
                return False
            
            logger.info(f"Connected to MCP server with {len(self.mcp_toolset.tools)} tools")
            return True
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """
        Disconnect from the MCP server.
        """
        if self.mcp_toolset:
            # Close the MCP toolset
            await self.mcp_toolset.close()
            self.mcp_toolset = None
            logger.info("Disconnected from MCP server")
    
    async def health_check(self) -> bool:
        """
        Check the health of the MCP server.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        # Check if we need to perform a health check
        current_time = time.time()
        if current_time - self.last_health_check < self.health_check_interval:
            return True
        
        # Update the last health check time
        self.last_health_check = current_time
        
        if not self.mcp_toolset:
            logger.warning("Not connected to MCP server, cannot perform health check")
            return False
        
        try:
            # Try to call a simple tool to check the connection
            # We'll use the gmail_check_connection tool
            if "gmail_check_connection" in self.mcp_toolset.tools:
                await self.mcp_toolset.tools["gmail_check_connection"]()
                logger.info("MCP server health check passed")
                return True
            else:
                logger.warning("gmail_check_connection tool not found, cannot perform health check")
                return False
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return False
    
    def get_tools(self) -> List[Any]:
        """
        Get the MCP tools.
        
        Returns:
            List[Any]: The MCP tools
        """
        if not self.mcp_toolset:
            logger.warning("Not connected to MCP server, cannot get tools")
            return []
        
        return self.mcp_toolset.tools
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """
        Get a specific MCP tool.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[Callable]: The MCP tool, or None if not found
        """
        if not self.mcp_toolset:
            logger.warning("Not connected to MCP server, cannot get tool")
            return None
        
        if name not in self.mcp_toolset.tools:
            logger.warning(f"Tool {name} not found")
            return None
        
        return self.mcp_toolset.tools[name] 