"""
Health request models for Oprina API.
"""

from pydantic import BaseModel, Field


class DetailedHealthRequest(BaseModel):
    """Request model for detailed health check."""
    include_components: bool = Field(default=True, description="Include component health details")
    include_metrics: bool = Field(default=False, description="Include performance metrics")
