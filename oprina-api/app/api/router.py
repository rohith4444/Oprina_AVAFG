"""
Main API router that combines all endpoint routers.
Updated for session management (removed chat endpoints).
"""

from fastapi import APIRouter

from app.api.endpoints.sessions import router as sessions_router  # SESSIONS NOT CHAT
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.user import router as user_router
from app.api.endpoints.health import router as health_router

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
    # Note: user_router already has prefix="/users" defined in the router
    tags=["users"]
)

api_router.include_router(
    sessions_router,  # SESSIONS INSTEAD OF CHAT
    prefix="/sessions",
    tags=["sessions"]
)

# REMOVED chat_router - we deleted chat endpoints