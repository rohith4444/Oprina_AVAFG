"""
Admin request models for Oprina API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TokenRefreshRequest(BaseModel):
    """Request model for manual token refresh."""
    force_refresh: bool = Field(default=False, description="Force refresh all tokens")


class SystemHealthRequest(BaseModel):
    """Request model for system health check."""
    detailed: bool = Field(default=False, description="Include detailed component status")
    include_metrics: bool = Field(default=False, description="Include performance metrics")
