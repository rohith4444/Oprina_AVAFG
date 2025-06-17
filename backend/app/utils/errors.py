"""
Custom exception classes for Oprina API.

This module defines all custom exceptions used throughout the application,
providing clear error types and helpful error messages.
"""

from typing import Optional, Dict, Any


class OprinaError(Exception):
    """Base exception class for all Oprina-specific errors."""
    
    def __init__(
        self,
        message: str = "An error occurred",
        error_code: str = "OPRINA_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(OprinaError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=error_details
        )


class AuthenticationError(OprinaError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationError(OprinaError):
    """Raised when authorization/permission checks fail."""
    
    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission
            
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=error_details
        )


class DatabaseError(OprinaError):
    """Raised when database operations fail."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=error_details
        )


class ExternalServiceError(OprinaError):
    """Raised when external service calls fail."""
    
    def __init__(
        self,
        message: str = "External service error",
        service: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if service:
            error_details["service"] = service
        if status_code:
            error_details["status_code"] = status_code
            
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=error_details
        )


class TokenError(AuthenticationError):
    """Raised when token operations fail."""
    
    def __init__(
        self,
        message: str = "Token error",
        token_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if token_type:
            error_details["token_type"] = token_type
            
        super().__init__(
            message=message,
            details=error_details
        )


class OAuthError(ExternalServiceError):
    """Raised when OAuth operations fail."""
    
    def __init__(
        self,
        message: str = "OAuth error",
        provider: Optional[str] = None,
        oauth_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if provider:
            error_details["provider"] = provider
        if oauth_error:
            error_details["oauth_error"] = oauth_error
            
        super().__init__(
            message=message,
            service=f"OAuth_{provider}" if provider else "OAuth",
            details=error_details
        )


class SessionError(OprinaError):
    """Raised when session operations fail."""
    
    def __init__(
        self,
        message: str = "Session error",
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if session_id:
            error_details["session_id"] = session_id
            
        super().__init__(
            message=message,
            error_code="SESSION_ERROR",
            details=error_details
        )


class AgentError(ExternalServiceError):
    """Raised when agent operations fail."""
    
    def __init__(
        self,
        message: str = "Agent communication error",
        agent_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if agent_type:
            error_details["agent_type"] = agent_type
            
        super().__init__(
            message=message,
            service=f"Agent_{agent_type}" if agent_type else "Agent",
            details=error_details
        )
