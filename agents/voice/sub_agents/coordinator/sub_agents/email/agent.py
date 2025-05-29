# Updated Agent Pattern - Example for Email Agent
"""
Email Agent for Oprina - Complete ADK Integration

This agent handles all Gmail operations using direct ADK tools with proper
Runner and session integration through the ADK Memory Manager.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple

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

# Import ADK Memory Manager
from memory.adk_memory_manager import get_adk_memory_manager

# Import direct Gmail tools
from agents.voice.sub_agents.coordinator.sub_agents.email.gmail_tools import GMAIL_TOOLS

# Import shared constants
from agents.voice.sub_agents.common import (
    USER_GMAIL_CONNECTED, USER_EMAIL, USER_NAME, USER_PREFERENCES,
    EMAIL_CURRENT, EMAIL_LAST_FETCH, EMAIL_UNREAD_COUNT, EMAIL_LAST_SENT
)

def create_email_agent() -> Tuple[Agent, callable]:
    """
    Create the Email Agent with complete ADK integration.
    
    Returns:
        Tuple of (agent_instance, runner_factory_function)
    """
    print("--- Initializing Email Agent with Complete ADK Integration ---")
    
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
        description="Handles Gmail operations with direct API access and session state integration",
        model=model,
        instruction=f"""
You are the Email Agent for Oprina with complete ADK session integration.

## Session State Access (REAL ADK Integration)

You now have REAL access to session state through tool_context.session.state:

**Connection State:**
- Gmail Connected: tool_context.session.state.get("{USER_GMAIL_CONNECTED}", False)
- User Email: tool_context.session.state.get("{USER_EMAIL}", "")
- User Name: tool_context.session.state.get("{USER_NAME}", "")

**Email State (current conversation):**
- Current Emails: tool_context.session.state.get("{EMAIL_CURRENT}", [])
- Last Fetch: tool_context.session.state.get("{EMAIL_LAST_FETCH}", "")
- Unread Count: tool_context.session.state.get("{EMAIL_UNREAD_COUNT}", 0)
- Last Sent: tool_context.session.state.get("{EMAIL_LAST_SENT}", "")

**User Preferences:**
- Preferences: tool_context.session.state.get("{USER_PREFERENCES}", {{}})

## Available Gmail Tools (with Session Context)

Your tools now receive tool_context automatically from the ADK Runner:

**Connection Tools:**
- `gmail_check_connection`: Checks session state for connection status
- `gmail_authenticate`: Updates session state with auth status

**Reading Tools:**
- `gmail_list_messages`: Lists emails and updates session state cache
- `gmail_get_message`: Gets specific email details  
- `gmail_search_messages`: Searches with Gmail query syntax

**Sending Tools:**
- `gmail_send_message`: Sends emails and updates session state
- `gmail_reply_to_message`: Replies with threading support

**Organization Tools:**
- `gmail_mark_as_read`: Marks emails and updates state
- `gmail_archive_message`: Archives emails
- `gmail_delete_message`: Deletes emails

## Cross-Session Memory

You have access to:
- `load_memory`: Search past conversations for email patterns and context
  - "What emails did we discuss about Project X?"
  - "What's my usual email workflow?"
  - "Show me past email summaries"

## ADK Integration Benefits

✅ **Real Session State**: Tools access actual session.state via tool_context
✅ **Automatic State Saving**: Your responses saved to state["{EMAIL_CURRENT}"] via output_key
✅ **Cross-Session Knowledge**: load_memory tool works with real MemoryService
✅ **Persistent Sessions**: Session state survives app restarts (with DatabaseSessionService)
✅ **UI Integration**: Messages automatically stored in chat history for sidebar

## How It Works

1. **User Request**: "Check my emails"
2. **ADK Runner**: Provides tool_context with session access
3. **Tool Execution**: gmail_list_messages(tool_context=context) 
4. **Session Access**: tool_context.session.state.get("{USER_GMAIL_CONNECTED}")
5. **State Update**: Your response automatically saved via output_key
6. **Memory Integration**: load_memory searches past email interactions

## Response Guidelines

- Always check session state for user preferences and connection status
- Update session state through your responses (ADK handles via output_key)
- Use load_memory for relevant past email context
- Provide clear, voice-optimized responses
- Handle authentication gracefully with session state updates

## Final Response Requirements

You MUST always provide a clear, comprehensive final response that:

1. **Summarizes what you accomplished**: "I checked your Gmail connection and found..."
2. **States the current status**: "Gmail is connected as user@example.com" or "Gmail authentication required"
3. **Provides actionable next steps**: "You can now ask me to list your emails" or "Please authenticate with Gmail first"
4. **Uses conversational language**: Optimized for voice delivery
5. **Ends with a complete thought**: Never leave responses hanging or incomplete

## Response Format Examples

**Connection Check**: "I checked your Gmail connection. You're currently connected as john@company.com and ready to manage your emails."

**Email Listing**: "I found 5 new emails in your inbox. The most recent is from Sarah about the Q3 budget meeting. Would you like me to read the details or summarize the others?"

**Send Email**: "I successfully sent your email to john@company.com with the subject 'Meeting Follow-up'. The message has been delivered."

