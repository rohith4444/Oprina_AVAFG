"""
Memory Manager for Oprina

This module provides a unified interface to all memory services:
- Redis cache for performance
- Session memory for agent coordination 
- Chat history for permanent conversation storage
- Long-term memory for learning and patterns

Acts as a facade pattern to simplify memory operations for agents.
"""

import uuid
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .redis_cache import RedisCacheService, get_redis_cache
from .session_memory import SessionMemoryService, get_session_memory
from .chat_history import ChatHistoryService, get_chat_history, ChatMessage, Conversation
from .long_term_memory import LongTermMemoryService, get_long_term_memory


class MemoryManager:
    """
    Unified memory manager providing a single interface to all memory services.
    
    Architecture:
    - Redis Cache: Fast temporary storage and email caching
    - Session Memory: ADK DatabaseSessionService with Supabase for agent coordination
    - Chat History: Direct Supabase for permanent conversation storage
    - Long-term Memory: ADK MemoryService for learning patterns
    """
    
    def __init__(self):
        """Initialize memory manager with all memory services."""
        self.logger = logging.getLogger("memory_manager")
        
        # Initialize individual memory services
        self.redis_cache = get_redis_cache()
        self.session_memory = get_session_memory()
        self.chat_history = get_chat_history()
        self.long_term_memory = get_long_term_memory()
        
        # Memory manager configuration
        self.auto_learning_enabled = True
        self.conversation_auto_create = True
        
        self.logger.info("Memory manager initialized with all services")
    
    # =============================================================================
    # Unified Session Management
    # =============================================================================
    
    async def create_oprina_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Create a new Oprina session with all memory services configured.
        
        Args:
            user_id: User identifier
            session_id: Optional session ID
            
        Returns:
            Session ID
        """
        try:
            # Create session in session memory service
            session_id = self.session_memory.create_session(user_id, session_id)
            
            # Initialize Redis cache for the session
            self.redis_cache.cache_session_data(session_id, {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            })
            
            # Learn session creation pattern
            if self.auto_learning_enabled:
                self.long_term_memory.learn_from_event(user_id, "session_created", {
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            self.logger.info(f"Created Oprina session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create Oprina session: {e}")
            raise
    
    def get_session_context(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive session context from all memory services.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Complete session context
        """
        try:
            # Get session state
            session = self.session_memory.get_session(user_id, session_id)
            if not session:
                return None
            
            # Get cached session data
            cached_data = self.redis_cache.get_session_cache(session_id)
            
            # Get user patterns for adaptive behavior
            user_patterns = self.long_term_memory.get_user_patterns(user_id)
            
            # Get recent conversation context
            conversations = self.chat_history.list_user_conversations(user_id, limit=5)
            recent_messages = self.chat_history.get_recent_messages(user_id, limit=10)
            
            # Combine all context
            context = {
                "session_state": session.state,
                "cached_data": cached_data,
                "user_patterns": user_patterns,
                "recent_conversations": [
                    {
                        "id": conv.id,
                        "title": conv.title,
                        "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                        "message_count": conv.message_count
                    } for conv in conversations
                ],
                "recent_messages": [
                    {
                        "type": msg.message_type,
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                    } for msg in recent_messages
                ]
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get session context: {e}")
            return None
    
    def update_session_context(self, user_id: str, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session context across relevant memory services.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            updates: Context updates
            
        Returns:
            True if successful
        """
        try:
            success = True
            
            # Update session memory if session-related updates
            if any(key.startswith(('agent_', 'email_', 'user_', 'session_')) for key in updates.keys()):
                session_success = self.session_memory.update_session_state(user_id, session_id, updates)
                success &= session_success
            
            # Update cache for performance-critical data
            cache_updates = {k: v for k, v in updates.items() if k in ['current_email_context', 'agent_states']}
            if cache_updates:
                cache_success = self.redis_cache.cache_session_data(session_id, cache_updates)
                success &= cache_success
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update session context: {e}")
            return False
    
    # =============================================================================
    # Conversation and Message Management
    # =============================================================================
    
    async def store_conversation_message(
        self,
        user_id: str,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        learn_from_message: bool = True
    ) -> str:
        """
        Store a conversation message across all relevant memory services.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            message_type: Type of message (user_voice, agent_response, etc.)
            content: Message content
            metadata: Additional metadata
            learn_from_message: Whether to learn from this message
            
        Returns:
            Message ID
        """
        try:
            # Auto-create conversation if needed
            conversation_id = None
            if self.conversation_auto_create:
                conversation_id = self.chat_history.auto_create_conversation_if_needed(user_id, session_id)
            
            if not conversation_id:
                # Create new conversation
                conversation_id = self.chat_history.create_conversation(user_id, session_id)
            
            # Store message in chat history
            message_id = self.chat_history.store_message(
                conversation_id, user_id, session_id, message_type, content, metadata
            )
            
            # Update session conversation history
            self.session_memory.add_conversation_entry(user_id, session_id, {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "type": message_type,
                "content_preview": content[:50] + "..." if len(content) > 50 else content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Learn from message if enabled
            if learn_from_message and self.auto_learning_enabled:
                await self._learn_from_message(user_id, message_type, content, metadata)
            
            # Update conversation title if it's the first user message
            if message_type.startswith("user") and content:
                conversation = self.chat_history.get_conversation(conversation_id)
                if conversation and conversation.message_count <= 1:
                    self.chat_history.update_conversation_title_from_content(conversation_id, content)
            
            self.logger.debug(f"Stored message {message_id} in conversation {conversation_id}")
            return message_id
            
        except Exception as e:
            self.logger.error(f"Failed to store conversation message: {e}")
            raise
    
    def get_conversation_context(self, conversation_id: str, message_limit: int = 20) -> Dict[str, Any]:
        """
        Get comprehensive conversation context.
        
        Args:
            conversation_id: Conversation identifier
            message_limit: Maximum messages to retrieve
            
        Returns:
            Conversation context
        """
        try:
            # Get conversation details
            conversation = self.chat_history.get_conversation(conversation_id)
            if not conversation:
                return {}
            
            # Get messages
            messages = self.chat_history.get_messages(conversation_id, limit=message_limit)
            
            # Get user patterns for context
            user_patterns = self.long_term_memory.get_user_patterns(conversation.user_id)
            
            # Build context
            context = {
                "conversation": {
                    "id": conversation.id,
                    "title": conversation.title,
                    "user_id": conversation.user_id,
                    "session_id": conversation.session_id,
                    "message_count": conversation.message_count,
                    "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                    "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None
                },
                "messages": [
                    {
                        "id": msg.id,
                        "type": msg.message_type,
                        "content": msg.content,
                        "metadata": msg.metadata,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                    } for msg in messages
                ],
                "user_patterns": user_patterns,
                "context_summary": self._generate_context_summary(messages, user_patterns)
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation context: {e}")
            return {}
    
    def search_conversations_and_messages(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, List]:
        """
        Search across conversations and messages.
        
        Args:
            user_id: User identifier
            query: Search query
            conversation_id: Optional conversation filter
            limit: Maximum results
            
        Returns:
            Search results
        """
        try:
            # Search messages
            messages = self.chat_history.search_messages(user_id, query, conversation_id, limit=limit)
            
            # Search conversations by title (simple implementation)
            conversations = self.chat_history.list_user_conversations(user_id, limit=50)
            matching_conversations = [
                conv for conv in conversations 
                if query.lower() in conv.title.lower()
            ]
            
            return {
                "messages": [
                    {
                        "id": msg.id,
                        "conversation_id": msg.conversation_id,
                        "type": msg.message_type,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                    } for msg in messages
                ],
                "conversations": [
                    {
                        "id": conv.id,
                        "title": conv.title,
                        "message_count": conv.message_count,
                        "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None
                    } for conv in matching_conversations
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to search conversations and messages: {e}")
            return {"messages": [], "conversations": []}
    
    # =============================================================================
    # Email Context Management
    # =============================================================================
    
    def cache_user_emails(self, user_id: str, emails: List[Dict], ttl_seconds: Optional[int] = None) -> bool:
        """
        Cache user emails with metadata tracking.
        
        Args:
            user_id: User identifier
            emails: Email data
            ttl_seconds: Cache TTL
            
        Returns:
            True if successful
        """
        try:
            # Cache emails in Redis
            cache_success = self.redis_cache.cache_emails(user_id, emails, ttl_seconds)
            
            # Update email metadata
            metadata = {
                "email_count": len(emails),
                "last_sync": datetime.utcnow().isoformat(),
                "unread_count": sum(1 for email in emails if not email.get("read", False)),
                "important_count": sum(1 for email in emails if email.get("important", False))
            }
            
            metadata_success = self.redis_cache.cache_email_metadata(user_id, metadata, ttl_seconds)
            
            # Learn from email patterns
            if self.auto_learning_enabled and emails:
                self.long_term_memory.learn_from_event(user_id, "email_check", {
                    "email_count": len(emails),
                    "unread_count": metadata["unread_count"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return cache_success and metadata_success
            
        except Exception as e:
            self.logger.error(f"Failed to cache user emails: {e}")
            return False
    
    def get_user_emails_with_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Get user emails with full context.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Emails with context
        """
        try:
            # Get cached emails
            emails = self.redis_cache.get_cached_emails(user_id)
            metadata = self.redis_cache.get_email_metadata(user_id)
            
            # Get email context from session
            email_context = self.session_memory.get_email_context(user_id, session_id)
            
            # Get adaptive settings based on learned patterns
            adaptive_settings = self.long_term_memory.get_adaptive_response_settings(user_id, {
                "email_count": len(emails) if emails else 0
            })
            
            return {
                "emails": emails or [],
                "metadata": metadata or {},
                "session_context": email_context or {},
                "adaptive_settings": adaptive_settings,
                "cache_status": {
                    "emails_cached": emails is not None,
                    "metadata_cached": metadata is not None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user emails with context: {e}")
            return {
                "emails": [],
                "metadata": {},
                "session_context": {},
                "adaptive_settings": {},
                "cache_status": {"emails_cached": False, "metadata_cached": False}
            }
    
    def update_email_context_across_services(
        self,
        user_id: str,
        session_id: str,
        email_context: Dict[str, Any]
    ) -> bool:
        """
        Update email context across session memory and cache.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            email_context: Email context updates
            
        Returns:
            True if successful
        """
        try:
            # Update in session memory
            session_success = self.session_memory.update_email_context(user_id, session_id, email_context)
            
            # Update in cache for quick access
            cache_key = f"{user_id}:email_context"
            cache_success = self.redis_cache.set(cache_key, email_context, prefix="temp")
            
            return session_success and cache_success
            
        except Exception as e:
            self.logger.error(f"Failed to update email context: {e}")
            return False
    
    # =============================================================================
    # Agent Coordination
    # =============================================================================
    
    def set_agent_coordination_data(
        self,
        session_id: str,
        agent_name: str,
        data: Dict[str, Any],
        persistent: bool = False
    ) -> bool:
        """
        Set agent coordination data with optional persistence.
        
        Args:
            session_id: Session identifier
            agent_name: Agent name
            data: Coordination data
            persistent: Whether to store in session memory (persistent) or cache (temporary)
            
        Returns:
            True if successful
        """
        try:
            if persistent:
                # Store in session memory for persistence
                session = self.session_memory.get_session("system", session_id)  # Use system user for coordination
                if session:
                    user_id = session.state.get("user_id", "system")
                    return self.session_memory.update_agent_state(user_id, session_id, agent_name, data)
            else:
                # Store in Redis cache for quick access
                return self.redis_cache.set_agent_context(session_id, agent_name, data)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to set agent coordination data: {e}")
            return False
    
    def get_agent_coordination_data(self, session_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get agent coordination data from cache and session.
        
        Args:
            session_id: Session identifier
            agent_name: Agent name
            
        Returns:
            Coordination data or None
        """
        try:
            # Try cache first (faster)
            cached_data = self.redis_cache.get_agent_context(session_id, agent_name)
            if cached_data:
                return cached_data
            
            # Fall back to session memory
            session = self.session_memory.get_session("system", session_id)
            if session:
                user_id = session.state.get("user_id", "system")
                return self.session_memory.get_agent_state(user_id, session_id, agent_name)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get agent coordination data: {e}")
            return None
    
    def clear_agent_coordination(self, session_id: str, agent_name: Optional[str] = None) -> bool:
        """
        Clear agent coordination data.
        
        Args:
            session_id: Session identifier
            agent_name: Specific agent (clears all if None)
            
        Returns:
            True if successful
        """
        try:
            # Clear from cache
            cache_success = self.redis_cache.clear_agent_context(session_id, agent_name)
            
            # Clear from session memory would require getting the session first
            # For now, just clear cache as that's where most coordination data is stored
            
            return cache_success
            
        except Exception as e:
            self.logger.error(f"Failed to clear agent coordination: {e}")
            return False
    
    # =============================================================================
    # Smart Suggestions and Adaptive Behavior
    # =============================================================================
    
    def get_smart_suggestions_for_context(
        self,
        user_id: str,
        session_id: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get smart suggestions based on current context and learned patterns.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            context: Current context (email count, time, etc.)
            
        Returns:
            List of smart suggestions
        """
        try:
            # Get base suggestions from long-term memory
            base_suggestions = self.long_term_memory.get_smart_suggestions(user_id, context)
            
            # Enhance with session context
            session_context = self.get_session_context(user_id, session_id)
            if session_context:
                # Add session-specific suggestions
                email_context = session_context.get("session_state", {}).get("current_email_context", {})
                
                if email_context.get("pending_actions"):
                    base_suggestions.append({
                        "type": "pending_action",
                        "message": f"You have {len(email_context['pending_actions'])} pending email actions",
                        "confidence": 0.9,
                        "action": "show_pending_actions"
                    })
                
                unread_count = email_context.get("unread_count", 0)
                if unread_count > 0:
                    base_suggestions.append({
                        "type": "unread_emails",
                        "message": f"You have {unread_count} unread emails",
                        "confidence": 0.8,
                        "action": "check_unread_emails"
                    })
            
            # Sort by confidence and return top suggestions
            all_suggestions = sorted(base_suggestions, key=lambda x: x["confidence"], reverse=True)
            return all_suggestions[:5]
            
        except Exception as e:
            self.logger.error(f"Failed to get smart suggestions: {e}")
            return []
    
    def get_adaptive_agent_settings(self, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get adaptive settings for agents based on learned patterns.
        
        Args:
            user_id: User identifier
            context: Current context
            
        Returns:
            Adaptive settings for agents
        """
        try:
            return self.long_term_memory.get_adaptive_response_settings(user_id, context)
            
        except Exception as e:
            self.logger.error(f"Failed to get adaptive agent settings: {e}")
            return {}
    
    # =============================================================================
    # Learning and Pattern Recognition
    # =============================================================================
    
    async def _learn_from_message(
        self,
        user_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Learn from conversation messages."""
        try:
            if message_type == "user_voice":
                # Learn voice patterns
                self.long_term_memory.learn_from_event(user_id, "voice_command", {
                    "command": content,
                    "duration": metadata.get("duration", 0) if metadata else 0
                })
            
            elif message_type == "agent_response":
                # Learn response style preferences
                self.long_term_memory.learn_from_event(user_id, "response_generated", {
                    "style": metadata.get("style", "brief") if metadata else "brief",
                    "length": len(content),
                    "tone": metadata.get("tone", "friendly") if metadata else "friendly"
                })
            
            elif message_type.startswith("summary"):
                # Learn summary preferences
                self.long_term_memory.learn_from_event(user_id, "summary_requested", {
                    "detail_level": metadata.get("detail_level", "moderate") if metadata else "moderate",
                    "email_count": metadata.get("email_count", 0) if metadata else 0
                })
            
        except Exception as e:
            self.logger.error(f"Failed to learn from message: {e}")
    
    def learn_from_user_action(
        self,
        user_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Learn from user actions.
        
        Args:
            user_id: User identifier
            action_type: Type of action (email_action, preference_change, etc.)
            action_data: Action data
            context: Additional context
            
        Returns:
            True if learning was successful
        """
        try:
            if not self.auto_learning_enabled:
                return True
            
            return self.long_term_memory.learn_from_event(user_id, action_type, action_data, context)
            
        except Exception as e:
            self.logger.error(f"Failed to learn from user action: {e}")
            return False
    
    def get_user_behavior_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user behavior insights.
        
        Args:
            user_id: User identifier
            
        Returns:
            Behavior insights and analytics
        """
        try:
            # Get insights from long-term memory
            behavior_analysis = self.long_term_memory.analyze_user_behavior(user_id)
            learning_stats = self.long_term_memory.get_learning_stats(user_id)
            
            # Get conversation stats
            conversation_stats = self.chat_history.get_conversation_stats(user_id)
            
            # Get recent activity from cache
            cached_data = self.redis_cache.get_user_preferences(user_id)
            
            # Combine all insights
            insights = {
                "user_id": user_id,
                "behavior_analysis": behavior_analysis,
                "learning_stats": learning_stats,
                "conversation_stats": conversation_stats,
                "cached_preferences": cached_data,
                "recommendations": self._generate_behavior_recommendations(behavior_analysis, learning_stats)
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to get user behavior insights: {e}")
            return {}
    
    def _generate_behavior_recommendations(
        self,
        behavior_analysis: Dict[str, Any],
        learning_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on behavior analysis."""
        recommendations = []
        
        try:
            # Check learning quality
            avg_quality = sum(learning_stats.get("learning_quality", {}).values()) / max(len(learning_stats.get("learning_quality", {})), 1)
            
            if avg_quality < 0.3:
                recommendations.append("Continue using Oprina to improve AI personalization")
            
            # Check pattern diversity
            pattern_count = learning_stats.get("total_patterns", 0)
            if pattern_count < 3:
                recommendations.append("Try using more Oprina features for better suggestions")
            
            # Check email frequency patterns
            insights = behavior_analysis.get("insights", [])
            has_email_pattern = any(insight.get("type") == "email_frequency" for insight in insights)
            
            if not has_email_pattern:
                recommendations.append("Use Oprina regularly to learn your email checking patterns")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate behavior recommendations: {e}")
            return []
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def _generate_context_summary(
        self,
        messages: List[ChatMessage],
        user_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a summary of conversation context."""
        try:
            if not messages:
                return {"summary": "No messages in conversation"}
            
            # Basic message analysis
            user_messages = [msg for msg in messages if msg.message_type.startswith("user")]
            agent_messages = [msg for msg in messages if msg.message_type.startswith("agent")]
            
            # Extract common topics/themes (simple keyword analysis)
            all_content = " ".join([msg.content for msg in messages])
            email_keywords = ["email", "inbox", "message", "send", "reply", "draft"]
            email_mentions = sum(all_content.lower().count(keyword) for keyword in email_keywords)
            
            summary = {
                "message_count": len(messages),
                "user_message_count": len(user_messages),
                "agent_message_count": len(agent_messages),
                "email_related": email_mentions > 0,
                "last_message_type": messages[-1].message_type if messages else None,
                "conversation_length": len(all_content),
                "primary_topic": "email_management" if email_mentions > 2 else "general"
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate context summary: {e}")
            return {"summary": "Error generating summary"}
    
    def reset_user_memory(
        self,
        user_id: str,
        components: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Reset user memory across specified components.
        
        Args:
            user_id: User identifier
            components: Memory components to reset (None for all)
            session_id: Optional session to reset
            
        Returns:
            Reset results by component
        """
        if components is None:
            components = ["cache", "patterns", "conversations", "sessions"]
        
        results = {}
        
        try:
            # Reset cache
            if "cache" in components:
                # Clear user-specific cache data
                cache_cleared = self.redis_cache.clear_cache("user")
                results["cache"] = cache_cleared
            
            # Reset learned patterns
            if "patterns" in components:
                patterns_reset = self.long_term_memory.reset_user_patterns(user_id)
                results["patterns"] = patterns_reset
            
            # Reset conversations (careful - this is permanent!)
            if "conversations" in components:
                conversations = self.chat_history.list_user_conversations(user_id)
                conversations_deleted = 0
                for conv in conversations:
                    if self.chat_history.delete_conversation(conv.id, user_id):
                        conversations_deleted += 1
                results["conversations"] = conversations_deleted == len(conversations)
            
            # Reset sessions
            if "sessions" in components and session_id:
                session_deleted = self.session_memory.delete_session(user_id, session_id)
                results["sessions"] = session_deleted
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to reset user memory: {e}")
            return {component: False for component in components}
    
    # =============================================================================
    # Health Check and Monitoring
    # =============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check of all memory services.
        
        Returns:
            Health check results for all services
        """
        health = {
            "service": "memory_manager",
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        try:
            # Check all individual services
            redis_health = await self.redis_cache.health_check()
            session_health = await self.session_memory.health_check()
            chat_health = await self.chat_history.health_check()
            ltm_health = await self.long_term_memory.health_check()
            
            health["services"] = {
                "redis_cache": redis_health,
                "session_memory": session_health,
                "chat_history": chat_health,
                "long_term_memory": ltm_health
            }
            
            # Overall status based on critical services
            critical_services = ["redis_cache", "session_memory", "chat_history"]
            critical_healthy = all(
                health["services"][service]["status"] == "healthy" 
                for service in critical_services
            )
            
            # Long-term memory is not critical for basic operation
            if critical_healthy:
                health["status"] = "healthy"
            else:
                health["status"] = "degraded"
            
            # Add summary
            healthy_count = sum(
                1 for service_health in health["services"].values() 
                if service_health["status"] == "healthy"
            )
            health["summary"] = f"{healthy_count}/4 services healthy"
            
        except Exception as e:
            health["error"] = str(e)
            health["status"] = "unhealthy"
        
        return health
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive memory usage and performance statistics.
        
        Returns:
            Memory statistics across all services
        """
        try:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "redis_stats": self.redis_cache.get_cache_stats(),
                "configuration": {
                    "auto_learning_enabled": self.auto_learning_enabled,
                    "conversation_auto_create": self.conversation_auto_create
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get memory statistics: {e}")
            return {"error": str(e)}


# =============================================================================
# Context Managers and Utilities
# =============================================================================

@asynccontextmanager
async def memory_context(user_id: str, session_id: Optional[str] = None):
    """Context manager for memory operations."""
    memory_manager = MemoryManager()
    
    # Create session if needed
    if session_id is None:
        session_id = await memory_manager.create_oprina_session(user_id)
    
    try:
        yield memory_manager, session_id
    finally:
        # Cleanup if needed
        pass


# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_memory_manager():
    """Test memory manager functionality."""
    memory_manager = MemoryManager()
    
    print("Testing Memory Manager...")
    
    # Health check
    health = await memory_manager.health_check()
    print(f"Overall Health: {health['status']}")
    print(f"Services: {health.get('summary', 'N/A')}")
    
    if health["status"] not in ["healthy", "degraded"]:
        print("Memory manager is not healthy enough for testing")
        return False
    
    # Test session creation
    test_user_id = "test_user_123"
    session_id = await memory_manager.create_oprina_session(test_user_id)
    print(f"Created session: {session_id}")
    
    # Test message storage
    message_id = await memory_manager.store_conversation_message(
        test_user_id, session_id, "user_voice", 
        "Can you help me check my emails?",
        {"duration": 2.5}
    )
    print(f"Stored message: {message_id}")
    
    # Test email caching
    test_emails = [
        {"id": "1", "subject": "Test Email 1", "read": False},
        {"id": "2", "subject": "Test Email 2", "read": True}
    ]
    email_cached = memory_manager.cache_user_emails(test_user_id, test_emails)
    print(f"Cached emails: {email_cached}")
    
    # Test smart suggestions
    suggestions = memory_manager.get_smart_suggestions_for_context(
        test_user_id, session_id, {"email_count": 2}
    )
    print(f"Smart suggestions: {len(suggestions)}")
    
    # Test behavior insights
    insights = memory_manager.get_user_behavior_insights(test_user_id)
    print(f"Behavior insights: {insights.get('learning_stats', {}).get('total_patterns', 0)} patterns learned")
    
    # Get statistics
    stats = memory_manager.get_memory_statistics()
    print(f"Memory statistics: {stats.get('redis_stats', {}).get('connected', 'Unknown')}")
    
    print("✅ Memory manager tests completed")
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_memory_manager())