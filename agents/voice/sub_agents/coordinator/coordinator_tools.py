"""
Simple Coordination Tools for ADK - Minimal but Powerful

These tools provide coordination capabilities for multi-agent workflows
while leveraging existing utility functions and ADK's automatic delegation system.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(5):  # Navigate to project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from services.logging.logger import setup_logger

# Import existing utility functions (your existing ones are perfect!)
from agents.voice.sub_agents.common.utils import (
    validate_tool_context, update_agent_activity, get_user_preferences,
    get_service_connection_status, get_session_summary, log_tool_execution
)

# Import coordination session keys
from agents.voice.sub_agents.common.session_keys import (
    COORDINATION_ACTIVE, COORDINATION_WORKFLOW_TYPE, COORDINATION_CURRENT_STEP,
    COORDINATION_REQUIRED_AGENTS, COORDINATION_COMPLETED_AGENTS,
    COORDINATION_LAST_DELEGATED_AGENT, COORDINATION_DELEGATION_HISTORY,
    COORDINATION_AGENT_OUTPUTS, COORDINATION_WORKFLOW_PROGRESS,
    EMAIL_CURRENT_RESULTS, CALENDAR_CURRENT, CONTENT_LAST_SUMMARY,
    USER_PREFERENCES, USER_NAME, WORKFLOW_EMAIL_ONLY, WORKFLOW_CALENDAR_ONLY,
    WORKFLOW_EMAIL_CONTENT, WORKFLOW_EMAIL_CALENDAR, WORKFLOW_ALL_AGENTS
)

logger = setup_logger("coordination_tools", console_output=True)


# =============================================================================
# Core Coordination Tools (Simple but Effective)
# =============================================================================

def analyze_coordination_context(tool_context=None) -> str:
    """
    Analyze current session context to determine coordination needs and status.
    Uses existing session data to provide insights for multi-agent workflows.
    """
    if not validate_tool_context(tool_context, "analyze_coordination_context"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "analyze_coordination_context", "analyze", True, 
                         "Analyzing coordination context")
        
        # Update agent activity
        update_agent_activity(tool_context, "coordinator_agent", "analyzing_context")
        
        # Get comprehensive session summary using existing utility
        session_summary = get_session_summary(tool_context)
        
        # Analyze agent results and availability
        email_results = tool_context.session.state.get("email_result", "")
        calendar_results = tool_context.session.state.get("calendar_result", "")
        content_results = tool_context.session.state.get("content_result", "")
        
        # Check service connections using existing utility
        gmail_status = get_service_connection_status(tool_context, "gmail")
        calendar_status = get_service_connection_status(tool_context, "calendar")
        
        # Determine active agents and workflow type
        active_agents = []
        if email_results:
            active_agents.append("email_agent")
        if calendar_results:
            active_agents.append("calendar_agent")
        if content_results:
            active_agents.append("content_agent")
        
        # Determine workflow type based on active agents
        workflow_type = "none"
        if len(active_agents) == 1:
            if "email_agent" in active_agents:
                workflow_type = WORKFLOW_EMAIL_ONLY
            elif "calendar_agent" in active_agents:
                workflow_type = WORKFLOW_CALENDAR_ONLY
        elif len(active_agents) == 2:
            if "email_agent" in active_agents and "content_agent" in active_agents:
                workflow_type = WORKFLOW_EMAIL_CONTENT
            elif "email_agent" in active_agents and "calendar_agent" in active_agents:
                workflow_type = WORKFLOW_EMAIL_CALENDAR
        elif len(active_agents) == 3:
            workflow_type = WORKFLOW_ALL_AGENTS
        
        # Update coordination state
        tool_context.session.state[COORDINATION_WORKFLOW_TYPE] = workflow_type
        tool_context.session.state[COORDINATION_COMPLETED_AGENTS] = active_agents
        tool_context.session.state[COORDINATION_AGENT_OUTPUTS] = {
            "email_agent": bool(email_results),
            "calendar_agent": bool(calendar_results),
            "content_agent": bool(content_results)
        }
        
        # Generate context analysis
        analysis_parts = []
        analysis_parts.append(f"Workflow Type: {workflow_type}")
        analysis_parts.append(f"Active Agents: {', '.join(active_agents) if active_agents else 'None'}")
        analysis_parts.append(f"Gmail Connected: {gmail_status.get('connected', False)}")
        analysis_parts.append(f"Calendar Connected: {calendar_status.get('connected', False)}")
        analysis_parts.append(f"Session Keys: {session_summary.get('total_state_keys', 0)}")
        
        result = " | ".join(analysis_parts)
        
        log_tool_execution(tool_context, "analyze_coordination_context", "analyze", True, 
                         f"Analysis completed: {workflow_type}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing coordination context: {e}")
        log_tool_execution(tool_context, "analyze_coordination_context", "analyze", False, str(e))
        return f"Error analyzing coordination context: {str(e)}"


def get_workflow_status(tool_context=None) -> str:
    """
    Get current multi-agent workflow status and progress.
    Provides visibility into coordination state and agent execution.
    """
    if not validate_tool_context(tool_context, "get_workflow_status"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "get_workflow_status", "status_check", True, 
                         "Checking workflow status")
        
        # Update agent activity
        update_agent_activity(tool_context, "coordinator_agent", "checking_workflow_status")
        
        # Get workflow information from session state
        workflow_type = tool_context.session.state.get(COORDINATION_WORKFLOW_TYPE, "unknown")
        completed_agents = tool_context.session.state.get(COORDINATION_COMPLETED_AGENTS, [])
        delegation_history = tool_context.session.state.get(COORDINATION_DELEGATION_HISTORY, [])
        
        # Check agent results availability
        agent_results = {
            "email_agent": bool(tool_context.session.state.get("email_result", "")),
            "calendar_agent": bool(tool_context.session.state.get("calendar_result", "")),
            "content_agent": bool(tool_context.session.state.get("content_result", ""))
        }
        
        # Count available results
        available_results = sum(1 for has_result in agent_results.values() if has_result)
        
        # Get user preferences for context
        user_prefs = get_user_preferences(tool_context, {})
        user_name = tool_context.session.state.get(USER_NAME, "User")
        
        # Generate status summary
        status_parts = []
        status_parts.append(f"Workflow: {workflow_type}")
        status_parts.append(f"Results Available: {available_results}/3 agents")
        status_parts.append(f"Completed Agents: {len(completed_agents)}")
        
        if delegation_history:
            status_parts.append(f"Last Delegation: {delegation_history[-1] if delegation_history else 'None'}")
        
        # Add service readiness
        gmail_connected = tool_context.session.state.get("user:gmail_connected", False)
        calendar_connected = tool_context.session.state.get("user:calendar_connected", False)
        
        readiness_status = []
        if gmail_connected:
            readiness_status.append("Gmail✓")
        if calendar_connected:
            readiness_status.append("Calendar✓")
        
        if readiness_status:
            status_parts.append(f"Services: {', '.join(readiness_status)}")
        
        # Update coordination tracking
        tool_context.session.state[COORDINATION_WORKFLOW_PROGRESS] = {
            "workflow_type": workflow_type,
            "completed_agents": completed_agents,
            "available_results": available_results,
            "services_ready": len(readiness_status),
            "status_checked_at": datetime.utcnow().isoformat()
        }
        
        result = " | ".join(status_parts)
        
        log_tool_execution(tool_context, "get_workflow_status", "status_check", True, 
                         f"Status: {available_results} results available")
        return result
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        log_tool_execution(tool_context, "get_workflow_status", "status_check", False, str(e))
        return f"Error checking workflow status: {str(e)}"


def coordinate_agent_results(agent_filter: str = "all", tool_context=None) -> str:
    """
    Coordinate and summarize results from multiple agents.
    Provides unified view of multi-agent workflow outcomes.
    
    Args:
        agent_filter: Filter results by agent type ("all", "email", "calendar", "content")
    """
    if not validate_tool_context(tool_context, "coordinate_agent_results"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "coordinate_agent_results", "coordinate", True, 
                         f"Coordinating results, filter: {agent_filter}")
        
        # Update agent activity
        update_agent_activity(tool_context, "coordinator_agent", "coordinating_results")
        
        # Get agent results from session state (using ADK output_key pattern)
        email_result = tool_context.session.state.get("email_result", "")
        calendar_result = tool_context.session.state.get("calendar_result", "")
        content_result = tool_context.session.state.get("content_result", "")
        
        # Collect results based on filter
        collected_results = []
        
        if agent_filter in ["all", "email"] and email_result:
            collected_results.append(f"Email Agent: {email_result[:100]}{'...' if len(email_result) > 100 else ''}")
        
        if agent_filter in ["all", "calendar"] and calendar_result:
            collected_results.append(f"Calendar Agent: {calendar_result[:100]}{'...' if len(calendar_result) > 100 else ''}")
        
        if agent_filter in ["all", "content"] and content_result:
            collected_results.append(f"Content Agent: {content_result[:100]}{'...' if len(content_result) > 100 else ''}")
        
        if not collected_results:
            result = f"No results available for filter '{agent_filter}'"
        else:
            # Create coordination summary
            summary_parts = [
                f"Coordination Summary (Filter: {agent_filter})",
                f"Results from {len(collected_results)} agent(s):"
            ]
            summary_parts.extend(collected_results)
            
            result = "\n".join(summary_parts)
        
        # Update coordination state with summary
        tool_context.session.state[COORDINATION_AGENT_OUTPUTS] = {
            "email_available": bool(email_result),
            "calendar_available": bool(calendar_result),
            "content_available": bool(content_result),
            "last_coordination": datetime.utcnow().isoformat(),
            "filter_used": agent_filter,
            "results_count": len(collected_results)
        }
        
        # Track delegation history for learning
        delegation_history = tool_context.session.state.get(COORDINATION_DELEGATION_HISTORY, [])
        if not delegation_history:
            # Infer delegation from available results
            if email_result:
                delegation_history.append("email_agent")
            if content_result:
                delegation_history.append("content_agent")
            if calendar_result:
                delegation_history.append("calendar_agent")
            
            tool_context.session.state[COORDINATION_DELEGATION_HISTORY] = delegation_history
        
        log_tool_execution(tool_context, "coordinate_agent_results", "coordinate", True, 
                         f"Coordinated {len(collected_results)} results")
        return result
        
    except Exception as e:
        logger.error(f"Error coordinating agent results: {e}")
        log_tool_execution(tool_context, "coordinate_agent_results", "coordinate", False, str(e))
        return f"Error coordinating results: {str(e)}"


# =============================================================================
# Create ADK Function Tools
# =============================================================================

# Core coordination tools
analyze_coordination_context_tool = FunctionTool(func=analyze_coordination_context)
get_workflow_status_tool = FunctionTool(func=get_workflow_status)
coordinate_agent_results_tool = FunctionTool(func=coordinate_agent_results)

# Coordination tools collection
COORDINATION_TOOLS = [
    analyze_coordination_context_tool,
    get_workflow_status_tool,
    coordinate_agent_results_tool
]

# Export for easy access
__all__ = [
    "analyze_coordination_context",
    "get_workflow_status", 
    "coordinate_agent_results",
    "COORDINATION_TOOLS"
]


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing Coordination Tools...")
    
    # Mock tool context for testing
    class MockSession:
        def __init__(self):
            self.state = {
                # Mock some agent results
                "email_result": "Successfully fetched 5 emails from Gmail",
                "content_result": "Summarized email content: Meeting reminder for tomorrow",
                "user:gmail_connected": True,
                "user:calendar_connected": False,
                "user:name": "Test User",
                "user:preferences": {"summary_detail": "moderate"}
            }
    
    class MockToolContext:
        def __init__(self):
            self.session = MockSession()
            self.invocation_id = "test_coordination_123"
    
    mock_context = MockToolContext()
    
    print("\n📊 Testing analyze_coordination_context...")
    context_analysis = analyze_coordination_context(mock_context)
    print(f"Context Analysis: {context_analysis}")
    
    print("\n📋 Testing get_workflow_status...")
    workflow_status = get_workflow_status(mock_context)
    print(f"Workflow Status: {workflow_status}")
    
    print("\n🔗 Testing coordinate_agent_results (all)...")
    all_results = coordinate_agent_results("all", mock_context)
    print(f"All Results: {all_results[:200]}...")
    
    print("\n🔗 Testing coordinate_agent_results (email only)...")
    email_results = coordinate_agent_results("email", mock_context)
    print(f"Email Results: {email_results}")
    
    # Check session state updates
    coordination_data = mock_context.session.state.get(COORDINATION_AGENT_OUTPUTS, {})
    print(f"\n📊 Session State Updated: {bool(coordination_data)}")
    
    if coordination_data:
        print(f"Coordination Data: {coordination_data}")
    
    print(f"\n✅ Coordination tools testing completed!")
    print(f"🔧 Total tools created: {len(COORDINATION_TOOLS)}")
    print("🎯 Ready for coordinator agent integration!")