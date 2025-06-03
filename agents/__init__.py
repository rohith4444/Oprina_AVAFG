"""
Agents Package for Oprina

This package contains all agent definitions for the Oprina voice assistant.
The root_agent is the main entry point for ADK integration.
"""

from .root_agent import root_agent, agent, get_root_agent

__all__ = ["root_agent", "agent", "get_root_agent"]
