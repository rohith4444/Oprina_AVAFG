"""
Session request models for Oprina API.
Simplified models for voice-first chat sessions.
"""

from pydantic import BaseModel, Field, field_validator
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

class UpdateSessionRequest(BaseModel):
    """Request model for updating session title."""
    title: str = Field(
        ..., 
        description="New session title",
        min_length=1,
        max_length=20
    )

    @field_validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        if len(v.strip()) > 20:
            raise ValueError('Title cannot exceed 20 characters')
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "title": "Gmail Integration"
            }
        }

class RegenerateTitleRequest(BaseModel):
    """Request model for regenerating session title (optional - can be empty for auto-generation)."""
    
    # Optional: Allow custom content for title generation
    custom_content: Optional[str] = Field(
        None, 
        description="Custom content to generate title from (uses first message if not provided)",
        max_length=200
    )

    class Config:
        schema_extra = {
            "example": {
                "custom_content": "Help me organize my Gmail inbox"
            }
        }