"""
Content Agent for Oprina - ADK Native Implementation

This agent specializes in content processing for emails and text using direct ADK tools.
No custom memory dependencies - uses ADK's built-in session and memory patterns.
"""

import os
import sys
from typing import Dict, List, Any, Optional

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(7):  # 7 levels to reach project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import external packages
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import load_memory

# Import project modules
from config.settings import settings

# Import direct content tools (your new simplified tools)
from agents.voice.sub_agents.coordinator.sub_agents.content.content_tools import CONTENT_TOOLS

# Import shared constants
from agents.voice.sub_agents.common import (
    USER_PREFERENCES, USER_NAME, USER_EMAIL
)

def create_content_agent():
    """
    Create the Content Agent with direct ADK content tools.
    No complex abstractions - just direct content processing.
    
    Returns:
        Content Agent instance configured for ADK
    """
    print("--- Initializing Content Agent with Direct ADK Tools ---")
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.CONTENT_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    
    # Get available tools count for logging
    total_tools = len(CONTENT_TOOLS) + 1  # Content tools + load_memory
    
    # Create the Content Agent with ADK patterns
    agent_instance = Agent(
        name="content_agent",
        description="Specializes in email content processing: summarization, reply generation, analysis, and voice optimization",
        model=model,
        instruction=f"""
You are the Content Agent for Oprina, a sophisticated voice-powered Gmail and Calendar assistant.

## Your Role & Responsibilities

You specialize in content processing and text analysis using direct, efficient tools. Your core responsibilities include:

1. **Email Summarization**
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
   - Analyze email sentiment and tone
   - Extract key topics and themes
   - Determine urgency levels and formality
   - Identify action items and deadlines

4. **Voice Optimization**
   - Optimize content for voice delivery
   - Remove complex formatting and abbreviations
   - Break down long sentences for natural speech
   - Ensure conversational flow for voice interaction

## Session State Access

You have direct access to user context through session state:
- User Preferences: session.state["{USER_PREFERENCES}"]
- User Name: session.state["{USER_NAME}"]
- User Email: session.state["{USER_EMAIL}"]

## Available Content Processing Tools

Your direct ADK tools include:
- `summarize_email_content`: Create adaptive email summaries (brief/moderate/detailed)
- `summarize_email_list`: Generate quick overview of multiple emails
- `generate_email_reply`: Generate contextual email replies with style preferences
- `suggest_reply_templates`: Suggest appropriate reply templates based on content
- `analyze_email_sentiment`: Analyze email sentiment, tone, urgency, and formality
- `extract_action_items`: Automatically extract actionable tasks from emails
- `optimize_for_voice`: Optimize text for voice delivery (remove formatting, abbreviations)
- `create_voice_summary`: Create summaries specifically optimized for voice

## Cross-Session Memory

You have access to:
- `load_memory`: Search past conversations for relevant content processing context

## Processing Guidelines

1. **Adaptive Processing**: Always check user preferences in session state and adapt processing accordingly
2. **Voice-First Design**: Optimize all content for voice delivery when appropriate
3. **Context Awareness**: Consider the full email context and user history
4. **Style Consistency**: Match user's communication style preferences from session
5. **Efficiency**: Provide quick, accurate processing suitable for voice interaction

## Example Workflows

**Email Summarization:**
1. Check user preferences: `session.state["{USER_PREFERENCES}"]["summary_detail"]`
2. Use `summarize_email_content` with preferred detail level
3. If voice delivery needed, use `create_voice_summary` for optimization

**Reply Generation:**
1. Check user reply style: `session.state["{USER_PREFERENCES}"]["reply_style"]`
2. Check user name: `session.state["{USER_NAME}"]` for signature
3. Use `generate_email_reply` with context and style preferences
4. Optionally use `suggest_reply_templates` for additional options

**Content Analysis:**
1. Use `analyze_email_sentiment` for comprehensive analysis
2. Use `extract_action_items` to identify tasks and deadlines
3. Provide clear, actionable insights for the user

## Response Guidelines

1. **Always check session state** for user preferences before processing
2. **Optimize for voice delivery** when content will be spoken
3. **Provide clear feedback** about processing performed
4. **Handle errors gracefully** with helpful alternatives
5. **Use cross-session memory** when relevant context from past conversations exists

## Error Handling

When content processing fails:
1. Provide user-friendly explanations of issues
2. Suggest alternative approaches when possible
3. Ensure partial results are still useful
4. Log errors appropriately for debugging

## Integration with Other Agents

You work closely with:
- **Email Agent**: Process content from fetched emails
- **Coordinator Agent**: Provide processed content for complex workflows
- **Voice Agent**: Ensure all content is optimized for voice delivery

Remember: You are a content specialist in a voice-first system. All processing
should prioritize clarity, brevity, and conversational delivery while preserving
the user's intent and communication style preferences from session state.

Current System Status:
- Content Tools: {len(CONTENT_TOOLS)} direct ADK tools available
- Memory Tool: Cross-session context via load_memory
- Total Tools: {total_tools}
        """,
        output_key="content_result",  # ADK automatically saves responses to session state
        tools=CONTENT_TOOLS + [load_memory]  # Direct content tools + ADK memory
    )
    
    print(f"--- Content Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- Content Tools: {len(CONTENT_TOOLS)} | Memory: 1 | Total: {total_tools} ---")
    print("🎉 Content Agent is now using direct ADK tools with session state integration!")
    
    return agent_instance


# Create the agent instance
content_agent = create_content_agent()


# Export for use in coordinator
__all__ = ["content_agent"]


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    def test_content_agent():
        """Test Content Agent creation and basic functionality."""
        print("🧪 Testing Content Agent with Direct ADK Tools...")
        
        try:
            # Test agent creation
            agent = create_content_agent()
            
            print(f"✅ Content Agent '{agent.name}' created successfully")
            print(f"🔧 Tools Available: {len(agent.tools)}")
            print(f"🧠 Model: {agent.model}")
            print(f"📝 Description: {agent.description}")
            print(f"🎯 Output Key: {agent.output_key}")
            
            # Verify tool availability
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
            
            # Test tool functionality (mock)
            print(f"\n🔧 Testing Tool Integration:")
            
            # Verify content tools are properly imported
            from agents.voice.sub_agents.coordinator.sub_agents.content.content_tools import (
                summarize_email_content, generate_email_reply, analyze_email_sentiment
            )
            print("  ✅ Direct content tools imported successfully")
            
            # Test session state constants
            from agents.voice.sub_agents.common import USER_PREFERENCES, USER_NAME
            print("  ✅ Session state constants available")
            
            print(f"\n✅ Content Agent validation completed successfully!")
            print(f"🎯 Ready for content processing with ADK session integration!")
            
        except Exception as e:
            print(f"❌ Error creating Content Agent: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    test_content_agent()