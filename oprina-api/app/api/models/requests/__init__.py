"""
Request models for Oprina API.

This module exports all implemented request models.
"""

# Auth models
from .auth import CreateUserRequest, UpdateUserRequest, LoginRequest, RegisterRequest
from .auth import UpdatePreferencesRequest, ChangePasswordRequest, ResetPasswordRequest, ConfirmResetPasswordRequest

# Chat models  
from .chat import CreateChatSessionRequest, SendMessageRequest, StreamMessageRequest
from .chat import ChatHistoryRequest, DeleteMessageRequest, UpdateSessionRequest, SessionFilterRequest

# Voice models
from .voice import VoiceMessageRequest, TranscriptionRequest, SynthesisRequest, VoiceSettingsRequest, VoiceStreamRequest

# OAuth models
from .oauth import OAuthInitiateRequest, TokenRefreshRequest, TokenRevokeRequest
from .oauth import BulkTokenRevokeRequest, APIKeyGenerateRequest, TokenFilterRequest

# Common models
from .common import PaginationRequest, FilterRequest

# Sessions models
from .sessions import SessionFilterRequest as SessionsFilterRequest, UpdateSessionRequest as SessionsUpdateRequest

# Admin models
from .admin import TokenRefreshRequest as AdminTokenRefreshRequest, SystemHealthRequest

# Health models
from .health import DetailedHealthRequest

__all__ = [
    # Auth
    "CreateUserRequest",
    "UpdateUserRequest", 
    "LoginRequest",
    "RegisterRequest",
    "UpdatePreferencesRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "ConfirmResetPasswordRequest",
    
    # Chat
    "CreateChatSessionRequest",
    "SendMessageRequest",
    "StreamMessageRequest",
    "ChatHistoryRequest",
    "DeleteMessageRequest",
    "UpdateSessionRequest",
    "SessionFilterRequest",
    
    # Voice
    "VoiceMessageRequest",
    "TranscriptionRequest",
    "SynthesisRequest",
    "VoiceSettingsRequest",
    "VoiceStreamRequest",
    
    # OAuth
    "OAuthInitiateRequest",
    "TokenRefreshRequest",
    "TokenRevokeRequest",
    "BulkTokenRevokeRequest",
    "APIKeyGenerateRequest",
    "TokenFilterRequest",
    
    # Common
    "PaginationRequest",
    "FilterRequest",
    
    # Sessions
    "SessionsFilterRequest",
    "SessionsUpdateRequest",
    
    # Admin
    "AdminTokenRefreshRequest",
    "SystemHealthRequest",
    
    # Health
    "DetailedHealthRequest"
]
