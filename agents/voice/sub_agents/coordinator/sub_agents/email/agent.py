"""Add commentMore actions
Email Agent for Oprina - Complete ADK Integration

This agent handles all Gmail operations using the MCP client.
Simplified to return a single LlmAgent with proper ADK integration.
"""

import os
import sys
import asyncio
from typing import Optional

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(7):  # 7 levels to reach project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import external packages
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import load_memory
from google.adk.runners import Runner

# Import project modules
from config.settings import settings

# Import MCP client
from mcp_server.client import MCPClient

# Import shared constants for documentation
from agents.common.session_keys import (
    USER_GMAIL_CONNECTED, USER_EMAIL, USER_NAME, USER_PREFERENCES,
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_UNREAD_COUNT, EMAIL_LAST_SENT
)

class ProcessableEmailAgent(LlmAgent):
    async def process(self, event, app_name=None, session_service=None, memory_service=None):
        """
        Process an event with proper session state handling.
        
        Args:
            event: The event to process
            app_name: The application name
            session_service: The session service
            memory_service: The memory service
            
        Returns:
            The processed event result
        """
        if not all([app_name, session_service, memory_service]):
            raise ValueError("app_name, session_service, and memory_service must be provided to process method.")
        
        # Create a runner with the provided services
        runner = Runner(
            agent=self,
            app_name=app_name,
            session_service=session_service,
            memory_service=memory_service
        )
        
        # Run the event through the runner
        return await runner.run(event)

class EmailAgent:
    def __init__(self, mcp_client, *args, **kwargs):
        self.mcp_client = mcp_client
        # ... other init ...

    async def process(self, event):
        # Stub: just echo the event for testing
        return {"content": f"EmailAgent received: {event['content']}"}

def create_email_agent():
    """
    Create the Email Agent with complete ADK integration.
    
    Returns:
        LlmAgent: Configured email agent ready for ADK hierarchy
    """
    print("--- Creating Email Agent with ADK Integration ---")

    # Define model for the agent
    model = LiteLlm(
        model=settings.EMAIL_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )

    # Create MCP client
    mcp_client = MCPClient(
        host=settings.MCP_HOST,
        port=settings.MCP_PORT
    )

    # Create the Email Agent with proper ADK patterns
    agent_instance = ProcessableEmailAgent(
        name="email_agent",
        description="Handles Gmail operations with MCP client access and session state integration",
        model=model,
        instruction="""
Handles Gmail operations: connection, email management, sending, organizing using direct Gmail API access
        """,
        tools=[
            load_memory,
            # Gmail connection tools
            gmail_check_connection,
            gmail_authenticate,
            # Gmail reading tools
            gmail_list_messages,
            gmail_get_message,
            gmail_search_messages,
            # Gmail sending tools
            gmail_send_message,
            gmail_reply_to_message,
            # Gmail organization tools
            gmail_mark_as_read,
            gmail_archive_message,
            gmail_delete_message
        ],
        output_key="email_result"
    )
    
    return agent_instance

