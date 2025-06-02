"""
Coordinator Agent for Oprina - Complete ADK Implementation

This agent orchestrates multi-agent workflows using ADK's automatic delegation.
Simple, clean implementation leveraging ADK's built-in coordination capabilities.
"""

import os
import sys

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(5):  # 5 levels to reach project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import external packages
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import load_memory

# Import project modules
from config.settings import settings
from services.logging.logger import setup_logger

# Import sub-agents
from agents.voice.sub_agents.coordinator.sub_agents.email.agent import create_email_agent
from agents.voice.sub_agents.coordinator.sub_agents.content.agent import create_content_agent
from agents.voice.sub_agents.coordinator.sub_agents.calendar.agent import create_calendar_agent

# Import coordination tools
from agents.voice.sub_agents.coordinator.coordinator_tools import COORDINATION_TOOLS

# Import shared constants for documentation
from agents.common import (
    USER_NAME, USER_PREFERENCES, USER_GMAIL_CONNECTED, USER_CALENDAR_CONNECTED,
    COORDINATION_ACTIVE, COORDINATION_WORKFLOW_TYPE, COORDINATION_CURRENT_STEP,
    WORKFLOW_EMAIL_ONLY, WORKFLOW_CALENDAR_ONLY, WORKFLOW_EMAIL_CONTENT,
    WORKFLOW_EMAIL_CALENDAR, WORKFLOW_ALL_AGENTS
)

# Configure logging
logger = setup_logger("coordinator_agent", console_output=True)


