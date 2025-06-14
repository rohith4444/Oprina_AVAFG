"""
Common response models for Oprina API.

This module defines shared Pydantic models used across different API domains.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict


class ErrorResponse(BaseModel):
    """Response model for API errors."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        schema_extra = {
            "example": {
                "error": "Resource not found",
                "error_code": "NOT_FOUND",
                "details": {"resource_id": "123"}
            }
        }


class SuccessResponse(BaseModel):
    """Response model for simple success operations."""
    message: str = Field(..., description="Success message")
    timestamp: str = Field(..., description="Operation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class PaginatedResponse(BaseModel):
    """Response model for paginated results."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Items skipped")
    has_more: bool = Field(..., description="Whether there are more items")

    class Config:
        schema_extra = {
            "example": {
                "items": [{"id": "1", "name": "Item 1"}],
                "total": 100,
                "limit": 20,
                "offset": 0,
                "has_more": True
            }
        }
