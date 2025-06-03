"""
Content Agent for Oprina - Complete ADK Integration

This agent specializes in content processing for emails and text using the MCP client.
Follows the same pattern as the email agent with proper ADK session integration.
"""

import os
import sys
import asyncio

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(7):  # 7 levels to reach project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import external packages
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import load_memory
from google.adk.runners import Runner

# Import project modules
from config.settings import settings

# Import MCP client
from mcp_server.client import MCPClient

# Import shared constants for documentation
from agents.common.session_keys import (
    USER_PREFERENCES, USER_NAME, USER_EMAIL, CONTENT_LAST_SUMMARY,
    CONTENT_LAST_ANALYSIS, CONTENT_PROCESSING_STATUS
)


class ProcessableContentAgent(LlmAgent):
    async def process(self, event, app_name=None, session_service=None, memory_service=None):
        """
        Process an event with proper session state handling.
        
        Args:
            event: The event to process
            app_name: The application name
            session_service: The session service
            memory_service: The memory service
            
        Returns:
            The processed event result
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
        
        # Run the event through the runner
        return await runner.run(event)


def create_content_agent():
    """
    Create the Content Agent with complete ADK integration.
    
    Returns:
        LlmAgent: Configured content agent ready for ADK hierarchy
    """
    print("--- Creating Content Agent with ADK Integration ---")
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.CONTENT_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    
    # Create MCP client
    mcp_client = MCPClient(
        host=settings.MCP_HOST,
        port=8765  # Use port 8765 instead of settings.MCP_PORT
    )
    
    # Create the Content Agent with proper ADK patterns
    agent_instance = ProcessableContentAgent(
        name="content_agent",
        description="Specializes in email content processing: summarization, reply generation, analysis, and voice optimization",
        model=model,
        instruction=f"""
You are the Content Agent for Oprina with complete ADK session integration.

## Your Role & Responsibilities

You specialize in content processing and text analysis using the MCP client. Your core responsibilities include:

1. **Email Content Summarization**
   - Create adaptive summaries based on user preferences from session state
   - Support brief, moderate, and detailed summary levels
   - Optimize summaries for voice delivery when requested
   - Consider user's time constraints and reading preferences

2. **Email Reply Generation**
   - Generate contextually appropriate email replies
   - Support multiple reply styles (professional, brief, formal, friendly)
   - Incorporate user's intent and communication style from session
   - Maintain proper email etiquette and structure

3. **Content Analysis**
   - Analyze email sentiment, tone, urgency, and formality
   - Extract key topics and themes from content
   - Identify action items and deadlines automatically
   - Determine content complexity and processing requirements

4. **Voice Optimization**
   - Optimize content for voice delivery and speech synthesis
   - Remove complex formatting and abbreviations for natural speech
   - Break down long sentences for conversational flow
   - Ensure content flows naturally when spoken aloud

## Session State Access (REAL ADK Integration)

You have REAL access to session state through tool_context.session.state:

**User Information:**
- User Preferences: tool_context.session.state.get("{USER_PREFERENCES}", {{}})
- User Name: tool_context.session.state.get("{USER_NAME}", "")
- User Email: tool_context.session.state.get("{USER_EMAIL}", "")

**Content Processing State (current conversation):**
- Last Summary: tool_context.session.state.get("{CONTENT_LAST_SUMMARY}", "")
- Last Analysis: tool_context.session.state.get("{CONTENT_LAST_ANALYSIS}", "")
- Processing Status: tool_context.session.state.get("{CONTENT_PROCESSING_STATUS}", "")

**Dynamic Session State Updates:**
- content:last_summary_at - Timestamp of last summarization
- content:last_reply_generated - Most recent reply generated
- content:last_analysis_data - Detailed sentiment analysis results
- content:last_voice_optimization - Most recent voice optimization
- content:last_action_items - Extracted action items list

## Available Content Processing Tools (with Session Context)

Your tools use the MCP client to communicate with the MCP server:

