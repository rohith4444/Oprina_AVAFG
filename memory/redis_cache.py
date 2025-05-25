"""
Redis Cache Service for Oprina

This module provides Redis caching functionality for:
- Email data caching
- Agent coordination data
- Session performance optimization
- Temporary storage

Uses Upstash Redis for cloud-based caching with fallback to local Redis.
"""

import json, sys, os
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.logging.logger import setup_logger
from contextlib import asynccontextmanager
from config.settings import settings


class RedisCacheService:
    """
    Redis cache service with connection pooling and error handling.
    Supports both Upstash Redis REST API and standard Redis protocol.
    """
    
    def __init__(self):
        """Initialize Redis cache service."""
        self.logger = setup_logger("redis_cache", console_output=True)
        self.logger.info("redis cache logging initialized")
        self._client = None
        self._is_connected = False
        self._connection_pool = None
        
        # Cache configuration
        self.default_ttl = settings.CACHE_TTL_SECONDS
        self.email_cache_ttl = settings.EMAIL_CACHE_TTL_SECONDS
        
        # Key prefixes for organization
        self.key_prefixes = {
            "email": "oprina:email:",
            "agent": "oprina:agent:",
            "session": "oprina:session:",
            "user": "oprina:user:",
            "temp": "oprina:temp:"
        }
    
    @property
    def client(self):
        """Get Redis client, creating connection if needed."""
        if self._client is None:
            self._create_connection()
        return self._client
    
    def _create_connection(self):
        """Create Redis connection based on configuration."""
        try:
            if settings.is_upstash_redis:
                if settings.use_redis_rest_api:
                    # Use Upstash REST API
                    from upstash_redis import Redis
                    self._client = Redis(
                        url=settings.UPSTASH_REDIS_REST_URL,
                        token=settings.UPSTASH_REDIS_REST_TOKEN
                    )
                    self.logger.info("Connected to Upstash Redis via REST API")
                else:
                    # Use Redis protocol with Upstash
                    import redis
                    self._client = redis.from_url(
                        settings.UPSTASH_REDIS_URL,
                        decode_responses=True,
                        socket_connect_timeout=10,
                        socket_timeout=10,
                        retry_on_timeout=True
                    )
                    self.logger.info("Connected to Upstash Redis via Redis protocol")
            else:
                # Use local Redis
                import redis
                pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    max_connections=20,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                self._client = redis.Redis(connection_pool=pool)
                self._connection_pool = pool
                self.logger.info("Connected to local Redis")
            
            # Test connection
            self._test_connection()
            self._is_connected = True
            
        except Exception as e:
            self.logger.error(f"Failed to create Redis connection: {e}")
            self._client = None
            self._is_connected = False
            raise
    
    def _test_connection(self):
        """Test Redis connection."""
        try:
            if hasattr(self._client, 'ping'):
                result = self._client.ping()
                if result != True and result != "PONG":
                    raise ConnectionError(f"Unexpected ping response: {result}")
            else:
                # Upstash REST client might not have ping
                self._client.set("oprina:test:connection", "test", ex=5)
                test_result = self._client.get("oprina:test:connection")
                if test_result != "test":
                    raise ConnectionError("Test set/get failed")
                self._client.delete("oprina:test:connection")
            
            self.logger.info("Redis connection test successful")
        except Exception as e:
            self.logger.error(f"Redis connection test failed: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and responsive."""
        if not self._is_connected or self.client is None:
            return False
        
        try:
            # Quick connection test
            if hasattr(self._client, 'ping'):
                self._client.ping()
            else:
                # For REST clients, do a quick operation
                self._client.set("oprina:health", "ok", ex=1)
            return True
        except Exception as e:
            self.logger.warning(f"Redis health check failed: {e}")
            self._is_connected = False
            return False
    
    def _build_key(self, prefix: str, key: str) -> str:
        """Build cache key with proper prefix."""
        if prefix in self.key_prefixes:
            return f"{self.key_prefixes[prefix]}{key}"
        return f"oprina:{prefix}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        elif isinstance(value, (dict, list)):
            return json.dumps(value, default=str)
        else:
            return json.dumps(value, default=str)
    
    def _deserialize_value(self, value: Optional[str]) -> Any:
        """Deserialize value from Redis."""
        if value is None:
            return None
        
        # Try to parse as JSON first
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return as string if JSON parsing fails
            return value
    
    # =============================================================================
    # Basic Cache Operations
    # =============================================================================
    
    def set(self, key: str, value: Any, prefix: str = "temp", ttl_seconds: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            prefix: Key prefix category
            ttl_seconds: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            self.logger.warning("Redis not connected, cache set failed")
            return False
        
        try:
            cache_key = self._build_key(prefix, key)
            serialized_value = self._serialize_value(value)
            ttl = ttl_seconds or self.default_ttl
            
            if hasattr(self._client, 'setex'):
                result = self._client.setex(cache_key, ttl, serialized_value)
            else:
                # Upstash REST API
                result = self._client.set(cache_key, serialized_value, ex=ttl)
            
            self.logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    def get(self, key: str, prefix: str = "temp") -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            prefix: Key prefix category
            
        Returns:
            Cached value or None if not found
        """
        if not self.is_connected():
            self.logger.warning("Redis not connected, cache get failed")
            return None
        
        try:
            cache_key = self._build_key(prefix, key)
            result = self._client.get(cache_key)
            
            if result is not None:
                self.logger.debug(f"Cache hit: {cache_key}")
                return self._deserialize_value(result)
            else:
                self.logger.debug(f"Cache miss: {cache_key}")
                return None
                
        except Exception as e:
            self.logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    def delete(self, key: str, prefix: str = "temp") -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            prefix: Key prefix category
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            self.logger.warning("Redis not connected, cache delete failed")
            return False
        
        try:
            cache_key = self._build_key(prefix, key)
            
            if hasattr(self._client, 'delete'):
                result = self._client.delete(cache_key)
            else:
                # Upstash REST API
                result = self._client.delete([cache_key])
            
            self.logger.debug(f"Cache delete: {cache_key}")
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    def exists(self, key: str, prefix: str = "temp") -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            prefix: Key prefix category
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            cache_key = self._build_key(prefix, key)
            
            if hasattr(self._client, 'exists'):
                result = self._client.exists(cache_key)
            else:
                # For REST API, try to get the key
                result = self._client.get(cache_key) is not None
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Cache exists check failed for key {key}: {e}")
            return False
    
    # =============================================================================
    # Email Caching
    # =============================================================================
    
    def cache_emails(self, user_id: str, emails: List[Dict], ttl_seconds: Optional[int] = None) -> bool:
        """
        Cache user emails.
        
        Args:
            user_id: User identifier
            emails: List of email data
            ttl_seconds: Cache TTL (uses email cache TTL if None)
            
        Returns:
            True if successful
        """
        ttl = ttl_seconds or self.email_cache_ttl
        return self.set(f"{user_id}:emails", emails, prefix="email", ttl_seconds=ttl)
    
    def get_cached_emails(self, user_id: str) -> Optional[List[Dict]]:
        """
        Get cached emails for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of cached emails or None
        """
        return self.get(f"{user_id}:emails", prefix="email")
    
    def cache_email_metadata(self, user_id: str, metadata: Dict, ttl_seconds: Optional[int] = None) -> bool:
        """
        Cache email metadata (sync status, counts, etc.).
        
        Args:
            user_id: User identifier
            metadata: Email metadata
            ttl_seconds: Cache TTL
            
        Returns:
            True if successful
        """
        ttl = ttl_seconds or self.email_cache_ttl
        return self.set(f"{user_id}:metadata", metadata, prefix="email", ttl_seconds=ttl)
    
    def get_email_metadata(self, user_id: str) -> Optional[Dict]:
        """
        Get cached email metadata.
        
        Args:
            user_id: User identifier
            
        Returns:
            Email metadata or None
        """
        return self.get(f"{user_id}:metadata", prefix="email")
    
    # =============================================================================
    # Agent Coordination
    # =============================================================================
    
    def set_agent_context(self, session_id: str, agent_name: str, context: Dict, ttl_seconds: Optional[int] = None) -> bool:
        """
        Store agent context for coordination.
        
        Args:
            session_id: Session identifier
            agent_name: Agent name
            context: Agent context data
            ttl_seconds: Cache TTL
            
        Returns:
            True if successful
        """
        ttl = ttl_seconds or self.default_ttl
        return self.set(f"{session_id}:{agent_name}", context, prefix="agent", ttl_seconds=ttl)
    
    def get_agent_context(self, session_id: str, agent_name: str) -> Optional[Dict]:
        """
        Get agent context.
        
        Args:
            session_id: Session identifier
            agent_name: Agent name
            
        Returns:
            Agent context or None
        """
        return self.get(f"{session_id}:{agent_name}", prefix="agent")
    
    def clear_agent_context(self, session_id: str, agent_name: Optional[str] = None) -> bool:
        """
        Clear agent context.
        
        Args:
            session_id: Session identifier
            agent_name: Specific agent name (clears all if None)
            
        Returns:
            True if successful
        """
        if agent_name:
            return self.delete(f"{session_id}:{agent_name}", prefix="agent")
        else:
            # Clear all agent contexts for session
            try:
                pattern = self._build_key("agent", f"{session_id}:*")
                if hasattr(self._client, 'scan_iter'):
                    keys = list(self._client.scan_iter(match=pattern))
                    if keys:
                        return bool(self._client.delete(*keys))
                return True
            except Exception as e:
                self.logger.error(f"Failed to clear agent contexts: {e}")
                return False
    
    # =============================================================================
    # Session Caching
    # =============================================================================
    
    def cache_session_data(self, session_id: str, data: Dict, ttl_seconds: Optional[int] = None) -> bool:
        """
        Cache session data for quick access.
        
        Args:
            session_id: Session identifier
            data: Session data
            ttl_seconds: Cache TTL
            
        Returns:
            True if successful
        """
        ttl = ttl_seconds or self.default_ttl
        return self.set(session_id, data, prefix="session", ttl_seconds=ttl)
    
    def get_session_cache(self, session_id: str) -> Optional[Dict]:
        """
        Get cached session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        return self.get(session_id, prefix="session")
    
    # =============================================================================
    # User Data Caching
    # =============================================================================
    
    def cache_user_preferences(self, user_id: str, preferences: Dict, ttl_seconds: Optional[int] = None) -> bool:
        """
        Cache user preferences.
        
        Args:
            user_id: User identifier
            preferences: User preferences
            ttl_seconds: Cache TTL
            
        Returns:
            True if successful
        """
        ttl = ttl_seconds or (self.default_ttl * 24)  # Longer TTL for preferences
        return self.set(f"{user_id}:preferences", preferences, prefix="user", ttl_seconds=ttl)
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """
        Get cached user preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            User preferences or None
        """
        return self.get(f"{user_id}:preferences", prefix="user")
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def clear_cache(self, prefix: Optional[str] = None) -> bool:
        """
        Clear cache entries.
        
        Args:
            prefix: Specific prefix to clear (clears all if None)
            
        Returns:
            True if successful
        """
        try:
            if prefix and prefix in self.key_prefixes:
                pattern = f"{self.key_prefixes[prefix]}*"
            elif prefix:
                pattern = f"oprina:{prefix}:*"
            else:
                pattern = "oprina:*"
            
            if hasattr(self._client, 'scan_iter'):
                keys = list(self._client.scan_iter(match=pattern))
                if keys:
                    deleted = self._client.delete(*keys)
                    self.logger.info(f"Cleared {deleted} cache entries with pattern: {pattern}")
                    return True
            else:
                # For REST APIs that don't support scanning
                self.logger.warning("Cache clearing not fully supported with REST API")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cache clear failed: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            stats = {
                "connected": self.is_connected(),
                "provider": "upstash" if settings.is_upstash_redis else "local",
                "using_rest_api": settings.use_redis_rest_api if settings.is_upstash_redis else False,
                "default_ttl": self.default_ttl,
                "email_cache_ttl": self.email_cache_ttl
            }
            
            if hasattr(self._client, 'info'):
                redis_info = self._client.info()
                stats.update({
                    "memory_used": redis_info.get("used_memory_human", "N/A"),
                    "connected_clients": redis_info.get("connected_clients", "N/A"),
                    "total_commands": redis_info.get("total_commands_processed", "N/A")
                })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis cache.
        
        Returns:
            Health check results
        """
        health = {
            "service": "redis_cache",
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Connection check
            health["checks"]["connection"] = self.is_connected()
            
            # Performance check
            start_time = datetime.utcnow()
            test_key = f"health_check_{start_time.timestamp()}"
            
            # Test set/get/delete
            set_success = self.set(test_key, "test", ttl_seconds=5)
            get_result = self.get(test_key) if set_success else None
            delete_success = self.delete(test_key) if set_success else False
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000  # ms
            
            health["checks"]["set_operation"] = set_success
            health["checks"]["get_operation"] = get_result == "test"
            health["checks"]["delete_operation"] = delete_success
            health["checks"]["response_time_ms"] = response_time
            
            # Overall status
            all_checks_passed = all([
                health["checks"]["connection"],
                health["checks"]["set_operation"],
                health["checks"]["get_operation"],
                health["checks"]["delete_operation"]
            ])
            
            health["status"] = "healthy" if all_checks_passed else "degraded"
            health["stats"] = self.get_cache_stats()
            
        except Exception as e:
            health["checks"]["error"] = str(e)
            health["status"] = "unhealthy"
        
        return health
    
    def close(self):
        """Close Redis connection."""
        try:
            if self._connection_pool:
                self._connection_pool.disconnect()
            if self._client:
                if hasattr(self._client, 'close'):
                    self._client.close()
            self._client = None
            self._is_connected = False
            self.logger.info("Redis connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Redis connection: {e}")


# =============================================================================
# Singleton instance and utility functions
# =============================================================================

# Global cache instance
_redis_cache_instance = None


def get_redis_cache() -> RedisCacheService:
    """Get singleton Redis cache instance."""
    global _redis_cache_instance
    if _redis_cache_instance is None:
        _redis_cache_instance = RedisCacheService()
    return _redis_cache_instance


@asynccontextmanager
async def redis_cache_context():
    """Context manager for Redis cache operations."""
    cache = get_redis_cache()
    try:
        yield cache
    finally:
        # Connection cleanup handled by cache service
        pass


# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_redis_cache():
    """Test Redis cache functionality."""
    cache = get_redis_cache()
    
    _ = cache.client  # This creates the connection
    print("Testing Redis Cache Service...")
    
    # Health check
    health = await cache.health_check()
    print(f"Health Check: {health['status']}")
    
    if health["status"] != "healthy":
        print("Redis cache is not healthy, skipping tests")
        return False
    
    # Test basic operations
    test_data = {"test": True, "timestamp": datetime.utcnow().isoformat()}
    
    # Set test
    set_result = cache.set("test_key", test_data, ttl_seconds=10)
    print(f"Set operation: {set_result}")
    
    # Get test
    get_result = cache.get("test_key")
    print(f"Get operation: {get_result == test_data}")
    
    # Email caching test
    emails = [{"id": "1", "subject": "Test Email"}]
    email_cache_result = cache.cache_emails("test_user", emails)
    print(f"Email caching: {email_cache_result}")
    
    # Agent context test
    context = {"status": "active", "last_action": "email_fetch"}
    agent_context_result = cache.set_agent_context("test_session", "email_agent", context)
    print(f"Agent context: {agent_context_result}")
    
    # Clean up
    cache.delete("test_key")
    cache.clear_cache("email")
    cache.clear_cache("agent")
    
    print("✅ Redis cache tests completed")
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_redis_cache())