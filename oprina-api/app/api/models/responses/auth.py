"""
Authentication response models for Oprina API.

This module defines Pydantic models for authentication-related API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class UserResponse(BaseModel):
    """Response model for user information with UI fields."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    
    # Profile fields
    full_name: Optional[str] = Field(None, description="User's full name")
    preferred_name: Optional[str] = Field(None, description="User's preferred name")
    display_name: Optional[str] = Field(None, description="User display name (legacy)")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    
    # UI specific fields
    work_type: Optional[str] = Field(None, description="User's work type")
    ai_preferences: Optional[str] = Field(None, description="User's AI preferences")
    
    # System fields
    preferences: Optional[Dict[str, Any]] = Field(None, description="Additional user preferences")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(None, description="User language")
    
    # Status fields
    is_active: Optional[bool] = Field(None, description="Whether user account is active")
    is_verified: Optional[bool] = Field(None, description="Whether user email is verified")
    
    # Timestamps
    created_at: Optional[str] = Field(None, description="Account creation timestamp")
    last_login_at: Optional[str] = Field(None, description="Last login timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "user-123",
                "email": "user@example.com",
                "full_name": "John Doe",
                "preferred_name": "Johnny",
                "work_type": "Software Developer",
                "ai_preferences": "Please provide detailed explanations",
                "avatar_url": "https://example.com/avatar.jpg",
                "timezone": "America/New_York",
                "language": "en",
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-15T10:30:00Z"
            }
        }


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(..., description="Token type")
    user: UserResponse = Field(..., description="User information")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "user-123",
                    "email": "user@example.com",
                    "display_name": "John Doe"
                }
            }
        }


class TokenValidationResponse(BaseModel):
    """Response model for token validation."""
    valid: bool = Field(..., description="Whether the token is valid")
    user_id: Optional[str] = Field(None, description="User ID if token is valid")
    email: Optional[str] = Field(None, description="User email if token is valid")
    expires_at: Optional[str] = Field(None, description="Token expiration timestamp")

    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "user_id": "user-123",
                "email": "user@example.com",
                "expires_at": "2024-01-15T12:00:00Z"
            }
        }


class LogoutResponse(BaseModel):
    """Response model for user logout."""
    message: str = Field(..., description="Logout confirmation message")
    user_id: str = Field(..., description="User ID that was logged out")
    logged_out_at: str = Field(..., description="Logout timestamp")

    class Config:
        schema_extra = {
            "example": {
                "message": "Successfully logged out",
                "user_id": "user-123",
                "logged_out_at": "2024-01-15T11:45:00Z"
            }
        }