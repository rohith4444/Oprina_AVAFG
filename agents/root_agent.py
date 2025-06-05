"""
Root Agent for ADK Integration

This module provides a root agent that handles high-level operations using direct API tools
instead of the MCP client.
"""

import os
import sys
import asyncio
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import project modules
from config.settings import settings
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("root_agent", console_output=True)

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

# Import voice agent
from agents.voice.agent import create_voice_agent

# Import direct tools
from agents.common.gmail_tools import gmail_tools
from agents.common.calendar_tools import calendar_tools
from agents.common.content_tools import content_tools

class ProcessableRootAgent:
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

class RootAgent:
    """
    Root agent that handles high-level operations.
    """
    
    def __init__(self, model=None, tools=None):
        self.model = model
        self.tools = tools or []
        
        # Create voice agent
        self.voice_agent = create_voice_agent()
        
    async def process(self, event, tool_context=None):
        # Extract intent from event
        intent = event.get("intent", {}).get("name", "")
        
        # Process intent
        if intent.startswith("voice_"):
            # Route to voice agent
            logger.info(f"Routing to voice agent: {intent}")
            return await self.voice_agent.process(event)
        else:
            # Handle root-level intents
            if intent == "check_connection":
                return await self._handle_check_connection(tool_context)
            elif intent == "authenticate":
                return await self._handle_authenticate(tool_context)
            else:
                # Default to voice agent
                logger.info(f"No specific intent match, defaulting to voice agent: {intent}")
                return await self.voice_agent.process(event)
    
    async def _handle_check_connection(self, tool_context):
        """Handle check_connection intent."""
        # Check Gmail connection
        gmail_connected = False
        for tool in self.tools:
            if tool.name == "gmail_check_connection":
                result = tool(tool_context=tool_context)
                gmail_connected = "connected" in result.get("status", "").lower()
                break
        
        # Check Calendar connection
        calendar_connected = False
        for tool in self.tools:
            if tool.name == "calendar_check_connection":
                result = tool(tool_context=tool_context)
                calendar_connected = "connected" in result.get("status", "").lower()
                break
        
        return {
            "gmail_connected": gmail_connected,
            "calendar_connected": calendar_connected,
            "status": "Connected" if gmail_connected or calendar_connected else "Not connected"
        }
    
    async def _handle_authenticate(self, tool_context):
        """Handle authenticate intent."""
        # Authenticate Gmail
        gmail_authenticated = False
        for tool in self.tools:
            if tool.name == "gmail_authenticate":
                result = tool(tool_context=tool_context)
                gmail_authenticated = "authenticated" in result.get("status", "").lower()
                break
        
        # Authenticate Calendar
        calendar_authenticated = False
        for tool in self.tools:
            if tool.name == "calendar_authenticate":
                result = tool(tool_context=tool_context)
                calendar_authenticated = "authenticated" in result.get("status", "").lower()
                break
        
        return {
            "gmail_authenticated": gmail_authenticated,
            "calendar_authenticated": calendar_authenticated,
            "status": "Authenticated" if gmail_authenticated or calendar_authenticated else "Not authenticated"
        }

def create_root_agent():
    """
    Create a root agent with ADK integration.
    
    Returns:
        RootAgent: The root agent
    """
    logger.info("Creating root agent with ADK integration")
    
    # Create model
    if ADK_AVAILABLE:
        model = LiteLlm(
            model=settings.ADK_MODEL,
            temperature=0.7,
            max_tokens=1000
        )
    else:
        model = LiteLlm()
    
    # Combine all tools
    all_tools = gmail_tools + calendar_tools + content_tools
    
    # Create root agent
    root_agent = RootAgent(
        model=model,
        tools=all_tools
    )
    
    return root_agent

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
def test_root_agent_adk_integration():
    """Test root agent ADK integration."""
    # Create root agent
    root_agent = create_root_agent()
    
    # Create test event
    test_event = {
        "intent": {
            "name": "check_connection",
            "parameters": {}
        },
        "session": {
            "id": "test_session_id",
            "user_id": "test_user_id",
            "app_name": "test_app"
        }
    }
    
    # Run test event
    asyncio.run(root_agent.process(test_event))