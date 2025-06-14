"""
Authentication response models for Oprina API.

This module defines Pydantic models for authentication-related API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class UserResponse(BaseModel):
    """Response model for user information."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    display_name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    created_at: Optional[str] = Field(None, description="Account creation timestamp")
    last_login_at: Optional[str] = Field(None, description="Last login timestamp")
    is_active: Optional[bool] = Field(None, description="Whether user account is active")
    is_verified: Optional[bool] = Field(None, description="Whether user email is verified")

    class Config:
        schema_extra = {
            "example": {
                "id": "user-123",
                "email": "user@example.com",
                "display_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "preferences": {
                    "theme": "dark",
                    "notifications": True
                },
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-15T10:30:00Z",
                "is_active": True,
                "is_verified": True
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


class LoginResponse(AuthResponse):
    """Response model for user login (extends AuthResponse)."""
    last_login_at: Optional[str] = Field(None, description="Previous login timestamp")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "last_login_at": "2024-01-14T08:15:00Z",
                "user": {
                    "id": "user-123",
                    "email": "user@example.com",
                    "display_name": "John Doe"
                }
            }
        }


class RegisterResponse(AuthResponse):
    """Response model for user registration (extends AuthResponse)."""
    is_new_user: bool = Field(..., description="Whether this is a newly created user")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "is_new_user": True,
                "user": {
                    "id": "user-456",
                    "email": "newuser@example.com",
                    "display_name": "New User"
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


class UserStatsResponse(BaseModel):
    """Response model for user statistics."""
    user_id: str = Field(..., description="User ID")
    total_sessions: int = Field(..., description="Total number of chat sessions")
    total_messages: int = Field(..., description="Total number of messages sent")
    account_age_days: int = Field(..., description="Account age in days")
    last_activity_at: Optional[str] = Field(None, description="Last activity timestamp")
    preferences_updated_at: Optional[str] = Field(None, description="Last preferences update")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user-123",
                "total_sessions": 25,
                "total_messages": 150,
                "account_age_days": 30,
                "last_activity_at": "2024-01-15T10:30:00Z",
                "preferences_updated_at": "2024-01-10T14:20:00Z"
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


class PasswordResetResponse(BaseModel):
    """Response model for password reset initiation."""
    message: str = Field(..., description="Password reset confirmation message")
    email: str = Field(..., description="Email address where reset link was sent")

    class Config:
        schema_extra = {
            "example": {
                "message": "Password reset link sent to your email",
                "email": "user@example.com"
            }
        }


class PreferencesUpdateResponse(BaseModel):
    """Response model for preferences update."""
    message: str = Field(..., description="Update confirmation message")
    preferences: Dict[str, Any] = Field(..., description="Updated preferences")
    updated_at: str = Field(..., description="Update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "message": "Preferences updated successfully",
                "preferences": {
                    "theme": "dark",
                    "notifications": True,
                    "language": "en"
                },
                "updated_at": "2024-01-15T11:45:00Z"
            }
        }
