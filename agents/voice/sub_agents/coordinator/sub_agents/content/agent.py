"""
Content Agent for Oprina Voice Assistant.

This module handles content processing operations using MCP tools.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../../"))
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

# Import settings
from config.settings import settings

class ProcessableContentAgent:
    """
    Processable Content Agent.
    
    This class handles the processing of content-related events.
    """
    
    def __init__(self, agent: 'ContentAgent'):
        """
        Initialize the ProcessableContentAgent.
        
        Args:
            agent (ContentAgent): The content agent
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
            if intent_name == 'summarize_email_content':
                return await self.agent.summarize_email_content(event)
            elif intent_name == 'summarize_email_list':
                return await self.agent.summarize_email_list(event)
            elif intent_name == 'generate_email_reply':
                return await self.agent.generate_email_reply(event)
            elif intent_name == 'analyze_email_sentiment':
                return await self.agent.analyze_email_sentiment(event)
            elif intent_name == 'extract_action_items':
                return await self.agent.extract_action_items(event)
            elif intent_name == 'optimize_for_voice':
                return await self.agent.optimize_for_voice(event)
            elif intent_name == 'create_voice_summary':
                return await self.agent.create_voice_summary(event)
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

class ContentAgent:
    """
    Content Agent.
    
    This class handles content processing operations.
    """
    
    def __init__(self, tools: Optional[List[Any]] = None):
        """
        Initialize the ContentAgent.
        
        Args:
            tools (Optional[List[Any]]): The tools to use
        """
        self.tools = tools or []
        
        # Create the processable agent
        self.processable = ProcessableContentAgent(self)
        
        # Create the ADK agent if available
        if ADK_AVAILABLE:
            self.adk_agent = LlmAgent(
                name="content_agent",
                description="Content processing agent for Oprina Voice Assistant",
                tools=self.tools
            )
        else:
            self.adk_agent = None
            
    async def summarize_email_content(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize email content.
        
        Args:
            event (Dict[str, Any]): The event to process
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Extract the parameters
            params = event.get('intent', {}).get('parameters', {})
            content = params.get('content', '')
            detail_level = params.get('detail_level', 'moderate')
            
            # Use the MCP tool
            for tool in self.tools:
                if tool.name == 'summarize_email_content':
                    result = await tool.call(content=content, detail_level=detail_level)
                    return {
                        'status': 'success',
                        'result': result
                    }
            
            # No tool found
            return {
                'status': 'error',
                'message': 'No summarize_email_content tool found'
            }
        except Exception as e:
            logger.error(f"Error summarizing email content: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def summarize_email_list(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize email list.
        
        Args:
            event (Dict[str, Any]): The event to process
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Extract the parameters
            params = event.get('intent', {}).get('parameters', {})
            emails = params.get('emails', '')
            max_emails = params.get('max_emails', 5)
            
            # Use the MCP tool
            for tool in self.tools:
                if tool.name == 'summarize_email_list':
                    result = await tool.call(emails=emails, max_emails=max_emails)
                    return {
                        'status': 'success',
                        'result': result
                    }
            
            # No tool found
            return {
                'status': 'error',
                'message': 'No summarize_email_list tool found'
            }
        except Exception as e:
            logger.error(f"Error summarizing email list: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def generate_email_reply(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate email reply.
        
        Args:
            event (Dict[str, Any]): The event to process
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Extract the parameters
            params = event.get('intent', {}).get('parameters', {})
            original_email = params.get('original_email', '')
            reply_intent = params.get('reply_intent', '')
            style = params.get('style', 'professional')
            
            # Use the MCP tool
            for tool in self.tools:
                if tool.name == 'generate_email_reply':
                    result = await tool.call(
                        original_email=original_email,
                        reply_intent=reply_intent,
                        style=style
                    )
                    return {
                        'status': 'success',
                        'result': result
                    }
            
            # No tool found
            return {
                'status': 'error',
                'message': 'No generate_email_reply tool found'
            }
        except Exception as e:
            logger.error(f"Error generating email reply: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def analyze_email_sentiment(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email sentiment.
        
        Args:
            event (Dict[str, Any]): The event to process
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Extract the parameters
            params = event.get('intent', {}).get('parameters', {})
            content = params.get('content', '')
            
            # Use the MCP tool
            for tool in self.tools:
                if tool.name == 'analyze_email_sentiment':
                    result = await tool.call(content=content)
                    return {
                        'status': 'success',
                        'result': result
                    }
            
            # No tool found
            return {
                'status': 'error',
                'message': 'No analyze_email_sentiment tool found'
            }
        except Exception as e:
            logger.error(f"Error analyzing email sentiment: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def extract_action_items(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract action items.
        
        Args:
            event (Dict[str, Any]): The event to process
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Extract the parameters
            params = event.get('intent', {}).get('parameters', {})
            content = params.get('content', '')
            
            # Use the MCP tool
            for tool in self.tools:
                if tool.name == 'extract_action_items':
                    result = await tool.call(content=content)
                    return {
                        'status': 'success',
                        'result': result
                    }
            
            # No tool found
            return {
                'status': 'error',
                'message': 'No extract_action_items tool found'
            }
        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def optimize_for_voice(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize for voice.
        
        Args:
            event (Dict[str, Any]): The event to process
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Extract the parameters
            params = event.get('intent', {}).get('parameters', {})
            content = params.get('content', '')
            max_length = params.get('max_length', 200)
            
            # Use the MCP tool
            for tool in self.tools:
                if tool.name == 'optimize_for_voice':
                    result = await tool.call(content=content, max_length=max_length)
                    return {
                        'status': 'success',
                        'result': result
                    }
            
            # No tool found
            return {
                'status': 'error',
                'message': 'No optimize_for_voice tool found'
            }
        except Exception as e:
            logger.error(f"Error optimizing for voice: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def create_voice_summary(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create voice summary.
        
        Args:
            event (Dict[str, Any]): The event to process
            
        Returns:
            Dict[str, Any]: The processed event
        """
        try:
            # Extract the parameters
            params = event.get('intent', {}).get('parameters', {})
            content = params.get('content', '')
            
            # Use the MCP tool
            for tool in self.tools:
                if tool.name == 'create_voice_summary':
                    result = await tool.call(content=content)
                    return {
                        'status': 'success',
                        'result': result
                    }
            
            # No tool found
            return {
                'status': 'error',
                'message': 'No create_voice_summary tool found'
            }
        except Exception as e:
            logger.error(f"Error creating voice summary: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

async def create_content_agent_with_mcp():
    """
    Create the Content Agent with proper ADK MCP integration.
    
    This function demonstrates the correct ADK MCP pattern using StdioServerParameters
    to automatically discover and load MCP tools.
    
    Returns:
        ContentAgent: Configured content agent with MCP tools
    """
    print("--- Creating Content Agent with ADK MCP Integration ---")
    
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
        
        # Filter for content tools
        content_tools = [tool for tool in mcp_toolset.tools if tool.name in [
            'summarize_email_content',
            'summarize_email_list',
            'generate_email_reply',
            'analyze_email_sentiment',
            'extract_action_items',
            'optimize_for_voice',
            'create_voice_summary'
        ]]
        
        # Create the Content Agent with MCP tools
        agent_instance = ContentAgent(tools=content_tools)
        
        print(f"Created Content Agent with {len(content_tools)} MCP tools")
        return agent_instance
        
    except ImportError:
        print("ADK MCP tools not available, falling back to direct tools")
        return ContentAgent()
    except Exception as e:
        print(f"Error creating Content Agent with MCP: {e}")
        return ContentAgent()

# Update the main function to use the MCP agent
async def main():
    """Main function to run the content agent."""
    # Create the content agent with MCP integration
    content_agent = await create_content_agent_with_mcp()
    
    # Run the agent
    if content_agent.adk_agent:
        await content_agent.adk_agent.run()
    else:
        print("ADK agent not available")

if __name__ == "__main__":
    asyncio.run(main())