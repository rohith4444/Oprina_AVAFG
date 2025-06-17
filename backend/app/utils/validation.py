"""
Input validation utilities for Oprina API.

This module provides validation functions for:
- Email addresses
- Passwords
- User input sanitization
- Data format validation
"""

import re
import html
from typing import Optional, List, Dict, Any, Union
from email_validator import validate_email as email_validate, EmailNotValidError
from urllib.parse import urlparse

from app.utils.errors import ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)


def validate_email(email: str) -> str:
    """
    Validate and normalize an email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email address
        
    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Email address is required")
    
    if not isinstance(email, str):
        raise ValidationError("Email must be a string")
    
    email = email.strip().lower()
    
    try:
        # Use email-validator library for comprehensive validation
        validated_email = email_validate(email)
        return validated_email.email
    except EmailNotValidError as e:
        logger.warning(f"Invalid email validation attempt: {email}")
        raise ValidationError(f"Invalid email address: {str(e)}")


def validate_password(password: str) -> bool:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        True if password is valid
        
    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if not password:
        raise ValidationError("Password is required")
    
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")
    
    # Check minimum length
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    # Check maximum length (prevent DoS)
    if len(password) > 128:
        raise ValidationError("Password must be less than 128 characters")
    
    # Check for at least one letter
    if not re.search(r'[a-zA-Z]', password):
        raise ValidationError("Password must contain at least one letter")
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one number")
    
    # Check for common weak passwords
    weak_passwords = {
        'password', '12345678', 'qwerty123', 'admin123',
        'password123', '123456789', 'letmein123'
    }
    
    if password.lower() in weak_passwords:
        raise ValidationError("Password is too common, please choose a stronger password")
    
    return True


def sanitize_input(
    data: str,
    max_length: Optional[int] = None,
    allow_html: bool = False,
    strip_whitespace: bool = True
) -> str:
    """
    Sanitize user input to prevent XSS and other attacks.
    
    Args:
        data: Input string to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
        strip_whitespace: Whether to strip leading/trailing whitespace
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If input is invalid
    """
    if data is None:
        return ""
    
    if not isinstance(data, str):
        data = str(data)
    
    # Strip whitespace if requested
    if strip_whitespace:
        data = data.strip()
    
    # Check length
    if max_length and len(data) > max_length:
        raise ValidationError(f"Input too long, maximum {max_length} characters allowed")
    
    # HTML escape if HTML not allowed
    if not allow_html:
        data = html.escape(data)
    
    # Remove null bytes and other control characters
    data = data.replace('\x00', '')
    data = re.sub(r'[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data)
    
    return data


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """
    Validate and normalize a URL.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes
        
    Returns:
        Normalized URL
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL is required")
    
    if not isinstance(url, str):
        raise ValidationError("URL must be a string")
    
    url = url.strip()
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {str(e)}")
    
    if not parsed.scheme:
        raise ValidationError("URL must include a scheme (http:// or https://)")
    
    if not parsed.netloc:
        raise ValidationError("URL must include a domain")
    
    # Check allowed schemes
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    if parsed.scheme.lower() not in allowed_schemes:
        raise ValidationError(f"URL scheme must be one of: {', '.join(allowed_schemes)}")
    
    return url


def validate_phone_number(phone: str) -> str:
    """
    Validate and normalize a phone number.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Normalized phone number
        
    Raises:
        ValidationError: If phone number is invalid
    """
    if not phone:
        raise ValidationError("Phone number is required")
    
    if not isinstance(phone, str):
        raise ValidationError("Phone number must be a string")
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone.strip())
    
    # Check if it starts with + (international format)
    if cleaned.startswith('+'):
        # International format: +1234567890 (minimum 10 digits after +)
        if len(cleaned) < 11:
            raise ValidationError("International phone number too short")
        if len(cleaned) > 16:
            raise ValidationError("International phone number too long")
    else:
        # Domestic format: assume 10 digits minimum
        if len(cleaned) < 10:
            raise ValidationError("Phone number too short")
        if len(cleaned) > 15:
            raise ValidationError("Phone number too long")
    
    return cleaned


def validate_json_data(
    data: Dict[str, Any],
    required_fields: Optional[List[str]] = None,
    allowed_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate JSON data structure.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        allowed_fields: List of allowed field names
        
    Returns:
        Validated data dictionary
        
    Raises:
        ValidationError: If data structure is invalid
    """
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")
    
    # Check required fields
    if required_fields:
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Check allowed fields
    if allowed_fields:
        extra_fields = []
        for field in data.keys():
            if field not in allowed_fields:
                extra_fields.append(field)
        
        if extra_fields:
            raise ValidationError(f"Unexpected fields: {', '.join(extra_fields)}")
    
    return data


def validate_pagination_params(
    page: Optional[int] = None,
    limit: Optional[int] = None,
    max_limit: int = 100
) -> tuple[int, int]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (1-based)
        limit: Items per page
        max_limit: Maximum allowed limit
        
    Returns:
        Tuple of (page, limit)
        
    Raises:
        ValidationError: If parameters are invalid
    """
    # Default values
    if page is None:
        page = 1
    if limit is None:
        limit = 20
    
    # Validate page
    if not isinstance(page, int) or page < 1:
        raise ValidationError("Page must be a positive integer")
    
    # Validate limit
    if not isinstance(limit, int) or limit < 1:
        raise ValidationError("Limit must be a positive integer")
    
    if limit > max_limit:
        raise ValidationError(f"Limit cannot exceed {max_limit}")
    
    return page, limit


def validate_uuid(uuid_string: str) -> str:
    """
    Validate UUID format.
    
    Args:
        uuid_string: UUID string to validate
        
    Returns:
        Normalized UUID string
        
    Raises:
        ValidationError: If UUID is invalid
    """
    if not uuid_string:
        raise ValidationError("UUID is required")
    
    if not isinstance(uuid_string, str):
        raise ValidationError("UUID must be a string")
    
    uuid_string = uuid_string.strip().lower()
    
    # UUID v4 pattern
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    )
    
    if not uuid_pattern.match(uuid_string):
        raise ValidationError("Invalid UUID format")
    
    return uuid_string


def validate_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_format: str = "%Y-%m-%d"
) -> tuple[Optional[str], Optional[str]]:
    """
    Validate date range parameters.
    
    Args:
        start_date: Start date string
        end_date: End date string
        date_format: Expected date format
        
    Returns:
        Tuple of (start_date, end_date)
        
    Raises:
        ValidationError: If dates are invalid
    """
    from datetime import datetime
    
    # Validate start_date
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, date_format)
        except ValueError:
            raise ValidationError(f"Invalid start_date format, expected {date_format}")
    
    # Validate end_date
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, date_format)
        except ValueError:
            raise ValidationError(f"Invalid end_date format, expected {date_format}")
    
    # Check date range logic
    if start_date and end_date:
        start_dt = datetime.strptime(start_date, date_format)
        end_dt = datetime.strptime(end_date, date_format)
        
        if start_dt > end_dt:
            raise ValidationError("start_date cannot be after end_date")
    
    return start_date, end_date
