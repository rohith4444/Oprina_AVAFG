"""Avatar usage tracking database models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AvatarUsageRecord(BaseModel):
    """Avatar usage record for tracking streaming sessions."""
    
    id: Optional[str] = None
    user_id: str = Field(..., description="User who initiated the session")
    session_id: str = Field(..., description="Chat session ID this avatar was used in")
    avatar_session_id: str = Field(..., description="HeyGen avatar session ID")
    avatar_name: str = Field(..., description="Name of the avatar used")
    
    # Session tracking
    session_started_at: datetime = Field(..., description="When avatar session started")
    session_ended_at: Optional[datetime] = Field(None, description="When avatar session ended")
    duration_seconds: Optional[int] = Field(None, description="Total session duration")
    
    # Usage tracking
    words_spoken: int = Field(default=0, description="Total words spoken by avatar")
    messages_count: int = Field(default=0, description="Number of messages sent to avatar")
    
    # Cost tracking
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in USD")
    billing_period: str = Field(..., description="Billing period (YYYY-MM)")
    
    # Status tracking
    status: str = Field(default="active", description="Session status: active, completed, error, timeout")
    error_message: Optional[str] = Field(None, description="Error message if session failed")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class UsageQuota(BaseModel):
    """User's avatar usage quota - 20 minutes total per account."""
    
    id: Optional[str] = None
    user_id: str = Field(..., description="User ID")
    
    # Total account limits (lifetime)
    total_limit_minutes: int = Field(default=20, description="Total limit in minutes (20 min per account)")
    
    # Current usage (lifetime)
    used_minutes: int = Field(default=0, description="Total minutes used")
    used_seconds: int = Field(default=0, description="Total seconds used (for precision)")
    session_count: int = Field(default=0, description="Total number of sessions")
    
    # Status
    is_active: bool = Field(default=True, description="Whether quota is active")
    quota_exhausted: bool = Field(default=False, description="Whether 20-minute limit reached")
    exhausted_at: Optional[datetime] = Field(None, description="When quota was exhausted")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    """Summary of avatar usage for reporting."""
    
    user_id: str
    billing_period: str
    
    # Session statistics
    total_sessions: int = 0
    completed_sessions: int = 0
    failed_sessions: int = 0
    
    # Usage statistics
    total_duration_minutes: float = 0.0
    total_words_spoken: int = 0
    total_messages: int = 0
    
    # Cost statistics
    total_estimated_cost: float = 0.0
    average_cost_per_session: float = 0.0
    average_duration_per_session: float = 0.0
    
    # Quota status
    quota_limit_minutes: int = 0
    quota_used_minutes: float = 0.0
    quota_remaining_minutes: float = 0.0
    quota_usage_percentage: float = 0.0
    
    # Time range
    period_start: datetime
    period_end: datetime 