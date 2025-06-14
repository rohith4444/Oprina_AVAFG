"""
Session response models for Oprina API.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SessionDetailResponse(BaseModel):
    """Response model for session details."""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    status: str = Field(..., description="Session status")
    session_type: str = Field(..., description="Session type")
    created_at: str = Field(..., description="Creation timestamp")
    last_activity_at: Optional[str] = Field(None, description="Last activity timestamp")
    message_count: int = Field(default=0, description="Number of messages in session")


class SessionListResponse(BaseModel):
    """Response model for session list."""
    sessions: List[SessionDetailResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Items skipped")
    has_more: bool = Field(..., description="Whether there are more sessions")


class SessionStatsResponse(BaseModel):
    """Response model for session statistics."""
    session_id: str = Field(..., description="Session ID")
    total_messages: int = Field(..., description="Total messages")
    user_messages: int = Field(..., description="User messages")
    assistant_messages: int = Field(..., description="Assistant messages")
    duration_seconds: Optional[float] = Field(None, description="Session duration")
    status: str = Field(..., description="Session status")
