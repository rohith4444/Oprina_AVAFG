"""
Admin response models for Oprina API.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class TokenRefreshResponse(BaseModel):
    """Response model for token refresh operation."""
    message: str = Field(..., description="Operation result message")
    tokens_refreshed: int = Field(..., description="Number of tokens refreshed")
    results: Dict[str, int] = Field(..., description="Refresh results by provider")


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    overall_healthy: bool = Field(..., description="Overall system health")
    timestamp: str = Field(..., description="Status check timestamp")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component status details")


class AdminStatsResponse(BaseModel):
    """Response model for admin statistics."""
    total_users: int = Field(..., description="Total number of users")
    active_sessions: int = Field(..., description="Currently active sessions")
    total_tokens: int = Field(..., description="Total OAuth tokens")
    system_uptime: float = Field(..., description="System uptime in seconds")
