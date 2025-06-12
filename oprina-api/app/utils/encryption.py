"""
Token encryption and password utilities for Oprina API.

This module provides secure encryption and hashing functions for:
- Service token encryption/decryption
- Password hashing and verification
- Secure data storage
"""

import os
import base64
import secrets
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import jwt
from datetime import datetime, timedelta

from app.utils.errors import TokenError, ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class EncryptionManager:
    """Manages encryption operations for the application."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize encryption manager with key."""
        if encryption_key:
            self._key = encryption_key.encode()
        else:
            # Use environment variable or generate a key
            key_b64 = os.getenv('ENCRYPTION_KEY')
            if key_b64:
                self._key = base64.b64decode(key_b64)
            else:
                logger.warning("No encryption key provided, generating temporary key")
                self._key = Fernet.generate_key()
        
        self._fernet = Fernet(self._key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result."""
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise TokenError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded data and return original string."""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise TokenError(f"Failed to decrypt data: {str(e)}")
    
    @classmethod
    def generate_key(cls) -> str:
        """Generate a new encryption key for configuration."""
        key = Fernet.generate_key()
        return base64.b64encode(key).decode()


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create the global encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_token(token: str) -> str:
    """
    Encrypt a service token for secure storage.
    
    Args:
        token: The token to encrypt
        
    Returns:
        Encrypted token as base64 string
    """
    if not token:
        raise ValidationError("Token cannot be empty")
    
    manager = get_encryption_manager()
    return manager.encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a service token from storage.
    
    Args:
        encrypted_token: Base64 encoded encrypted token
        
    Returns:
        Decrypted token string
    """
    if not encrypted_token:
        raise ValidationError("Encrypted token cannot be empty")
    
    manager = get_encryption_manager()
    return manager.decrypt(encrypted_token)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    if not password:
        raise ValidationError("Password cannot be empty")
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing failed: {str(e)}")
        raise TokenError(f"Failed to hash password: {str(e)}")


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        hashed_password: Stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    if not password or not hashed_password:
        return False
    
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        return False


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        Base64 encoded secure token
    """
    random_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(random_bytes).decode()


def create_jwt_token(
    user_id: str,
    expiry_hours: int = 24,
    secret_key: Optional[str] = None
) -> str:
    """
    Create a JWT token for user authentication.
    
    Args:
        user_id: User identifier
        expiry_hours: Token expiry in hours
        secret_key: JWT secret key
        
    Returns:
        JWT token string
    """
    if not secret_key:
        secret_key = os.getenv('JWT_SECRET_KEY', 'development-secret-key')
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
        'iat': datetime.utcnow(),
        'type': 'access_token'
    }
    
    try:
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f"JWT token creation failed: {str(e)}")
        raise TokenError(f"Failed to create JWT token: {str(e)}")


def verify_jwt_token(
    token: str,
    secret_key: Optional[str] = None
) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        secret_key: JWT secret key
        
    Returns:
        Decoded token payload
        
    Raises:
        TokenError: If token is invalid or expired
    """
    if not secret_key:
        secret_key = os.getenv('JWT_SECRET_KEY', 'development-secret-key')
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenError(f"Invalid token: {str(e)}")


def encrypt_sensitive_data(data: str) -> str:
    """
    Encrypt sensitive data for database storage.
    
    Args:
        data: Sensitive data to encrypt
        
    Returns:
        Encrypted data as base64 string
    """
    return encrypt_token(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data from database storage.
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        
    Returns:
        Decrypted data string
    """
    return decrypt_token(encrypted_data)


def generate_api_key(prefix: str = "oprina") -> str:
    """
    Generate an API key with specific format.
    
    Args:
        prefix: Prefix for the API key
        
    Returns:
        Formatted API key
    """
    token = generate_secure_token(24)
    return f"{prefix}_{token}"


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging/display.
    
    Args:
        data: Sensitive data to mask
        visible_chars: Number of characters to show at the end
        
    Returns:
        Masked data string
    """
    if not data or len(data) <= visible_chars:
        return "*" * len(data) if data else ""
    
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]
