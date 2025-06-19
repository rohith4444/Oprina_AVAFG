# app/main.py - Updated with Avatar Endpoints

"""
Updated main.py - INCLUDES AUTH, USER, SESSIONS, OAUTH, VOICE, AVATAR, AND BACKGROUND TOKEN REFRESH.

This version includes session management with Vertex AI integration, OAuth, 
voice services, avatar session tracking, and automatic background token refresh.
"""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.utils.logging import get_logger

# Import all working endpoints
from app.api.endpoints import health
from app.api.endpoints import auth
from app.api.endpoints import user
from app.api.endpoints import sessions
from app.api.endpoints import oauth
from app.api.endpoints import voice
from app.api.endpoints import avatar  # Added avatar endpoints
from app.api.endpoints import test_supabase

# Import background service
from app.core.services.background_tasks import (
    start_background_token_service,
    stop_background_token_service,
    get_background_token_service
)

# Initialize settings
settings = get_settings()

# Setup logging
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version="1.0.0",
    description="AI Agent API - Full Session Management with OAuth, Voice Services, Avatar Tracking & Background Token Refresh",
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
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(user.router, prefix="/api/v1/user", tags=["users"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["oauth"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(avatar.router, prefix="/api/v1/avatar", tags=["avatar"])  # Added avatar router
app.include_router(test_supabase.router, prefix="/api/v1/test", tags=["testing"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with available endpoints."""
    # Get background service stats
    bg_service = get_background_token_service()
    bg_stats = bg_service.get_stats()
    
    return {
        "name": "Oprina API",
        "version": "1.0.0",
        "status": "running - full session management with OAuth, Voice, Avatar Tracking & background refresh",
        "docs": "/docs",
        "redoc": "/redoc",
        "oauth_configured": settings.oauth_configured,
        "voice_configured": hasattr(settings, 'GOOGLE_CLOUD_PROJECT') and bool(getattr(settings, 'GOOGLE_CLOUD_PROJECT', None)),
        "background_service": {
            "enabled": bg_stats["enabled"],
            "running": bg_stats["is_running"],
            "total_refreshes": bg_stats["total_refreshes"],
            "last_run": bg_stats["last_run"]
        },
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
                "GET /api/v1/user/me",
                "PUT /api/v1/user/me",
                "POST /api/v1/user/change-password"
            ],
            "sessions": [
                "POST /api/v1/sessions",
                "GET /api/v1/sessions",
                "GET /api/v1/sessions/{id}",
                "DELETE /api/v1/sessions/{id}",
                "GET /api/v1/sessions/{id}/messages",
                "POST /api/v1/sessions/{id}/end"
            ],
            "oauth": [
                "GET /api/v1/oauth/connect/{service}",
                "POST /api/v1/oauth/disconnect",
                "GET /api/v1/oauth/status",
                "GET /api/v1/oauth/google/login",
                "GET /api/v1/oauth/google/signup",
                "GET /api/v1/oauth/callback",
                "GET /api/v1/oauth/config",
                "GET /api/v1/oauth/health",
                "GET /api/v1/oauth/background-status"
            ],
            "voice": [
                "POST /api/v1/voice/message",
                "POST /api/v1/voice/transcribe",
                "POST /api/v1/voice/synthesize"
            ],
            "avatar": [
                "GET /api/v1/avatar/quota",
                "POST /api/v1/avatar/check-quota",
                "POST /api/v1/avatar/sessions/start",
                "POST /api/v1/avatar/sessions/end",
                "POST /api/v1/avatar/sessions/status",
                "GET /api/v1/avatar/sessions",
                "POST /api/v1/avatar/admin/cleanup",
                "POST /api/v1/avatar/token",
                "GET /api/v1/avatar/health"
            ]
        }
    }

# Simple ping
@app.get("/ping")
async def ping():
    """Simple ping."""
    return {"status": "ok", "timestamp": time.time()}

# Background service status endpoint
@app.get("/api/v1/admin/background-status")
async def background_service_status():
    """Get background service status (for monitoring)."""
    bg_service = get_background_token_service()
    return bg_service.get_stats()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event to log available endpoints and start background service."""
    logger.info("🎯 Starting Oprina API with Session Management, OAuth, Voice Services, Avatar Tracking & Background Token Refresh")
    logger.info("Available endpoints:")
    logger.info("  📋 Health: GET /api/v1/health/")
    logger.info("  🔐 Auth: POST /api/v1/auth/register")
    logger.info("  🔐 Auth: POST /api/v1/auth/login")
    logger.info("  🔐 Auth: POST /api/v1/auth/logout")
    logger.info("  🔐 Auth: GET /api/v1/auth/validate")
    logger.info("  🔐 Auth: DELETE /api/v1/auth/deactivate")
    logger.info("  👤 Users: GET /api/v1/user/me")
    logger.info("  👤 Users: PUT /api/v1/user/me")
    logger.info("  👤 Users: POST /api/v1/user/change-password")
    logger.info("  💬 Sessions: POST /api/v1/sessions")
    logger.info("  💬 Sessions: GET /api/v1/sessions")
    logger.info("  💬 Sessions: GET /api/v1/sessions/{id}")
    logger.info("  💬 Sessions: DELETE /api/v1/sessions/{id}")
    logger.info("  💬 Sessions: GET /api/v1/sessions/{id}/messages")
    logger.info("  🔗 OAuth: GET /api/v1/oauth/connect/{service}")
    logger.info("  🔗 OAuth: GET /api/v1/oauth/google/login")
    logger.info("  🔗 OAuth: GET /api/v1/oauth/google/signup")
    logger.info("  🔗 OAuth: GET /api/v1/oauth/callback")
    logger.info("  🔗 OAuth: GET /api/v1/oauth/status")
    logger.info("  🔗 OAuth: GET /api/v1/oauth/background-status")
    logger.info("  🎤 Voice: POST /api/v1/voice/message")
    logger.info("  🎤 Voice: POST /api/v1/voice/transcribe")
    logger.info("  🎤 Voice: POST /api/v1/voice/synthesize")
    logger.info("  🤖 Avatar: GET /api/v1/avatar/quota")  # Added avatar endpoints
    logger.info("  🤖 Avatar: POST /api/v1/avatar/check-quota")
    logger.info("  🤖 Avatar: POST /api/v1/avatar/sessions/start")
    logger.info("  🤖 Avatar: POST /api/v1/avatar/sessions/end")
    logger.info("  🤖 Avatar: POST /api/v1/avatar/sessions/status")
    logger.info("  🤖 Avatar: GET /api/v1/avatar/sessions")
    logger.info("  🤖 Avatar: POST /api/v1/avatar/token")
    logger.info("  🤖 Avatar: GET /api/v1/avatar/health")
    
    # Log OAuth configuration status
    if settings.oauth_configured:
        logger.info("  ✅ OAuth is configured and ready")
    else:
        logger.warning("  ⚠️  OAuth not configured - check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
    
    # Log Voice service configuration status
    if hasattr(settings, 'GOOGLE_CLOUD_PROJECT') and getattr(settings, 'GOOGLE_CLOUD_PROJECT', None):
        logger.info("  ✅ Voice services are configured and ready")
    else:
        logger.warning("  ⚠️  Voice services not configured - check GOOGLE_CLOUD_PROJECT and credentials")
    
    # Log Avatar service status
    logger.info("  ✅ Avatar tracking service is ready")
    logger.info("     Features: 20-minute quota enforcement, session tracking")
    
    # Start background token refresh service
    try:
        if settings.ENABLE_BACKGROUND_TASKS:
            start_background_token_service()
            logger.info("  🔄 Background token refresh service started")
            logger.info(f"     Refresh interval: {settings.TOKEN_REFRESH_INTERVAL_MINUTES} minutes")
            logger.info(f"     Cleanup interval: {settings.CLEANUP_INTERVAL_HOURS} hours")
        else:
            logger.info("  ⏸️  Background token refresh is disabled")
    except Exception as e:
        logger.error(f"  ❌ Failed to start background service: {str(e)}")
    
    logger.info("  📖 Docs: /docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event - stop background service."""
    logger.info("🛑 Shutting down Oprina API")
    
    try:
        stop_background_token_service()
        logger.info("🔄 Background token refresh service stopped")
    except Exception as e:
        logger.error(f"Error stopping background service: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)