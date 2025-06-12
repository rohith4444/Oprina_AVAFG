"""
Pydantic models for API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")


class UserResponse(BaseModel):
    """Response model for user information."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    display_name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    created_at: Optional[str] = Field(None, description="Account creation timestamp")
    last_login_at: Optional[str] = Field(None, description="Last login timestamp")


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(..., description="Token type")
    user: UserResponse = Field(..., description="User information")


class ChatSessionResponse(BaseModel):
    """Response model for chat session creation."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    agent_session_id: Optional[str] = Field(None, description="Agent session ID")
    status: str = Field(..., description="Session status")
    created_at: str = Field(..., description="Session creation timestamp")


class MessageResponse(BaseModel):
    """Response model for message sending."""
    session_id: str = Field(..., description="Session ID")
    user_message: Dict[str, Any] = Field(..., description="User message data")
    assistant_response: Dict[str, Any] = Field(..., description="Assistant response data")
    response_text: str = Field(..., description="Assistant response text")


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict[str, Any]] = Field(..., description="List of messages")
    total_messages: int = Field(..., description="Total number of messages")
    session_info: Dict[str, Any] = Field(..., description="Session information")


class SessionStatsResponse(BaseModel):
    """Response model for session statistics."""
    session_id: str = Field(..., description="Session ID")
    total_messages: int = Field(..., description="Total number of messages")
    user_messages_count: int = Field(..., description="Number of user messages")
    assistant_messages_count: int = Field(..., description="Number of assistant messages")
    session_duration: Optional[float] = Field(None, description="Session duration in seconds")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    status: str = Field(..., description="Session status") 