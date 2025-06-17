"""
Session response models for Oprina API.
Simplified models for voice-first chat sessions.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SessionResponse(BaseModel):
    """Response model for individual session data."""
    session_id: str = Field(..., description="Unique session identifier")
    title: str = Field(..., description="Session title")
    status: str = Field(..., description="Session status: active, ended, deleted")
    created_at: str = Field(..., description="Session creation timestamp")
    last_activity_at: str = Field(..., description="Last activity timestamp")
    message_count: int = Field(..., description="Number of messages in session")
    has_vertex_session: bool = Field(..., description="Whether linked to Vertex AI")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Voice Chat with Oprina",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z",
                "last_activity_at": "2024-01-15T10:30:00Z",
                "message_count": 8,
                "has_vertex_session": True
            }
        }


class SessionDetailResponse(BaseModel):
    """Response model for detailed session information."""
    session_id: str = Field(..., description="Unique session identifier")
    title: str = Field(..., description="Session title")
    status: str = Field(..., description="Session status")
    created_at: str = Field(..., description="Session creation timestamp")
    last_activity_at: str = Field(..., description="Last activity timestamp")
    updated_at: str = Field(..., description="Last updated timestamp")
    vertex_session_id: Optional[str] = Field(None, description="Vertex AI session ID")
    message_count: int = Field(..., description="Total messages in session")
    latest_messages: List[Dict[str, Any]] = Field(..., description="Preview of recent messages")
    permissions: Dict[str, bool] = Field(..., description="User permissions for this session")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Voice Chat with Oprina",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z",
                "last_activity_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "vertex_session_id": "vertex_abc123",
                "message_count": 8,
                "latest_messages": [
                    {
                        "role": "user",
                        "content": "Can you help me with my tasks?",
                        "message_type": "voice",
                        "created_at": "2024-01-15T10:25:00Z"
                    }
                ],
                "permissions": {
                    "can_read": True,
                    "can_send_messages": True,
                    "can_delete": True
                }
            }
        }


class SessionListResponse(BaseModel):
    """Response model for session list."""
    sessions: List[SessionResponse] = Field(..., description="List of user sessions")
    total: int = Field(..., description="Total number of sessions returned")
    user_id: str = Field(..., description="User ID")
    active_only: bool = Field(..., description="Whether only active sessions were returned")

    class Config:
        schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Voice Chat with Oprina",
                        "status": "active",
                        "created_at": "2024-01-15T10:00:00Z",
                        "last_activity_at": "2024-01-15T10:30:00Z",
                        "message_count": 8,
                        "has_vertex_session": True
                    }
                ],
                "total": 1,
                "user_id": "user-123",
                "active_only": True
            }
        }


class CreateSessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str = Field(..., description="Newly created session ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Session title")
    status: str = Field(..., description="Session status")
    created_at: str = Field(..., description="Creation timestamp")
    vertex_session_id: Optional[str] = Field(None, description="Vertex AI session ID (if created)")
    message: str = Field(..., description="Success message")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user-123",
                "title": "New Chat",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z",
                "vertex_session_id": None,
                "message": "Session created successfully"
            }
        }


class SessionMessagesResponse(BaseModel):
    """Response model for session messages."""
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict[str, Any]] = Field(..., description="List of messages")
    total_messages: int = Field(..., description="Number of messages returned")
    limit: int = Field(..., description="Applied message limit")
    message_type_filter: Optional[str] = Field(None, description="Applied message type filter")
    session_info: Dict[str, Any] = Field(..., description="Basic session information")

    class Config:
        schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "messages": [
                    {
                        "id": "msg-123",
                        "role": "user",
                        "content": "Can you help me with my tasks today?",
                        "message_type": "voice",
                        "voice_metadata": {
                            "duration": 3.2,
                            "confidence": 0.95
                        },
                        "message_index": 1,
                        "created_at": "2024-01-15T10:25:00Z"
                    },
                    {
                        "id": "msg-124",
                        "role": "assistant",
                        "content": "I'd be happy to help you with your tasks!",
                        "message_type": "text",
                        "voice_metadata": {},
                        "message_index": 2,
                        "created_at": "2024-01-15T10:25:30Z"
                    }
                ],
                "total_messages": 2,
                "limit": 50,
                "message_type_filter": None,
                "session_info": {
                    "title": "Voice Chat with Oprina",
                    "status": "active",
                    "created_at": "2024-01-15T10:00:00Z",
                    "last_activity_at": "2024-01-15T10:25:30Z"
                }
            }
        }


class DeleteSessionResponse(BaseModel):
    """Response model for session deletion."""
    message: str = Field(..., description="Success message")
    session_id: str = Field(..., description="Deleted session ID")
    title: str = Field(..., description="Deleted session title")

    class Config:
        schema_extra = {
            "example": {
                "message": "Session deleted successfully",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Voice Chat with Oprina"
            }
        }


class EndSessionResponse(BaseModel):
    """Response model for ending a session."""
    message: str = Field(..., description="Success message")
    session_id: str = Field(..., description="Ended session ID")
    title: str = Field(..., description="Session title")
    status: str = Field(..., description="New session status")
    ended_at: str = Field(..., description="When session was ended")

    class Config:
        schema_extra = {
            "example": {
                "message": "Session ended successfully",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Voice Chat with Oprina",
                "status": "ended",
                "ended_at": "2024-01-15T11:00:00Z"
            }
        }