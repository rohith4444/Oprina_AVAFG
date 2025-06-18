"""
Background token refresh service for Oprina API.

Fixed version that works with Supabase and your existing OAuth token storage.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import schedule
import threading
import time
import json

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
                    # Check and refresh tokens for this user
                    refreshed_gmail = await self._refresh_user_gmail_tokens(user)
                    refreshed_calendar = await self._refresh_user_calendar_tokens(user)
                    
                    if refreshed_gmail:
                        self.stats["successful_refreshes"] += 1
                        logger.info(f"Refreshed Gmail tokens for user {user_email}")
                    
                    if refreshed_calendar:
                        self.stats["successful_refreshes"] += 1
                        logger.info(f"Refreshed Calendar tokens for user {user_email}")
                    
                    refresh_results.append({
                        "user_id": user_id,
                        "email": user_email,
                        "gmail_refreshed": refreshed_gmail,
                        "calendar_refreshed": refreshed_calendar
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
            # FIXED: Use proper Supabase syntax instead of SQLAlchemy-style
            response = self.db_client.table("users").select(
                "id, email, gmail_tokens, calendar_tokens"
            ).not_.is_("gmail_tokens", None).execute()
            
            # Also get users with calendar tokens
            calendar_response = self.db_client.table("users").select(
                "id, email, gmail_tokens, calendar_tokens"
            ).not_.is_("calendar_tokens", None).execute()
            
            # Combine and deduplicate
            all_users = {}
            
            for user in response.data or []:
                all_users[user["id"]] = user
            
            for user in calendar_response.data or []:
                all_users[user["id"]] = user
            
            users_with_tokens = []
            
            for user in all_users.values():
                has_tokens = False
                
                # Check if user has OAuth tokens that might need refreshing
                if user.get("gmail_tokens"):
                    try:
                        gmail_tokens = json.loads(user["gmail_tokens"]) if isinstance(user["gmail_tokens"], str) else user["gmail_tokens"]
                        if gmail_tokens and self._should_refresh_token(gmail_tokens):
                            has_tokens = True
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                if user.get("calendar_tokens"):
                    try:
                        calendar_tokens = json.loads(user["calendar_tokens"]) if isinstance(user["calendar_tokens"], str) else user["calendar_tokens"]
                        if calendar_tokens and self._should_refresh_token(calendar_tokens):
                            has_tokens = True
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                if has_tokens:
                    users_with_tokens.append(user)
            
            logger.info(f"Found {len(users_with_tokens)} users with tokens that may need refreshing")
            return users_with_tokens
            
        except Exception as e:
            logger.error(f"Failed to get users with expiring tokens: {str(e)}")
            return []
    
    def _should_refresh_token(self, token_data: Dict[str, Any]) -> bool:
        """Check if a token should be refreshed based on expiry time."""
        try:
            if not token_data or not isinstance(token_data, dict):
                return False
            
            expires_at_str = token_data.get("expires_at")
            if not expires_at_str:
                return False
            
            # Parse expiry time
            if isinstance(expires_at_str, str):
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            else:
                expires_at = expires_at_str
            
            # Check if token expires within the next hour
            refresh_threshold = datetime.utcnow() + timedelta(hours=1)
            
            return expires_at <= refresh_threshold
            
        except Exception as e:
            logger.error(f"Error checking token expiry: {str(e)}")
            return False
    
    async def _refresh_user_gmail_tokens(self, user: Dict[str, Any]) -> bool:
        """Refresh Gmail tokens for a user."""
        try:
            if not user.get("gmail_tokens"):
                return False
            
            user_id = user["id"]
            gmail_tokens = json.loads(user["gmail_tokens"]) if isinstance(user["gmail_tokens"], str) else user["gmail_tokens"]
            
            if not self._should_refresh_token(gmail_tokens):
                return False
            
            # Use your OAuth service to refresh the token
            refresh_result = await self.oauth_service.refresh_access_token(
                user_id=user_id,
                service="gmail",
                refresh_token=gmail_tokens.get("refresh_token")
            )
            
            return refresh_result.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to refresh Gmail tokens for user {user.get('id')}: {str(e)}")
            return False
    
    async def _refresh_user_calendar_tokens(self, user: Dict[str, Any]) -> bool:
        """Refresh Calendar tokens for a user."""
        try:
            if not user.get("calendar_tokens"):
                return False
            
            user_id = user["id"]
            calendar_tokens = json.loads(user["calendar_tokens"]) if isinstance(user["calendar_tokens"], str) else user["calendar_tokens"]
            
            if not self._should_refresh_token(calendar_tokens):
                return False
            
            # Use your OAuth service to refresh the token
            refresh_result = await self.oauth_service.refresh_access_token(
                user_id=user_id,
                service="calendar",
                refresh_token=calendar_tokens.get("refresh_token")
            )
            
            return refresh_result.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to refresh Calendar tokens for user {user.get('id')}: {str(e)}")
            return False
    
    async def _cleanup_expired_tokens(self):
        """Clean up expired tokens from the database."""
        try:
            logger.info("Running expired token cleanup")
            
            # Get all users with tokens
            response = self.db_client.table("users").select(
                "id, gmail_tokens, calendar_tokens"
            ).execute()
            
            cleanup_count = 0
            
            for user in response.data or []:
                user_id = user["id"]
                updated_data = {}
                
                # Check Gmail tokens
                if user.get("gmail_tokens"):
                    try:
                        gmail_tokens = json.loads(user["gmail_tokens"]) if isinstance(user["gmail_tokens"], str) else user["gmail_tokens"]
                        if self._is_token_expired(gmail_tokens):
                            updated_data["gmail_tokens"] = None
                            cleanup_count += 1
                    except (json.JSONDecodeError, TypeError):
                        updated_data["gmail_tokens"] = None
                        cleanup_count += 1
                
                # Check Calendar tokens
                if user.get("calendar_tokens"):
                    try:
                        calendar_tokens = json.loads(user["calendar_tokens"]) if isinstance(user["calendar_tokens"], str) else user["calendar_tokens"]
                        if self._is_token_expired(calendar_tokens):
                            updated_data["calendar_tokens"] = None
                            cleanup_count += 1
                    except (json.JSONDecodeError, TypeError):
                        updated_data["calendar_tokens"] = None
                        cleanup_count += 1
                
                # Update user if needed
                if updated_data:
                    self.db_client.table("users").update(updated_data).eq("id", user_id).execute()
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} expired tokens")
            else:
                logger.info("No expired tokens to clean up")
                
        except Exception as e:
            logger.error(f"Token cleanup failed: {str(e)}")
    
    def _is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if a token is expired."""
        try:
            if not token_data or not isinstance(token_data, dict):
                return True
            
            expires_at_str = token_data.get("expires_at")
            if not expires_at_str:
                return True
            
            # Parse expiry time
            if isinstance(expires_at_str, str):
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            else:
                expires_at = expires_at_str
            
            # Token is expired if past expiry time
            return expires_at <= datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error checking token expiry: {str(e)}")
            return True
    
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