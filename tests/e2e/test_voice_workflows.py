"""
End-to-end tests for voice workflows

This module contains tests that verify complete voice workflows from user input
to system response, including speech recognition, agent processing, and response generation.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from tests.utils import TestUtils

class TestVoiceWorkflows:
    """Tests for voice workflows"""
    
    @pytest.mark.asyncio
    async def test_email_workflow(self, test_voice_agent, mock_mcp_client):
        """Test the complete email workflow"""
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.email.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Process the audio data
                response = await test_voice_agent.process_audio(b"fake_audio_data")
                
                # Verify the response
                assert response is not None
                assert "content" in response
                assert "email" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_calendar_workflow(self, test_voice_agent, mock_mcp_client):
        """Test the complete calendar workflow"""
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my calendar"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.calendar.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Process the audio data
                response = await test_voice_agent.process_audio(b"fake_audio_data")
                
                # Verify the response
                assert response is not None
                assert "content" in response
                assert "calendar" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_complex_workflow(self, test_voice_agent, mock_mcp_client):
        """Test a complex workflow with multiple steps"""
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Schedule a meeting with John tomorrow at 2pm"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.calendar.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Process the audio data
                response = await test_voice_agent.process_audio(b"fake_audio_data")
                
                # Verify the response
                assert response is not None
                assert "content" in response
                assert "meeting" in response["content"].lower()
                assert "scheduled" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_voice_agent):
        """Test error handling in voice workflows"""
        # Mock the speech recognition service to return an error
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.side_effect = Exception("Speech recognition failed")
            
            # Process the audio data
            response = await test_voice_agent.process_audio(b"fake_audio_data")
            
            # Verify the error response
            assert response is not None
            assert "content" in response
            assert "error" in response["content"].lower()
            assert "sorry" in response["content"].lower() 