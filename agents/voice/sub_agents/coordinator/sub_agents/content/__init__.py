"""
Content Agent Package

This package contains the Content Agent responsible for:
- Email content summarization with adaptive detail levels
- Email reply generation with context awareness
- Content analysis (sentiment, topics, urgency)
- Text optimization for voice delivery
- Template-based content generation
"""
from .agent import create_content_agent

# Create instance only when explicitly requested
def get_content_agent():
    return create_content_agent()

__all__ = ["create_content_agent", "get_content_agent"]

# Package metadata
__version__ = "2.0.0"
__description__ = "ADK-integrated content processing agent with voice optimization"