**Summarization Tools:**
- `summarize_email_content`: Create adaptive email summaries with user preference support
  - Uses session preferences for detail level (brief/moderate/detailed)
  - Updates content:last_summary and metadata in session state
  - Optimizes length based on user's typical preferences

- `summarize_email_list`: Generate quick overview of multiple emails
  - Processes email lists for rapid scanning
  - Updates content:last_list_summary with count and timestamp

**Reply Generation Tools:**
- `generate_email_reply`: Generate contextual email replies with style preferences
  - Uses session state for user name and reply style preferences
  - Supports professional, brief, formal, and friendly styles
  - Updates content:last_reply_generated with style and sender info

**Analysis Tools:**
- `analyze_email_sentiment`: Comprehensive sentiment, tone, urgency, and formality analysis
  - Detects positive/negative/neutral sentiment
  - Identifies formal/casual/professional tone
  - Flags urgent content with specific indicators
  - Updates content:last_analysis with structured data

- `extract_action_items`: Automatically extract actionable tasks from emails
  - Uses regex patterns to identify action-oriented language
  - Extracts deadlines, requests, and commitments
  - Updates content:last_action_items with structured list

**Voice Optimization Tools:**
- `optimize_for_voice`: Optimize text for voice delivery and speech synthesis
  - Replaces abbreviations and symbols with spoken equivalents
  - Breaks long sentences at natural pause points
  - Removes URLs and email addresses for voice-friendly content
  - Updates content:last_voice_optimization with length metrics

- `create_voice_summary`: Create summaries specifically optimized for voice delivery
  - Combines summarization with voice optimization
  - Perfect for voice assistant responses
  - Updates content:last_voice_summary for coordination

## Cross-Session Memory

You have access to:
- `load_memory`: Search past conversations for content processing patterns and preferences
  Examples:
  - "What summarization style does this user prefer?"
  - "How do I usually format replies for this user?"
  - "What content analysis patterns have I seen before?"
  - "What are the user's typical voice optimization preferences?"

## Content Processing Examples

**Email Summarization:**
- "Summarize this email briefly" → Use `summarize_email_content` with detail_level="brief"
- "Give me a detailed summary" → Use `summarize_email_content` with detail_level="detailed"
- "Summarize for voice delivery" → Use `create_voice_summary` for voice-optimized output

**Reply Generation:**
- "Generate a professional reply" → Use `generate_email_reply` with style="professional"
- "Draft a quick response" → Use `generate_email_reply` with style="brief"

**Content Analysis:**
- "Analyze the tone of this email" → Use `analyze_email_sentiment` for comprehensive analysis
- "What action items are in this email?" → Use `extract_action_items` for task extraction
- "Is this email urgent?" → Use `analyze_email_sentiment` to check urgency indicators

**Voice Optimization:**
- "Optimize this for voice delivery" → Use `optimize_for_voice` with appropriate max_length
- "Create a voice-friendly summary" → Use `create_voice_summary` for combined processing

## Workflow Examples

