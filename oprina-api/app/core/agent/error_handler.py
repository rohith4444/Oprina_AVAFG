"""
Error handler for agent-related errors and recovery mechanisms.
"""

from typing import Dict, Any, Optional
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class AgentErrorType(Enum):
    """Types of agent errors."""
    CONNECTION_ERROR = "connection_error"
    SESSION_NOT_FOUND = "session_not_found"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"
    INVALID_REQUEST = "invalid_request"
    AGENT_UNAVAILABLE = "agent_unavailable"
    UNKNOWN_ERROR = "unknown_error"


class AgentError(Exception):
    """Base exception for agent-related errors."""
    
    def __init__(
        self, 
        message: str, 
        error_type: AgentErrorType = AgentErrorType.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.recoverable = recoverable


class AgentConnectionError(AgentError):
    """Raised when agent connection fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, 
            AgentErrorType.CONNECTION_ERROR, 
            details, 
            recoverable=True
        )


class AgentSessionError(AgentError):
    """Raised when agent session operations fail."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, 
            AgentErrorType.SESSION_NOT_FOUND, 
            details, 
            recoverable=False
        )


class AgentTimeoutError(AgentError):
    """Raised when agent operations timeout."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, 
            AgentErrorType.TIMEOUT_ERROR, 
            details, 
            recoverable=True
        )


class AgentRateLimitError(AgentError):
    """Raised when agent rate limits are exceeded."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, 
            AgentErrorType.RATE_LIMIT_ERROR, 
            details, 
            recoverable=True
        )


class AgentErrorHandler:
    """Handles agent errors and provides recovery mechanisms."""
    
    def __init__(self):
        self.error_counts = {}
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    def classify_error(self, error: Exception) -> AgentErrorType:
        """Classify an error into a specific type."""
        error_message = str(error).lower()
        
        if "connection" in error_message or "network" in error_message:
            return AgentErrorType.CONNECTION_ERROR
        elif "session" in error_message and "not found" in error_message:
            return AgentErrorType.SESSION_NOT_FOUND
        elif "auth" in error_message or "credential" in error_message:
            return AgentErrorType.AUTHENTICATION_ERROR
        elif "rate limit" in error_message or "quota" in error_message:
            return AgentErrorType.RATE_LIMIT_ERROR
        elif "timeout" in error_message:
            return AgentErrorType.TIMEOUT_ERROR
        elif "invalid" in error_message or "bad request" in error_message:
            return AgentErrorType.INVALID_REQUEST
        elif "unavailable" in error_message or "service" in error_message:
            return AgentErrorType.AGENT_UNAVAILABLE
        else:
            return AgentErrorType.UNKNOWN_ERROR
    
    def handle_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle an agent error and return appropriate response."""
        error_type = self.classify_error(error)
        
        error_response = {
            "error_type": error_type.value,
            "message": str(error),
            "context": context,
            "recoverable": self._is_recoverable(error_type),
            "retry_suggested": self._should_retry(error_type, context),
            "user_message": self._get_user_message(error_type)
        }
        
        # Log the error
        logger.error(
            f"Agent error occurred",
            error_type=error_type.value,
            message=str(error),
            context=context
        )
        
        return error_response
    
    def _is_recoverable(self, error_type: AgentErrorType) -> bool:
        """Determine if an error type is recoverable."""
        recoverable_errors = {
            AgentErrorType.CONNECTION_ERROR,
            AgentErrorType.TIMEOUT_ERROR,
            AgentErrorType.RATE_LIMIT_ERROR,
            AgentErrorType.AGENT_UNAVAILABLE
        }
        return error_type in recoverable_errors
    
    def _should_retry(self, error_type: AgentErrorType, context: Dict[str, Any]) -> bool:
        """Determine if an operation should be retried."""
        if not self._is_recoverable(error_type):
            return False
        
        # Check retry count for this context
        context_key = f"{context.get('user_id', 'unknown')}:{context.get('session_id', 'unknown')}"
        retry_count = self.error_counts.get(context_key, 0)
        
        return retry_count < self.max_retries
    
    def _get_user_message(self, error_type: AgentErrorType) -> str:
        """Get user-friendly error message."""
        messages = {
            AgentErrorType.CONNECTION_ERROR: 
                "Unable to connect to the assistant. Please try again in a moment.",
            AgentErrorType.SESSION_NOT_FOUND: 
                "Your session has expired. Please start a new conversation.",
            AgentErrorType.AUTHENTICATION_ERROR: 
                "Authentication failed. Please sign in again.",
            AgentErrorType.RATE_LIMIT_ERROR: 
                "You've reached the usage limit. Please wait a moment before trying again.",
            AgentErrorType.TIMEOUT_ERROR: 
                "The request timed out. Please try again.",
            AgentErrorType.INVALID_REQUEST: 
                "Invalid request. Please check your input and try again.",
            AgentErrorType.AGENT_UNAVAILABLE: 
                "The assistant is temporarily unavailable. Please try again later.",
            AgentErrorType.UNKNOWN_ERROR: 
                "An unexpected error occurred. Please try again."
        }
        return messages.get(error_type, "An error occurred. Please try again.")
    
    def increment_error_count(self, context: Dict[str, Any]) -> int:
        """Increment error count for a context."""
        context_key = f"{context.get('user_id', 'unknown')}:{context.get('session_id', 'unknown')}"
        self.error_counts[context_key] = self.error_counts.get(context_key, 0) + 1
        return self.error_counts[context_key]
    
    def reset_error_count(self, context: Dict[str, Any]) -> None:
        """Reset error count for a context."""
        context_key = f"{context.get('user_id', 'unknown')}:{context.get('session_id', 'unknown')}"
        if context_key in self.error_counts:
            del self.error_counts[context_key]
    
    def get_recovery_suggestions(self, error_type: AgentErrorType) -> list[str]:
        """Get recovery suggestions for an error type."""
        suggestions = {
            AgentErrorType.CONNECTION_ERROR: [
                "Check your internet connection",
                "Try refreshing the page",
                "Wait a moment and try again"
            ],
            AgentErrorType.SESSION_NOT_FOUND: [
                "Start a new conversation",
                "Sign in again if necessary"
            ],
            AgentErrorType.AUTHENTICATION_ERROR: [
                "Sign out and sign in again",
                "Check your account permissions"
            ],
            AgentErrorType.RATE_LIMIT_ERROR: [
                "Wait before sending another message",
                "Reduce the frequency of requests"
            ],
            AgentErrorType.TIMEOUT_ERROR: [
                "Try again with a shorter message",
                "Check your internet connection"
            ],
            AgentErrorType.INVALID_REQUEST: [
                "Check your message format",
                "Try rephrasing your request"
            ],
            AgentErrorType.AGENT_UNAVAILABLE: [
                "Try again in a few minutes",
                "Check system status"
            ],
            AgentErrorType.UNKNOWN_ERROR: [
                "Try again",
                "Contact support if the problem persists"
            ]
        }
        return suggestions.get(error_type, ["Try again later"])


# Global error handler instance
agent_error_handler = AgentErrorHandler()
