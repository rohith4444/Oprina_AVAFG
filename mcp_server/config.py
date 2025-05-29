"""
Configuration module for the Oprina MCP server.

This module loads environment variables from the .env file and provides
configuration settings for the MCP server.
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

def get_config() -> Dict[str, Any]:
    """
    Get configuration settings from environment variables.
    
    Returns:
        Dict[str, Any]: Configuration settings
    """
    return {
        # Google API settings
        "google_api_key": os.environ.get("GOOGLE_API_KEY"),
        "gmail_redirect_uri": os.environ.get("GMAIL_REDIRECT_URI"),
        
        # Supabase settings
        "supabase_url": os.environ.get("SUPABASE_URL"),
        "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY"),
        "supabase_service_role_key": os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
        "supabase_database_password": os.environ.get("SUPABASE_DATABASE_PASSWORD"),
        
        # Redis settings
        "redis_provider": os.environ.get("REDIS_PROVIDER", "upstash"),
        "redis_url": os.environ.get("REDIS_URL", "redis://localhost:6379"),
        "redis_password": os.environ.get("REDIS_PASSWORD"),
        "upstash_redis_rest_url": os.environ.get("UPSTASH_REDIS_REST_URL"),
        "upstash_redis_rest_token": os.environ.get("UPSTASH_REDIS_REST_TOKEN"),
        "upstash_redis_url": os.environ.get("UPSTASH_REDIS_URL"),
        
        # Application settings
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "debug": os.environ.get("DEBUG", "true").lower() == "true",
        "log_level": os.environ.get("LOG_LEVEL", "INFO"),
        "api_host": os.environ.get("API_HOST", "0.0.0.0"),
        "api_port": int(os.environ.get("API_PORT", "8000")),
        "frontend_url": os.environ.get("FRONTEND_URL", "http://localhost:3000"),
        
        # Feature flags
        "enable_voice_processing": os.environ.get("ENABLE_VOICE_PROCESSING", "true").lower() == "true",
        "enable_avatar_animation": os.environ.get("ENABLE_AVATAR_ANIMATION", "true").lower() == "true",
        "enable_email_sending": os.environ.get("ENABLE_EMAIL_SENDING", "false").lower() == "true",
        "enable_redis_caching": os.environ.get("ENABLE_REDIS_CACHING", "true").lower() == "true",
        
        # Development settings
        "test_user_email": os.environ.get("TEST_USER_EMAIL", "test@example.com"),
        "mock_gmail_api": os.environ.get("MOCK_GMAIL_API", "false").lower() == "true",
    }

# Create a singleton config instance
config = get_config() 