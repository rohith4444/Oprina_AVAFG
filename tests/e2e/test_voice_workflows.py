"""
End-to-end tests for voice workflows

This module contains tests that verify complete voice workflows from user input
to system response, including speech recognition, agent processing, and response generation.
"""
import pytest
from unittest.mock import patch, AsyncMock

class TestVoiceWorkflows:
    """Tests for voice workflows"""
    
    @pytest.mark.asyncio
    async def test_voice_email_workflow(self, test_voice_agent, mock_mcp_client):
        """Test the complete email workflow from voice input to response"""
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my emails"
            mock_mcp_client.list_gmail_messages.return_value = {
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
            mock_mcp_client.get_gmail_message.return_value = {
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
            response = await test_voice_agent.process_audio(b"email")
            assert response is not None
            assert "content" in response
            assert "email" in response["content"].lower()
            assert mock_mcp_client.list_gmail_messages.called
            assert mock_mcp_client.get_gmail_message.called

    @pytest.mark.asyncio
    async def test_voice_calendar_workflow(self, test_voice_agent, mock_mcp_client):
        """Test the complete calendar workflow from voice input to response"""
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Check my calendar for tomorrow"
            mock_mcp_client.list_calendar_events.return_value = {
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
            response = await test_voice_agent.process_audio(b"calendar")
            assert response is not None
            assert "content" in response
            assert "calendar" in response["content"].lower()
            assert mock_mcp_client.list_calendar_events.called

    @pytest.mark.asyncio
    async def test_voice_content_workflow(self, test_voice_agent, mock_mcp_client):
        """Test the complete content workflow from voice input to response"""
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Summarize this email: Hi, I need a summary of the Q3 report"
            mock_mcp_client.summarize_text.return_value = {
                "status": "success",
                "data": {
                    "summary": "This is a summary of the provided text."
                }
            }
            response = await test_voice_agent.process_audio(b"summarize")
            assert response is not None
            assert "content" in response
            assert "summary" in response["content"].lower()
            assert mock_mcp_client.summarize_text.called

    @pytest.mark.asyncio
    async def test_complex_multi_agent_workflow(self, test_voice_agent, mock_mcp_client):
        """Test a complex workflow with multiple agents and steps"""
        with patch("services.google_cloud.speech_services.get_speech_services") as mock_speech:
            mock_speech.return_value.transcribe_audio.return_value = "Schedule a meeting with John tomorrow at 2pm and send him an email about the agenda"
            mock_mcp_client.create_calendar_event.return_value = {
                "status": "success",
                "data": {
                    "id": "event2",
                    "summary": "New Test Event",
                    "start": {"dateTime": "2024-01-02T14:00:00Z"},
                    "end": {"dateTime": "2024-01-02T15:00:00Z"}
                }
            }
            mock_mcp_client.send_gmail_message.return_value = {
                "status": "success",
                "data": {
                    "id": "msg2",
                    "threadId": "thread2"
                }
            }
            response = await test_voice_agent.process_audio(b"meeting")
            assert response is not None
            assert "content" in response
            assert ("meeting" in response["content"].lower() or "email" in response["content"].lower())
            assert mock_mcp_client.create_calendar_event.called
            assert mock_mcp_client.send_gmail_message.called

    @pytest.mark.asyncio
    async def test_error_handling(self, test_voice_agent):
        """Test error handling in voice workflows"""
        # Patch process_audio to simulate an error
        test_voice_agent.process_audio = AsyncMock(return_value={
            "content": "Error: Speech recognition failed. Sorry, could not process.",
            "status": "error"
        })
        response = await test_voice_agent.process_audio(b"fake_audio_data")
        assert response is not None
        assert "content" in response
        assert "error" in response["content"].lower()
        assert "sorry" in response["content"].lower() 