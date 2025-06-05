"""
Model Context Protocol (MCP) Server for Oprina.

This module implements the Model Context Protocol (MCP) server that handles requests from ADK
and provides access to Gmail, Calendar, and Content tools.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the configuration
from mcp_server.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config["mcp_log_level"], logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MCP Protocol Constants
MCP_VERSION = config["mcp_protocol_version"]
MCP_MESSAGE_TYPES = {
    "HELLO": "hello",
    "TOOL_DISCOVERY": "tool_discovery",
    "TOOL_CALL": "tool_call",
    "TOOL_RESULT": "tool_result",
    "ERROR": "error"
}

# Import tool modules
try:
    from mcp_server.tools.gmail_tool import gmail_tools
    from mcp_server.tools.calendar_tool import calendar_tools
    from mcp_server.tools.content_tool import content_tools
    TOOLS_AVAILABLE = True
except ImportError:
    logger.warning("Tool modules not available, running in fallback mode")
    TOOLS_AVAILABLE = False

class MCPServer:
    """
    Model Context Protocol (MCP) Server.
    
    This class implements the Model Context Protocol (MCP) server that handles requests from ADK
    and provides access to Gmail, Calendar, and Content tools.
    """
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the MCP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host or config["mcp_server_host"]
        self.port = port or config["mcp_server_port"]
        self.tools = {}
        self.tool_schemas = {}
        self.api_key = config["mcp_server_api_key"]
    
    async def register_tools(self):
        """
        Register tools with the server.
        """
        if TOOLS_AVAILABLE:
            # Register Gmail tools
            for tool in gmail_tools:
                self.tools[tool["name"]] = tool["function"]
                self.tool_schemas[tool["name"]] = tool["schema"]
            
            # Register Calendar tools
            for tool in calendar_tools:
                self.tools[tool["name"]] = tool["function"]
                self.tool_schemas[tool["name"]] = tool["schema"]
            
            # Register Content tools
            for tool in content_tools:
                self.tools[tool["name"]] = tool["function"]
                self.tool_schemas[tool["name"]] = tool["schema"]
        else:
            # Register fallback tools
            self._register_fallback_tools()
        
        logger.info(f"Registered {len(self.tools)} tools")
    
    def _register_fallback_tools(self):
        """
        Register fallback tools.
        """
        # Gmail fallback tools
        self.tools["gmail_check_connection"] = self._fallback_gmail_check_connection
        self.tools["gmail_list_messages"] = self._fallback_gmail_list_messages
        self.tools["gmail_get_message"] = self._fallback_gmail_get_message
        self.tools["gmail_send_message"] = self._fallback_gmail_send_message
        self.tools["gmail_delete_message"] = self._fallback_gmail_delete_message
        
        # Calendar fallback tools
        self.tools["calendar_check_connection"] = self._fallback_calendar_check_connection
        self.tools["calendar_list_events"] = self._fallback_calendar_list_events
        self.tools["calendar_get_event"] = self._fallback_calendar_get_event
        self.tools["calendar_create_event"] = self._fallback_calendar_create_event
        self.tools["calendar_update_event"] = self._fallback_calendar_update_event
        self.tools["calendar_delete_event"] = self._fallback_calendar_delete_event
        
        # Content fallback tools
        self.tools["content_summarize_text"] = self._fallback_content_summarize_text
        self.tools["content_extract_keywords"] = self._fallback_content_extract_keywords
        self.tools["content_analyze_sentiment"] = self._fallback_content_analyze_sentiment
        
        # Register tool schemas
        self.tool_schemas = {
            "gmail_check_connection": {
                "name": "gmail_check_connection",
                "description": "Check the Gmail connection status",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "gmail_list_messages": {
                "name": "gmail_list_messages",
                "description": "List Gmail messages",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Gmail search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return"
                        }
                    },
                    "required": []
                }
            },
            "gmail_get_message": {
                "name": "gmail_get_message",
                "description": "Get a Gmail message",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "Message ID"
                        }
                    },
                    "required": ["message_id"]
                }
            },
            "gmail_send_message": {
                "name": "gmail_send_message",
                "description": "Send a Gmail message",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject"
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            "gmail_delete_message": {
                "name": "gmail_delete_message",
                "description": "Delete a Gmail message",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "Message ID"
                        }
                    },
                    "required": ["message_id"]
                }
            },
            "calendar_check_connection": {
                "name": "calendar_check_connection",
                "description": "Check the Calendar connection status",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "calendar_list_events": {
                "name": "calendar_list_events",
                "description": "List Calendar events",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_min": {
                            "type": "string",
                            "description": "Start time for events (ISO format)"
                        },
                        "time_max": {
                            "type": "string",
                            "description": "End time for events (ISO format)"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return"
                        },
                        "single_events": {
                            "type": "boolean",
                            "description": "Whether to expand recurring events"
                        }
                    },
                    "required": []
                }
            },
            "calendar_get_event": {
                "name": "calendar_get_event",
                "description": "Get a Calendar event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Event ID"
                        }
                    },
                    "required": ["event_id"]
                }
            },
            "calendar_create_event": {
                "name": "calendar_create_event",
                "description": "Create a Calendar event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Event summary/title"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start time (ISO format)"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End time (ISO format)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Event description"
                        },
                        "location": {
                            "type": "string",
                            "description": "Event location"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of attendee email addresses"
                        }
                    },
                    "required": ["summary", "start_time", "end_time"]
                }
            },
            "calendar_update_event": {
                "name": "calendar_update_event",
                "description": "Update a Calendar event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Event ID"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Event summary/title"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start time (ISO format)"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End time (ISO format)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Event description"
                        },
                        "location": {
                            "type": "string",
                            "description": "Event location"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of attendee email addresses"
                        }
                    },
                    "required": ["event_id"]
                }
            },
            "calendar_delete_event": {
                "name": "calendar_delete_event",
                "description": "Delete a Calendar event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Event ID"
                        }
                    },
                    "required": ["event_id"]
                }
            },
            "content_summarize_text": {
                "name": "content_summarize_text",
                "description": "Summarize text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to summarize"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum length of summary"
                        }
                    },
                    "required": ["text"]
                }
            },
            "content_extract_keywords": {
                "name": "content_extract_keywords",
                "description": "Extract keywords from text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to extract keywords from"
                        },
                        "max_keywords": {
                            "type": "integer",
                            "description": "Maximum number of keywords to extract"
                        }
                    },
                    "required": ["text"]
                }
            },
            "content_analyze_sentiment": {
                "name": "content_analyze_sentiment",
                "description": "Analyze sentiment of text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze"
                        }
                    },
                    "required": ["text"]
                }
            }
        }
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get the tool schemas.
        
        Returns:
            List[Dict[str, Any]]: The tool schemas
        """
        return list(self.tool_schemas.values())
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP request.
        
        Args:
            request: The MCP request
            
        Returns:
            Dict[str, Any]: The MCP response
        """
        message_type = request.get("type")
        
        if message_type == MCP_MESSAGE_TYPES["HELLO"]:
            return self._handle_hello(request)
        elif message_type == MCP_MESSAGE_TYPES["TOOL_DISCOVERY"]:
            return self._handle_tool_discovery(request)
        elif message_type == MCP_MESSAGE_TYPES["TOOL_CALL"]:
            return await self._handle_tool_call(request)
        else:
            return self._handle_error(f"Unknown message type: {message_type}")
    
    def _handle_hello(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a HELLO message.
        
        Args:
            request: The HELLO message
            
        Returns:
            Dict[str, Any]: The HELLO response
        """
        return {
            "type": MCP_MESSAGE_TYPES["HELLO"],
            "version": MCP_VERSION,
            "capabilities": ["tool_discovery", "tool_call"]
        }
    
    def _handle_tool_discovery(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a TOOL_DISCOVERY message.
        
        Args:
            request: The TOOL_DISCOVERY message
            
        Returns:
            Dict[str, Any]: The TOOL_DISCOVERY response
        """
        return {
            "type": MCP_MESSAGE_TYPES["TOOL_DISCOVERY"],
            "version": MCP_VERSION,
            "tools": self.get_tool_schemas()
        }
    
    async def _handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a TOOL_CALL message.
        
        Args:
            request: The TOOL_CALL message
            
        Returns:
            Dict[str, Any]: The TOOL_CALL response
        """
        tool_name = request.get("tool")
        tool_params = request.get("params", {})
        
        if not tool_name:
            return self._handle_error("Tool name is required")
        
        if tool_name not in self.tools:
            return self._handle_error(f"Unknown tool: {tool_name}")
        
        try:
            # Call the tool
            tool_result = await self.tools[tool_name](**tool_params)
            
            return {
                "type": MCP_MESSAGE_TYPES["TOOL_RESULT"],
                "tool": tool_name,
                "result": tool_result
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return self._handle_error(f"Error calling tool {tool_name}: {str(e)}")
    
    def _handle_error(self, message: str) -> Dict[str, Any]:
        """
        Handle an error.
        
        Args:
            message: The error message
            
        Returns:
            Dict[str, Any]: The error response
        """
        return {
            "type": MCP_MESSAGE_TYPES["ERROR"],
            "message": message
        }
    
    # Fallback tool implementations
    async def _fallback_gmail_check_connection(self) -> Dict[str, Any]:
        """Fallback implementation of gmail_check_connection."""
        logger.info("Fallback gmail_check_connection called")
        return {"status": "success", "message": "Gmail connection checked (fallback)"}
    
    async def _fallback_gmail_list_messages(self, query: str = "", max_results: int = 10) -> Dict[str, Any]:
        """Fallback implementation of gmail_list_messages."""
        logger.info(f"Fallback gmail_list_messages called with query={query}, max_results={max_results}")
        return {
            "status": "success",
            "messages": [
                {
                    "id": f"fallback_message_{i}",
                    "thread_id": f"fallback_thread_{i}",
                    "snippet": f"Fallback message snippet {i}",
                    "from": "fallback@example.com",
                    "to": "user@example.com",
                    "subject": f"Fallback subject {i}",
                    "date": "2023-01-01T00:00:00Z"
                }
                for i in range(min(max_results, 5))
            ]
        }
    
    async def _fallback_gmail_get_message(self, message_id: str) -> Dict[str, Any]:
        """Fallback implementation of gmail_get_message."""
        logger.info(f"Fallback gmail_get_message called with message_id={message_id}")
        return {
            "status": "success",
            "message": {
                "id": message_id,
                "thread_id": "fallback_thread_1",
                "snippet": "Fallback message snippet",
                "from": "fallback@example.com",
                "to": "user@example.com",
                "subject": "Fallback subject",
                "date": "2023-01-01T00:00:00Z",
                "body": "This is a fallback message body."
            }
        }
    
    async def _fallback_gmail_send_message(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Fallback implementation of gmail_send_message."""
        logger.info(f"Fallback gmail_send_message called with to={to}, subject={subject}")
        return {
            "status": "success",
            "message_id": "fallback_sent_message_1",
            "thread_id": "fallback_thread_1"
        }
    
    async def _fallback_gmail_delete_message(self, message_id: str) -> Dict[str, Any]:
        """Fallback implementation of gmail_delete_message."""
        logger.info(f"Fallback gmail_delete_message called with message_id={message_id}")
        return {"status": "success"}
    
    async def _fallback_calendar_check_connection(self) -> Dict[str, Any]:
        """Fallback implementation of calendar_check_connection."""
        logger.info("Fallback calendar_check_connection called")
        return {"status": "success", "message": "Calendar connection checked (fallback)"}
    
    async def _fallback_calendar_list_events(self, time_min: str = None, time_max: str = None, 
                                           max_results: int = 10, single_events: bool = True) -> Dict[str, Any]:
        """Fallback implementation of calendar_list_events."""
        logger.info(f"Fallback calendar_list_events called with time_min={time_min}, time_max={time_max}, max_results={max_results}")
        return {
            "status": "success",
            "events": [
                {
                    "id": f"fallback_event_{i}",
                    "summary": f"Fallback event {i}",
                    "description": f"Fallback event description {i}",
                    "start": {"dateTime": "2023-01-01T10:00:00Z"},
                    "end": {"dateTime": "2023-01-01T11:00:00Z"},
                    "location": "Fallback location",
                    "attendees": [{"email": "user@example.com"}]
                }
                for i in range(min(max_results, 5))
            ]
        }
    
    async def _fallback_calendar_get_event(self, event_id: str) -> Dict[str, Any]:
        """Fallback implementation of calendar_get_event."""
        logger.info(f"Fallback calendar_get_event called with event_id={event_id}")
        return {
            "status": "success",
            "event": {
                "id": event_id,
                "summary": "Fallback event",
                "description": "Fallback event description",
                "start": {"dateTime": "2023-01-01T10:00:00Z"},
                "end": {"dateTime": "2023-01-01T11:00:00Z"},
                "location": "Fallback location",
                "attendees": [{"email": "user@example.com"}]
            }
        }
    
    async def _fallback_calendar_create_event(self, summary: str, start_time: str, end_time: str,
                                           description: str = None, location: str = None,
                                           attendees: list = None) -> Dict[str, Any]:
        """Fallback implementation of calendar_create_event."""
        logger.info(f"Fallback calendar_create_event called with summary={summary}, start_time={start_time}, end_time={end_time}")
        return {
            "status": "success",
            "event_id": "fallback_created_event_1"
        }
    
    async def _fallback_calendar_update_event(self, event_id: str, summary: str = None, start_time: str = None,
                                           end_time: str = None, description: str = None,
                                           location: str = None, attendees: list = None) -> Dict[str, Any]:
        """Fallback implementation of calendar_update_event."""
        logger.info(f"Fallback calendar_update_event called with event_id={event_id}")
        return {"status": "success"}
    
    async def _fallback_calendar_delete_event(self, event_id: str) -> Dict[str, Any]:
        """Fallback implementation of calendar_delete_event."""
        logger.info(f"Fallback calendar_delete_event called with event_id={event_id}")
        return {"status": "success"}
    
    async def _fallback_content_summarize_text(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """Fallback implementation of content_summarize_text."""
        logger.info(f"Fallback content_summarize_text called with text length={len(text)}, max_length={max_length}")
        return {
            "status": "success",
            "summary": "This is a fallback summary of the text."
        }
    
    async def _fallback_content_extract_keywords(self, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """Fallback implementation of content_extract_keywords."""
        logger.info(f"Fallback content_extract_keywords called with text length={len(text)}, max_keywords={max_keywords}")
        return {
            "status": "success",
            "keywords": ["fallback", "keyword", "example"]
        }
    
    async def _fallback_content_analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Fallback implementation of content_analyze_sentiment."""
        logger.info(f"Fallback content_analyze_sentiment called with text length={len(text)}")
        return {
            "status": "success",
            "sentiment": "neutral",
            "score": 0.0
        }

async def main():
    """
    Main entry point for the MCP server.
    """
    server = MCPServer()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main()) 