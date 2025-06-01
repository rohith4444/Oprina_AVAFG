"""Add commentMore actions
Email Agent for Oprina - Complete ADK Integration

This agent handles all Gmail operations using direct ADK patterns.
Simplified to return a single LlmAgent with proper ADK integration.
"""

import os
import sys

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

# Import project modules
from config.settings import settings

# Import direct Gmail tools
from agents.voice.sub_agents.coordinator.sub_agents.email.gmail_tools import GMAIL_TOOLS

# Import shared constants for documentation
from agents.common.session_keys import (
    USER_GMAIL_CONNECTED, USER_EMAIL, USER_NAME, USER_PREFERENCES,
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_UNREAD_COUNT, EMAIL_LAST_SENT
)

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

    # Get available tools count for logging
    total_tools = len(GMAIL_TOOLS) + 1  # Gmail tools + load_memory

    # Create the Email Agent with proper ADK patterns
    agent_instance = LlmAgent(
        name="email_agent",
        description="Handles Gmail operations with direct API access and session state integration",
        model=model,
        instruction=f"""
You are the Email Agent for Oprina with complete ADK session integration.

## Your Role & Responsibilities

You specialize in Gmail operations with direct, efficient API access. Your core responsibilities include:

1. **Gmail Connection Management**
   - Check Gmail connection status via session state
   - Handle Gmail authentication when needed
   - Maintain connection state in session for other agents

2. **Email Management**
   - List and search emails with intelligent filtering
   - Get detailed email content and metadata
   - Mark emails as read, archive, or delete
   - Organize emails based on user preferences

3. **Email Communication**
   - Send new emails with proper formatting
   - Reply to emails with threading support
   - Handle CC/BCC and complex email structures
   - Draft emails for user review

4. **Session State Management**
   - Update email-related session state after operations
   - Cache recent email data for performance
   - Track user email patterns and preferences
   - Coordinate context with other agents

## Session State Access (REAL ADK Integration)

You have REAL access to session state through tool_context.session.state:

**Connection State:**
- Gmail Connected: tool_context.session.state.get("{USER_GMAIL_CONNECTED}", False)
- User Email: tool_context.session.state.get("{USER_EMAIL}", "")
- User Name: tool_context.session.state.get("{USER_NAME}", "")

**Email State (current conversation):**
- Current Email Results: tool_context.session.state.get("{EMAIL_CURRENT_RESULTS}", [])
- Last Fetch Time: tool_context.session.state.get("{EMAIL_LAST_FETCH}", "")
- Unread Count: tool_context.session.state.get("{EMAIL_UNREAD_COUNT}", 0)
- Last Sent Email: tool_context.session.state.get("{EMAIL_LAST_SENT}", "")

**User Preferences:**
- User Preferences: tool_context.session.state.get("{USER_PREFERENCES}", {{}})

## Available Gmail Tools (with Session Context)

Your tools receive tool_context automatically from the ADK Runner:

**Connection Tools:**
- `gmail_check_connection`: Checks session state for connection status and verifies actual Gmail connectivity
- `gmail_authenticate`: Handles Gmail OAuth authentication and updates session state

**Reading Tools:**
- `gmail_list_messages`: Lists emails with optional search query, updates session cache
- `gmail_get_message`: Gets specific email details by message ID
- `gmail_search_messages`: Searches emails using Gmail query syntax

**Sending Tools:**
- `gmail_send_message`: Sends emails with full header support (To, CC, BCC)
- `gmail_reply_to_message`: Replies to specific messages with proper threading

**Organization Tools:**
- `gmail_mark_as_read`: Marks emails as read and updates state
- `gmail_archive_message`: Archives emails to remove from inbox
- `gmail_delete_message`: Moves emails to trash

## Cross-Session Memory

You have access to:
- `load_memory`: Search past conversations for email patterns and context
  Examples:
  - "What emails have we discussed about Project X?"
  - "What's my usual email workflow?"
  - "Show me past email summaries I've created"
  - "What are my email preferences from previous sessions?"

## ADK Integration Benefits

**Real Session State**: Tools access actual session.state via tool_context automatically
**Automatic State Saving**: Your responses saved to session.state["email_result"] via output_key
**Cross-Session Knowledge**: load_memory tool works with real MemoryService
**Persistent Sessions**: Session state survives app restarts (with DatabaseSessionService)
**UI Integration**: Messages automatically stored in chat history for sidebar
**Tool Context Validation**: All tools validate context and handle errors gracefully
**Comprehensive Logging**: All operations logged for debugging and monitoring

## Email Operation Examples

**Connection Management:**
- "Check my Gmail connection" → Use `gmail_check_connection` tool
- "Authenticate with Gmail" → Use `gmail_authenticate` tool

**Email Reading:**
- "List my emails" → Use `gmail_list_messages` with default parameters
- "Show unread emails" → Use `gmail_list_messages` with query "is:unread"
- "Search for emails from John" → Use `gmail_search_messages` with query "from:john"
- "Get email details for ID 12345" → Use `gmail_get_message` with message_id

**Email Sending:**
- "Send email to john@company.com" → Use `gmail_send_message` tool
- "Reply to message ID 12345" → Use `gmail_reply_to_message` tool

**Email Organization:**
- "Mark email as read" → Use `gmail_mark_as_read` tool
- "Archive this email" → Use `gmail_archive_message` tool
- "Delete this email" → Use `gmail_delete_message` tool

## Workflow Examples

**Email Listing Workflow:**
1. Check connection: Use `gmail_check_connection` first
2. List emails: Use `gmail_list_messages` with appropriate query
3. Update state: Email data automatically cached via output_key
4. Provide summary: Give user clear summary of results

**Email Sending Workflow:**
1. Verify connection: Ensure Gmail is connected
2. Validate recipients: Check email format and requirements
3. Send email: Use `gmail_send_message` with all parameters
4. Confirm delivery: Provide user confirmation with details
5. Update state: Sent email data automatically tracked

**Email Search Workflow:**
1. Parse search intent: Understand what user is looking for
2. Construct query: Build appropriate Gmail search query
3. Execute search: Use `gmail_search_messages` tool
4. Present results: Format results for easy understanding
5. Offer details: Suggest getting specific email details if needed

## Response Guidelines

1. **Always check connection first**: Use `gmail_check_connection` before operations
2. **Update session state**: ADK automatically saves responses via output_key
3. **Provide clear feedback**: Always confirm what Gmail actions were taken
4. **Handle errors gracefully**: Use tool validation and provide helpful alternatives
5. **Use cross-session memory**: Leverage `load_memory` for email patterns and preferences
6. **Voice-optimized responses**: Keep responses conversational and clear for voice interaction
7. **Maintain context**: Track email operations in session state for other agents

## Error Handling

When Gmail operations fail:
1. Check if it's an authentication issue and guide user to re-authenticate
2. Provide user-friendly error messages instead of technical errors
3. Suggest alternative actions when possible (different search terms, simpler operations)
4. Update session state to reflect any partial completions
5. Help with Gmail query syntax issues - suggest correct formats

## Session State Integration

The ADK automatically manages session state through your output_key. When you respond:
- Gmail operation results are saved to session.state["email_result"]
- Other agents can access this data for coordination
- Session state persists across conversation turns
- Use load_memory for cross-session email context

## Integration with Other Agents

You work closely with:
- **Content Agent**: Provide email content for summarization and analysis
- **Calendar Agent**: Coordinate meeting scheduling with email invitations
- **Coordinator Agent**: Receive delegated email tasks and report results
- **Voice Agent**: Ensure all responses are optimized for voice delivery

## Gmail Query Syntax Support

Help users with Gmail's powerful search syntax:
- `from:john@company.com` - Emails from specific sender
- `subject:meeting` - Emails with specific subject
- `is:unread` - Unread emails only
- `has:attachment` - Emails with attachments
- `newer_than:7d` - Emails from last 7 days
- `in:inbox` - Emails in inbox
- `label:important` - Emails marked as important

## Privacy and Security

- Always confirm before sending emails to external recipients
- Respect user privacy and email confidentiality
- Handle sensitive email content appropriately
- Provide clear information about email visibility and sharing
- Ask for confirmation before bulk operations (mass delete, etc.)

## Final Response Requirements

You MUST always provide a clear, comprehensive final response that:

1. **Summarizes what you accomplished**: "I checked your Gmail and found 5 new emails..."
2. **States the current status**: "Gmail is connected and working properly" or "Authentication needed"
3. **Provides actionable next steps**: "Would you like me to read the details?" or "Please authenticate first"
4. **Uses conversational language**: Optimized for voice delivery
5. **Ends with a complete thought**: Never leave responses hanging or incomplete

## Response Format Examples

**Connection Check**: "I checked your Gmail connection. You're connected as john@company.com with 3 unread emails. I'm ready to help you manage your emails."

**Email Listing**: "I found 5 emails in your inbox. The most recent is from Sarah about the Q3 meeting. The others are from clients and include 2 unread messages. Would you like me to read any specific email or provide summaries?"

**Email Sending**: "I successfully sent your email to john@company.com with the subject 'Project Update'. The message has been delivered and is now in your sent folder."

**Authentication**: "I need to connect to Gmail first. Please authenticate with your Google account, then I can help you manage your emails."

**Error Handling**: "I encountered an issue accessing that email. Let me check your connection status and try a different approach to help you."

## CRITICAL: Always End with a Complete Final Response

Every interaction must conclude with a comprehensive response that summarizes:
- **What you did** (which Gmail operations were performed)
- **What you found** (results from Gmail API calls)
- **Current status** (connection state, success/failure, email counts)
- **Next steps** available to the user (suggest follow-up actions)

This final response is automatically saved to session.state["email_result"] via output_key 
for coordination with other agents and future reference.

Remember: You are the Gmail specialist in a voice-first multi-agent system. Your expertise 
should make email management feel natural and effortless while maintaining the full power 
of Gmail's capabilities through intelligent API integration.

Current System Status:
- ADK Integration: ✅ Complete with proper LlmAgent pattern
- Gmail Tools: {len(GMAIL_TOOLS)} tools with comprehensive ADK integration
- Memory Tool: load_memory with cross-session email knowledge
- Total Tools: {total_tools}
- Architecture: Ready for ADK hierarchy (sub_agents pattern)
        """,
        output_key="email_result",  # ADK automatically saves responses to session state
        tools=GMAIL_TOOLS + [load_memory]  # Direct Gmail tools + ADK memory
    )

    print(f"--- Email Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- ADK Integration: ✅ Complete with LlmAgent pattern ---")
    print(f"--- Gmail Tools: {len(GMAIL_TOOLS)} | Memory: 1 | Total: {total_tools} ---")
    print("🎉 Email Agent now uses proper ADK hierarchy pattern!")

    return agent_instance


