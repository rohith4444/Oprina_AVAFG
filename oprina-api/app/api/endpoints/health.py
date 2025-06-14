"""
Health check endpoints.
"""

import os
from fastapi import APIRouter, Depends
from datetime import datetime

from app.core.database.connection import get_database_client
from app.api.models.responses.health import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )


@router.get("/detailed", response_model=dict)
async def detailed_health_check():
    """Detailed health check with service dependencies."""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check database connection
    try:
        async with get_database_client() as db:
            # Simple query to test connection
            result = await db.table("users").select("count").execute()
            health_data["services"]["database"] = {
                "status": "healthy",
                "response_time_ms": None  # Could add timing
            }
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check environment configuration
    required_env_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "VERTEX_AI_PROJECT_ID",
        "VERTEX_AI_LOCATION"
    ]
    
    env_status = "healthy"
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            env_status = "unhealthy"
    
    health_data["services"]["environment"] = {
        "status": env_status,
        "missing_variables": missing_vars if missing_vars else None
    }
    
    if env_status == "unhealthy":
        health_data["status"] = "unhealthy"
    
    return health_data


@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    try:
        # Test critical dependencies
        async with get_database_client() as db:
            await db.table("users").select("count").execute()
        
        return {"status": "ready"}
        
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}


@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()} 