"""
Pytest configuration and shared fixtures for Oprina backend testing
"""
import pytest
import pytest_asyncio
import asyncio
import os
import sys
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import settings
from memory.chat_history import get_chat_history
from services.logging.logger import setup_logger
from agents.voice.agent import ProcessableVoiceAgent
from agents.voice.sub_agents.coordinator.agent import ProcessableCoordinatorAgent
from agents.voice.sub_agents.coordinator.sub_agents.email.agent import EmailAgent, ProcessableEmailAgent
from agents.voice.sub_agents.coordinator.sub_agents.calendar.agent import CalendarAgent, ProcessableCalendarAgent
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

# Import agent classes
from agents.voice.agent import ProcessableVoiceAgent
from agents.voice.sub_agents.coordinator.agent import ProcessableCoordinatorAgent
from agents.voice.sub_agents.coordinator.sub_agents.email.agent import ProcessableEmailAgent
from agents.voice.sub_agents.coordinator.sub_agents.calendar.agent import ProcessableCalendarAgent
from agents.voice.sub_agents.coordinator.sub_agents.content.agent import ProcessableContentAgent

# Import ADK components
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
import google.adk.sessions as adk_sessions

# Define our patched session service
class PatchedInMemorySessionService:
    def __init__(self):
        self.sessions = {}
    
    async def get_session(self, user_id, session_id=None, app_name=None):
        if session_id is None:
            # If no session_id provided, return first session for user_id
            for (uid, sid), session in self.sessions.items():
                if uid == user_id:
                    return session
            return None
            
        if (user_id, session_id) not in self.sessions:
            self.sessions[(user_id, session_id)] = MagicMock()
            self.sessions[(user_id, session_id)].user_id = user_id
            self.sessions[(user_id, session_id)].session_id = session_id
            self.sessions[(user_id, session_id)].state = {}
        
        return self.sessions[(user_id, session_id)]
    
    async def create_session(self, user_id, state=None, session_id=None):
        if session_id is None:
            session_id = str(uuid.uuid4())
        session = MagicMock()
        session.user_id = user_id
        session.session_id = session_id
        session.state = state or {}
        self.sessions[(user_id, session_id)] = session
        return session
    
    async def save_session(self, session):
        if hasattr(session, 'user_id') and hasattr(session, 'session_id'):
            self.sessions[(session.user_id, session.session_id)] = session
    
    async def get_session_state(self, user_id, session_id):
        session = await self.get_session(user_id, session_id)
        return session.state if session else {}
    
    async def set_session_state(self, user_id, session_id, state):
        session = await self.get_session(user_id, session_id)
        if session:
            session.state = state
            await self.save_session(session)
            return True
        return False
        
    async def list_sessions(self, app_name, user_id):
        # Mock implementation for list_sessions
        result = MagicMock()
        result.sessions = []
        for (uid, sid), session in self.sessions.items():
            if uid == user_id:
                session_info = MagicMock()
                session_info.id = sid
                result.sessions.append(session_info)
        return result

# Define our patched memory service
class PatchedInMemoryMemoryService:
    def __init__(self):
        self.memories = {}
    
    async def store(self, user_id, session_id, data):
        key = (user_id, session_id)
        if key not in self.memories:
            self.memories[key] = {}
        self.memories[key].update(data)
        return True
    
    async def retrieve(self, user_id, session_id):
        key = (user_id, session_id)
        return self.memories.get(key, {})

# Patch agent factory functions to always return test doubles
import agents.voice.sub_agents.coordinator.agent as coordinator_module
import agents.voice.sub_agents.coordinator.sub_agents.email.agent as email_module
import agents.voice.sub_agents.coordinator.sub_agents.calendar.agent as calendar_module
from unittest.mock import AsyncMock

class TestDoubleEmailAgent(ProcessableEmailAgent):
    session_service: Any = None
    memory_service: Any = None
    def __init__(self, *args, **kwargs):
        super().__init__(name="test_email_agent", *args, **kwargs)
        self.session_service = PatchedInMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        
    async def process(self, event, app_name="test_app", session_service=None, memory_service=None):
        return {"content": "Email agent processed event"}

class TestDoubleCalendarAgent(ProcessableCalendarAgent):
    session_service: Any = None
    memory_service: Any = None
    def __init__(self, *args, **kwargs):
        super().__init__(name="test_calendar_agent", *args, **kwargs)
        self.session_service = PatchedInMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        
    async def process(self, event, app_name="test_app", session_service=None, memory_service=None):
        return {"content": "Calendar agent processed event"}

class TestDoubleCoordinatorAgent(ProcessableCoordinatorAgent):
    session_service: Any = None
    memory_service: Any = None
    email_agent: Any = None
    content_agent: Any = None
    calendar_agent: Any = None
    def __init__(self, *args, **kwargs):
        super().__init__(name="test_coordinator_agent", *args, **kwargs)
        self.email_agent = TestDoubleEmailAgent()
        self.content_agent = AsyncMock()
        self.calendar_agent = TestDoubleCalendarAgent()
        self.session_service = PatchedInMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        
    async def process(self, event, app_name="test_app", session_service=None, memory_service=None):
        content = event.get("content", "").lower()
        if "email" in content or "gmail" in content or "inbox" in content:
            return {"content": "I'll help you with email"}
        elif "calendar" in content or "schedule" in content or "meeting" in content:
            return {"content": "I'll help you with calendar"}
        elif "summarize" in content or "analyze" in content or "content" in content:
            return {"content": "Content handled"}
        else:
            return {"content": "I'll help you with that"}

# Add process method to LlmAgent for testing
from google.adk.agents import LlmAgent
original_init = LlmAgent.__init__

