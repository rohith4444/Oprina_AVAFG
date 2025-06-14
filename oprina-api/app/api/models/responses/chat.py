"""
Chat response models for Oprina API.

This module defines Pydantic models for chat-related API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatSessionResponse(BaseModel):
    """Response model for chat session creation."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    agent_session_id: Optional[str] = Field(None, description="Agent session ID")
    status: str = Field(..., description="Session status")
    created_at: str = Field(..., description="Session creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "user_id": "user-456",
                "agent_session_id": "agent-session-789",
                "status": "active",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class MessageResponse(BaseModel):
    """Response model for message sending."""
    session_id: str = Field(..., description="Session ID")
    user_message: Dict[str, Any] = Field(..., description="User message data")
    assistant_response: Dict[str, Any] = Field(..., description="Assistant response data")
    response_text: str = Field(..., description="Assistant response text")
    message_id: Optional[str] = Field(None, description="Message ID")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "user_message": {
                    "id": "msg-user-456",
                    "text": "Hello, how are you?",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                "assistant_response": {
                    "id": "msg-assistant-789",
                    "text": "Hello! I'm doing well, thank you for asking. How can I help you today?",
                    "timestamp": "2024-01-15T10:30:05Z"
                },
                "response_text": "Hello! I'm doing well, thank you for asking. How can I help you today?",
                "message_id": "msg-assistant-789",
                "processing_time": 2.5
            }
        }


class StreamEventResponse(BaseModel):
    """Response model for streaming events."""
    type: str = Field(..., description="Event type")
    data: Optional[Dict[str, Any]] = Field(None, description="Event data")
    message: Optional[str] = Field(None, description="Event message")
    timestamp: str = Field(..., description="Event timestamp")

    class Config:
        schema_extra = {
            "example": {
                "type": "message_chunk",
                "data": {
                    "chunk": "Hello! I'm",
                    "chunk_index": 1,
                    "total_chunks": 10
                },
                "message": "Streaming message chunk",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict[str, Any]] = Field(..., description="List of messages")
    total_messages: int = Field(..., description="Total number of messages")
    session_info: Dict[str, Any] = Field(..., description="Session information")
    has_more: bool = Field(default=False, description="Whether there are more messages")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "text": "Hello",
                        "timestamp": "2024-01-15T10:30:00Z"
                    },
                    {
                        "id": "msg-2",
                        "role": "assistant",
                        "text": "Hello! How can I help you?",
                        "timestamp": "2024-01-15T10:30:05Z"
                    }
                ],
                "total_messages": 2,
                "session_info": {
                    "status": "active",
                    "created_at": "2024-01-15T10:00:00Z",
                    "last_activity_at": "2024-01-15T10:30:05Z"
                },
                "has_more": False
            }
        }


class SessionStatsResponse(BaseModel):
    """Response model for session statistics."""
    session_id: str = Field(..., description="Session ID")
    total_messages: int = Field(..., description="Total number of messages")
    user_messages_count: int = Field(..., description="Number of user messages")
    assistant_messages_count: int = Field(..., description="Number of assistant messages")
    session_duration: Optional[float] = Field(None, description="Session duration in seconds")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    status: str = Field(..., description="Session status")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "session-123",
                "total_messages": 10,
                "user_messages_count": 5,
                "assistant_messages_count": 5,
                "session_duration": 1800.0,
                "last_activity": "2024-01-15T10:30:00Z",
                "status": "active"
            }
        }


class SessionListResponse(BaseModel):
    """Response model for session list."""
    sessions: List[Dict[str, Any]] = Field(..., description="List of sessions")
    total_sessions: int = Field(..., description="Total number of sessions")
    user_id: str = Field(..., description="User ID")
    has_more: bool = Field(default=False, description="Whether there are more sessions")

    class Config:
        schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "session-123",
                        "status": "active",
                        "created_at": "2024-01-15T10:00:00Z",
                        "last_activity_at": "2024-01-15T10:30:00Z",
                        "message_count": 10
                    }
                ],
                "total_sessions": 1,
                "user_id": "user-456",
                "has_more": False
            }
        }


class DeleteMessageResponse(BaseModel):
    """Response model for message deletion."""
    message: str = Field(..., description="Deletion confirmation message")
    message_id: str = Field(..., description="ID of deleted message")
    deleted_at: str = Field(..., description="Deletion timestamp")

    class Config:
        schema_extra = {
            "example": {
                "message": "Message deleted successfully",
                "message_id": "msg-123",
                "deleted_at": "2024-01-15T10:30:00Z"
            }
        }


class EndSessionResponse(BaseModel):
    """Response model for ending a session."""
    message: str = Field(..., description="Session end confirmation message")
    session_id: str = Field(..., description="ID of ended session")
    ended_at: str = Field(..., description="Session end timestamp")
    final_stats: Optional[Dict[str, Any]] = Field(None, description="Final session statistics")

    class Config:
        schema_extra = {
            "example": {
                "message": "Session ended successfully",
                "session_id": "session-123",
                "ended_at": "2024-01-15T10:30:00Z",
                "final_stats": {
                    "total_messages": 10,
                    "duration_seconds": 1800
                }
            }
        }
