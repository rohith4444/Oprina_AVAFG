"""
OAuth request models for Oprina API.

This module defines Pydantic models for OAuth-related API requests.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator

from app.utils.validation import validate_email


class OAuthInitiateRequest(BaseModel):
    """Request model for initiating OAuth authorization flow."""
    
    provider: str = Field(
        ...,
        description="OAuth provider name (e.g., 'google', 'microsoft')",
        min_length=1,
        max_length=50
    )
    
    service_type: str = Field(
        default="default",
        description="Type of service being authorized",
        min_length=1,
        max_length=100
    )
    
    additional_scopes: Optional[List[str]] = Field(
        default=None,
        description="Additional OAuth scopes to request"
    )
    
    @validator('provider')
    def validate_provider(cls, v):
        """Validate provider name format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Provider name must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()
    
    @validator('service_type')
    def validate_service_type(cls, v):
        """Validate service type format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Service type must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()
    
    @validator('additional_scopes')
    def validate_additional_scopes(cls, v):
        """Validate additional scopes format."""
        if v is not None:
            for scope in v:
                if not isinstance(scope, str) or len(scope.strip()) == 0:
                    raise ValueError("All scopes must be non-empty strings")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "google",
                "service_type": "gmail",
                "additional_scopes": ["https://www.googleapis.com/auth/gmail.modify"]
            }
        }


class TokenRefreshRequest(BaseModel):
    """Request model for refreshing a service token."""
    
    force_refresh: bool = Field(
        default=False,
        description="Force refresh even if token is not expired"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "force_refresh": false
            }
        }


class TokenRevokeRequest(BaseModel):
    """Request model for revoking a service token."""
    
    revoke_with_provider: bool = Field(
        default=True,
        description="Also revoke token with the OAuth provider"
    )
    
    reason: Optional[str] = Field(
        default=None,
        description="Reason for token revocation",
        max_length=500
    )
    
    class Config:
        schema_extra = {
            "example": {
                "revoke_with_provider": True,
                "reason": "User requested token revocation"
            }
        }


class BulkTokenRevokeRequest(BaseModel):
    """Request model for revoking multiple tokens."""
    
    token_ids: List[str] = Field(
        ...,
        description="List of token IDs to revoke",
        min_items=1,
        max_items=50
    )
    
    revoke_with_provider: bool = Field(
        default=True,
        description="Also revoke tokens with their OAuth providers"
    )
    
    reason: Optional[str] = Field(
        default=None,
        description="Reason for bulk token revocation",
        max_length=500
    )
    
    @validator('token_ids')
    def validate_token_ids(cls, v):
        """Validate token IDs format."""
        unique_ids = set()
        for token_id in v:
            if not isinstance(token_id, str) or len(token_id.strip()) == 0:
                raise ValueError("All token IDs must be non-empty strings")
            if token_id in unique_ids:
                raise ValueError("Duplicate token IDs are not allowed")
            unique_ids.add(token_id)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token_ids": ["token-123", "token-456"],
                "revoke_with_provider": True,
                "reason": "Security cleanup"
            }
        }


class APIKeyGenerateRequest(BaseModel):
    """Request model for generating API keys."""
    
    key_name: str = Field(
        ...,
        description="Human-readable name for the API key",
        min_length=1,
        max_length=100
    )
    
    permissions: Optional[List[str]] = Field(
        default=None,
        description="List of permissions/scopes for the API key"
    )
    
    expires_in_days: Optional[int] = Field(
        default=None,
        description="Expiry time in days (None for no expiry)",
        ge=1,
        le=365
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Description of the API key purpose",
        max_length=500
    )
    
    @validator('key_name')
    def validate_key_name(cls, v):
        """Validate API key name."""
        if not v.strip():
            raise ValueError("API key name cannot be empty")
        return v.strip()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """Validate permissions format."""
        if v is not None:
            allowed_permissions = [
                "read", "write", "admin", "chat", "sessions", "avatar",
                "tokens", "users", "analytics"
            ]
            for permission in v:
                if permission not in allowed_permissions:
                    raise ValueError(f"Invalid permission: {permission}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "key_name": "Mobile App API Key",
                "permissions": ["read", "chat", "sessions"],
                "expires_in_days": 90,
                "description": "API key for mobile application access"
            }
        }


class TokenFilterRequest(BaseModel):
    """Request model for filtering tokens in list operations."""
    
    service_type: Optional[str] = Field(
        default=None,
        description="Filter by service type"
    )
    
    provider: Optional[str] = Field(
        default=None,
        description="Filter by OAuth provider"
    )
    
    active_only: bool = Field(
        default=True,
        description="Only return active tokens"
    )
    
    expires_within_days: Optional[int] = Field(
        default=None,
        description="Filter tokens expiring within specified days",
        ge=1,
        le=365
    )
    
    created_after: Optional[str] = Field(
        default=None,
        description="Filter tokens created after this date (ISO format)"
    )
    
    created_before: Optional[str] = Field(
        default=None,
        description="Filter tokens created before this date (ISO format)"
    )
    
    @validator('service_type', 'provider')
    def validate_filter_strings(cls, v):
        """Validate filter string format."""
        if v is not None and not v.strip():
            raise ValueError("Filter values cannot be empty strings")
        return v.lower() if v else None
    
    class Config:
        schema_extra = {
            "example": {
                "service_type": "gmail",
                "provider": "google",
                "active_only": True,
                "expires_within_days": 30
            }
        } 