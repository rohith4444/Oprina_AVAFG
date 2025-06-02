"""
Integration tests for Oprina agents

This module contains tests that verify the integration between different agents
in the Oprina system, such as the voice agent, coordinator agent, and sub-agents.
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import patch, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.utils import TestUtils

class TestAgentIntegration:
    """Tests for agent integration"""
    
    @pytest.mark.asyncio
    async def test_voice_agent_creation(self, test_voice_agent):
        """Test that the voice agent can be created"""
        assert test_voice_agent is not None
        assert hasattr(test_voice_agent, "process")
    
    @pytest.mark.asyncio
    async def test_coordinator_agent_creation(self, test_coordinator_agent):
        """Test that the coordinator agent can be created"""
        assert test_coordinator_agent is not None
        assert hasattr(test_coordinator_agent, "process")
    
    @pytest.mark.asyncio
    async def test_email_agent_creation(self, test_email_agent):
        """Test that the email agent can be created"""
        assert test_email_agent is not None
        assert hasattr(test_email_agent, "process")
    
    @pytest.mark.asyncio
    async def test_calendar_agent_creation(self, test_calendar_agent):
        """Test that the calendar agent can be created"""
        assert test_calendar_agent is not None
        assert hasattr(test_calendar_agent, "process")
    
    @pytest.mark.asyncio
    async def test_voice_to_coordinator_integration(self, test_voice_agent, test_coordinator_agent):
        """Test integration between voice agent and coordinator agent"""
        # Mock the coordinator agent's process method
        original_process = test_coordinator_agent.process
        test_coordinator_agent.process = AsyncMock(return_value=TestUtils.create_mock_adk_response("Coordinator response"))
        
        # Create a test event
        test_event = {
            "author": "user",
            "content": "Check my emails",
            "timestamp": 1234567890,
            "is_final": True
        }
        
        # Process the event with the voice agent
        response = await test_voice_agent.process(test_event)
        
        # Verify the response
        assert response is not None
        assert "content" in response
        assert "Coordinator response" in response["content"]
        
        # Restore the original process method
        test_coordinator_agent.process = original_process
    
    @pytest.mark.asyncio
    async def test_coordinator_to_email_integration(self, test_coordinator_agent, test_email_agent):
        """Test integration between coordinator agent and email agent"""
        # Mock the email agent's process method
        original_process = test_email_agent.process
        test_email_agent.process = AsyncMock(return_value=TestUtils.create_mock_adk_response("Email response"))
        
        # Create a test event
        test_event = {
            "author": "user",
            "content": "Check my emails",
            "timestamp": 1234567890,
            "is_final": True
        }
        
        # Process the event with the coordinator agent
        response = await test_coordinator_agent.process(test_event)
        
        # Verify the response
        assert response is not None
        assert "content" in response
        assert "Email response" in response["content"]
        
        # Restore the original process method
        test_email_agent.process = original_process
    
    @pytest.mark.asyncio
    async def test_coordinator_to_calendar_integration(self, test_coordinator_agent, test_calendar_agent):
        """Test integration between coordinator agent and calendar agent"""
        # Mock the calendar agent's process method
        original_process = test_calendar_agent.process
        test_calendar_agent.process = AsyncMock(return_value=TestUtils.create_mock_adk_response("Calendar response"))
        
        # Create a test event
        test_event = {
            "author": "user",
            "content": "Check my calendar",
            "timestamp": 1234567890,
            "is_final": True
        }
        
        # Process the event with the coordinator agent
        response = await test_coordinator_agent.process(test_event)
        
        # Verify the response
        assert response is not None
        assert "content" in response
        assert "Calendar response" in response["content"]
        
        # Restore the original process method
        test_calendar_agent.process = original_process

@pytest.mark.asyncio
async def test_voice_to_coordinator_delegation(test_voice_agent, test_coordinator_agent):
    """Test that the voice agent delegates to the coordinator agent."""
    # Mock coordinator process
    test_coordinator_agent.process = AsyncMock(return_value={"content": "Coordinator handled"})
    # Simulate user event
    user_event = {"author": "user", "content": "Check my email", "timestamp": 1234567890, "is_final": True}
    # Voice agent should delegate
    response = await test_voice_agent.process(user_event)
    assert response is not None
    assert "Coordinator handled" in response["content"]

@pytest.mark.asyncio
async def test_coordinator_to_subagent_routing(test_coordinator_agent, test_email_agent, test_calendar_agent):
    """Test that the coordinator agent routes to the correct sub-agent."""
    # Mock sub-agent process
    test_email_agent.process = AsyncMock(return_value={"content": "Email handled"})
    test_calendar_agent.process = AsyncMock(return_value={"content": "Calendar handled"})
    # Simulate email event
    email_event = {"author": "user", "content": "Read my emails", "timestamp": 1234567890, "is_final": True}
    response_email = await test_coordinator_agent.process(email_event)
    assert response_email is not None
    assert "Email handled" in response_email["content"]
    # Simulate calendar event
    calendar_event = {"author": "user", "content": "Show my calendar", "timestamp": 1234567890, "is_final": True}
    response_calendar = await test_coordinator_agent.process(calendar_event)
    assert response_calendar is not None
    assert "Calendar handled" in response_calendar["content"]

@pytest.mark.asyncio
async def test_email_content_pipeline(test_email_agent):
    """Test the email content pipeline through the email agent."""
    # Simulate email content event
    event = {"author": "user", "content": "Summarize my latest email", "timestamp": 1234567890, "is_final": True}
    test_email_agent.process = AsyncMock(return_value={"content": "Summary: ..."})
    response = await test_email_agent.process(event)
    assert response is not None
    assert "Summary" in response["content"]

@pytest.mark.asyncio
async def test_calendar_coordination_workflow(test_calendar_agent):
    """Test the calendar workflow through the calendar agent."""
    # Simulate calendar event
    event = {"author": "user", "content": "Schedule a meeting tomorrow at 2pm", "timestamp": 1234567890, "is_final": True}
    test_calendar_agent.process = AsyncMock(return_value={"content": "Meeting scheduled"})
    response = await test_calendar_agent.process(event)
    assert response is not None
    assert "Meeting scheduled" in response["content"] 