"""Configuration loader for Oprina"""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables with fallback paths"""
    possible_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent / ".env",
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            print(f"Loaded environment from: {env_path}")
            return str(env_path)
    
    print(" No .env file found, using system environment variables")
    return None

def get_config():
    """Get configuration with validation"""
    load_environment()
    
    config = {
        # Vertex AI Configuration (REQUIRED for deployment)
        "google_cloud_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "google_cloud_location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "google_cloud_storage_bucket": os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET"),
        "google_genai_use_vertexai": os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "1"),
        "google_application_credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        
        # Agent configuration
        "agent_model": os.getenv("AGENT_MODEL", "gemini-2.0-flash"),
        
        # Development vs Production
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }
    
    return config

def validate_deployment_config():
    """Validate that required configuration is present for deployment"""
    config = get_config()
    required_keys = [
        "google_cloud_project", 
        "google_cloud_location", 
        "google_cloud_storage_bucket"
    ]
    
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        print(f"Missing required environment variables for deployment: {', '.join(missing_keys)}")
        return False
    
    return True

# Auto-load environment when module is imported
load_environment()