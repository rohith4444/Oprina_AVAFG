"""Avatar usage tracking repository."""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from supabase import Client

from app.models.database.avatar_usage import AvatarUsageRecord, UsageQuota, UsageSummary
from app.utils.logging import get_logger

logger = get_logger(__name__)


class UsageRepository:
    """Repository for avatar usage tracking operations."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    # Avatar Usage Records
    
    async def create_usage_record(self, record: AvatarUsageRecord) -> AvatarUsageRecord:
        """Create a new avatar usage record."""
        try:
            record.id = str(uuid.uuid4())
            record.created_at = datetime.utcnow()
            record.updated_at = datetime.utcnow()
            
            # Calculate billing period
            record.billing_period = record.session_started_at.strftime("%Y-%m")
            
            data = record.model_dump()
            
            response = self.client.table("avatar_usage_records").insert(data).execute()
            
            if response.data:
                logger.info(f"Created avatar usage record: {record.id}")
                return AvatarUsageRecord(**response.data[0])
            else:
                raise Exception("Failed to create usage record")
                
        except Exception as e:
            logger.error(f"Error creating usage record: {str(e)}")
            raise
    
    async def update_usage_record(self, record_id: str, updates: Dict[str, Any]) -> Optional[AvatarUsageRecord]:
        """Update an existing usage record."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.client.table("avatar_usage_records").update(updates).eq("id", record_id).execute()
            
            if response.data:
                logger.info(f"Updated usage record: {record_id}")
                return AvatarUsageRecord(**response.data[0])
            else:
                logger.warning(f"Usage record not found: {record_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating usage record {record_id}: {str(e)}")
            raise
    
    async def end_session(self, avatar_session_id: str, words_spoken: int = 0, error_message: Optional[str] = None) -> Optional[AvatarUsageRecord]:
        """End an avatar session and calculate final usage."""
        try:
            # Find the active record
            response = self.client.table("avatar_usage_records").select("*").eq("avatar_session_id", avatar_session_id).eq("status", "active").execute()
            
            if not response.data:
                logger.warning(f"No active usage record found for avatar session: {avatar_session_id}")
                return None
            
            record_data = response.data[0]
            session_started_at = datetime.fromisoformat(record_data["session_started_at"])
            session_ended_at = datetime.utcnow()
            duration_seconds = int((session_ended_at - session_started_at).total_seconds())
            
            # Calculate estimated cost (rough estimate: $0.50 per minute)
            duration_minutes = duration_seconds / 60.0
            estimated_cost = round(duration_minutes * 0.50, 2)
            
            updates = {
                "session_ended_at": session_ended_at.isoformat(),
                "duration_seconds": duration_seconds,
                "words_spoken": words_spoken,
                "estimated_cost": estimated_cost,
                "status": "error" if error_message else "completed",
                "error_message": error_message
            }
            
            return await self.update_usage_record(record_data["id"], updates)
            
        except Exception as e:
            logger.error(f"Error ending avatar session {avatar_session_id}: {str(e)}")
            raise
    
    async def get_user_usage_records(self, user_id: str, billing_period: Optional[str] = None, limit: int = 50) -> List[AvatarUsageRecord]:
        """Get usage records for a user."""
        try:
            query = self.client.table("avatar_usage_records").select("*").eq("user_id", user_id)
            
            if billing_period:
                query = query.eq("billing_period", billing_period)
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            return [AvatarUsageRecord(**record) for record in response.data]
            
        except Exception as e:
            logger.error(f"Error getting user usage records for {user_id}: {str(e)}")
            raise
    
    # Usage Quotas
    
    async def get_or_create_quota(self, user_id: str) -> UsageQuota:
        """Get or create usage quota for a user (20 minutes total per account)."""
        try:
            # Try to get existing quota (one per user, lifetime)
            response = self.client.table("usage_quotas").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                return UsageQuota(**response.data[0])
            
            # Create new quota for this user (20 minutes total)
            quota = UsageQuota(
                id=str(uuid.uuid4()),
                user_id=user_id,
                total_limit_minutes=20,
                used_minutes=0,
                used_seconds=0,
                session_count=0,
                quota_exhausted=False
            )
            
            data = quota.model_dump()
            
            response = self.client.table("usage_quotas").insert(data).execute()
            
            if response.data:
                logger.info(f"Created new 20-minute quota for user {user_id}")
                return UsageQuota(**response.data[0])
            else:
                raise Exception("Failed to create usage quota")
                
        except Exception as e:
            logger.error(f"Error getting/creating quota for user {user_id}: {str(e)}")
            raise
    
    async def update_quota_usage(self, user_id: str, duration_seconds: int) -> Optional[UsageQuota]:
        """Update quota usage after a session (20-minute total limit)."""
        try:
            quota = await self.get_or_create_quota(user_id)
            
            # Calculate new totals
            new_total_seconds = quota.used_seconds + duration_seconds
            new_total_minutes = new_total_seconds // 60
            
            # Check if quota is now exhausted (>= 20 minutes)
            quota_exhausted = new_total_minutes >= quota.total_limit_minutes
            
            updates = {
                "used_seconds": new_total_seconds,
                "used_minutes": new_total_minutes,
                "session_count": quota.session_count + 1,
                "quota_exhausted": quota_exhausted,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Mark exhaustion timestamp if just reached limit
            if quota_exhausted and not quota.quota_exhausted:
                updates["exhausted_at"] = datetime.utcnow().isoformat()
            
            response = self.client.table("usage_quotas").update(updates).eq("id", quota.id).execute()
            
            if response.data:
                logger.info(f"Updated quota usage for user {user_id}: {new_total_minutes}/{quota.total_limit_minutes} minutes used")
                if quota_exhausted:
                    logger.warning(f"User {user_id} has exhausted their 20-minute quota!")
                return UsageQuota(**response.data[0])
            else:
                logger.warning(f"Failed to update quota for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating quota usage for user {user_id}: {str(e)}")
            raise
    
    async def check_quota_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if user has exceeded 20-minute quota limit."""
        try:
            quota = await self.get_or_create_quota(user_id)
            
            minutes_remaining = max(0, quota.total_limit_minutes - quota.used_minutes)
            seconds_remaining = max(0, (quota.total_limit_minutes * 60) - quota.used_seconds)
            
            minutes_percentage = (quota.used_minutes / quota.total_limit_minutes) * 100 if quota.total_limit_minutes > 0 else 0
            
            return {
                "can_create_session": not quota.quota_exhausted and minutes_remaining > 0,
                "quota": quota,
                "limits": {
                    "total_limit_minutes": quota.total_limit_minutes,
                    "used_minutes": quota.used_minutes,
                    "used_seconds": quota.used_seconds,
                    "minutes_remaining": minutes_remaining,
                    "seconds_remaining": seconds_remaining,
                    "minutes_percentage": round(minutes_percentage, 1),
                    "quota_exhausted": quota.quota_exhausted
                },
                "warnings": {
                    "approaching_limit": minutes_percentage >= 80,  # 16+ minutes used
                    "quota_exhausted": quota.quota_exhausted,
                    "exhausted_at": quota.exhausted_at.isoformat() if quota.exhausted_at else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking quota limits for user {user_id}: {str(e)}")
            raise 