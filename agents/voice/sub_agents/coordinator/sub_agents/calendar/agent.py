"""
Calendar Agent for ADK Integration

This module provides a calendar agent that handles Calendar operations using MCP tools.
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

async def create_calendar_agent_with_mcp():
    """
    Create the Calendar Agent with proper ADK MCP integration.
    
    This function demonstrates the correct ADK MCP pattern using StdioServerParameters
    to automatically discover and load MCP tools.
    
    Returns:
        CalendarAgent: Configured calendar agent with MCP tools
    """
    print("--- Creating Calendar Agent with ADK MCP Integration ---")
    
    try:
        # Import ADK MCP tools
        from google.adk.tools.mcp import MCPToolset
        from google.adk.tools.mcp.server_parameters import StdioServerParameters
        
        # ADK automatically discovers and loads MCP tools
        mcp_toolset = await MCPToolset.from_server(
            StdioServerParameters(
                command="python",
                args=["mcp_server/run_server.py"],
                env=os.environ.copy()
            )
        )
        
        # Filter for calendar tools
        calendar_tools = [tool for tool in mcp_toolset.tools if tool.name.startswith("calendar_")]
        
        # Create the Calendar Agent with MCP tools
        agent_instance = CalendarAgent(tools=calendar_tools)
        
        print(f"Created Calendar Agent with {len(calendar_tools)} MCP tools")
        return agent_instance
        
    except ImportError:
        print("ADK MCP tools not available, falling back to direct tools")
        return CalendarAgent()
    except Exception as e:
        print(f"Error creating Calendar Agent with MCP: {e}")
        return CalendarAgent()

def _extract_session(event):
    """Extract session from event."""
    return event.get("session", {})

def _extract_app_name_and_user_id(event):
    """Extract app name and user ID from event."""
    session = _extract_session(event)
    app_name = session.get("app_name", "default")
    user_id = session.get("user_id", "default")
    return app_name, user_id

def _ensure_session(event):
    """Ensure session exists in event."""
    if "session" not in event:
        event["session"] = {}
    return event

# Update the main function to use the MCP agent
async def main():
    """Main function to run the calendar agent."""
    # Create the calendar agent with MCP integration
    calendar_agent = await create_calendar_agent_with_mcp()
    
    # Create a processable agent
    processable_agent = ProcessableCalendarAgent(calendar_agent)
    
    # Run the agent
    if ADK_AVAILABLE:
        # Create an ADK agent
        model = LiteLlm(
            model=settings.CALENDAR_MODEL,
            api_key=settings.GOOGLE_API_KEY
        )
        
        adk_agent = LlmAgent(
            name="calendar_agent",
            description="Calendar operations agent",
            model=model,
            tools=calendar_agent.tools
        )
        
        # Run the ADK agent
        await adk_agent.run()
    else:
        print("ADK not available, running in fallback mode")

if __name__ == "__main__":
    asyncio.run(main())