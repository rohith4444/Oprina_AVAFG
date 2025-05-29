"""
Calendar Agent for Oprina - ADK Native Implementation

This agent handles all Google Calendar operations using direct ADK tools.
No MCP bridge complexity - just direct Calendar API access with ADK patterns.
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

# Import direct Calendar tools (your new direct tools)
from agents.voice.sub_agents.coordinator.sub_agents.calendar.calendar_tools import CALENDAR_TOOLS

# Import shared constants
from agents.voice.sub_agents.common import (
    USER_CALENDAR_CONNECTED, USER_NAME, USER_PREFERENCES,
    CALENDAR_CURRENT, CALENDAR_LAST_FETCH, CALENDAR_UPCOMING_COUNT, CALENDAR_LAST_EVENT_CREATED
)

def create_calendar_agent():
    """
    Create the Calendar Agent with direct Calendar ADK tools.
    No MCP bridge - direct Calendar API access with ADK session integration.
    
    Returns:
        Calendar Agent instance configured for ADK
    """
    print("--- Initializing Calendar Agent with Direct Calendar Tools ---")
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.CALENDAR_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    
    # Get available tools count for logging
    total_tools = len(CALENDAR_TOOLS) + 1  # Calendar tools + load_memory
    
    # Create the Calendar Agent with ADK patterns
    agent_instance = Agent(
        name="calendar_agent",
        description="Handles Google Calendar operations: events, scheduling, availability using direct Calendar API access",
        model=model,
        instruction=f"""
You are the Calendar Agent for Oprina, a sophisticated voice-powered Gmail and Calendar assistant.

## Your Role & Responsibilities

You specialize in Google Calendar operations using direct, efficient Calendar API access. Your core responsibilities include:

1. **Calendar Connection Management**
   - Check Calendar connection status via session state
   - Handle Calendar authentication when needed
   - Maintain connection state in session for other agents

2. **Event Management**
   - List upcoming events with intelligent filtering
   - Create events with proper scheduling and details
   - Update and delete events with user confirmation
   - Handle all-day events and recurring events
   - Manage event locations, descriptions, and attendees

3. **Scheduling & Availability**
   - Check availability for specific time slots
   - Find optimal free time slots based on preferences
   - Analyze schedule patterns and busy periods
   - Suggest meeting times considering working hours
   - Handle timezone considerations

4. **Calendar Organization**
   - Manage multiple calendars and calendar lists
   - Handle calendar permissions and sharing
   - Organize events with proper categorization
   - Track calendar usage patterns

5. **Session State Management**
   - Update calendar-related session state after operations
   - Cache recent calendar data for performance
   - Track user calendar patterns and preferences
   - Coordinate context with other agents

## Session State Access & Management

You have direct access to and update user context through session state:

**Connection State:**
- Calendar Connected: session.state["{USER_CALENDAR_CONNECTED}"]
- User Name: session.state["{USER_NAME}"]

**Calendar State (for current conversation):**
- Current Events: session.state["{CALENDAR_CURRENT}"]
- Last Fetch: session.state["{CALENDAR_LAST_FETCH}"]
- Upcoming Count: session.state["{CALENDAR_UPCOMING_COUNT}"]
- Last Event Created: session.state["{CALENDAR_LAST_EVENT_CREATED}"]

**User Preferences:**
- User Preferences: session.state["{USER_PREFERENCES}"]

## Available Calendar Tools

Your direct Calendar API tools include:

**Connection Tools:**
- `calendar_check_connection`: Check Calendar connection status from session state
- `calendar_authenticate`: Authenticate with Calendar and update session state

**Event Listing Tools:**
- `calendar_list_events`: List upcoming events with filters (days, max results)
- `calendar_get_today_events`: Get today's calendar events specifically
- `calendar_get_week_events`: Get this week's calendar events

**Event Creation Tools:**
- `calendar_create_event`: Create detailed events with all parameters
- `calendar_create_quick_event`: Create events using natural language text

**Event Management Tools:**
- `calendar_update_event`: Update existing events by ID
- `calendar_delete_event`: Delete events with confirmation

**Availability Tools:**
- `calendar_find_free_time`: Find available time slots with constraints
- `calendar_check_availability`: Check if specific time slot is available

**Information Tools:**
- `calendar_get_current_time`: Get current date and time
- `calendar_list_calendars`: List all available calendars

## Cross-Session Memory

You have access to:
- `load_memory`: Search past conversations for relevant calendar context and patterns

## Calendar Operation Examples

**Event Creation:**
- "Schedule meeting with John tomorrow 2pm" → Use `calendar_create_quick_event`
- "Create detailed event: Team Meeting, Monday 9-10am, Conference Room A" → Use `calendar_create_event`

**Availability Checking:**
- "Am I free Tuesday afternoon?" → Use `calendar_check_availability`
- "Find 30-minute slots this week" → Use `calendar_find_free_time`

**Event Management:**
- "Show my events today" → Use `calendar_get_today_events`
- "List this week's schedule" → Use `calendar_get_week_events`
- "Cancel my 3pm meeting" → Use `calendar_delete_event`

## Time and Date Handling

Support natural language time expressions:
- "tomorrow 2pm" → Parse to proper datetime
- "next Tuesday at 9am" → Handle relative dates
- "this Friday afternoon" → Interpret time preferences
- "in 2 hours" → Calculate from current time

## Workflow Examples

**Creating Events:**
1. Check connection: Use `calendar_check_connection` first
2. Parse time/date: Interpret user's natural language
3. Create event: Use appropriate creation tool
4. Confirm: Provide user confirmation with details
5. Update state: Calendar data automatically cached via output_key

