"""
Common request models for Oprina API.

This module defines shared Pydantic models used across different API domains.
"""

from pydantic import BaseModel, Field
from typing import Optional


class PaginationRequest(BaseModel):
    """Request model for pagination parameters."""
    limit: int = Field(default=20, description="Number of items to return", ge=1, le=100)
    offset: int = Field(default=0, description="Number of items to skip", ge=0)

    class Config:
        schema_extra = {
            "example": {
                "limit": 20,
                "offset": 0
            }
        }


class FilterRequest(BaseModel):
    """Request model for basic filtering."""
    search: Optional[str] = Field(default=None, description="Search term", max_length=100)
    active_only: bool = Field(default=True, description="Only return active items")

    class Config:
        schema_extra = {
            "example": {
                "search": "example",
                "active_only": True
            }
        }
