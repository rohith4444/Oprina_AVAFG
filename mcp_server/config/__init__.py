"""
MCP Server Configuration Module

This module provides access to the MCP server configuration.
"""

from mcp_server.config.mcp_config import (
    MCP_SERVER_HOST,
    MCP_SERVER_PORT,
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_API_KEY,
    MCP_LOG_LEVEL
)

# Create a config dictionary for backward compatibility
config = {
    "mcp_server_host": MCP_SERVER_HOST,
    "mcp_server_port": MCP_SERVER_PORT,
    "mcp_protocol_version": MCP_PROTOCOL_VERSION,
    "mcp_server_api_key": MCP_SERVER_API_KEY,
    "mcp_log_level": MCP_LOG_LEVEL
} 