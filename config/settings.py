"""
Oprina Configuration Settings

This module handles all environment variables and configuration settings
for the Oprina voice-powered Gmail assistant.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # =============================================================================
    # Database & Storage Settings
    # =============================================================================
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anonymous key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Supabase service role key")
    SUPABASE_DATABASE_PASSWORD: str = Field(..., description="Supabase database password")
    
    # Redis Configuration - Upstash Support
    REDIS_PROVIDER: str = Field(
        default="upstash",
        description="Redis provider: 'local' for local Redis, 'upstash' for Upstash Redis"
    )

    # Local Redis (fallback/development)
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Local Redis connection URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Local Redis password if required"
    )

    # Upstash Redis Configuration
    UPSTASH_REDIS_REST_URL: str = Field(
        default=None,
        description="Upstash Redis REST API URL (e.g., https://your-db.upstash.io)"
    )
    UPSTASH_REDIS_REST_TOKEN: str = Field(
        default=None,
        description="Upstash Redis REST API token"
    )

    TEST_USER_EMAIL: str = Field(
    default="test@example.com",
    description="Test user email for development"
    )

    MOCK_GMAIL_API: bool = Field(
        default=False,
        description="Use mock Gmail API for testing"
    )

    # Optional: Upstash Redis connection string (alternative to REST)
    UPSTASH_REDIS_URL: Optional[str] = Field(
        default=None,
        description="Upstash Redis connection string (rediss://...)"
    )
    # =============================================================================
    # Google Cloud & AI Settings
    # =============================================================================
    
    # Google API Configuration
    GOOGLE_API_KEY: str = Field(..., description="Google API key for Gemini models")
    
    # # Gmail API Configuration
    # GMAIL_CLIENT_ID: str = Field(..., description="Gmail OAuth client ID")
    # GMAIL_CLIENT_SECRET: str = Field(..., description="Gmail OAuth client secret")
    # GMAIL_REDIRECT_URI: str = Field(
    #     default="http://localhost:3000/auth/gmail/callback",
    #     description="Gmail OAuth redirect URI"
    # )
    
    # =============================================================================
    # ADK & Agent Settings
    # =============================================================================
    
    # ADK Model Configuration
    ADK_MODEL: str = Field(
        default="gemini-2.5-flash-preview-05-20",
        description="Primary model for ADK agents"
    )
    
    # Alternative models for specific agents
    VOICE_MODEL: str = Field(
        default="gemini-2.5-flash-exp-native-audio-thinking-dialog",
        description="Model for voice agent"
    )
    COORDINATOR_MODEL: str = Field(
        default="gemini-2.5-flash-preview-05-20",
        description="Model for coordinator agent"
    )
    EMAIL_MODEL: str = Field(
        default="gemini-2.5-flash-preview-05-20",
        description="Model for email agent"
    )
    CONTENT_MODEL: str = Field(
        default="gemini-2.5-flash-preview-05-20",
        description="Model for content agent"
    )
    
    # =============================================================================
    # Application Settings
    # =============================================================================
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment (development/staging/production)"
    )
    
    # Debug Settings
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # API Settings
    API_HOST: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    API_PORT: int = Field(
        default=8000,
        description="API server port"
    )
    
    # Frontend Settings
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Frontend application URL"
    )
    
    # =============================================================================
    # Memory & Performance Settings
    # =============================================================================
    
    # Session Settings
    SESSION_TIMEOUT_HOURS: int = Field(
        default=24,
        description="Session timeout in hours"
    )
    
    # Cache Settings
    CACHE_TTL_SECONDS: int = Field(
        default=3600,
        description="Default cache TTL in seconds"
    )
    EMAIL_CACHE_TTL_SECONDS: int = Field(
        default=300,
        description="Email cache TTL in seconds (5 minutes)"
    )
    
    # Rate Limiting
    GMAIL_API_RATE_LIMIT: int = Field(
        default=100,
        description="Gmail API requests per minute limit"
    )
    
    # =============================================================================
    # Security Settings
    # =============================================================================
    
    # JWT Settings
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key-change-in-production",
        description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    JWT_EXPIRATION_HOURS: int = Field(
        default=24,
        description="JWT token expiration in hours"
    )
    
    # CORS Settings
    ALLOWED_ORIGINS: list = Field(
        default=["http://localhost:3000", "https://bolt.new"],
        description="Allowed CORS origins"
    )
    
    # =============================================================================
    # Feature Flags
    # =============================================================================
    
    # Feature toggles
    ENABLE_VOICE_PROCESSING: bool = Field(
        default=True,
        description="Enable voice input/output processing"
    )
    ENABLE_AVATAR_ANIMATION: bool = Field(
        default=True,
        description="Enable avatar lip-sync animation"
    )
    ENABLE_EMAIL_SENDING: bool = Field(
        default=False,
        description="Enable actual email sending (vs draft-only mode)"
    )
    ENABLE_REDIS_CACHING: bool = Field(
        default=True,
        description="Enable Redis caching"
    )
    
    # =============================================================================
    # Database Connection Strings
    # =============================================================================
    
    @property
    def supabase_database_url(self) -> str:
        """Generate Supabase database connection string for ADK DatabaseSessionService."""
        # ADK's DatabaseSessionService expects a PostgreSQL connection string
        # Extract the database details from Supabase URL
        import re
        
        # Parse Supabase URL to get connection details
        # Format: https://[project-id].supabase.co
        match = re.match(r'https://([^.]+)\.supabase\.co', self.SUPABASE_URL)
        if not match:
            raise ValueError("Invalid Supabase URL format")
            
        project_id = match.group(1)
        
        # Construct PostgreSQL connection string
        # Note: You'll need to use the service role key for database access
        return (
            f"postgresql://postgres:[YOUR-PASSWORD]@db.{project_id}.supabase.co:5432/postgres"
            "?sslmode=require"
        )
    
    @property
    def redis_connection_params(self) -> dict:
        """Get Redis connection parameters."""
        params = {
            "url": self.REDIS_URL,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True,
        }
        
        if self.REDIS_PASSWORD:
            params["password"] = self.REDIS_PASSWORD
            
        return params
    
    @property
    def redis_connection_params(self) -> dict:
        """Get Redis connection parameters based on provider."""
        if self.REDIS_PROVIDER == "upstash":
            # Upstash Redis configuration
            if self.UPSTASH_REDIS_URL:
                # Use direct connection string if available
                return {
                    "url": self.UPSTASH_REDIS_URL,
                    "decode_responses": True,
                    "socket_connect_timeout": 10,
                    "socket_timeout": 10,
                    "retry_on_timeout": True,
                    # Remove SSL parameters that cause conflicts
                }
            else:
                # Use REST API configuration
                return {
                    "provider": "upstash_rest",
                    "url": self.UPSTASH_REDIS_REST_URL,
                    "token": self.UPSTASH_REDIS_REST_TOKEN,
                    "decode_responses": True,
                }
        else:
            # Local Redis configuration
            params = {
                "url": self.REDIS_URL,
                "decode_responses": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "retry_on_timeout": True,
            }
            
            if self.REDIS_PASSWORD:
                params["password"] = self.REDIS_PASSWORD
                
            return params

    @property
    def is_upstash_redis(self) -> bool:
        """Check if using Upstash Redis."""
        return self.REDIS_PROVIDER == "upstash"

    @property
    def use_redis_rest_api(self) -> bool:
        """Check if should use Upstash REST API instead of Redis protocol."""
        return (
            self.is_upstash_redis and 
            self.UPSTASH_REDIS_REST_URL and 
            not self.UPSTASH_REDIS_URL
        )

    
    # =============================================================================
    # Validation & Configuration
    # =============================================================================
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"
        
        # Custom validation
        @staticmethod
        def parse_env_var(field_name: str, raw_val: str):
            if field_name == "ALLOWED_ORIGINS":
                return [origin.strip() for origin in raw_val.split(",")]
            return raw_val
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate configuration settings."""
        # Check required Google API key
        if not self.GOOGLE_API_KEY or self.GOOGLE_API_KEY == "your_api_key_here":
            raise ValueError("GOOGLE_API_KEY must be set to a valid Google API key")
        
        # Check Supabase configuration
        if not self.SUPABASE_URL or not self.SUPABASE_ANON_KEY:
            raise ValueError("Supabase configuration (URL and ANON_KEY) must be provided")
        
        # Validate Redis configuration
        if self.REDIS_PROVIDER == "upstash":
            if not self.UPSTASH_REDIS_REST_URL:
                raise ValueError("UPSTASH_REDIS_REST_URL must be set when using Upstash Redis")
            if not self.UPSTASH_REDIS_REST_TOKEN and not self.UPSTASH_REDIS_URL:
                raise ValueError("Either UPSTASH_REDIS_REST_TOKEN or UPSTASH_REDIS_URL must be set")
        elif self.REDIS_PROVIDER == "local":
            if not self.REDIS_URL:
                raise ValueError("REDIS_URL must be set when using local Redis")
        else:
            raise ValueError("REDIS_PROVIDER must be either 'upstash' or 'local'")
        
        # Validate environment
        if self.ENVIRONMENT not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be one of: development, staging, production")
        
        # Production-specific validations
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET_KEY == "your-super-secret-jwt-key-change-in-production":
                raise ValueError("JWT_SECRET_KEY must be changed for production")
            if self.DEBUG:
                print("WARNING: DEBUG is enabled in production environment")


