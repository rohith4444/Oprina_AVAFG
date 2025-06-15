"""
Main API router that combines all endpoint routers.
Updated to include auth and user endpoints.
"""

from fastapi import APIRouter

from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.sessions import router as sessions_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.user import router as users_router  # ADD THIS
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
    users_router,  # ADD THIS - Users endpoints
    # Note: users_router already has prefix="/users" defined in the router
    tags=["users"]
)

api_router.include_router(
    chat_router,
    prefix="/chat",
    tags=["chat"]
)

api_router.include_router(
    sessions_router,
    prefix="/sessions",
    tags=["sessions"]
)