"""
Pytest configuration and shared fixtures for Oprina backend testing
"""
import pytest
import pytest_asyncio
import asyncio
import os
import sys
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from memory.chat_history import get_chat_history
from services.logging.logger import setup_logger
from agents.voice.agent import VoiceAgent
from agents.voice.sub_agents.coordinator.agent import CoordinatorAgent
from agents.voice.sub_agents.coordinator.sub_agents.email.agent import EmailAgent
from agents.voice.sub_agents.coordinator.sub_agents.calendar.agent import CalendarAgent
from mcp_server.client import MCPClient

# Configure for test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["SESSION_SERVICE_TYPE"] = "inmemory"
os.environ["MEMORY_SERVICE_TYPE"] = "inmemory"
os.environ["MOCK_GMAIL_API"] = "true"
os.environ["MOCK_CALENDAR_API"] = "true"

# Setup test logger
logger = setup_logger("test", console_output=True)
logger.info("Initializing test environment")

# Patch InMemorySessionService for test compatibility
try:
    from google.adk.sessions import InMemorySessionService
    from unittest.mock import AsyncMock, MagicMock

    class PatchedInMemorySessionService(InMemorySessionService):
        async def get_session(self, user_id, session_id):
            # Return a MagicMock session with a .state dict
            session = MagicMock()
            session.state = {}
            session.id = session_id
            return session

    # Patch the class in the module
    sys.modules["google.adk.sessions"].InMemorySessionService = PatchedInMemorySessionService
except ImportError:
    pass

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def test_memory_manager():
    """Memory Manager for testing"""
    from memory.adk_memory_manager import get_adk_memory_manager
    manager = get_adk_memory_manager()
    yield manager
    # Cleanup after test

@pytest_asyncio.fixture
async def test_voice_agent():
    mcp_client = MCPClient(host="localhost", port=8765)
    await mcp_client.connect()
    agent = VoiceAgent(mcp_client)
    return agent

@pytest_asyncio.fixture
async def test_coordinator_agent():
    mcp_client = MCPClient(host="localhost", port=8765)
    await mcp_client.connect()
    agent = CoordinatorAgent(mcp_client)
    return agent

@pytest_asyncio.fixture
async def test_email_agent():
    mcp_client = MCPClient(host="localhost", port=8765)
    await mcp_client.connect()
    agent = EmailAgent(mcp_client)
    return agent

@pytest_asyncio.fixture
async def test_calendar_agent():
    mcp_client = MCPClient(host="localhost", port=8765)
    await mcp_client.connect()
    agent = CalendarAgent(mcp_client)
    return agent

@pytest.fixture
def mock_tool_context():
    """Mock tool context for testing tools"""
    class MockSession:
        def __init__(self):
            self.state = {
                "user:id": "test_user_123",
                "user:name": "Test User",
                "user:email": "test@example.com",
                "user:gmail_connected": True,
                "user:calendar_connected": True,
                "user:preferences": {
                    "summary_detail": "moderate",
                    "reply_style": "professional"
                }
            }
    
    class MockToolContext:
        def __init__(self):
            self.session = MockSession()
            self.invocation_id = "test_invocation_123"
    
    return MockToolContext()

@pytest.fixture
def mock_gmail_service():
    """Mock Gmail service for testing"""
    mock_service = Mock()
    mock_service.users().getProfile().execute.return_value = {
        "emailAddress": "test@example.com",
        "messagesTotal": 100
    }
    mock_service.users().messages().list().execute.return_value = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"}
        ]
    }
    return mock_service

@pytest.fixture
def mock_calendar_service():
    """Mock Calendar service for testing"""
    mock_service = Mock()
    mock_service.calendarList().list().execute.return_value = {
        "items": [
            {"id": "primary", "summary": "Primary Calendar", "primary": True}
        ]
    }
    return mock_service

@pytest_asyncio.fixture
async def test_session_data():
    """Test session data"""
    return {
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "app_name": "oprina_test"
    }