# Global settings instance
settings = Settings()


# =============================================================================
# Helper Functions
# =============================================================================

def get_database_url() -> str:
    """Get the database URL for ADK DatabaseSessionService."""
    return settings.supabase_database_url


def get_redis_params() -> dict:
    """Get Redis connection parameters."""
    return settings.redis_connection_params


def is_development() -> bool:
    """Check if running in development mode."""
    return settings.ENVIRONMENT == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return settings.ENVIRONMENT == "production"

def get_redis_client():
    """Get Redis client based on configuration."""
    if settings.is_upstash_redis:
        if settings.use_redis_rest_api:
            # Use Upstash REST API client
            from upstash_redis import Redis
            return Redis(
                url=settings.UPSTASH_REDIS_REST_URL,
                token=settings.UPSTASH_REDIS_REST_TOKEN
            )
        else:
            # Use regular Redis client with Upstash connection string
            import redis
            # Remove SSL parameters that cause conflicts
            return redis.from_url(
                settings.UPSTASH_REDIS_URL,
                decode_responses=True
                # Remove ssl_cert_reqs=None - this causes the error
            )
    else:
        # Use local Redis
        import redis
        params = settings.redis_connection_params
        return redis.from_url(params["url"], **{k: v for k, v in params.items() if k != "url"})