def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    if not hasattr(self, 'process'):
        async def process(self, event):
            return {"content": f"LlmAgent {self.name} processed event: {event}"}
        self.process = process.__get__(self)

# Apply the patch
patch('google.adk.agents.LlmAgent.__init__', patched_init).start()

# Create test double classes for agents
# Removed duplicate class definitions

import pytest
@pytest.fixture(autouse=True, scope='function')
def patch_agent_factories(monkeypatch):
    monkeypatch.setattr(coordinator_module, 'create_coordinator_agent', lambda: TestDoubleCoordinatorAgent())
    monkeypatch.setattr(email_module, 'create_email_agent', lambda: TestDoubleEmailAgent())
    monkeypatch.setattr(calendar_module, 'create_calendar_agent', lambda: TestDoubleCalendarAgent())

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def test_memory_manager():
    """Memory Manager for testing"""
    from memory.adk_memory_manager import OprinaMemoryManager
    manager = OprinaMemoryManager()
    manager._session_service = shared_session_service
    manager._memory_service = shared_memory_service
    manager.app_name = "test_app"
    yield manager
    # Cleanup after test

@pytest.fixture(autouse=True)
def patch_inmemory_session_service(monkeypatch):
    import google.adk.sessions as adk_sessions
    import google.adk.memory as adk_memory
    
    # Create instances of our patched services
    patched_session_service = PatchedInMemorySessionService()
    patched_memory_service = PatchedInMemoryMemoryService()
    
    # Patch the classes
    monkeypatch.setattr(adk_sessions, 'InMemorySessionService', PatchedInMemorySessionService)
    monkeypatch.setattr(adk_memory, 'InMemoryMemoryService', PatchedInMemoryMemoryService)
    
    # Also patch the global shared services
    global shared_session_service, shared_memory_service
    shared_session_service = patched_session_service
    shared_memory_service = patched_memory_service
    
    # Return the patched services for use in tests
    return patched_session_service, patched_memory_service

@pytest_asyncio.fixture
async def adk_runner():
    memory_service = shared_memory_service
    mcp_client = MagicMock()
    root_agent = TestDoubleCoordinatorAgent()
    runner = Runner(
        agent=root_agent,
        app_name="test_app",
        session_service=shared_session_service,
        memory_service=memory_service
    )
    yield runner

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
                "subject": "Test Subject",
                "date": "2024-01-01T12:00:00Z"
            }
        ]
    }
    
    mock_client.get_gmail_message.return_value = {
        "status": "success",
        "data": {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test email snippet",
            "from": "sender@example.com",
            "subject": "Test Subject",
            "date": "2024-01-01T12:00:00Z",
            "body": "Test email body"
        }
    }
    
    mock_client.send_gmail_message.return_value = {
        "status": "success",
        "data": {
            "id": "msg2",
            "threadId": "thread2"
        }
    }
    
    # Mock Calendar responses
    mock_client.list_calendar_events.return_value = {
        "status": "success",
        "data": [
            {
                "id": "event1",
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T14:00:00Z"},
                "end": {"dateTime": "2024-01-01T15:00:00Z"}
            }
        ]
    }
    
    mock_client.create_calendar_event.return_value = {
        "status": "success",
        "data": {
            "id": "event2",
            "summary": "New Test Event",
            "start": {"dateTime": "2024-01-02T14:00:00Z"},
            "end": {"dateTime": "2024-01-02T15:00:00Z"}
        }
    }
    
    # Mock Content responses
    mock_client.summarize_text.return_value = {
        "status": "success",
        "data": {
            "summary": "This is a summary of the provided text."
        }
    }
    
    # Mock the connect method to avoid actual WebSocket connection
    mock_client.connect = AsyncMock()
    
    return mock_client

# Test database cleanup
@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """Automatically cleanup test data after each test"""
    yield
    # Add cleanup logic here if needed
    pass 

@pytest.fixture
def test_voice_agent(test_coordinator_agent):
    agent = MagicMock(spec=ProcessableVoiceAgent)
    agent.name = "test_voice_agent"
    agent.mcp_client = MagicMock()
    async def process(event, *args, **kwargs):
        # Delegate to coordinator if present
        if test_coordinator_agent:
            return await test_coordinator_agent.process(event)
        return {"content": "I heard you say something"}
    agent.process = process
    agent.process_audio = AsyncMock(return_value={"content": "I heard you say something"})
    return agent

@pytest.fixture
def test_email_agent():
    agent = MagicMock(spec=ProcessableEmailAgent)
    agent.name = "test_email_agent"
    agent.mcp_client = MagicMock()
    async def process(event, *args, **kwargs):
        return {"content": "Email handled"}
    agent.process = process
    return agent

@pytest.fixture
def test_calendar_agent():
    agent = MagicMock(spec=ProcessableCalendarAgent)
    agent.name = "test_calendar_agent"
    agent.mcp_client = MagicMock()
    async def process(event, *args, **kwargs):
        return {"content": "Calendar handled"}
    agent.process = process
    return agent

@pytest.fixture
def test_coordinator_agent(test_email_agent, test_calendar_agent):
    agent = MagicMock(spec=ProcessableCoordinatorAgent)
    agent.name = "test_coordinator_agent"
    agent.mcp_client = MagicMock()
    async def process(event, *args, **kwargs):
        content = event.get("content", "").lower()
        if "email" in content or "gmail" in content or "inbox" in content:
            return await test_email_agent.process(event)
        elif "calendar" in content or "schedule" in content or "meeting" in content:
            return await test_calendar_agent.process(event)
        return {"content": "I'll help you with that"}
    agent.process = process
    return agent 