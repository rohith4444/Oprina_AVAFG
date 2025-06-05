"""
Coordinator Agent Package - Complete ADK Implementation

This package contains the Coordinator Agent responsible for:
- Multi-agent workflow orchestration using ADK auto-delegation
- Complex task coordination between Email, Content, and Calendar agents
- Session state management and result coordination
- Cross-session memory and workflow optimization

The coordinator leverages ADK's automatic delegation system where the LLM
intelligently routes tasks to the most appropriate sub-agent based on
descriptions and context.
"""

import os
import sys
import asyncio
from typing import Optional
import uuid
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

# --- ADK Imports with Fallback ---
try:
    from google.adk.agents import LlmAgent
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.tools import load_memory
    from google.adk.runners import Runner
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    ADK_IMPORT_ERROR = "ADK not available, running in fallback mode"
    
    # Fallback implementations
    class LlmAgent:
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name', 'llm_agent')
            self.description = kwargs.get('description', '')
            self.model = kwargs.get('model', None)
            self.instruction = kwargs.get('instruction', '')
            self.tools = kwargs.get('tools', [])
            self.sub_agents = kwargs.get('sub_agents', [])
            self.output_key = kwargs.get('output_key', None)
            
        async def process(self, event, app_name=None, session_service=None, memory_service=None, tool_context=None):
            return {"content": f"Fallback LlmAgent received event: {event}"}
            
    class LiteLlm:
        def __init__(self, model=None, api_key=None):
            self.model = model
            self.api_key = api_key
            
        async def generate(self, prompt):
            return {"text": f"Fallback LiteLlm response for: {prompt}"}
            
    def load_memory(*args, **kwargs):
        return {"content": "Fallback load_memory tool executed"}
        
    class Runner:
        def __init__(self, agent, app_name, session_service, memory_service):
            self.agent = agent
            self.app_name = app_name
            self.session_service = session_service
            self.memory_service = memory_service
            
        async def run(self, event):
            return {"content": f"Fallback Runner processed event: {event.get('content', '')}"}

# Import project modules
from config.settings import settings

# Import sub-agents
from .agent import create_coordinator_agent

# Import shared constants for documentation
from agents.common.session_keys import (
    USER_GMAIL_CONNECTED, USER_EMAIL, USER_NAME, USER_PREFERENCES,
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_UNREAD_COUNT, EMAIL_LAST_SENT,
    USER_CALENDAR_CONNECTED, CONTENT_LAST_SUMMARY
)

from agents.common.utils import validate_tool_context, log_tool_execution, update_agent_activity, format_timestamp
from memory.adk_memory_manager import get_adk_memory_manager
from agents.common.tool_context import ToolContext

# --- Additional ADK Imports with Fallback ---
try:
    from google.adk.memory.adk_memory_manager import get_memory_manager
    ADK_MEMORY_AVAILABLE = True
except ImportError:
    ADK_MEMORY_AVAILABLE = False
    def get_memory_manager(*args, **kwargs):
        return {"content": "Fallback memory manager executed"}

# Create the coordinator agent
coordinator_agent = create_coordinator_agent()

# Export the agent and creation function
__all__ = ['coordinator_agent', 'create_coordinator_agent']

# Function to get the coordinator agent
def get_coordinator_agent():
    return coordinator_agent

# Import the main coordinator agent
from .agent import coordinator_agent, create_coordinator_agent, get_coordinator_agent

# Import coordination tools for direct access if needed
from .coordinator_tools import (
    analyze_coordination_context,
    get_workflow_status,
    coordinate_agent_results,
    COORDINATION_TOOLS
)

# Import sub-agents for reference (though ADK handles delegation automatically)
from .sub_agents.email import create_email_agent
from .sub_agents.content import create_content_agent
from .sub_agents.calendar import create_calendar_agent

# Import workflow type constants from common
from agents.common.session_keys import (
    WORKFLOW_EMAIL_ONLY, WORKFLOW_CALENDAR_ONLY, WORKFLOW_CONTENT_ONLY,
    WORKFLOW_EMAIL_CONTENT, WORKFLOW_CALENDAR_CONTENT,
    WORKFLOW_EMAIL_CALENDAR, WORKFLOW_ALL_AGENTS
)

# Export main components
__all__ = [
    # Main coordinator agent
    "get_coordinator_agent", "create_coordinator_agent",
    
    # Coordination tools (for direct use if needed)
    "analyze_coordination_context", "get_workflow_status", 
    "coordinate_agent_results", "COORDINATION_TOOLS",
    
    # Sub-agents (for reference, ADK handles delegation)
    "email_agent", "content_agent", "calendar_agent",
    
    # Workflow type constants
    "WORKFLOW_EMAIL_ONLY", "WORKFLOW_CALENDAR_ONLY", "WORKFLOW_CONTENT_ONLY",
    "WORKFLOW_EMAIL_CONTENT", "WORKFLOW_CALENDAR_CONTENT",
    "WORKFLOW_EMAIL_CALENDAR", "WORKFLOW_ALL_AGENTS"
]

# Package metadata
__version__ = "2.0.0"
__description__ = "ADK-native coordinator agent with automatic delegation"

def get_package_info():
    """Get package information for debugging and monitoring."""
    return {
        "package": "coordinator",
        "version": __version__,
        "description": __description__,
        "main_agent": coordinator_agent.name if coordinator_agent else "Not loaded",
        "sub_agents": [
            "email_agent",
            "content_agent", 
            "calendar_agent"
        ],
        "coordination_tools": len(COORDINATION_TOOLS),
        "workflow_types": [
            WORKFLOW_EMAIL_ONLY, WORKFLOW_CALENDAR_ONLY, WORKFLOW_CONTENT_ONLY,
            WORKFLOW_EMAIL_CONTENT, WORKFLOW_CALENDAR_CONTENT, 
            WORKFLOW_EMAIL_CALENDAR, WORKFLOW_ALL_AGENTS
        ],
        "adk_features": [
            "automatic_delegation",
            "session_state_management", 
            "cross_session_memory",
            "tool_context_injection",
            "output_key_persistence"
        ]
    }

# Add package info to exports
__all__.append("get_package_info")