"""
Oprina Memory Module

This package provides comprehensive memory management for the Oprina voice-powered
Gmail assistant, including session state, conversation history, and long-term learning.

Memory Architecture:
    1. Session Memory (ADK DatabaseSessionService + Supabase)
       - Current conversation context for agent coordination
       - User preferences and settings
       - Active email context and pending actions
       
    2. Chat History (Direct Supabase)
       - Permanent storage of all conversations
       - User message and agent response history
       - Searchable conversation logs
       
    3. Long-term Memory (ADK InMemoryMemoryService)
       - User behavior patterns and preferences
       - Email interaction learning
       - Smart suggestions and automation
       
    4. Redis Cache
       - Recently fetched emails
       - Temporary agent coordination data
       - Performance optimization

Usage:
    from memory import MemoryManager
    
    # Initialize memory manager
    memory = MemoryManager()
    
    # Create a new session
    session_id = await memory.create_oprina_session(user_id="user123")
    
    # Store conversation message
    await memory.store_chat_message(
        session_id=session_id,
        message_type="user",
        content="Summarize my emails"
    )
    
    # Update agent context
    await memory.update_agent_context(
        session_id=session_id,
        agent_name="email_agent",
        context={"last_sync": "2024-05-23T10:30:00Z"}
    )
"""

# Core memory components
from .memory_manager import MemoryManager
from .session_memory import SessionMemoryService
from .chat_history import ChatHistoryService
from .long_term_memory import LongTermMemoryService
from .redis_cache import RedisCacheService

# # Memory models and schemas
# from .models import (
#     SessionState,
#     ChatMessage,
#     AgentContext,
#     UserPreferences,
#     EmailContext,
#     ConversationSummary
# )

# # Exceptions
# from .exceptions import (
#     MemoryError,
#     SessionNotFoundError,
#     InvalidSessionStateError,
#     CacheConnectionError,
#     DatabaseConnectionError
# )

# # Constants
# from .constants import (
#     DEFAULT_SESSION_TIMEOUT,
#     DEFAULT_CACHE_TTL,
#     EMAIL_CACHE_TTL,
#     MAX_CONVERSATION_HISTORY,
#     SUPPORTED_MESSAGE_TYPES
# )

# Version info
__version__ = "1.0.0"
__author__ = "Rohith"
__description__ = "Memory management system for Oprina voice assistant"

# Package-level exports
__all__ = [
    # Core services
    "MemoryManager",
    "SessionMemoryService", 
    "ChatHistoryService",
    "LongTermMemoryService",
    "RedisCacheService",
    
    # Models
    "SessionState",
    "ChatMessage",
    "AgentContext", 
    "UserPreferences",
    "EmailContext",
    "ConversationSummary",
    
    # Exceptions
    "MemoryError",
    "SessionNotFoundError",
    "InvalidSessionStateError",
    "CacheConnectionError",
    "DatabaseConnectionError",
    
    # Constants
    "DEFAULT_SESSION_TIMEOUT",
    "DEFAULT_CACHE_TTL",
    "EMAIL_CACHE_TTL",
    "MAX_CONVERSATION_HISTORY",
    "SUPPORTED_MESSAGE_TYPES"
]


# =============================================================================
# Package Initialization and Health Checks
# =============================================================================

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import redis
    except ImportError:
        missing_deps.append("redis")
    
    try:
        import supabase
    except ImportError:
        missing_deps.append("supabase")
    
    try:
        from google.adk.sessions import DatabaseSessionService
    except ImportError:
        missing_deps.append("google-adk")
    
    if missing_deps:
        raise ImportError(
            f"Missing required dependencies: {', '.join(missing_deps)}. "
            f"Please install them using: pip install {' '.join(missing_deps)}"
        )


def validate_environment():
    """Validate that required environment variables are set."""
    from config.settings import settings
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "REDIS_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please check your .env file."
        )


