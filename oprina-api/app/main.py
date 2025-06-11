"""
FastAPI application entry point for Oprina API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.router import api_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    print("🚀 Starting Oprina API...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Oprina API...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Oprina API",
        description="Multi-User Voice Assistant API with Avatar Integration",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api")
    
    @app.get("/")
    async def root():
        """Root endpoint for basic API info."""
        return {
            "message": "Oprina API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if settings.DEBUG else "disabled"
        }
    
    return app


# Create the FastAPI app instance
app = create_application() 