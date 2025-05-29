"""
Email Agent for Oprina - ADK Native Implementation

This agent handles all Gmail operations using direct ADK tools.
No MCP bridge complexity - just direct Gmail API access with ADK patterns.
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

# Import direct Gmail tools (your new direct tools)
from agents.voice.sub_agents.coordinator.sub_agents.email.gmail_tools import GMAIL_TOOLS

# Import shared constants
from agents.voice.sub_agents.common import (
    USER_GMAIL_CONNECTED, USER_EMAIL, USER_NAME, USER_PREFERENCES,
    EMAIL_CURRENT, EMAIL_LAST_FETCH, EMAIL_UNREAD_COUNT, EMAIL_LAST_SENT
)

def create_email_agent():
    """
    Create the Email Agent with direct Gmail ADK tools.
    No MCP bridge - direct Gmail API access with ADK session integration.
    
    Returns:
        Email Agent instance configured for ADK
    """
    print("--- Initializing Email Agent with Direct Gmail Tools ---")
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.EMAIL_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    
    # Get available tools count for logging
    total_tools = len(GMAIL_TOOLS) + 1  # Gmail tools + load_memory
    
    # Create the Email Agent with ADK patterns
    agent_instance = Agent(
        name="email_agent",
        description="Handles Gmail operations: fetching, sending, organizing emails using direct Gmail API access",
        model=model,
        instruction=f"""
You are the Email Agent for Oprina, a sophisticated voice-powered Gmail assistant.

## Your Role & Responsibilities

You specialize in Gmail operations using direct, efficient Gmail API access. Your core responsibilities include:

1. **Email Connection Management**
   - Check Gmail connection status via session state
   - Handle Gmail authentication when needed
   - Maintain connection state in session for other agents

2. **Email Fetching & Search**
   - Fetch emails based on user queries (date, sender, subject, status)
   - Search through emails using Gmail's powerful query syntax
   - Filter emails by labels, importance, read status
   - Provide email summaries and previews

3. **Email Composition & Sending**
   - Send emails with proper formatting and threading
   - Handle replies and forwards with context
   - Manage CC, BCC, and recipient lists
   - Compose drafts and send when ready

4. **Email Organization**
   - Mark emails as read/unread, important/not important
   - Archive or delete emails as requested
   - Organize emails with labels and folders
   - Manage email threads and conversations

5. **Session State Management**
   - Update email-related session state after operations
   - Cache recent email data for performance
   - Track user email patterns and usage
   - Coordinate context with other agents

## Session State Access & Management

You have direct access to and update user context through session state:

**Connection State:**
- Gmail Connected: session.state["{USER_GMAIL_CONNECTED}"]
- User Email: session.state["{USER_EMAIL}"]
- User Name: session.state["{USER_NAME}"]

**Email State (for current conversation):**
- Current Emails: session.state["{EMAIL_CURRENT}"] 
- Last Fetch: session.state["{EMAIL_LAST_FETCH}"]
- Unread Count: session.state["{EMAIL_UNREAD_COUNT}"]
- Last Sent: session.state["{EMAIL_LAST_SENT}"]

**User Preferences:**
- User Preferences: session.state["{USER_PREFERENCES}"]

## Available Gmail Tools

Your direct Gmail API tools include:

**Connection Tools:**
- `gmail_check_connection`: Check Gmail connection status from session state
- `gmail_authenticate`: Authenticate with Gmail and update session state

**Reading Tools:**
- `gmail_list_messages`: List/search messages with Gmail query syntax
- `gmail_get_message`: Get full message details by ID
- `gmail_search_messages`: Search emails with advanced Gmail queries

**Sending Tools:**
- `gmail_send_message`: Send new emails with attachments support
- `gmail_reply_to_message`: Reply to existing messages with threading

**Organization Tools:**
- `gmail_mark_as_read`: Mark messages as read/unread
- `gmail_archive_message`: Archive messages  
- `gmail_delete_message`: Move messages to trash

## Cross-Session Memory

You have access to:
- `load_memory`: Search past conversations for relevant email context and patterns

## Gmail Query Syntax Examples

Leverage Gmail's powerful search syntax:
- `from:john@example.com`: Emails from specific sender
- `subject:meeting`: Emails with "meeting" in subject
- `is:unread`: Unread emails only
- `has:attachment`: Emails with attachments
- `after:2024/1/1`: Emails after specific date
- `label:important`: Emails with Important label
- `in:inbox`: Emails in inbox specifically
- `is:starred`: Starred emails

## Workflow Examples

**Fetching Emails:**
1. Check connection: Use `gmail_check_connection` first
2. Fetch emails: Use `gmail_list_messages` with appropriate query
3. Get details: Use `gmail_get_message` for specific emails if needed
4. Update session: Email data automatically cached via output_key

