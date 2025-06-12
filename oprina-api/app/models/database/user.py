"""
User database entity model for Oprina API.

This module defines the SQLAlchemy User model that corresponds to the 'users' table
in the database schema. It includes all user-related fields and relationships.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class User(Base):
    """
    User entity representing a registered user in the system.
    
    This model handles user authentication, profile information,
    preferences, and OAuth integration status.
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # NULL for OAuth-only users
    
    # Profile information
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # User preferences
    preferences = Column(JSONB, default=dict, nullable=False)
    timezone = Column(String(50), default='UTC', nullable=False)
    language = Column(String(10), default='en', nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    
    # OAuth integration flags
    has_google_oauth = Column(Boolean, default=False, nullable=False)
    has_microsoft_oauth = Column(Boolean, default=False, nullable=False)
    
    # Activity tracking
    last_login_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    service_tokens = relationship("ServiceToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, active={self.is_active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for API responses."""
        return {
            'id': str(self.id),
            'email': self.email,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'preferences': self.preferences,
            'timezone': self.timezone,
            'language': self.language,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
            'has_google_oauth': self.has_google_oauth,
            'has_microsoft_oauth': self.has_microsoft_oauth,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def to_public_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary with only public information."""
        return {
            'id': str(self.id),
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'timezone': self.timezone,
            'language': self.language,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def full_name(self) -> str:
        """Get the user's display name or email as fallback."""
        return self.display_name or self.email.split('@')[0]
    
    @property
    def has_password(self) -> bool:
        """Check if user has a password set."""
        return self.password_hash is not None
    
    @property
    def has_oauth(self) -> bool:
        """Check if user has any OAuth integration."""
        return self.has_google_oauth or self.has_microsoft_oauth
    
    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update user preferences, merging with existing ones."""
        if self.preferences is None:
            self.preferences = {}
        
        # Merge preferences
        current_prefs = dict(self.preferences)
        current_prefs.update(new_preferences)
        self.preferences = current_prefs
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a specific preference value."""
        if self.preferences is None:
            return default
        return self.preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a specific preference value."""
        if self.preferences is None:
            self.preferences = {}
        
        prefs = dict(self.preferences)
        prefs[key] = value
        self.preferences = prefs
    
    def mark_login(self) -> None:
        """Mark user as logged in with current timestamp."""
        now = datetime.utcnow()
        self.last_login_at = now
        self.last_activity_at = now
    
    def mark_activity(self) -> None:
        """Mark user activity with current timestamp."""
        self.last_activity_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        """Mark user email as verified."""
        self.is_verified = True
        self.email_verified_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
    
    def enable_google_oauth(self) -> None:
        """Enable Google OAuth for this user."""
        self.has_google_oauth = True
    
    def disable_google_oauth(self) -> None:
        """Disable Google OAuth for this user."""
        self.has_google_oauth = False
    
    def enable_microsoft_oauth(self) -> None:
        """Enable Microsoft OAuth for this user."""
        self.has_microsoft_oauth = True
    
    def disable_microsoft_oauth(self) -> None:
        """Disable Microsoft OAuth for this user."""
        self.has_microsoft_oauth = False
    
    @classmethod
    def create_user(
        cls,
        email: str,
        password_hash: Optional[str] = None,
        display_name: Optional[str] = None,
        **kwargs
    ) -> "User":
        """
        Create a new user instance.
        
        Args:
            email: User email address
            password_hash: Hashed password (optional for OAuth users)
            display_name: User display name
            **kwargs: Additional user attributes
            
        Returns:
            New User instance
        """
        return cls(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            **kwargs
        )
    
    @classmethod
    def create_oauth_user(
        cls,
        email: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider: str = 'google',
        **kwargs
    ) -> "User":
        """
        Create a new OAuth user instance.
        
        Args:
            email: User email address
            display_name: User display name
            avatar_url: User avatar URL
            provider: OAuth provider ('google' or 'microsoft')
            **kwargs: Additional user attributes
            
        Returns:
            New User instance
        """
        oauth_flags = {}
        if provider == 'google':
            oauth_flags['has_google_oauth'] = True
        elif provider == 'microsoft':
            oauth_flags['has_microsoft_oauth'] = True
        
        return cls(
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            password_hash=None,  # OAuth users don't have passwords
            is_verified=True,  # OAuth users are pre-verified
            email_verified_at=datetime.utcnow(),
            **oauth_flags,
            **kwargs
        )
