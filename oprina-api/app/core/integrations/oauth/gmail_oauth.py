"""
Gmail OAuth integration for Oprina API.

This module provides Gmail-specific OAuth configuration and integration
with the main OAuth service.
"""

from app.core.services.oauth_service import GoogleOAuthProvider
from app.config import get_settings

settings = get_settings()

# Gmail API scopes - comprehensive permissions
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',      # Read emails
    'https://www.googleapis.com/auth/gmail.send',          # Send emails
    'https://www.googleapis.com/auth/gmail.modify',        # Modify emails (labels, etc.)
    'https://www.googleapis.com/auth/gmail.compose',       # Compose emails
    'https://www.googleapis.com/auth/gmail.labels',        # Manage labels
    'https://www.googleapis.com/auth/gmail.metadata'       # Access email metadata
]


class GmailOAuthProvider(GoogleOAuthProvider):
    """Gmail-specific OAuth provider with enhanced configuration."""
    
    def __init__(self):
        super().__init__(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=f"{settings.BACKEND_URL}/api/v1/oauth/callback/google"
        )
        
        # Override with Gmail-specific scopes
        self.scope = " ".join(GMAIL_SCOPES)
        self.service_type = "gmail"


def get_gmail_oauth_provider() -> GmailOAuthProvider:
    """Get configured Gmail OAuth provider."""
    return GmailOAuthProvider()