# Gmail connection tools
async def gmail_check_connection(tool_context):
    """
    Check Gmail connection status.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        dict: Connection status
    """
    # Check session state for connection status
    is_connected = tool_context.session.state.get(USER_GMAIL_CONNECTED, False)
    
    # If not connected in session state, try to authenticate
    if not is_connected:
        return {
            "status": "disconnected",
            "message": "Gmail is not connected. Please authenticate first."
        }
    
    # If connected in session state, verify with MCP client
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Try to list messages to verify connection
        response = await mcp_client.list_gmail_messages(query="is:unread", max_results=1)
        
        if response.get("status") == "success":
            return {
                "status": "connected",
                "message": "Gmail is connected and working properly."
            }
        else:
            # Update session state
            tool_context.session.state[USER_GMAIL_CONNECTED] = False
            
            return {
                "status": "disconnected",
                "message": f"Gmail connection failed: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        # Update session state
        tool_context.session.state[USER_GMAIL_CONNECTED] = False
        
        return {
            "status": "error",
            "message": f"Error checking Gmail connection: {str(e)}"
        }

async def gmail_authenticate(tool_context):
    """
    Authenticate with Gmail.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        dict: Authentication status
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Try to list messages to verify authentication
        response = await mcp_client.list_gmail_messages(query="is:unread", max_results=1)
        
        if response.get("status") == "success":
            # Update session state
            tool_context.session.state[USER_GMAIL_CONNECTED] = True
            
            # Get user profile
            profile = await mcp_client.send_request("gmail", "get_profile", {})
            
            if profile.get("status") == "success":
                user_email = profile.get("data", {}).get("emailAddress", "")
                user_name = profile.get("data", {}).get("displayName", "")
                
                # Update session state with user info
                tool_context.session.state[USER_EMAIL] = user_email
                tool_context.session.state[USER_NAME] = user_name
            
            return {
                "status": "success",
                "message": "Gmail authentication successful."
            }
        else:
            return {
                "status": "error",
                "message": f"Gmail authentication failed: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error authenticating with Gmail: {str(e)}"
        }

# Gmail reading tools
async def gmail_list_messages(tool_context, query: str = "", max_results: int = 10):
    """
    List Gmail messages.
    
    Args:
        tool_context: ADK tool context
        query: Gmail search query
        max_results: Maximum number of results to return
        
    Returns:
        dict: List of messages
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # List messages
        response = await mcp_client.list_gmail_messages(query=query, max_results=max_results)
        
        if response.get("status") == "success":
            # Update session state
            tool_context.session.state[EMAIL_CURRENT_RESULTS] = response.get("data", [])
            tool_context.session.state[EMAIL_LAST_FETCH] = asyncio.get_event_loop().time()
            
            # Count unread messages
            unread_count = sum(1 for msg in response.get("data", []) if msg.get("is_unread", False))
            tool_context.session.state[EMAIL_UNREAD_COUNT] = unread_count
            
            return {
                "status": "success",
                "data": response.get("data", []),
                "count": len(response.get("data", [])),
                "unread_count": unread_count
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to list messages: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing messages: {str(e)}"
        }

async def gmail_get_message(tool_context, message_id: str):
    """
    Get Gmail message details.
    
    Args:
        tool_context: ADK tool context
        message_id: Message ID
        
    Returns:
        dict: Message details
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Get message
        response = await mcp_client.get_gmail_message(message_id=message_id)
        
        if response.get("status") == "success":
            return {
                "status": "success",
                "data": response.get("data", {})
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to get message: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting message: {str(e)}"
        }

async def gmail_search_messages(tool_context, query: str, max_results: int = 10):
    """
    Search Gmail messages.
    
    Args:
        tool_context: ADK tool context
        query: Gmail search query
        max_results: Maximum number of results to return
        
    Returns:
        dict: Search results
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Search messages
        response = await mcp_client.list_gmail_messages(query=query, max_results=max_results)
        
        if response.get("status") == "success":
            # Update session state
            tool_context.session.state[EMAIL_CURRENT_RESULTS] = response.get("data", [])
            tool_context.session.state[EMAIL_LAST_FETCH] = asyncio.get_event_loop().time()
            
            return {
                "status": "success",
                "data": response.get("data", []),
                "count": len(response.get("data", [])),
                "query": query
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to search messages: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching messages: {str(e)}"
        }

# Gmail sending tools
async def gmail_send_message(tool_context, to: str, subject: str, body: str, cc: Optional[str] = None, bcc: Optional[str] = None):
    """
    Send Gmail message.
    
    Args:
        tool_context: ADK tool context
        to: Recipient email address
        subject: Email subject
        body: Email body
        cc: CC email address
        bcc: BCC email address
        
    Returns:
        dict: Send status
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Prepare parameters
        params = {
            "to": to,
            "subject": subject,
            "body": body
        }
        
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc
        
        # Send message
        response = await mcp_client.send_gmail_message(**params)
        
        if response.get("status") == "success":
            # Update session state
            tool_context.session.state[EMAIL_LAST_SENT] = {
                "to": to,
                "subject": subject,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            return {
                "status": "success",
                "message": "Email sent successfully.",
                "data": response.get("data", {})
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to send email: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error sending email: {str(e)}"
        }

async def gmail_reply_to_message(tool_context, message_id: str, reply_text: str):
    """
    Reply to Gmail message.
    
    Args:
        tool_context: ADK tool context
        message_id: Message ID to reply to
        reply_text: Reply text
        
    Returns:
        dict: Reply status
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Get original message
        message_response = await mcp_client.get_gmail_message(message_id=message_id)
        
        if message_response.get("status") != "success":
            return {
                "status": "error",
                "message": f"Failed to get original message: {message_response.get('message', 'Unknown error')}"
            }
        
        # Extract original message details
        original_message = message_response.get("data", {})
        subject = original_message.get("subject", "")
        
        # Add "Re:" prefix if not already present
        if not subject.startswith("Re:"):
            subject = f"Re: {subject}"
        
        # Get sender email
        sender = original_message.get("from", "")
        
        # Send reply
        response = await mcp_client.send_gmail_message(
            to=sender,
            subject=subject,
            body=reply_text
        )
        
        if response.get("status") == "success":
            # Update session state
            tool_context.session.state[EMAIL_LAST_SENT] = {
                "to": sender,
                "subject": subject,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            return {
                "status": "success",
                "message": "Reply sent successfully.",
                "data": response.get("data", {})
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to send reply: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error sending reply: {str(e)}"
        }

# Gmail organization tools
async def gmail_mark_as_read(tool_context, message_id: str):
    """
    Mark Gmail message as read.
    
    Args:
        tool_context: ADK tool context
        message_id: Message ID
        
    Returns:
        dict: Operation status
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Mark as read
        response = await mcp_client.send_request("gmail", "modify_labels", {
            "message_id": message_id,
            "add_labels": [],
            "remove_labels": ["UNREAD"]
        })
        
        if response.get("status") == "success":
            # Update session state
            current_results = tool_context.session.state.get(EMAIL_CURRENT_RESULTS, [])
            for msg in current_results:
                if msg.get("id") == message_id:
                    msg["is_unread"] = False
            
            tool_context.session.state[EMAIL_CURRENT_RESULTS] = current_results
            
            # Update unread count
            unread_count = sum(1 for msg in current_results if msg.get("is_unread", False))
            tool_context.session.state[EMAIL_UNREAD_COUNT] = unread_count
            
            return {
                "status": "success",
                "message": "Message marked as read."
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to mark message as read: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error marking message as read: {str(e)}"
        }

async def gmail_archive_message(tool_context, message_id: str):
    """
    Archive Gmail message.
    
    Args:
        tool_context: ADK tool context
        message_id: Message ID
        
    Returns:
        dict: Operation status
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Archive message
        response = await mcp_client.send_request("gmail", "modify_labels", {
            "message_id": message_id,
            "add_labels": [],
            "remove_labels": ["INBOX"]
        })
        
        if response.get("status") == "success":
            # Update session state
            current_results = tool_context.session.state.get(EMAIL_CURRENT_RESULTS, [])
            current_results = [msg for msg in current_results if msg.get("id") != message_id]
            
            tool_context.session.state[EMAIL_CURRENT_RESULTS] = current_results
            
            return {
                "status": "success",
                "message": "Message archived."
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to archive message: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error archiving message: {str(e)}"
        }

async def gmail_delete_message(tool_context, message_id: str):
    """
    Delete Gmail message.
    
    Args:
        tool_context: ADK tool context
        message_id: Message ID
        
    Returns:
        dict: Operation status
    """
    try:
        # Create MCP client
        mcp_client = MCPClient(
            host=settings.MCP_HOST,
            port=settings.MCP_PORT
        )
        
        # Delete message
        response = await mcp_client.send_request("gmail", "delete_message", {
            "message_id": message_id
        })
        
        if response.get("status") == "success":
            # Update session state
            current_results = tool_context.session.state.get(EMAIL_CURRENT_RESULTS, [])
            current_results = [msg for msg in current_results if msg.get("id") != message_id]
            
            tool_context.session.state[EMAIL_CURRENT_RESULTS] = current_results
            
            return {
                "status": "success",
                "message": "Message deleted."
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to delete message: {response.get('message', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error deleting message: {str(e)}"
        }

def create_email_runner():
    """
    Create an email agent runner for testing.
    
    Returns:
        Runner: Email agent runner
    """
    from google.adk.runner import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.memory import InMemoryMemoryService
    
    # Create the agent
    agent = create_email_agent()
    
    # Create services
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    
    # Create runner with proper configuration
    runner = Runner(
        agent=agent,
        app_name="test_app",
        session_service=session_service,
        memory_service=memory_service
    )
    
    return runner

if __name__ == "__main__":
    def test_email_agent_adk_integration():
        """
        Test the email agent ADK integration.
        """
        import asyncio
        
        async def run_test():
            runner = create_email_runner()
            
            # Test connection
            connection_result = await runner.run("Check my Gmail connection")
            print(f"Connection result: {connection_result}")
            
            # Test listing messages
            list_result = await runner.run("List my unread emails")
            print(f"List result: {list_result}")
            
            # Test getting a message
            if list_result.get("data", {}).get("count", 0) > 0:
                message_id = list_result.get("data", {}).get("data", [])[0].get("id")
                get_result = await runner.run(f"Get email details for ID {message_id}")
                print(f"Get result: {get_result}")
            
            # Test searching messages
            search_result = await runner.run("Search for emails from Google")
            print(f"Search result: {search_result}")
            
            # Test sending a message
            send_result = await runner.run("Send a test email to myself")
            print(f"Send result: {send_result}")
            
            # Test replying to a message
            if list_result.get("data", {}).get("count", 0) > 0:
                message_id = list_result.get("data", {}).get("data", [])[0].get("id")
                reply_result = await runner.run(f"Reply to message ID {message_id} with 'This is a test reply'")
                print(f"Reply result: {reply_result}")
            
            # Test marking a message as read
            if list_result.get("data", {}).get("count", 0) > 0:
                message_id = list_result.get("data", {}).get("data", [])[0].get("id")
                mark_result = await runner.run(f"Mark message ID {message_id} as read")
                print(f"Mark result: {mark_result}")
            
            # Test archiving a message
            if list_result.get("data", {}).get("count", 0) > 0:
                message_id = list_result.get("data", {}).get("data", [])[0].get("id")
                archive_result = await runner.run(f"Archive message ID {message_id}")
                print(f"Archive result: {archive_result}")
            
            # Test deleting a message
            if list_result.get("data", {}).get("count", 0) > 0:
                message_id = list_result.get("data", {}).get("data", [])[0].get("id")
                delete_result = await runner.run(f"Delete message ID {message_id}")
                print(f"Delete result: {delete_result}")
        
        asyncio.run(run_test())
    
    test_email_agent_adk_integration()