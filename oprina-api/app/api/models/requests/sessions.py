"""
Session request models for Oprina API.

This module defines Pydantic models for session management API requests.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SessionFilterRequest(BaseModel):
    """Request model for filtering sessions."""
    active_only: bool = Field(default=True, description="Only return active sessions")
    session_type: Optional[str] = Field(default=None, description="Filter by session type")
    limit: int = Field(default=50, description="Maximum sessions to return", ge=1, le=100)
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


class UpdateSessionRequest(BaseModel):
    """Request model for updating session metadata."""
    status: Optional[str] = Field(None, description="Session status")
    metadata: Optional[dict] = Field(None, description="Session metadata")

    class Config:
        schema_extra = {
            "example": {
                "status": "active",
                "metadata": {"last_updated": "2024-01-15T10:30:00Z"}
            }
        }
