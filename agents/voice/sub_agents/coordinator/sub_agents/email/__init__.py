
"""
Email Agent Package

This package contains the Email Agent responsible for Gmail operations:
- Fetching emails
- Sending and drafting emails  
- Email organization (labels, archive, etc.)
- Gmail authentication and connection management
"""

from .agent import root_agent as email_agent_creator

__all__ = ["email_agent_creator"]