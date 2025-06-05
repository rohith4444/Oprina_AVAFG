# Oprina Voice Assistant

Oprina is a voice-powered Gmail assistant with ADK-native memory services. It allows users to manage their email, calendar, and content using natural language.

## Project Overview

Oprina is built on the ADK (Agent Development Kit) platform and uses the MCP (Model Context Protocol) for communication between agents and external services. It provides a voice interface for managing Gmail, Google Calendar, and content processing.

## Architecture

The Oprina Voice Assistant consists of the following components:

### Agents

- **Coordinator Agent**: Routes user requests to the appropriate sub-agent based on the intent.
- **Email Agent**: Handles email-related operations such as listing messages, reading messages, and sending messages.
- **Calendar Agent**: Handles calendar-related operations such as listing events, creating events, and updating events.
- **Content Agent**: Handles content processing operations such as summarizing email content and extracting information.

### Services

- **MCP Integration Layer**: Provides utilities for connecting to the MCP server, loading tools, and executing tools.
- **MCP Server**: Implements the Model Context Protocol (MCP) server that handles requests from ADK and provides access to Gmail, Calendar, and Content tools.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Google Cloud Platform account
- Gmail account
- Google Calendar account

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/oprina-voice-assistant.git
   cd oprina-voice-assistant
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   cp config/.env.example .env
   ```
   Edit the `.env` file and fill in your actual values.

4. Run the MCP server:
   ```
   python mcp_server/run_server.py
   ```

5. Run the voice assistant:
   ```
   python main.py
   ```

## MCP Integration

The MCP integration layer provides utilities for connecting to the MCP server, loading tools, and executing tools. It is used by the agents to communicate with the MCP server.

### Configuration

The MCP integration layer uses environment variables for configuration. The following environment variables are used:

- `MCP_SERVER_HOST`: The host of the MCP server (default: "localhost").
- `MCP_SERVER_PORT`: The port of the MCP server (default: 8765).
- `MCP_CONNECTION_TYPE`: The connection type ("stdio" or "sse") (default: "stdio").
- `MCP_SERVER_URL`: The URL of the MCP server (required for SSE connection).
- `MCP_SERVER_API_KEY`: The API key for the MCP server (required for SSE connection).

These environment variables should be set in the `.env` file. See the `.env.example` file for an example configuration.

### Usage

The MCP integration layer is used by the agents to communicate with the MCP server. Each agent has its own MCP integration module that provides utilities for integrating the agent with the MCP server.

For example, the Email Agent has an MCP integration module at `agents/voice/sub_agents/coordinator/sub_agents/email/mcp_integration.py` that provides utilities for integrating the Email Agent with the MCP server.

## ADK Integration

The Oprina Voice Assistant is built on the ADK (Agent Development Kit) platform. It uses ADK for agent development, memory services, and session management.

### Configuration

The ADK integration uses environment variables for configuration. The following environment variables are used:

- `ADK_APP_NAME`: The name of the ADK application (default: "oprina").
- `ADK_MODEL`: The model to use for ADK (default: "gemini-2.5-flash-preview-05-20").
- `ADK_TEMPERATURE`: The temperature to use for ADK (default: 0.7).
- `ADK_MAX_TOKENS`: The maximum number of tokens to use for ADK (default: 1024).
- `ADK_SESSION_TTL_SECONDS`: The TTL for ADK sessions in seconds (default: 86400).

These environment variables should be set in the `.env` file. See the `.env.example` file for an example configuration.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.