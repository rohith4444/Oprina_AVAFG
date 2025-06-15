"""
Health check endpoints  
"""

import os
import time
from datetime import datetime
from typing import Dict, Any 

from fastapi import APIRouter 
from pydantic import BaseModel

from app.core.database.connection import get_database_client
from app.config import get_settings

# Inline Pydantic models - no separate files needed
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class DetailedHealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    services: Dict[str, Any]

router = APIRouter()
settings = get_settings()

# Track startup time for uptime calculation
_startup_time = time.time()

@router.get("/ping")
async def ping():
    """Simple ping - no dependencies."""
    return {"status": "ok"}

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )

@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health with database and environment checks."""
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "uptime_seconds": time.time() - _startup_time,
        "services": {}
    }
    
    # Check environment variables using settings (not os.getenv)
    missing_vars = []
    if not settings.SUPABASE_URL:
        missing_vars.append("SUPABASE_URL")
    if not settings.SUPABASE_KEY:
        missing_vars.append("SUPABASE_KEY")
    
    if missing_vars:
        health_data["status"] = "unhealthy"
        health_data["services"]["environment"] = {
            "status": "unhealthy",
            "missing_variables": missing_vars
        }
        return DetailedHealthResponse(**health_data)
    
    health_data["services"]["environment"] = {"status": "healthy"}
    
    # Check database connection
    try:
        db_client = get_database_client()
        # Use a simple query that works on any Supabase database
        try:
            # Try to access users table
            result = db_client.table("users").select("id").limit(1).execute()
            health_data["services"]["database"] = {
                "status": "healthy",
                "connected": True,
                "test_query": "users table accessible"
            }
        except Exception as query_error:
            # If users table doesn't exist, that's still a successful connection
            if "relation" in str(query_error).lower() and "does not exist" in str(query_error).lower():
                health_data["services"]["database"] = {
                    "status": "healthy", 
                    "connected": True,
                    "test_query": "connection successful",
                    "note": "users table not created yet (run migrations)"
                }
            else:
                # Some other error
                raise query_error
        
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["services"]["database"] = {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    return DetailedHealthResponse(**health_data)