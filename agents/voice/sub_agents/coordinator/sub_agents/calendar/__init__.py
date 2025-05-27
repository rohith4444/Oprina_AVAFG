"""
Calendar Agent Package

This package contains the Calendar Agent responsible for Google Calendar operations:
- Event listing and searching
- Event creation and management
- Schedule analysis and free time finding
- Calendar organization and preferences
- Calendar authentication and connection management
"""

from .agent import root_agent as calendar_agent_creator

__all__ = ["calendar_agent_creator"]