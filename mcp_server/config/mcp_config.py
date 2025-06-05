"""
MCP Server Configuration

This file contains configuration settings specific to the MCP server.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# MCP Server host and port
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))

# MCP Server protocol version
MCP_PROTOCOL_VERSION = os.getenv("MCP_PROTOCOL_VERSION", "1.0")

# Optional: API key for secure connections
MCP_SERVER_API_KEY = os.getenv("MCP_SERVER_API_KEY", None)

# Optional: Logging level
MCP_LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO") 