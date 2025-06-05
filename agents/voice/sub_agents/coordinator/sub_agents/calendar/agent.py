"""
Calendar Agent for ADK Integration

This module provides a calendar agent that handles Calendar operations using direct API tools
instead of the MCP client.
"""

import os
import sys
import asyncio
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.append(str(project_root))

# Import project modules
from config.settings import settings
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("calendar_agent", console_output=True)

# --- ADK Imports with Fallback ---
try:
    from google.adk.agent import LlmAgent
    from google.adk.runner import Runner
    from google.adk.tools import FunctionTool
    from google.adk.types import LiteLlm
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    ADK_IMPORT_ERROR = "ADK not available, running in fallback mode"
    
    # Fallback implementation
    class LlmAgent:
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'fallback_agent')
            self.description = kwargs.get('description', 'Fallback agent')
            self.tools = kwargs.get('tools', [])
            self.model = kwargs.get('model', None)
            
        async def process(self, event):
            logger.info(f"Fallback agent processing event: {event}")
            return {"response": "Fallback agent response"}
    
    class Runner:
        def __init__(self, agent, **kwargs):
            self.agent = agent
            self.services = kwargs.get('services', {})
            
        async def run(self, event):
            logger.info(f"Fallback runner running event: {event}")
            return await self.agent.process(event)
    
    class LiteLlm:
        def __init__(self, **kwargs):
            self.model = kwargs.get('model', 'fallback_model')
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens', 1000)
    
    class FunctionTool:
        def __init__(self, func=None, **kwargs):
            self.func = func
            self.name = kwargs.get('name', func.__name__ if func else 'unknown')
            self.description = kwargs.get('description', '')
            self.parameters = kwargs.get('parameters', {})
            
        def __call__(self, *args, **kwargs):
            if self.func:
                return self.func(*args, **kwargs)
            return {"error": "Function not implemented"}

# Import direct tools
from agents.common.calendar_tools import calendar_tools
from agents.common.gmail_tools import gmail_tools

class ProcessableCalendarAgent:
    """
    Processable agent that handles events with session state handling and tool context forwarding.
    """
    
    def __init__(self, agent):
        self.agent = agent
        
    async def process(self, event):
        # Extract session from event
        session = _extract_session(event)
        
        # Create tool context with session
        tool_context = {"session": session} if session else {}
        
        # Process event with tool context
        return await self.agent.process(event, tool_context=tool_context)

