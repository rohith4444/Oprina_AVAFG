"""
Main server module for the Oprina MCP server.

This module implements the Model Context Protocol (MCP) server that handles
requests from the client and provides access to Gmail and Calendar tools.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
import websockets
from dotenv import load_dotenv

# Import the auth manager and tools
from mcp_server.auth_manager import AuthManager
from mcp_server.tools.gmail_tool import GmailTool
from mcp_server.tools.calendar_tool import CalendarTool
from mcp_server.tools.content_tool import ContentTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MCPServer:
    """
    Model Context Protocol (MCP) server.
    
    This class implements the MCP server that handles requests from the client
    and provides access to Gmail and Calendar tools.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize the MCP server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.host = host
        self.port = port
        self.auth_manager = AuthManager()
        self.gmail_tool = GmailTool(self.auth_manager)
        self.calendar_tool = CalendarTool(self.auth_manager)
        self.content_tool = ContentTool()
        self.clients = set()
        self.client_sessions = {}  # Map websocket to session state
    
    async def handle_client(self, websocket):
        """
        Handle a client connection.
        
        Args:
            websocket: WebSocket connection
        """
        self.clients.add(websocket)
        # Initialize session state for this client
        self.client_sessions[websocket] = {"gmail_connected": False, "calendar_connected": False}
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            async for message in websocket:
                try:
                    # Parse the message
                    request = json.loads(message)
                    logger.info(f"Received request: {request}")
                    
                    # Pass the session state for this client
                    response = await self.handle_request(request, self.client_sessions[websocket])
                    
                    # Send the response
                    await websocket.send(json.dumps(response))
                    logger.info(f"Sent response: {response}")
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {message}")
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "Invalid JSON"
                    }))
                except Exception as e:
                    logger.error(f"Error handling request: {e}")
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": str(e)
                    }))
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        finally:
            self.clients.remove(websocket)
            # Clean up session state for this client
            if websocket in self.client_sessions:
                del self.client_sessions[websocket]
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def handle_request(self, request: Dict[str, Any], session_state: Dict[str, bool]) -> Dict[str, Any]:
        """
        Handle a request from the client.
        
        Args:
            request: Request data
            session_state: Session state for the client
            
        Returns:
            Dict[str, Any]: Response data
        """
        # Get the tool and action
        tool = request.get("tool")
        action = request.get("action")
        params = request.get("params", {})
        
        if not tool or not action:
            return {
                "status": "error",
                "message": "Missing tool or action"
            }
        
        # Skip global auth check for authenticate action
        if action != "authenticate":
            # Check if the user is authenticated
            if not await self.auth_manager.check_auth():
                return {
                    "status": "error",
                    "message": "Not authenticated with Google services"
                }
        
        # Handle the request based on the tool and action
        try:
            if tool == "gmail":
                return await self.handle_gmail_request(action, params, session_state)
            elif tool == "calendar":
                return await self.handle_calendar_request(action, params, session_state)
            elif tool == "content":
                return await self.handle_content_request(action, params)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown tool: {tool}"
                }
        except Exception as e:
            logger.error(f"Error handling {tool}.{action}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def handle_gmail_request(self, action: str, params: Dict[str, Any], session_state: Dict[str, bool]) -> Dict[str, Any]:
        """
        Handle a Gmail request.
        
        Args:
            action: Action to perform
            params: Action parameters
            session_state: Session state
            
        Returns:
            Dict[str, Any]: Response data
        """
        if action == "authenticate":
            session_state["gmail_connected"] = True
            logger.info(f"[DIAG] Gmail session state updated: {session_state} (id={id(session_state)})")
            return {"status": "success", "message": "Gmail authenticated and session state updated."}
        logger.info(f"[DIAG] Gmail session state at check: {session_state} (id={id(session_state)})")
        logger.info(f"[DIAG] session_state.get('gmail_connected', False): {session_state.get('gmail_connected', False)}")
        if not session_state.get("gmail_connected", False):
            logger.info(f"Gmail not connected. Session state: {session_state}")
            return {"status": "success", "data": [{"result": "Gmail not connected. Please authenticate first."}]}
        if action == "list_messages":
            query = params.get("query", "")
            max_results = params.get("max_results", 10)
            logger.info(f"[DIAG] Calling gmail_tool.list_messages with query='{query}', max_results={max_results}")
            messages = await self.gmail_tool.list_messages(query, max_results, session_state)
            logger.info(f"[DIAG] gmail_tool.list_messages returned: {messages}")
            return {
                "status": "success",
                "data": messages
            }
        elif action == "get_message":
            message_id = params.get("message_id")
            if not message_id:
                return {
                    "status": "error",
                    "message": "Missing message_id"
                }
            message = await self.gmail_tool.get_message_content(message_id)
            return {
                "status": "success",
                "data": message
            }
        elif action == "send_message":
            to = params.get("to")
            subject = params.get("subject")
            body = params.get("body")
            if not to or not subject or not body:
                return {
                    "status": "error",
                    "message": "Missing required parameters: to, subject, body"
                }
            response = await self.gmail_tool.send_message(to, subject, body)
            return {
                "status": "success",
                "data": response
            }
        elif action == "modify_labels":
            message_id = params.get("message_id")
            add_labels = params.get("add_labels")
            remove_labels = params.get("remove_labels")
            if not message_id:
                return {
                    "status": "error",
                    "message": "Missing message_id"
                }
            response = await self.gmail_tool.modify_labels(message_id, add_labels, remove_labels)
            return {
                "status": "success",
                "data": response
            }
        elif action == "list_labels":
            labels = await self.gmail_tool.list_labels()
            return {
                "status": "success",
                "data": labels
            }
        else:
            return {
                "status": "error",
                "message": f"Unknown Gmail action: {action}"
            }
    
    async def handle_calendar_request(self, action: str, params: Dict[str, Any], session_state: Dict[str, bool]) -> Dict[str, Any]:
        """
        Handle a Calendar request.
        
        Args:
            action: Action to perform
            params: Action parameters
            session_state: Session state
            
        Returns:
            Dict[str, Any]: Response data
        """
        if action == "authenticate":
            session_state["calendar_connected"] = True
            logger.info(f"[DIAG] Calendar session state updated: {session_state} (id={id(session_state)})")
            return {"status": "success", "message": "Calendar authenticated and session state updated."}
        logger.info(f"[DIAG] Calendar session state at check: {session_state} (id={id(session_state)})")
        logger.info(f"[DIAG] session_state.get('calendar_connected', False): {session_state.get('calendar_connected', False)}")
        if not session_state.get("calendar_connected", False):
            logger.info(f"Calendar not connected. Session state: {session_state}")
            return {"status": "success", "data": [{"result": "Calendar not connected. Please authenticate first."}]}
        if action == "list_events":
            time_min = params.get("time_min")
            time_max = params.get("time_max")
            max_results = params.get("max_results", 10)
            single_events = params.get("single_events", True)
            logger.info(f"[DIAG] Calling calendar_tool.list_events with time_min={time_min}, time_max={time_max}, max_results={max_results}, single_events={single_events}")
            events = await self.calendar_tool.list_events(time_min, time_max, max_results, single_events, session_state=session_state)
            logger.info(f"[DIAG] calendar_tool.list_events returned: {events}")
            return {
                "status": "success",
                "data": events
            }
        elif action == "get_event":
            event_id = params.get("event_id")
            if not event_id:
                return {
                    "status": "error",
                    "message": "Missing event_id"
                }
            event = await self.calendar_tool.get_event(event_id)
            return {
                "status": "success",
                "data": event
            }
        elif action == "create_event":
            summary = params.get("summary")
            start_time = params.get("start_time")
            end_time = params.get("end_time")
            description = params.get("description")
            location = params.get("location")
            attendees = params.get("attendees")
            if not summary or not start_time or not end_time:
                return {
                    "status": "error",
                    "message": "Missing required parameters: summary, start_time, end_time"
                }
            event = await self.calendar_tool.create_event(
                summary, start_time, end_time, description, location, attendees
            )
            return {
                "status": "success",
                "data": event
            }
        elif action == "update_event":
            event_id = params.get("event_id")
            if not event_id:
                return {
                    "status": "error",
                    "message": "Missing event_id"
                }
            # Remove event_id from params
            params_copy = params.copy()
            params_copy.pop("event_id", None)
            event = await self.calendar_tool.update_event(event_id, **params_copy)
            return {
                "status": "success",
                "data": event
            }
        elif action == "delete_event":
            event_id = params.get("event_id")
            if not event_id:
                return {
                    "status": "error",
                    "message": "Missing event_id"
                }
            await self.calendar_tool.delete_event(event_id)
            return {
                "status": "success",
                "message": "Event deleted"
            }
        elif action == "list_calendars":
            calendars = await self.calendar_tool.list_calendars()
            return {
                "status": "success",
                "data": calendars
            }
        else:
            return {
                "status": "error",
                "message": f"Unknown Calendar action: {action}"
            }
    
    async def handle_content_request(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a Content request.
        
        Args:
            action: Action to perform
            params: Action parameters
            
        Returns:
            Dict[str, Any]: Response data
        """
        if action == "summarize_email_content":
            content = params.get("content")
            detail_level = params.get("detail_level", "moderate")
            if not content:
                return {
                    "status": "error",
                    "message": "Missing content"
                }
            return await self.content_tool.summarize_email_content(content, detail_level)
            
        elif action == "summarize_email_list":
            emails = params.get("emails")
            max_emails = params.get("max_emails", 5)
            if not emails:
                return {
                    "status": "error",
                    "message": "Missing emails"
                }
            return await self.content_tool.summarize_email_list(emails, max_emails)
            
        elif action == "generate_email_reply":
            original_email = params.get("original_email")
            reply_intent = params.get("reply_intent")
            style = params.get("style", "professional")
            if not original_email or not reply_intent:
                return {
                    "status": "error",
                    "message": "Missing original_email or reply_intent"
                }
            return await self.content_tool.generate_email_reply(original_email, reply_intent, style)
            
        elif action == "analyze_email_sentiment":
            content = params.get("content")
            if not content:
                return {
                    "status": "error",
                    "message": "Missing content"
                }
            return await self.content_tool.analyze_email_sentiment(content)
            
        elif action == "extract_action_items":
            content = params.get("content")
            if not content:
                return {
                    "status": "error",
                    "message": "Missing content"
                }
            return await self.content_tool.extract_action_items(content)
            
        elif action == "optimize_for_voice":
            content = params.get("content")
            max_length = params.get("max_length", 200)
            if not content:
                return {
                    "status": "error",
                    "message": "Missing content"
                }
            return await self.content_tool.optimize_for_voice(content, max_length)
            
        elif action == "create_voice_summary":
            content = params.get("content")
            if not content:
                return {
                    "status": "error",
                    "message": "Missing content"
                }
            return await self.content_tool.create_voice_summary(content)
            
        else:
            return {
                "status": "error",
                "message": f"Unknown Content action: {action}"
            }
    
    async def start(self):
        """
        Start the MCP server.
        """
        server = await websockets.serve(self.handle_client, self.host, self.port)
        logger.info(f"MCP server started on ws://{self.host}:{self.port}")
        await server.wait_closed()

async def main():
    """
    Main entry point for the MCP server.
    """
    server = MCPServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main()) 