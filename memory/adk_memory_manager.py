"""
ADK Memory Manager - Complete Implementation

This module provides a complete ADK-native memory facade that connects:
- ADK SessionService (conversation state & history)
- ADK MemoryService (cross-session knowledge)
- ADK Runner (agent execution with session context)
- ChatHistoryService (UI conversation lists)

Key Features:
- Proper ADK session lifecycle management
- Cross-session memory with load_memory tool
- Tool context injection for session state access
- Configurable service types (inmemory for dev, database/rag for production)
"""

import os
import sys
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Add project root to path for imports
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(2):  # Go up 2 levels to reach project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.logging.logger import setup_logger
from config.settings import settings

# ADK Imports
try:
    from google.adk.sessions import DatabaseSessionService, InMemorySessionService
    from google.adk.memory import InMemoryMemoryService, VertexAiRagMemoryService
    from google.adk.runners import Runner
    from google.adk.sessions.state import State
    from google.adk.events import Event, EventActions
    from google.genai.types import Content, Part
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    ADK_IMPORT_ERROR = str(e)

# Chat History Service (keep for UI)
from memory.chat_history import ChatHistoryService, get_chat_history

# Configure logging
logger = setup_logger("adk_memory_manager", console_output=True)


class OprinaMemoryManager:
    """
    Complete ADK Memory Manager that provides proper session and memory services.
    
    This replaces all custom memory implementations with ADK-native patterns:
    - DatabaseSessionService for persistent conversation state
    - VertexAiRagMemoryService for cross-session knowledge
    - ChatHistoryService for UI conversation lists
    - Proper Runner integration for agent execution
    """
    
    def __init__(self):
        """Initialize ADK memory manager with configured services."""
        self.logger = logger
        self.logger.info("Initializing Complete ADK Memory Manager...")
        
        # Check ADK availability
        if not ADK_AVAILABLE:
            self.logger.error(f"ADK not available: {ADK_IMPORT_ERROR}")
            raise ImportError(f"ADK dependencies not available: {ADK_IMPORT_ERROR}")
        
        # Initialize services
        self._session_service = None
        self._memory_service = None
        self._chat_history = None
        
        # Service configuration
        self.app_name = settings.ADK_APP_NAME
        self.session_config = settings.get_session_service_config()
        self.memory_config = settings.get_memory_service_config()
        
        # Initialize all services
        self._initialize_services()
        
        self.logger.info("Complete ADK Memory Manager initialized successfully")
    
    def _initialize_services(self):
        """Initialize ADK session and memory services based on configuration."""
        try:
            # Initialize Session Service
            self._initialize_session_service()
            
            # Initialize Memory Service
            self._initialize_memory_service()
            
            # Initialize Chat History Service (for UI)
            self._initialize_chat_history()
            
            self.logger.info(
                f"Services initialized: "
                f"Session={self.session_config['type']}, "
                f"Memory={self.memory_config['type']}, "
                f"ChatHistory={'enabled' if self._chat_history else 'disabled'}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ADK services: {e}")
            raise
    
    def _initialize_session_service(self):
        """Initialize ADK session service based on configuration."""
        try:
            if self.session_config["type"] == "database":
                self.logger.info("Initializing ADK DatabaseSessionService...")
                self._session_service = DatabaseSessionService(
                    db_url=self.session_config["db_url"]
                )
                self.logger.info("✅ DatabaseSessionService initialized with Supabase")
                
            else:  # inmemory
                self.logger.info("Initializing ADK InMemorySessionService...")
                self._session_service = InMemorySessionService()
                self.logger.info("✅ InMemorySessionService initialized")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize session service: {e}")
            raise
    
    def _initialize_memory_service(self):
        """Initialize ADK memory service based on configuration."""
        try:
            if self.memory_config["type"] == "vertexai_rag":
                self.logger.info("Initializing ADK VertexAiRagMemoryService...")
                self._memory_service = VertexAiRagMemoryService(
                    rag_corpus=self.memory_config["rag_corpus"]
                )
                self.logger.info("✅ VertexAiRagMemoryService initialized")
                
            else:  # inmemory
                self.logger.info("Initializing ADK InMemoryMemoryService...")
                self._memory_service = InMemoryMemoryService()
                self.logger.info("✅ InMemoryMemoryService initialized")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize memory service: {e}")
            raise
    
    def _initialize_chat_history(self):
        """Initialize chat history service for UI."""
        try:
            if settings.CHAT_HISTORY_ENABLED:
                self._chat_history = get_chat_history()
                self.logger.info("✅ ChatHistoryService initialized for UI")
            else:
                self._chat_history = None
                self.logger.info("ChatHistoryService disabled")
                
        except Exception as e:
            self.logger.warning(f"Chat history service initialization failed: {e}")
            self._chat_history = None
    
    # =============================================================================
    # ADK Runner Integration (Core Feature)
    # =============================================================================
    
    def create_runner(self, agent) -> Runner:
        """
        Create ADK Runner for agent with proper session and memory service integration.
        This is the key method that connects agents to ADK services.
        
        Args:
            agent: ADK Agent instance (LlmAgent, etc.)
            
        Returns:
            Configured ADK Runner with session and memory services
        """
        try:
            self.logger.info(f"Creating ADK Runner for agent: {agent.name}")
            
            runner = Runner(
                agent=agent,
                app_name=self.app_name,
                session_service=self._session_service,
                memory_service=self._memory_service
            )
            
            self.logger.info(f"✅ ADK Runner created for {agent.name}")
            return runner
            
        except Exception as e:
            self.logger.error(f"Failed to create Runner for {agent.name}: {e}")
            raise
    
    # =============================================================================
    # Session Management (ADK Native)
    # =============================================================================
    
    async def create_session(self, user_id: str, initial_state: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new ADK session with proper state initialization.
        
        Args:
            user_id: User identifier
            initial_state: Optional initial session state
            
        Returns:
            Session ID
        """
        try:
            # Prepare initial state with ADK state prefixes
            state = self._prepare_initial_state(user_id, initial_state)
            
            # Create ADK session
            session = await self._session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                state=state
            )
            
            self.logger.info(f"Created ADK session {session.id} for user {user_id}")
            
            # Create corresponding chat history conversation if enabled
            if self._chat_history:
                try:
                    conversation_id = self._chat_history.auto_create_conversation_if_needed(
                        user_id, session.id
                    )
                    self.logger.debug(f"Chat history conversation: {conversation_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to create chat history conversation: {e}")
            
            return session.id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session(self, user_id: str, session_id: str):
        """
        Get ADK session by ID.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Session object or None
        """
        try:
            session = await self._session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            if session:
                self.logger.debug(f"Retrieved session {session_id} for user {user_id}")
                return session
            else:
                self.logger.debug(f"Session {session_id} not found for user {user_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def run_agent(
        self, 
        agent, 
        user_id: str, 
        session_id: str, 
        user_message: str
    ) -> List[Dict[str, Any]]:
        """
        Run agent with proper ADK Runner and session context.
        This is the main method for executing agents with session state.
        
        Args:
            agent: ADK Agent instance
            user_id: User identifier
            session_id: Session identifier
            user_message: User's message text
            
        Returns:
            List of events from agent execution
        """
        try:
            # Create runner for this agent
            runner = self.create_runner(agent)
            
            # Prepare user content
            user_content = Content(parts=[Part(text=user_message)])
            
            # Execute agent through runner (this provides tool_context automatically)
            events = []
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_content
            ):
                # Store UI message in chat history
                if self._chat_history:
                    try:
                        await self.store_ui_message(
                            user_id, session_id, 
                            "agent_response" if event.author == "agent" else event.author,
                            str(event.content) if event.content else "",
                            {"event_type": type(event).__name__}
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to store UI message: {e}")
                
                # Convert event to dict for return
                event_dict = {
                    "author": event.author,
                    "content": str(event.content) if event.content else "",
                    "timestamp": getattr(event, 'timestamp', time.time()),
                    "is_final": event.is_final_response() if hasattr(event, 'is_final_response') else False
                }
                events.append(event_dict)
                
                self.logger.debug(f"Agent event: {event.author} - {type(event).__name__}")
            
            self.logger.info(f"Agent {agent.name} completed execution with {len(events)} events")
            return events
            
        except Exception as e:
            self.logger.error(f"Failed to run agent {agent.name}: {e}")
            return [{
                "author": "system",
                "content": f"Error running agent: {str(e)}",
                "timestamp": time.time(),
                "is_final": True
            }]
    
    async def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List ADK sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session information
        """
        try:
            sessions_response = await self._session_service.list_sessions(
                app_name=self.app_name,
                user_id=user_id
            )
            
            sessions = []
            for session_info in sessions_response.sessions:
                # Get full session details
                session = await self.get_session(user_id, session_info.id)
                if session:
                    sessions.append({
                        "session_id": session_info.id,
                        "user_id": user_id,
                        "created_at": session.state.get("created_at"),
                        "last_activity": session.state.get("user:last_activity"),
                        "user_name": session.state.get("user:name", ""),
                        "gmail_connected": session.state.get("user:gmail_connected", False),
                        "event_count": len(session.events) if hasattr(session, 'events') else 0
                    })
            
            self.logger.debug(f"Listed {len(sessions)} sessions for user {user_id}")
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to list sessions for user {user_id}: {e}")
            return []
    
    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """
        Delete an ADK session and optionally archive to memory.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            # Add to memory before deletion if enabled
            if settings.ENABLE_CROSS_SESSION_MEMORY:
                await self._archive_session_to_memory(user_id, session_id)
            
            # Delete from ADK session service
            await self._session_service.delete_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            self.logger.info(f"Deleted session {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    # =============================================================================
    # Memory Management (Cross-Session Knowledge)
    # =============================================================================
    
    async def add_session_to_memory(self, user_id: str, session_id: str) -> bool:
        """
        Add completed session to long-term memory for cross-session retrieval.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            if not settings.ENABLE_CROSS_SESSION_MEMORY:
                self.logger.debug("Cross-session memory disabled, skipping archive")
                return True
            
            session = await self.get_session(user_id, session_id)
            if not session:
                self.logger.warning(f"Cannot archive non-existent session {session_id}")
                return False
            
            # Check if session has meaningful content (more than just initialization)
            if hasattr(session, 'events') and len(session.events) > 2:
                await self._memory_service.add_session_to_memory(session)
                self.logger.info(f"Added session {session_id} to long-term memory")
                return True
            else:
                self.logger.debug(f"Session {session_id} too short for memory archive")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add session to memory: {e}")
            return False
    
    # =============================================================================
    # Chat History Integration (UI Support)
    # =============================================================================
    
    async def store_ui_message(
        self,
        user_id: str,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store message in chat history for UI display (separate from ADK session).
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            message_type: Type of message (user_voice, agent_response, etc.)
            content: Message content
            metadata: Additional metadata
            
        Returns:
            Message ID if successful
        """
        try:
            if not self._chat_history:
                self.logger.debug("Chat history service not available")
                return None
            
            # Auto-create conversation if needed
            conversation_id = self._chat_history.auto_create_conversation_if_needed(
                user_id, session_id
            )
            
            # Store message
            message_id = self._chat_history.store_message(
                conversation_id, user_id, session_id, message_type, content, metadata
            )
            
            self.logger.debug(f"Stored UI message {message_id} in conversation {conversation_id}")
            return message_id
            
        except Exception as e:
            self.logger.error(f"Failed to store UI message: {e}")
            return None
    
    def get_conversation_history_for_ui(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get conversation history for UI display.
        
        Args:
            user_id: User identifier
            limit: Maximum conversations to return
            
        Returns:
            List of conversations for UI
        """
        try:
            if not self._chat_history:
                return []
            
            conversations = self._chat_history.list_user_conversations(user_id, limit=limit)
            
            # Convert to UI-friendly format
            ui_conversations = []
            for conv in conversations:
                ui_conversations.append({
                    "id": conv.id,
                    "title": conv.title,
                    "message_count": conv.message_count,
                    "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None
                })
            
            return ui_conversations
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation history for UI: {e}")
            return []
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def _prepare_initial_state(self, user_id: str, custom_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare initial session state with proper ADK state prefixes.
        
        Args:
            user_id: User identifier
            custom_state: Custom state to merge
            
        Returns:
            Properly structured initial state
        """
        # Base state with ADK prefixes
        state = {
            # Session-scoped (current conversation only)
            "conversation_active": True,
            "current_agent": "coordinator",
            "created_at": datetime.utcnow().isoformat(),
            
            # User-scoped (persistent across sessions)
            "user:id": user_id,
            "user:name": "",
            "user:email": "",
            "user:gmail_connected": False,
            "user:calendar_connected": False,
            "user:last_activity": datetime.utcnow().isoformat(),
            "user:preferences": {
                "response_style": "brief",
                "summary_detail": "moderate",
                "voice_enabled": True,
                "auto_actions": False
            },
            
            # App-scoped (global application data)
            "app:version": "1.0",
            "app:features": ["email", "calendar", "voice"],
            "app:name": self.app_name,
            
            # Temporary data (discarded after session)
            "temp:initializing": True,
            "temp:startup_time": time.time()
        }
        
        # Merge custom state if provided
        if custom_state:
            state.update(custom_state)
        
        return state
    
    async def _archive_session_to_memory(self, user_id: str, session_id: str):
        """Archive session to memory before deletion."""
        try:
            await self.add_session_to_memory(user_id, session_id)
        except Exception as e:
            self.logger.warning(f"Failed to archive session {session_id} to memory: {e}")
    
    # =============================================================================
    # Health Check and Status
    # =============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on ADK memory services.
        
        Returns:
            Health check results
        """
        health = {
            "service": "adk_memory_manager",
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Check ADK availability
            health["checks"]["adk_available"] = ADK_AVAILABLE
            
            # Check session service
            health["checks"]["session_service_available"] = self._session_service is not None
            health["checks"]["session_service_type"] = self.session_config["type"]
            
            # Check memory service
            health["checks"]["memory_service_available"] = self._memory_service is not None
            health["checks"]["memory_service_type"] = self.memory_config["type"]
            
            # Check chat history service
            health["checks"]["chat_history_available"] = self._chat_history is not None
            
            # Test basic operations if possible
            if self._session_service:
                try:
                    # Test session creation/deletion
                    test_session = await self._session_service.create_session(
                        app_name=self.app_name,
                        user_id="health_check_user",
                        state={"test": True}
                    )
                    
                    await self._session_service.delete_session(
                        app_name=self.app_name,
                        user_id="health_check_user",
                        session_id=test_session.id
                    )
                    
                    health["checks"]["session_operations"] = True
                except Exception as e:
                    health["checks"]["session_operations"] = False
                    health["checks"]["session_error"] = str(e)
            
            # Overall status
            critical_checks = [
                "adk_available",
                "session_service_available",
                "memory_service_available"
            ]
            
            all_critical_passed = all(
                health["checks"].get(check, False) for check in critical_checks
            )
            
            health["status"] = "healthy" if all_critical_passed else "degraded"
            
            # Add configuration info
            health["configuration"] = {
                "app_name": self.app_name,
                "session_type": self.session_config["type"],
                "memory_type": self.memory_config["type"],
                "chat_history_enabled": settings.CHAT_HISTORY_ENABLED,
                "cross_session_memory": settings.ENABLE_CROSS_SESSION_MEMORY,
                "session_persistence": settings.ENABLE_SESSION_PERSISTENCE
            }
            
        except Exception as e:
            health["checks"]["error"] = str(e)
            health["status"] = "unhealthy"
        
        return health
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about configured services."""
        return {
            "session_service": {
                "type": self.session_config["type"],
                "app_name": self.app_name,
                "available": self._session_service is not None
            },
            "memory_service": {
                "type": self.memory_config["type"],
                "available": self._memory_service is not None
            },
            "chat_history": {
                "enabled": settings.CHAT_HISTORY_ENABLED,
                "available": self._chat_history is not None
            },
            "features": {
                "cross_session_memory": settings.ENABLE_CROSS_SESSION_MEMORY,
                "session_persistence": settings.ENABLE_SESSION_PERSISTENCE
            }
        }


# =============================================================================
# Singleton and Context Managers
# =============================================================================

# Global memory manager instance
_adk_memory_manager = None


def get_adk_memory_manager() -> OprinaMemoryManager:
    """Get singleton ADK memory manager instance."""
    global _adk_memory_manager
    if _adk_memory_manager is None:
        _adk_memory_manager = OprinaMemoryManager()
    return _adk_memory_manager


@asynccontextmanager
async def adk_memory_context(user_id: str):
    """Context manager for ADK memory operations."""
    memory_manager = get_adk_memory_manager()
    
    try:
        yield memory_manager
    finally:
        # Cleanup if needed (ADK handles most cleanup automatically)
        pass


# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_complete_adk_memory_manager():
    """Test complete ADK memory manager functionality."""
    logger.info("🧪 Testing Complete ADK Memory Manager...")
    
    try:
        # Initialize manager
        manager = get_adk_memory_manager()
        logger.info("✅ Manager initialized")
        
        # Health check
        health = await manager.health_check()
        logger.info(f"Health Status: {health['status']}")
        
        # Test session operations
        test_user_id = "test_user_123"
        
        # Create session
        session_id = await manager.create_session(test_user_id, {
            "user:name": "Test User",
            "test_data": "hello world"
        })
        logger.info(f"✅ Created session: {session_id}")
        
        # Get session
        session = await manager.get_session(test_user_id, session_id)
        logger.info(f"✅ Retrieved session: {session is not None}")
        
        # Test Runner creation
        from google.adk.agents import LlmAgent
        from google.adk.models.lite_llm import LiteLlm
        
        test_agent = LlmAgent(
            name="test_agent",
            model=LiteLlm(model="gemini-2.0-flash", api_key="test"),
            instruction="Test agent",
            output_key="test_result"
        )
        
        runner = manager.create_runner(test_agent)
        logger.info(f"✅ Created Runner: {runner is not None}")
        
        # Store UI message
        if manager._chat_history:
            message_id = await manager.store_ui_message(
                test_user_id, session_id, "user_voice", "Test message"
            )
            logger.info(f"✅ Stored UI message: {message_id}")
        
        # List sessions
        sessions = await manager.list_user_sessions(test_user_id)
        logger.info(f"✅ Listed sessions: {len(sessions)}")
        
        # Test memory operations
        if settings.ENABLE_CROSS_SESSION_MEMORY:
            memory_added = await manager.add_session_to_memory(test_user_id, session_id)
            logger.info(f"✅ Added to memory: {memory_added}")
        
        # Get service info
        service_info = manager.get_service_info()
        logger.info(f"✅ Service info: {service_info}")
        
        # Cleanup
        await manager.delete_session(test_user_id, session_id)
        logger.info("✅ Cleaned up test session")
        
        logger.info("🎉 Complete ADK Memory Manager test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Complete ADK Memory Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run test
    asyncio.run(test_complete_adk_memory_manager())