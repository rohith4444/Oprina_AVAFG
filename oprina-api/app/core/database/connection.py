"""
Supabase database connection and client management.
"""

from typing import Optional
from supabase import create_client, Client
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)


class DatabaseConnection:
    """Manages Supabase database connections."""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the database connection."""
        if self._initialized:
            return
            
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError("Supabase URL and Key must be configured")
            
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            
            # Test connection
            result = self._client.table("users").select("id").limit(1).execute()
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    @property
    def client(self) -> Client:
        """Get the Supabase client."""
        if not self._initialized or not self._client:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._client
    
    async def close(self) -> None:
        """Close the database connection."""
        if self._client:
            # Supabase client doesn't need explicit closing
            self._client = None
            self._initialized = False
            logger.info("Database connection closed")


# Global database connection instance
db_connection = DatabaseConnection()


async def get_database() -> Client:
    """Dependency to get database client."""
    if not db_connection._initialized:
        await db_connection.initialize()
    return db_connection.client


async def init_database() -> None:
    """Initialize database on app startup."""
    await db_connection.initialize()


async def close_database() -> None:
    """Close database on app shutdown."""
    await db_connection.close() 