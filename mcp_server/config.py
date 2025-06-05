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
        # MCP Server settings
        "mcp_server_host": os.environ.get("MCP_SERVER_HOST", "localhost"),
        "mcp_server_port": int(os.environ.get("MCP_SERVER_PORT", "8765")),
        "mcp_connection_type": os.environ.get("MCP_CONNECTION_TYPE", "stdio"),
        "mcp_server_url": os.environ.get("MCP_SERVER_URL"),
        "mcp_server_api_key": os.environ.get("MCP_SERVER_API_KEY"),
        
        # Google API settings
        "google_api_key": os.environ.get("GOOGLE_API_KEY"),
        "gmail_client_id": os.environ.get("GMAIL_CLIENT_ID"),
        "gmail_client_secret": os.environ.get("GMAIL_CLIENT_SECRET"),
        "gmail_redirect_uri": os.environ.get("GMAIL_REDIRECT_URI"),
        "google_client_secret_file": os.environ.get("GOOGLE_CLIENT_SECRET_FILE"),
        "google_token_file": os.environ.get("GOOGLE_TOKEN_FILE"),
        "google_gmail_enabled": os.environ.get("GOOGLE_GMAIL_ENABLED", "true").lower() == "true",
        "google_cloud_project_id": os.environ.get("GOOGLE_CLOUD_PROJECT_ID"),
        "google_cloud_location": os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        "google_application_credentials": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        
        # ADK settings
        "adk_app_name": os.environ.get("ADK_APP_NAME", "oprina"),
        "adk_model": os.environ.get("ADK_MODEL", "gemini-2.5-flash-preview-05-20"),
        "adk_temperature": float(os.environ.get("ADK_TEMPERATURE", "0.7")),
        "adk_max_tokens": int(os.environ.get("ADK_MAX_TOKENS", "1024")),
        "adk_session_ttl_seconds": int(os.environ.get("ADK_SESSION_TTL_SECONDS", "86400")),
        
        # Memory service settings
        "memory_service_type": os.environ.get("MEMORY_SERVICE_TYPE", "inmemory"),
        "memory_retention_days": int(os.environ.get("MEMORY_RETENTION_DAYS", "30")),
        
        # Session service settings
        "session_service_type": os.environ.get("SESSION_SERVICE_TYPE", "inmemory"),
        "session_cleanup_interval_hours": int(os.environ.get("SESSION_CLEANUP_INTERVAL_HOURS", "6")),
        
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