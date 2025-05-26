
"""
MCP Integration for Email Agent

This module handles the connection to Calvin's custom Gmail MCP server
and provides tools for email operations.

Key Features:
- Gmail MCP server connection
- Email fetching tools
- Email sending/drafting tools
- Email organization tools
- Authentication handling
"""

import os
import sys
import asyncio
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
# From: agents/voice/sub_agents/coordinator/sub_agents/email/mcp_integration.py
# Need to go up 6 levels to reach project root
project_root = current_file
for _ in range(7):  # 6 levels + 1 for the file itself
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("email_mcp_integration", console_output=True)

class EmailMCPIntegration:
    """
    Integration with Calvin's custom Gmail MCP server.
    Manages connection and provides email operation tools.
    """
    
    def __init__(self):
        """Initialize MCP integration."""
        self.logger = logger
        self.tools = []
        self.exit_stack = None
        self.connected = False
        
        # MCP server configuration
        self.mcp_server_command = os.getenv("GMAIL_MCP_COMMAND", "gmail-mcp-server")
        self.mcp_server_args = os.getenv("GMAIL_MCP_ARGS", "").split() if os.getenv("GMAIL_MCP_ARGS") else []
        
    async def connect_to_gmail_mcp(self):
        """
        Connect to Calvin's Gmail MCP server.
        
        Returns:
            Tuple of (tools, exit_stack) for use in agent
        """
        self.logger.info("--- Attempting to connect to Gmail MCP server ---")
        
        try:
            # Connect to Calvin's Gmail MCP server
            # This will be updated once Calvin provides the exact server details
            self.tools, self.exit_stack = await MCPToolset.create(
                connection_params=StdioServerParameters(
                    command=self.mcp_server_command,
                    args=self.mcp_server_args,
                    env={
                        # Gmail API credentials will be provided by Calvin
                        "GMAIL_CLIENT_ID": os.getenv("GMAIL_CLIENT_ID", ""),
                        "GMAIL_CLIENT_SECRET": os.getenv("GMAIL_CLIENT_SECRET", ""),
                        "GMAIL_REFRESH_TOKEN": os.getenv("GMAIL_REFRESH_TOKEN", ""),
                        # Additional environment variables as needed
                        **os.environ
                    }
                )
            )
            
            self.connected = True
            self.logger.info(f"--- Successfully connected to Gmail MCP server. Discovered {len(self.tools)} tool(s). ---")
            
            # Log discovered tools for debugging
            for tool in self.tools:
                self.logger.info(f"  - Discovered Gmail tool: {tool.name}")
            
            return self.tools, self.exit_stack
            
        except FileNotFoundError:
            self.logger.error("!!! Gmail MCP server command not found !!!")
            self.logger.error(f"!!! Tried to run: {self.mcp_server_command} {' '.join(self.mcp_server_args)} !!!")
            return self._get_mock_tools()
            
        except Exception as e:
            self.logger.error(f"--- ERROR connecting to Gmail MCP server: {e} ---")
            self.logger.warning("--- Falling back to mock tools for development ---")
            return self._get_mock_tools()
    
    def _get_mock_tools(self):
        """
        Provide mock tools for development when MCP server is not available.
        
        Returns:
            Tuple of (mock_tools, dummy_exit_stack)
        """
        from google.adk.tools import FunctionTool
        
        def mock_fetch_emails(query: str = "", max_results: int = 10) -> Dict[str, Any]:
            """Mock email fetching for development."""
            self.logger.info(f"MOCK: Fetching emails with query='{query}', max_results={max_results}")
            
            # Return mock email data
            return {
                "emails": [
                    {
                        "id": "mock_email_1",
                        "thread_id": "mock_thread_1",
                        "subject": "Test Email 1",
                        "sender": "test1@example.com",
                        "date": "2024-05-25T10:00:00Z",
                        "snippet": "This is a test email for development...",
                        "read": False,
                        "important": False,
                        "labels": ["INBOX"]
                    },
                    {
                        "id": "mock_email_2", 
                        "thread_id": "mock_thread_2",
                        "subject": "Important Update",
                        "sender": "important@company.com",
                        "date": "2024-05-25T09:30:00Z",
                        "snippet": "This is an important update regarding...",
                        "read": True,
                        "important": True,
                        "labels": ["INBOX", "IMPORTANT"]
                    }
                ],
                "total_count": 2,
                "query_used": query,
                "mock_mode": True
            }
        
        def mock_send_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> Dict[str, Any]:
            """Mock email sending for development."""
            self.logger.info(f"MOCK: Sending email to='{to}', subject='{subject}'")
            
            return {
                "success": True,
                "message_id": f"mock_sent_{hash(to + subject)}",
                "to": to,
                "subject": subject,
                "sent_at": "2024-05-25T12:00:00Z",
                "mock_mode": True
            }
        
        def mock_draft_email(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> Dict[str, Any]:
            """Mock email drafting for development."""
            self.logger.info(f"MOCK: Creating draft to='{to}', subject='{subject}'")
            
            return {
                "success": True,
                "draft_id": f"mock_draft_{hash(to + subject)}",
                "to": to,
                "subject": subject,
                "created_at": "2024-05-25T12:00:00Z",
                "mock_mode": True
            }
        
        def mock_organize_email(email_id: str, action: str, label: str = "") -> Dict[str, Any]:
            """Mock email organization for development."""
            self.logger.info(f"MOCK: Organizing email_id='{email_id}', action='{action}', label='{label}'")
            
            return {
                "success": True,
                "email_id": email_id,
                "action_performed": action,
                "label": label,
                "updated_at": "2024-05-25T12:00:00Z",
                "mock_mode": True
            }
        
        # Create mock tools
        mock_tools = [
            FunctionTool(func=mock_fetch_emails),
            FunctionTool(func=mock_send_email),
            FunctionTool(func=mock_draft_email),
            FunctionTool(func=mock_organize_email)
        ]
                
        # Create dummy exit stack
        class DummyExitStack:
            async def __aenter__(self): 
                return self
            async def __aexit__(self, *args): 
                pass
        
        self.connected = False  # Mark as mock mode
        return mock_tools, DummyExitStack()
    
    def is_connected(self) -> bool:
        """Check if connected to real MCP server (not mock mode)."""
        return self.connected
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status."""
        return {
            "connected": self.connected,
            "mock_mode": not self.connected,
            "tools_count": len(self.tools),
            "server_command": self.mcp_server_command,
            "server_args": self.mcp_server_args
        }


# Global instance for use in agent
email_mcp = EmailMCPIntegration()

async def get_gmail_tools():
    """
    Get Gmail tools from MCP server.
    
    Returns:
        Tuple of (tools, exit_stack) for agent initialization
    """
    return await email_mcp.connect_to_gmail_mcp()


# Tool status function for debugging
def get_gmail_mcp_status() -> Dict[str, Any]:
    """Get Gmail MCP connection status for debugging."""
    return email_mcp.get_connection_status()


if __name__ == "__main__":
    # Test MCP integration
    async def test_gmail_mcp():
        print("Testing Gmail MCP Integration...")
        
        tools, exit_stack = await get_gmail_tools()
        
        print(f"Connected: {email_mcp.is_connected()}")
        print(f"Tools available: {len(tools)}")
        
        for tool in tools:
            print(f"  - {tool.name}")
        
        # Test a mock tool if in mock mode
        if not email_mcp.is_connected() and tools:
            print("\nTesting mock fetch_emails tool:")
            try:
                # This is a bit tricky to test directly since tools need proper context
                # But we can at least verify the function exists
                print("✅ Mock tools created successfully")
            except Exception as e:
                print(f"❌ Error with mock tools: {e}")
        
        print("✅ Gmail MCP integration test completed")
    
    asyncio.run(test_gmail_mcp())