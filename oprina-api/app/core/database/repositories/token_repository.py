"""
Token repository for Oprina API.

This module handles database operations for service tokens including
OAuth tokens, API keys, and token refresh operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.database.token import ServiceToken, TokenRefreshLog
from app.utils.errors import DatabaseError, TokenError
from app.utils.logging import get_logger
from app.utils.encryption import encrypt_token, decrypt_token

logger = get_logger(__name__)


class TokenRepository:
    """Repository for service token database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_service_token(
        self,
        user_id: str,
        service_type: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        id_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        scope: Optional[str] = None,
        provider_user_id: Optional[str] = None,
        provider_email: Optional[str] = None,
        service_name: Optional[str] = None,
        token_metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceToken:
        """
        Create a new service token with encrypted storage.
        
        Args:
            user_id: User identifier
            service_type: Type of service (gmail, calendar, etc.)
            provider: OAuth provider (google, microsoft, etc.)
            access_token: Access token to encrypt and store
            refresh_token: Refresh token to encrypt and store
            id_token: ID token to encrypt and store
            expires_at: When the access token expires
            scope: Granted OAuth scopes
            provider_user_id: Provider's user ID
            provider_email: Email from provider
            service_name: Human-readable service name
            token_metadata: Additional token metadata
            
        Returns:
            Created ServiceToken instance
        """
        try:
            # Encrypt tokens before storage
            access_token_encrypted = encrypt_token(access_token)
            refresh_token_encrypted = encrypt_token(refresh_token) if refresh_token else None
            id_token_encrypted = encrypt_token(id_token) if id_token else None
            
            # Create service token
            service_token = ServiceToken.create_oauth_token(
                user_id=user_id,
                service_type=service_type,
                provider=provider,
                access_token_encrypted=access_token_encrypted,
                refresh_token_encrypted=refresh_token_encrypted,
                expires_at=expires_at,
                scope=scope,
                provider_user_id=provider_user_id,
                provider_email=provider_email
            )
            
            if id_token_encrypted:
                service_token.id_token_encrypted = id_token_encrypted
            
            if service_name:
                service_token.service_name = service_name
                
            if token_metadata:
                service_token.token_metadata = token_metadata
            
            self.db.add(service_token)
            self.db.commit()
            self.db.refresh(service_token)
            
            logger.info(f"Created service token for user {user_id}, service {service_type}, provider {provider}")
            return service_token
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create service token: {str(e)}")
            raise DatabaseError(f"Failed to create service token: {str(e)}")
    
    async def get_service_token(self, token_id: str) -> Optional[ServiceToken]:
        """Get a service token by ID."""
        try:
            return self.db.query(ServiceToken).filter(ServiceToken.id == token_id).first()
        except Exception as e:
            logger.error(f"Failed to get service token {token_id}: {str(e)}")
            raise DatabaseError(f"Failed to get service token: {str(e)}")
    
    async def get_user_service_tokens(
        self,
        user_id: str,
        service_type: Optional[str] = None,
        provider: Optional[str] = None,
        active_only: bool = True
    ) -> List[ServiceToken]:
        """Get all service tokens for a user."""
        try:
            query = self.db.query(ServiceToken).filter(ServiceToken.user_id == user_id)
            
            if service_type:
                query = query.filter(ServiceToken.service_type == service_type)
            
            if provider:
                query = query.filter(ServiceToken.provider == provider)
            
            if active_only:
                query = query.filter(
                    and_(
                        ServiceToken.is_active == True,
                        ServiceToken.is_revoked == False
                    )
                )
            
            return query.order_by(desc(ServiceToken.created_at)).all()
            
        except Exception as e:
            logger.error(f"Failed to get user service tokens: {str(e)}")
            raise DatabaseError(f"Failed to get user service tokens: {str(e)}")
    
    async def get_active_token(
        self,
        user_id: str,
        service_type: str,
        provider: Optional[str] = None  # Auto-detect provider based on service_type
    ) -> Optional[ServiceToken]:
        """Get the active token for a specific user, service, and provider."""
        try:
            # Auto-detect provider based on service_type if not specified
            if provider is None:
                if service_type in ["gmail", "calendar"]:
                    provider = service_type  # Use service_type as provider name
                else:
                    provider = "google"  # Default fallback
            
            return self.db.query(ServiceToken).filter(
                and_(
                    ServiceToken.user_id == user_id,
                    ServiceToken.service_type == service_type,
                    ServiceToken.provider == provider,
                    ServiceToken.is_active == True,
                    ServiceToken.is_revoked == False
                )
            ).first()
            
        except Exception as e:
            logger.error(f"Failed to get active token: {str(e)}")
            raise DatabaseError(f"Failed to get active token: {str(e)}")
    
    async def get_active_token_data(
        self,
        user_id: str,
        service_type: str,
        provider: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get active token with decrypted access token as dict."""
        try:
            token = await self.get_active_token(user_id, service_type, provider)
            if not token or not token.is_valid:
                return None
            
            # Decrypt and return token data
            from app.utils.encryption import decrypt_token
            
            # Mark as used
            token.mark_used()
            self.db.commit()
            
            return {
                "access_token": decrypt_token(token.access_token_encrypted),
                "expires_at": token.expires_at,
                "service": service_type,
                "user_id": user_id,
                "provider": token.provider,
                "scope": token.scope
            }
            
        except Exception as e:
            logger.error(f"Failed to get active token data: {str(e)}")
            raise DatabaseError(f"Failed to get active token data: {str(e)}")
    
    async def is_service_connected(
        self,
        user_id: str,
        service_type: str,
        provider: Optional[str] = None
    ) -> bool:
        """Check if user has an active token for the specified service."""
        try:
            token = await self.get_active_token(user_id, service_type, provider)
            return token is not None and token.is_valid
            
        except Exception as e:
            logger.error(f"Failed to check service connection: {str(e)}")
            return False
    
    async def get_decrypted_access_token(self, token_id: str) -> Optional[str]:
        """Get and decrypt the access token."""
        try:
            service_token = await self.get_service_token(token_id)
            if not service_token:
                return None
            
            if not service_token.is_valid:
                logger.warning(f"Attempted to decrypt invalid token {token_id}")
                return None
            
            # Mark token as used
            service_token.mark_used()
            self.db.commit()
            
            return decrypt_token(service_token.access_token_encrypted)
            
        except Exception as e:
            logger.error(f"Failed to decrypt access token {token_id}: {str(e)}")
            raise TokenError(f"Failed to decrypt access token: {str(e)}")
    
    async def get_decrypted_refresh_token(self, token_id: str) -> Optional[str]:
        """Get and decrypt the refresh token."""
        try:
            service_token = await self.get_service_token(token_id)
            if not service_token or not service_token.refresh_token_encrypted:
                return None
            
            if not service_token.is_valid:
                logger.warning(f"Attempted to decrypt refresh token for invalid token {token_id}")
                return None
            
            return decrypt_token(service_token.refresh_token_encrypted)
            
        except Exception as e:
            logger.error(f"Failed to decrypt refresh token {token_id}: {str(e)}")
            raise TokenError(f"Failed to decrypt refresh token: {str(e)}")
    
    async def update_token(
        self,
        token_id: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        scope: Optional[str] = None
    ) -> Optional[ServiceToken]:
        """Update a service token with new values."""
        try:
            service_token = await self.get_service_token(token_id)
            if not service_token:
                return None
            
            # Update encrypted tokens if provided
            if access_token:
                service_token.access_token_encrypted = encrypt_token(access_token)
            
            if refresh_token:
                service_token.refresh_token_encrypted = encrypt_token(refresh_token)
            
            if expires_at:
                service_token.update_expiry(expires_at)
            
            if scope:
                service_token.update_scope(scope)
            
            self.db.commit()
            self.db.refresh(service_token)
            
            logger.info(f"Updated service token {token_id}")
            return service_token
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update service token {token_id}: {str(e)}")
            raise DatabaseError(f"Failed to update service token: {str(e)}")
    
    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a service token."""
        try:
            service_token = await self.get_service_token(token_id)
            if not service_token:
                return False
            
            service_token.revoke()
            self.db.commit()
            
            logger.info(f"Revoked service token {token_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to revoke service token {token_id}: {str(e)}")
            raise DatabaseError(f"Failed to revoke service token: {str(e)}")
    
    async def revoke_user_tokens(
        self,
        user_id: str,
        service_type: Optional[str] = None,
        provider: Optional[str] = None
    ) -> int:
        """Revoke all tokens for a user, optionally filtered by service/provider."""
        try:
            query = self.db.query(ServiceToken).filter(
                and_(
                    ServiceToken.user_id == user_id,
                    ServiceToken.is_active == True,
                    ServiceToken.is_revoked == False
                )
            )
            
            if service_type:
                query = query.filter(ServiceToken.service_type == service_type)
            
            if provider:
                query = query.filter(ServiceToken.provider == provider)
            
            tokens = query.all()
            revoked_count = 0
            
            for token in tokens:
                token.revoke()
                revoked_count += 1
            
            self.db.commit()
            
            logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            return revoked_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to revoke user tokens: {str(e)}")
            raise DatabaseError(f"Failed to revoke user tokens: {str(e)}")
    
    async def get_expiring_tokens(self, minutes_ahead: int = 30) -> List[ServiceToken]:
        """Get tokens that will expire within the specified minutes."""
        try:
            expiry_threshold = datetime.utcnow() + timedelta(minutes=minutes_ahead)
            
            return self.db.query(ServiceToken).filter(
                and_(
                    ServiceToken.is_active == True,
                    ServiceToken.is_revoked == False,
                    ServiceToken.expires_at.isnot(None),
                    ServiceToken.expires_at <= expiry_threshold,
                    ServiceToken.refresh_token_encrypted.isnot(None)
                )
            ).all()
            
        except Exception as e:
            logger.error(f"Failed to get expiring tokens: {str(e)}")
            raise DatabaseError(f"Failed to get expiring tokens: {str(e)}")
    
    async def cleanup_expired_tokens(self) -> int:
        """Mark expired tokens as inactive and return count."""
        try:
            expired_tokens = self.db.query(ServiceToken).filter(
                and_(
                    ServiceToken.is_active == True,
                    ServiceToken.expires_at.isnot(None),
                    ServiceToken.expires_at < datetime.utcnow()
                )
            ).all()
            
            cleanup_count = 0
            for token in expired_tokens:
                token.deactivate()
                cleanup_count += 1
            
            if cleanup_count > 0:
                self.db.commit()
                logger.info(f"Cleaned up {cleanup_count} expired tokens")
            
            return cleanup_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup expired tokens: {str(e)}")
            raise DatabaseError(f"Failed to cleanup expired tokens: {str(e)}")
    
    # Token Refresh Log Operations
    
    async def create_refresh_log(
        self,
        service_token_id: str,
        refresh_type: str = 'automatic',
        refresh_metadata: Optional[Dict[str, Any]] = None
    ) -> TokenRefreshLog:
        """Create a new token refresh log entry."""
        try:
            refresh_log = TokenRefreshLog.create_refresh_log(
                service_token_id=service_token_id,
                refresh_type=refresh_type,
                refresh_metadata=refresh_metadata
            )
            
            self.db.add(refresh_log)
            self.db.commit()
            self.db.refresh(refresh_log)
            
            return refresh_log
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create refresh log: {str(e)}")
            raise DatabaseError(f"Failed to create refresh log: {str(e)}")
    
    async def update_refresh_log(
        self,
        log_id: str,
        success: bool,
        new_expires_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ) -> Optional[TokenRefreshLog]:
        """Update a refresh log with results."""
        try:
            refresh_log = self.db.query(TokenRefreshLog).filter(
                TokenRefreshLog.id == log_id
            ).first()
            
            if not refresh_log:
                return None
            
            if success:
                refresh_log.mark_success(new_expires_at)
            else:
                refresh_log.mark_failed(error_message or "Unknown error")
            
            self.db.commit()
            self.db.refresh(refresh_log)
            
            return refresh_log
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update refresh log {log_id}: {str(e)}")
            raise DatabaseError(f"Failed to update refresh log: {str(e)}")
    
    async def get_token_refresh_history(
        self,
        service_token_id: str,
        limit: int = 10
    ) -> List[TokenRefreshLog]:
        """Get refresh history for a token."""
        try:
            return self.db.query(TokenRefreshLog).filter(
                TokenRefreshLog.service_token_id == service_token_id
            ).order_by(desc(TokenRefreshLog.created_at)).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to get refresh history: {str(e)}")
            raise DatabaseError(f"Failed to get refresh history: {str(e)}")
    
    async def delete_token(self, token_id: str) -> bool:
        """Permanently delete a service token."""
        try:
            service_token = await self.get_service_token(token_id)
            if not service_token:
                return False
            
            # Delete associated refresh logs first
            self.db.query(TokenRefreshLog).filter(
                TokenRefreshLog.service_token_id == token_id
            ).delete()
            
            # Delete the token
            self.db.delete(service_token)
            self.db.commit()
            
            logger.info(f"Deleted service token {token_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete service token {token_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete service token: {str(e)}")


def get_token_repository(db: Session) -> TokenRepository:
    """Get a token repository instance."""
    return TokenRepository(db)
