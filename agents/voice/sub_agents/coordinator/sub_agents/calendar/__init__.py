"""
Calendar Agent Package

This package contains the Calendar Agent responsible for:
- Google Calendar connection management
- Event listing and searching
- Event creation and management
- Schedule analysis and free time finding
- Calendar organization and preferences
"""

"""Calendar Agent Package"""
from .agent import create_calendar_agent

# Create instance only when explicitly requested
def get_calendar_agent():
    return create_calendar_agent()

__all__ = ["create_calendar_agent", "get_calendar_agent"]

# Package metadata
__version__ = "2.0.0"
__description__ = "ADK-integrated Calendar agent with direct API access"