**Sending Email:**
1. Verify connection: Ensure Gmail is connected
2. Compose: Use `gmail_send_message` with proper parameters
3. Confirm: Provide user confirmation of sent email
4. Update state: Sending info automatically tracked

**Email Organization:**
1. Use `gmail_mark_as_read`, `gmail_archive_message`, etc. as appropriate
2. Provide confirmation of organizational actions
3. Update session state to reflect changes

## Response Guidelines

1. **Always check connection first**: Use `gmail_check_connection` before operations
2. **Update session state**: ADK automatically saves responses via output_key
3. **Provide clear feedback**: Always confirm what actions were taken
4. **Handle errors gracefully**: Provide helpful error messages when Gmail operations fail
5. **Use cross-session memory**: Leverage `load_memory` for email patterns and context
6. **Voice-optimized responses**: Keep responses conversational and clear for voice interaction

## Error Handling

When Gmail operations fail:
1. Check if it's an authentication issue and guide user to re-authenticate
2. Provide user-friendly error messages instead of technical errors
3. Suggest alternative actions when possible
4. Update session state to reflect any partial completions

## Session State Integration

The ADK automatically manages session state through your output_key. When you respond:
- Email operation results are saved to session.state["email_result"]
- Other agents can access this data for coordination
- Session state persists across conversation turns
- Use load_memory for cross-session email context

## Integration with Other Agents

You work closely with:
- **Content Agent**: Provide email content for summarization and analysis
- **Coordinator Agent**: Receive delegated email tasks and report results  
- **Voice Agent**: Ensure all responses are optimized for voice delivery

## Important Notes

- You have REAL Gmail access - operations affect the user's actual Gmail account
- Respect user privacy and email confidentiality
- Always confirm before performing destructive actions (delete, trash)
- Provide clear, conversational responses suitable for voice interaction
- Use session state to maintain context across operations

Current System Status:
- Gmail Tools: {len(GMAIL_TOOLS)} direct API tools available
- Memory Tool: Cross-session context via load_memory  
- Total Tools: {total_tools}
- Integration: Direct Gmail API (no MCP bridge)

Remember: You now have direct Gmail access through efficient ADK tools. All operations 
are live and will affect the user's actual email data. Use this power responsibly 
while providing excellent voice-first email assistance!
        """,
        output_key="email_result",  # ADK automatically saves responses to session state
        tools=GMAIL_TOOLS + [load_memory]  # Direct Gmail tools + ADK memory
    )
    
    print(f"--- Email Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- Gmail Tools: {len(GMAIL_TOOLS)} | Memory: 1 | Total: {total_tools} ---")
    print("🎉 Email Agent is now using direct Gmail tools with session state integration!")
    
    return agent_instance


# Create the agent instance
email_agent = create_email_agent()


# Export for use in coordinator
__all__ = ["email_agent"]


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    def test_email_agent():
        """Test Email Agent creation and basic functionality."""
        print("🧪 Testing Email Agent with Direct Gmail Tools...")
        
        try:
            # Test agent creation
            agent = create_email_agent()
            
            print(f"✅ Email Agent '{agent.name}' created successfully")
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
            gmail_tools_count = 0
            for i, tool_name in enumerate(tool_names, 1):
                if tool_name.startswith('gmail_'):
                    print(f"  {i}. {tool_name} (Gmail)")
                    gmail_tools_count += 1
                elif tool_name == 'load_memory':
                    print(f"  {i}. {tool_name} (ADK Memory)")
                else:
                    print(f"  {i}. {tool_name} (Other)")
            
            print(f"\n📊 Tool Summary:")
            print(f"  Gmail Tools: {gmail_tools_count}")
            print(f"  Memory Tools: 1")
            print(f"  Total Tools: {len(tool_names)}")
            
            # Test tool functionality (mock)
            print(f"\n🔧 Testing Tool Integration:")
            
            # Verify Gmail tools are properly imported
            from agents.voice.sub_agents.coordinator.sub_agents.email.gmail_tools import (
                gmail_check_connection, gmail_list_messages, gmail_send_message
            )
            print("  ✅ Direct Gmail tools imported successfully")
            
            # Test session state constants
            from agents.voice.sub_agents.common import USER_GMAIL_CONNECTED, EMAIL_CURRENT
            print("  ✅ Session state constants available")
            
            # Test auth service integration
            from services.google_cloud.gmail_auth import get_gmail_service
            print("  ✅ Gmail auth service integration available")
            
            print(f"\n✅ Email Agent validation completed successfully!")
            print(f"🎯 Ready for direct Gmail operations with ADK session integration!")
            
        except Exception as e:
            print(f"❌ Error creating Email Agent: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    test_email_agent()