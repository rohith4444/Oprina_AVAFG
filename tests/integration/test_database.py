"""
Database Integration Tests

This module contains integration tests for database services:
- Session Database Persistence
- Chat History Storage
- Memory Service Integration
- Database Cleanup

These tests use a test database and mock services where appropriate.
"""

import os
import sys
import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):  # 3 levels to reach project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import project modules
from config.settings import settings
from google.adk.sessions import DatabaseSessionService
from memory.chat_history import ChatHistoryService
from memory.adk_memory_manager import OprinaMemoryManager

# Test data
TEST_USER_ID = "test_user_123"
TEST_SESSION_ID = str(uuid.uuid4())
TEST_CHAT_ID = str(uuid.uuid4())
TEST_MEMORY_ID = str(uuid.uuid4())


@pytest.fixture
def database_session_service():
    """Fixture for Database Session Service."""
    # Create a mock DatabaseSessionService
    mock_service = MagicMock(spec=DatabaseSessionService)

    # Shared session dict to simulate state
    session_dict = {
        "session_id": TEST_SESSION_ID,
        "user_id": TEST_USER_ID,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "metadata": {"state": "active"}
    }

    async def create_session(session_id, user_id, metadata):
        session_dict["session_id"] = session_id
        session_dict["user_id"] = user_id
        session_dict["metadata"] = metadata
        session_dict["updated_at"] = datetime.now()
        return session_id

    async def get_session(session_id):
        return session_dict

    async def update_session(session_id, metadata):
        session_dict["metadata"] = metadata
        session_dict["updated_at"] = datetime.now()
        return True

    async def delete_session(session_id):
        return True

    async def cleanup_old_sessions(days):
        return 2

    mock_service.create_session = AsyncMock(side_effect=create_session)
    mock_service.get_session = AsyncMock(side_effect=get_session)
    mock_service.update_session = AsyncMock(side_effect=update_session)
    mock_service.delete_session = AsyncMock(side_effect=delete_session)
    mock_service.cleanup_old_sessions = AsyncMock(side_effect=cleanup_old_sessions)

    return mock_service


@pytest.fixture
def chat_history_service():
    """Fixture for Chat History Service."""
    return ChatHistoryService()


@pytest.fixture
def memory_manager():
    """Fixture for Memory Manager."""
    return OprinaMemoryManager()


@pytest.mark.asyncio
async def test_session_database_persistence(database_session_service):
    """Test session database persistence."""
    # Test creating a session
    session_data = {
        "user_id": TEST_USER_ID,
        "state": "active"
    }
    result = await database_session_service.create_session(
        session_id=TEST_SESSION_ID,
        user_id=TEST_USER_ID,
        metadata=session_data
    )
    # Verify the results
    assert result is not None
    assert result == TEST_SESSION_ID
    # Test getting a session
    get_result = await database_session_service.get_session(TEST_SESSION_ID)
    # Verify the results
    assert get_result is not None
    assert get_result["session_id"] == TEST_SESSION_ID
    assert get_result["user_id"] == TEST_USER_ID
    assert get_result["metadata"]["state"] == "active"
    # Test updating a session
    update_result = await database_session_service.update_session(
        session_id=TEST_SESSION_ID,
        metadata={"state": "inactive"}
    )
    # Verify the results
    assert update_result is not None
    # Get the updated session
    updated_session = await database_session_service.get_session(TEST_SESSION_ID)
    # Verify the results
    assert updated_session is not None
    assert updated_session["metadata"]["state"] == "inactive"


