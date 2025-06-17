"""
Avatar request models for Oprina API.
Simple models for avatar session management and quota tracking.
"""

from pydantic import BaseModel, Field
from typing import Optional


class StartSessionRequest(BaseModel):
    """Request to start tracking a HeyGen avatar session."""
    
    heygen_session_id: str = Field(
        ..., 
        description="HeyGen session ID returned from HeyGen SDK",
        min_length=1,
        max_length=500
    )
    
    avatar_name: str = Field(
        default="Ann_Therapist_public",
        description="Name of the avatar being used",
        max_length=255
    )
    
    class Config:
        schema_extra = {
            "example": {
                "heygen_session_id": "session_abc123xyz789",
                "avatar_name": "Ann_Therapist_public"
            }
        }


class EndSessionRequest(BaseModel):
    """Request to end a HeyGen avatar session."""
    
    heygen_session_id: str = Field(
        ..., 
        description="HeyGen session ID to end",
        min_length=1,
        max_length=500
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Optional error message if session ended due to error",
        max_length=1000
    )
    
    class Config:
        schema_extra = {
            "example": {
                "heygen_session_id": "session_abc123xyz789",
                "error_message": None
            }
        }


class QuotaCheckRequest(BaseModel):
    """Request to check user's avatar quota status (usually no body needed)."""
    pass


class SessionStatusRequest(BaseModel):
    """Request to get status of a specific session."""
    
    heygen_session_id: str = Field(
        ..., 
        description="HeyGen session ID to check",
        min_length=1,
        max_length=500
    )
    
    class Config:
        schema_extra = {
            "example": {
                "heygen_session_id": "session_abc123xyz789"
            }
        }