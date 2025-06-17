"""
Authentication request models for Oprina API.

This module defines Pydantic models for authentication-related API requests.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
import re
from pydantic import validator


class RegisterRequest(BaseModel):
    """Request model for user registration with proper password and UI fields."""
    
    # Authentication fields
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    confirm_password: str = Field(..., min_length=8, description="Confirm password")
    
    # Profile fields (your UI requirements)
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    preferred_name: Optional[str] = Field(None, max_length=255, description="User's preferred name/nickname")
    
    # UI specific fields
    work_type: Optional[str] = Field(None, max_length=100, description="What best describes your work?")
    ai_preferences: Optional[str] = Field(None, max_length=1000, description="Personal preferences for AI responses")
    
    # Optional fields
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    timezone: Optional[str] = Field(default="UTC", description="User timezone")
    language: Optional[str] = Field(default="en", description="User language preference")

    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that passwords match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('full_name', 'preferred_name', 'work_type')
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
                "full_name": "John Doe",
                "preferred_name": "Johnny",
                "work_type": "Software Developer",
                "ai_preferences": "Please provide detailed explanations and focus on code examples",
                "timezone": "America/New_York",
                "language": "en"
            }
        }

class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }

 