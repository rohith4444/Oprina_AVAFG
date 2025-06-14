"""
Response models for Oprina API.

This module exports all response models for easy importing.
"""

# Auth models
from .auth import UserResponse, AuthResponse, LoginResponse, RegisterResponse
from .auth import TokenValidationResponse, LogoutResponse, UserStatsResponse
from .auth import PasswordChangeResponse, PasswordResetResponse, PreferencesUpdateResponse

# Chat models
from .chat import ChatSessionResponse, MessageResponse, StreamEventResponse
from .chat import ChatHistoryResponse, SessionStatsResponse, SessionListResponse
from .chat import DeleteMessageResponse, EndSessionResponse

# Voice models
from .voice import VoiceMessageResponse, TranscriptionResponse, SynthesisResponse
from .voice import VoiceCapabilitiesResponse, VoiceSettingsValidationResponse
from .voice import VoiceErrorResponse, VoiceStreamResponse

# OAuth models
from .oauth import OAuthInitiateResponse, TokenResponse, TokenListResponse
from .oauth import TokenStatsResponse, ProviderListResponse, TokenRefreshResponse
from .oauth import TokenRevokeResponse, APIKeyResponse

# Health models
from .health import HealthResponse, DetailedHealthResponse, ServiceStatusResponse

# Common models
from .common import ErrorResponse, SuccessResponse, PaginatedResponse

# Sessions models
from .sessions import SessionDetailResponse, SessionListResponse as SessionsListResponse, SessionStatsResponse as SessionsStatsResponse

# Admin models
from .admin import TokenRefreshResponse, SystemStatusResponse, AdminStatsResponse

__all__ = [
    # Auth
    "UserResponse",
    "AuthResponse",
    "LoginResponse",
    "RegisterResponse",
    "TokenValidationResponse",
    "LogoutResponse",
    "UserStatsResponse",
    "PasswordChangeResponse",
    "PasswordResetResponse",
    "PreferencesUpdateResponse",
    
    # Chat
    "ChatSessionResponse",
    "MessageResponse",
    "StreamEventResponse",
    "ChatHistoryResponse",
    "SessionStatsResponse",
    "SessionListResponse",
    "DeleteMessageResponse",
    "EndSessionResponse",
    
    # Voice
    "VoiceMessageResponse",
    "TranscriptionResponse",
    "SynthesisResponse",
    "VoiceCapabilitiesResponse",
    "VoiceSettingsValidationResponse",
    "VoiceErrorResponse",
    "VoiceStreamResponse",
    
    # OAuth
    "OAuthInitiateResponse",
    "TokenResponse",
    "TokenListResponse",
    "TokenStatsResponse",
    "ProviderListResponse",
    "TokenRefreshResponse",
    "TokenRevokeResponse",
    "APIKeyResponse",
    
    # Health
    "HealthResponse",
    "DetailedHealthResponse",
    "ServiceStatusResponse",
    
    # Common
    "ErrorResponse",
    "SuccessResponse",
    "PaginatedResponse",
    
    # Sessions
    "SessionDetailResponse",
    "SessionsListResponse",
    "SessionsStatsResponse",
    
    # Admin
    "SystemStatusResponse",
    "AdminStatsResponse"
]
