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
        """Get or create usage quota for a user."""
        try:
            current_month = datetime.utcnow().strftime("%Y-%m")
            
            # Try to get existing quota
            response = self.client.table("usage_quotas").select("*").eq("user_id", user_id).eq("current_month", current_month).execute()
            
            if response.data:
                return UsageQuota(**response.data[0])
            
            # Create new quota for this month
            quota = UsageQuota(
                id=str(uuid.uuid4()),
                user_id=user_id,
                current_month=current_month,
                last_reset_at=datetime.utcnow()
            )
            
            data = quota.model_dump()
            
            response = self.client.table("usage_quotas").insert(data).execute()
            
            if response.data:
                logger.info(f"Created new quota for user {user_id} for {current_month}")
                return UsageQuota(**response.data[0])
            else:
                raise Exception("Failed to create usage quota")
                
        except Exception as e:
            logger.error(f"Error getting/creating quota for user {user_id}: {str(e)}")
            raise
    
    async def update_quota_usage(self, user_id: str, duration_minutes: float, cost: float) -> Optional[UsageQuota]:
        """Update quota usage after a session."""
        try:
            quota = await self.get_or_create_quota(user_id)
            
            updates = {
                "used_minutes": quota.used_minutes + int(duration_minutes),
                "used_cost": round(quota.used_cost + cost, 2),
                "session_count": quota.session_count + 1,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("usage_quotas").update(updates).eq("id", quota.id).execute()
            
            if response.data:
                logger.info(f"Updated quota usage for user {user_id}")
                return UsageQuota(**response.data[0])
            else:
                logger.warning(f"Failed to update quota for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating quota usage for user {user_id}: {str(e)}")
            raise
    
    async def check_quota_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if user has exceeded quota limits."""
        try:
            quota = await self.get_or_create_quota(user_id)
            
            minutes_remaining = max(0, quota.monthly_limit_minutes - quota.used_minutes)
            cost_remaining = max(0.0, quota.monthly_limit_cost - quota.used_cost)
            
            minutes_percentage = (quota.used_minutes / quota.monthly_limit_minutes) * 100 if quota.monthly_limit_minutes > 0 else 0
            cost_percentage = (quota.used_cost / quota.monthly_limit_cost) * 100 if quota.monthly_limit_cost > 0 else 0
            
            return {
                "can_create_session": minutes_remaining > 0 and cost_remaining > 0,
                "quota": quota,
                "limits": {
                    "minutes_remaining": minutes_remaining,
                    "cost_remaining": round(cost_remaining, 2),
                    "minutes_percentage": round(minutes_percentage, 1),
                    "cost_percentage": round(cost_percentage, 1)
                },
                "warnings": {
                    "approaching_minute_limit": minutes_percentage >= 80,
                    "approaching_cost_limit": cost_percentage >= 80,
                    "exceeded_minute_limit": minutes_remaining <= 0,
                    "exceeded_cost_limit": cost_remaining <= 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking quota limits for user {user_id}: {str(e)}")
            raise 