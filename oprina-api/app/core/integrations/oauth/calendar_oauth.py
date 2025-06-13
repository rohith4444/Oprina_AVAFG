"""
Google Calendar OAuth integration for Oprina API.

This module provides Calendar-specific OAuth configuration and integration
with the main OAuth service.
"""

from app.core.services.oauth_service import GoogleOAuthProvider
from app.config import get_settings

settings = get_settings()

# Google Calendar API scopes - comprehensive permissions
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar',                    # Full calendar access
    'https://www.googleapis.com/auth/calendar.events',            # Manage events
    'https://www.googleapis.com/auth/calendar.events.readonly',   # Read events
    'https://www.googleapis.com/auth/calendar.readonly',          # Read calendar data
    'https://www.googleapis.com/auth/calendar.settings.readonly'  # Read calendar settings
]


class CalendarOAuthProvider(GoogleOAuthProvider):
    """Calendar-specific OAuth provider with enhanced configuration."""
    
    def __init__(self):
        super().__init__(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=f"{settings.BACKEND_URL}/api/v1/oauth/callback/google"
        )
        
        # Override with Calendar-specific scopes
        self.scope = " ".join(CALENDAR_SCOPES)
        self.service_type = "calendar"


def get_calendar_oauth_provider() -> CalendarOAuthProvider:
    """Get configured Calendar OAuth provider."""
    return CalendarOAuthProvider()