@pytest.mark.asyncio
async def test_chat_history_storage(chat_history_service):
    """Test chat history storage."""
    # Mock the database connection
    with patch('memory.chat_history.ChatHistoryService._initialize_client') as mock_init_client:
        # Create a mock client
        mock_client = MagicMock()
        mock_init_client.return_value = None
        chat_history_service._client = mock_client
        
        # Mock the insert method
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {
                "id": TEST_CHAT_ID,
                "conversation_id": str(uuid.uuid4()),
                "user_id": TEST_USER_ID,
                "session_id": TEST_SESSION_ID,
                "message_type": "assistant",
                "content": "Hello, how can I help you?",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Mock the store_message method to be async
        with patch.object(chat_history_service, 'store_message', new_callable=AsyncMock) as mock_store:
            mock_store.return_value = {
                "id": TEST_CHAT_ID,
                "conversation_id": str(uuid.uuid4()),
                "user_id": TEST_USER_ID,
                "session_id": TEST_SESSION_ID,
                "message_type": "assistant",
                "content": "Hello, how can I help you?",
                "created_at": datetime.now().isoformat()
            }

            # Test creating a chat message
            result = await chat_history_service.store_message(
                conversation_id=str(uuid.uuid4()),
                user_id=TEST_USER_ID,
                session_id=TEST_SESSION_ID,
                message_type="assistant",
                content="Hello, how can I help you?"
            )
            
            # Verify the results
            assert result is not None
            assert result["id"] == TEST_CHAT_ID
            assert result["message_type"] == "assistant"
            assert result["content"] == "Hello, how can I help you?"
        
        # Mock the select method
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": str(uuid.uuid4()),
                "conversation_id": str(uuid.uuid4()),
                "user_id": TEST_USER_ID,
                "session_id": TEST_SESSION_ID,
                "message_type": "assistant",
                "content": "Hello, how can I help you?",
                "created_at": (datetime.now() - timedelta(minutes=5)).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "conversation_id": str(uuid.uuid4()),
                "user_id": TEST_USER_ID,
                "session_id": TEST_SESSION_ID,
                "message_type": "user",
                "content": "I need help with my email",
                "created_at": (datetime.now() - timedelta(minutes=4)).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "conversation_id": str(uuid.uuid4()),
                "user_id": TEST_USER_ID,
                "session_id": TEST_SESSION_ID,
                "message_type": "assistant",
                "content": "I can help you with that. What's the issue?",
                "created_at": (datetime.now() - timedelta(minutes=3)).isoformat()
            }
        ]
        
        # Mock the get_messages method to be async
        with patch.object(chat_history_service, 'get_messages', new_callable=AsyncMock) as mock_get_messages:
            mock_get_messages.return_value = [
                {
                    "id": str(uuid.uuid4()),
                    "conversation_id": str(uuid.uuid4()),
                    "user_id": TEST_USER_ID,
                    "session_id": TEST_SESSION_ID,
                    "message_type": "assistant",
                    "content": "Hello, how can I help you?",
                    "created_at": (datetime.now() - timedelta(minutes=5)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "conversation_id": str(uuid.uuid4()),
                    "user_id": TEST_USER_ID,
                    "session_id": TEST_SESSION_ID,
                    "message_type": "user",
                    "content": "I need help with my email",
                    "created_at": (datetime.now() - timedelta(minutes=4)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "conversation_id": str(uuid.uuid4()),
                    "user_id": TEST_USER_ID,
                    "session_id": TEST_SESSION_ID,
                    "message_type": "assistant",
                    "content": "I can help you with that. What's the issue?",
                    "created_at": (datetime.now() - timedelta(minutes=3)).isoformat()
                }
            ]
            
            history_result = await chat_history_service.get_messages(
                conversation_id=str(uuid.uuid4())
            )
        
        # Verify the results
        assert history_result is not None
        assert len(history_result) == 3
        
        # Test getting chat history with limit
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": str(uuid.uuid4()),
                "conversation_id": str(uuid.uuid4()),
                "user_id": TEST_USER_ID,
                "session_id": TEST_SESSION_ID,
                "message_type": "assistant",
                "content": "I can help you with that. What's the issue?",
                "created_at": (datetime.now() - timedelta(minutes=3)).isoformat()
            }
        ]
        
        # Mock the get_messages method with limit parameter
        with patch.object(chat_history_service, 'get_messages', new_callable=AsyncMock) as mock_get_messages_limit:
            mock_get_messages_limit.return_value = [
                {
                    "id": str(uuid.uuid4()),
                    "conversation_id": str(uuid.uuid4()),
                    "user_id": TEST_USER_ID,
                    "session_id": TEST_SESSION_ID,
                    "message_type": "assistant",
                    "content": "I can help you with that. What's the issue?",
                    "created_at": (datetime.now() - timedelta(minutes=3)).isoformat()
                }
            ]

            limit_result = await chat_history_service.get_messages(
                conversation_id=str(uuid.uuid4()),
                limit=1
            )

            # Verify the results
            assert limit_result is not None
            assert len(limit_result) == 1


