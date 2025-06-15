"""
Updated main.py - INCLUDES AUTH, USER, AND SESSIONS ENDPOINTS.

This version includes session management with Vertex AI integration.
"""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.utils.logging import get_logger  # UPDATED IMPORT

# Import all working endpoints
from app.api.endpoints import health
from app.api.endpoints import auth
from app.api.endpoints import user
from app.api.endpoints import sessions  # ADDED

# Initialize settings
settings = get_settings()

# Setup logging
logger = get_logger(__name__)  # UPDATED

# Create FastAPI app
app = FastAPI(
    title=settings.API_V1_STR if hasattr(settings, 'API_V1_STR') else "Oprina API",
    version="1.0.0",
    description="AI Agent API - Full Session Management",  # UPDATED
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with logging."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "path": str(request.url.path)
        }
    )

# Include routers
# 1. Health endpoints (basic testing)
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["health"]
)

# 2. Auth endpoints (registration, login, etc.)
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

# 3. User endpoints (profile management)
app.include_router(
    user.router,
    prefix="/api/v1",  # users.router already has /users prefix
    tags=["users"]
)

# 4. Session endpoints (session management)  # ADDED
app.include_router(
    sessions.router,
    prefix="/api/v1/sessions",
    tags=["sessions"]
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with available endpoints."""
    return {
        "name": "Oprina API",
        "version": "1.0.0",
        "status": "running - full session management",  # UPDATED
        "docs": "/docs",
        "redoc": "/redoc",
        "available_endpoints": {
            "health": [
                "GET /api/v1/health/ping",
                "GET /api/v1/health/",
                "GET /api/v1/health/detailed"
            ],
            "auth": [
                "POST /api/v1/auth/register",
                "POST /api/v1/auth/login", 
                "POST /api/v1/auth/logout",
                "GET /api/v1/auth/validate",
                "DELETE /api/v1/auth/deactivate"
            ],
            "users": [
                "GET /api/v1/users/me",
                "PUT /api/v1/users/me",
                "POST /api/v1/users/change-password"
            ],
            "sessions": [  # ADDED
                "POST /api/v1/sessions",
                "GET /api/v1/sessions",
                "GET /api/v1/sessions/{id}",
                "DELETE /api/v1/sessions/{id}",
                "GET /api/v1/sessions/{id}/messages",
                "POST /api/v1/sessions/{id}/end"
            ]
        }
    }

# Simple ping at root level
@app.get("/ping")
async def ping():
    """Simple ping."""
    return {"status": "ok", "timestamp": time.time()}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event to log available endpoints."""
    logger.info("🎯 Starting Oprina API with Session Management")  # UPDATED
    logger.info("Available endpoints:")
    logger.info("  📋 Health: GET /api/v1/health/")
    logger.info("  🔐 Auth: POST /api/v1/auth/register")
    logger.info("  🔐 Auth: POST /api/v1/auth/login")
    logger.info("  🔐 Auth: POST /api/v1/auth/logout")
    logger.info("  🔐 Auth: GET /api/v1/auth/validate")
    logger.info("  🔐 Auth: DELETE /api/v1/auth/deactivate")
    logger.info("  👤 Users: GET /api/v1/users/me")
    logger.info("  👤 Users: PUT /api/v1/users/me")
    logger.info("  👤 Users: POST /api/v1/users/change-password")
    logger.info("  💬 Sessions: POST /api/v1/sessions")  # ADDED
    logger.info("  💬 Sessions: GET /api/v1/sessions")   # ADDED
    logger.info("  💬 Sessions: GET /api/v1/sessions/{id}")  # ADDED
    logger.info("  💬 Sessions: DELETE /api/v1/sessions/{id}")  # ADDED
    logger.info("  💬 Sessions: GET /api/v1/sessions/{id}/messages")  # ADDED
    logger.info("  📖 Docs: /docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event."""
    logger.info("🛑 Shutting down Oprina API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)