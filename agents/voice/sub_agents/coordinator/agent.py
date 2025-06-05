"""
Coordinator Agent for Oprina Voice Assistant.

This module handles coordination between sub-agents using MCP tools.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import ADK components with fallback
try:
    from adk.agents import LlmAgent, Runner
    from adk.llms import LiteLlm
    from adk.tools import FunctionTool
    ADK_AVAILABLE = True
except ImportError:
    logger.warning("ADK not available, using fallback implementations")
    ADK_AVAILABLE = False
    
    # Fallback implementations
    class LlmAgent:
        def __init__(self, *args, **kwargs):
            pass
            
    class Runner:
        def __init__(self, *args, **kwargs):
            pass
            
    class LiteLlm:
        def __init__(self, *args, **kwargs):
            pass
            
    class FunctionTool:
        def __init__(self, *args, **kwargs):
            pass

# Import the MCP integration
from services.mcp import load_mcp_toolset, MCPConnectionManager

# Import the sub-agents
from .sub_agents.email.agent import create_email_agent
from .sub_agents.calendar.agent import create_calendar_agent
from .sub_agents.content.agent import create_content_agent

class ProcessableCoordinatorAgent:
    """
    Processable Coordinator Agent.
    
    This class handles the processing of coordination events.
    """
    
    def __init__(self, agent: 'CoordinatorAgent'):
        """
        Initialize the ProcessableCoordinatorAgent.
        
        Args:
            agent (CoordinatorAgent): The coordinator agent
        """
        self.agent = agent
        
    async def process(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an event.
        
        Args:
            event (Dict[str, Any]): The event to process
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Extract the intent
            intent = event.get('intent', {})
            intent_name = intent.get('name', '')
            
            # Route the event based on the intent
            if intent_name.startswith('email_'):
                return await self.agent.route_to_email_agent(event)
            elif intent_name.startswith('calendar_'):
                return await self.agent.route_to_calendar_agent(event)
            elif intent_name.startswith('content_'):
                return await self.agent.route_to_content_agent(event)
            else:
                logger.warning(f"Unknown intent: {intent_name}")
                return {
                    'status': 'error',
                    'message': f"Unknown intent: {intent_name}"
                }
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

class CoordinatorAgent:
    """
    Coordinator Agent.
    
    This class handles coordination between sub-agents.
    """
    
    def __init__(self, tools: Optional[List[Any]] = None):
        """
        Initialize the CoordinatorAgent.
        
        Args:
            tools (Optional[List[Any]]): The tools to use
        """
        self.tools = tools or []
        
        # Create the processable agent
        self.processable = ProcessableCoordinatorAgent(self)
        
        # Create the ADK agent if available
        if ADK_AVAILABLE:
            self.adk_agent = LlmAgent(
                name="coordinator_agent",
                description="Coordinator agent for Oprina Voice Assistant",
                tools=self.tools
            )
        else:
            self.adk_agent = None
            
        # Create the sub-agents
        self.email_agent = create_email_agent()
        self.calendar_agent = create_calendar_agent()
        self.content_agent = create_content_agent()
        
    async def route_to_email_agent(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an event to the email agent.
        
        Args:
            event (Dict[str, Any]): The event to route
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Process the event with the email agent
            return await self.email_agent.processable.process(event)
        except Exception as e:
            logger.error(f"Error routing to email agent: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def route_to_calendar_agent(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an event to the calendar agent.
        
        Args:
            event (Dict[str, Any]): The event to route
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Process the event with the calendar agent
            return await self.calendar_agent.processable.process(event)
        except Exception as e:
            logger.error(f"Error routing to calendar agent: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def route_to_content_agent(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an event to the content agent.
        
        Args:
            event (Dict[str, Any]): The event to route
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Process the event with the content agent
            return await self.content_agent.processable.process(event)
        except Exception as e:
            logger.error(f"Error routing to content agent: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

def create_coordinator_agent() -> CoordinatorAgent:
    """
    Create a coordinator agent.
    
    Returns:
        CoordinatorAgent: The coordinator agent
    """
    # Get the MCP tools
    mcp_toolset = load_mcp_toolset_sync()
    tools = mcp_toolset.tools if mcp_toolset else []
    
    # Create the coordinator agent
    coordinator_agent = CoordinatorAgent(tools=tools)
    
    return coordinator_agent

# Test function
def test_coordinator_agent_mcp_integration():
    """
    Test the coordinator agent MCP integration.
    """
    # Create the coordinator agent
    coordinator_agent = create_coordinator_agent()
    
    # Create a test event
    test_event = {
        'intent': {
            'name': 'email_list_messages',
            'parameters': {
                'max_results': 5
            }
        }
    }
    
    # Process the test event
    result = asyncio.run(coordinator_agent.processable.process(test_event))
    
    # Print the result
    print(f"Test result: {result}")
    
    return result

if __name__ == "__main__":
    test_coordinator_agent_mcp_integration()