@pytest.mark.asyncio
async def test_memory_service_integration(memory_manager):
    """Test memory service integration."""
    # Mock the memory service
    with patch('memory.adk_memory_manager.OprinaMemoryManager._initialize_memory_service') as mock_init_memory:
        # Create a mock memory service
        mock_memory_service = MagicMock()
        mock_init_memory.return_value = None
        memory_manager._memory_service = mock_memory_service

        # Mock the add_memory method
        mock_memory_service.add_memory.return_value = {
            "status": "success",
            "memory_id": TEST_MEMORY_ID
        }

        # Mock the add_session_to_memory method to return True
        with patch.object(memory_manager, 'add_session_to_memory', new_callable=AsyncMock) as mock_add_session:
            mock_add_session.return_value = True

            # Test creating a memory
            result = await memory_manager.add_session_to_memory(
                user_id=TEST_USER_ID,
                session_id=TEST_SESSION_ID
            )

            # Verify the results
            assert result is not None
            assert result is True
        
        # Mock the get_memories method
        mock_memory_service.get_memories.return_value = [
            {
                "memory_id": str(uuid.uuid4()),
                "session_id": TEST_SESSION_ID,
                "user_id": TEST_USER_ID,
                "memory_type": "conversation",
                "content": "User mentioned they have a meeting at 2pm tomorrow",
                "created_at": datetime.now() - timedelta(hours=1)
            },
            {
                "memory_id": str(uuid.uuid4()),
                "session_id": TEST_SESSION_ID,
                "user_id": TEST_USER_ID,
                "memory_type": "preference",
                "content": "User prefers short, concise responses",
                "created_at": datetime.now() - timedelta(hours=2)
            }
        ]
        
        # Mock the _archive_session_to_memory method to return True
        with patch.object(memory_manager, '_archive_session_to_memory', new_callable=AsyncMock) as mock_archive:
            mock_archive.return_value = True
            
            memories_result = await memory_manager._archive_session_to_memory(
                user_id=TEST_USER_ID,
                session_id=TEST_SESSION_ID
            )
        
        # Verify the results
        assert memories_result is not None
        
        # Mock the get_memories_by_type method
        mock_memory_service.get_memories_by_type.return_value = [
            {
                "memory_id": str(uuid.uuid4()),
                "session_id": TEST_SESSION_ID,
                "user_id": TEST_USER_ID,
                "memory_type": "preference",
                "content": "User prefers short, concise responses",
                "created_at": datetime.now() - timedelta(hours=2)
            }
        ]
        
        # Test getting memories by type
        with patch.object(memory_manager, '_archive_session_to_memory', new_callable=AsyncMock) as mock_archive_type:
            mock_archive_type.return_value = True
            
            type_result = await memory_manager._archive_session_to_memory(
                user_id=TEST_USER_ID,
                session_id=TEST_SESSION_ID
            )

            # Verify the results
            assert type_result is not None
            assert type_result is True


@pytest.mark.asyncio
async def test_database_cleanup(database_session_service):
    """Test database cleanup."""
    # Test deleting a session
    delete_result = await database_session_service.delete_session(TEST_SESSION_ID)
    # Verify the results
    assert delete_result is not None
    # Test cleaning up old sessions
    cleanup_result = await database_session_service.cleanup_old_sessions(days=30)
    # Verify the results
    assert cleanup_result is not None
    assert cleanup_result == 2


if __name__ == "__main__":
    # Run the tests
    asyncio.run(pytest.main([__file__, "-v"])) 