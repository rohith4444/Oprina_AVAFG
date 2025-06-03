"""
Oprina Configuration Settings - ADK Memory Migration

This module handles all environment variables and configuration settings
for the Oprina voice-powered Gmail assistant with ADK-native memory services.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List
import os, glob, sys, re
import urllib.parse

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from services.logging.logger import setup_logger

# Configure logging for settings
# logger = setup_logger("settings", console_output=True)


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # =============================================================================
    # ADK Memory Service Configuration (NEW)
    # =============================================================================
    
    # Memory Service Type
    MEMORY_SERVICE_TYPE: str = Field(
        default="inmemory",
        description="Memory service type: 'inmemory' for development, 'vertexai_rag' for production"
    )
    
    # Session Service Type
    SESSION_SERVICE_TYPE: str = Field(
        default="inmemory",
        description="Session service type: 'inmemory' for development, 'database' for production"
    )
    
    # ADK Application Configuration
    ADK_APP_NAME: str = Field(
        default="oprina",
        description="ADK application name for session management"
    )
    
    # Vertex AI RAG Configuration (for production memory service)
    VERTEX_AI_PROJECT_ID: Optional[str] = Field(
        default=None,
        description="Google Cloud Project ID for Vertex AI RAG"
    )
    VERTEX_AI_LOCATION: str = Field(
        default="us-central1",
        description="Vertex AI location/region"
    )
    VERTEX_AI_RAG_CORPUS_ID: Optional[str] = Field(
        default=None,
        description="Vertex AI RAG Corpus ID for memory service"
    )
    
    # =============================================================================
    # Database & Storage Settings
    # =============================================================================
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anonymous key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., description="Supabase service role key")
    SUPABASE_DATABASE_PASSWORD: str = Field(..., description="Supabase database password")
    
    # Chat History Configuration (UI only - separate from ADK)
    CHAT_HISTORY_ENABLED: bool = Field(
        default=True,
        description="Enable chat history service for UI conversation lists"
    )
    
    # =============================================================================
    # Google Cloud & AI Settings
    # =============================================================================
    
    # Google API Configuration
    GOOGLE_API_KEY: str = Field(..., description="Google API key for Gemini models")

    # ADD THIS:
    GOOGLE_GENAI_USE_VERTEXAI: bool = Field(
        default=False,
        description="Force Google AI Studio instead of Vertex AI for Gemini models"
    )
    
    # ✅ NEW: Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT_ID: str = Field(..., description="Google Cloud Project ID")

    # ✅ NEW: Speech-to-Text Settings
    STT_LANGUAGE_CODE: str = Field(default="en-US", description="Speech recognition language")
    STT_MODEL: str = Field(default="latest_long", description="STT model type")
    STT_USE_ENHANCED: bool = Field(default=True, description="Use enhanced STT model")
    STT_ENABLE_AUTOMATIC_PUNCTUATION: bool = Field(default=True, description="Auto punctuation")
    STT_SAMPLE_RATE: int = Field(default=16000, description="Audio sample rate")

    # ✅ NEW: Text-to-Speech Settings
    TTS_LANGUAGE_CODE: str = Field(default="en-US", description="TTS language")
    TTS_VOICE_NAME: str = Field(default="en-US-Neural2-F", description="TTS voice name")
    TTS_VOICE_GENDER: str = Field(default="FEMALE", description="Voice gender")
    TTS_AUDIO_ENCODING: str = Field(default="MP3", description="Audio output format")
    TTS_SPEAKING_RATE: float = Field(default=1.0, description="Speech rate")
    TTS_PITCH: float = Field(default=0.0, description="Voice pitch")

    AUDIO_SAMPLE_RATE: int = Field(default=16000, description="Audio processing sample rate")
    AUDIO_CHANNELS: int = Field(default=1, description="Audio channels (1=mono, 2=stereo)")
    PROCESSING_TIMEOUT: int = Field(default=30, description="Audio processing timeout in seconds")
    # =============================================================================
    # Google API Settings
    # =============================================================================
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_SECRET_FILE: str = Field(
        default="credentials/client_secret_7774023189-5ga9j3epn8nja2aumfnmf09mh10osquh.apps.googleusercontent.com.json",
        description="Path to Google OAuth client secret file"
    )
    GOOGLE_TOKEN_FILE: str = Field(
        default="credentials/token.json",
        description="Path to Google OAuth token file"
    )
    
    # Google API Scopes
    GOOGLE_API_SCOPES: List[str] = Field(
        default=[
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email", 
            "openid"
        ],
        description="Google API OAuth scopes"
    )
    
    # Google API Features
    GOOGLE_GMAIL_ENABLED: bool = Field(
        default=True,
        description="Enable Gmail API integration"
    )
    GOOGLE_CALENDAR_ENABLED: bool = Field(
        default=False,  # We'll enable this when we add calendar
        description="Enable Calendar API integration"
    )
    
    # Testing Configuration
    TEST_USER_EMAIL: str = Field(
        default="test@example.com",
        description="Test user email for development"
    )
    MOCK_GMAIL_API: bool = Field(
        default=False,
        description="Use mock Gmail API for testing"
    )
    
    # =============================================================================
    # ADK & Agent Settings
    # =============================================================================
    
    # ADK Model Configuration
    ADK_MODEL: str = Field(
        default="gemini-2.0-flash",  # Changed to stable model
        description="Primary model for ADK agents"
    )

    # Alternative models for specific agents
    VOICE_MODEL: str = Field(
        default="gemini-2.0-flash",  # Changed to stable model
        description="Model for voice agent"
    )
    COORDINATOR_MODEL: str = Field(
        default="gemini-2.0-flash",  # Already correct
        description="Model for coordinator agent"
    )
    EMAIL_MODEL: str = Field(
        default="gemini-2.0-flash",  # Changed to stable model
        description="Model for email agent"
    )
    CONTENT_MODEL: str = Field(
        default="gemini-2.0-flash",  # Changed to stable model
        description="Model for content agent"
    )
    CALENDAR_MODEL: str = Field(
        default="gemini-2.0-flash",  # Changed to stable model
        description="Model for calendar agent"
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
    
    # MCP Server Settings
    MCP_HOST: str = Field(
        default="localhost",
        description="MCP server host"
    )
    MCP_PORT: int = Field(
        default=8001,
        description="MCP server port"
    )
    
    # Frontend Settings
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Frontend application URL"
    )
    
    # =============================================================================
    # ADK Session & Memory Settings (NEW)
    # =============================================================================
    
    # Session Settings
    SESSION_TIMEOUT_HOURS: int = Field(
        default=24,
        description="Session timeout in hours"
    )
    
    # ADK Session Configuration
    ADK_SESSION_TTL_SECONDS: int = Field(
        default=86400,  # 24 hours
        description="ADK session TTL in seconds"
    )
    
    # Memory Configuration
    MEMORY_RETENTION_DAYS: int = Field(
        default=30,
        description="Number of days to retain completed sessions in memory"
    )
    
    # Performance Settings
    SESSION_CLEANUP_INTERVAL_HOURS: int = Field(
        default=6,
        description="Interval for cleaning up expired sessions"
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
    
    # ADK Memory Features
    ENABLE_CROSS_SESSION_MEMORY: bool = Field(
        default=True,
        description="Enable cross-session memory retrieval via load_memory tool"
    )
    ENABLE_SESSION_PERSISTENCE: bool = Field(
        default=True,
        description="Enable session persistence across app restarts"
    )
    
    VOICE_ENABLED: bool = Field(default=True, description="Enable voice processing")
    VOICE_MAX_AUDIO_DURATION: int = Field(default=60, description="Max audio duration in seconds")

    AVATAR_ENABLED: bool = Field(default=True, description="Enable avatar animation")
    AVATAR_LIP_SYNC: bool = Field(default=True, description="Enable avatar lip-sync")

    SPEECH_TO_TEXT_ENABLED: bool = Field(default=True, description="Enable Google STT")
    TEXT_TO_SPEECH_ENABLED: bool = Field(default=True, description="Enable Google TTS")
    # =============================================================================
    # Helper Methods and Properties
    # =============================================================================
    
    @property
    def google_client_secret_path(self) -> str:
        """Get absolute path to Google client secret file with auto-discovery."""
        if os.path.isabs(self.GOOGLE_CLIENT_SECRET_FILE):
            if os.path.exists(self.GOOGLE_CLIENT_SECRET_FILE):
                return self.GOOGLE_CLIENT_SECRET_FILE
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        explicit_path = os.path.join(project_root, self.GOOGLE_CLIENT_SECRET_FILE)
        
        if os.path.exists(explicit_path):
            return explicit_path
        
        credentials_dir = os.path.join(project_root, "credentials")
        if os.path.exists(credentials_dir):
            pattern = os.path.join(credentials_dir, "client_secret*.json")
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
        
        return explicit_path
    
    @property
    def google_cloud_credentials_path(self) -> str:
        """Get Google Cloud service account key path"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "credentials", "google_cloud_service_account.json")
    
    @property  
    def google_token_path(self) -> str:
        """Get absolute path to Google token file."""
        if os.path.isabs(self.GOOGLE_TOKEN_FILE):
            return self.GOOGLE_TOKEN_FILE
            
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, self.GOOGLE_TOKEN_FILE)
    
    def validate_google_credentials(self) -> bool:
        """Validate that Google credentials file exists."""
        return os.path.exists(self.google_client_secret_path)
    
    # =============================================================================
    # ADK Database Connection Strings (NEW)
    # =============================================================================
    
    @property
    def adk_database_url(self) -> str:
        """Generate Supabase PostgreSQL connection string for ADK DatabaseSessionService."""
        try:
            # Parse Supabase URL to extract project ID
            # Format: https://[project-id].supabase.co
            match = re.match(r'https://([^.]+)\.supabase\.co', self.SUPABASE_URL)
            if not match:
                raise ValueError(f"Invalid Supabase URL format: {self.SUPABASE_URL}")
                
            project_id = match.group(1)
            
            # URL encode the password to handle special characters
            db_password = urllib.parse.quote_plus(self.SUPABASE_DATABASE_PASSWORD)
            
            # Construct PostgreSQL connection string for ADK
            # ADK DatabaseSessionService requires direct PostgreSQL access
            connection_string = (
                f"postgresql://postgres.{project_id}:{db_password}"
                f"@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
                "?sslmode=require"
            )
            
            # logger.debug(f"Generated ADK database URL for project: {project_id}")
            return connection_string
            
        except Exception as e:
            # logger.error(f"Failed to generate ADK database URL: {e}")
            raise ValueError(f"Could not generate database URL: {e}")
    
    @property
    def vertex_ai_rag_corpus_name(self) -> Optional[str]:
        """Generate full Vertex AI RAG corpus resource name."""
        if not self.VERTEX_AI_PROJECT_ID or not self.VERTEX_AI_RAG_CORPUS_ID:
            return None
            
        return (
            f"projects/{self.VERTEX_AI_PROJECT_ID}/"
            f"locations/{self.VERTEX_AI_LOCATION}/"
            f"ragCorpora/{self.VERTEX_AI_RAG_CORPUS_ID}"
        )
    
    # =============================================================================
    # ADK Service Factory Methods (NEW)
    # =============================================================================
    
    def get_session_service_config(self) -> dict:
        """Get configuration for ADK session service."""
        if self.SESSION_SERVICE_TYPE == "database":
            return {
                "type": "database",
                "db_url": self.adk_database_url,
                "app_name": self.ADK_APP_NAME,
                "ttl_seconds": self.ADK_SESSION_TTL_SECONDS
            }
        else:
            return {
                "type": "inmemory",
                "app_name": self.ADK_APP_NAME,
                "ttl_seconds": self.ADK_SESSION_TTL_SECONDS
            }
    
    def get_memory_service_config(self) -> dict:
        """Get configuration for ADK memory service."""
        if self.MEMORY_SERVICE_TYPE == "vertexai_rag":
            return {
                "type": "vertexai_rag",
                "rag_corpus": self.vertex_ai_rag_corpus_name,
                "project_id": self.VERTEX_AI_PROJECT_ID,
                "location": self.VERTEX_AI_LOCATION
            }
        else:
            return {
                "type": "inmemory",
                "retention_days": self.MEMORY_RETENTION_DAYS
            }
    
    # =============================================================================
    # Legacy Method Cleanup (Removed Redis-related methods)
    # =============================================================================
    # Note: All Redis-related configuration methods have been removed
    # as we're migrating to ADK-native memory services
    
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

        # Force Google AI Studio for LiteLLM
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = str(self.GOOGLE_GENAI_USE_VERTEXAI).lower()
        
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate configuration settings."""
        # logger.info("Validating Oprina configuration...")
        
        # Check required Google API key
        if not self.GOOGLE_API_KEY or self.GOOGLE_API_KEY == "your_api_key_here":
            raise ValueError("GOOGLE_API_KEY must be set to a valid Google API key")
        
        # Check Supabase configuration
        if not self.SUPABASE_URL or not self.SUPABASE_ANON_KEY:
            raise ValueError("Supabase configuration (URL and ANON_KEY) must be provided")
        
        # Validate ADK memory service configuration
        if self.MEMORY_SERVICE_TYPE not in ["inmemory", "vertexai_rag"]:
            raise ValueError("MEMORY_SERVICE_TYPE must be either 'inmemory' or 'vertexai_rag'")
        
        if self.SESSION_SERVICE_TYPE not in ["inmemory", "database"]:
            raise ValueError("SESSION_SERVICE_TYPE must be either 'inmemory' or 'database'")
        
        # Validate Vertex AI configuration if using RAG
        if self.MEMORY_SERVICE_TYPE == "vertexai_rag":
            if not self.VERTEX_AI_PROJECT_ID:
                raise ValueError("VERTEX_AI_PROJECT_ID must be set when using vertexai_rag memory service")
            if not self.VERTEX_AI_RAG_CORPUS_ID:
                # logger.warning("VERTEX_AI_RAG_CORPUS_ID not set - you'll need to create a RAG corpus")
                pass
        
        # Validate database configuration if using database sessions
        if self.SESSION_SERVICE_TYPE == "database":
            if not self.SUPABASE_DATABASE_PASSWORD:
                raise ValueError("SUPABASE_DATABASE_PASSWORD must be set when using database session service")
            try:
                # Test database URL generation
                db_url = self.adk_database_url
                # logger.debug("Database URL validation passed")
            except Exception as e:
                raise ValueError(f"Invalid database configuration: {e}")
        
        # Validate environment
        if self.ENVIRONMENT not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be one of: development, staging, production")
        
        # Production-specific validations
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET_KEY == "your-super-secret-jwt-key-change-in-production":
                raise ValueError("JWT_SECRET_KEY must be changed for production")
            if self.DEBUG:
                # logger.warning("DEBUG is enabled in production environment")
                pass
            if self.MEMORY_SERVICE_TYPE == "inmemory":
                # logger.warning("Using inmemory memory service in production - consider upgrading to vertexai_rag")
                pass
            if self.SESSION_SERVICE_TYPE == "inmemory":
                # logger.warning("Using inmemory session service in production - consider upgrading to database")
                pass
        
        # logger.info("Configuration validation completed successfully")


# Global settings instance
settings = Settings()


# =============================================================================
# Helper Functions
# =============================================================================

def get_adk_database_url() -> str:
    """Get the database URL for ADK DatabaseSessionService."""
    return settings.adk_database_url


def get_session_service_config() -> dict:
    """Get ADK session service configuration."""
    return settings.get_session_service_config()


def get_memory_service_config() -> dict:
    """Get ADK memory service configuration."""
    return settings.get_memory_service_config()


def is_development() -> bool:
    """Check if running in development mode."""
    return settings.ENVIRONMENT == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return settings.ENVIRONMENT == "production"


# =============================================================================
# ADK Service Validation Functions (NEW)
# =============================================================================

def validate_adk_database_connection() -> bool:
    """Validate ADK database connection (when using database sessions)."""
    if settings.SESSION_SERVICE_TYPE != "database":
        return True  # Not using database, so validation passes
    
    try:
        import asyncpg
        import asyncio
        
        async def test_connection():
            conn = await asyncpg.connect(settings.adk_database_url)
            await conn.close()
            return True
        
        return asyncio.run(test_connection())
    except Exception as e:
        # logger.error(f"ADK database connection test failed: {e}")
        return False


def validate_vertex_ai_rag_access() -> bool:
    """Validate Vertex AI RAG access (when using RAG memory service)."""
    if settings.MEMORY_SERVICE_TYPE != "vertexai_rag":
        return True  # Not using Vertex AI RAG, so validation passes
    
    try:
        from google.cloud import aiplatform
        
        # Initialize Vertex AI client
        aiplatform.init(
            project=settings.VERTEX_AI_PROJECT_ID,
            location=settings.VERTEX_AI_LOCATION
        )
        
        # Test basic access (this will fail if credentials are wrong)
        # Note: This is a basic test - actual RAG corpus validation would require more setup
        # logger.info("Vertex AI RAG configuration appears valid")
        return True
    except Exception as e:
        # logger.error(f"Vertex AI RAG validation failed: {e}")
        return False


# =============================================================================
# Configuration Display (for debugging)
# =============================================================================

def print_configuration():
    """Print current configuration (excluding sensitive data)."""
    # logger.info("=== Oprina ADK Configuration ===")
    logger.info("=== Oprina ADK Configuration ===")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"ADK App Name: {settings.ADK_APP_NAME}")
    logger.info(f"Session Service: {settings.SESSION_SERVICE_TYPE}")
    logger.info(f"Memory Service: {settings.MEMORY_SERVICE_TYPE}")
    logger.info(f"ADK Model: {settings.ADK_MODEL}")
    logger.info(f"API Server: {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Frontend URL: {settings.FRONTEND_URL}")
    
    # ADK-specific configuration
    logger.info(f"Cross-Session Memory: {settings.ENABLE_CROSS_SESSION_MEMORY}")
    logger.info(f"Session Persistence: {settings.ENABLE_SESSION_PERSISTENCE}")
    logger.info(f"Chat History (UI): {settings.CHAT_HISTORY_ENABLED}")
    
    # Service-specific info
    if settings.SESSION_SERVICE_TYPE == "database":
        logger.info(f"Database Sessions: Enabled via Supabase PostgreSQL")
    
    if settings.MEMORY_SERVICE_TYPE == "vertexai_rag":
        logger.info(f"Vertex AI RAG: {settings.VERTEX_AI_PROJECT_ID}/{settings.VERTEX_AI_LOCATION}")
    
    # Features
    logger.info(f"Voice Processing: {settings.ENABLE_VOICE_PROCESSING}")
    logger.info(f"Avatar Animation: {settings.ENABLE_AVATAR_ANIMATION}")
    logger.info(f"Email Sending: {settings.ENABLE_EMAIL_SENDING}")
    
    logger.info("============================")


def test_adk_configuration():
    """Test ADK-specific configuration."""
    # logger.info("Testing ADK Configuration...")
    logger.info("Testing ADK Configuration...")
    
    try:
        # Test session service configuration
        session_config = get_session_service_config()
        logger.info(f"✅ Session Service Config: {session_config['type']}")
        
        # Test memory service configuration  
        memory_config = get_memory_service_config()
        logger.info(f"✅ Memory Service Config: {memory_config['type']}")
        
        # Test database connection if using database sessions
        if settings.SESSION_SERVICE_TYPE == "database":
            db_valid = validate_adk_database_connection()
            logger.info(f"{'✅' if db_valid else '❌'} Database Connection: {db_valid}")
        
        # Test Vertex AI access if using RAG
        if settings.MEMORY_SERVICE_TYPE == "vertexai_rag":
            rag_valid = validate_vertex_ai_rag_access()
            logger.info(f"{'✅' if rag_valid else '❌'} Vertex AI RAG Access: {rag_valid}")
        
        logger.info("✅ ADK configuration test completed!")
        return True
        
    except Exception as e:
        # logger.error(f"❌ ADK configuration test failed: {e}")
        logger.error(f"❌ ADK configuration test failed: {e}")
        return False


if __name__ == "__main__":
    # Test configuration loading
    try:
        print_configuration()
        test_adk_configuration()
        logger.info("✅ Configuration loaded successfully!")
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")