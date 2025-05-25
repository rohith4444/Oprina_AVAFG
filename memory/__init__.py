"""
Oprina Memory Module

This package provides memory management for the Oprina voice-powered Gmail assistant.
"""

# Core memory components that actually exist
from .redis_cache import RedisCacheService, get_redis_cache

# Version info
__version__ = "1.0.0"
__author__ = "Rohith"
__description__ = "Memory management system for Oprina voice assistant"

# Only export what exists
__all__ = [
    "RedisCacheService",
    "get_redis_cache",
]