class CalendarAgent:
    """
    Calendar agent that handles Calendar operations.
    """
    
    def __init__(self, model=None, tools=None):
        self.model = model
        self.tools = tools or []
        
    async def process(self, event, tool_context=None):
        # Extract intent from event
        intent = event.get("intent", {}).get("name", "")
        parameters = event.get("intent", {}).get("parameters", {})
        
        # Process intent
        if intent == "calendar_check_connection":
            return await self._handle_check_connection(tool_context)
        elif intent == "calendar_authenticate":
            return await self._handle_authenticate(tool_context)
        elif intent == "calendar_list_events":
            return await self._handle_list_events(parameters, tool_context)
        elif intent == "calendar_get_event":
            return await self._handle_get_event(parameters, tool_context)
        elif intent == "calendar_create_event":
            return await self._handle_create_event(parameters, tool_context)
        elif intent == "calendar_update_event":
            return await self._handle_update_event(parameters, tool_context)
        elif intent == "calendar_delete_event":
            return await self._handle_delete_event(parameters, tool_context)
        else:
            return {"error": f"Unknown intent: {intent}"}
    
    async def _handle_check_connection(self, tool_context):
        """Handle calendar_check_connection intent."""
        for tool in self.tools:
            if tool.name == "calendar_check_connection":
                return tool(tool_context=tool_context)
        return {"error": "calendar_check_connection tool not found"}
    
    async def _handle_authenticate(self, tool_context):
        """Handle calendar_authenticate intent."""
        for tool in self.tools:
            if tool.name == "calendar_authenticate":
                return tool(tool_context=tool_context)
        return {"error": "calendar_authenticate tool not found"}
    
    async def _handle_list_events(self, parameters, tool_context):
        """Handle calendar_list_events intent."""
        for tool in self.tools:
            if tool.name == "calendar_list_events":
                return tool(
                    tool_context=tool_context,
                    time_min=parameters.get("time_min"),
                    time_max=parameters.get("time_max"),
                    max_results=parameters.get("max_results", 10)
                )
        return {"error": "calendar_list_events tool not found"}
    
    async def _handle_get_event(self, parameters, tool_context):
        """Handle calendar_get_event intent."""
        for tool in self.tools:
            if tool.name == "calendar_get_event":
                return tool(
                    tool_context=tool_context,
                    event_id=parameters.get("event_id")
                )
        return {"error": "calendar_get_event tool not found"}
    
    async def _handle_create_event(self, parameters, tool_context):
        """Handle calendar_create_event intent."""
        for tool in self.tools:
            if tool.name == "calendar_create_event":
                return tool(
                    tool_context=tool_context,
                    summary=parameters.get("summary"),
                    start_time=parameters.get("start_time"),
                    end_time=parameters.get("end_time"),
                    description=parameters.get("description"),
                    location=parameters.get("location"),
                    attendees=parameters.get("attendees", [])
                )
        return {"error": "calendar_create_event tool not found"}
    
    async def _handle_update_event(self, parameters, tool_context):
        """Handle calendar_update_event intent."""
        for tool in self.tools:
            if tool.name == "calendar_update_event":
                return tool(
                    tool_context=tool_context,
                    event_id=parameters.get("event_id"),
                    summary=parameters.get("summary"),
                    start_time=parameters.get("start_time"),
                    end_time=parameters.get("end_time"),
                    description=parameters.get("description"),
                    location=parameters.get("location"),
                    attendees=parameters.get("attendees", [])
                )
        return {"error": "calendar_update_event tool not found"}
    
    async def _handle_delete_event(self, parameters, tool_context):
        """Handle calendar_delete_event intent."""
        for tool in self.tools:
            if tool.name == "calendar_delete_event":
                return tool(
                    tool_context=tool_context,
                    event_id=parameters.get("event_id")
                )
        return {"error": "calendar_delete_event tool not found"}

def create_calendar_agent():
    """
    Create a calendar agent with ADK integration.
    
    Returns:
        CalendarAgent: The calendar agent
    """
    logger.info("Creating calendar agent with ADK integration")
    
    # Create model
    if ADK_AVAILABLE:
        model = LiteLlm(
            model=settings.ADK_MODEL,
            temperature=0.7,
            max_tokens=1000
        )
    else:
        model = LiteLlm()
    
    # Create calendar agent
    calendar_agent = CalendarAgent(
        model=model,
        tools=calendar_tools
    )
    
    return calendar_agent

# Helper functions for session management
def _extract_session(event):
    """Extract session from event."""
    if not event:
        return None
    
    # Try to get session from event
    session = event.get("session", {})
    
    # If session is empty, try to get from context
    if not session and "context" in event:
        session = event["context"].get("session", {})
    
    return session

def _extract_app_name_and_user_id(event):
    """Extract app name and user ID from event."""
    if not event:
        return None, None
    
    # Try to get app name and user ID from event
    app_name = event.get("app_name")
    user_id = event.get("user_id")
    
    # If not found, try to get from context
    if not app_name and "context" in event:
        app_name = event["context"].get("app_name")
    
    if not user_id and "context" in event:
        user_id = event["context"].get("user_id")
    
    return app_name, user_id

def _ensure_session(event):
    """Ensure session exists in event."""
    if not event:
        return event
    
    # If session doesn't exist, create it
    if "session" not in event:
        event["session"] = {}
    
    return event

# Test function
def test_calendar_agent_adk_integration():
    """Test calendar agent ADK integration."""
    # Create calendar agent
    calendar_agent = create_calendar_agent()
    
    # Create test event
    test_event = {
        "intent": {
            "name": "calendar_list_events",
            "parameters": {
                "time_min": "2023-01-01T00:00:00Z",
                "time_max": "2023-12-31T23:59:59Z",
                "max_results": 5
            }
        },
        "session": {
            "id": "test_session_id",
            "user_id": "test_user_id",
            "app_name": "test_app"
        }
    }
    
    # Run test event
    asyncio.run(calendar_agent.process(test_event))