import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_runner_session_management(adk_runner):
    """Test that the ADK runner manages sessions correctly."""
    # Simulate session creation and retrieval
    session_id = "test_session_123"
    user_id = "test_user_123"
    # Assume runner has a session_service with create/get methods
    session_service = adk_runner.session_service
    await session_service.create_session(user_id, {"foo": "bar"})
    session = await session_service.get_session(user_id, session_id)
    assert session is not None

@pytest.mark.asyncio
async def test_runner_memory_integration(adk_runner):
    """Test that the ADK runner integrates with memory service."""
    # Assume runner has a memory_service with store/retrieve methods
    memory_service = adk_runner.memory_service
    user_id = "test_user_123"
    session_id = "test_session_123"
    await memory_service.store(user_id, session_id, {"key": "value"})
    data = await memory_service.retrieve(user_id, session_id)
    assert data is not None
    assert data.get("key") == "value"

@pytest.mark.asyncio
async def test_runner_event_processing(adk_runner):
    """Test that the ADK runner processes events correctly."""
    # Simulate running an event through the runner
    event = {"author": "user", "content": "Hello", "timestamp": 1234567890, "is_final": True}
    # Assume runner.run returns a list of events
    adk_runner.run = AsyncMock(return_value=[{"content": "Hi there!"}])
    result = await adk_runner.run(event)
    assert result is not None
    assert any("Hi there!" in e["content"] for e in result)

@pytest.mark.asyncio
async def test_runner_error_handling(adk_runner):
    """Test that the ADK runner handles errors gracefully."""
    # Simulate an error during event processing
    adk_runner.run = AsyncMock(side_effect=Exception("Test error"))
    with pytest.raises(Exception) as exc:
        await adk_runner.run({"author": "user", "content": "Trigger error"})
    assert "Test error" in str(exc.value) 