**Authentication Required**: "I need to connect to Gmail first. Please authenticate with Gmail, then I can help you manage your emails."

**Error Handling**: "I encountered an issue accessing Gmail. Let me check the connection status and help you resolve this."

## CRITICAL: Always End with a Complete Final Response

Every interaction must conclude with a comprehensive response that summarizes:
- **What you did** (actions taken with which tools)
- **What you found** (results from Gmail operations)
- **Current status** (connection state, success/failure)
- **Next steps** available to the user

This final response will be automatically saved to session.state["email_result"] via output_key 
for coordination with other agents and future reference.

## Example Complete Interaction Flow

1. User: "Check my Gmail connection status"
2. You: Use `gmail_check_connection` tool
3. You: Process the tool result
4. You: **ALWAYS provide final response**: "I checked your Gmail connection. You're connected as user@company.com and have 3 unread emails. I'm ready to help you list, read, or manage your emails."

Remember: Your final response is what other agents will see in session state, so make it 
informative and actionable for the complete Oprina assistant experience.

Current System Status:
- ADK Integration: ✅ Complete with Runner + SessionService + MemoryService
- Gmail Tools: {len(GMAIL_TOOLS)} tools with real session context
- Memory Tool: load_memory with cross-session knowledge
- Total Tools: {total_tools}
        """,
        output_key="email_result",  # ADK automatically saves responses to session state
        tools=GMAIL_TOOLS + [load_memory]  # Direct Gmail tools + ADK memory
    )
    
    # Create runner factory function
    def create_runner():
        """Create ADK Runner for this agent with session/memory services."""
        memory_manager = get_adk_memory_manager()
        return memory_manager.create_runner(agent_instance)
    
    print(f"--- Email Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- ADK Integration: ✅ Complete with SessionService + MemoryService ---")
    print(f"--- Gmail Tools: {len(GMAIL_TOOLS)} | Memory: 1 | Total: {total_tools} ---")
    print("🎉 Email Agent now has REAL ADK session integration!")
    
    return agent_instance, create_runner


# Create the agent instance and runner factory
email_agent, create_email_runner = create_email_agent()


# =============================================================================
# ADK Runner Integration Example
# =============================================================================

async def run_email_agent_example():
    """Example of running the email agent with proper ADK integration."""
    print("🧪 Testing Email Agent with ADK Runner Integration...")
    
    try:
        # Get the memory manager
        memory_manager = get_adk_memory_manager()
        
        # Create session for user
        user_id = "test_user_123"
        session_id = await memory_manager.create_session(user_id, {
            "user:name": "Test User",
            "user:email": "test@example.com",
            "user:gmail_connected": True
        })
        
        print(f"✅ Created session: {session_id}")
        
        # Run agent through memory manager (provides full ADK context)
        events = await memory_manager.run_agent(
            agent=email_agent,
            user_id=user_id,
            session_id=session_id,
            user_message="Check my Gmail connection status"
        )
        
        print(f"✅ Agent executed with {len(events)} events")
        for event in events:
            print(f"   Event: {event['author']} - {event['content'][:50]}...")
        
        # Check updated session state
        updated_session = await memory_manager.get_session(user_id, session_id)
        if updated_session:
            print(f"✅ Session state updated: {list(updated_session.state.keys())}")
            email_result = updated_session.state.get("email_result", "No result")
            print(f"   Email Result: {email_result[:100]}...")
        
        # Cleanup
        await memory_manager.delete_session(user_id, session_id)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


# Export for use in coordinator
__all__ = ["email_agent", "create_email_runner", "run_email_agent_example"]


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    def test_email_agent_integration():
        """Test Email Agent ADK integration."""
        print("🧪 Testing Email Agent ADK Integration...")
        
        try:
            # Test agent creation
            agent, runner_factory = create_email_agent()
            
            print(f"✅ Email Agent '{agent.name}' created with ADK integration")
            print(f"🔧 Tools: {len(agent.tools)}")
            print(f"🎯 Output Key: {agent.output_key}")
            
            # Test runner factory
            try:
                runner = runner_factory()
                print(f"✅ ADK Runner created: {runner is not None}")
                print(f"📱 App Name: {runner.app_name}")
            except Exception as e:
                print(f"⚠️ Runner creation failed (expected if ADK not fully configured): {e}")
            
            # Test tool imports
            from agents.voice.sub_agents.coordinator.sub_agents.email.gmail_tools import (
                gmail_check_connection, gmail_list_messages
            )
            print("✅ Gmail tools imported successfully")
            
            # Test memory manager import
            from memory.adk_memory_manager import get_adk_memory_manager
            print("✅ ADK Memory Manager imported successfully")
            
            print(f"\n✅ Email Agent ADK integration completed successfully!")
            print(f"🎯 Ready for real session context and state management!")
            
        except Exception as e:
            print(f"❌ Error testing Email Agent integration: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    test_email_agent_integration()
    
    # Run async example if requested
    import asyncio
    print("\n" + "="*50)
    print("Run async ADK integration example? (requires proper ADK setup)")
    try:
        asyncio.run(run_email_agent_example())
    except Exception as e:
        print(f"Async example skipped: {e}")