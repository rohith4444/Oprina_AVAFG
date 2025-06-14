"""
OAuth response models for Oprina API.

This module defines Pydantic models for OAuth-related API responses.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class OAuthInitiateResponse(BaseModel):
    """Response model for OAuth authorization initiation."""
    
    authorization_url: str = Field(
        ...,
        description="URL to redirect user for OAuth authorization"
    )
    
    state: str = Field(
        ...,
        description="State parameter for OAuth flow validation"
    )
    
    provider: str = Field(
        ...,
        description="OAuth provider name"
    )
    
    service_type: str = Field(
        ...,
        description="Type of service being authorized"
    )
    
    expires_in: int = Field(
        ...,
        description="State expiry time in seconds"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
                "state": "abc123xyz789",
                "provider": "google",
                "service_type": "gmail",
                "expires_in": 600
            }
        }


class TokenResponse(BaseModel):
    """Response model for individual service token information."""
    
    id: str = Field(..., description="Token ID")
    service_type: str = Field(..., description="Type of service")
    provider: str = Field(..., description="OAuth provider")
    service_name: Optional[str] = Field(None, description="Human-readable service name")
    scope: Optional[str] = Field(None, description="OAuth scopes granted")
    is_active: bool = Field(..., description="Whether token is active")
    is_revoked: bool = Field(..., description="Whether token is revoked")
    expires_at: Optional[str] = Field(None, description="Token expiry time (ISO format)")
    created_at: str = Field(..., description="Token creation time (ISO format)")
    last_used_at: Optional[str] = Field(None, description="Last usage time (ISO format)")
    provider_email: Optional[str] = Field(None, description="Email from OAuth provider")
    token_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional token metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "token-123-456",
                "service_type": "gmail",
                "provider": "google",
                "service_name": "Google Gmail",
                "scope": "openid email profile gmail.readonly",
                "is_active": True,
                "is_revoked": False,
                "expires_at": "2024-02-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "last_used_at": "2024-01-15T12:00:00Z",
                "provider_email": "user@example.com",
                "token_metadata": {
                    "user_info": {
                        "name": "John Doe"
                    }
                }
            }
        }


class TokenListResponse(BaseModel):
    """Response model for list of service tokens."""
    
    tokens: List[Dict[str, Any]] = Field(
        ...,
        description="List of service tokens"
    )
    
    count: int = Field(
        ...,
        description="Total number of tokens returned"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "tokens": [
                    {
                        "id": "token-123",
                        "service_type": "gmail",
                        "provider": "google",
                        "is_active": True,
                        "expires_at": "2024-02-01T12:00:00Z"
                    }
                ],
                "count": 1
            }
        }


class TokenStatsResponse(BaseModel):
    """Response model for token statistics."""
    
    total_tokens: int = Field(..., description="Total number of tokens")
    active_tokens: int = Field(..., description="Number of active tokens")
    expiring_soon: int = Field(..., description="Number of tokens expiring soon")
    by_provider: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Token counts by provider"
    )
    by_service_type: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Token counts by service type"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "total_tokens": 5,
                "active_tokens": 3,
                "expiring_soon": 1,
                "by_provider": {
                    "google": {"total": 3, "active": 2},
                    "microsoft": {"total": 2, "active": 1}
                },
                "by_service_type": {
                    "gmail": {"total": 2, "active": 1},
                    "calendar": {"total": 3, "active": 2}
                }
            }
        }


class ProviderListResponse(BaseModel):
    """Response model for available OAuth providers."""
    
    providers: List[str] = Field(
        ...,
        description="List of available OAuth providers"
    )
    
    count: int = Field(
        ...,
        description="Number of available providers"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "providers": ["google", "microsoft"],
                "count": 2
            }
        }


class OAuthCallbackResponse(BaseModel):
    """Response model for OAuth callback completion."""
    
    message: str = Field(..., description="Success message")
    token_id: str = Field(..., description="Created token ID")
    provider: str = Field(..., description="OAuth provider")
    service_type: str = Field(..., description="Service type")
    expires_at: Optional[str] = Field(None, description="Token expiry time")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "OAuth authorization completed successfully",
                "token_id": "token-123-456",
                "provider": "google",
                "service_type": "gmail",
                "expires_at": "2024-02-01T12:00:00Z"
            }
        }


class TokenRefreshResponse(BaseModel):
    """Response model for token refresh operation."""
    
    message: str = Field(..., description="Success message")
    token: TokenResponse = Field(..., description="Updated token information")
    previous_expires_at: Optional[str] = Field(None, description="Previous expiry time")
    refresh_timestamp: str = Field(..., description="When refresh occurred")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Token refreshed successfully",
                "token": {
                    "id": "token-123-456",
                    "service_type": "gmail",
                    "provider": "google",
                    "expires_at": "2024-02-01T12:00:00Z"
                },
                "previous_expires_at": "2024-01-15T12:00:00Z",
                "refresh_timestamp": "2024-01-14T12:00:00Z"
            }
        }


class TokenRevokeResponse(BaseModel):
    """Response model for token revocation."""
    
    message: str = Field(..., description="Success message")
    token_id: str = Field(..., description="Revoked token ID")
    revoked_at: str = Field(..., description="When token was revoked")
    provider_revoked: bool = Field(..., description="Whether provider was notified")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Token revoked successfully",
                "token_id": "token-123-456",
                "revoked_at": "2024-01-14T12:00:00Z",
                "provider_revoked": True
            }
        }


class BulkTokenRevokeResponse(BaseModel):
    """Response model for bulk token revocation."""
    
    message: str = Field(..., description="Overall operation message")
    total_requested: int = Field(..., description="Total tokens requested for revocation")
    successfully_revoked: int = Field(..., description="Number of tokens successfully revoked")
    failed_revocations: int = Field(..., description="Number of failed revocations")
    results: List[Dict[str, Any]] = Field(
        ...,
        description="Detailed results for each token"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Bulk revocation completed",
                "total_requested": 3,
                "successfully_revoked": 2,
                "failed_revocations": 1,
                "results": [
                    {
                        "token_id": "token-123",
                        "success": True,
                        "message": "Token revoked successfully"
                    },
                    {
                        "token_id": "token-456",
                        "success": False,
                        "message": "Token not found"
                    }
                ]
            }
        }


class APIKeyResponse(BaseModel):
    """Response model for API key generation."""
    
    api_key: str = Field(..., description="Generated API key")
    token_id: str = Field(..., description="Associated token ID")
    key_name: str = Field(..., description="API key name")
    permissions: List[str] = Field(..., description="Granted permissions")
    expires_at: Optional[str] = Field(None, description="Key expiry time")
    created_at: str = Field(..., description="Key creation time")
    
    class Config:
        schema_extra = {
            "example": {
                "api_key": "oprina_abc123xyz789",
                "token_id": "token-123-456",
                "key_name": "Mobile App API Key",
                "permissions": ["read", "chat", "sessions"],
                "expires_at": "2024-04-01T12:00:00Z",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class TokenCleanupResponse(BaseModel):
    """Response model for token cleanup operations."""
    
    message: str = Field(..., description="Cleanup operation message")
    expired_cleaned: int = Field(..., description="Number of expired tokens cleaned")
    auto_refresh_results: Dict[str, int] = Field(
        ...,
        description="Results from automatic token refresh"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Token cleanup completed successfully",
                "expired_cleaned": 5,
                "auto_refresh_results": {
                    "total": 10,
                    "refreshed": 8,
                    "failed": 2,
                    "skipped": 0
                }
            }
        } 