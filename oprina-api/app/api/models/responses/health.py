"""
Health response models for Oprina API.

This module defines Pydantic models for health check API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    environment: Optional[str] = Field(None, description="Environment name")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
                "uptime": 86400.0,
                "environment": "production"
            }
        }


class DetailedHealthResponse(BaseModel):
    """Response model for detailed health check."""
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    environment: Optional[str] = Field(None, description="Environment name")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component health status")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
                "uptime": 86400.0,
                "environment": "production",
                "components": {
                    "database": {
                        "status": "healthy",
                        "response_time_ms": 5.2,
                        "last_check": "2024-01-15T10:29:55Z"
                    },
                    "voice_service": {
                        "status": "healthy",
                        "available": True,
                        "last_check": "2024-01-15T10:29:55Z"
                    },
                    "oauth_service": {
                        "status": "healthy",
                        "providers_available": 2,
                        "last_check": "2024-01-15T10:29:55Z"
                    }
                }
            }
        }


class ServiceStatusResponse(BaseModel):
    """Response model for individual service status."""
    service_name: str = Field(..., description="Name of the service")
    status: str = Field(..., description="Service status")
    last_check: str = Field(..., description="Last health check timestamp")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional service details")

    class Config:
        schema_extra = {
            "example": {
                "service_name": "database",
                "status": "healthy",
                "last_check": "2024-01-15T10:30:00Z",
                "response_time_ms": 5.2,
                "details": {
                    "connection_pool_size": 10,
                    "active_connections": 3
                }
            }
        }
