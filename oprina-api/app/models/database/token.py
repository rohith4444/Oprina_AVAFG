"""
Service Token database entity model for Oprina API.

This module defines the SQLAlchemy ServiceToken model for storing encrypted
OAuth tokens and API keys for external service integrations.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class ServiceToken(Base):
    """
    Service token entity for storing encrypted OAuth tokens and API keys.
    
    This model handles secure storage of tokens for external services like
    Gmail, Google Calendar, Microsoft Graph, etc.
    """
    
    __tablename__ = "service_tokens"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Foreign key to users
    
    # Service identification
    service_type = Column(String(100), nullable=False, index=True)  # gmail, calendar, microsoft, etc.
    service_name = Column(String(255), nullable=True)  # Human-readable service name
    
    # Token data (encrypted)
    access_token_encrypted = Column(Text, nullable=False)  # Encrypted access token
    refresh_token_encrypted = Column(Text, nullable=True)  # Encrypted refresh token (if available)
    id_token_encrypted = Column(Text, nullable=True)  # Encrypted ID token (if available)
    
    # Token metadata
    token_type = Column(String(50), default='Bearer', nullable=False)  # Bearer, Basic, etc.
    scope = Column(Text, nullable=True)  # Granted scopes
    expires_at = Column(DateTime, nullable=True)  # When access token expires
    
    # OAuth provider details
    provider = Column(String(100), nullable=False)  # google, microsoft, etc.
    provider_user_id = Column(String(255), nullable=True)  # Provider's user ID
    provider_email = Column(String(255), nullable=True)  # Email from provider
    
    # Token status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Additional metadata
    token_metadata = Column(JSONB, default=dict, nullable=False)  # Additional token info
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships (Note: User relationship is defined in user.py to avoid circular imports)
    
    def __repr__(self) -> str:
        return f"<ServiceToken(id={self.id}, user_id={self.user_id}, service={self.service_type}, provider={self.provider})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert token to dictionary for API responses (without sensitive data)."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'service_type': self.service_type,
            'service_name': self.service_name,
            'token_type': self.token_type,
            'scope': self.scope,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'provider': self.provider,
            'provider_user_id': self.provider_user_id,
            'provider_email': self.provider_email,
            'is_active': self.is_active,
            'is_revoked': self.is_revoked,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'token_metadata': self.token_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert token to summary dictionary for listing APIs."""
        return {
            'id': str(self.id),
            'service_type': self.service_type,
            'service_name': self.service_name or self.service_type.title(),
            'provider': self.provider,
            'provider_email': self.provider_email,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (active, not revoked, not expired)."""
        return self.is_active and not self.is_revoked and not self.is_expired
    
    @property
    def display_name(self) -> str:
        """Get a display-friendly name for the token."""
        if self.service_name:
            return self.service_name
        elif self.provider_email:
            return f"{self.service_type.title()} ({self.provider_email})"
        else:
            return f"{self.service_type.title()} - {self.provider.title()}"
    
    @property
    def expires_in_minutes(self) -> Optional[int]:
        """Get minutes until token expires."""
        if self.expires_at is None:
            return None
        
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 60))
    
    @property
    def needs_refresh(self) -> bool:
        """Check if token needs to be refreshed (expires within 10 minutes)."""
        if self.expires_at is None:
            return False
        
        minutes_left = self.expires_in_minutes
        return minutes_left is not None and minutes_left <= 10
    
    def update_metadata(self, new_metadata: Dict[str, Any]) -> None:
        """Update token metadata, merging with existing metadata."""
        if self.token_metadata is None:
            self.token_metadata = {}
        
        # Merge metadata
        current_metadata = dict(self.token_metadata)
        current_metadata.update(new_metadata)
        self.token_metadata = current_metadata
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a specific metadata value."""
        if self.token_metadata is None:
            return default
        return self.token_metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set a specific metadata value."""
        if self.token_metadata is None:
            self.token_metadata = {}
        
        metadata = dict(self.token_metadata)
        metadata[key] = value
        self.token_metadata = metadata
    
    def mark_used(self) -> None:
        """Mark token as recently used."""
        self.last_used_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the token."""
        self.is_active = True
        self.is_revoked = False
    
    def deactivate(self) -> None:
        """Deactivate the token."""
        self.is_active = False
    
    def revoke(self) -> None:
        """Revoke the token."""
        self.is_revoked = True
        self.is_active = False
    
    def update_expiry(self, expires_at: datetime) -> None:
        """Update token expiry time."""
        self.expires_at = expires_at
    
    def update_scope(self, scope: str) -> None:
        """Update token scope."""
        self.scope = scope
    
    @classmethod
    def create_oauth_token(
        cls,
        user_id: str,
        service_type: str,
        provider: str,
        access_token_encrypted: str,
        refresh_token_encrypted: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        scope: Optional[str] = None,
        provider_user_id: Optional[str] = None,
        provider_email: Optional[str] = None,
        **kwargs
    ) -> "ServiceToken":
        """
        Create a new OAuth service token instance.
        
        Args:
            user_id: User identifier
            service_type: Type of service (gmail, calendar, etc.)
            provider: OAuth provider (google, microsoft, etc.)
            access_token_encrypted: Encrypted access token
            refresh_token_encrypted: Encrypted refresh token
            expires_at: When the access token expires
            scope: Granted OAuth scopes
            provider_user_id: Provider's user ID
            provider_email: Email from provider
            **kwargs: Additional token attributes
            
        Returns:
            New ServiceToken instance
        """
        return cls(
            user_id=user_id,
            service_type=service_type,
            provider=provider,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            expires_at=expires_at,
            scope=scope,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            **kwargs
        )
    
    @classmethod
    def create_api_key_token(
        cls,
        user_id: str,
        service_type: str,
        provider: str,
        api_key_encrypted: str,
        service_name: Optional[str] = None,
        **kwargs
    ) -> "ServiceToken":
        """
        Create a new API key service token instance.
        
        Args:
            user_id: User identifier
            service_type: Type of service
            provider: Service provider
            api_key_encrypted: Encrypted API key
            service_name: Human-readable service name
            **kwargs: Additional token attributes
            
        Returns:
            New ServiceToken instance
        """
        return cls(
            user_id=user_id,
            service_type=service_type,
            service_name=service_name,
            provider=provider,
            access_token_encrypted=api_key_encrypted,
            token_type='ApiKey',
            **kwargs
        )


class TokenRefreshLog(Base):
    """
    Token refresh log entity for tracking token refresh operations.
    
    This model tracks when tokens are refreshed, helping with debugging
    and monitoring token health.
    """
    
    __tablename__ = "token_refresh_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_token_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Foreign key to service_tokens
    
    # Refresh details
    refresh_type = Column(String(50), nullable=False)  # automatic, manual, expired
    refresh_status = Column(String(50), nullable=False)  # success, failed, partial
    
    # Timing
    refresh_started_at = Column(DateTime, nullable=False)
    refresh_completed_at = Column(DateTime, nullable=True)
    
    # Results
    new_expires_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    refresh_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self) -> str:
        return f"<TokenRefreshLog(id={self.id}, token_id={self.service_token_id}, status={self.refresh_status})>"
    
    @property
    def is_successful(self) -> bool:
        """Check if refresh was successful."""
        return self.refresh_status == 'success'
    
    @property
    def is_failed(self) -> bool:
        """Check if refresh failed."""
        return self.refresh_status == 'failed'
    
    @property
    def refresh_duration_seconds(self) -> Optional[float]:
        """Calculate refresh duration in seconds."""
        if self.refresh_completed_at is None:
            return None
        
        delta = self.refresh_completed_at - self.refresh_started_at
        return delta.total_seconds()
    
    @classmethod
    def create_refresh_log(
        cls,
        service_token_id: str,
        refresh_type: str = 'automatic',
        refresh_metadata: Optional[Dict[str, Any]] = None
    ) -> "TokenRefreshLog":
        """
        Create a new token refresh log entry.
        
        Args:
            service_token_id: Service token identifier
            refresh_type: Type of refresh (automatic, manual, expired)
            refresh_metadata: Additional refresh metadata
            
        Returns:
            New TokenRefreshLog instance
        """
        return cls(
            service_token_id=service_token_id,
            refresh_type=refresh_type,
            refresh_status='started',
            refresh_started_at=datetime.utcnow(),
            refresh_metadata=refresh_metadata or {}
        )
    
    def mark_success(self, new_expires_at: Optional[datetime] = None) -> None:
        """Mark refresh as successful."""
        self.refresh_status = 'success'
        self.refresh_completed_at = datetime.utcnow()
        if new_expires_at:
            self.new_expires_at = new_expires_at
    
    def mark_failed(self, error_message: str) -> None:
        """Mark refresh as failed."""
        self.refresh_status = 'failed'
        self.refresh_completed_at = datetime.utcnow()
        self.error_message = error_message
