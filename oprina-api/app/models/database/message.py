"""
Message database entity model for Oprina API.

This module defines the SQLAlchemy Message model that corresponds to the 'messages' table
in the database schema. It handles individual chat messages within sessions.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class Message(Base):
    """
    Message entity representing a single message in a chat session.
    
    This model handles message content, metadata, token usage,
    and agent processing information.
    """
    
    __tablename__ = "messages"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Message content
    role = Column(String(50), nullable=False, index=True)  # user, assistant, system, function
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default='text', nullable=False)  # text, image, audio, file
    
    # Message metadata
    message_index = Column(Integer, nullable=False, index=True)  # Order within session
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=True, index=True)
    
    # Agent processing
    agent_response_data = Column(JSONB, default=dict, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Token usage
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Numeric(10, 4), default=Decimal('0.0000'), nullable=False)
    
    # Voice/Avatar integration
    has_voice_response = Column(Boolean, default=False, nullable=False)
    voice_response_url = Column(Text, nullable=True)
    has_avatar_response = Column(Boolean, default=False, nullable=False)
    avatar_session_id = Column(String(255), nullable=True)
    
    # Message status
    status = Column(String(50), default='completed', nullable=False)  # pending, processing, completed, error
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    parent_message = relationship("Message", remote_side=[id], backref="child_messages")
    
    # Unique constraint on session_id and message_index
    __table_args__ = (
        # UniqueConstraint('session_id', 'message_index', name='uq_session_message_index'),
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, session_id={self.session_id}, role={self.role}, index={self.message_index})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for API responses."""
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'role': self.role,
            'content': self.content,
            'content_type': self.content_type,
            'message_index': self.message_index,
            'parent_message_id': str(self.parent_message_id) if self.parent_message_id else None,
            'agent_response_data': self.agent_response_data,
            'processing_time_ms': self.processing_time_ms,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'estimated_cost': float(self.estimated_cost),
            'has_voice_response': self.has_voice_response,
            'voice_response_url': self.voice_response_url,
            'has_avatar_response': self.has_avatar_response,
            'avatar_session_id': self.avatar_session_id,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_chat_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format suitable for chat display."""
        return {
            'id': str(self.id),
            'role': self.role,
            'content': self.content,
            'content_type': self.content_type,
            'message_index': self.message_index,
            'has_voice_response': self.has_voice_response,
            'voice_response_url': self.voice_response_url,
            'has_avatar_response': self.has_avatar_response,
            'processing_time_ms': self.processing_time_ms,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }
    
    def to_agent_format(self) -> Dict[str, Any]:
        """Convert message to format suitable for AI agent."""
        return {
            'role': self.role,
            'content': self.content
        }
    
    @property
    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.role == 'user'
    
    @property
    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message."""
        return self.role == 'assistant'
    
    @property
    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.role == 'system'
    
    @property
    def is_function_message(self) -> bool:
        """Check if this is a function message."""
        return self.role == 'function'
    
    @property
    def is_completed(self) -> bool:
        """Check if message processing is completed."""
        return self.status == 'completed'
    
    @property
    def is_processing(self) -> bool:
        """Check if message is currently being processed."""
        return self.status == 'processing'
    
    @property
    def is_pending(self) -> bool:
        """Check if message is pending processing."""
        return self.status == 'pending'
    
    @property
    def has_error(self) -> bool:
        """Check if message has an error."""
        return self.status == 'error' or self.error_message is not None
    
    @property
    def content_preview(self) -> str:
        """Get a preview of the message content (first 100 characters)."""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."
    
    def update_agent_response(self, response_data: Dict[str, Any]) -> None:
        """Update agent response data, merging with existing data."""
        if self.agent_response_data is None:
            self.agent_response_data = {}
        
        # Merge response data
        current_data = dict(self.agent_response_data)
        current_data.update(response_data)
        self.agent_response_data = current_data
    
    def get_agent_response(self, key: str, default: Any = None) -> Any:
        """Get a specific agent response value."""
        if self.agent_response_data is None:
            return default
        return self.agent_response_data.get(key, default)
    
    def set_agent_response(self, key: str, value: Any) -> None:
        """Set a specific agent response value."""
        if self.agent_response_data is None:
            self.agent_response_data = {}
        
        data = dict(self.agent_response_data)
        data[key] = value
        self.agent_response_data = data
    
    def set_tokens(self, prompt_tokens: int, completion_tokens: int, cost: Decimal = Decimal('0.0000')) -> None:
        """Set token usage for this message."""
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.estimated_cost = cost
    
    def set_processing_time(self, processing_time_ms: int) -> None:
        """Set the processing time for this message."""
        self.processing_time_ms = processing_time_ms
    
    def start_processing(self) -> None:
        """Mark message as being processed."""
        self.status = 'processing'
    
    def complete_processing(self) -> None:
        """Mark message processing as completed."""
        self.status = 'completed'
    
    def mark_error(self, error_message: str) -> None:
        """Mark message as having an error."""
        self.status = 'error'
        self.error_message = error_message
    
    def clear_error(self) -> None:
        """Clear any error status."""
        if self.status == 'error':
            self.status = 'completed'
        self.error_message = None
    
    def set_voice_response(self, voice_url: str) -> None:
        """Set voice response URL for this message."""
        self.has_voice_response = True
        self.voice_response_url = voice_url
    
    def set_avatar_response(self, avatar_session_id: str) -> None:
        """Set avatar session ID for this message."""
        self.has_avatar_response = True
        self.avatar_session_id = avatar_session_id
    
    def clear_voice_response(self) -> None:
        """Clear voice response data."""
        self.has_voice_response = False
        self.voice_response_url = None
    
    def clear_avatar_response(self) -> None:
        """Clear avatar response data."""
        self.has_avatar_response = False
        self.avatar_session_id = None
    
    @classmethod
    def create_user_message(
        cls,
        session_id: str,
        content: str,
        message_index: int,
        content_type: str = 'text',
        **kwargs
    ) -> "Message":
        """
        Create a new user message instance.
        
        Args:
            session_id: Session identifier
            content: Message content
            message_index: Index in the session
            content_type: Type of content
            **kwargs: Additional message attributes
            
        Returns:
            New Message instance
        """
        return cls(
            session_id=session_id,
            role='user',
            content=content,
            message_index=message_index,
            content_type=content_type,
            status='completed',  # User messages are immediately completed
            **kwargs
        )
    
    @classmethod
    def create_assistant_message(
        cls,
        session_id: str,
        content: str,
        message_index: int,
        parent_message_id: Optional[str] = None,
        **kwargs
    ) -> "Message":
        """
        Create a new assistant message instance.
        
        Args:
            session_id: Session identifier
            content: Message content
            message_index: Index in the session
            parent_message_id: ID of the user message this responds to
            **kwargs: Additional message attributes
            
        Returns:
            New Message instance
        """
        return cls(
            session_id=session_id,
            role='assistant',
            content=content,
            message_index=message_index,
            parent_message_id=parent_message_id,
            content_type='text',
            status='processing',  # Assistant messages start as processing
            **kwargs
        )
    
    @classmethod
    def create_system_message(
        cls,
        session_id: str,
        content: str,
        message_index: int,
        **kwargs
    ) -> "Message":
        """
        Create a new system message instance.
        
        Args:
            session_id: Session identifier
            content: Message content
            message_index: Index in the session
            **kwargs: Additional message attributes
            
        Returns:
            New Message instance
        """
        return cls(
            session_id=session_id,
            role='system',
            content=content,
            message_index=message_index,
            content_type='text',
            status='completed',  # System messages are immediately completed
            **kwargs
        )
    
    def get_conversation_context(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """Get conversation context including this message and previous messages."""
        # This would typically be implemented by the repository layer
        # Here we return a placeholder
        return [self.to_agent_format()]