async def initialize_memory_system():
    """Initialize the memory system and verify all connections."""
    check_dependencies()
    validate_environment()
    
    # Initialize memory manager
    memory_manager = MemoryManager()
    
    # Test connections
    try:
        await memory_manager.health_check()
        print("✅ Memory system initialized successfully")
        return memory_manager
    except Exception as e:
        print(f"❌ Memory system initialization failed: {e}")
        raise


# =============================================================================
# Development Utilities
# =============================================================================

def get_memory_stats():
    """Get memory system statistics (for debugging)."""
    from .memory_manager import MemoryManager
    
    memory = MemoryManager()
    return {
        "redis_connected": memory.redis_cache.is_connected(),
        "supabase_configured": memory.chat_history.is_configured(),
        "session_service_ready": memory.session_memory.is_ready(),
        "package_version": __version__
    }


def clear_all_caches():
    """Clear all Redis caches (development/testing only)."""
    from .memory_manager import MemoryManager
    
    memory = MemoryManager()
    return memory.redis_cache.clear_all()


def reset_user_session(user_id: str):
    """Reset all session data for a user (development/testing only)."""
    from .memory_manager import MemoryManager
    
    memory = MemoryManager()
    return memory.reset_user_data(user_id)


# =============================================================================
# Compatibility and Migration
# =============================================================================

# Legacy imports for backward compatibility
SessionMemory = SessionMemoryService
ChatHistory = ChatHistoryService
LongTermMemory = LongTermMemoryService
RedisCache = RedisCacheService

# Migration utilities (if needed for future versions)
def migrate_memory_schema(from_version: str, to_version: str):
    """Migrate memory data between schema versions."""
    # Implementation would go here for future schema changes
    pass


# =============================================================================
# Package Documentation
# =============================================================================

MEMORY_ARCHITECTURE_DOCS = """
Oprina Memory Architecture

┌─────────────────────────────────────────────────────────────────────────┐
│                            Memory Manager                               │
│                        (Unified Interface)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │  Session Memory │  │  Chat History   │  │ Long-term Memory│        │
│  │                 │  │                 │  │                 │        │
│  │ ADK Database    │  │ Direct Supabase │  │ ADK InMemory    │        │
│  │ SessionService  │  │ Tables          │  │ MemoryService   │        │
│  │                 │  │                 │  │                 │        │
│  │ • Agent Context │  │ • All Messages  │  │ • User Patterns │        │
│  │ • User Settings │  │ • Conversations │  │ • Preferences   │        │
│  │ • Email Context │  │ • Search History│  │ • Learning Data │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Redis Cache                                  │   │
│  │                                                                 │   │
│  │ • Recent Emails    • Agent Coordination    • Performance       │   │
│  │ • Temp Data        • Session Cache         • Speed Optimization│   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

Data Flow:
1. User Message → Chat History (permanent) + Session Memory (context)
2. Agent Processing → Session Memory (coordination) + Redis (temp data)
3. Email Operations → Redis (cache) + Session Memory (context updates)
4. Learning → Long-term Memory (patterns) + Session Memory (preferences)

Key Benefits:
• Persistence: Conversations survive app restarts
• Performance: Redis caching for speed
• Coordination: Shared state between agents
• Learning: Behavioral pattern recognition
• Scalability: Separate concerns and storage types
"""


# =============================================================================
# Quick Start Example
# =============================================================================

QUICK_START_EXAMPLE = '''
# Quick Start Example

async def example_usage():
    """Example of how to use the memory system."""
    from memory import MemoryManager
    
    # Initialize memory system
    memory = MemoryManager()
    
    # Create new user session
    user_id = "user_123"
    session_id = await memory.create_oprina_session(user_id)
    
    # Store user message
    await memory.store_chat_message(
        session_id=session_id,
        message_type="user_voice",
        content="Check my emails from today",
        metadata={"audio_duration": 3.5}
    )
    
    # Update email agent context
    await memory.update_agent_context(
        session_id=session_id,
        agent_name="email_agent",
        context={
            "last_gmail_sync": "2024-05-23T10:30:00Z",
            "fetched_count": 25,
            "unread_count": 7
        }
    )
    
    # Cache recent emails
    emails = [{"id": "email1", "subject": "Meeting today"}]
    await memory.cache_emails(user_id, emails, ttl_seconds=300)
    
    # Store agent response
    await memory.store_chat_message(
        session_id=session_id,
        message_type="agent_response",
        content="I found 7 unread emails from today. Here's a summary...",
        metadata={"processing_time": 1.2}
    )
    
    # Get conversation history
    history = await memory.get_conversation_history(session_id, limit=10)
    
    # Learn from interaction
    await memory.learn_user_pattern(
        user_id=user_id,
        pattern_type="email_check_frequency",
        data={"preferred_time": "morning", "summary_detail": "brief"}
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
'''


