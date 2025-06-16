"""
Configuration settings for Oprina API.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # API settings
    API_TITLE: str = "Oprina API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI Agent API with HeyGen Avatar Integration"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Database settings (Supabase)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Vertex AI Agent settings
    VERTEX_AI_AGENT_ID: str = ""
    
    # HeyGen settings
    HEYGEN_API_KEY: str = ""
    HEYGEN_API_URL: str = "https://api.heygen.com"
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/callback"
    
    # OAuth Scopes
    GOOGLE_GMAIL_SCOPES: str = " ".join([
        "openid",
        "email", 
        "profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.labels",
        "https://www.googleapis.com/auth/gmail.metadata"
    ])

    GOOGLE_CALENDAR_SCOPES: str = " ".join([
        "openid",
        "email",
        "profile", 
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.settings.readonly"
    ])

    GOOGLE_AUTH_SCOPES: str = "openid email profile"
        
    # Frontend URLs (for redirects after OAuth)
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Voice Services Configuration
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # Voice Service Settings
    VOICE_MAX_AUDIO_SIZE_MB: int = 10
    VOICE_MAX_TEXT_LENGTH: int = 5000
    VOICE_DEFAULT_LANGUAGE: str = "en-US"
    VOICE_DEFAULT_VOICE_NAME: str = "en-US-Neural2-F"
    VOICE_DEFAULT_SPEAKING_RATE: float = 1.0
    VOICE_DEFAULT_AUDIO_FORMAT: str = "mp3"
    
    # JWT settings
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # Admin settings
    ADMIN_TOKEN: str = "admin-token-change-in-production"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Background tasks
    ENABLE_BACKGROUND_TASKS: bool = True
    TOKEN_REFRESH_INTERVAL_MINUTES: int = 30
    CLEANUP_INTERVAL_HOURS: int = 6

    BACKEND_API_URL: str = "http://localhost:8000"  # Your backend URL
    INTERNAL_API_KEY: str = "your-internal-api-key"  # Your internal API key
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Properties that depend on other settings
    @property
    def FRONTEND_SETTINGS_URL(self) -> str:
        return f"{self.FRONTEND_URL}/settings"
    
    @property
    def FRONTEND_DASHBOARD_URL(self) -> str:
        return f"{self.FRONTEND_URL}/dashboard"
    
    @property
    def FRONTEND_LOGIN_URL(self) -> str:
        return f"{self.FRONTEND_URL}/login"
    
    @property
    def oauth_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Simple singleton pattern
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get settings - simple implementation."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings