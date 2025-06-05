"""Add commentMore actions
Email Agent for Oprina - Complete ADK Integration

This agent handles all Gmail operations using direct API tools.
Simplified to return a single LlmAgent with proper ADK integration.
"""

import os
import sys
import asyncio
from typing import Optional
import uuid
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
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

# Import direct Gmail and Calendar tools
from agents.common.gmail_tools import gmail_tools
from agents.common.calendar_tools import calendar_tools

# Import shared constants for documentation
from agents.common.session_keys import (
    USER_GMAIL_CONNECTED, USER_EMAIL, USER_NAME, USER_PREFERENCES,
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_UNREAD_COUNT, EMAIL_LAST_SENT,
    USER_CALENDAR_CONNECTED
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

class ProcessableEmailAgent(LlmAgent):
    async def process(self, event, app_name=None, session_service=None, memory_service=None, tool_context=None):
        """
        Process an event with proper session state handling and tool_context forwarding.
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
        # Forward tool_context if present
        if tool_context is not None:
            event.tool_context = tool_context
        return await runner.run(event)

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

    # Create the Email Agent with proper ADK patterns
    agent_instance = ProcessableEmailAgent(
        name="email_agent",
        description="Handles Gmail operations with direct API access and session state integration",
        model=model,
        instruction="""
Handles Gmail operations: connection, email management, sending, organizing using direct Gmail API access
        """,
        tools=[
            load_memory,
            # Use direct Gmail and Calendar tools
            *gmail_tools,
            *calendar_tools
        ],
        output_key="email_result"
    )
    return agent_instance

async def create_email_agent_with_mcp():
    """
    Create the Email Agent with proper ADK MCP integration.
    
    This function demonstrates the correct ADK MCP pattern using StdioServerParameters
    to automatically discover and load MCP tools.
    
    Returns:
        LlmAgent: Configured email agent with MCP tools
    """
    print("--- Creating Email Agent with ADK MCP Integration ---")
    
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
        
        # Define model for the agent
        model = LiteLlm(
            model=settings.EMAIL_MODEL,
            api_key=settings.GOOGLE_API_KEY
        )
        
        # Create the Email Agent with MCP tools
        agent_instance = ProcessableEmailAgent(
            name="email_agent",
            description="Handles Gmail operations with MCP integration",
            model=model,
            instruction="""
Handles Gmail operations: connection, email management, sending, organizing using MCP tools
            """,
            tools=[
                load_memory,
                *mcp_toolset.tools  # All MCP tools auto-discovered
            ],
            output_key="email_result"
        )
        
        print(f"Created Email Agent with {len(mcp_toolset.tools)} MCP tools")
        return agent_instance
        
    except ImportError:
        print("ADK MCP tools not available, falling back to direct tools")
        return create_email_agent()
    except Exception as e:
        print(f"Error creating Email Agent with MCP: {e}")
        return create_email_agent()

def _extract_session(tool_context):
    """
    Extract session from tool_context or create a new one.
    
    Args:
        tool_context: The tool context containing session information
        
    Returns:
        Session: The extracted or created session
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.error(f"AGENT DEBUG: _extract_session called with tool_context type={type(tool_context)}, value={tool_context}")
    
    # First try to get session from tool_context
    if hasattr(tool_context, 'session') and tool_context.session:
        logger.error(f"AGENT DEBUG: Found session in tool_context: {tool_context.session.id}")
        return tool_context.session
    
    # If not in tool_context, try to get from memory manager
    logger.error("AGENT DEBUG: No session found in tool_context, trying memory manager")
    
    try:
        # Try to get memory manager from ADK
        from google.adk.memory.adk_memory_manager import get_memory_manager
        memory_manager = get_memory_manager()
        
        # Create a new session
        session_id = str(uuid.uuid4())
        logger.error(f"AGENT DEBUG: Creating new session with ID: {session_id}")
        
        # Create a simple session object
        session = SimpleSession(session_id)
        
        # Store in memory manager
        memory_manager.set_session(session)
        
        return session
        
    except Exception as e:
        logger.error(f"AGENT DEBUG: Error creating session: {e}")
        # Create a simple session as fallback
        return SimpleSession(str(uuid.uuid4()))

def _extract_app_name_and_user_id(tool_context, session):
    """
    Extract app_name and user_id from tool_context or session.
    
    Args:
        tool_context: The tool context containing session information
        session: The session object
        
    Returns:
        Tuple[str, str]: App name and user ID
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Default values
    app_name = "oprina"
    user_id = "default_user"
    
    # Try to get from tool_context
    if hasattr(tool_context, 'app_name') and tool_context.app_name:
        app_name = tool_context.app_name
    
    if hasattr(tool_context, 'user_id') and tool_context.user_id:
        user_id = tool_context.user_id
    
    # Try to get from session
    if session:
        if session.get('app_name'):
            app_name = session.get('app_name')
        
        if session.get('user_id'):
            user_id = session.get('user_id')
    
    logger.error(f"AGENT DEBUG: Extracted app_name={app_name}, user_id={user_id}")
    
    return app_name, user_id

def _get_session_state(session):
    """
    Get session state.
    
    Args:
        session: The session object
        
    Returns:
        dict: Session state
    """
    if hasattr(session, 'get_state'):
        return session.get_state()
    elif hasattr(session, 'state'):
        return session.state
    else:
        return {}

def _update_tool_context_with_session(tool_context, session):
    """
    Update tool_context with session information.
    
    Args:
        tool_context: The tool context
        session: The session object
        
    Returns:
        ToolContext: Updated tool context
    """
    if not tool_context:
        tool_context = ToolContext()
    
    tool_context.session = session
    return tool_context

async def _ensure_session(tool_context, session):
    """
    Ensure session is valid and update tool_context.
    
    Args:
        tool_context: The tool context
        session: The session object
        
    Returns:
        Tuple[ToolContext, Session]: Updated tool context and session
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # If no session, create one
    if not session:
        logger.error("AGENT DEBUG: No session provided, creating new one")
        session = _extract_session(tool_context)
    
    # Update tool_context with session
    tool_context = _update_tool_context_with_session(tool_context, session)
    
    return tool_context, session

def create_email_runner():
    """
    Create a runner for the email agent.
    
    Returns:
        Runner: Configured runner
    """
    # Create agent
    agent = create_email_agent()
    
    # Create services
    from google.adk.sessions import InMemorySessionService
    from google.adk.memory import InMemoryMemoryService
    
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    
    # Create runner
    runner = Runner(
        agent=agent,
        app_name="oprina",
        session_service=session_service,
        memory_service=memory_service
    )
    
    return runner

class SimpleSession:
    """Simple session implementation for testing."""
    
    def __init__(self, session_id=None):
        self.id = session_id or str(uuid.uuid4())
        self._data = {}
        self._state = {}
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def set(self, key, value):
        self._data[key] = value
    
    def get_state(self, key=None, default=None):
        if key:
            return self._state.get(key, default)
        return self._state
    
    def set_state(self, key, value):
        self._state[key] = value
    
    def update_state(self, state_dict):
        self._state.update(state_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'data': self._data,
            'state': self._state
        }

def test_email_agent_adk_integration():
    """Test the email agent ADK integration."""
    
    async def run_test():
        # Create runner
        runner = create_email_runner()
        
        # Run test event
        result = await runner.run({"content": "Test email agent"})
        
        print(f"Test result: {result}")
    
    # Run test
    asyncio.run(run_test())

# Update the main function to use the MCP agent
async def main():
    """Main function to run the email agent."""
    # Create the email agent with MCP integration
    email_agent = await create_email_agent_with_mcp()
    
    # Run the agent
    await email_agent.run()

if __name__ == "__main__":
    asyncio.run(main())