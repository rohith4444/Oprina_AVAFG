import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_session_state_persistence(test_memory_manager):
    """Test that session state persists across calls."""
    user_id = "test_user_123"
    session_id = "test_session_456"
    # Set state
    await test_memory_manager.set_session_state(user_id, session_id, {"foo": "bar"})
    # Get state
    state = await test_memory_manager.get_session_state(user_id, session_id)
    assert state is not None
    assert state.get("foo") == "bar"

@pytest.mark.asyncio
async def test_cross_agent_state_sharing(test_memory_manager):
    """Test that session state is shared across agents."""
    user_id = "test_user_123"
    session_id = "test_session_456"
    # Set state in one agent
    await test_memory_manager.set_session_state(user_id, session_id, {"shared": True})
    # Get state in another agent
    state = await test_memory_manager.get_session_state(user_id, session_id)
    assert state is not None
    assert state.get("shared") is True

@pytest.mark.asyncio
async def test_session_state_cleanup(test_memory_manager):
    """Test that session state is cleaned up after session ends."""
    user_id = "test_user_123"
    session_id = "test_session_456"
    # Set state
    await test_memory_manager.set_session_state(user_id, session_id, {"temp": 123})
    # Cleanup
    await test_memory_manager.delete_session_state(user_id, session_id)
    # Get state
    state = await test_memory_manager.get_session_state(user_id, session_id)
    assert state is None or state == {}

@pytest.mark.asyncio
async def test_user_preferences_persistence(test_memory_manager):
    """Test that user preferences persist in session state."""
    user_id = "test_user_123"
    session_id = "test_session_456"
    prefs = {"reply_style": "friendly", "summary_detail": "detailed"}
    await test_memory_manager.set_session_state(user_id, session_id, {"user:preferences": prefs})
    state = await test_memory_manager.get_session_state(user_id, session_id)
    assert state is not None
    assert state.get("user:preferences") == prefs 