# =============================================================================
# Error Handling Utilities
# =============================================================================

def handle_memory_error(func):
    """Decorator for consistent memory error handling."""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Log error and re-raise with context
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Memory operation failed in {func.__name__}: {e}")
            raise MemoryError(f"Memory operation failed: {e}") from e
    
    return wrapper


# =============================================================================
# Performance Monitoring
# =============================================================================

class MemoryMetrics:
    """Performance metrics for memory operations."""
    
    def __init__(self):
        self.operation_counts = {}
        self.operation_times = {}
        self.error_counts = {}
    
    def record_operation(self, operation: str, duration: float, success: bool = True):
        """Record a memory operation for metrics."""
        if operation not in self.operation_counts:
            self.operation_counts[operation] = 0
            self.operation_times[operation] = []
            self.error_counts[operation] = 0
        
        self.operation_counts[operation] += 1
        self.operation_times[operation].append(duration)
        
        if not success:
            self.error_counts[operation] += 1
    
    def get_stats(self) -> dict:
        """Get performance statistics."""
        stats = {}
        for operation in self.operation_counts:
            times = self.operation_times[operation]
            stats[operation] = {
                "count": self.operation_counts[operation],
                "avg_time": sum(times) / len(times) if times else 0,
                "max_time": max(times) if times else 0,
                "min_time": min(times) if times else 0,
                "error_rate": self.error_counts[operation] / self.operation_counts[operation]
            }
        return stats


# Global metrics instance
memory_metrics = MemoryMetrics()


# =============================================================================
# Testing Utilities
# =============================================================================

async def create_test_session(user_id: str = "test_user") -> str:
    """Create a test session for development/testing."""
    memory = MemoryManager()
    return await memory.create_oprina_session(user_id)


async def populate_test_data(session_id: str):
    """Populate test data for development/testing."""
    memory = MemoryManager()
    
    # Add test messages
    test_messages = [
        {"type": "user_voice", "content": "Check my emails"},
        {"type": "agent_response", "content": "You have 5 unread emails"},
        {"type": "user_voice", "content": "Summarize the important ones"},
        {"type": "agent_response", "content": "Here are the important emails..."}
    ]
    
    for msg in test_messages:
        await memory.store_chat_message(
            session_id=session_id,
            message_type=msg["type"],
            content=msg["content"]
        )


# =============================================================================
# Development Mode Setup
# =============================================================================

def setup_development_mode():
    """Setup memory system for development with helpful defaults."""
    import os
    import logging
    
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Set development environment variables if not set
    dev_vars = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "ENABLE_REDIS_CACHING": "true",
        "LOG_LEVEL": "DEBUG"
    }
    
    for var, value in dev_vars.items():
        if not os.getenv(var):
            os.environ[var] = value
    
    print("🔧 Development mode configured")


# Auto-setup development mode if running module directly
if __name__ == "__main__":
    setup_development_mode()
    
    # Run quick health check
    import asyncio
    
    async def health_check():
        try:
            memory = await initialize_memory_system()
            print("✅ Memory system ready for development")
            
            # Print helpful info
            print("\nMemory System Status:")
            stats = get_memory_stats()
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            print("\nTroubleshooting:")
            print("1. Check your .env file exists and has required values")
            print("2. Ensure Redis server is running")
            print("3. Verify Supabase credentials are correct")
            print("4. Run: pip install -r requirements.txt")
    
    asyncio.run(health_check())