# Oprina - Voice-powered Gmail Assistant

Oprina is a voice-powered Gmail assistant that helps users manage their emails, calendar, and content. It can process voice input, convert it to text, and perform various operations on Gmail, Google Calendar, and content generation. It can also convert text responses back to voice output.

## Features

- **Voice Input/Output**: Process voice input and convert it to text, and convert text responses back to voice output.
- **Email Management**: Search, read, compose, and send emails, manage email labels, handle attachments, and process email threads.
- **Calendar Management**: Manage calendar events and schedules, handle meeting scheduling and coordination, process calendar invitations, manage calendar settings and preferences, and handle calendar conflicts and rescheduling.
- **Content Generation**: Generate text content for emails and documents, summarize and analyze content, format and structure content, manage content templates, and handle content revisions and versions.

## Architecture

Oprina is built using a multi-agent architecture:

- **Root Agent**: Orchestrates the sub-agents and handles voice input/output.
- **Email Agent**: Handles Gmail operations.
- **Calendar Agent**: Handles Google Calendar operations.
- **Content Agent**: Handles content generation and management.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Oprina_AVAFG.git
   cd Oprina_AVAFG
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Google API credentials:
   - Create a project in the Google Cloud Console
   - Enable the Gmail API, Google Calendar API, and Google Cloud Text-to-Speech API
   - Create a service account and download the credentials JSON file
   - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the credentials file

## Usage

Run the Oprina application:

```
python -m oprina.main
```

Command-line options:

- `--debug`: Enable debug logging
- `--model`: Model to use for the agent (default: gemini-2.0-flash-001)
- `--temperature`: Temperature for content generation (default: 0.0)
- `--top_p`: Top-p for content generation (default: 0.5)

## Development

### Project Structure

```
oprina/
├── main.py                  # Main entry point
├── root_agent.py            # Root agent definition
├── common.py                # Shared constants
├── sub_agents/              # Sub-agent definitions
│   ├── email/               # Email agent
│   │   └── agent.py
│   ├── calendar/            # Calendar agent
│   │   └── agent.py
│   └── content/             # Content agent
│       └── agent.py
└── tools/                   # Tool definitions
    ├── memory.py            # Memory tools
    ├── email.py             # Email tools
    ├── calendar.py          # Calendar tools
    └── content.py           # Content tools
```

### Adding a New Sub-agent

1. Create a new directory in `oprina/sub_agents/` for your sub-agent
2. Create an `agent.py` file in the new directory
3. Define your sub-agent using the `Agent` class
4. Add the sub-agent to the root agent in `oprina/root_agent.py`

### Adding a New Tool

1. Create a new file in `oprina/tools/` for your tool
2. Define your tool using the `Tool` class
3. Add the tool to the appropriate sub-agent in `oprina/sub_agents/*/agent.py`

## License

This project is licensed under the Apache License, Version 2.0 - see the LICENSE file for details.

## Acknowledgments

- Google ADK (Agent Development Kit)
- Google Gemini models
- Google Cloud APIs