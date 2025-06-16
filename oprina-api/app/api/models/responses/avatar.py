"""
Avatar response models for Oprina API.
Simple models for avatar session management and quota tracking responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QuotaStatusResponse(BaseModel):
    """Response showing user's current avatar quota status."""
    
    can_create_session: bool = Field(
        ..., 
        description="Whether user can create a new session (under 20-minute limit)"
    )
    
    total_seconds_used: int = Field(
        ..., 
        description="Total seconds of avatar streaming used (lifetime)"
    )
    
    remaining_seconds: int = Field(
        ..., 
        description="Remaining seconds before hitting 20-minute limit"
    )
    
    quota_exhausted: bool = Field(
        ..., 
        description="Whether user has exhausted their 20-minute quota"
    )
    
    quota_percentage: float = Field(
        ..., 
        description="Percentage of quota used (0-100)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "can_create_session": True,
                "total_seconds_used": 450,
                "remaining_seconds": 750,
                "quota_exhausted": False,
                "quota_percentage": 37.5
            }
        }


class SessionResponse(BaseModel):
    """Response for session creation/ending operations."""
    
    success: bool = Field(..., description="Whether operation was successful")
    
    session_id: Optional[str] = Field(
        None, 
        description="Internal session ID (UUID)"
    )
    
    heygen_session_id: str = Field(
        ..., 
        description="HeyGen session ID"
    )
    
    status: str = Field(
        ..., 
        description="Session status (active, completed, error, timeout)"
    )
    
    duration_seconds: Optional[int] = Field(
        None, 
        description="Session duration in seconds (for ended sessions)"
    )
    
    quota_info: Optional[QuotaStatusResponse] = Field(
        None, 
        description="Updated quota information"
    )
    
    message: Optional[str] = Field(
        None, 
        description="Additional message or error details"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "heygen_session_id": "session_abc123xyz789",
                "status": "active",
                "duration_seconds": None,
                "quota_info": {
                    "can_create_session": True,
                    "total_seconds_used": 0,
                    "remaining_seconds": 1200,
                    "quota_exhausted": False,
                    "quota_percentage": 0.0
                },
                "message": "Session started successfully"
            }
        }


class SessionStatusResponse(BaseModel):
    """Response for session status check."""
    
    exists: bool = Field(..., description="Whether session exists")
    
    active: bool = Field(..., description="Whether session is currently active")
    
    heygen_session_id: str = Field(..., description="HeyGen session ID")
    
    status: str = Field(
        ..., 
        description="Session status (active, completed, error, timeout)"
    )
    
    started_at: Optional[datetime] = Field(
        None, 
        description="When session was started"
    )
    
    duration_seconds: Optional[int] = Field(
        None, 
        description="Current or final duration in seconds"
    )
    
    remaining_seconds: Optional[int] = Field(
        None, 
        description="Seconds remaining before 20-minute timeout (for active sessions)"
    )
    
    avatar_name: Optional[str] = Field(
        None, 
        description="Avatar name used in session"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "exists": True,
                "active": True,
                "heygen_session_id": "session_abc123xyz789",
                "status": "active",
                "started_at": "2025-06-16T10:30:00Z",
                "duration_seconds": 150,
                "remaining_seconds": 1050,
                "avatar_name": "Ann_Therapist_public"
            }
        }


class UserSessionsResponse(BaseModel):
    """Response showing all user's sessions."""
    
    total_sessions: int = Field(..., description="Total number of sessions")
    
    active_sessions: int = Field(..., description="Number of currently active sessions")
    
    sessions: List[SessionStatusResponse] = Field(
        ..., 
        description="List of session details"
    )
    
    quota_status: QuotaStatusResponse = Field(
        ..., 
        description="Current quota status"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "total_sessions": 5,
                "active_sessions": 1,
                "sessions": [
                    {
                        "exists": True,
                        "active": True,
                        "heygen_session_id": "session_abc123",
                        "status": "active",
                        "started_at": "2025-06-16T10:30:00Z",
                        "duration_seconds": 150,
                        "remaining_seconds": 1050,
                        "avatar_name": "Ann_Therapist_public"
                    }
                ],
                "quota_status": {
                    "can_create_session": True,
                    "total_seconds_used": 450,
                    "remaining_seconds": 750,
                    "quota_exhausted": False,
                    "quota_percentage": 37.5
                }
            }
        }


class AvatarErrorResponse(BaseModel):
    """Response for avatar operation errors."""
    
    success: bool = Field(False, description="Always false for errors")
    
    error_code: str = Field(..., description="Error code identifier")
    
    error_message: str = Field(..., description="Human-readable error message")
    
    details: Optional[str] = Field(
        None, 
        description="Additional error details"
    )
    
    quota_status: Optional[QuotaStatusResponse] = Field(
        None, 
        description="Current quota status (when relevant)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error_code": "QUOTA_EXHAUSTED",
                "error_message": "20-minute avatar streaming quota has been exhausted",
                "details": "User has used 1200/1200 seconds",
                "quota_status": {
                    "can_create_session": False,
                    "total_seconds_used": 1200,
                    "remaining_seconds": 0,
                    "quota_exhausted": True,
                    "quota_percentage": 100.0
                }
            }
        }