@pytest.fixture
def test_audio_data():
    """Mock audio data for voice testing"""
    return b"fake_audio_data_for_testing" * 100

@pytest.fixture
def sample_email_content():
    """Sample email content for testing"""
    return """
    Hi John,
    
    I hope this email finds you well. I wanted to follow up on our meeting yesterday 
    about the Q3 marketing campaign. We discussed budget allocation and timeline.
    
    Can you please send me the revised budget by Friday? We need to finalize this 
    before the board meeting next week.
    
    Thanks!
    Sarah
    """

@pytest.fixture
def sample_calendar_event():
    """Sample calendar event for testing"""
    return {
        "summary": "Team Meeting",
        "start": {"dateTime": "2024-12-01T14:00:00Z"},
        "end": {"dateTime": "2024-12-01T15:00:00Z"},
        "location": "Conference Room A",
        "description": "Weekly team sync"
    }

@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing"""
    mock_client = AsyncMock()
    
    # Mock Gmail responses
    mock_client.list_gmail_messages.return_value = {
        "status": "success",
        "data": [
            {
                "id": "msg1",
                "threadId": "thread1",
                "snippet": "Test email snippet",
                "from": "sender@example.com",
                "to": "test@example.com",
                "subject": "Test Subject",
                "date": "2024-01-01T12:00:00Z",
                "is_unread": True
            }
        ]
    }
    
    mock_client.get_gmail_message.return_value = {
        "status": "success",
        "data": {
            "id": "msg1",
            "threadId": "thread1",
            "from": "sender@example.com",
            "to": "test@example.com",
            "subject": "Test Subject",
            "body": "Test email body",
            "date": "2024-01-01T12:00:00Z",
            "is_unread": True
        }
    }
    
    mock_client.send_gmail_message.return_value = {
        "status": "success",
        "data": {
            "id": "sent_msg1",
            "threadId": "thread1"
        }
    }
    
    # Mock Calendar responses
    mock_client.list_calendar_events.return_value = {
        "status": "success",
        "data": [
            {
                "id": "event1",
                "summary": "Team Meeting",
                "start": {"dateTime": "2024-12-01T14:00:00Z"},
                "end": {"dateTime": "2024-12-01T15:00:00Z"},
                "location": "Conference Room A",
                "description": "Weekly team sync"
            }
        ]
    }
    
    mock_client.get_calendar_event.return_value = {
        "status": "success",
        "data": {
            "id": "event1",
            "summary": "Team Meeting",
            "start": {"dateTime": "2024-12-01T14:00:00Z"},
            "end": {"dateTime": "2024-12-01T15:00:00Z"},
            "location": "Conference Room A",
            "description": "Weekly team sync"
        }
    }
    
    mock_client.create_calendar_event.return_value = {
        "status": "success",
        "data": {
            "id": "new_event1",
            "summary": "New Team Meeting",
            "start": {"dateTime": "2024-12-02T14:00:00Z"},
            "end": {"dateTime": "2024-12-02T15:00:00Z"},
            "location": "Conference Room B",
            "description": "New team sync"
        }
    }
    
    return mock_client

@pytest_asyncio.fixture
async def adk_runner():
    """Mock ADK runner for testing"""
    from unittest.mock import AsyncMock, MagicMock
    
    # Create a mock runner
    mock_runner = MagicMock()
    
    # Add session_service
    mock_session_service = MagicMock()
    mock_session_service.get_session = AsyncMock(return_value=MagicMock())
    mock_runner.session_service = mock_session_service
    
    # Add memory_service
    mock_memory_service = MagicMock()
    mock_memory_service.search = AsyncMock(return_value=[])
    mock_runner.memory_service = mock_memory_service
    
    # Add run method
    mock_runner.run = AsyncMock(return_value=[{"content": "Test response"}])
    
    return mock_runner

# Test database cleanup
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Automatically cleanup test data after each test"""
    yield
    # Add cleanup logic here if needed
    pass 