"""
Chat History Service for Oprina

This module provides direct Supabase operations for storing and retrieving
chat history. This is separate from session state and focuses on permanent
storage of all user conversations for the conversation sidebar.

Key Features:
- Permanent conversation storage
- Searchable message history
- Conversation threading
- User conversation management
- Message metadata tracking
"""

import uuid
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from supabase import create_client, Client
from config.settings import settings


@dataclass
class ChatMessage:
    """Chat message data structure."""
    id: Optional[str] = None
    conversation_id: str = ""
    user_id: str = ""
    session_id: str = ""
    message_type: str = ""  # user_voice, agent_response, system, etc.
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Conversation:
    """Conversation data structure."""
    id: Optional[str] = None
    user_id: str = ""
    title: str = ""
    session_id: str = ""
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatHistoryService:
    """
    Chat history service using direct Supabase operations.
    Manages permanent storage of conversations and messages.
    """
    
    def __init__(self):
        """Initialize chat history service."""
        self.logger = logging.getLogger("chat_history")
        self._client: Optional[Client] = None
        
        # Table names
        self.conversations_table = "conversations"
        self.messages_table = "messages"
        
        # Initialize Supabase client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client."""
        try:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY  # Use service role for server operations
            )
            
            self.logger.info("Chat history service initialized with Supabase")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return self._client is not None
    
    # =============================================================================
    # Conversation Management
    # =============================================================================
    
    def create_conversation(self, user_id: str, session_id: str, title: Optional[str] = None) -> str:
        """
        Create a new conversation.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            title: Conversation title (auto-generated if None)
            
        Returns:
            Conversation ID
        """
        if not self.is_configured():
            raise RuntimeError("Chat history service not configured")
        
        try:
            conversation_id = str(uuid.uuid4())
            
            # Auto-generate title if not provided
            if not title:
                title = f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            
            conversation_data = {
                "id": conversation_id,
                "user_id": user_id,
                "session_id": session_id,
                "title": title,
                "message_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": {}
            }
            
            result = self._client.table(self.conversations_table).insert(conversation_data).execute()
            
            if result.data:
                self.logger.info(f"Created conversation {conversation_id} for user {user_id}")
                return conversation_id
            else:
                raise Exception("Failed to create conversation")
                
        except Exception as e:
            self.logger.error(f"Failed to create conversation: {e}")
            raise
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation object or None
        """
        if not self.is_configured():
            return None
        
        try:
            result = self._client.table(self.conversations_table).select("*").eq("id", conversation_id).execute()
            
            if result.data:
                conv_data = result.data[0]
                return Conversation(
                    id=conv_data["id"],
                    user_id=conv_data["user_id"],
                    title=conv_data["title"],
                    session_id=conv_data["session_id"],
                    message_count=conv_data["message_count"],
                    last_message_at=datetime.fromisoformat(conv_data["last_message_at"]) if conv_data.get("last_message_at") else None,
                    created_at=datetime.fromisoformat(conv_data["created_at"]) if conv_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(conv_data["updated_at"]) if conv_data.get("updated_at") else None,
                    metadata=conv_data.get("metadata", {})
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None
    
    def list_user_conversations(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """
        List conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            
        Returns:
            List of conversations
        """
        if not self.is_configured():
            return []
        
        try:
            result = (
                self._client.table(self.conversations_table)
                .select("*")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            
            conversations = []
            for conv_data in result.data:
                conversations.append(Conversation(
                    id=conv_data["id"],
                    user_id=conv_data["user_id"],
                    title=conv_data["title"],
                    session_id=conv_data["session_id"],
                    message_count=conv_data["message_count"],
                    last_message_at=datetime.fromisoformat(conv_data["last_message_at"]) if conv_data.get("last_message_at") else None,
                    created_at=datetime.fromisoformat(conv_data["created_at"]) if conv_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(conv_data["updated_at"]) if conv_data.get("updated_at") else None,
                    metadata=conv_data.get("metadata", {})
                ))
            
            return conversations
            
        except Exception as e:
            self.logger.error(f"Failed to list conversations for user {user_id}: {e}")
            return []
    
    def update_conversation(self, conversation_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update conversation.
        
        Args:
            conversation_id: Conversation identifier
            updates: Updates to apply
            
        Returns:
            True if successful
        """
        if not self.is_configured():
            return False
        
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = (
                self._client.table(self.conversations_table)
                .update(updates)
                .eq("id", conversation_id)
                .execute()
            )
            
            return len(result.data) > 0
            
        except Exception as e:
            self.logger.error(f"Failed to update conversation {conversation_id}: {e}")
            return False
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Delete conversation and all its messages.
        
        Args:
            conversation_id: Conversation identifier
            user_id: User identifier (for security)
            
        Returns:
            True if successful
        """
        if not self.is_configured():
            return False
        
        try:
            # Delete messages first
            self._client.table(self.messages_table).delete().eq("conversation_id", conversation_id).execute()
            
            # Delete conversation
            result = (
                self._client.table(self.conversations_table)
                .delete()
                .eq("id", conversation_id)
                .eq("user_id", user_id)  # Security check
                .execute()
            )
            
            success = len(result.data) > 0
            if success:
                self.logger.info(f"Deleted conversation {conversation_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    # =============================================================================
    # Message Management
    # =============================================================================
    
    def store_message(
        self,
        conversation_id: str,
        user_id: str,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a chat message.
        
        Args:
            conversation_id: Conversation identifier
            user_id: User identifier
            session_id: Session identifier
            message_type: Type of message (user_voice, agent_response, etc.)
            content: Message content
            metadata: Additional message metadata
            
        Returns:
            Message ID
        """
        if not self.is_configured():
            raise RuntimeError("Chat history service not configured")
        
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            message_data = {
                "id": message_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "session_id": session_id,
                "message_type": message_type,
                "content": content,
                "metadata": metadata or {},
                "timestamp": timestamp.isoformat(),
                "created_at": timestamp.isoformat(),
                "updated_at": timestamp.isoformat()
            }
            
            # Insert message
            result = self._client.table(self.messages_table).insert(message_data).execute()
            
            if result.data:
                # Update conversation metadata
                self._update_conversation_on_message(conversation_id, timestamp)
                
                self.logger.debug(f"Stored message {message_id} in conversation {conversation_id}")
                return message_id
            else:
                raise Exception("Failed to store message")
                
        except Exception as e:
            self.logger.error(f"Failed to store message: {e}")
            raise
    
    def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
        message_type: Optional[str] = None
    ) -> List[ChatMessage]:
        """
        Get messages from a conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            message_type: Filter by message type
            
        Returns:
            List of chat messages
        """
        if not self.is_configured():
            return []
        
        try:
            query = (
                self._client.table(self.messages_table)
                .select("*")
                .eq("conversation_id", conversation_id)
                .order("timestamp", desc=False)
                .limit(limit)
                .offset(offset)
            )
            
            if message_type:
                query = query.eq("message_type", message_type)
            
            result = query.execute()
            
            messages = []
            for msg_data in result.data:
                messages.append(ChatMessage(
                    id=msg_data["id"],
                    conversation_id=msg_data["conversation_id"],
                    user_id=msg_data["user_id"],
                    session_id=msg_data["session_id"],
                    message_type=msg_data["message_type"],
                    content=msg_data["content"],
                    metadata=msg_data.get("metadata", {}),
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]) if msg_data.get("timestamp") else None,
                    created_at=datetime.fromisoformat(msg_data["created_at"]) if msg_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(msg_data["updated_at"]) if msg_data.get("updated_at") else None
                ))
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []
    
    def get_recent_messages(self, user_id: str, limit: int = 50) -> List[ChatMessage]:
        """
        Get recent messages for a user across all conversations.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of recent chat messages
        """
        if not self.is_configured():
            return []
        
        try:
            result = (
                self._client.table(self.messages_table)
                .select("*")
                .eq("user_id", user_id)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            
            messages = []
            for msg_data in result.data:
                messages.append(ChatMessage(
                    id=msg_data["id"],
                    conversation_id=msg_data["conversation_id"],
                    user_id=msg_data["user_id"],
                    session_id=msg_data["session_id"],
                    message_type=msg_data["message_type"],
                    content=msg_data["content"],
                    metadata=msg_data.get("metadata", {}),
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]) if msg_data.get("timestamp") else None,
                    created_at=datetime.fromisoformat(msg_data["created_at"]) if msg_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(msg_data["updated_at"]) if msg_data.get("updated_at") else None
                ))
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Failed to get recent messages for user {user_id}: {e}")
            return []
    
    def search_messages(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Search messages by content.
        
        Args:
            user_id: User identifier
            query: Search query
            conversation_id: Optional conversation filter
            message_type: Optional message type filter
            limit: Maximum number of results
            
        Returns:
            List of matching messages
        """
        if not self.is_configured():
            return []
        
        try:
            # Build search query
            search_query = (
                self._client.table(self.messages_table)
                .select("*")
                .eq("user_id", user_id)
                .ilike("content", f"%{query}%")
                .order("timestamp", desc=True)
                .limit(limit)
            )
            
            if conversation_id:
                search_query = search_query.eq("conversation_id", conversation_id)
            
            if message_type:
                search_query = search_query.eq("message_type", message_type)
            
            result = search_query.execute()
            
            messages = []
            for msg_data in result.data:
                messages.append(ChatMessage(
                    id=msg_data["id"],
                    conversation_id=msg_data["conversation_id"],
                    user_id=msg_data["user_id"],
                    session_id=msg_data["session_id"],
                    message_type=msg_data["message_type"],
                    content=msg_data["content"],
                    metadata=msg_data.get("metadata", {}),
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]) if msg_data.get("timestamp") else None,
                    created_at=datetime.fromisoformat(msg_data["created_at"]) if msg_data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(msg_data["updated_at"]) if msg_data.get("updated_at") else None
                ))
            
            return messages
            
        except Exception as e:
            self.logger.error(f"Failed to search messages: {e}")
            return []
    
    def update_message(self, message_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a message.
        
        Args:
            message_id: Message identifier
            updates: Updates to apply
            
        Returns:
            True if successful
        """
        if not self.is_configured():
            return False
        
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = (
                self._client.table(self.messages_table)
                .update(updates)
                .eq("id", message_id)
                .execute()
            )
            
            return len(result.data) > 0
            
        except Exception as e:
            self.logger.error(f"Failed to update message {message_id}: {e}")
            return False
    
    def delete_message(self, message_id: str, user_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: Message identifier
            user_id: User identifier (for security)
            
        Returns:
            True if successful
        """
        if not self.is_configured():
            return False
        
        try:
            result = (
                self._client.table(self.messages_table)
                .delete()
                .eq("id", message_id)
                .eq("user_id", user_id)  # Security check
                .execute()
            )
            
            success = len(result.data) > 0
            if success:
                self.logger.debug(f"Deleted message {message_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete message {message_id}: {e}")
            return False
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    def _update_conversation_on_message(self, conversation_id: str, message_timestamp: datetime):
        """
        Update conversation metadata when a message is added.
        
        Args:
            conversation_id: Conversation identifier
            message_timestamp: Timestamp of the new message
        """
        try:
            # Get current message count
            count_result = (
                self._client.table(self.messages_table)
                .select("id", count="exact")
                .eq("conversation_id", conversation_id)
                .execute()
            )
            
            message_count = count_result.count if hasattr(count_result, 'count') else 0
            
            # Update conversation
            self.update_conversation(conversation_id, {
                "message_count": message_count,
                "last_message_at": message_timestamp.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to update conversation metadata: {e}")
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Statistics dictionary
        """
        if not self.is_configured():
            return {}
        
        try:
            # Get conversation count
            conv_result = (
                self._client.table(self.conversations_table)
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            
            # Get message count
            msg_result = (
                self._client.table(self.messages_table)
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            
            # Get recent activity
            recent_messages = self.get_recent_messages(user_id, 1)
            last_activity = recent_messages[0].timestamp if recent_messages else None
            
            return {
                "conversation_count": conv_result.count if hasattr(conv_result, 'count') else 0,
                "message_count": msg_result.count if hasattr(msg_result, 'count') else 0,
                "last_activity": last_activity.isoformat() if last_activity else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation stats: {e}")
            return {}
    
    # =============================================================================
    # Conversation Auto-Management
    # =============================================================================
    
    def auto_create_conversation_if_needed(self, user_id: str, session_id: str) -> str:
        """
        Auto-create conversation if none exists for the session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Conversation ID (existing or newly created)
        """
        try:
            # Check if conversation exists for this session
            result = (
                self._client.table(self.conversations_table)
                .select("id")
                .eq("user_id", user_id)
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data:
                return result.data[0]["id"]
            
            # Create new conversation
            return self.create_conversation(user_id, session_id)
            
        except Exception as e:
            self.logger.error(f"Failed to auto-create conversation: {e}")
            # Return a fallback conversation ID
            return f"fallback_{user_id}_{session_id}"
    
    def update_conversation_title_from_content(self, conversation_id: str, first_message: str) -> bool:
        """
        Update conversation title based on first message content.
        
        Args:
            conversation_id: Conversation identifier
            first_message: First message content
            
        Returns:
            True if successful
        """
        try:
            # Generate title from first message (truncate and clean)
            title = first_message.strip()
            if len(title) > 60:
                title = title[:57] + "..."
            
            # Remove newlines and extra spaces
            title = " ".join(title.split())
            
            # Ensure title is not empty
            if not title:
                title = f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            
            return self.update_conversation(conversation_id, {"title": title})
            
        except Exception as e:
            self.logger.error(f"Failed to update conversation title: {e}")
            return False
    
    # =============================================================================
    # Database Schema Management
    # =============================================================================
    
    def ensure_tables_exist(self) -> bool:
        """
        Ensure required tables exist in Supabase.
        
        Note: This would typically be handled by Supabase migrations,
        but included here for development convenience.
        
        Returns:
            True if tables exist or were created
        """
        if not self.is_configured():
            return False
        
        try:
            # This is a simplified check - in production, use proper migrations
            # Check if tables exist by trying to query them
            
            # Test conversations table
            self._client.table(self.conversations_table).select("id").limit(1).execute()
            
            # Test messages table
            self._client.table(self.messages_table).select("id").limit(1).execute()
            
            self.logger.info("Chat history tables verified")
            return True
            
        except Exception as e:
            self.logger.warning(f"Chat history tables may not exist: {e}")
            return False
    
    # =============================================================================
    # Health Check and Monitoring
    # =============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on chat history service.
        
        Returns:
            Health check results
        """
        health = {
            "service": "chat_history",
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Configuration check
            health["checks"]["configured"] = self.is_configured()
            
            if self.is_configured():
                # Database connection check
                try:
                    # Test table access
                    self._client.table(self.conversations_table).select("id").limit(1).execute()
                    health["checks"]["database_connection"] = True
                    
                    # Test table existence
                    tables_exist = self.ensure_tables_exist()
                    health["checks"]["tables_exist"] = tables_exist
                    
                    # Performance test
                    start_time = datetime.utcnow()
                    test_user_id = "health_check_user"
                    
                    # Create test conversation
                    conv_id = self.create_conversation(test_user_id, "health_check_session", "Health Check")
                    
                    # Store test message
                    msg_id = self.store_message(
                        conv_id, test_user_id, "health_check_session",
                        "system", "Health check message"
                    )
                    
                    # Retrieve test data
                    conversation = self.get_conversation(conv_id)
                    messages = self.get_messages(conv_id, limit=1)
                    
                    # Clean up test data
                    self.delete_conversation(conv_id, test_user_id)
                    
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds() * 1000  # ms
                    
                    health["checks"]["crud_operations"] = (
                        conversation is not None and 
                        len(messages) > 0 and
                        messages[0].id == msg_id
                    )
                    health["checks"]["response_time_ms"] = response_time
                    
                except Exception as e:
                    health["checks"]["database_operations"] = False
                    health["checks"]["error"] = str(e)
            
            # Overall status
            all_checks_passed = all(
                check for check in health["checks"].values() 
                if isinstance(check, bool)
            )
            
            health["status"] = "healthy" if all_checks_passed else "degraded"
            health["supabase_url"] = settings.SUPABASE_URL
            
        except Exception as e:
            health["checks"]["error"] = str(e)
            health["status"] = "unhealthy"
        
        return health


# =============================================================================
# Singleton instance and utility functions
# =============================================================================

# Global chat history instance
_chat_history_instance = None


def get_chat_history() -> ChatHistoryService:
    """Get singleton chat history instance."""
    global _chat_history_instance
    if _chat_history_instance is None:
        _chat_history_instance = ChatHistoryService()
    return _chat_history_instance


# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_chat_history():
    """Test chat history functionality."""
    chat_history = get_chat_history()
    
    print("Testing Chat History Service...")
    
    # Health check
    health = await chat_history.health_check()
    print(f"Health Check: {health['status']}")
    
    if health["status"] != "healthy":
        print("Chat history is not healthy, skipping tests")
        return False
    
    # Test conversation and message lifecycle
    test_user_id = "test_user_123"
    test_session_id = "test_session_456"
    
    # Create conversation
    conv_id = chat_history.create_conversation(test_user_id, test_session_id, "Test Conversation")
    print(f"Created conversation: {conv_id}")
    
    # Store messages
    msg1_id = chat_history.store_message(
        conv_id, test_user_id, test_session_id,
        "user_voice", "Hello, can you help me with my emails?",
        {"duration": 2.5}
    )
    print(f"Stored user message: {msg1_id}")
    
    msg2_id = chat_history.store_message(
        conv_id, test_user_id, test_session_id,
        "agent_response", "Of course! I can help you manage your emails. What would you like to do?",
        {"processing_time": 1.2}
    )
    print(f"Stored agent message: {msg2_id}")
    
    # Retrieve conversation and messages
    conversation = chat_history.get_conversation(conv_id)
    print(f"Retrieved conversation: {conversation.title if conversation else 'None'}")
    
    messages = chat_history.get_messages(conv_id)
    print(f"Retrieved {len(messages)} messages")
    
    # Test search
    search_results = chat_history.search_messages(test_user_id, "emails")
    print(f"Search results: {len(search_results)} messages")
    
    # Test user conversations list
    user_conversations = chat_history.list_user_conversations(test_user_id)
    print(f"User conversations: {len(user_conversations)}")
    
    # Get stats
    stats = chat_history.get_conversation_stats(test_user_id)
    print(f"User stats: {stats}")
    
    # Clean up
    chat_history.delete_conversation(conv_id, test_user_id)
    print("Cleaned up test data")
    
    print("✅ Chat history tests completed")
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chat_history())