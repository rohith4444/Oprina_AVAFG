"""
Database connection - MINIMAL FIX for health endpoint only.

Only modify what's needed for health check to work.
"""

from typing import Optional
from supabase import create_client, Client
from app.config import get_settings

_db_client: Optional[Client] = None
_initialized = False

def get_database_client() -> Client:
    """
    Get database client for health endpoint.
    
    Simple implementation - initialize once, reuse.
    """
    global _db_client, _initialized
    
    if not _initialized:
        settings = get_settings()
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured")
        
        _db_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        _initialized = True
    
    if not _db_client:
        raise RuntimeError("Database client not initialized")
    
    return _db_client
