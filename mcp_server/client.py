"""
Simple client for testing the Oprina MCP server.

This module provides a simple client for testing the MCP server.
"""

import os
import json
import asyncio
import logging
import websockets
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MCPClient:
    """
    Simple client for testing the MCP server.
    
    This class provides methods for sending requests to the MCP server
    and receiving responses.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize the MCP client.
        
        Args:
            host: Host to connect to
            port: Port to connect to
        """
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self.websocket = None
    
    async def connect(self):
        """Connect to the MCP server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"Connected to {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.uri}: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")
    
    async def send_request(self, tool: str, action: str, params: dict = None) -> dict:
        """
        Send a request to the MCP server.
        
        Args:
            tool: Tool to use (gmail, calendar, content)
            action: Action to perform
            params: Action parameters
            
        Returns:
            dict: Response from the server
        """
        if not self.websocket:
            await self.connect()
        
        request = {
            "tool": tool,
            "action": action,
            "params": params or {}
        }
        
        logger.info(f"Sending request: {request}")
        await self.websocket.send(json.dumps(request))
        
        response = await self.websocket.recv()
        logger.info(f"Received response: {response}")
        
        return json.loads(response)
    
    async def list_gmail_messages(self, query: str = "", max_results: int = 10) -> dict:
        """
        List Gmail messages.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results to return
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("gmail", "list_messages", {
            "query": query,
            "max_results": max_results
        })
    
    async def get_gmail_message(self, message_id: str) -> dict:
        """
        Get a Gmail message.
        
        Args:
            message_id: Message ID
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("gmail", "get_message", {
            "message_id": message_id
        })
    
    async def send_gmail_message(self, to: str, subject: str, body: str) -> dict:
        """
        Send a Gmail message.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("gmail", "send_message", {
            "to": to,
            "subject": subject,
            "body": body
        })
    
    async def list_calendar_events(self, time_min: str = None, time_max: str = None, 
                                  max_results: int = 10, single_events: bool = True) -> dict:
        """
        List Calendar events.
        
        Args:
            time_min: Start time for events (ISO format)
            time_max: End time for events (ISO format)
            max_results: Maximum number of results to return
            single_events: Whether to expand recurring events
            
        Returns:
            dict: Response from the server
        """
        params = {
            "max_results": max_results,
            "single_events": single_events
        }
        
        if time_min:
            params["time_min"] = time_min
        if time_max:
            params["time_max"] = time_max
        
        return await self.send_request("calendar", "list_events", params)
    
    async def create_calendar_event(self, summary: str, start_time: str, end_time: str,
                                   description: str = None, location: str = None,
                                   attendees: list = None) -> dict:
        """
        Create a Calendar event.
        
        Args:
            summary: Event summary/title
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            description: Event description
            location: Event location
            attendees: List of attendee email addresses
            
        Returns:
            dict: Response from the server
        """
        params = {
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time
        }
        
        if description:
            params["description"] = description
        if location:
            params["location"] = location
        if attendees:
            params["attendees"] = attendees
        
        return await self.send_request("calendar", "create_event", params)
    
    # Content tool methods
    async def summarize_email_content(self, content: str, detail_level: str = "moderate") -> dict:
        """
        Summarize email content.
        
        Args:
            content: Email content to summarize
            detail_level: Detail level for summary (brief, moderate, detailed)
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("content", "summarize_email_content", {
            "content": content,
            "detail_level": detail_level
        })
    
    async def summarize_email_list(self, emails: str, max_emails: int = 5) -> dict:
        """
        Summarize a list of emails.
        
        Args:
            emails: List of emails to summarize
            max_emails: Maximum number of emails to summarize
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("content", "summarize_email_list", {
            "emails": emails,
            "max_emails": max_emails
        })
    
    async def generate_email_reply(self, original_email: str, reply_intent: str, style: str = "professional") -> dict:
        """
        Generate email reply.
        
        Args:
            original_email: Original email content
            reply_intent: User's intent for the reply
            style: Reply style (brief, professional, formal, friendly)
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("content", "generate_email_reply", {
            "original_email": original_email,
            "reply_intent": reply_intent,
            "style": style
        })
    
    async def analyze_email_sentiment(self, content: str) -> dict:
        """
        Analyze email sentiment.
        
        Args:
            content: Email content to analyze
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("content", "analyze_email_sentiment", {
            "content": content
        })
    
    async def extract_action_items(self, content: str) -> dict:
        """
        Extract action items from email content.
        
        Args:
            content: Email content to analyze
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("content", "extract_action_items", {
            "content": content
        })
    
    async def optimize_for_voice(self, content: str, max_length: int = 200) -> dict:
        """
        Optimize text for voice delivery.
        
        Args:
            content: Text to optimize
            max_length: Maximum length of optimized text
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("content", "optimize_for_voice", {
            "content": content,
            "max_length": max_length
        })
    
    async def create_voice_summary(self, content: str) -> dict:
        """
        Create a voice-optimized summary.
        
        Args:
            content: Content to summarize
            
        Returns:
            dict: Response from the server
        """
        return await self.send_request("content", "create_voice_summary", {
            "content": content
        })

    async def authenticate_gmail(self) -> dict:
        """
        Authenticate with Gmail.
        
        Returns:
            dict: Response from the server
        """
        return await self.send_request("gmail", "authenticate", {})

    async def authenticate_calendar(self) -> dict:
        """
        Authenticate with Calendar.
        
        Returns:
            dict: Response from the server
        """
        return await self.send_request("calendar", "authenticate", {})

async def main():
    """Main entry point for the MCP client."""
    # Get host and port from environment variables
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8765"))
    
    logger.info(f"Connecting to MCP server at {host}:{port}")
    
    # Create the client
    client = MCPClient(host, port)
    
    try:
        # Connect to the server
        await client.connect()
        
        # Example: List Gmail messages
        response = await client.list_gmail_messages("is:unread", 5)
        print(json.dumps(response, indent=2))
        
        # Example: List Calendar events
        response = await client.list_calendar_events(max_results=5)
        print(json.dumps(response, indent=2))
        
        # Example: Summarize email content
        sample_email = """
        From: John Doe <john.doe@example.com>
        Subject: Project Update
        
        Hi Team,
        
        I wanted to provide an update on the project we discussed last week. We've made significant progress on the frontend implementation and are now moving to the backend integration phase.
        
        The timeline is still on track, and we expect to complete the first phase by the end of the month. Please let me know if you have any questions or concerns.
        
        Best regards,
        John
        """
        response = await client.summarize_email_content(sample_email, "moderate")
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Disconnect from the server
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 