"""
Session Memory Service for Oprina - FIXED VERSION

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

import uuid, sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.logging.logger import setup_logger
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from google.adk.sessions import DatabaseSessionService
from google.adk.sessions.state import State
from google.adk.events import Event, EventActions

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
        import urllib.parse
        
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
    # Session Lifecycle Management - FIXED ASYNC METHODS
    # =============================================================================
    
    async def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Create a new session - ONLY for new sessions.
        
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
            
            # Check if session already exists
            try:
                existing_session = await self._session_service.get_session(
                    app_name=self.app_name,
                    user_id=user_id,
                    session_id=session_id
                )
                
                if existing_session:
                    self.logger.info(f"Session {session_id} already exists, returning existing session")
                    return session_id
            except Exception:
                # Session doesn't exist, continue with creation
                pass
            
            # Create session with initial state ONLY if it doesn't exist
            initial_state = self._get_initial_state(user_id)
            
            session = await self._session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
                state=initial_state
            )
            
            self.logger.info(f"Created NEW session {session_id} for user {user_id}")
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
            session = await self._session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            if session:
                # # Update last activity timestamp using the correct method
                # await self.update_session_state(user_id, session_id, {
                #     "last_activity": datetime.utcnow().isoformat()
                # })
                
                # # Return the session (it will have updated state)
                # updated_session = await self._session_service.get_session(
                #     app_name=self.app_name,
                #     user_id=user_id,
                #     session_id=session_id
                # )
                return session
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            return None
        
    async def update_last_activity(self, user_id: str, session_id: str) -> bool:
        """
        Update last activity timestamp for a session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        return await self.update_session_state(user_id, session_id, {
            "last_activity": datetime.utcnow().isoformat()
        })


    async def update_session_state(self, user_id: str, session_id: str, state_updates: Dict[str, Any]) -> bool:
        """
        Update session state using ADK's append_event with state_delta.
        This is the correct way to update state in ADK.
        
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
            # Get current session first
            session = await self._session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            if not session:
                self.logger.warning(f"Session {session_id} not found for update")
                return False
            
            # Apply deep updates to handle nested state changes
            processed_updates = self._process_state_updates(state_updates)
            
            # Create EventActions with state_delta
            actions_with_update = EventActions(state_delta=processed_updates)
            
            # Create system event for state update
            system_event = Event(
                invocation_id=f"state_update_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                author="system",
                actions=actions_with_update,
                timestamp=time.time()
            )
            
            # Use append_event to update state (this is the correct ADK way)
            await self._session_service.append_event(session, system_event)
            
            self.logger.debug(f"Updated session {session_id} state using append_event")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update session state: {e}")
            return False


    def _process_state_updates(self, state_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process state updates to handle dot notation and nested updates.
        
        Args:
            state_updates: Updates to process
            
        Returns:
            Processed updates ready for ADK
        """
        processed = {}
        
        for key, value in state_updates.items():
            if '.' in key:
                # Handle dot notation (e.g., "agent_states.email_agent")
                keys = key.split('.')
                current = processed
                
                # Navigate/create nested structure
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                # Set the final value
                current[keys[-1]] = value
            else:
                # Direct key assignment
                processed[key] = value
        
        return processed

    async def delete_session(self, user_id: str, session_id: str) -> bool:
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
            # FIXED: Add await here
            await self._session_service.delete_session(  # Add await
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            self.logger.info(f"Marked session {session_id} as deleted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete session: {e}")
            return False
    
    async def list_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
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
            # FIXED: Add await here
            sessions_response = await self._session_service.list_sessions(
                app_name=self.app_name,
                user_id=user_id
            )
            
            sessions = []
            for session in sessions_response.sessions:
                # FIXED: Add await here
                session_data = await self.get_session(user_id, session.id)
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
    # Agent State Management - FIXED ASYNC METHODS
    # =============================================================================
    
    async def update_agent_state(self, user_id: str, session_id: str, agent_name: str, agent_state: Dict[str, Any]) -> bool:
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
        # FIXED: Add await here
        return await self.update_session_state(user_id, session_id, state_updates)
    
    async def get_agent_state(self, user_id: str, session_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get agent state from session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            agent_name: Agent name
            
        Returns:
            Agent state or None
        """
        # FIXED: Add await here
        session = await self.get_session(user_id, session_id)
        if session:
            return session.state.get("agent_states", {}).get(agent_name)
        return None
    
    async def update_email_context(self, user_id: str, session_id: str, email_context: Dict[str, Any]) -> bool:
        """
        Update email context in session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            email_context: Email context updates
            
        Returns:
            True if successful
        """
        # FIXED: Add await here
        session = await self.get_session(user_id, session_id)
        if session:
            current_email_context = session.state.get("current_email_context", {})
            current_email_context.update(email_context)
            
            # FIXED: Add await here
            return await self.update_session_state(user_id, session_id, {
                "current_email_context": current_email_context
            })
        return False
    
    async def get_email_context(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get email context from session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Email context or None
        """
        # FIXED: Add await here
        session = await self.get_session(user_id, session_id)
        if session:
            return session.state.get("current_email_context")
        return None
    
    # =============================================================================
    # User Preferences Management - FIXED ASYNC METHODS
    # =============================================================================
    
    async def update_user_preferences(self, user_id: str, session_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences in session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            preferences: Preference updates
            
        Returns:
            True if successful
        """
        # FIXED: Add await here
        session = await self.get_session(user_id, session_id)
        if session:
            current_preferences = session.state.get("session_preferences", {})
            current_preferences.update(preferences)
            
            # FIXED: Add await here
            return await self.update_session_state(user_id, session_id, {
                "session_preferences": current_preferences
            })
        return False
    
    async def get_user_preferences(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences from session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            User preferences or None
        """
        # FIXED: Add await here
        session = await self.get_session(user_id, session_id)
        if session:
            return session.state.get("session_preferences")
        return None
    
    async def update_user_info(self, user_id: str, session_id: str, user_info: Dict[str, Any]) -> bool:
        """
        Update user information in session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            user_info: User information updates
            
        Returns:
            True if successful
        """
        # FIXED: Add await here
        return await self.update_session_state(user_id, session_id, user_info)
    
    # =============================================================================
    # Conversation Management - FIXED ASYNC METHODS
    # =============================================================================
    
    async def add_conversation_entry(self, user_id: str, session_id: str, entry: Dict[str, Any]) -> bool:
        """
        Add entry to conversation history.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            entry: Conversation entry
            
        Returns:
            True if successful
        """
        # FIXED: Add await here
        session = await self.get_session(user_id, session_id)
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
            
            # FIXED: Add await here
            return await self.update_session_state(user_id, session_id, {
                "conversation_history": conversation_history
            })
        return False
    
    async def get_conversation_history(self, user_id: str, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history from session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum number of entries to return
            
        Returns:
            Conversation history
        """
        # FIXED: Add await here
        session = await self.get_session(user_id, session_id)
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
                    # Test session creation/retrieval - REMOVE await
                    test_user_id = "health_check_user"
                    test_session_id = f"health_check_{datetime.utcnow().timestamp()}"
                    
                    # These are SYNCHRONOUS calls in ADK
                    created_session = await self._session_service.create_session(
                        app_name=self.app_name,
                        user_id=test_user_id,
                        session_id=test_session_id,
                        state=self._get_initial_state(test_user_id)
                    )
                    health["checks"]["session_creation"] = created_session is not None
                    
                    # Test state update using the correct method
                    update_success = await self.update_session_state(test_user_id, test_session_id, {
                        "health_check": True
                    })
                    health["checks"]["session_update"] = update_success
                    
                    # Clean up test session
                    await self._session_service.delete_session(
                        app_name=self.app_name,
                        user_id=test_user_id,
                        session_id=test_session_id
                    )
                    
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
# Testing and Development Utilities - FIXED ASYNC TEST
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
    session_id = await session_memory.create_session(test_user_id)  # ✅ Awaited
    print(f"Created session: {session_id}")
    
    # Update user info
    user_info_update = await session_memory.update_user_info(test_user_id, session_id, {  # ✅ Awaited
        "user_name": "Test User",
        "user_email": "test@example.com"
    })
    print(f"Updated user info: {user_info_update}")
    
    # Update agent state
    agent_update = await session_memory.update_agent_state(test_user_id, session_id, "email_agent", {  # ✅ Awaited
        "status": "processing",
        "last_operation": "fetch_emails"
    })
    print(f"Updated agent state: {agent_update}")
    
    # Add conversation entry
    conversation_entry = await session_memory.add_conversation_entry(test_user_id, session_id, {  # ✅ Awaited
        "type": "user_voice",
        "content": "Check my emails",
        "duration": 2.5
    })
    print(f"Added conversation entry: {conversation_entry}")
    
    # Get session data
    session = await session_memory.get_session(test_user_id, session_id)  # ✅ Awaited
    print(f"Retrieved session: {session is not None}")
    
    # List sessions
    sessions = await session_memory.list_user_sessions(test_user_id)  # This one can stay sync
    print(f"User sessions count: {len(sessions)}")
    
    # Update last activity explicitly
    await session_memory.update_last_activity(test_user_id, session_id)  # ✅ New method
    
    # Clean up
    await session_memory.delete_session(test_user_id, session_id)  # ✅ Awaited
    
    print("✅ Session memory tests completed")
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_session_memory())