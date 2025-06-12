"""
Session database entity model for Oprina API.

This module defines the SQLAlchemy Session model that corresponds to the 'sessions' table
in the database schema. It handles chat sessions between users and the AI agent.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class Session(Base):
    """
    Session entity representing a chat session between a user and the AI agent.
    
    This model handles session metadata, configuration, statistics,
    and lifecycle management.
    """
    
    __tablename__ = "sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Session identification
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    session_name = Column(String(255), nullable=True)
    
    # Session metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    context_data = Column(JSONB, default=dict, nullable=False)
    
    # Agent configuration
    agent_type = Column(String(100), default='default', nullable=False)
    agent_config = Column(JSONB, default=dict, nullable=False)
    
    # Session statistics
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens_used = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Numeric(10, 4), default=Decimal('0.0000'), nullable=False)
    
    # Session lifecycle
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Session status
    status = Column(String(50), default='active', nullable=False, index=True)  # active, paused, ended, archived
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.message_index")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, status={self.status}, messages={self.message_count})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for API responses."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'session_token': self.session_token,
            'session_name': self.session_name,
            'title': self.title,
            'description': self.description,
            'context_data': self.context_data,
            'agent_type': self.agent_type,
            'agent_config': self.agent_config,
            'message_count': self.message_count,
            'total_tokens_used': self.total_tokens_used,
            'estimated_cost': float(self.estimated_cost),
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'last_activity_at': self.last_activity_at.isoformat(),
            'status': self.status,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert session to summary dictionary for listing APIs."""
        return {
            'id': str(self.id),
            'session_name': self.session_name,
            'title': self.title or self.session_name or f"Session {str(self.id)[:8]}",
            'message_count': self.message_count,
            'total_tokens_used': self.total_tokens_used,
            'estimated_cost': float(self.estimated_cost),
            'status': self.status,
            'is_archived': self.is_archived,
            'last_activity_at': self.last_activity_at.isoformat(),
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def display_title(self) -> str:
        """Get a display-friendly title for the session."""
        if self.title:
            return self.title
        elif self.session_name:
            return self.session_name
        else:
            return f"Session {str(self.id)[:8]}"
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == 'active'
    
    @property
    def is_ended(self) -> bool:
        """Check if session has ended."""
        return self.status == 'ended' or self.ended_at is not None
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate session duration in minutes."""
        if self.ended_at:
            delta = self.ended_at - self.started_at
        else:
            delta = datetime.utcnow() - self.started_at
        
        return delta.total_seconds() / 60.0
    
    @property
    def has_messages(self) -> bool:
        """Check if session has any messages."""
        return self.message_count > 0
    
    def update_context(self, new_context: Dict[str, Any]) -> None:
        """Update session context data, merging with existing context."""
        if self.context_data is None:
            self.context_data = {}
        
        # Merge context data
        current_context = dict(self.context_data)
        current_context.update(new_context)
        self.context_data = current_context
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a specific context value."""
        if self.context_data is None:
            return default
        return self.context_data.get(key, default)
    
    def set_context(self, key: str, value: Any) -> None:
        """Set a specific context value."""
        if self.context_data is None:
            self.context_data = {}
        
        context = dict(self.context_data)
        context[key] = value
        self.context_data = context
    
    def update_agent_config(self, new_config: Dict[str, Any]) -> None:
        """Update agent configuration, merging with existing config."""
        if self.agent_config is None:
            self.agent_config = {}
        
        # Merge agent config
        current_config = dict(self.agent_config)
        current_config.update(new_config)
        self.agent_config = current_config
    
    def get_agent_config(self, key: str, default: Any = None) -> Any:
        """Get a specific agent configuration value."""
        if self.agent_config is None:
            return default
        return self.agent_config.get(key, default)
    
    def set_agent_config(self, key: str, value: Any) -> None:
        """Set a specific agent configuration value."""
        if self.agent_config is None:
            self.agent_config = {}
        
        config = dict(self.agent_config)
        config[key] = value
        self.agent_config = config
    
    def mark_activity(self) -> None:
        """Mark session as having recent activity."""
        self.last_activity_at = datetime.utcnow()
    
    def start(self) -> None:
        """Start the session."""
        self.status = 'active'
        self.started_at = datetime.utcnow()
        self.mark_activity()
    
    def pause(self) -> None:
        """Pause the session."""
        self.status = 'paused'
        self.mark_activity()
    
    def resume(self) -> None:
        """Resume a paused session."""
        self.status = 'active'
        self.mark_activity()
    
    def end(self) -> None:
        """End the session."""
        self.status = 'ended'
        self.ended_at = datetime.utcnow()
        self.mark_activity()
    
    def archive(self) -> None:
        """Archive the session."""
        self.is_archived = True
        if self.status == 'active':
            self.end()
    
    def unarchive(self) -> None:
        """Unarchive the session."""
        self.is_archived = False
    
    def set_title(self, title: str) -> None:
        """Set session title."""
        self.title = title[:500]  # Ensure max length
    
    def set_description(self, description: str) -> None:
        """Set session description."""
        self.description = description
    
    def add_tokens(self, tokens: int, cost: Decimal = Decimal('0.0000')) -> None:
        """Add token usage to session statistics."""
        self.total_tokens_used += tokens
        self.estimated_cost += cost
        self.mark_activity()
    
    def increment_message_count(self) -> None:
        """Increment the message count for this session."""
        self.message_count += 1
        self.mark_activity()
    
    @classmethod
    def create_session(
        cls,
        user_id: str,
        session_token: str,
        session_name: Optional[str] = None,
        agent_type: str = 'default',
        **kwargs
    ) -> "Session":
        """
        Create a new session instance.
        
        Args:
            user_id: User identifier
            session_token: Unique session token
            session_name: Optional session name
            agent_type: Type of agent to use
            **kwargs: Additional session attributes
            
        Returns:
            New Session instance
        """
        return cls(
            user_id=user_id,
            session_token=session_token,
            session_name=session_name,
            agent_type=agent_type,
            **kwargs
        )
    
    def get_recent_messages(self, limit: int = 10) -> List["Message"]:
        """Get recent messages from this session."""
        # This would be implemented by the repository layer
        # Here we just return an empty list as placeholder
        return []
    
    def get_message_history(self, include_system: bool = False) -> List[Dict[str, Any]]:
        """Get formatted message history for agent context."""
        # This would be implemented by the repository layer
        # Return format suitable for AI agent
        return []


class UserToken(Base):
    """
    User token entity for authentication and password reset tokens.
    """
    
    __tablename__ = "user_tokens"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Token details
    token_type = Column(String(50), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    token_data = Column(JSONB, default=dict, nullable=False)
    
    # Token lifecycle
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    
    def __repr__(self) -> str:
        return f"<UserToken(id={self.id}, user_id={self.user_id}, type={self.token_type})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired, not used, not revoked)."""
        return not self.is_expired and not self.is_revoked and self.used_at is None
    
    def use_token(self) -> None:
        """Mark token as used."""
        self.used_at = datetime.utcnow()
    
    def revoke_token(self) -> None:
        """Revoke the token."""
        self.is_revoked = True


class UserActivity(Base):
    """
    User activity log entity for tracking user actions.
    """
    
    __tablename__ = "user_activities"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(100), nullable=False, index=True)
    activity_data = Column(JSONB, default=dict, nullable=False)
    
    # Context
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    session = relationship("Session")
    
    def __repr__(self) -> str:
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type={self.activity_type})>"
