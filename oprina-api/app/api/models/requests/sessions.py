"""
Session request models for Oprina API.
Simplified models for voice-first chat sessions.
"""

from pydantic import BaseModel, Field
from typing import Optional


class CreateSessionRequest(BaseModel):
    """Request model for creating a new session."""
    title: Optional[str] = Field(
        default=None, 
        description="Custom title for the session",
        max_length=500
    )

    class Config:
        schema_extra = {
            "example": {
                "title": "Voice Chat with Oprina"
            }
        }


class SessionListRequest(BaseModel):
    """Request model for listing user sessions."""
    active_only: bool = Field(
        default=True, 
        description="Only return active sessions (exclude ended/deleted)"
    )
    limit: int = Field(
        default=50, 
        description="Maximum sessions to return", 
        ge=1, 
        le=100
    )

    class Config:
        schema_extra = {
            "example": {
                "active_only": True,
                "limit": 20
            }
        }


class SessionMessagesRequest(BaseModel):
    """Request model for getting session messages."""
    limit: int = Field(
        default=50, 
        description="Maximum messages to return", 
        ge=1, 
        le=200
    )
    message_type: Optional[str] = Field(
        default=None, 
        description="Filter by message type: 'voice', 'text', or None for all"
    )

    class Config:
        schema_extra = {
            "example": {
                "limit": 50,
                "message_type": "voice"
            }
        }