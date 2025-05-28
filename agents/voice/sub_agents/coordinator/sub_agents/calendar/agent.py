# agents/voice/sub_agents/coordinator/sub_agents/calendar/agent.py
"""
Calendar Agent for Oprina

This agent handles all Calendar operations with specialized calendar tools:
- Calendar availability checking with smart analysis
- Event management with context awareness
- Free time finding with user preference learning
- Schedule optimization and conflict resolution
"""

import asyncio
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(7):  # 7 levels to reach project root
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import external packages
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

# Import project modules
from config.settings import settings
from agents.voice.sub_agents.coordinator.sub_agents.calendar.mcp_integration import get_calendar_tools, get_calendar_mcp_status

# Import shared tools
from agents.voice.sub_agents.common.shared_tools import (
    CORE_ADK_TOOLS,
    CONTEXT_ADK_TOOLS,
    LEARNING_ADK_TOOLS,
    # Individual functions needed by our coordinator tools

    get_calendar_context,
    update_calendar_context,
    handle_agent_error,
    log_agent_action,
    measure_performance,
    complete_performance_measurement,
    learn_from_interaction
)

# =============================================================================
# Calendar-Specific Agent Tools
# =============================================================================

def check_calendar_availability(
    date_range: str,
    duration_minutes: int = 60,
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to check calendar availability with smart analysis.
    
    Args:
        date_range: Date range to check (e.g., "today", "this week", "2024-01-15 to 2024-01-20")
        duration_minutes: Duration needed for the meeting/event
        user_id: User identifier for personalization
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Availability analysis with recommendations
    """
    try:
        # Start performance tracking
        perf_result = measure_performance("calendar_availability_check", "calendar_agent", session_id, tool_context)
        tracking_id = perf_result.get("tracking_id")
        
        # Get calendar context
        context_result = get_calendar_context(user_id, session_id, tool_context)
        calendar_context = context_result.get("calendar_context", {})
        
        # Parse date range
        start_date, days = _parse_date_range(date_range)
        
        # Use the MCP calendar tools to find free time
        # This would call the actual MCP tools through the bridge
        from .mcp_integration import calendar_mcp
        
        # Get events for the date range first
        events_result = None
        try:
            # This calls the actual Calendar MCP tool
            if hasattr(calendar_mcp, 'bridge') and calendar_mcp.bridge:
                events_result = calendar_mcp.bridge.mcp_discovery.run_tool(
                    "calendar_list_events",
                    start_date=start_date,
                    days=days
                )
        except Exception as e:
            log_agent_action(
                "calendar_agent",
                "calendar_availability_check_fallback",
                {"error": str(e), "using_mock_data": True},
                session_id,
                tool_context
            )
        
        # Find free time slots
        free_slots_result = None
        try:
            if hasattr(calendar_mcp, 'bridge') and calendar_mcp.bridge:
                free_slots_result = calendar_mcp.bridge.mcp_discovery.run_tool(
                    "calendar_find_free_time",
                    start_date=start_date,
                    days=days,
                    duration_minutes=duration_minutes
                )
        except Exception as e:
            log_agent_action(
                "calendar_agent",
                "free_time_search_fallback",
                {"error": str(e)},
                session_id,
                tool_context
            )
        
        # Analyze availability with business logic
        availability_analysis = _analyze_availability(
            events_result, 
            free_slots_result, 
            duration_minutes,
            calendar_context
        )
        
        # Update calendar context
        update_calendar_context(
            {
                "last_availability_check": datetime.utcnow().isoformat(),
                "checked_date_range": date_range,
                "availability_summary": availability_analysis.get("summary", "")
            },
            user_id,
            session_id,
            tool_context
        )
        
        # Learn from interaction
        learn_from_interaction(
            user_id,
            "availability_check",
            {
                "date_range": date_range,
                "duration_requested": duration_minutes,
                "free_slots_found": len(availability_analysis.get("free_slots", []))
            },
            context={"session_id": session_id},
            tool_context=tool_context
        )
        
        # Complete performance tracking
        if tracking_id:
            complete_performance_measurement(
                tracking_id,
                "success",
                {"slots_analyzed": len(availability_analysis.get("free_slots", []))},
                tool_context
            )
        
        # Log the action
        log_agent_action(
            "calendar_agent",
            "availability_check",
            {
                "date_range": date_range,
                "duration_minutes": duration_minutes,
                "free_slots_found": len(availability_analysis.get("free_slots", []))
            },
            session_id,
            tool_context
        )
        
        return {
            "success": True,
            "availability": availability_analysis,
            "metadata": {
                "date_range_checked": date_range,
                "duration_requested": duration_minutes,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        error_result = handle_agent_error("calendar_agent", e, {
            "operation": "check_calendar_availability",
            "date_range": date_range
        }, session_id, tool_context)
        
        return {
            "success": False,
            "availability": {"free_slots": [], "summary": "Unable to check availability"},
            "error_message": str(e),
            "error_handled": error_result["success"]
        }


def manage_calendar_event(
    action: str,
    event_details: Dict[str, Any],
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to manage calendar events (create, update, delete) with smart handling.
    
    Args:
        action: Action to perform ("create", "update", "delete")
        event_details: Event details (title, start_time, end_time, etc.)
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Event management result
    """
    try:
        # Start performance tracking
        perf_result = measure_performance("calendar_event_management", "calendar_agent", session_id, tool_context)
        tracking_id = perf_result.get("tracking_id")
        
        # Get calendar context for user preferences
        context_result = get_calendar_context(user_id, session_id, tool_context)
        calendar_context = context_result.get("calendar_context", {})
        
        # Apply user preferences to event details
        enhanced_event_details = _apply_user_preferences(event_details, calendar_context)
        
        # Execute the action using MCP tools
        result = None
        try:
            from .mcp_integration import calendar_mcp
            
            if action == "create" and hasattr(calendar_mcp, 'bridge') and calendar_mcp.bridge:
                result = calendar_mcp.bridge.mcp_discovery.run_tool(
                    "calendar_create_event",
                    summary=enhanced_event_details.get("title", "New Event"),
                    start_time=enhanced_event_details.get("start_time", ""),
                    end_time=enhanced_event_details.get("end_time", ""),
                    description=enhanced_event_details.get("description", ""),
                    location=enhanced_event_details.get("location", "")
                )
            elif action == "update" and hasattr(calendar_mcp, 'bridge') and calendar_mcp.bridge:
                result = calendar_mcp.bridge.mcp_discovery.run_tool(
                    "calendar_update_event",
                    event_id=enhanced_event_details.get("event_id", ""),
                    summary=enhanced_event_details.get("title", ""),
                    start_time=enhanced_event_details.get("start_time", ""),
                    end_time=enhanced_event_details.get("end_time", ""),
                    description=enhanced_event_details.get("description", ""),
                    location=enhanced_event_details.get("location", "")
                )
            elif action == "delete" and hasattr(calendar_mcp, 'bridge') and calendar_mcp.bridge:
                result = calendar_mcp.bridge.mcp_discovery.run_tool(
                    "calendar_delete_event",
                    event_id=enhanced_event_details.get("event_id", ""),
                    confirm=enhanced_event_details.get("confirm", False)
                )
        except Exception as e:
            log_agent_action(
                "calendar_agent",
                f"calendar_event_{action}_fallback",
                {"error": str(e)},
                session_id,
                tool_context
            )
        
        # Update calendar context
        update_calendar_context(
            {
                f"last_{action}_event": datetime.utcnow().isoformat(),
                "last_event_action": action,
                "events_modified": calendar_context.get("events_modified", 0) + 1
            },
            user_id,
            session_id,
            tool_context
        )
        
        # Learn from interaction
        learn_from_interaction(
            user_id,
            "calendar_event_action",
            {
                "action": action,
                "event_type": enhanced_event_details.get("title", "unknown"),
                "success": result is not None
            },
            context={"session_id": session_id},
            tool_context=tool_context
        )
        
        # Complete performance tracking
        if tracking_id:
            complete_performance_measurement(
                tracking_id,
                "success" if result else "failure",
                {"action_performed": action},
                tool_context
            )
        
        # Log the action
        log_agent_action(
            "calendar_agent",
            f"calendar_event_{action}",
            {
                "action": action,
                "event_title": enhanced_event_details.get("title", ""),
                "success": result is not None
            },
            session_id,
            tool_context
        )
        
        return {
            "success": result is not None,
            "result": result,
            "action_performed": action,
            "event_details": enhanced_event_details,
            "metadata": {
                "action_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        error_result = handle_agent_error("calendar_agent", e, {
            "operation": "manage_calendar_event",
            "action": action
        }, session_id, tool_context)
        
        return {
            "success": False,
            "result": None,
            "error_message": str(e),
            "error_handled": error_result["success"]
        }


def find_optimal_meeting_time(
    participants: List[str],
    duration_minutes: int,
    date_preferences: str = "this week",
    time_preferences: str = "business hours",
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to find optimal meeting times considering preferences and availability.
    
    Args:
        participants: List of participant emails (for future multi-calendar support)
        duration_minutes: Meeting duration in minutes
        date_preferences: Date preferences ("this week", "next week", specific dates)
        time_preferences: Time preferences ("business hours", "morning", "afternoon")
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Optimal meeting time suggestions
    """
    try:
        # Start performance tracking
        perf_result = measure_performance("optimal_meeting_time", "calendar_agent", session_id, tool_context)
        tracking_id = perf_result.get("tracking_id")
        
        # Get user's calendar preferences
        context_result = get_calendar_context(user_id, session_id, tool_context)
        calendar_context = context_result.get("calendar_context", {})
        
        # Parse preferences
        start_date, days = _parse_date_range(date_preferences)
        time_constraints = _parse_time_preferences(time_preferences, calendar_context)
        
        # Find free time using MCP tools
        free_slots = []
        try:
            from .mcp_integration import calendar_mcp
            
            if hasattr(calendar_mcp, 'bridge') and calendar_mcp.bridge:
                free_time_result = calendar_mcp.bridge.mcp_discovery.run_tool(
                    "calendar_find_free_time",
                    start_date=start_date,
                    days=days,
                    duration_minutes=duration_minutes
                )
                
                if free_time_result and free_time_result.get("status") == "success":
                    free_slots = free_time_result.get("free_slots", [])
        except Exception as e:
            log_agent_action(
                "calendar_agent",
                "optimal_meeting_time_fallback",
                {"error": str(e)},
                session_id,
                tool_context
            )
        
        # Apply intelligent ranking
        ranked_slots = _rank_meeting_slots(
            free_slots, 
            time_constraints, 
            calendar_context,
            participants
        )
        
        # Update calendar context
        update_calendar_context(
            {
                "last_meeting_search": datetime.utcnow().isoformat(),
                "meeting_preferences": {
                    "duration": duration_minutes,
                    "time_pref": time_preferences,
                    "date_pref": date_preferences
                }
            },
            user_id,
            session_id,
            tool_context
        )
        
        # Learn from interaction
        learn_from_interaction(
            user_id,
            "meeting_time_search",
            {
                "duration_requested": duration_minutes,
                "date_preferences": date_preferences,
                "time_preferences": time_preferences,
                "slots_found": len(ranked_slots)
            },
            context={"session_id": session_id},
            tool_context=tool_context
        )
        
        # Complete performance tracking
        if tracking_id:
            complete_performance_measurement(
                tracking_id,
                "success",
                {"optimal_slots_found": len(ranked_slots)},
                tool_context
            )
        
        # Log the action
        log_agent_action(
            "calendar_agent",
            "optimal_meeting_time_search",
            {
                "duration_minutes": duration_minutes,
                "participants_count": len(participants),
                "optimal_slots_found": len(ranked_slots)
            },
            session_id,
            tool_context
        )
        
        return {
            "success": True,
            "optimal_slots": ranked_slots[:5],  # Top 5 recommendations
            "search_criteria": {
                "duration_minutes": duration_minutes,
                "date_preferences": date_preferences,
                "time_preferences": time_preferences,
                "participants": participants
            },
            "metadata": {
                "search_timestamp": datetime.utcnow().isoformat(),
                "total_slots_analyzed": len(free_slots)
            }
        }
        
    except Exception as e:
        error_result = handle_agent_error("calendar_agent", e, {
            "operation": "find_optimal_meeting_time",
            "duration_minutes": duration_minutes
        }, session_id, tool_context)
        
        return {
            "success": False,
            "optimal_slots": [],
            "error_message": str(e),
            "error_handled": error_result["success"]
        }


def analyze_schedule_patterns(
    time_period: str = "last month",
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to analyze user's schedule patterns and provide insights.
    
    Args:
        time_period: Period to analyze ("last week", "last month", "this year")
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Schedule pattern analysis and insights
    """
    try:
        # Start performance tracking
        perf_result = measure_performance("schedule_pattern_analysis", "calendar_agent", session_id, tool_context)
        tracking_id = perf_result.get("tracking_id")
        
        # Parse time period
        start_date, days = _parse_time_period(time_period)
        
        # Get events for analysis
        events = []
        try:
            from .mcp_integration import calendar_mcp
            
            if hasattr(calendar_mcp, 'bridge') and calendar_mcp.bridge:
                events_result = calendar_mcp.bridge.mcp_discovery.run_tool(
                    "calendar_list_events",
                    start_date=start_date,
                    days=days
                )
                
                if events_result and events_result.get("status") == "success":
                    events = events_result.get("events", [])
        except Exception as e:
            log_agent_action(
                "calendar_agent",
                "schedule_analysis_fallback",
                {"error": str(e)},
                session_id,
                tool_context
            )
        
        # Analyze patterns
        pattern_analysis = _analyze_patterns(events, time_period)
        
        # Update calendar context with insights
        update_calendar_context(
            {
                "last_pattern_analysis": datetime.utcnow().isoformat(),
                "schedule_insights": pattern_analysis.get("insights", {}),
                "analysis_period": time_period
            },
            user_id,
            session_id,
            tool_context
        )
        
        # Learn from analysis
        learn_from_interaction(
            user_id,
            "schedule_analysis",
            {
                "time_period": time_period,
                "events_analyzed": len(events),
                "patterns_found": len(pattern_analysis.get("patterns", []))
            },
            context={"session_id": session_id},
            tool_context=tool_context
        )
        
        # Complete performance tracking
        if tracking_id:
            complete_performance_measurement(
                tracking_id,
                "success",
                {"events_analyzed": len(events)},
                tool_context
            )
        
        # Log the action
        log_agent_action(
            "calendar_agent",
            "schedule_pattern_analysis",
            {
                "time_period": time_period,
                "events_analyzed": len(events),
                "insights_generated": len(pattern_analysis.get("insights", {}))
            },
            session_id,
            tool_context
        )
        
        return {
            "success": True,
            "analysis": pattern_analysis,
            "metadata": {
                "time_period_analyzed": time_period,
                "events_count": len(events),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        error_result = handle_agent_error("calendar_agent", e, {
            "operation": "analyze_schedule_patterns",
            "time_period": time_period
        }, session_id, tool_context)
        
        return {
            "success": False,
            "analysis": {"patterns": [], "insights": {}},
            "error_message": str(e),
            "error_handled": error_result["success"]
        }


# =============================================================================
# Helper Functions for Business Logic
# =============================================================================

def _parse_date_range(date_range: str) -> Tuple[str, int]:
    """Parse natural language date range into start date and days."""
    today = datetime.now()
    
    if "today" in date_range.lower():
        return today.strftime("%Y-%m-%d"), 1
    elif "tomorrow" in date_range.lower():
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d"), 1
    elif "this week" in date_range.lower():
        return today.strftime("%Y-%m-%d"), 7
    elif "next week" in date_range.lower():
        next_week = today + timedelta(days=7)
        return next_week.strftime("%Y-%m-%d"), 7
    elif "this month" in date_range.lower():
        return today.strftime("%Y-%m-%d"), 30
    else:
        # Default to today
        return today.strftime("%Y-%m-%d"), 1


def _parse_time_period(time_period: str) -> Tuple[str, int]:
    """Parse time period for analysis."""
    today = datetime.now()
    
    if "last week" in time_period.lower():
        start = today - timedelta(days=7)
        return start.strftime("%Y-%m-%d"), 7
    elif "last month" in time_period.lower():
        start = today - timedelta(days=30)
        return start.strftime("%Y-%m-%d"), 30
    elif "this year" in time_period.lower():
        start = datetime(today.year, 1, 1)
        days = (today - start).days
        return start.strftime("%Y-%m-%d"), days
    else:
        # Default to last week
        start = today - timedelta(days=7)
        return start.strftime("%Y-%m-%d"), 7


def _analyze_availability(events_result, free_slots_result, duration_minutes, calendar_context):
    """Analyze availability with business logic."""
    analysis = {
        "free_slots": [],
        "busy_periods": [],
        "recommendations": [],
        "summary": ""
    }
    
    # Process free slots if available
    if free_slots_result and free_slots_result.get("status") == "success":
        analysis["free_slots"] = free_slots_result.get("free_slots", [])
    
    # Generate summary
    slot_count = len(analysis["free_slots"])
    if slot_count == 0:
        analysis["summary"] = f"No {duration_minutes}-minute slots available in the specified period"
    else:
        analysis["summary"] = f"Found {slot_count} available {duration_minutes}-minute slots"
    
    return analysis


def _apply_user_preferences(event_details, calendar_context):
    """Apply user preferences to event details."""
    enhanced_details = event_details.copy()
    
    # Get calendar preferences
    preferences = calendar_context.get("calendar_preferences", {})
    
    # Apply default duration if not specified
    if "end_time" not in enhanced_details and "start_time" in enhanced_details:
        default_duration = preferences.get("default_event_duration", 60)
        # Add logic to calculate end_time based on duration
    
    # Apply default calendar
    if "calendar_id" not in enhanced_details:
        enhanced_details["calendar_id"] = preferences.get("default_calendar_id", "primary")
    
    return enhanced_details


def _parse_time_preferences(time_preferences, calendar_context):
    """Parse time preferences into constraints."""
    preferences = calendar_context.get("calendar_preferences", {})
    
    constraints = {
        "start_hour": preferences.get("working_hours_start", 9),
        "end_hour": preferences.get("working_hours_end", 17),
        "preferred_times": []
    }
    
    if "morning" in time_preferences.lower():
        constraints["preferred_times"] = ["09:00", "10:00", "11:00"]
    elif "afternoon" in time_preferences.lower():
        constraints["preferred_times"] = ["13:00", "14:00", "15:00", "16:00"]
    
    return constraints


def _rank_meeting_slots(free_slots, time_constraints, calendar_context, participants):
    """Rank meeting slots by preference and optimization."""
    if not free_slots:
        return []
    
    # Simple ranking - prefer earlier times within business hours
    ranked_slots = []
    for slot in free_slots:
        score = 100  # Base score
        
        # Prefer business hours
        slot_time = slot.get("start", "")
        if "09:" in slot_time or "10:" in slot_time:
            score += 20
        elif "14:" in slot_time or "15:" in slot_time:
            score += 15
        
        ranked_slots.append({**slot, "preference_score": score})
    
    # Sort by score descending
    return sorted(ranked_slots, key=lambda x: x.get("preference_score", 0), reverse=True)


def _analyze_patterns(events, time_period):
    """Analyze schedule patterns from events."""
    analysis = {
        "patterns": [],
        "insights": {},
        "recommendations": []
    }
    
    if not events:
        analysis["insights"]["event_count"] = 0
        analysis["recommendations"].append("Your calendar appears to be light - consider scheduling regular focused work time")
        return analysis
    
    # Basic pattern analysis
    analysis["insights"]["event_count"] = len(events)
    analysis["insights"]["average_events_per_day"] = len(events) / 7  # Assuming weekly analysis
    
    # Generate simple recommendations
    if len(events) > 35:  # More than 5 per day average
        analysis["recommendations"].append("Your calendar seems quite busy - consider blocking time for focused work")
    elif len(events) < 7:  # Less than 1 per day average
        analysis["recommendations"].append("You have a light schedule - great for deep work and planning")
    
    return analysis


# Create calendar-specific tools
calendar_agent_tools = [
    FunctionTool(func=check_calendar_availability),
    FunctionTool(func=manage_calendar_event),
    FunctionTool(func=find_optimal_meeting_time),
    FunctionTool(func=analyze_schedule_patterns)
]


async def create_calendar_agent() -> Tuple[Agent, Optional[object]]:
    """
    Create the Calendar Agent with specialized calendar tools.
    
    Returns:
        Tuple of (agent_instance, exit_stack) for proper cleanup
    """
    print("--- Initializing Calendar Agent with Specialized Tools ---")
    
    # Get Calendar MCP tools from bridge
    calendar_mcp_tools, exit_stack = await get_calendar_tools()
    
    # Get MCP connection status for agent instructions
    mcp_status = get_calendar_mcp_status()
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.CALENDAR_MODEL if hasattr(settings, 'CALENDAR_MODEL') else settings.ADK_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    
    # Determine tools status for instructions
    tools_status = "REAL Calendar tools via MCP Bridge" if mcp_status["connected"] else "No tools available"
    total_tools = len(calendar_mcp_tools) + len(calendar_agent_tools) + 6  # MCP + Agent + Shared tools
    
    # Create the Calendar Agent
    agent_instance = Agent(
        name="calendar_agent",
        description="Handles Calendar operations with intelligent scheduling, availability checking, and event management",
        model=model,
        instruction=f"""
You are the Calendar Agent for Oprina, a sophisticated voice-powered Gmail and Calendar assistant.

## Your Role & Responsibilities

You specialize in Calendar operations with intelligent business logic. Your core responsibilities include:

1. **Smart Availability Checking**
   - Use `check_calendar_availability` to analyze availability with context
   - Consider user preferences, working hours, and scheduling patterns
   - Provide intelligent recommendations based on calendar analysis

2. **Intelligent Event Management**
   - Use `manage_calendar_event` for create/update/delete operations
   - Apply user preferences and smart defaults
   - Handle conflicts and suggest alternatives

3. **Optimal Meeting Scheduling**
   - Use `find_optimal_meeting_time` for intelligent meeting scheduling
   - Consider participant preferences and time zone differences
   - Rank meeting slots by optimization criteria

4. **Schedule Analysis & Insights**
   - Use `analyze_schedule_patterns` to provide schedule insights
   - Identify patterns, busy periods, and optimization opportunities
   - Suggest schedule improvements and time management tips

## Current System Status

- Calendar Tools Status: {tools_status}
- Available Tools: {len(calendar_mcp_tools)} MCP + {len(calendar_agent_tools)} Agent + 6 Shared = {total_tools} total
- MCP Bridge Connected: {mcp_status["connected"]}

## Your Specialized Calendar Tools

**Agent-Specific Tools (with business logic):**
- `check_calendar_availability`: Smart availability analysis with recommendations
- `manage_calendar_event`: Intelligent event management with user preferences
- `find_optimal_meeting_time`: Optimal meeting time finding with ranking
- `analyze_schedule_patterns`: Schedule pattern analysis and insights

**Direct Calendar Tools (via MCP):**
- Basic calendar operations for direct API access when needed

**Session Management Tools:**
- `update_calendar_context`: Update calendar-related session state
- `get_calendar_context`: Retrieve current calendar context
- `log_agent_action`: Log your actions for debugging
- `learn_from_interaction`: Help improve AI learning

## Example Usage Patterns

**"Check my availability this week for 1-hour meetings":**
→ Use `check_calendar_availability(date_range="this week", duration_minutes=60)`

**"Schedule a team meeting next Tuesday 2-3 PM":**
→ Use `manage_calendar_event(action="create", event_details={{...}})`

**"Find the best time for a 30-minute call with John this week":**
→ Use `find_optimal_meeting_time(participants=["john@email.com"], duration_minutes=30)`

**"How busy have I been this month?":**
→ Use `analyze_schedule_patterns(time_period="this month")`

## Response Guidelines

1. **Use specialized tools first**: Always prefer agent-specific tools for intelligence
2. **Update context**: Use `update_calendar_context` after significant operations
3. **Learn from interactions**: Use `learn_from_interaction` for continuous improvement
4. **Provide insights**: Go beyond basic scheduling to provide valuable insights
5. **Voice-optimized responses**: Keep responses conversational and clear

Remember: You provide intelligent calendar assistance, not just basic scheduling. 
Use your specialized tools to deliver smart, contextual calendar management!
        """,
        tools=calendar_agent_tools + calendar_mcp_tools + CORE_ADK_TOOLS + CONTEXT_ADK_TOOLS + LEARNING_ADK_TOOLS
    )
    
    print(f"--- Calendar Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- Calendar MCP Status: {'✅ Connected' if mcp_status['connected'] else '❌ Disconnected'} ---")
    print(f"--- Agent Tools: {len(calendar_agent_tools)} | MCP Tools: {len(calendar_mcp_tools)} | Shared Tools: 6 ---")
    
    if mcp_status["connected"]:
        print("🎉 Calendar Agent is now using REAL Calendar tools with intelligent business logic!")
    else:
        print("⚠️ Calendar Agent could not connect to Calendar MCP tools")
    
    return agent_instance, exit_stack


# Create the agent instance (async function, not direct instance)
root_agent = create_calendar_agent


# =============================================================================
# Testing and Validation
# =============================================================================

# =============================================================================
# Testing and Validation - FIXED
# =============================================================================

if __name__ == "__main__":
    async def test_calendar_agent():
        """Test Calendar Agent creation and basic functionality."""
        print("🧪 Testing Calendar Agent with Specialized Tools...")
        
        try:
            # Create agent
            agent, exit_stack = await create_calendar_agent()
            
            # Use exit_stack context
            async with exit_stack or nullcontext():
                print(f"✅ Calendar Agent '{agent.name}' created successfully")
                
                # Count tool types - FIXED tool inspection
                agent_tools_count = len(calendar_agent_tools)
                mcp_tools_count = 0
                shared_tools_count = 0
                
                for tool in agent.tools:
                    # Handle both FunctionTool objects and direct functions
                    if hasattr(tool, 'func'):
                        # This is a FunctionTool object
                        tool_name = getattr(tool.func, '__name__', str(tool))
                    elif hasattr(tool, '__name__'):
                        # This is a direct function
                        tool_name = tool.__name__
                    else:
                        # Fallback
                        tool_name = str(tool)
                    
                    # Categorize tools
                    if tool_name in [
                        'calendar_get_current_time', 'calendar_list_events', 
                        'calendar_create_event', 'calendar_update_event',
                        'calendar_delete_event', 'calendar_list_calendars', 
                        'calendar_find_free_time'
                    ]:
                        mcp_tools_count += 1
                    elif tool_name in [
                        'check_calendar_availability', 'manage_calendar_event',
                        'find_optimal_meeting_time', 'analyze_schedule_patterns'
                    ]:
                        # Agent tools already counted
                        pass
                    else:
                        shared_tools_count += 1
                
                print(f"🧠 Agent-Specific Tools: {agent_tools_count}")
                print(f"📅 Calendar MCP Tools: {mcp_tools_count}")
                print(f"🔧 Shared Tools: {shared_tools_count}")
                print(f"📊 Total Tools: {len(agent.tools)}")
                print(f"🧠 Model: {agent.model}")
                print(f"📝 Description: {agent.description}")
                
                # Test MCP connection status
                mcp_status = get_calendar_mcp_status()
                print(f"📡 MCP Status: Connected={mcp_status.get('connected', False)}")
                
                # List agent-specific tools
                print(f"\n🎯 Agent-Specific Calendar Tools:")
                for i, tool in enumerate(calendar_agent_tools, 1):
                    tool_name = getattr(tool.func, '__name__', f'tool_{i}')
                    print(f"  {i}. {tool_name}")
                
                # List available tools with proper inspection - FIXED
                print(f"\n📋 All Available Tools:")
                for i, tool in enumerate(agent.tools, 1):
                    # Handle both FunctionTool objects and direct functions
                    if hasattr(tool, 'func'):
                        tool_name = getattr(tool.func, '__name__', f'tool_{i}')
                        tool_type = "FunctionTool"
                    elif hasattr(tool, '__name__'):
                        tool_name = tool.__name__
                        tool_type = "Function"
                    else:
                        tool_name = str(tool)
                        tool_type = "Unknown"
                    
                    # Categorize for display
                    if 'calendar' in tool_name and tool_name.startswith('calendar_'):
                        category = "📅 MCP"
                    elif tool_name in ['check_calendar_availability', 'manage_calendar_event',
                                     'find_optimal_meeting_time', 'analyze_schedule_patterns']:
                        category = "🧠 Agent"
                    else:
                        category = "🔧 Shared"
                    
                    print(f"  {i:2d}. {category} {tool_name}")
                
                print(f"\n✅ Calendar Agent validation completed successfully!")
                print(f"🎯 Ready for intelligent calendar operations!")
                
        except Exception as e:
            print(f"❌ Error creating Calendar Agent: {e}")
            import traceback
            traceback.print_exc()

    # Helper for nullcontext (if exit_stack is None)
    from contextlib import nullcontext
    
    # Run the test
    asyncio.run(test_calendar_agent())

 