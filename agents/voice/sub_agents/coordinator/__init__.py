"""
Coordinator Agent Package - Complete ADK Implementation

This package contains the Coordinator Agent responsible for:
- Multi-agent workflow orchestration using ADK auto-delegation
- Complex task coordination between Email, Content, and Calendar agents
- Session state management and result coordination
- Cross-session memory and workflow optimization

The coordinator leverages ADK's automatic delegation system where the LLM
intelligently routes tasks to the most appropriate sub-agent based on
descriptions and context.
"""

# Import the main coordinator agent
from agents.voice.sub_agents.coordinator.agent import coordinator_agent, create_coordinator_agent

# Import coordination tools for direct access if needed
from agents.voice.sub_agents.coordinator.coordinator_tools import (
    analyze_coordination_context,
    get_workflow_status,
    coordinate_agent_results,
    COORDINATION_TOOLS
)

# Import sub-agents for reference (though ADK handles delegation automatically)
from agents.voice.sub_agents.coordinator.sub_agents.email import email_agent
from agents.voice.sub_agents.coordinator.sub_agents.content import content_agent
from agents.voice.sub_agents.coordinator.sub_agents.calendar import calendar_agent

# Export main components
__all__ = [
    # Main coordinator agent
    "coordinator_agent",
    "create_coordinator_agent",
    
    # Coordination tools (for direct use if needed)
    "analyze_coordination_context",
    "get_workflow_status", 
    "coordinate_agent_results",
    "COORDINATION_TOOLS",
    
    # Sub-agents (for reference, ADK handles delegation)
    "email_agent",
    "content_agent", 
    "calendar_agent"
]

# Package metadata
__version__ = "2.0.0"
__description__ = "ADK-native coordinator agent with automatic delegation"

# Coordination workflow types (imported from session_keys for consistency)
from agents.voice.sub_agents.common.session_keys import (
    WORKFLOW_EMAIL_ONLY,
    WORKFLOW_CALENDAR_ONLY,
    WORKFLOW_CONTENT_ONLY,
    WORKFLOW_EMAIL_CONTENT,
    WORKFLOW_CALENDAR_CONTENT,
    WORKFLOW_EMAIL_CALENDAR,
    WORKFLOW_ALL_AGENTS
)

# Export workflow types
__all__.extend([
    "WORKFLOW_EMAIL_ONLY",
    "WORKFLOW_CALENDAR_ONLY", 
    "WORKFLOW_CONTENT_ONLY",
    "WORKFLOW_EMAIL_CONTENT",
    "WORKFLOW_CALENDAR_CONTENT",
    "WORKFLOW_EMAIL_CALENDAR",
    "WORKFLOW_ALL_AGENTS"
])

# Package information for debugging
def get_package_info():
    """Get package information for debugging and monitoring."""
    return {
        "package": "coordinator",
        "version": __version__,
        "description": __description__,
        "main_agent": coordinator_agent.name if coordinator_agent else "Not loaded",
        "sub_agents": [
            email_agent.name if email_agent else "email_agent not loaded",
            content_agent.name if content_agent else "content_agent not loaded", 
            calendar_agent.name if calendar_agent else "calendar_agent not loaded"
        ],
        "coordination_tools": len(COORDINATION_TOOLS),
        "workflow_types": [
            WORKFLOW_EMAIL_ONLY, WORKFLOW_CALENDAR_ONLY, WORKFLOW_CONTENT_ONLY,
            WORKFLOW_EMAIL_CONTENT, WORKFLOW_CALENDAR_CONTENT, 
            WORKFLOW_EMAIL_CALENDAR, WORKFLOW_ALL_AGENTS
        ],
        "adk_features": [
            "automatic_delegation",
            "session_state_management", 
            "cross_session_memory",
            "tool_context_injection",
            "output_key_persistence"
        ]
    }

# Add package info to exports
__all__.append("get_package_info")