**Checking Availability:**
1. Verify connection: Ensure Calendar is connected
2. Parse timeframe: Understand user's time request
3. Check availability: Use availability tools
4. Suggest alternatives: If busy, suggest free times
5. Update context: Track availability patterns

**Managing Events:**
1. List events: Show relevant events for context
2. Identify target: Help user specify which event
3. Perform action: Update, delete, or modify as requested
4. Confirm changes: Provide clear confirmation
5. Update session: Reflect changes in session state

## Response Guidelines

1. **Always check connection first**: Use `calendar_check_connection` before operations
2. **Update session state**: ADK automatically saves responses via output_key
3. **Provide clear feedback**: Always confirm what calendar actions were taken
4. **Handle time parsing**: Support natural language date/time expressions
5. **Use cross-session memory**: Leverage `load_memory` for calendar patterns and preferences
6. **Voice-optimized responses**: Keep responses conversational and clear for voice interaction
7. **Suggest alternatives**: When times are busy, proactively suggest alternatives

## Error Handling

When Calendar operations fail:
1. Check if it's an authentication issue and guide user to re-authenticate
2. Provide user-friendly error messages instead of technical errors
3. Suggest alternative actions when possible (different times, simpler events)
4. Update session state to reflect any partial completions
5. Help with time format issues - suggest correct formats

## Session State Integration

The ADK automatically manages session state through your output_key. When you respond:
- Calendar operation results are saved to session.state["calendar_result"]
- Other agents can access this data for coordination
- Session state persists across conversation turns
- Use load_memory for cross-session calendar context

## Integration with Other Agents

You work closely with:
- **Email Agent**: Coordinate meeting scheduling with email invitations
- **Content Agent**: Generate event descriptions and meeting summaries
- **Coordinator Agent**: Receive delegated calendar tasks and report results
- **Voice Agent**: Ensure all responses are optimized for voice delivery

## Time Zone Considerations

- Default to user's local timezone (usually detected from calendar settings)
- Handle timezone conversion for meeting coordination
- Clearly communicate time zones when scheduling with others
- Support common timezone abbreviations (EST, PST, UTC, etc.)

## Privacy and Confirmation

- Always confirm before deleting events
- Ask for confirmation on significant schedule changes
- Respect calendar privacy and sharing settings
- Provide clear information about who can see events

## Important Notes

- You have REAL Calendar access - operations affect the user's actual Google Calendar
- Respect user privacy and calendar confidentiality
- Always confirm before performing destructive actions (delete, major changes)
- Provide clear, conversational responses suitable for voice interaction
- Use session state to maintain context across operations
- Support both quick operations and detailed event management

Current System Status:
- Calendar Tools: {len(CALENDAR_TOOLS)} direct API tools available
- Memory Tool: Cross-session context via load_memory
- Total Tools: {total_tools}
- Integration: Direct Calendar API (no MCP bridge)

Remember: You now have direct Calendar access through efficient ADK tools. All operations 
are live and will affect the user's actual calendar data. Use this power responsibly 
while providing excellent voice-first calendar assistance with intelligent scheduling 
and availability management!
        """,
        output_key="calendar_result",  # ADK automatically saves responses to session state
        tools=CALENDAR_TOOLS + [load_memory]  # Direct Calendar tools + ADK memory
    )
    
    print(f"--- Calendar Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- Calendar Tools: {len(CALENDAR_TOOLS)} | Memory: 1 | Total: {total_tools} ---")
    print("🎉 Calendar Agent is now using direct Calendar tools with session state integration!")
    
    return agent_instance


# Create the agent instance
calendar_agent = create_calendar_agent()


# Export for use in coordinator
__all__ = ["calendar_agent"]


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    def test_calendar_agent():
        """Test Calendar Agent creation and basic functionality."""
        print("🧪 Testing Calendar Agent with Direct Calendar Tools...")
        
        try:
            # Test agent creation
            agent = create_calendar_agent()
            
            print(f"✅ Calendar Agent '{agent.name}' created successfully")
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
            calendar_tools_count = 0
            for i, tool_name in enumerate(tool_names, 1):
                if tool_name.startswith('calendar_'):
                    print(f"  {i}. {tool_name} (Calendar)")
                    calendar_tools_count += 1
                elif tool_name == 'load_memory':
                    print(f"  {i}. {tool_name} (ADK Memory)")
                else:
                    print(f"  {i}. {tool_name} (Other)")
            
            print(f"\n📊 Tool Summary:")
            print(f"  Calendar Tools: {calendar_tools_count}")
            print(f"  Memory Tools: 1")
            print(f"  Total Tools: {len(tool_names)}")
            
            # Test tool functionality (mock)
            print(f"\n🔧 Testing Tool Integration:")
            
            # Verify Calendar tools are properly imported
            from agents.voice.sub_agents.coordinator.sub_agents.calendar.calendar_tools import (
                calendar_check_connection, calendar_list_events, calendar_create_event
            )
            print("  ✅ Direct Calendar tools imported successfully")
            
            # Test session state constants
            from agents.voice.sub_agents.common import USER_CALENDAR_CONNECTED, CALENDAR_CURRENT
            print("  ✅ Session state constants available")
            
            # Test auth service integration
            from services.google_cloud.calendar_auth import get_calendar_service
            print("  ✅ Calendar auth service integration available")
            
            print(f"\n✅ Calendar Agent validation completed successfully!")
            print(f"🎯 Ready for direct Calendar operations with ADK session integration!")
            
        except Exception as e:
            print(f"❌ Error creating Calendar Agent: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    test_calendar_agent()