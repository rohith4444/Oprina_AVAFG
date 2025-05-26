
"""
Content Agent Package

This package contains the Content Agent responsible for:
- Email content summarization with adaptive detail levels
- Email reply generation with context awareness
- Content analysis (sentiment, topics, urgency)
- Text optimization for voice delivery
- Template-based content generation
"""

from .agent import content_agent

__all__ = ["content_agent"]