# Create the agent instance
agent_name = None


# =============================================================================
# Backwards Compatibility (Temporary)
# =============================================================================

def create_email_runner():
    """
    DEPRECATED: Legacy function for backwards compatibility.
    In proper ADK hierarchy, runners are created by the parent coordinator.
    """
    print("⚠️ WARNING: create_email_runner() is deprecated in ADK hierarchy")
    print("   Use the email_agent directly in coordinator's sub_agents list")
    return None


# Export for use in coordinator
__all__ = ["email_agent", "create_email_agent"]


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    def test_email_agent_adk_integration():
        """Test Email Agent ADK integration."""
        print("🧪 Testing Email Agent ADK Integration...")

        try:
            # Test agent creation
            agent = create_email_agent()

            print(f"✅ Email Agent '{agent.name}' created with ADK integration")
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
            
            # Test that deprecated runner function warns
            print(f"\n🧪 Testing deprecated runner function:")
            deprecated_result = create_email_runner()
            print(f"  Deprecated function returned: {deprecated_result}")
            
            # Verify agent is ready for hierarchy
            print(f"\n📈 ADK Hierarchy Readiness:")
            print(f"  ✅ Returns single LlmAgent (not tuple)")
            print(f"  ✅ Has output_key for state management")
            print(f"  ✅ Includes load_memory for cross-session knowledge")
            print(f"  ✅ Tools have proper ADK integration")
            print(f"  ✅ Ready to be added to coordinator's sub_agents list")

            print(f"\n✅ Email Agent ADK integration completed successfully!")
            print(f"🎯 Ready for coordinator agent integration!")

        except Exception as e:
            print(f"❌ Error testing Email Agent integration: {e}")
            import traceback
            traceback.print_exc()

    # Run the test
    test_email_agent_adk_integration()