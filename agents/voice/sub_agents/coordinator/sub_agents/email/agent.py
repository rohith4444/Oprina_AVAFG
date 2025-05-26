
"""
Email Agent for Oprina

This agent handles all Gmail operations including:
- Fetching and searching emails
- Sending and drafting emails
- Email organization (labels, archive, etc.)
- Gmail authentication and connection management

The agent integrates with Calvin's custom Gmail MCP server for actual Gmail operations
and uses the memory system to maintain email context and user preferences.
"""

import asyncio
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
# From: agents/voice/sub_agents/coordinator/sub_agents/email/agent.py
# Need to go up 6 levels to reach project root
project_root = current_file
for _ in range(7):  # 6 levels + 1 for the file itself
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import your services and config
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from config.settings import settings

# Use absolute imports like your other modules
from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_integration import get_gmail_tools, get_gmail_mcp_status

# Import shared tools
from agents.voice.sub_agents.common.shared_tools import (
    update_email_context,
    get_email_context,
    log_agent_action,
    handle_agent_error,
    update_session_state,
    learn_from_interaction
)

async def create_email_agent():
    """
    Create the Email Agent with Gmail MCP tools.
    
    Returns:
        Tuple of (agent_instance, exit_stack) for proper cleanup
    """
    print("--- Initializing Email Agent ---")
    
    # Get Gmail tools from MCP server
    gmail_tools, exit_stack = await get_gmail_tools()
    
    # Get MCP connection status for agent instructions
    mcp_status = get_gmail_mcp_status()
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.EMAIL_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    # Create the Email Agent
    agent_instance = Agent(
        name="email_agent",
        description="Handles Gmail operations: fetching, sending, organizing emails with intelligent context awareness",
        model=model,
        instruction=f"""
You are the Email Agent for Oprina, a sophisticated voice-powered Gmail assistant.

## Your Role & Responsibilities

You specialize in Gmail operations and email management. Your core responsibilities include:

1. **Email Fetching & Search**
   - Fetch emails based on user queries (date, sender, subject, status)
   - Search through email content intelligently
   - Filter emails by labels, importance, read status
   - Provide email summaries and previews

2. **Email Composition & Sending**
   - Draft emails based on user voice commands
   - Send emails with proper formatting
   - Handle replies and forwards
   - Manage CC, BCC, and attachments

3. **Email Organization**
   - Apply labels and organize emails
   - Archive or delete emails as requested
   - Mark emails as read/unread, important/not important
   - Manage email threads and conversations

4. **Context Management**
   - Update email context in session state
   - Cache email data for performance
   - Track user email patterns and preferences
   - Coordinate with other agents when needed

## Current System Status

- Gmail MCP Connection: {"Connected" if mcp_status["connected"] else "Mock Mode (Development)"}
- Available Tools: {len(gmail_tools)} Gmail tools
- Mock Mode: {mcp_status["mock_mode"]}

## User Context Access

You have access to user context through session state:
- User Name: {{user_name}}
- User Email: {{user_email}}
- Gmail Connected: {{gmail_connected}}
- Email Context: {{current_email_context}}
- User Preferences: {{session_preferences}}

## Available Gmail Tools

Your Gmail tools include:
- `fetch_emails`: Retrieve emails with filtering options
- `send_email`: Send new emails
- `draft_email`: Create email drafts
- `organize_email`: Label, archive, or organize emails

## Session Management Tools

Use these tools to maintain context:
- `update_email_context`: Update email-related session state
- `get_email_context`: Retrieve current email context
- `log_agent_action`: Log your actions for debugging
- `update_session_state`: Update broader session state
- `learn_from_interaction`: Help the system learn from user interactions

## Response Guidelines

1. **Always update context**: Use `update_email_context` after email operations
2. **Log important actions**: Use `log_agent_action` for significant operations
3. **Handle errors gracefully**: Use `handle_agent_error` when things go wrong
4. **Learn from interactions**: Use `learn_from_interaction` to improve user experience
5. **Provide clear feedback**: Always confirm what actions were taken

## Example Workflows

**Fetching Emails:**
1. Use `fetch_emails` with appropriate filters
2. Update `current_email_context` with results
3. Provide user-friendly summary of emails found

**Sending Email:**
1. Use `draft_email` or `send_email` as appropriate
2. Log the action with `log_agent_action`
3. Update email context to reflect the sent email
4. Learn from the interaction to improve future email composition

**Email Organization:**
1. Use `organize_email` with specified action
2. Update context to reflect organizational changes
3. Provide confirmation of actions taken

## Error Handling

If Gmail operations fail:
1. Use `handle_agent_error` to log the error properly
2. Provide user-friendly error messages
3. Suggest alternative actions when possible
4. Update session state to reflect any partial completions

## Important Notes

- Always respect user privacy and email confidentiality
- Provide clear, conversational responses suitable for voice interaction
- When in mock mode, clearly indicate that operations are simulated
- Coordinate with other agents when tasks require content processing or complex workflows

Remember: You are part of a larger voice assistant system. Focus on email operations
while maintaining seamless integration with the broader Oprina experience.
        """,
        tools=gmail_tools + [
            update_email_context,
            get_email_context,
            log_agent_action,
            handle_agent_error,
            update_session_state,
            learn_from_interaction
        ]
    )
    
    print(f"--- Email Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- Gmail MCP Status: {'Connected' if mcp_status['connected'] else 'Mock Mode'} ---")
    
    return agent_instance, exit_stack


# Create the agent instance (async)
root_agent = create_email_agent


# Validation and testing
if __name__ == "__main__":
    async def test_email_agent():
        """Test Email Agent creation and basic functionality."""
        print("Testing Email Agent Creation...")
        
        try:
            # Create agent
            agent, exit_stack = await create_email_agent()
            
            async with exit_stack:
                print(f"✅ Email Agent '{agent.name}' created successfully")
                # Safe tool name access:
                gmail_tools = []
                for tool in agent.tools:
                    tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
                    if any(gmail_op in tool_name for gmail_op in ['fetch', 'send', 'draft', 'organize']):
                        gmail_tools.append(tool)

                print(f"📧 Gmail Tools: {len(gmail_tools)}")
                print(f"🔧 Session Tools: {len(agent.tools) - 4}")
                print(f"🧠 Model: {agent.model}")
                print(f"📝 Description: {agent.description}")
                
                # Test MCP connection status
                mcp_status = get_gmail_mcp_status()
                print(f"📡 MCP Connection: {'✅ Connected' if mcp_status['connected'] else '🔄 Mock Mode'}")
                
                # List all available tools
                print("\n📋 Available Tools:")
                for i, tool in enumerate(agent.tools, 1):
                    tool_name = getattr(tool, 'name', str(tool))
                    print(f"  {i}. {tool_name}")
                
                print("\n✅ Email Agent validation completed successfully!")
                
        except Exception as e:
            print(f"❌ Error creating Email Agent: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    asyncio.run(test_email_agent())