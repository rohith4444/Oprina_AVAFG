"""
Configuration settings for Oprina API.
"""

from typing import List
from pydantic import BaseSettings


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
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Database settings (Supabase)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # Vertex AI Agent settings
    VERTEX_AI_AGENT_ID: str = ""
    
    # HeyGen settings
    HEYGEN_API_KEY: str = ""
    HEYGEN_API_URL: str = "https://api.heygen.com"
    
    # OAuth settings
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""  # For Gmail/Calendar integration
    GOOGLE_CLIENT_SECRET: str = ""  # For Gmail/Calendar integration
    MICROSOFT_OAUTH_CLIENT_ID: str = ""
    MICROSOFT_OAUTH_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8000"
    BACKEND_URL: str = "http://localhost:8000"  # For OAuth integration files
    
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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings 