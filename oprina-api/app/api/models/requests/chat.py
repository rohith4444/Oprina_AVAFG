"""
Chat request models for Oprina API.

This module defines Pydantic models for chat-related API requests.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class CreateChatSessionRequest(BaseModel):
    """Request model for creating a chat session."""
    session_type: str = Field(default="chat", description="Type of chat session")

    class Config:
        schema_extra = {
            "example": {
                "session_type": "chat"
            }
        }


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    message: str = Field(..., description="Message content", min_length=1, max_length=5000)
    message_type: str = Field(default="text", description="Type of message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")

    class Config:
        schema_extra = {
            "example": {
                "message": "Hello, how can you help me today?",
                "message_type": "text",
                "metadata": {
                    "source": "web_app",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }


class StreamMessageRequest(BaseModel):
    """Request model for streaming a message."""
    message: str = Field(..., description="Message content", min_length=1, max_length=5000)
    message_type: str = Field(default="text", description="Type of message")
    stream_settings: Optional[Dict[str, Any]] = Field(default=None, description="Streaming configuration")

    class Config:
        schema_extra = {
            "example": {
                "message": "Tell me a story about AI",
                "message_type": "text",
                "stream_settings": {
                    "chunk_size": 50,
                    "delay_ms": 100
                }
            }
        }


class ChatHistoryRequest(BaseModel):
    """Request model for getting chat history."""
    limit: int = Field(default=20, description="Maximum number of messages to return", ge=1, le=100)
    offset: int = Field(default=0, description="Number of messages to skip", ge=0)
    message_type: Optional[str] = Field(default=None, description="Filter by message type")

    class Config:
        schema_extra = {
            "example": {
                "limit": 20,
                "offset": 0,
                "message_type": "text"
            }
        }


class DeleteMessageRequest(BaseModel):
    """Request model for deleting a message."""
    reason: Optional[str] = Field(default=None, description="Reason for deletion", max_length=500)

    class Config:
        schema_extra = {
            "example": {
                "reason": "User requested message deletion"
            }
        }


class UpdateSessionRequest(BaseModel):
    """Request model for updating a session."""
    status: Optional[str] = Field(None, description="Session status")
    session_type: Optional[str] = Field(None, description="Session type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")

    class Config:
        schema_extra = {
            "example": {
                "status": "active",
                "session_type": "chat",
                "metadata": {
                    "last_updated": "2024-01-15T10:30:00Z",
                    "updated_by": "user"
                }
            }
        }


class SessionFilterRequest(BaseModel):
    """Request model for filtering sessions."""
    active_only: bool = Field(default=True, description="Only return active sessions")
    session_type: Optional[str] = Field(default=None, description="Filter by session type")
    limit: int = Field(default=50, description="Maximum number of sessions to return", ge=1, le=100)
    offset: int = Field(default=0, description="Number of sessions to skip", ge=0)

    class Config:
        schema_extra = {
            "example": {
                "active_only": True,
                "session_type": "chat",
                "limit": 50,
                "offset": 0
            }
        }
