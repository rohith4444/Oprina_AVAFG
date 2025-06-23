"""
Configuration settings for Oprina API.
Simple approach with multiple env files.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


def get_env_file():
    """
    Determine which environment file to use.
    NOTE: This expects to be run from the backend/ directory.
    """
    
    is_production = any([
        os.getenv("GOOGLE_CLOUD_PROJECT"),
        os.getenv("K_SERVICE"), 
        os.getenv("GAE_ENV"),
        os.getenv("ENVIRONMENT") == "production"
    ])
    
    if is_production:
        return None
    else:
        # This will look for .env in current working directory
        # Make sure to run: cd backend && python -m app.main
        return ".env" if os.path.exists(".env") else None

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings (configurable for production)
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # ... (rest of your settings remain the same) ...
    
    # All your existing settings here
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_TITLE: str = "Oprina API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI Agent API with HeyGen Avatar Integration"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:3001"
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    
    # Vertex AI Agent settings
    VERTEX_AI_AGENT_ID: str = ""
    
    # Google Cloud settings
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    
    # HeyGen settings
    HEYGEN_API_KEY: str = ""
    HEYGEN_API_URL: str = "https://api.heygen.com"
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/callback"
    
    # OAuth Scopes
    GOOGLE_GMAIL_SCOPES: str = " ".join([
        "openid", "email", "profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.labels",
        "https://www.googleapis.com/auth/gmail.metadata",
    ])

    GOOGLE_CALENDAR_SCOPES: str = " ".join([
        "openid", "email", "profile", 
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.settings.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ])

    GOOGLE_AUTH_SCOPES: str = "openid email profile"
    
    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_API_URL: str = "http://localhost:8000"
    
    # Voice Services Configuration
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # Voice Service Settings
    VOICE_MAX_AUDIO_SIZE_MB: int = 10
    VOICE_MAX_TEXT_LENGTH: int = 5000
    VOICE_DEFAULT_LANGUAGE: str = "en-US"
    VOICE_DEFAULT_VOICE_NAME: str = "en-US-Neural2-F"
    VOICE_DEFAULT_SPEAKING_RATE: float = 1.0
    VOICE_DEFAULT_AUDIO_FORMAT: str = "mp3"
    
    # Security settings
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ADMIN_TOKEN: str = "dev-admin-token-change-in-production"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Background tasks
    ENABLE_BACKGROUND_TASKS: bool = True
    TOKEN_REFRESH_INTERVAL_MINUTES: int = 30
    CLEANUP_INTERVAL_HOURS: int = 6

    # ENCRYPTION_KEY: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Computed properties
    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def FRONTEND_SETTINGS_URL(self) -> str:
        return f"{self.FRONTEND_URL}/settings/connected-apps"

    @property  
    def FRONTEND_DASHBOARD_URL(self) -> str:
        return f"{self.FRONTEND_URL}/dashboard"
    
    @property
    def FRONTEND_LOGIN_URL(self) -> str:
        return f"{self.FRONTEND_URL}/login"
    
    @property
    def oauth_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)
    
    class Config:
        env_file = get_env_file()
        case_sensitive = True
        extra = "allow"


# Singleton pattern
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        # Optional: Print which config is being used
        env_file = get_env_file()
        if env_file:
            print(f"🔧 Loading config from: {env_file}")
        else:
            print(f"🔧 Loading config from: environment variables (production)")
    return _settings