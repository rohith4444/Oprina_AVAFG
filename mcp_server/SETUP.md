# Oprina MCP Server Setup Guide

This guide will help you set up and run the Oprina MCP server.

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with Gmail and Calendar APIs enabled
- Google OAuth 2.0 client credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Oprina_AVAFG.git
cd Oprina_AVAFG
```

2. Create a virtual environment and activate it:
```bash
python -m venv mcp_server/venv
# On Windows
mcp_server\venv\Scripts\activate
# On macOS/Linux
source mcp_server/venv/bin/activate
```

3. Install the required dependencies:
```bash
cd mcp_server
pip install -r requirements.txt
```

## Authentication Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project or select an existing one.

2. Enable the Gmail API and Google Calendar API for your project.

3. Create OAuth 2.0 client credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Give it a name and click "Create"
   - Download the client secrets file and save it as `client_secrets.json` in the `mcp_server` directory

4. Run the authentication setup script:
```bash
python auth_setup.py
```

5. Follow the instructions in the browser to authenticate with your Google account.

## Running the Server

1. Start the MCP server:
```bash
python run_server.py
```

2. In a separate terminal, run the client to test the server:
```bash
python run_client.py
```

## Troubleshooting

### Authentication Issues

If you encounter authentication issues:

1. Make sure you have the correct `client_secrets.json` file in the `mcp_server` directory.
2. Delete the `token.json` file (if it exists) and run the authentication setup script again.
3. Check that you have enabled the Gmail API and Google Calendar API in the Google Cloud Console.

### Connection Issues

If you have connection issues:

1. Make sure the server is running on the correct host and port.
2. Check that the client is connecting to the correct host and port.
3. Check your firewall settings to ensure that the port is not blocked.

## Additional Resources

- [Google Gmail API Documentation](https://developers.google.com/gmail/api/guides)
- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [WebSockets Documentation](https://websockets.readthedocs.io/) 