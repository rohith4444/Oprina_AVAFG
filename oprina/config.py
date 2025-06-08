"""Configuration loader for Oprina"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables with fallback paths"""
    
    # Try multiple .env locations (in order of preference)
    possible_paths = [
        Path.cwd() / ".env",                    # Current working directory (for adk run/web)
        Path(__file__).parent.parent / ".env", # Project root (../oprina/.env -> ../.env)
        Path(__file__).parent / ".env",        # oprina/ directory (fallback)
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)  # Don't override existing env vars
            print(f"📁 Loaded environment from: {env_path}")
            return str(env_path)
    
    print("⚠️  No .env file found, using system environment variables")
    return None

def get_config():
    """Get configuration with validation"""
    load_environment()
    
    config = {
        # Google Cloud / Vertex AI
        "google_api_key": os.getenv("GOOGLE_GENAI_USE_VERTEXAI"),
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        
        # Development vs Production
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        
        # Agent configuration
        "agent_model": os.getenv("AGENT_MODEL", "gemini-2.0-flash"),
    }
    
    return config

def validate_config(required_keys=None):
    """Validate that required configuration is present"""
    if required_keys is None:
        required_keys = ["google_api_key"]
    
    config = get_config()
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        print(f"❌ Missing required environment variables: {', '.join(missing_keys)}")
        return False
    
    return True

# Auto-load environment when module is imported
load_environment()