# MCP Integration Layer

This directory contains the MCP (Model Context Protocol) integration layer for the Oprina Voice Assistant. The MCP integration layer provides utilities for connecting to the MCP server, loading tools, and executing tools.

## Directory Structure

- `__init__.py`: Exports the main components of the MCP integration layer.
- `connection_manager.py`: Manages connections to the MCP server.
- `toolset.py`: Provides utilities for loading and managing MCP toolsets.
- `README.md`: This file.

## Components

### MCPConnectionManager

The `MCPConnectionManager` class manages connections to the MCP server. It provides methods for connecting to the MCP server, disconnecting from the MCP server, checking the health of the MCP server, and getting tools from the MCP server.

### MCPToolset

The `MCPToolset` class represents a set of MCP tools. It provides methods for getting tools by name and getting tools by category.

### load_mcp_toolset

The `load_mcp_toolset` function loads the MCP toolset from the MCP server. It returns an instance of the `MCPToolset` class.

## Usage

### Connecting to the MCP Server

```python
from services.mcp import MCPConnectionManager

# Create a connection manager
connection_manager = MCPConnectionManager()

# Connect to the MCP server
await connection_manager.connect()

# Check the health of the MCP server
is_healthy = await connection_manager.health_check()

# Get tools from the MCP server
tools = connection_manager.get_tools()

# Get a specific tool
tool = connection_manager.get_tool("gmail_check_connection")

# Disconnect from the MCP server
await connection_manager.disconnect()
```

### Loading the MCP Toolset

```python
from services.mcp import load_mcp_toolset

# Load the MCP toolset
toolset = await load_mcp_toolset()

# Get a tool by name
tool = toolset.get_tool("gmail_check_connection")

# Get tools by category
email_tools = toolset.get_tools_by_category("email")
```

### Using MCP Tools in Agents

```python
from services.mcp import load_mcp_toolset

# Load the MCP toolset
toolset = await load_mcp_toolset()

# Get the gmail_check_connection tool
check_connection = toolset.get_tool("gmail_check_connection")

# Call the tool
result = await check_connection()
```

## Integration with Agents

The MCP integration layer is designed to be used by agents to communicate with the MCP server. Each agent should have its own MCP integration module that provides utilities for integrating the agent with the MCP server.

For example, the Email Agent has an MCP integration module at `agents/voice/sub_agents/coordinator/sub_agents/email/mcp_integration.py` that provides utilities for integrating the Email Agent with the MCP server.

## Error Handling

The MCP integration layer includes error handling for connection failures, tool loading failures, and tool execution failures. It uses the Python `logging` module to log events and errors.

## Configuration

The MCP integration layer uses environment variables for configuration. The following environment variables are used:

- `MCP_SERVER_HOST`: The host of the MCP server (default: "localhost").
- `MCP_SERVER_PORT`: The port of the MCP server (default: 8765).
- `MCP_CONNECTION_TYPE`: The connection type ("stdio" or "sse") (default: "stdio").
- `MCP_SERVER_URL`: The URL of the MCP server (required for SSE connection).
- `MCP_SERVER_API_KEY`: The API key for the MCP server (required for SSE connection).

These environment variables should be set in the `.env` file. See the `.env.example` file for an example configuration. 