def test_redis_connection() -> bool:
    """Test Redis connection."""
    try:
        client = get_redis_client()
        
        if settings.use_redis_rest_api:
            # Test Upstash REST API
            result = client.ping()
            return result == "PONG"
        else:
            # Test regular Redis
            return client.ping()
            
    except Exception as e:
        print(f"Redis connection test failed: {e}")
        return False


# =============================================================================
# Configuration Display (for debugging)
# =============================================================================

def print_configuration():
    """Print current configuration (excluding sensitive data)."""
    print("=== Oprina Configuration ===")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"ADK Model: {settings.ADK_MODEL}")
    print(f"API Server: {settings.API_HOST}:{settings.API_PORT}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print(f"Redis Provider: {settings.REDIS_PROVIDER}")
    if settings.is_upstash_redis:
        print(f"Upstash Redis: {settings.UPSTASH_REDIS_REST_URL[:30]}...")
        print(f"Using REST API: {settings.use_redis_rest_api}")
    else:
        print(f"Local Redis: {settings.REDIS_URL}") 
    print(f"Redis Connected: {test_redis_connection()}")
    print(f"Voice Processing: {settings.ENABLE_VOICE_PROCESSING}")
    print(f"Avatar Animation: {settings.ENABLE_AVATAR_ANIMATION}")
    print(f"Email Sending: {settings.ENABLE_EMAIL_SENDING}")
    print("============================")


if __name__ == "__main__":
    # Test configuration loading
    try:
        print_configuration()
        print("✅ Configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Configuration error: {e}")