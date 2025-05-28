# agents/voice/sub_agents/coordinator/sub_agents/email/agent.py
"""
Email Agent for Oprina - UPDATED to use Real MCP Tools

This agent handles all Gmail operations using Calvin's MCP tools via the bridge:
- Fetching and searching emails
- Sending and drafting emails
- Email organization (labels, archive, etc.)
- Gmail authentication and connection management

Now uses REAL Gmail tools instead of mock tools!
"""

import asyncio
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(7):  # 6 levels + 1 for the file itself
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import external packages
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from config.settings import settings

# Import MCP integration (updated to use bridge)
from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_integration import get_gmail_tools, get_gmail_mcp_status

# Import shared tools
from agents.voice.sub_agents.common.shared_tools import (
    CORE_ADK_TOOLS,
    CONTEXT_ADK_TOOLS,
    LEARNING_ADK_TOOLS
)

async def create_email_agent() -> Tuple[Agent, Optional[object]]:
    """
    Create the Email Agent with real Gmail MCP tools via bridge.
    
    Returns:
        Tuple of (agent_instance, exit_stack) for proper cleanup
    """
    print("--- Initializing Email Agent with Real MCP Tools ---")
    
    # Get Gmail tools from MCP bridge
    gmail_tools, exit_stack = await get_gmail_tools()
    
    # Get MCP connection status for agent instructions
    mcp_status = get_gmail_mcp_status()
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.EMAIL_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    
    # Determine tools status for instructions
    tools_status = "REAL Gmail tools via MCP Bridge" if mcp_status["connected"] else "No tools available"
    total_tools = len(gmail_tools) + 6  # Gmail tools + shared tools
    
    # Create the Email Agent
    agent_instance = Agent(
        name="email_agent",
        description="Handles Gmail operations: fetching, sending, organizing emails using real Gmail API",
        model=model,
        instruction=f"""
You are the Email Agent for Oprina, a sophisticated voice-powered Gmail assistant.

## Your Role & Responsibilities

You specialize in Gmail operations and email management using REAL Gmail tools. Your core responsibilities include:

1. **Email Fetching & Search**
   - Fetch emails based on user queries (date, sender, subject, status)
   - Search through email content intelligently using Gmail search syntax
   - Filter emails by labels, importance, read status
   - Provide email summaries and previews

2. **Email Composition & Sending**
   - Draft emails based on user voice commands
   - Send emails with proper formatting
   - Handle replies and forwards with threading
   - Manage CC, BCC, and attachments

3. **Email Organization**
   - Apply labels and organize emails
   - Archive or delete emails as requested
   - Mark emails as read/unread, important/not important
   - Manage email threads and conversations

4. **Context Management**
   - Update email context in session state after operations
   - Cache email data for performance
   - Track user email patterns and preferences
   - Coordinate with other agents when needed

## Current System Status

- Gmail Tools Status: {tools_status}
- Available Tools: {len(gmail_tools)} Gmail tools + 6 shared tools = {total_tools} total
- MCP Bridge Connected: {mcp_status["connected"]}
- Integration Type: {mcp_status.get("integration_type", "unknown")}

## User Context Access

You have access to user context through session state:
- User Name: {{user_name}}
- User Email: {{user_email}}
- Gmail Connected: {{gmail_connected}}
- Email Context: {{current_email_context}}
- User Preferences: {{session_preferences}}

## Available Gmail Tools

Your real Gmail tools include:
- `gmail_list_messages`: List/search messages with Gmail query syntax
- `gmail_get_message`: Get full message details by ID
- `gmail_search`: Search emails with advanced queries
- `gmail_send_message`: Send new emails with attachments
- `gmail_reply_message`: Reply to existing messages
- `gmail_create_draft`: Create email drafts
- `gmail_modify_labels`: Apply/remove labels
- `gmail_mark_message_status`: Mark read/unread/starred/important
- `gmail_archive_message`: Archive messages
- `gmail_trash_message`: Move to trash
- `gmail_get_attachments`: Download attachments
- And 15+ more Gmail operations...

## Session Management Tools

Use these tools to maintain context and learn:
- `update_email_context`: Update email-related session state
- `get_email_context`: Retrieve current email context
- `log_agent_action`: Log your actions for debugging
- `update_session_state`: Update broader session state
- `learn_from_interaction`: Help the system learn from user interactions
- `measure_performance`: Track operation performance

## Response Guidelines

1. **Always update context**: Use `update_email_context` after significant email operations
2. **Log important actions**: Use `log_agent_action` for significant operations
3. **Handle errors gracefully**: Provide helpful error messages when Gmail operations fail
4. **Learn from interactions**: Use `learn_from_interaction` to improve user experience
5. **Provide clear feedback**: Always confirm what actions were taken
6. **Use real Gmail syntax**: Leverage Gmail's powerful query syntax for searches

## Example Workflows

**Fetching Emails:**
1. Use `gmail_list_messages` or `gmail_search` with appropriate Gmail query syntax
2. Use `gmail_get_message` for full details if needed
3. Update `current_email_context` with results using `update_email_context`
4. Provide user-friendly summary of emails found

**Sending Email:**
1. Use `gmail_send_message` with proper parameters
2. Log the action with `log_agent_action`
3. Update email context to reflect the sent email
4. Learn from the interaction to improve future email composition

**Email Organization:**
1. Use `gmail_modify_labels`, `gmail_archive_message`, etc. as appropriate
2. Update context to reflect organizational changes
3. Provide confirmation of actions taken

## Gmail Query Syntax Examples

- `from:john@example.com`: Emails from specific sender
- `subject:meeting`: Emails with "meeting" in subject
- `is:unread`: Unread emails
- `has:attachment`: Emails with attachments
- `after:2024/1/1`: Emails after specific date
- `label:important`: Emails with Important label
- `in:inbox`: Emails in inbox
- `is:starred`: Starred emails

## Error Handling

When Gmail operations fail:
1. Use `handle_agent_error` to log the error appropriately
2. Check if it's an authentication issue and guide user to re-authenticate
3. Provide user-friendly error messages
4. Suggest alternative actions when possible
5. Update session state to reflect any partial completions

## Important Notes

- You now have REAL Gmail access - operations will affect the user's actual Gmail account
- Respect user privacy and email confidentiality
- Provide clear, conversational responses suitable for voice interaction
- Always confirm before performing destructive actions (delete, trash)
- Use performance measurement tools to track operation efficiency

## Integration with Other Agents

You work closely with:
- **Content Agent**: Process content from fetched emails (summarization, analysis)
- **Coordinator Agent**: Receive delegated email tasks and report results
- **Voice Agent**: Ensure all responses are optimized for voice delivery

Remember: You are now connected to the user's REAL Gmail account via Calvin's MCP tools. 
All operations are live and will affect their actual email data. Use this power responsibly!
        """,
        tools=gmail_tools + CORE_ADK_TOOLS + CONTEXT_ADK_TOOLS + LEARNING_ADK_TOOLS
    )
    
    print(f"--- Email Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- Gmail MCP Status: {'✅ Connected' if mcp_status['connected'] else '❌ Disconnected'} ---")
    print(f"--- Gmail Tools: {len(gmail_tools)} | Shared Tools: 6 ---")
    
    if mcp_status["connected"]:
        print("🎉 Email Agent is now using REAL Gmail tools!")
    else:
        print("⚠️ Email Agent could not connect to Gmail tools")
    
    return agent_instance, exit_stack


# Create the agent instance (async function, not direct instance)
root_agent = create_email_agent


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    async def test_email_agent():
        """Test Email Agent creation and basic functionality."""
        print("🧪 Testing Email Agent with Real MCP Tools...")
        
        try:
            # Create agent
            agent, exit_stack = await create_email_agent()
            
            # Use exit_stack context
            async with exit_stack or nullcontext():
                print(f"✅ Email Agent '{agent.name}' created successfully")
                
                # Count tool types
                gmail_tools_count = 0
                shared_tools_count = 0
                
                for tool in agent.tools:
                    tool_name = getattr(tool.func, '__name__', str(tool))
                    if 'gmail' in tool_name.lower():
                        gmail_tools_count += 1
                    else:
                        shared_tools_count += 1
                
                print(f"📧 Gmail Tools: {gmail_tools_count}")
                print(f"🔧 Shared Tools: {shared_tools_count}")
                print(f"🧠 Model: {agent.model}")
                print(f"📝 Description: {agent.description}")
                
                # Test MCP connection status
                mcp_status = get_gmail_mcp_status()
                print(f"📡 MCP Status: {mcp_status}")
                
                # List some available tools
                print(f"\n📋 Available Tools (first 10):")
                for i, tool in enumerate(agent.tools[:10], 1):
                    tool_name = getattr(tool.func, '__name__', f'tool_{i}')
                    print(f"  {i}. {tool_name}")
                
                if len(agent.tools) > 10:
                    print(f"  ... and {len(agent.tools) - 10} more tools")
                
                print(f"\n✅ Email Agent validation completed successfully!")
                print(f"🎯 Ready for real Gmail operations!")
                
        except Exception as e:
            print(f"❌ Error creating Email Agent: {e}")
            import traceback
            traceback.print_exc()

    # Helper for nullcontext (if exit_stack is None)
    from contextlib import nullcontext
    
    # Run the test
    asyncio.run(test_email_agent())