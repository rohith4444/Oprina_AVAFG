"""
Background token refresh service for Oprina API.

This service runs in the background and automatically refreshes OAuth tokens
before they expire, ensuring users never lose access to connected services.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import schedule
import threading
import time

from app.core.database.repositories.user_repository import UserRepository
from app.core.services.google_oauth_service import GoogleOAuthService
from app.core.database.connection import get_database_client
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class BackgroundTokenService:
    """Service for background token refresh operations."""
    
    def __init__(self):
        self.is_running = False
        self.refresh_thread = None
        self.db_client = None
        self.user_repository = None
        self.oauth_service = None
        
        # Configuration from settings
        self.refresh_interval_minutes = settings.TOKEN_REFRESH_INTERVAL_MINUTES
        self.cleanup_interval_hours = settings.CLEANUP_INTERVAL_HOURS
        self.enabled = settings.ENABLE_BACKGROUND_TASKS
        
        # Statistics
        self.stats = {
            "total_refreshes": 0,
            "successful_refreshes": 0,
            "failed_refreshes": 0,
            "last_run": None,
            "last_cleanup": None,
            "errors": []
        }
    
    def initialize_services(self):
        """Initialize database and OAuth services."""
        try:
            self.db_client = get_database_client()
            self.user_repository = UserRepository(self.db_client)
            self.oauth_service = GoogleOAuthService(self.user_repository)
            logger.info("Background token service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize background token service: {str(e)}")
            raise
    
    def start(self):
        """Start the background token refresh service."""
        if not self.enabled:
            logger.info("Background token refresh is disabled")
            return
        
        if self.is_running:
            logger.warning("Background token service is already running")
            return
        
        try:
            self.initialize_services()
            
            # Schedule token refresh
            schedule.every(self.refresh_interval_minutes).minutes.do(
                self._run_token_refresh_job
            )
            
            # Schedule cleanup (daily)
            schedule.every(self.cleanup_interval_hours).hours.do(
                self._run_cleanup_job
            )
            
            # Start the scheduler thread
            self.is_running = True
            self.refresh_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.refresh_thread.start()
            
            logger.info(f"Background token service started")
            logger.info(f"Token refresh interval: {self.refresh_interval_minutes} minutes")
            logger.info(f"Cleanup interval: {self.cleanup_interval_hours} hours")
            
        except Exception as e:
            logger.error(f"Failed to start background token service: {str(e)}")
            self.is_running = False
            raise
    
    def stop(self):
        """Stop the background token refresh service."""
        self.is_running = False
        schedule.clear()
        
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=5)
        
        logger.info("Background token service stopped")
    
    def _run_scheduler(self):
        """Run the background scheduler."""
        logger.info("Background scheduler started")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                self.stats["errors"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                    "type": "scheduler_error"
                })
                time.sleep(60)  # Continue running even on errors
        
        logger.info("Background scheduler stopped")
    
    def _run_token_refresh_job(self):
        """Run the token refresh job."""
        logger.info("Starting background token refresh job")
        
        try:
            # Run async function in the scheduler thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._refresh_expiring_tokens())
            loop.close()
            
            self.stats["last_run"] = datetime.utcnow().isoformat()
            logger.info("Background token refresh job completed")
            
        except Exception as e:
            logger.error(f"Token refresh job failed: {str(e)}")
            self.stats["errors"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "type": "refresh_job_error"
            })
    
    def _run_cleanup_job(self):
        """Run the cleanup job."""
        logger.info("Starting background cleanup job")
        
        try:
            # Run async function in the scheduler thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._cleanup_expired_tokens())
            loop.close()
            
            self.stats["last_cleanup"] = datetime.utcnow().isoformat()
            logger.info("Background cleanup job completed")
            
        except Exception as e:
            logger.error(f"Cleanup job failed: {str(e)}")
            self.stats["errors"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "type": "cleanup_job_error"
            })
    
    async def _refresh_expiring_tokens(self):
        """Find and refresh tokens that are expiring soon."""
        try:
            # Get all users with OAuth tokens
            users_with_tokens = await self._get_users_with_expiring_tokens()
            
            if not users_with_tokens:
                logger.info("No users with expiring tokens found")
                return
            
            logger.info(f"Found {len(users_with_tokens)} users with expiring tokens")
            
            refresh_results = []
            
            for user in users_with_tokens:
                user_id = user["id"]
                user_email = user.get("email", "unknown")
                
                try:
                    # Check and refresh all services for this user
                    result = await self.oauth_service.check_and_refresh_expired_tokens(user_id)
                    
                    # Count successful refreshes
                    for service, service_result in result.items():
                        if service_result.get("refreshed"):
                            self.stats["successful_refreshes"] += 1
                            logger.info(f"Refreshed {service} token for user {user_email}")
                        elif service_result.get("error"):
                            self.stats["failed_refreshes"] += 1
                            logger.warning(f"Failed to refresh {service} token for user {user_email}: {service_result['error']}")
                    
                    refresh_results.append({
                        "user_id": user_id,
                        "email": user_email,
                        "result": result
                    })
                    
                except Exception as e:
                    self.stats["failed_refreshes"] += 1
                    logger.error(f"Token refresh failed for user {user_email}: {str(e)}")
                    refresh_results.append({
                        "user_id": user_id,
                        "email": user_email,
                        "error": str(e)
                    })
                
                # Small delay between users to avoid rate limiting
                await asyncio.sleep(1)
            
            self.stats["total_refreshes"] += len(users_with_tokens)
            
            # Log summary
            successful = sum(1 for r in refresh_results if "error" not in r)
            failed = len(refresh_results) - successful
            
            logger.info(f"Token refresh summary: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Failed to refresh expiring tokens: {str(e)}")
            raise
    
    async def _get_users_with_expiring_tokens(self) -> List[Dict[str, Any]]:
        """Get users whose tokens are expiring within the next hour."""
        try:
            # This is a simplified query - in production you'd want to check actual expiry times
            # For now, we'll get all users with OAuth tokens and let the service check expiry
            
            response = self.db_client.table("users").select(
                "id, email, gmail_tokens, calendar_tokens"
            ).or_(
                "gmail_tokens.is.not.null,calendar_tokens.is.not.null"
            ).execute()
            
            users_with_tokens = []
            
            for user in response.data:
                has_tokens = False
                
                # Check if user has any OAuth tokens
                if user.get("gmail_tokens") or user.get("calendar_tokens"):
                    has_tokens = True
                
                if has_tokens:
                    users_with_tokens.append(user)
            
            return users_with_tokens
            
        except Exception as e:
            logger.error(f"Failed to get users with expiring tokens: {str(e)}")
            return []
    
    async def _cleanup_expired_tokens(self):
        """Clean up expired tokens from the database."""
        try:
            logger.info("Running expired token cleanup")
            
            # Use the database function we created in the migration
            cleanup_result = self.db_client.rpc("cleanup_expired_oauth_tokens").execute()
            
            cleaned_count = cleanup_result.data if cleanup_result.data else 0
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired tokens")
            else:
                logger.info("No expired tokens to clean up")
                
        except Exception as e:
            logger.error(f"Token cleanup failed: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get background service statistics."""
        return {
            **self.stats,
            "is_running": self.is_running,
            "enabled": self.enabled,
            "refresh_interval_minutes": self.refresh_interval_minutes,
            "cleanup_interval_hours": self.cleanup_interval_hours,
            "next_refresh": self._get_next_scheduled_time("token_refresh"),
            "next_cleanup": self._get_next_scheduled_time("cleanup")
        }
    
    def _get_next_scheduled_time(self, job_type: str) -> str:
        """Get the next scheduled time for a job type."""
        try:
            jobs = schedule.get_jobs()
            for job in jobs:
                if job_type in str(job.job_func):
                    return job.next_run.isoformat() if job.next_run else "Not scheduled"
            return "Not scheduled"
        except:
            return "Unknown"


# Global background service instance
_background_service: BackgroundTokenService = None


def get_background_token_service() -> BackgroundTokenService:
    """Get the global background token service instance."""
    global _background_service
    if _background_service is None:
        _background_service = BackgroundTokenService()
    return _background_service


def start_background_token_service():
    """Start the background token service."""
    service = get_background_token_service()
    service.start()


def stop_background_token_service():
    """Stop the background token service."""
    service = get_background_token_service()
    service.stop()