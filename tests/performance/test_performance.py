"""
Performance tests for Oprina backend

This module contains tests that verify the system's performance under load,
including response times, resource usage, and scalability.
"""
import pytest
import asyncio
import time
import statistics
from unittest.mock import patch, AsyncMock

from tests.utils import TestUtils

class TestPerformance:
    """Tests for system performance"""
    
    @pytest.mark.asyncio
    async def test_response_time(self, test_voice_agent, mock_mcp_client):
        """Test response time for voice agent"""
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.email.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Measure response time
                start_time = time.time()
                response = await test_voice_agent.process_audio(b"fake_audio_data")
                end_time = time.time()
                
                # Calculate response time
                response_time = end_time - start_time
                
                # Verify the response
                assert response is not None
                assert "content" in response
                
                # Verify response time is within acceptable range (e.g., less than 2 seconds)
                assert response_time < 2.0, f"Response time {response_time} exceeds threshold"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_voice_agent, mock_mcp_client):
        """Test performance with concurrent requests"""
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.email.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Create multiple concurrent requests
                num_requests = 5
                tasks = []
                
                # Start all requests concurrently
                start_time = time.time()
                for _ in range(num_requests):
                    tasks.append(asyncio.create_task(test_voice_agent.process_audio(b"fake_audio_data")))
                
                # Wait for all requests to complete
                responses = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # Calculate total time
                total_time = end_time - start_time
                
                # Verify all responses
                for response in responses:
                    assert response is not None
                    assert "content" in response
                
                # Verify total time is within acceptable range
                # For 5 concurrent requests, we expect the total time to be less than 5 times the single request time
                assert total_time < 5.0, f"Total time {total_time} exceeds threshold"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, test_voice_agent, mock_mcp_client):
        """Test memory usage during operation"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.email.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Process multiple requests
                for _ in range(10):
                    response = await test_voice_agent.process_audio(b"fake_audio_data")
                    assert response is not None
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Calculate memory increase
        memory_increase = final_memory - initial_memory
        
        # Verify memory usage is within acceptable range (e.g., less than 100MB increase)
        assert memory_increase < 100.0, f"Memory increase {memory_increase}MB exceeds threshold"
    
    @pytest.mark.asyncio
    async def test_response_time_distribution(self, test_voice_agent, mock_mcp_client):
        """Test response time distribution over multiple requests"""
        # Mock the speech recognition service
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            
            # Mock the MCP client
            with patch("agents.voice.sub_agents.coordinator.sub_agents.email.agent.get_mcp_client") as mock_get_mcp:
                mock_get_mcp.return_value = mock_mcp_client
                
                # Measure response times for multiple requests
                num_requests = 10
                response_times = []
                
                for _ in range(num_requests):
                    start_time = time.time()
                    response = await test_voice_agent.process_audio(b"fake_audio_data")
                    end_time = time.time()
                    
                    # Calculate response time
                    response_time = end_time - start_time
                    response_times.append(response_time)
                    
                    # Verify the response
                    assert response is not None
                    assert "content" in response
                
                # Calculate statistics
                mean_time = statistics.mean(response_times)
                median_time = statistics.median(response_times)
                std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
                
                # Verify statistics are within acceptable ranges
                assert mean_time < 1.0, f"Mean response time {mean_time} exceeds threshold"
                assert median_time < 1.0, f"Median response time {median_time} exceeds threshold"
                assert std_dev < 0.5, f"Response time standard deviation {std_dev} exceeds threshold" 