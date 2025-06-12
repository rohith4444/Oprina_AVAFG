"""
Utilities package for Oprina API.

This package contains common utilities used throughout the application:
- errors: Custom exception classes
- logging: Enhanced logging setup
- encryption: Token and data encryption utilities
- validation: Input validation helpers
- auth: Authentication utilities
"""

from .errors import (
    OprinaError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ExternalServiceError
)

from .logging import setup_logger, get_logger
from .encryption import encrypt_token, decrypt_token, hash_password, verify_password
from .validation import validate_email, validate_password, sanitize_input
from .auth import generate_token, verify_token, get_user_from_token

__all__ = [
    # Errors
    "OprinaError",
    "ValidationError", 
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseError",
    "ExternalServiceError",
    
    # Logging
    "setup_logger",
    "get_logger",
    
    # Encryption
    "encrypt_token",
    "decrypt_token", 
    "hash_password",
    "verify_password",
    
    # Validation
    "validate_email",
    "validate_password",
    "sanitize_input",
    
    # Auth
    "generate_token",
    "verify_token",
    "get_user_from_token"
]
