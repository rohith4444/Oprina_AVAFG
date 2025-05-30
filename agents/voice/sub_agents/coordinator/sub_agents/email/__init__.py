"""
Email Agent Package

This package contains the Email Agent responsible for:
- Gmail connection management
- Email listing, searching, and reading
- Email sending and replying
- Email organization (read, archive, delete)
- Session state management for email operations
"""

from .agent import create_email_agent

# Create instance only when explicitly requested
def get_email_agent():
    return create_email_agent()

__all__ = ["create_email_agent", "get_email_agent"]

# Package metadata
__version__ = "2.0.0"
__description__ = "ADK-integrated Gmail agent with direct API access"