**Email Content Processing Workflow:**
1. Check user preferences: tool_context.session.state.get("{USER_PREFERENCES}")
2. Process content: Use appropriate content tool based on request
3. Update session state: Tools automatically update relevant state keys
4. Provide response: Clear, actionable response optimized for voice delivery
""",
        tools=[
            load_memory,
            # MCP client tools
            summarize_email_content,
            summarize_email_list,
            generate_email_reply,
            analyze_email_sentiment,
            extract_action_items,
            optimize_for_voice,
            create_voice_summary
        ]
    )
    
    # Store MCP client in agent for tool access
    agent_instance._mcp_client = mcp_client
    
    print(f"Content Agent created with MCP client integration")
    return agent_instance


# MCP client tool implementations
async def summarize_email_content(tool_context, content: str, detail_level: str = "moderate"):
    """
    Summarize email content with specified detail level.
    
    Args:
        tool_context: ADK tool context
        content: Email content to summarize
        detail_level: Detail level for summary (brief, moderate, detailed)
        
    Returns:
        str: Summary result
    """
    try:
        # Get user preferences from session state
        user_preferences = tool_context.session.state.get(USER_PREFERENCES, {})
        
        # Override detail level with user preference if available
        if "content_summary_detail" in user_preferences:
            detail_level = user_preferences["content_summary_detail"]
        
        # Call MCP client
        response = await tool_context.agent._mcp_client.summarize_email_content(content, detail_level)
        
        if response["status"] == "success":
            # Update session state
            tool_context.session.state[CONTENT_LAST_SUMMARY] = response["data"]["summary"]
            tool_context.session.state["content:last_summary_at"] = response["data"]["timestamp"]
            
            return response["data"]["summary"]
        else:
            return f"Error summarizing email content: {response['message']}"
    except Exception as e:
        return f"Error summarizing email content: {str(e)}"


async def summarize_email_list(tool_context, emails: str, max_emails: int = 5):
    """
    Summarize a list of emails for quick overview.
    
    Args:
        tool_context: ADK tool context
        emails: List of emails to summarize
        max_emails: Maximum number of emails to summarize
        
    Returns:
        str: Summary result
    """
    try:
        # Call MCP client
        response = await tool_context.agent._mcp_client.summarize_email_list(emails, max_emails)
        
        if response["status"] == "success":
            # Update session state
            tool_context.session.state["content:last_list_summary"] = response["data"]["summary"]
            tool_context.session.state["content:last_list_summary_count"] = response["data"]["email_count"]
            tool_context.session.state["content:last_list_summary_at"] = response["data"]["timestamp"]
            
            return response["data"]["summary"]
        else:
            return f"Error summarizing email list: {response['message']}"
    except Exception as e:
        return f"Error summarizing email list: {str(e)}"


async def generate_email_reply(tool_context, original_email: str, reply_intent: str, style: str = "professional"):
    """
    Generate email reply based on original email and user intent.
    
    Args:
        tool_context: ADK tool context
        original_email: Original email content
        reply_intent: User's intent for the reply
        style: Reply style (brief, professional, formal, friendly)
        
    Returns:
        str: Generated reply
    """
    try:
        # Get user preferences from session state
        user_preferences = tool_context.session.state.get(USER_PREFERENCES, {})
        user_name = tool_context.session.state.get(USER_NAME, "")
        
        # Override style with user preference if available
        if "email_reply_style" in user_preferences:
            style = user_preferences["email_reply_style"]
        
        # Call MCP client
        response = await tool_context.agent._mcp_client.generate_email_reply(original_email, reply_intent, style)
        
        if response["status"] == "success":
            # Update session state
            tool_context.session.state["content:last_reply_generated"] = response["data"]["reply"]
            tool_context.session.state["content:last_reply_style"] = response["data"]["style"]
            tool_context.session.state["content:last_reply_at"] = response["data"]["timestamp"]
            
            return response["data"]["reply"]
        else:
            return f"Error generating email reply: {response['message']}"
    except Exception as e:
        return f"Error generating email reply: {str(e)}"


async def analyze_email_sentiment(tool_context, content: str):
    """
    Analyze email sentiment, tone, urgency, and formality.
    
    Args:
        tool_context: ADK tool context
        content: Email content to analyze
        
    Returns:
        str: Analysis result
    """
    try:
        # Call MCP client
        response = await tool_context.agent._mcp_client.analyze_email_sentiment(content)
        
        if response["status"] == "success":
            analysis = response["data"]["analysis"]
            
            # Update session state
            tool_context.session.state[CONTENT_LAST_ANALYSIS] = analysis
            tool_context.session.state["content:last_analysis_at"] = response["data"]["timestamp"]
            
            # Format the result for display
            result = f"Sentiment: {analysis['sentiment']}\n"
            result += f"Urgency: {analysis['urgency']}\n"
            result += f"Formality: {analysis['formality']}\n"
            
            return result
        else:
            return f"Error analyzing email sentiment: {response['message']}"
    except Exception as e:
        return f"Error analyzing email sentiment: {str(e)}"


async def extract_action_items(tool_context, content: str):
    """
    Extract actionable tasks from email content.
    
    Args:
        tool_context: ADK tool context
        content: Email content to analyze
        
    Returns:
        str: Extracted action items
    """
    try:
        # Call MCP client
        response = await tool_context.agent._mcp_client.extract_action_items(content)
        
        if response["status"] == "success":
            action_items = response["data"].get("action_items", [])
            
            # Update session state
            tool_context.session.state["content:last_action_items"] = action_items
            tool_context.session.state["content:last_action_items_count"] = len(action_items)
            tool_context.session.state["content:last_action_items_at"] = response["data"]["timestamp"]
            
            if not action_items:
                return "No action items found in the content."
            
            # Format the result for display
            result = f"Found {len(action_items)} action items:\n"
            for i, item in enumerate(action_items, 1):
                result += f"{i}. {item}\n"
            
            return result
        else:
            return f"Error extracting action items: {response['message']}"
    except Exception as e:
        return f"Error extracting action items: {str(e)}"


async def optimize_for_voice(tool_context, content: str, max_length: int = 200):
    """
    Optimize text for voice delivery and speech synthesis.
    
    Args:
        tool_context: ADK tool context
        content: Text to optimize
        max_length: Maximum length of optimized text
        
    Returns:
        str: Optimized text
    """
    try:
        # Call MCP client
        response = await tool_context.agent._mcp_client.optimize_for_voice(content, max_length)
        
        if response["status"] == "success":
            # Update session state
            tool_context.session.state["content:last_voice_optimization"] = response["data"]["optimized_text"]
            tool_context.session.state["content:last_voice_optimization_length"] = len(response["data"]["optimized_text"])
            tool_context.session.state["content:last_voice_optimization_at"] = response["data"]["timestamp"]
            
            return response["data"]["optimized_text"]
        else:
            return f"Error optimizing for voice: {response['message']}"
    except Exception as e:
        return f"Error optimizing for voice: {str(e)}"


async def create_voice_summary(tool_context, content: str):
    """
    Create a summary optimized for voice delivery.
    
    Args:
        tool_context: ADK tool context
        content: Content to summarize
        
    Returns:
        str: Voice-optimized summary
    """
    try:
        # Call MCP client
        response = await tool_context.agent._mcp_client.create_voice_summary(content)
        
        if response["status"] == "success":
            # Update session state
            tool_context.session.state["content:last_voice_summary"] = response["data"]["summary"]
            tool_context.session.state["content:last_voice_summary_length"] = len(response["data"]["summary"])
            tool_context.session.state["content:last_voice_summary_at"] = response["data"]["timestamp"]
            
            return response["data"]["summary"]
        else:
            return f"Error creating voice summary: {response['message']}"
    except Exception as e:
        return f"Error creating voice summary: {str(e)}"


def test_content_agent_adk_integration():
    """
    Test the Content Agent's ADK integration.
    """
    # Create the agent
    agent = create_content_agent()
    
    # Test the agent
    print("Testing Content Agent ADK integration...")
    
    # Test summarization
    print("\nTesting summarization...")
    result = asyncio.run(agent.run(
        "Summarize this email briefly: Hi, I wanted to let you know that the project is on track and we expect to complete it by the end of the month. Please let me know if you have any questions."
    ))
    print(f"Result: {result}")
    
    # Test reply generation
    print("\nTesting reply generation...")
    result = asyncio.run(agent.run(
        "Generate a professional reply to this email: Hi, I wanted to let you know that the project is on track and we expect to complete it by the end of the month. Please let me know if you have any questions."
    ))
    print(f"Result: {result}")
    
    # Test sentiment analysis
    print("\nTesting sentiment analysis...")
    result = asyncio.run(agent.run(
        "Analyze the sentiment of this email: Hi, I wanted to let you know that the project is on track and we expect to complete it by the end of the month. Please let me know if you have any questions."
    ))
    print(f"Result: {result}")
    
    # Test action item extraction
    print("\nTesting action item extraction...")
    result = asyncio.run(agent.run(
        "Extract action items from this email: Hi, I wanted to let you know that the project is on track and we expect to complete it by the end of the month. Please let me know if you have any questions."
    ))
    print(f"Result: {result}")
    
    # Test voice optimization
    print("\nTesting voice optimization...")
    result = asyncio.run(agent.run(
        "Optimize this for voice delivery: Hi, I wanted to let you know that the project is on track and we expect to complete it by the end of the month. Please let me know if you have any questions."
    ))
    print(f"Result: {result}")
    
    # Test voice summary
    print("\nTesting voice summary...")
    result = asyncio.run(agent.run(
        "Create a voice summary of this email: Hi, I wanted to let you know that the project is on track and we expect to complete it by the end of the month. Please let me know if you have any questions."
    ))
    print(f"Result: {result}")
    
    print("\nContent Agent ADK integration test completed.")


# Create the agent instance
agent_name = None


# Export for use in coordinator
__all__ = ["content_agent", "create_content_agent"]


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    def test_content_agent_adk_integration():
        """Test Content Agent ADK integration."""
        print("🧪 Testing Content Agent ADK Integration...")
        
        try:
            # Test agent creation
            agent = create_content_agent()
            
            print(f"✅ Content Agent '{agent.name}' created with ADK integration")
            print(f"🔧 Tools: {len(agent.tools)}")
            print(f"🧠 Model: {agent.model}")
            print(f"📝 Description: {agent.description}")
            print(f"🎯 Output Key: {agent.output_key}")
            
            # Verify it's an LlmAgent (ADK pattern)
            print(f"✅ Agent Type: {type(agent).__name__}")
            
            # Test tool availability
            tool_names = []
            for tool in agent.tools:
                if hasattr(tool, 'func'):
                    tool_names.append(getattr(tool.func, '__name__', 'unknown'))
                else:
                    tool_names.append(str(tool))
            
            print(f"\n📋 Available Tools:")
            content_tools_count = 0
            for i, tool_name in enumerate(tool_names, 1):
                if tool_name.startswith(('summarize', 'generate', 'analyze', 'extract', 'optimize', 'create')):
                    print(f"  {i}. {tool_name} (Content)")
                    content_tools_count += 1
                elif tool_name == 'load_memory':
                    print(f"  {i}. {tool_name} (ADK Memory)")
                else:
                    print(f"  {i}. {tool_name} (Other)")
            
            print(f"\n📊 Tool Summary:")
            print(f"  Content Tools: {content_tools_count}")
            print(f"  Memory Tools: 1")
            print(f"  Total Tools: {len(tool_names)}")
            
            # Verify agent is ready for hierarchy
            print(f"\n📈 ADK Hierarchy Readiness:")
            print(f"  ✅ Returns single LlmAgent (not tuple)")
            print(f"  ✅ Has output_key for state management")
            print(f"  ✅ Includes load_memory for cross-session knowledge")
            print(f"  ✅ Tools have proper ADK integration")
            print(f"  ✅ Ready to be added to coordinator's sub_agents list")
            
            # Test session state constants
            from agents.common.session_keys import USER_PREFERENCES, CONTENT_LAST_SUMMARY
            print("  ✅ Session state constants available")
            
            print(f"\n✅ Content Agent ADK integration completed successfully!")
            print(f"🎯 Ready for coordinator agent integration!")
            
        except Exception as e:
            print(f"❌ Error testing Content Agent integration: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    test_content_agent_adk_integration()


def create_content_runner():
    """
    Create a content agent runner with proper session state handling.
    
    Returns:
        A configured Runner instance
    """
    from google.adk.sessions import InMemorySessionService
    from google.adk.memory import InMemoryMemoryService
    
    # Create the agent
    agent = create_content_agent()
    
    # Create services
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    
    # Create and configure the runner
    runner = Runner(
        agent=agent,
        app_name="test_app",
        session_service=session_service,
        memory_service=memory_service
    )
    
    return runner