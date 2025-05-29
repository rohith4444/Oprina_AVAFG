"""
Email Agent Package
"""
from .agent import email_agent, create_email_runner

# For backward compatibility
async def email_agent_creator():
    """Legacy wrapper"""
    agent, create_runner = email_agent, create_email_runner
    return agent, None  # No exit stack needed with ADK

__all__ = ["email_agent", "create_email_runner", "email_agent_creator"]