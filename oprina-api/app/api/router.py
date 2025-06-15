"""
Main API router that combines all endpoint routers.
Updated for session management and OAuth integration.
"""

from fastapi import APIRouter

from app.api.endpoints.sessions import router as sessions_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.user import router as user_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.oauth import router as oauth_router  # ADDED OAUTH

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(
    health_router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    user_router,
    prefix="/user", 
    tags=["user"]
  
)

api_router.include_router(
    sessions_router,
    prefix="/sessions",
    tags=["sessions"]
)

# ADDED: OAuth router for Google OAuth integration
api_router.include_router(
    oauth_router,
    prefix="/oauth",
    tags=["oauth"]
)