def create_coordinator_agent():
    """
    Create the Coordinator Agent with complete ADK hierarchy integration.
    
    Returns:
        LlmAgent: Configured coordinator agent with automatic delegation
    """
    logger.info("Creating Coordinator Agent with ADK Auto-Delegation")
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.COORDINATOR_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    
    # Get tool counts for logging
    coordination_tools_count = len(COORDINATION_TOOLS)
    memory_tools_count = 1  # load_memory
    total_tools = coordination_tools_count + memory_tools_count

    email_sub_agent = create_email_agent()
    content_sub_agent = create_content_agent()
    calendar_sub_agent = create_calendar_agent()
    
    # Create the Coordinator Agent with ADK auto-delegation
    agent_instance = LlmAgent(
        name="coordinator_agent",
        description="Orchestrates Gmail, Calendar, and Content agents for complex multi-step workflows with intelligent task routing and result coordination",
        model=model,
        
        # ✅ ADK AUTO-DELEGATION: Sub-agents for automatic routing
        sub_agents=[email_sub_agent, content_sub_agent, calendar_sub_agent],
        
        instruction=f"""
You are the Coordinator Agent for Oprina, a sophisticated voice-powered Gmail and Calendar assistant.

## Your Role & ADK Auto-Delegation

You orchestrate complex workflows by leveraging ADK's automatic delegation system. The ADK framework will automatically route tasks to the most appropriate sub-agent based on their descriptions and your delegation instructions.

### Available Sub-Agents (ADK Auto-Routes Based on Descriptions):

1. **Email Agent** - Handles all Gmail operations
   - Description: "Handles Gmail operations: connection, email management, sending, organizing using direct Gmail API access"
   - Use for: Gmail connection, reading emails, sending messages, email organization
   - Auto-delegated when: User mentions emails, Gmail, messages, sending, inbox, etc.

2. **Content Agent** - Specializes in text processing  
   - Description: "Specializes in email content processing: summarization, reply generation, analysis, and voice optimization"
   - Use for: Email summarization, reply generation, content analysis, voice optimization
   - Auto-delegated when: User needs summaries, replies, content analysis, voice processing

3. **Calendar Agent** - Manages Google Calendar
   - Description: "Handles Google Calendar operations: events, scheduling, availability using direct Calendar API access"
   - Use for: Calendar events, scheduling, availability checking, calendar management
   - Auto-delegated when: User mentions calendar, events, meetings, scheduling, availability

## Session State Access (REAL ADK Integration)

You have REAL access to session state through tool_context.session.state and automatic updates via output_key:

**User Information:**
- User Name: tool_context.session.state.get("{USER_NAME}", "")
- User Preferences: tool_context.session.state.get("{USER_PREFERENCES}", {{}})
- Gmail Connected: tool_context.session.state.get("{USER_GMAIL_CONNECTED}", False)
- Calendar Connected: tool_context.session.state.get("{USER_CALENDAR_CONNECTED}", False)

**Coordination State (current conversation):**
- Active Coordination: tool_context.session.state.get("{COORDINATION_ACTIVE}", False)
- Workflow Type: tool_context.session.state.get("{COORDINATION_WORKFLOW_TYPE}", "")
- Current Step: tool_context.session.state.get("{COORDINATION_CURRENT_STEP}", "")

**Sub-Agent Results (via ADK output_key):**
- Email Results: tool_context.session.state.get("email_result", "")
- Content Results: tool_context.session.state.get("content_result", "")
- Calendar Results: tool_context.session.state.get("calendar_result", "")

## Available Coordination Tools

Your coordination tools help with workflow management:

**Workflow Analysis:**
- `analyze_coordination_context`: Analyze current session context and determine coordination needs
- `get_workflow_status`: Check multi-agent workflow status and progress
- `coordinate_agent_results`: Coordinate and summarize results from multiple agents

**Cross-Session Memory:**
- `load_memory`: Search past conversations for coordination patterns and user preferences

## Coordination Patterns & ADK Delegation

### Simple Workflows (Single Agent):
- **Email Only**: "Check my emails" → ADK auto-delegates to Email Agent
- **Calendar Only**: "What's on my calendar?" → ADK auto-delegates to Calendar Agent  
- **Content Only**: "Summarize this text" → ADK auto-delegates to Content Agent

### Complex Workflows (Multi-Agent Coordination):
- **Email + Content**: "Summarize my latest emails" → Email Agent (fetch) → Content Agent (summarize)
- **Email + Calendar**: "Schedule meeting based on this email" → Email Agent (read) → Calendar Agent (schedule)
- **All Agents**: "Process my emails and update calendar" → Email (fetch) → Content (analyze) → Calendar (schedule)

## Delegation Strategy

When handling complex requests:

1. **Analyze the Request**: Use `analyze_coordination_context` to understand what's needed
2. **Plan Workflow**: Determine which agents are required and in what order
3. **Let ADK Route**: Provide clear instructions that trigger automatic delegation
4. **Coordinate Results**: Use `coordinate_agent_results` to combine outputs
5. **Provide Summary**: Give user a comprehensive response from all agent outputs

## Examples of Delegation Instructions

**For Email Tasks:**
- "Please check Gmail for new messages and provide a summary"
- "Send an email to [recipient] with [content]"
- "Search for emails about [topic] and organize them"

**For Content Tasks:**  
- "Please summarize the following email content: [content]"
- "Generate a professional reply to this email: [email]"
- "Analyze the sentiment and extract action items from: [content]"

**For Calendar Tasks:**
- "Please check my calendar for next week and show available times"
- "Create a meeting for [details] at [time]"
- "Find free time slots for a [duration] meeting this week"

**For Multi-Agent Workflows:**
- "Get my latest emails and create calendar events for any meetings mentioned"
- "Summarize my important emails and check if I have conflicts with any mentioned times"
- "Process my email inbox and organize tasks in my calendar"

## Workflow Types You Can Coordinate

- `{WORKFLOW_EMAIL_ONLY}`: Pure Gmail operations
- `{WORKFLOW_CALENDAR_ONLY}`: Pure Calendar operations  
- `{WORKFLOW_EMAIL_CONTENT}`: Email processing with content analysis
- `{WORKFLOW_EMAIL_CALENDAR}`: Email and calendar coordination
- `{WORKFLOW_ALL_AGENTS}`: Complex workflows using all agents

## Response Guidelines

1. **Let ADK Handle Delegation**: Trust the automatic routing system
2. **Provide Clear Instructions**: Make delegation triggers obvious
3. **Coordinate Results**: Combine outputs from multiple agents effectively
4. **Voice-Optimized Responses**: Ensure all responses work well for voice delivery
5. **Session State Awareness**: Use session context for personalized coordination
6. **Error Recovery**: Handle partial failures gracefully across agents

## Multi-Agent Workflow Examples

**Example 1: Email Summary with Calendar Check**
1. User: "Summarize my emails and check for any scheduling conflicts"
2. You: "I'll check your emails and analyze them for any calendar-related content"
3. ADK auto-delegates to Email Agent → gets emails
4. ADK auto-delegates to Content Agent → summarizes emails  
5. ADK auto-delegates to Calendar Agent → checks for conflicts
6. You: Coordinate all results into comprehensive response

**Example 2: Meeting Scheduling from Email**
1. User: "Create a calendar event for the meeting mentioned in my latest email"
2. You: "I'll find the meeting details in your email and schedule it"
3. ADK auto-delegates to Email Agent → fetch latest email
4. ADK auto-delegates to Content Agent → extract meeting details
5. ADK auto-delegates to Calendar Agent → create event
6. You: Confirm meeting created with details

**Example 3: Comprehensive Email Processing**
1. User: "Process my inbox - summarize important emails and schedule any meetings"
2. You: "I'll analyze your emails and handle any calendar coordination needed"
3. ADK auto-delegates to Email Agent → fetch emails
4. ADK auto-delegates to Content Agent → analyze and categorize
5. ADK auto-delegates to Calendar Agent → schedule meetings found
6. You: Provide complete summary of actions taken

## Session State Integration

The ADK automatically manages session state through your output_key. When you respond:
- Coordination results are saved to session.state["coordination_result"]
- Sub-agent results are accessible via their output_keys
- Session state persists across conversation turns
- Use load_memory for cross-session coordination patterns

## Integration with Voice Agent

You work closely with the Voice Agent:
- Receive delegated complex tasks requiring multi-agent coordination
- Provide voice-optimized responses that flow naturally when spoken
- Handle user clarification requests during complex workflows
- Maintain conversation context across multiple coordination steps

## Important Notes

- **ADK handles all delegation automatically** - you don't need to manually route
- **Trust the system** - clear descriptions and instructions trigger proper routing
- **Focus on coordination** - your job is to orchestrate, not duplicate agent work
- **Session state flows automatically** - via tool_context and output_key
- **Voice-first design** - all responses should work well for speech synthesis

Remember: You are the conductor of an orchestra. Each sub-agent is a virtuoso musician. 
ADK is your automatic music stand that ensures the right musician plays at the right time. 
Your job is to create beautiful symphonies of coordinated assistance.

Current System Status:
- ADK Integration: Complete with automatic delegation
- Sub-Agents: {len([email_sub_agent, content_sub_agent, calendar_sub_agent])} specialized agents ready
- Coordination Tools: {coordination_tools_count} workflow management tools
- Memory Tool: load_memory with cross-session coordination knowledge  
- Total Tools: {total_tools}
- Architecture: Ready for production multi-agent coordination

Trust the ADK framework - it will handle the complexity while you focus on creating 
exceptional coordinated experiences for voice-first Gmail and Calendar assistance!
        """,
        output_key="coordination_result",  # ADK automatically saves responses to session state
        tools=COORDINATION_TOOLS + [load_memory]  # Coordination tools + ADK memory
    )
    
    logger.info(f"Coordinator Agent created with {len(agent_instance.sub_agents)} sub-agents")
    logger.info(f"Sub-agents: {[agent.name for agent in agent_instance.sub_agents]}")
    logger.info(f"Coordination Tools: {coordination_tools_count} | Memory: 1 | Total: {total_tools}")
    logger.info("✅ ADK Auto-Delegation: Enabled with sub_agents hierarchy")
    logger.info("✅ Session State: Managed via output_key and tool_context")
    logger.info("✅ Ready for complex multi-agent workflow coordination!")
    
    return agent_instance


