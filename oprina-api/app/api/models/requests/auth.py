"""
Authentication request models for Oprina API.

This module defines Pydantic models for authentication-related API requests.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    email: EmailStr = Field(..., description="User email address")
    display_name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User preferences")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "display_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "preferences": {
                    "theme": "dark",
                    "notifications": True
                }
            }
        }


class UpdateUserRequest(BaseModel):
    """Request model for updating user information."""
    display_name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    settings: Optional[Dict[str, Any]] = Field(None, description="User settings")

    class Config:
        schema_extra = {
            "example": {
                "display_name": "Jane Doe",
                "avatar_url": "https://example.com/new-avatar.jpg",
                "preferences": {
                    "theme": "light",
                    "notifications": False
                },
                "settings": {
                    "language": "en",
                    "timezone": "UTC"
                }
            }
        }


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: Optional[str] = Field(None, description="User password (optional for OAuth)")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "secure_password"
            }
        }


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: EmailStr = Field(..., description="User email address")
    password: Optional[str] = Field(None, description="User password (optional for OAuth)")
    display_name: Optional[str] = Field(None, description="User display name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")

    class Config:
        schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "secure_password",
                "display_name": "New User"
            }
        }


class UpdatePreferencesRequest(BaseModel):
    """Request model for updating user preferences."""
    preferences: Dict[str, Any] = Field(..., description="User preferences to update")

    class Config:
        schema_extra = {
            "example": {
                "preferences": {
                    "theme": "dark",
                    "notifications": True,
                    "language": "en",
                    "timezone": "America/New_York"
                }
            }
        }


class ChangePasswordRequest(BaseModel):
    """Request model for changing user password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password", min_length=8)

    class Config:
        schema_extra = {
            "example": {
                "current_password": "old_password",
                "new_password": "new_secure_password"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""
    email: EmailStr = Field(..., description="User email address")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ConfirmResetPasswordRequest(BaseModel):
    """Request model for confirming password reset."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., description="New password", min_length=8)

    class Config:
        schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "new_secure_password"
            }
        }
