"""
Google Cloud Services Package

Provides authentication and API access for Google Cloud services.
Now includes Speech-to-Text and Text-to-Speech services.
"""

# Existing exports
from .auth_utils import (
    GoogleAuthError,
    get_or_create_credentials,
    check_service_connection
)

from .gmail_auth import (
    get_gmail_service,
    check_gmail_connection
)

from .calendar_auth import (
    get_calendar_service, 
    check_calendar_connection
)

# NEW: Speech services exports
from .speech_services import (
    GoogleCloudSpeechServices,
    get_speech_services,
    speech_to_text,
    text_to_speech
)

__all__ = [
    # Existing auth services
    "GoogleAuthError",
    "get_or_create_credentials", 
    "check_service_connection",
    "get_gmail_service",
    "check_gmail_connection",
    "get_calendar_service",
    "check_calendar_connection",
    
    # NEW: Speech services
    "GoogleCloudSpeechServices",
    "get_speech_services",
    "speech_to_text", 
    "text_to_speech"
]