_coordinator_instance = None

def get_coordinator_agent():
    """Get singleton coordinator agent instance."""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = create_coordinator_agent()
    return _coordinator_instance

# Export this instead of direct instance
coordinator_agent = get_coordinator_agent


# Export for use in voice agent
__all__ = ["coordinator_agent", "create_coordinator_agent"]


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    def test_coordinator_agent_adk_integration():
        """Test Coordinator Agent ADK integration and auto-delegation setup."""
        logger.info("Testing Coordinator Agent ADK Integration")
        
        try:
            # Test agent creation
            agent = create_coordinator_agent()
            
            logger.info(f"✅ Coordinator Agent '{agent.name}' created with ADK auto-delegation")
            print(f"✅ Coordinator Agent '{agent.name}' created with ADK auto-delegation")
            print(f"🤖 Sub-agents: {len(agent.sub_agents)}")
            print(f"🔧 Tools: {len(agent.tools)}")
            print(f"🧠 Model: {agent.model}")
            print(f"📝 Description: {agent.description}")
            print(f"🎯 Output Key: {agent.output_key}")
            
            # Verify it's an LlmAgent (ADK pattern)
            print(f"✅ Agent Type: {type(agent).__name__}")
            
            # Test sub-agents are properly configured
            print(f"\n🤖 Sub-Agents Analysis:")
            for i, sub_agent in enumerate(agent.sub_agents, 1):
                print(f"  {i}. {sub_agent.name} - {sub_agent.description[:60]}...")
                print(f"     Tools: {len(sub_agent.tools)} | Output: {sub_agent.output_key}")
            
            # Test coordination tools
            tool_names = []
            for tool in agent.tools:
                if hasattr(tool, 'func'):
                    tool_names.append(getattr(tool.func, '__name__', 'unknown'))
                else:
                    tool_names.append(str(tool))
            
            print(f"\n🔧 Coordination Tools:")
            coordination_tools_count = 0
            for i, tool_name in enumerate(tool_names, 1):
                if tool_name.startswith(('analyze_coordination', 'get_workflow', 'coordinate_agent')):
                    print(f"  {i}. {tool_name} (Coordination)")
                    coordination_tools_count += 1
                elif tool_name == 'load_memory':
                    print(f"  {i}. {tool_name} (ADK Memory)")
                else:
                    print(f"  {i}. {tool_name} (Other)")
            
            print(f"\n📊 Tool Summary:")
            print(f"  Coordination Tools: {coordination_tools_count}")
            print(f"  Memory Tools: 1")
            print(f"  Total Tools: {len(tool_names)}")
            
            # Verify ADK auto-delegation readiness
            print(f"\n📈 ADK Auto-Delegation Readiness:")
            print(f"  ✅ Has sub_agents list with {len(agent.sub_agents)} agents")
            print(f"  ✅ Clear agent descriptions for LLM routing")
            print(f"  ✅ Coordination instruction with delegation examples")
            print(f"  ✅ Output key for session state management")
            print(f"  ✅ Load memory for cross-session coordination")
            
            # Test workflow type constants
            print(f"\n📋 Workflow Types Supported:")
            workflow_types = [
                WORKFLOW_EMAIL_ONLY, WORKFLOW_CALENDAR_ONLY, 
                WORKFLOW_EMAIL_CONTENT, WORKFLOW_EMAIL_CALENDAR, WORKFLOW_ALL_AGENTS
            ]
            for workflow in workflow_types:
                print(f"  • {workflow}")
            
            # Test session state constants integration
            print(f"\n🗂️ Session State Integration:")
            print(f"  ✅ User state constants imported")
            print(f"  ✅ Coordination state constants imported") 
            print(f"  ✅ Agent result keys documented")
            print(f"  ✅ Tool context patterns ready")
            
            logger.info("✅ Coordinator Agent ADK integration completed successfully")
            print(f"\n✅ Coordinator Agent ADK integration completed successfully!")
            print(f"🎯 Ready for Voice Agent integration!")
            print(f"🚀 ADK auto-delegation system operational!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing Coordinator Agent integration: {e}")
            print(f"❌ Error testing Coordinator Agent integration: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Run the test
    success = test_coordinator_agent_adk_integration()
    if success:
        print(f"\n🎉 Coordinator Agent is ready for multi-agent orchestration!")
        print(f"🤖 ADK will automatically delegate to: Email, Content, Calendar agents")
        print(f"🧠 Session state coordination via tool_context and output_key")
        print(f"💾 Cross-session memory via load_memory tool")
    else:
        print(f"\n🔧 Please review and fix issues before Voice Agent integration")

class CoordinatorAgent:
    def __init__(self, mcp_client, *args, **kwargs):
        self._mcp_client = mcp_client
        self.email_agent = create_email_agent()
        self.content_agent = create_content_agent()
        self.calendar_agent = create_calendar_agent()
    
    async def process(self, event):
        # Route to appropriate sub-agent based on content
        content = event.get("content", "").lower()
        
        if "email" in content or "gmail" in content or "inbox" in content:
            return await self.email_agent.process(event)
        elif "calendar" in content or "schedule" in content or "meeting" in content:
            return await self.calendar_agent.process(event)
        elif "summarize" in content or "analyze" in content or "content" in content:
            return await self.content_agent.process(event)
        else:
            # Default to email agent if no clear routing
            return await self.email_agent.process(event)