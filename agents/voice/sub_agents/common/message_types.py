"""
Message Types for Oprina Agent Communication

This module defines standard message formats and data structures used
for communication between agents in the Oprina voice assistant system.

Key Components:
- AgentMessage: Standard inter-agent communication format
- VoiceInput: Voice command processing data
- EmailContext: Email-related message context
- ResponseMetadata: Response formatting and delivery info
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """Standard message types for agent communication."""
    
    # Voice-related messages
    VOICE_INPUT = "voice_input"
    VOICE_COMMAND = "voice_command"
    SPEECH_SYNTHESIS = "speech_synthesis"
    
    # Email-related messages
    EMAIL_FETCH_REQUEST = "email_fetch_request"
    EMAIL_FETCH_RESPONSE = "email_fetch_response"
    EMAIL_SEND_REQUEST = "email_send_request"
    EMAIL_SEND_RESPONSE = "email_send_response"
    EMAIL_DRAFT_REQUEST = "email_draft_request"
    EMAIL_DRAFT_RESPONSE = "email_draft_response"
    
    # Content processing messages
    CONTENT_SUMMARIZE_REQUEST = "content_summarize_request"
    CONTENT_SUMMARIZE_RESPONSE = "content_summarize_response"
    CONTENT_GENERATE_REQUEST = "content_generate_request"
    CONTENT_GENERATE_RESPONSE = "content_generate_response"
    
    # Coordination messages
    TASK_DELEGATION = "task_delegation"
    TASK_COMPLETION = "task_completion"
    STATUS_UPDATE = "status_update"
    ERROR_NOTIFICATION = "error_notification"
    
    # System messages
    SESSION_INIT = "session_init"
    SESSION_UPDATE = "session_update"
    HEALTH_CHECK = "health_check"


class AgentRole(Enum):
    """Agent roles in the Oprina system."""
    
    VOICE_AGENT = "voice_agent"
    COORDINATOR_AGENT = "coordinator_agent"
    EMAIL_AGENT = "email_agent"
    CONTENT_AGENT = "content_agent"
    SYSTEM = "system"


class Priority(Enum):
    """Message priority levels."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """
    Standard message format for inter-agent communication.
    
    This is the core message structure used throughout the Oprina system
    for agent-to-agent communication and coordination.
    """
    
    sender: str  # Agent name/ID that sent the message
    recipient: str  # Agent name/ID that should receive the message
    message_type: MessageType  # Type of message (from MessageType enum)
    payload: Dict[str, Any]  # Message data/content
    session_id: str  # Session identifier for context
    timestamp: datetime = field(default_factory=datetime.utcnow)  # When message was created
    message_id: str = field(default_factory=lambda: f"msg_{datetime.utcnow().timestamp()}")  # Unique message ID
    priority: Priority = Priority.NORMAL  # Message priority
    requires_response: bool = False  # Whether sender expects a response
    correlation_id: Optional[str] = None  # For request-response correlation
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "priority": self.priority.value,
            "requires_response": self.requires_response,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        return cls(
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=MessageType(data["message_type"]),
            payload=data["payload"],
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_id=data["message_id"],
            priority=Priority(data["priority"]),
            requires_response=data["requires_response"],
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {})
        )


@dataclass
class VoiceInput:
    """
    Voice input data structure for processing voice commands.
    """
    
    audio_data: Optional[bytes] = None  # Raw audio data
    transcribed_text: str = ""  # Speech-to-text result
    confidence_score: float = 0.0  # Transcription confidence (0.0-1.0)
    language: str = "en-US"  # Detected/specified language
    duration_seconds: float = 0.0  # Audio duration
    sample_rate: int = 16000  # Audio sample rate
    user_id: str = ""  # User who spoke
    session_id: str = ""  # Session context
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional voice metadata
    
    def to_agent_message(self, sender: str, recipient: str) -> AgentMessage:
        """Convert to AgentMessage for inter-agent communication."""
        return AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.VOICE_INPUT,
            payload={
                "transcribed_text": self.transcribed_text,
                "confidence_score": self.confidence_score,
                "language": self.language,
                "duration_seconds": self.duration_seconds,
                "user_id": self.user_id,
                "metadata": self.metadata
            },
            session_id=self.session_id
        )


@dataclass
class EmailContext:
    """
    Email context data for email-related operations.
    """
    
    operation: str = ""  # fetch, send, draft, organize, etc.
    email_ids: List[str] = field(default_factory=list)  # Specific email IDs
    query_params: Dict[str, Any] = field(default_factory=dict)  # Search/filter parameters
    content_data: Dict[str, Any] = field(default_factory=dict)  # Email content for send/draft
    user_id: str = ""  # User performing the operation
    session_id: str = ""  # Session context
    gmail_authenticated: bool = False  # Whether Gmail is connected
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_agent_message(self, sender: str, recipient: str, message_type: MessageType) -> AgentMessage:
        """Convert to AgentMessage for inter-agent communication."""
        return AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            payload={
                "operation": self.operation,
                "email_ids": self.email_ids,
                "query_params": self.query_params,
                "content_data": self.content_data,
                "user_id": self.user_id,
                "gmail_authenticated": self.gmail_authenticated
            },
            session_id=self.session_id,
            requires_response=True
        )


@dataclass
class ContentProcessingRequest:
    """
    Content processing request for summarization, generation, etc.
    """
    
    operation: str = ""  # summarize, generate, analyze, etc.
    content: str = ""  # Text content to process
    content_type: str = "text"  # text, email, html, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)  # Processing parameters
    user_preferences: Dict[str, Any] = field(default_factory=dict)  # User preferences
    user_id: str = ""  # User requesting the operation
    session_id: str = ""  # Session context
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_agent_message(self, sender: str, recipient: str) -> AgentMessage:
        """Convert to AgentMessage for inter-agent communication."""
        return AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.CONTENT_GENERATE_REQUEST if "generate" in self.operation else MessageType.CONTENT_SUMMARIZE_REQUEST,
            payload={
                "operation": self.operation,
                "content": self.content,
                "content_type": self.content_type,
                "parameters": self.parameters,
                "user_preferences": self.user_preferences,
                "user_id": self.user_id
            },
            session_id=self.session_id,
            requires_response=True
        )


@dataclass
class ResponseMetadata:
    """
    Metadata for agent responses including formatting and delivery preferences.
    """
    
    response_format: str = "text"  # text, audio, html, json
    include_audio: bool = False  # Whether to synthesize speech
    voice_settings: Dict[str, Any] = field(default_factory=dict)  # TTS settings
    avatar_animation: bool = False  # Whether to animate avatar
    user_preferences: Dict[str, Any] = field(default_factory=dict)  # User response preferences
    processing_time_ms: float = 0.0  # Time taken to process
    confidence_score: float = 1.0  # Response confidence
    sources: List[str] = field(default_factory=list)  # Information sources
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for embedding in AgentMessage."""
        return {
            "response_format": self.response_format,
            "include_audio": self.include_audio,
            "voice_settings": self.voice_settings,
            "avatar_animation": self.avatar_animation,
            "user_preferences": self.user_preferences,
            "processing_time_ms": self.processing_time_ms,
            "confidence_score": self.confidence_score,
            "sources": self.sources
        }


@dataclass
class TaskResult:
    """
    Standard result format for completed tasks.
    """
    
    success: bool = False  # Whether task completed successfully
    result_data: Any = None  # Task result data
    error_message: str = ""  # Error description if failed
    processing_time_ms: float = 0.0  # Time taken
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional result metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for use in AgentMessage payload."""
        return {
            "success": self.success,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata
        }


# =============================================================================
# Message Builder Helper Functions
# =============================================================================

def create_voice_command_message(
    sender: str,
    recipient: str,
    transcribed_text: str,
    session_id: str,
    user_id: str,
    **kwargs
) -> AgentMessage:
    """Helper function to create voice command messages."""
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type=MessageType.VOICE_COMMAND,
        payload={
            "transcribed_text": transcribed_text,
            "user_id": user_id,
            **kwargs
        },
        session_id=session_id,
        requires_response=True
    )


def create_email_operation_message(
    sender: str,
    recipient: str,
    operation: str,
    session_id: str,
    user_id: str,
    **kwargs
) -> AgentMessage:
    """Helper function to create email operation messages."""
    message_type_map = {
        "fetch": MessageType.EMAIL_FETCH_REQUEST,
        "send": MessageType.EMAIL_SEND_REQUEST,
        "draft": MessageType.EMAIL_DRAFT_REQUEST
    }
    
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type=message_type_map.get(operation, MessageType.EMAIL_FETCH_REQUEST),
        payload={
            "operation": operation,
            "user_id": user_id,
            **kwargs
        },
        session_id=session_id,
        requires_response=True
    )


def create_content_processing_message(
    sender: str,
    recipient: str,
    operation: str,
    content: str,
    session_id: str,
    user_id: str,
    **kwargs
) -> AgentMessage:
    """Helper function to create content processing messages."""
    message_type = (
        MessageType.CONTENT_GENERATE_REQUEST 
        if "generate" in operation 
        else MessageType.CONTENT_SUMMARIZE_REQUEST
    )
    
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type=message_type,
        payload={
            "operation": operation,
            "content": content,
            "user_id": user_id,
            **kwargs
        },
        session_id=session_id,
        requires_response=True
    )


def create_task_completion_message(
    sender: str,
    recipient: str,
    task_result: TaskResult,
    session_id: str,
    correlation_id: str = None
) -> AgentMessage:
    """Helper function to create task completion messages."""
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type=MessageType.TASK_COMPLETION,
        payload=task_result.to_dict(),
        session_id=session_id,
        correlation_id=correlation_id
    )


# =============================================================================
# Message Validation
# =============================================================================

def validate_agent_message(message: AgentMessage) -> List[str]:
    """
    Validate an AgentMessage and return list of validation errors.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    if not message.sender:
        errors.append("Message must have a sender")
    
    if not message.recipient:
        errors.append("Message must have a recipient")
    
    if not message.session_id:
        errors.append("Message must have a session_id")
    
    if not isinstance(message.payload, dict):
        errors.append("Message payload must be a dictionary")
    
    if not isinstance(message.message_type, MessageType):
        errors.append("Message type must be a valid MessageType enum")
    
    return errors


# =============================================================================
# Export All Public Components
# =============================================================================

__all__ = [
    # Enums
    "MessageType",
    "AgentRole", 
    "Priority",
    
    # Data Classes
    "AgentMessage",
    "VoiceInput",
    "EmailContext",
    "ContentProcessingRequest",
    "ResponseMetadata",
    "TaskResult",
    
    # Helper Functions
    "create_voice_command_message",
    "create_email_operation_message",
    "create_content_processing_message",
    "create_task_completion_message",
    "validate_agent_message",
]