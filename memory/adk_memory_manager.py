"""
ADK Memory Manager - Simplified Service Configuration Helper

This module provides a streamlined ADK service configuration helper that:
- Sets up ADK services based on settings  
- Provides health monitoring
- Handles UI chat history (separate from session state)
- Offers debugging utilities

ADK handles all session lifecycle automatically - we don't manage it manually.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

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
    Simplified ADK Service Configuration Helper.
    
    Purpose:
    - Configure ADK services based on settings
    - Provide health monitoring and debugging
    - Handle UI chat history (separate from ADK session state)
    - Service information utilities
    
    What ADK Handles Automatically:
    - Session creation/deletion/lifecycle
    - Session state management via tool_context
    - Agent responses via output_key
    - Cross-session memory via load_memory tool
    """
    
    def __init__(self):
        """Initialize ADK service configuration helper."""
        self.logger = logger
        self.logger.info("Initializing ADK Service Configuration Helper...")
        
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
        
        self.logger.info("ADK Service Configuration Helper initialized successfully")
    
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
                f"Services configured: "
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
                self.logger.info("Configuring ADK DatabaseSessionService...")
                self._session_service = DatabaseSessionService(
                    db_url=self.session_config["db_url"]
                )
                self.logger.info("✅ DatabaseSessionService configured with Supabase")
                
            else:  # inmemory
                self.logger.info("Configuring ADK InMemorySessionService...")
                self._session_service = InMemorySessionService()
                self.logger.info("✅ InMemorySessionService configured")
                
        except Exception as e:
            self.logger.error(f"Failed to configure session service: {e}")
            raise
    
    def _initialize_memory_service(self):
        """Initialize ADK memory service based on configuration."""
        try:
            if self.memory_config["type"] == "vertexai_rag":
                self.logger.info("Configuring ADK VertexAiRagMemoryService...")
                self._memory_service = VertexAiRagMemoryService(
                    rag_corpus=self.memory_config["rag_corpus"]
                )
                self.logger.info("✅ VertexAiRagMemoryService configured")
                
            else:  # inmemory
                self.logger.info("Configuring ADK InMemoryMemoryService...")
                self._memory_service = InMemoryMemoryService()
                self.logger.info("✅ InMemoryMemoryService configured")
                
        except Exception as e:
            self.logger.error(f"Failed to configure memory service: {e}")
            raise
    
    def _initialize_chat_history(self):
        """Initialize chat history service for UI."""
        try:
            if settings.CHAT_HISTORY_ENABLED:
                self._chat_history = get_chat_history()
                self.logger.info("✅ ChatHistoryService configured for UI")
            else:
                self._chat_history = None
                self.logger.info("ChatHistoryService disabled")
                
        except Exception as e:
            self.logger.warning(f"Chat history service configuration failed: {e}")
            self._chat_history = None
    
    # =============================================================================
    # Service Access Methods (for ADK Runner creation)
    # =============================================================================
    
    def get_session_service(self):
        """Get configured session service for ADK Runner."""
        return self._session_service
    
    def get_memory_service(self):
        """Get configured memory service for ADK Runner."""
        return self._memory_service
    
    # =============================================================================
    # UI Chat History Integration (Separate from ADK Sessions)
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
            metadata: Additional message metadata
            
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
    # Health Check and Monitoring
    # =============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on ADK service configuration.
        
        Returns:
            Health check results
        """
        health = {
            "service": "adk_service_configuration",
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Check ADK availability
            health["checks"]["adk_available"] = ADK_AVAILABLE
            
            # Check session service
            health["checks"]["session_service_configured"] = self._session_service is not None
            health["checks"]["session_service_type"] = self.session_config["type"]
            
            # Check memory service
            health["checks"]["memory_service_configured"] = self._memory_service is not None
            health["checks"]["memory_service_type"] = self.memory_config["type"]
            
            # Check chat history service
            health["checks"]["chat_history_available"] = self._chat_history is not None
            
            # Test basic service access
            if self._session_service and self._memory_service:
                health["checks"]["services_accessible"] = True
            else:
                health["checks"]["services_accessible"] = False
            
            # Overall status
            critical_checks = [
                "adk_available",
                "session_service_configured",
                "memory_service_configured",
                "services_accessible"
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
                "configured": self._session_service is not None
            },
            "memory_service": {
                "type": self.memory_config["type"],
                "configured": self._memory_service is not None
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
    """Get singleton ADK service configuration helper instance."""
    global _adk_memory_manager
    if _adk_memory_manager is None:
        _adk_memory_manager = OprinaMemoryManager()
    return _adk_memory_manager


# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_simplified_adk_memory_manager():
    """Test simplified ADK memory manager functionality."""
    logger.info("🧪 Testing Simplified ADK Service Configuration Helper...")
    
    try:
        # Initialize manager
        manager = get_adk_memory_manager()
        logger.info("✅ Manager initialized")
        
        # Health check
        health = await manager.health_check()
        logger.info(f"Health Status: {health['status']}")
        
        # Test service access
        session_service = manager.get_session_service()
        memory_service = manager.get_memory_service()
        
        logger.info(f"✅ Session Service: {session_service is not None}")
        logger.info(f"✅ Memory Service: {memory_service is not None}")
        
        # Test UI chat history (if enabled)
        if manager._chat_history:
            test_user_id = "test_user_123"
            test_session_id = "test_session_456"
            
            message_id = await manager.store_ui_message(
                test_user_id, test_session_id, "user_voice", "Test message"
            )
            logger.info(f"✅ Stored UI message: {message_id}")
            
            conversations = manager.get_conversation_history_for_ui(test_user_id)
            logger.info(f"✅ Retrieved conversations: {len(conversations)}")
        
        # Get service info
        service_info = manager.get_service_info()
        logger.info(f"✅ Service info: {service_info}")
        
        logger.info("🎉 Simplified ADK Memory Manager test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Simplified ADK Memory Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run test
    import asyncio
    asyncio.run(test_simplified_adk_memory_manager())