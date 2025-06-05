# Model Context Protocol (MCP) Implementation

This document outlines the proper implementation of the Model Context Protocol (MCP) for ADK integration.

## Overview

The Model Context Protocol (MCP) is a communication protocol between ADK and external tools. It enables ADK to discover, negotiate capabilities, and call tools provided by external services.

## Key Components

### 1. MCP Server

The MCP server is responsible for:
- Handling requests from ADK
- Providing access to tools (Gmail, Calendar, Content)
- Implementing the MCP protocol (versioning, tool discovery, capability negotiation)

### 2. MCP Protocol

The MCP protocol consists of the following message types:
- `HELLO`: Initial handshake to establish protocol version and capabilities
- `TOOL_DISCOVERY`: Request and response for available tools
- `TOOL_CALL`: Request to execute a specific tool
- `TOOL_RESULT`: Response with the result of a tool call
- `ERROR`: Error message

### 3. ADK Integration

The ADK integration is responsible for:
- Creating agents with proper ADK patterns
- Using `FunctionTool` for tool integration
- Handling session state and tool context

## Implementation Details

### MCP Server

The MCP server is implemented in `mcp_server/server.py` and `mcp_server/run_server.py`. It follows these principles:

1. **Protocol Compliance**:
   - Implements all required message types
   - Handles versioning and capability negotiation
   - Provides tool discovery

2. **Communication**:
   - Uses stdio for communication with ADK
   - Reads from stdin and writes to stdout
   - No WebSocket or non-MCP communication

3. **Tool Registration**:
   - Registers tools with the server
   - Provides fallback tools if primary tools are unavailable
   - Exposes tool schemas for discovery

### ADK Integration

The ADK integration is implemented in `agents/voice/sub_agents/coordinator/sub_agents/email/agent.py`. It follows these principles:

1. **Agent Creation**:
   - Uses `LlmAgent` for agent creation
   - Configures agents with proper ADK patterns
   - Uses `FunctionTool` for tool integration

2. **Session State Management**:
   - Handles session state and tool context
   - Updates session state with connection status and operation results
   - Provides fallback mechanisms for session state

3. **OAuth Flow**:
   - Uses the Gmail authentication service for OAuth flow
   - Handles credential management and token persistence
   - Provides connection status and error handling

### Proper ADK MCP Integration

The correct way to integrate with ADK MCP is to use the `MCPToolset` and `StdioServerParameters`:

```python
from google.adk.tools.mcp import MCPToolset
from google.adk.tools.mcp.server_parameters import StdioServerParameters

# ADK automatically discovers and loads MCP tools
mcp_toolset = await MCPToolset.from_server(
    StdioServerParameters(
        command="python",
        args=["mcp_server/run_server.py"],
        env=os.environ.copy()
    )
)

# Tools are automatically available as ADK tools
agent = LlmAgent(
    name="agent",
    tools=mcp_toolset.tools,  # All MCP tools auto-discovered
    # ...
)
```

This approach:
- Automatically discovers and loads MCP tools
- Handles the MCP server lifecycle
- Makes MCP tools available as regular ADK tools
- Follows the proper ADK MCP pattern

### Server Parameters

ADK provides two types of server parameters:

1. **StdioServerParameters**: Runs the MCP server as a subprocess
   ```python
   StdioServerParameters(
       command="python",
       args=["mcp_server/run_server.py"],
       env=os.environ.copy()
   )
   ```

2. **SSEServerParameters**: Connects to a running MCP server
   ```python
   SSEServerParameters(
       url="http://localhost:8000/sse",
       api_key="optional-api-key"
   )
   ```

## Testing

The MCP server can be tested using the `mcp_server/test_client.py` script. It verifies that the server correctly implements the MCP protocol by:

1. Starting the MCP server as a subprocess
2. Sending messages to stdin and reading from stdout
3. Verifying that the server responds correctly to different message types

## Best Practices

1. **Protocol Compliance**:
   - Always implement all required message types
   - Handle versioning and capability negotiation
   - Provide tool discovery

2. **Communication**:
   - Use stdio for communication with ADK
   - Read from stdin and write to stdout
   - Avoid WebSocket or non-MCP communication

3. **Tool Registration**:
   - Register tools with the server
   - Provide fallback tools if primary tools are unavailable
   - Expose tool schemas for discovery

4. **ADK Integration**:
   - Use `LlmAgent` for agent creation
   - Configure agents with proper ADK patterns
   - Use `FunctionTool` for tool integration
   - Use `MCPToolset` and `StdioServerParameters` for MCP integration

5. **Session State Management**:
   - Handle session state and tool context
   - Update session state with connection status and operation results
   - Provide fallback mechanisms for session state

6. **OAuth Flow**:
   - Use the Gmail authentication service for OAuth flow
   - Handle credential management and token persistence
   - Provide connection status and error handling