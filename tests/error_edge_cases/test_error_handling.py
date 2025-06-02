"""
Tests for error handling

This module contains tests that verify the system's behavior in error conditions,
ensuring robust error handling and graceful degradation.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from tests.utils import TestUtils

class TestErrorHandling:
    """Tests for error handling"""
    
    @pytest.mark.asyncio
    async def test_network_error(self, test_voice_agent, mock_mcp_client):
        """Test handling of network errors"""
        # Mock the MCP client to raise a network error
        mock_mcp_client.list_gmail_messages.side_effect = Exception("Network error")
        
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.email.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Process the audio data
                response = await test_voice_agent.process_audio(b"fake_audio_data")
                
                # Verify the error response
                assert response is not None
                assert "content" in response
                assert "error" in response["content"].lower()
                assert "network" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_api_error(self, test_voice_agent, mock_mcp_client):
        """Test handling of API errors"""
        # Mock the MCP client to return an API error
        mock_mcp_client.list_gmail_messages.return_value = {
            "status": "error",
            "error": {
                "code": 403,
                "message": "API quota exceeded"
            }
        }
        
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.email.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Process the audio data
                response = await test_voice_agent.process_audio(b"fake_audio_data")
                
                # Verify the error response
                assert response is not None
                assert "content" in response
                assert "error" in response["content"].lower()
                assert "quota" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_input(self, test_voice_agent):
        """Test handling of invalid input"""
        # Mock the speech recognition service to return invalid input
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Invalid command"
            
            # Process the audio data
            response = await test_voice_agent.process_audio(b"fake_audio_data")
            
            # Verify the error response
            assert response is not None
            assert "content" in response
            assert "sorry" in response["content"].lower()
            assert "understand" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_timeout(self, test_voice_agent, mock_mcp_client):
        """Test handling of timeouts"""
        # Mock the MCP client to simulate a timeout
        async def timeout_simulator(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate a long-running operation
            return {"status": "success", "data": []}
        
        mock_mcp_client.list_gmail_messages.side_effect = timeout_simulator
        
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.email.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Process the audio data with a short timeout
                with patch("config.settings.settings.PROCESSING_TIMEOUT", 1):
                    response = await test_voice_agent.process_audio(b"fake_audio_data")
                    
                    # Verify the timeout response
                    assert response is not None
                    assert "content" in response
                    assert "timeout" in response["content"].lower()
                    assert "sorry" in response["content"].lower() 