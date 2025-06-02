"""
Integration tests for Google Cloud services.

This module contains integration tests for:
- Gmail API Integration
- Calendar API Integration
- Speech Services Integration
- Authentication Flow Integration
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from services.google_cloud.gmail_auth import GmailAuthService
from services.google_cloud.calendar_auth import CalendarAuthService
from services.google_cloud.speech_services import GoogleCloudSpeechServices
from services.google_cloud.auth_utils import refresh_credentials

# Test data
TEST_CREDENTIALS = {
    "token": "test_access_token",
    "refresh_token": "test_refresh_token",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "test_client_id",
    "client_secret": "test_client_secret",
    "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
}

TEST_MESSAGE = {
    "id": "test_message_id",
    "threadId": "test_thread_id",
    "labelIds": ["INBOX"],
    "snippet": "Test message snippet",
    "payload": {
        "headers": [
            {"name": "From", "value": "test@example.com"},
            {"name": "Subject", "value": "Test Subject"}
        ]
    }
}

TEST_EVENT = {
    "id": "test_event_id",
    "summary": "Test Event",
    "start": {"dateTime": datetime.now().isoformat()},
    "end": {"dateTime": (datetime.now() + timedelta(hours=1)).isoformat()}
}

# Fixtures
@pytest.fixture
def gmail_service():
    """Fixture for GmailAuthService"""
    service = GmailAuthService()
    service.service = MagicMock()
    return service

@pytest.fixture
def calendar_service():
    """Fixture for CalendarAuthService"""
    service = CalendarAuthService()
    service.service = MagicMock()
    return service

@pytest.fixture
def speech_service():
    """Fixture for GoogleCloudSpeechServices"""
    with patch("services.google_cloud.speech_services.GoogleCloudSpeechServices._initialize_clients") as mock_init:
        service = GoogleCloudSpeechServices()
        service._stt_client = MagicMock()
        service._tts_client = MagicMock()
        return service

# Tests
@pytest.mark.asyncio
async def test_gmail_api_integration(gmail_service):
    """Test Gmail API integration using test_gmail_operations."""
    result = gmail_service.test_gmail_operations()
    assert isinstance(result, dict)
    assert result.get("overall_success") is True

@pytest.mark.asyncio
async def test_calendar_api_integration(calendar_service):
    """Test Calendar API integration using test_calendar_operations."""
    result = calendar_service.test_calendar_operations()
    assert isinstance(result, dict)
    assert result.get("overall_success") is True

@pytest.mark.asyncio
async def test_speech_services_integration(speech_service):
    """Test Speech Services integration"""
    # Mock the speech-to-text response
    mock_stt_response = MagicMock()
    mock_stt_response.results = [
        MagicMock(
            alternatives=[
                MagicMock(
                    transcript="Test transcript",
                    confidence=0.95,
                    words=[
                        MagicMock(
                            word="Test",
                            start_time=MagicMock(total_seconds=lambda: 0.0),
                            end_time=MagicMock(total_seconds=lambda: 0.5),
                            confidence=0.95
                        ),
                        MagicMock(
                            word="transcript",
                            start_time=MagicMock(total_seconds=lambda: 0.5),
                            end_time=MagicMock(total_seconds=lambda: 1.0),
                            confidence=0.95
                        )
                    ]
                )
            ]
        )
    ]
    speech_service._stt_client.recognize.return_value = mock_stt_response
    
    # Mock the text-to-speech response
    mock_tts_response = MagicMock()
    mock_tts_response.audio_content = b"test_audio_content"
    speech_service._tts_client.synthesize_speech.return_value = mock_tts_response
    
    # Test speech-to-text
    stt_result = await speech_service.speech_to_text(b"test_audio_data", config={})
    assert stt_result["transcript"] == "Test transcript"
    assert stt_result["confidence"] == 0.95
    assert len(stt_result["words"]) == 2
    
    # Test text-to-speech
    tts_result = await speech_service.text_to_speech("Test text", voice_config={})
    assert tts_result["audio_content"] == b"test_audio_content"
    assert tts_result["text"] == "Test text"

@pytest.mark.asyncio
async def test_auth_flow_integration():
    """Test Authentication Flow integration using refresh_credentials utility function."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = MagicMock(spec=Credentials)
    creds.expired = True
    creds.refresh_token = "dummy_refresh_token"
    # Patch creds.refresh to simulate successful refresh
    with patch.object(creds, "refresh", return_value=None) as mock_refresh:
        success, error = refresh_credentials(creds, service_name="gmail")
        assert success is True
        assert error is None
        mock_refresh.assert_called_once()

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"])) 