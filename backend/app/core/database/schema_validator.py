"""
Simplified database schema utilities for Oprina API.
Contains only table name constants - validation logic removed.
"""

from app.utils.logging import get_logger

logger = get_logger(__name__)


class TableNames:
    """Centralized table name constants for repositories."""
    
    # Core application tables (from your actual migrations)
    USERS = "users"
    SESSIONS = "sessions" 
    MESSAGES = "messages"
    
    # Avatar tracking tables (from migrations 006 & 007)
    USER_AVATAR_QUOTAS = "user_avatar_quotas"
    AVATAR_SESSIONS = "avatar_sessions"
    
    # OAuth tables (if you have them)
    # Uncomment these if you implement OAuth token storage
    # SERVICE_TOKENS = "service_tokens"
    # TOKEN_REFRESH_LOGS = "token_refresh_logs"


# Simple utility function for table existence check
def check_table_exists(db_client, table_name: str) -> bool:
    """
    Simple check if a table exists by attempting to query it.
    
    Args:
        db_client: Supabase client
        table_name: Name of table to check
        
    Returns:
        bool: True if table exists and is accessible
    """
    try:
        db_client.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        logger.debug(f"Table {table_name} not accessible: {str(e)}")
        return False


# Quick health check for your main tables
async def validate_core_tables(db_client) -> dict:
    """
    Quick validation that your core tables exist.
    
    Returns:
        dict: Status of each core table
    """
    core_tables = {
        "users": TableNames.USERS,
        "sessions": TableNames.SESSIONS,
        "messages": TableNames.MESSAGES,
        "user_avatar_quotas": TableNames.USER_AVATAR_QUOTAS,
        "avatar_sessions": TableNames.AVATAR_SESSIONS
    }
    
    results = {}
    
    for description, table_name in core_tables.items():
        exists = check_table_exists(db_client, table_name)
        results[description] = {
            "table_name": table_name,
            "exists": exists
        }
        
        if exists:
            logger.debug(f"✅ {description} table ({table_name}) exists")
        else:
            logger.warning(f"❌ {description} table ({table_name}) missing")
    
    return results