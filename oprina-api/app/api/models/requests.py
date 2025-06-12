"""
Pydantic models for API requests.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    email: EmailStr = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User preferences")


class UpdateUserRequest(BaseModel):
    """Request model for updating user information."""
    display_name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    settings: Optional[Dict[str, Any]] = Field(None, description="User settings")


class CreateChatSessionRequest(BaseModel):
    """Request model for creating a chat session."""
    session_type: str = Field(default="chat", description="Type of chat session")


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    message: str = Field(..., description="Message content")
    message_type: str = Field(default="text", description="Type of message")


class UpdateSessionRequest(BaseModel):
    """Request model for updating a session."""
    status: Optional[str] = Field(None, description="Session status")
    session_type: Optional[str] = Field(None, description="Session type") 