"""
Main FastAPI application for Oprina API.

This module sets up the FastAPI application with all routes, middleware,
and configuration for the Oprina AI agent API.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from app.config import get_settings
from app.api.endpoints import auth, chat, sessions, health, oauth, voice, admin
from app.utils.logging import get_logger, setup_logging
from app.utils.errors import (
    OprinaError, ValidationError, AuthenticationError, 
    TokenError, OAuthError, DatabaseError
)

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE if hasattr(settings, 'API_TITLE') else "Oprina API",
    version=settings.API_VERSION if hasattr(settings, 'API_VERSION') else "1.0.0",
    description=settings.API_DESCRIPTION if hasattr(settings, 'API_DESCRIPTION') else "AI Agent API with HeyGen Avatar Integration",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


# Request/Response middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time and request ID headers."""
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Start timer
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Add headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    # Log request
    logger.info(
        f"Request processed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "process_time": process_time,
            "user_agent": request.headers.get("User-Agent"),
            "ip": request.client.host if request.client else None
        }
    )
    
    return response


# Global exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.warning(f"Authentication error: {str(exc)}")
    return JSONResponse(
        status_code=401,
        content={
            "error": "Authentication Error",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(TokenError)
async def token_exception_handler(request: Request, exc: TokenError):
    """Handle token errors."""
    logger.warning(f"Token error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Token Error",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(OAuthError)
async def oauth_exception_handler(request: Request, exc: OAuthError):
    """Handle OAuth errors."""
    logger.warning(f"OAuth error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "OAuth Error",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database Error",
            "message": "An internal database error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(OprinaError)
async def oprina_exception_handler(request: Request, exc: OprinaError):
    """Handle general Oprina errors."""
    logger.error(f"Oprina error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Error",
            "message": str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Include API routers
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["health"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    oauth.router,
    prefix="/api/v1/oauth",
    tags=["oauth"]
)

app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["chat"]
)

app.include_router(
    sessions.router,
    prefix="/api/v1/sessions",
    tags=["sessions"]
)

app.include_router(
    voice.router,
    prefix="/api/v1/voice",
    tags=["voice"]
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["admin"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Oprina API",
        "version": "1.0.0",
        "description": "AI Agent API with HeyGen Avatar Integration",
        "status": "active",
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc",
        "openapi": "/api/v1/openapi.json"
    }


# Health check endpoint (simplified)
@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers."""
    return {"status": "ok", "timestamp": time.time()}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Oprina API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"API docs available at: /api/v1/docs")
    
    # Log configured OAuth providers
    oauth_providers = []
    if settings.GOOGLE_OAUTH_CLIENT_ID:
        oauth_providers.append("google")
    if settings.MICROSOFT_OAUTH_CLIENT_ID:
        oauth_providers.append("microsoft")
    
    if oauth_providers:
        logger.info(f"OAuth providers configured: {', '.join(oauth_providers)}")
    else:
        logger.warning("No OAuth providers configured")
    
    # Start background tasks
    try:
        from app.core.database.repositories.token_repository import TokenRepository
        from app.core.services.oauth_service import get_oauth_service
        from app.core.services.background_tasks import startup_background_tasks
        
        # Initialize services
        token_repo = TokenRepository()
        oauth_service = get_oauth_service(token_repo)
        
        # Start background tasks
        await startup_background_tasks(oauth_service)
        
    except Exception as e:
        logger.error(f"Failed to start background tasks: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Oprina API...")
    
    # Stop background tasks
    try:
        from app.core.services.background_tasks import shutdown_background_tasks
        await shutdown_background_tasks()
    except Exception as e:
        logger.error(f"Error stopping background tasks: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 