#!/usr/bin/env python3
"""
Entry point for the Oprina MCP server.

This script is called by ADK via StdioServerParameters to start the MCP server.
It implements the proper MCP protocol with tool discovery, capability negotiation,
and standard MCP message handling.
"""

import os
import sys
import asyncio
import logging
import json
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the server
from mcp_server.server import MCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def handle_stdio():
    """
    Handle stdio communication with ADK.
    
    This function reads from stdin and writes to stdout to communicate with ADK.
    It implements the proper MCP protocol with tool discovery, capability negotiation,
    and standard MCP message handling.
    """
    # Create the MCP server
    server = MCPServer()
    
    # Register tools with the server
    await server.register_tools()
    
    # Send the tool discovery message
    discovery_message = {
        "type": "tool_discovery",
        "version": "1.0",
        "tools": server.get_tool_schemas()
    }
    print(json.dumps(discovery_message), flush=True)
    
    # Handle messages from ADK
    while True:
        try:
            # Read a message from stdin
            message = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not message:
                break
                
            # Parse the message
            request = json.loads(message)
            logger.info(f"Received request: {request}")
            
            # Handle the request
            response = await server.handle_mcp_request(request)
            
            # Send the response
            print(json.dumps(response), flush=True)
            logger.info(f"Sent response: {response}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {message}")
            print(json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }), flush=True)
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            print(json.dumps({
                "type": "error",
                "message": str(e)
            }), flush=True)

if __name__ == "__main__":
    try:
        logger.info("Starting Oprina MCP server for ADK...")
        asyncio.run(handle_stdio())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1) 