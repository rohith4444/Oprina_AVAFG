"""
Memory Package for Oprina - Simplified ADK Integration

This package provides memory services for the Oprina voice assistant.
Uses ADK-native memory services with UI support.

Architecture:
- ADK Service Configuration Helper: Sets up ADK services based on settings
- Chat History Service: UI conversation lists and user experience

Usage:
    from memory import get_adk_memory_manager, get_chat_history
    
    # Get ADK service configuration helper
    memory_manager = get_adk_memory_manager()
    
    # Get chat history service (UI only)
    chat_history = get_chat_history()
"""

# Chat History Service (UI support)
from .chat_history import (
    ChatHistoryService,
    ChatMessage,
    Conversation,
    get_chat_history
)

# ADK Service Configuration Helper (simplified)
from .adk_memory_manager import (
    OprinaMemoryManager,
    get_adk_memory_manager
)

# Export main interfaces
__all__ = [
    # ADK Service Configuration Helper
    "OprinaMemoryManager",
    "get_adk_memory_manager",
    
    # Chat History (UI)
    "ChatHistoryService",
    "ChatMessage",
    "Conversation", 
    "get_chat_history",
]

# Package metadata
__version__ = "2.1.0"
__description__ = "Simplified ADK service configuration with UI chat history"

# Legacy imports removed:
# - adk_memory_context (no longer needed - ADK handles session context)
# - RedisCacheService (replaced by ADK session state)
# - SessionMemoryService (replaced by ADK SessionService) 
# - LongTermMemoryService (replaced by ADK MemoryService)
# - MemoryManager (replaced by simplified ADK Service Configuration Helper)