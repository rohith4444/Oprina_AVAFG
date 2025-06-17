"""
User request models for user management endpoints.
Based on your actual UI form fields.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
import re


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile - matches your UI exactly."""
    
    # Core profile fields from your UI
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    preferred_name: Optional[str] = Field(None, max_length=255, description="User's preferred name")
    work_type: Optional[str] = Field(None, max_length=100, description="What best describes your work?")
    ai_preferences: Optional[str] = Field(None, max_length=1000, description="What personal preferences should Oprina consider?")
    
    # Optional system fields (not in UI but available)
    avatar_url: Optional[str] = Field(None, description="User's avatar URL")
    timezone: Optional[str] = Field(None, max_length=50, description="User's timezone")
    language: Optional[str] = Field(None, max_length=10, description="User's preferred language")

    @validator('full_name')
    def validate_full_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Full name cannot be empty')
        return v.strip() if v else v

    @validator('preferred_name')
    def validate_preferred_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None  # Allow empty preferred name
        return v.strip() if v else v

    @validator('work_type')
    def validate_work_type(cls, v):
        if v is not None:
            # Common work types for validation
            valid_work_types = [
                'Software Developer', 'Product Manager', 'Designer', 'Data Scientist',
                'Marketing Manager', 'Sales Representative', 'Consultant', 'Engineer',
                'Teacher', 'Student', 'Researcher', 'Other'
            ]
            if v not in valid_work_types:
                # Still allow custom work types
                pass
        return v

    @validator('ai_preferences')
    def validate_ai_preferences(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None  # Allow empty AI preferences
        return v.strip() if v else v

    @validator('avatar_url')
    def validate_avatar_url(cls, v):
        if v is not None and v.strip():
            # Basic URL validation
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v.strip()):
                raise ValueError('Invalid URL format')
        return v.strip() if v else v

    @validator('timezone')
    def validate_timezone(cls, v):
        if v is not None:
            # Basic timezone validation
            common_timezones = [
                'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 
                'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 
                'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney'
            ]
            if v not in common_timezones and not v.startswith(('America/', 'Europe/', 'Asia/', 'Africa/', 'Australia/')):
                raise ValueError('Invalid timezone format')
        return v

    @validator('language')
    def validate_language(cls, v):
        if v is not None:
            # Basic language code validation
            if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', v):
                raise ValueError('Language must be in format "en" or "en-US"')
        return v

    class Config:
        schema_extra = {
            "example": {
                "full_name": "John Smith",
                "preferred_name": "Johnny",
                "work_type": "Software Developer", 
                "ai_preferences": "I prefer detailed explanations and focus on code examples",
                "avatar_url": "https://example.com/avatar.jpg",
                "timezone": "America/New_York",
                "language": "en"
            }
        }


class ChangePasswordRequest(BaseModel):
    """Request model for changing user password."""
    
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_new_password: str = Field(..., min_length=8, description="Confirm new password")

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, one lowercase, one digit
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        
        return v

    @validator('confirm_new_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "NewPassword123",
                "confirm_new_password": "NewPassword123"
            }
        }