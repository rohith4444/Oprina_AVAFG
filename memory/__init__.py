"""
Memory Package for Oprina - ADK Migration

This package provides memory services for the Oprina voice assistant.
Now uses ADK-native memory services with UI support.

Architecture:
- ADK Memory Manager: Primary memory interface using ADK services
- Chat History Service: UI conversation lists and user experience

Usage:
    from memory import get_adk_memory_manager, get_chat_history
    
    # Get ADK memory manager (session + memory + UI integration)
    memory_manager = get_adk_memory_manager()
    
    # Get chat history service (UI only)
    chat_history = get_chat_history()
"""

# ADK Memory Manager (primary interface)
from .adk_memory_manager import (
    OprinaMemoryManager,
    get_adk_memory_manager,
    adk_memory_context
)

# Chat History Service (UI support)
from .chat_history import (
    ChatHistoryService,
    ChatMessage,
    Conversation,
    get_chat_history
)

# Export main interfaces
__all__ = [
    # ADK Memory Manager
    "OprinaMemoryManager",
    "get_adk_memory_manager", 
    "adk_memory_context",
    
    # Chat History (UI)
    "ChatHistoryService",
    "ChatMessage",
    "Conversation", 
    "get_chat_history",
]

# Package metadata
__version__ = "2.0.0"
__description__ = "ADK-native memory services for Oprina"

# Legacy imports removed:
# - RedisCacheService (replaced by ADK session state)
# - SessionMemoryService (replaced by ADK SessionService) 
# - LongTermMemoryService (replaced by ADK MemoryService)
# - MemoryManager (replaced by ADK Memory Manager)