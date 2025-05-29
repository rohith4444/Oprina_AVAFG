# Oprina MCP Server

The Model Context Protocol (MCP) server for Oprina, a voice-powered Gmail assistant. This server provides a WebSocket-based API for interacting with Gmail and Google Calendar.

## Features

- WebSocket-based API for real-time communication
- Gmail integration for reading and sending emails
- Google Calendar integration for managing events
- Authentication with Google services

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Oprina_AVAFG.git
cd Oprina_AVAFG
```

2. Install the required dependencies:
```bash
cd mcp_server
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the `mcp_server` directory with the following variables:
```
MCP_HOST=localhost
MCP_PORT=8765
```

## Usage

### Starting the Server

To start the MCP server, run:
```bash
python server.py
```

The server will start on the specified host and port (default: localhost:8765).

### Testing with the Client

A simple client is provided for testing the MCP server. To run the client, use:
```bash
python client.py
```

The client will connect to the server and perform some example operations.

## API Reference

### Request Format

All requests to the MCP server should be in JSON format with the following structure:
```json
{
  "tool": "gmail|calendar",
  "action": "action_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### Response Format

All responses from the MCP server will be in JSON format with the following structure:
```json
{
  "status": "success|error",
  "data": { ... } | null,
  "message": "Error message (only if status is error)"
}
```

### Gmail Actions

- `list_messages`: List messages matching a query
  - Parameters:
    - `query`: Gmail search query (optional)
    - `max_results`: Maximum number of results to return (optional, default: 10)

- `get_message`: Get a message by ID
  - Parameters:
    - `message_id`: Message ID

- `send_message`: Send an email
  - Parameters:
    - `to`: Recipient email address
    - `subject`: Email subject
    - `body`: Email body

- `modify_labels`: Modify labels on a message
  - Parameters:
    - `message_id`: Message ID
    - `add_labels`: Labels to add (optional)
    - `remove_labels`: Labels to remove (optional)

- `list_labels`: List all labels
  - Parameters: None

### Calendar Actions

- `list_events`: List events in the calendar
  - Parameters:
    - `time_min`: Start time for events (ISO format, optional)
    - `time_max`: End time for events (ISO format, optional)
    - `max_results`: Maximum number of results to return (optional, default: 10)
    - `single_events`: Whether to expand recurring events (optional, default: true)

- `get_event`: Get an event by ID
  - Parameters:
    - `event_id`: Event ID

- `create_event`: Create a new event
  - Parameters:
    - `summary`: Event summary/title
    - `start_time`: Start time (ISO format)
    - `end_time`: End time (ISO format)
    - `description`: Event description (optional)
    - `location`: Event location (optional)
    - `attendees`: List of attendee email addresses (optional)

- `update_event`: Update an existing event
  - Parameters:
    - `event_id`: Event ID
    - Any other event fields to update

- `delete_event`: Delete an event
  - Parameters:
    - `event_id`: Event ID

- `list_calendars`: List all calendars
  - Parameters: None

## License

This project is licensed under the MIT License - see the LICENSE file for details. 