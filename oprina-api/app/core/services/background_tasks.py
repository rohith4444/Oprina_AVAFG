"""
Background task service for Oprina API.

This module handles scheduled background tasks like token refresh,
cleanup operations, and other maintenance tasks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from app.core.database.repositories.token_repository import TokenRepository
from app.core.services.oauth_service import OAuthService
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class BackgroundTaskService:
    """Service for managing background tasks."""
    
    def __init__(self, oauth_service: OAuthService):
        self.oauth_service = oauth_service
        self.running = False
        self.tasks: Dict[str, asyncio.Task] = {}
        
    async def start(self):
        """Start all background tasks."""
        if self.running:
            logger.warning("Background tasks already running")
            return
        
        self.running = True
        logger.info("Starting background tasks")
        
        # Start token refresh task
        self.tasks["token_refresh"] = asyncio.create_task(
            self._token_refresh_loop()
        )
        
        # Start cleanup task
        self.tasks["cleanup"] = asyncio.create_task(
            self._cleanup_loop()
        )
        
        logger.info(f"Started {len(self.tasks)} background tasks")
    
    async def stop(self):
        """Stop all background tasks."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping background tasks")
        
        # Cancel all tasks
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Task {task_name} cancelled")
        
        self.tasks.clear()
        logger.info("All background tasks stopped")
    
    async def _token_refresh_loop(self):
        """Background loop for refreshing expiring tokens."""
        logger.info("Starting token refresh background task")
        
        while self.running:
            try:
                # Refresh expiring tokens
                refresh_results = await self.oauth_service.auto_refresh_expiring_tokens()
                
                if refresh_results:
                    total_refreshed = sum(refresh_results.values())
                    if total_refreshed > 0:
                        logger.info(f"Background refresh completed: {refresh_results}")
                
                # Wait for next refresh cycle (30 minutes)
                await asyncio.sleep(30 * 60)  # 30 minutes
                
            except asyncio.CancelledError:
                logger.info("Token refresh task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in token refresh loop: {e}")
                # Wait 5 minutes before retrying on error
                await asyncio.sleep(5 * 60)
    
    async def _cleanup_loop(self):
        """Background loop for cleanup operations."""
        logger.info("Starting cleanup background task")
        
        while self.running:
            try:
                # Clean up expired tokens
                expired_count = await self.oauth_service.cleanup_expired_tokens()
                
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired tokens")
                
                # Wait for next cleanup cycle (6 hours)
                await asyncio.sleep(6 * 60 * 60)  # 6 hours
                
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                # Wait 30 minutes before retrying on error
                await asyncio.sleep(30 * 60)
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all background tasks."""
        status = {
            "running": self.running,
            "tasks": {}
        }
        
        for task_name, task in self.tasks.items():
            status["tasks"][task_name] = {
                "done": task.done(),
                "cancelled": task.cancelled(),
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
        
        return status


# Global background task service instance
_background_service: Optional[BackgroundTaskService] = None


def get_background_service(oauth_service: OAuthService) -> BackgroundTaskService:
    """Get or create background task service."""
    global _background_service
    
    if _background_service is None:
        _background_service = BackgroundTaskService(oauth_service)
    
    return _background_service


@asynccontextmanager
async def background_task_lifespan(oauth_service: OAuthService):
    """Context manager for background task lifecycle."""
    service = get_background_service(oauth_service)
    
    try:
        await service.start()
        yield service
    finally:
        await service.stop()


# Startup/shutdown functions for FastAPI
async def startup_background_tasks(oauth_service: OAuthService):
    """Start background tasks on application startup."""
    if settings.ENABLE_BACKGROUND_TASKS:
        service = get_background_service(oauth_service)
        await service.start()
        logger.info("Background tasks started")
    else:
        logger.info("Background tasks disabled by configuration")


async def shutdown_background_tasks():
    """Stop background tasks on application shutdown."""
    global _background_service
    
    if _background_service:
        await _background_service.stop()
        logger.info("Background tasks stopped")


# Manual trigger functions (for testing/admin)
async def trigger_token_refresh(oauth_service: OAuthService) -> Dict[str, int]:
    """Manually trigger token refresh."""
    logger.info("Manually triggering token refresh")
    return await oauth_service.auto_refresh_expiring_tokens()


async def trigger_cleanup(oauth_service: OAuthService) -> int:
    """Manually trigger cleanup."""
    logger.info("Manually triggering cleanup")
    return await oauth_service.cleanup_expired_tokens() 