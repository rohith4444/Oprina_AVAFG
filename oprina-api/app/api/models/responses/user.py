"""
User response models for user management endpoints.
Based on your actual database schema and UI requirements.
"""

from typing import Optional
from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    """Response model for user profile data - matches your database schema."""
    
    # Core user fields
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    
    # Profile fields from your UI/database
    full_name: Optional[str] = Field(None, description="User's full name")
    preferred_name: Optional[str] = Field(None, description="User's preferred name")
    work_type: Optional[str] = Field(None, description="What best describes your work")
    ai_preferences: Optional[str] = Field(None, description="Personal preferences for AI")
    
    # Keep display_name for compatibility
    display_name: Optional[str] = Field(None, description="User's display name")
    avatar_url: Optional[str] = Field(None, description="User's avatar URL")
    
    # System preferences
    timezone: str = Field(..., description="User's timezone")
    language: str = Field(..., description="User's preferred language")
    
    # Account status
    is_active: bool = Field(..., description="Whether user account is active")
    is_verified: bool = Field(..., description="Whether user email is verified")
    
    # OAuth integration status
    has_google_oauth: bool = Field(..., description="Whether user has Google OAuth connected")
    has_microsoft_oauth: bool = Field(..., description="Whether user has Microsoft OAuth connected")
    
    # Timestamps
    created_at: str = Field(..., description="Account creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    last_login_at: Optional[str] = Field(None, description="Last login timestamp")
    last_activity_at: Optional[str] = Field(None, description="Last activity timestamp")
    email_verified_at: Optional[str] = Field(None, description="Email verification timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "user-123",
                "email": "john@example.com",
                "full_name": "John Smith",
                "preferred_name": "Johnny",
                "work_type": "Software Developer",
                "ai_preferences": "I prefer detailed explanations and focus on code examples",
                "display_name": "John Smith",
                "avatar_url": "https://example.com/avatar.jpg",
                "timezone": "UTC",
                "language": "en",
                "is_active": True,
                "is_verified": True,
                "has_google_oauth": False,
                "has_microsoft_oauth": False,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T11:45:00Z",
                "last_login_at": "2024-01-15T11:30:00Z",
                "last_activity_at": "2024-01-15T11:45:00Z",
                "email_verified_at": "2024-01-15T10:35:00Z"
            }
        }


class ProfileUpdateResponse(BaseModel):
    """Response model for profile update operations."""
    
    message: str = Field(..., description="Update confirmation message")
    updated_at: str = Field(..., description="Update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "message": "Profile updated successfully",
                "updated_at": "2024-01-15T11:45:00Z"
            }
        }


class PasswordChangeResponse(BaseModel):
    """Response model for password change."""
    
    message: str = Field(..., description="Password change confirmation message")
    changed_at: str = Field(..., description="Password change timestamp")

    class Config:
        schema_extra = {
            "example": {
                "message": "Password changed successfully",
                "changed_at": "2024-01-15T11:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

    class Config:
        schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Invalid input data",
                "details": "Full name cannot be empty"
            }
        }