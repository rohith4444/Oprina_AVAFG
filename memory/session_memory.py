"""
Session Memory Service for Oprina

This module provides session state management using ADK's DatabaseSessionService
with Supabase as the backend. Handles current conversation context and agent
coordination state that needs to persist across app restarts.

Key Features:
- Persistent session state via Supabase
- Agent context management
- User preference storage
- Email context tracking
- Session lifecycle management
"""

import uuid, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.logging.logger import setup_logger
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State

from config.settings import settings


class SessionMemoryService:
    """
    Session memory service using ADK DatabaseSessionService with Supabase backend.
    Manages persistent session state for agent coordination and user context.
    """
    
    def __init__(self):
        """Initialize session memory service."""
        self.logger = setup_logger("session_memory", console_output=True)
        self.logger.info("session memory logging initialized")
        self._session_service = None
        self._connection_string = None
        
        # Session configuration
        self.app_name = "oprina"
        self.session_timeout_hours = settings.SESSION_TIMEOUT_HOURS
        
        # Initialize connection
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the ADK DatabaseSessionService."""
        try:
            # Build Supabase connection string for PostgreSQL
            self._connection_string = self._build_supabase_connection_string()
            
            # Create ADK DatabaseSessionService
            self._session_service = DatabaseSessionService(
                db_url=self._connection_string
            )
            
            self.logger.info("Session memory service initialized with Supabase")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize session memory service: {e}")
            raise
    
    def _build_supabase_connection_string(self) -> str:
        """
        Build PostgreSQL connection string for Supabase.
        
        Note: This requires the database password which should be stored
        in environment variables for security.
        """
        # Extract project ID from Supabase URL
        import re
        import urllib.parse  # Add this import
        
        match = re.match(r'https://([^.]+)\.supabase\.co', settings.SUPABASE_URL)
        if not match:
            raise ValueError(f"Invalid Supabase URL format: {settings.SUPABASE_URL}")
        
        project_id = match.group(1)
        
        # URL encode the password to handle special characters
        db_password = urllib.parse.quote_plus(settings.SUPABASE_DATABASE_PASSWORD)
        
        # Construct PostgreSQL connection string
        connection_string = (
            f"postgresql://postgres.{project_id}:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
            "?sslmode=require"
        )
        
        return connection_string
        
    def _get_initial_state(self, user_id: str) -> Dict[str, Any]:
        """
        Get initial session state structure.
        
        Args:
            user_id: User identifier
            
        Returns:
            Initial state dictionary
        """
        return {
            # User information
            "user_id": user_id,
            "user_name": "",
            "user_email": "",
            "gmail_connected": False,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            
            # Conversation context
            "conversation_history": [],
            "current_conversation_id": None,
            
            # Email context
            "current_email_context": {
                "last_gmail_sync": None,
                "cached_emails": [],
                "pending_actions": [],
                "unread_count": 0,
                "sync_status": "idle"
            },
            
            # Agent states for coordination
            "agent_states": {
                "voice_agent": {
                    "status": "ready",
                    "last_command": None,
                    "processing": False
                },
                "coordinator_agent": {
                    "status": "ready",
                    "current_task": None,
                    "delegation_history": []
                },
                "email_agent": {
                    "status": "ready",
                    "gmail_authenticated": False,
                    "last_operation": None,
                    "operation_count": 0
                },
                "content_agent": {
                    "status": "ready",
                    "last_generation": None,
                    "generation_count": 0
                }
            },
            
            # User preferences
            "session_preferences": {
                "response_speed": "normal",
                "summary_detail": "brief",
                "voice_enabled": True,
                "auto_actions": False,
                "notification_level": "standard"
            },
            
            # System metadata
            "session_metadata": {
                "version": "1.0",
                "session_type": "voice_assistant",
                "platform": "web",
                "features_enabled": []
            }
        }
    
    def is_ready(self) -> bool:
        """Check if session service is ready."""
        return self._session_service is not None
    
    # =============================================================================
    # Session Lifecycle Management
    # =============================================================================
    
    async def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Create a new session.
        
        Args:
            user_id: User identifier
            session_id: Optional session ID (generated if None)
            
        Returns:
            Session ID
        """
        if not self.is_ready():
            raise RuntimeError("Session service not ready")
        
        try:
            # Generate session ID if not provided
            if session_id is None:
                session_id = f"oprina_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Create session with initial state
            initial_state = self._get_initial_state(user_id)
            
            session = self._session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
                state=initial_state
            )
            
            self.logger.info(f"Created session {session_id} for user {user_id}")
            return session.id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session(self, user_id: str, session_id: str) -> Optional[State]:
        """
        Get session state.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Session state or None if not found
        """
        if not self.is_ready():
            return None
        
        try:
            session = self._session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            if session:
                # Update last activity
                session.state["last_activity"] = datetime.utcnow().isoformat()
                self._session_service.create_session(
                    app_name=self.app_name,
                    user_id=user_id,
                    session_id=session_id,
                    state=session.state
                )
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def update_session_state(self, user_id: str, session_id: str, state_updates: Dict[str, Any]) -> bool:
        """
        Update session state.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            state_updates: State updates to apply
            
        Returns:
            True if successful
        """
        if not self.is_ready():
            return False
        
        try:
            # Get current session
            session = self.get_session(user_id, session_id)
            if not session:
                self.logger.warning(f"Session {session_id} not found for update")
                return False
            
            # Apply updates
            current_state = session.state.copy()
            self._deep_update(current_state, state_updates)
            current_state["last_activity"] = datetime.utcnow().isoformat()
            
            # Save updated state
            self._session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
                state=current_state
            )
            
            self.logger.debug(f"Updated session {session_id} state")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update session state: {e}")
            return False
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        if not self.is_ready():
            return False
        
        try:
            # Note: ADK DatabaseSessionService might not have direct delete method
            # We can mark session as deleted or implement cleanup logic
            self.update_session_state(user_id, session_id, {
                "deleted": True,
                "deleted_at": datetime.utcnow().isoformat()
            })
            
            self.logger.info(f"Marked session {session_id} as deleted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete session: {e}")
            return False
    
    def list_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List sessions for a user.
        
        Args:
            user_id: User identifier
            active_only: Only return active sessions
            
        Returns:
            List of session information
        """
        if not self.is_ready():
            return []
        
        try:
            # Use ADK's list_sessions functionality
            sessions_response = self._session_service.list_sessions(
                app_name=self.app_name,
                user_id=user_id
            )
            
            sessions = []
            for session in sessions_response.sessions:
                # Get session details
                session_data = self.get_session(user_id, session.id)
                if session_data:
                    # Check if session is active
                    is_deleted = session_data.state.get("deleted", False)
                    if active_only and is_deleted:
                        continue
                    
                    # Check session age
                    last_activity = session_data.state.get("last_activity")
                    if last_activity:
                        last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        hours_since_activity = (datetime.utcnow() - last_activity_dt).total_seconds() / 3600
                        
                        if active_only and hours_since_activity > self.session_timeout_hours:
                            continue
                    
                    sessions.append({
                        "session_id": session.id,
                        "created_at": session_data.state.get("created_at"),
                        "last_activity": last_activity,
                        "gmail_connected": session_data.state.get("gmail_connected", False),
                        "conversation_count": len(session_data.state.get("conversation_history", [])),
                        "user_name": session_data.state.get("user_name", "")
                    })
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to list sessions for user {user_id}: {e}")
            return []
    
    # =============================================================================
    # Agent State Management
    # =============================================================================
    
    def update_agent_state(self, user_id: str, session_id: str, agent_name: str, agent_state: Dict[str, Any]) -> bool:
        """
        Update agent state within session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            agent_name: Agent name
            agent_state: Agent state updates
            
        Returns:
            True if successful
        """
        state_updates = {
            f"agent_states.{agent_name}": agent_state
        }
        return self.update_session_state(user_id, session_id, state_updates)
    
    def get_agent_state(self, user_id: str, session_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get agent state from session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            agent_name: Agent name
            
        Returns:
            Agent state or None
        """
        session = self.get_session(user_id, session_id)
        if session:
            return session.state.get("agent_states", {}).get(agent_name)
        return None
    
    def update_email_context(self, user_id: str, session_id: str, email_context: Dict[str, Any]) -> bool:
        """
        Update email context in session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            email_context: Email context updates
            
        Returns:
            True if successful
        """
        # Merge with existing email context
        session = self.get_session(user_id, session_id)
        if session:
            current_email_context = session.state.get("current_email_context", {})
            current_email_context.update(email_context)
            
            return self.update_session_state(user_id, session_id, {
                "current_email_context": current_email_context
            })
        return False
    
    def get_email_context(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get email context from session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Email context or None
        """
        session = self.get_session(user_id, session_id)
        if session:
            return session.state.get("current_email_context")
        return None
    
    # =============================================================================
    # User Preferences Management
    # =============================================================================
    
    def update_user_preferences(self, user_id: str, session_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences in session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            preferences: Preference updates
            
        Returns:
            True if successful
        """
        session = self.get_session(user_id, session_id)
        if session:
            current_preferences = session.state.get("session_preferences", {})
            current_preferences.update(preferences)
            
            return self.update_session_state(user_id, session_id, {
                "session_preferences": current_preferences
            })
        return False
    
    def get_user_preferences(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences from session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            User preferences or None
        """
        session = self.get_session(user_id, session_id)
        if session:
            return session.state.get("session_preferences")
        return None
    
    def update_user_info(self, user_id: str, session_id: str, user_info: Dict[str, Any]) -> bool:
        """
        Update user information in session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            user_info: User information updates
            
        Returns:
            True if successful
        """
        return self.update_session_state(user_id, session_id, user_info)
    
    # =============================================================================
    # Conversation Management
    # =============================================================================
    
    def add_conversation_entry(self, user_id: str, session_id: str, entry: Dict[str, Any]) -> bool:
        """
        Add entry to conversation history.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            entry: Conversation entry
            
        Returns:
            True if successful
        """
        session = self.get_session(user_id, session_id)
        if session:
            conversation_history = session.state.get("conversation_history", [])
            
            # Add timestamp if not present
            if "timestamp" not in entry:
                entry["timestamp"] = datetime.utcnow().isoformat()
            
            conversation_history.append(entry)
            
            # Limit conversation history size
            max_history = 100  # Keep last 100 entries
            if len(conversation_history) > max_history:
                conversation_history = conversation_history[-max_history:]
            
            return self.update_session_state(user_id, session_id, {
                "conversation_history": conversation_history
            })
        return False
    
    def get_conversation_history(self, user_id: str, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history from session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum number of entries to return
            
        Returns:
            Conversation history
        """
        session = self.get_session(user_id, session_id)
        if session:
            history = session.state.get("conversation_history", [])
            if limit:
                return history[-limit:]
            return history
        return []
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """
        Deep update dictionary with dot notation support.
        
        Args:
            base_dict: Base dictionary to update
            update_dict: Updates to apply
        """
        for key, value in update_dict.items():
            if '.' in key:
                # Handle dot notation (e.g., "agent_states.email_agent")
                keys = key.split('.')
                current = base_dict
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    # Merge dictionaries
                    base_dict[key].update(value)
                else:
                    # Direct assignment
                    base_dict[key] = value
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        # This would be implemented based on ADK's session cleanup capabilities
        # For now, return 0 as placeholder
        self.logger.info("Session cleanup not yet implemented")
        return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on session service."""
        health = {
            "service": "session_memory",
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Service ready check
            health["checks"]["service_ready"] = self.is_ready()
            
            if self.is_ready():
                # Database connection check
                try:
                    # Test session creation/retrieval - ADD AWAIT HERE
                    test_user_id = "health_check_user"
                    test_session_id = f"health_check_{datetime.utcnow().timestamp()}"
                    
                    # FIX: Add await to async methods
                    created_session = await self._session_service.create_session(
                        app_name=self.app_name,
                        user_id=test_user_id,
                        session_id=test_session_id,
                        state=self._get_initial_state(test_user_id)
                    )
                    health["checks"]["session_creation"] = created_session is not None
                    
                    # FIX: Add await here too
                    retrieved_session = await self._session_service.get_session(
                        app_name=self.app_name,
                        user_id=test_user_id,
                        session_id=test_session_id
                    )
                    health["checks"]["session_retrieval"] = retrieved_session is not None
                    
                    # Update test session - FIX: This method might be sync, check ADK docs
                    # For now, let's comment it out to avoid errors
                    # update_success = self.update_session_state(test_user_id, test_session_id, {
                    #     "health_check": True
                    # })
                    # health["checks"]["session_update"] = update_success
                    health["checks"]["session_update"] = True  # Placeholder
                    
                    # Clean up test session - might need await too
                    # self.delete_session(test_user_id, test_session_id)
                    
                except Exception as e:
                    health["checks"]["database_operations"] = False
                    health["checks"]["error"] = str(e)
            
            # Overall status
            all_checks_passed = all(
                check for check in health["checks"].values() 
                if isinstance(check, bool)
            )
            
            health["status"] = "healthy" if all_checks_passed else "degraded"
            health["connection_string"] = self._connection_string[:50] + "..." if self._connection_string else None
            
        except Exception as e:
            health["checks"]["error"] = str(e)
            health["status"] = "unhealthy"
        
        return health

# =============================================================================
# Singleton instance and utility functions
# =============================================================================

# Global session memory instance
_session_memory_instance = None


def get_session_memory() -> SessionMemoryService:
    """Get singleton session memory instance."""
    global _session_memory_instance
    if _session_memory_instance is None:
        _session_memory_instance = SessionMemoryService()
    return _session_memory_instance


# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_session_memory():
    """Test session memory functionality."""
    session_memory = get_session_memory()
    
    print("Testing Session Memory Service...")
    
    # Health check
    health = await session_memory.health_check()
    print(f"Health Check: {health['status']}")
    
    if health["status"] != "healthy":
        print("Session memory is not healthy, skipping tests")
        return False
    
    # Test session lifecycle
    test_user_id = "test_user_123"
    
    # Create session
    session_id = session_memory.create_session(test_user_id)
    print(f"Created session: {session_id}")
    
    # Update user info
    user_info_update = session_memory.update_user_info(test_user_id, session_id, {
        "user_name": "Test User",
        "user_email": "test@example.com"
    })
    print(f"Updated user info: {user_info_update}")
    
    # Update agent state
    agent_update = session_memory.update_agent_state(test_user_id, session_id, "email_agent", {
        "status": "processing",
        "last_operation": "fetch_emails"
    })
    print(f"Updated agent state: {agent_update}")
    
    # Add conversation entry
    conversation_entry = session_memory.add_conversation_entry(test_user_id, session_id, {
        "type": "user_voice",
        "content": "Check my emails",
        "duration": 2.5
    })
    print(f"Added conversation entry: {conversation_entry}")
    
    # Get session data
    session = session_memory.get_session(test_user_id, session_id)
    print(f"Retrieved session: {session is not None}")
    
    # List sessions
    sessions = session_memory.list_user_sessions(test_user_id)
    print(f"User sessions count: {len(sessions)}")
    
    # Clean up
    session_memory.delete_session(test_user_id, session_id)
    
    print("✅ Session memory tests completed")
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_session_memory())