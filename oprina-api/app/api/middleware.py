"""
API middleware for Oprina API.

This module provides middleware components for request/response processing,
authentication, and cross-origin resource sharing (CORS).
"""

from typing import Callable, List, Optional
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request information and adding request ID.
    
    This middleware:
    1. Generates a unique request ID for each request
    2. Adds the request ID to the request state
    3. Logs request information
    4. Measures request processing time
    5. Adds request ID and processing time to response headers
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add logging."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            # Log successful request
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
            
        except Exception as e:
            # Calculate processing time even if there's an error
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "error": str(e),
                    "process_time": process_time,
                    "user_agent": request.headers.get("User-Agent"),
                    "ip": request.client.host if request.client else None
                },
                exc_info=True
            )
            
            # Return error response with request ID
            error_response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id
                }
            )
            error_response.headers["X-Process-Time"] = str(process_time)
            error_response.headers["X-Request-ID"] = request_id
            
            return error_response


class APIKeyHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling API key authentication through headers.
    
    This middleware normalizes API key headers to ensure consistent processing:
    1. Accepts multiple header formats: X-API-Key, x-api-key, API-Key
    2. Normalizes to a standard header: X-API-Key
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and normalize API key headers."""
        # Check for API key in different header formats
        api_key = None
        
        for header in ["X-API-Key", "x-api-key", "API-Key", "api-key"]:
            if header in request.headers:
                api_key = request.headers[header]
                break
        
        # If API key found, normalize to X-API-Key
        if api_key:
            request.headers.__dict__["_list"].append(
                (b"X-API-Key", api_key.encode())
            )
        
        # Continue with request processing
        response = await call_next(request)
        return response


def setup_middlewares(app: FastAPI) -> None:
    """Set up all middlewares for the application."""
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time", "X-Request-ID"]
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # Add request logger middleware
    app.add_middleware(RequestLoggerMiddleware)
    
    # Add API key header middleware
    app.add_middleware(APIKeyHeaderMiddleware)
    
    logger.info("Middleware setup completed")
