"""
Tests for MCP compatibility

This module contains tests that verify the compatibility with the MCP server,
including API calls, response handling, and error handling.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from tests.utils import TestUtils

class TestMCPCompatibility:
    """Tests for MCP compatibility"""
    
    @pytest.mark.asyncio
    async def test_mcp_client_creation(self, mock_mcp_client):
        """Test that the MCP client can be created"""
        assert mock_mcp_client is not None
        assert hasattr(mock_mcp_client, "list_gmail_messages")
        assert hasattr(mock_mcp_client, "get_gmail_message")
        assert hasattr(mock_mcp_client, "send_gmail_message")
        assert hasattr(mock_mcp_client, "list_calendar_events")
        assert hasattr(mock_mcp_client, "get_calendar_event")
        assert hasattr(mock_mcp_client, "create_calendar_event")
    
    @pytest.mark.asyncio
    async def test_gmail_api_calls(self, mock_mcp_client):
        """Test Gmail API calls through MCP client"""
        # Test list_gmail_messages
        response = await mock_mcp_client.list_gmail_messages()
        assert response is not None
        assert "status" in response
        assert response["status"] == "success"
        assert "data" in response
        assert len(response["data"]) > 0
        
        # Test get_gmail_message
        response = await mock_mcp_client.get_gmail_message("msg1")
        assert response is not None
        assert "status" in response
        assert response["status"] == "success"
        assert "data" in response
        assert response["data"]["id"] == "msg1"
        
        # Test send_gmail_message
        response = await mock_mcp_client.send_gmail_message(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        assert response is not None
        assert "status" in response
        assert response["status"] == "success"
        assert "data" in response
        assert "id" in response["data"]
    
    @pytest.mark.asyncio
    async def test_calendar_api_calls(self, mock_mcp_client):
        """Test Calendar API calls through MCP client"""
        # Test list_calendar_events
        response = await mock_mcp_client.list_calendar_events()
        assert response is not None
        assert "status" in response
        assert response["status"] == "success"
        assert "data" in response
        assert len(response["data"]) > 0
        
        # Test get_calendar_event
        response = await mock_mcp_client.get_calendar_event("event1")
        assert response is not None
        assert "status" in response
        assert response["status"] == "success"
        assert "data" in response
        assert response["data"]["id"] == "event1"
        
        # Test create_calendar_event
        event_data = {
            "summary": "New Team Meeting",
            "start": {"dateTime": "2024-12-02T14:00:00Z"},
            "end": {"dateTime": "2024-12-02T15:00:00Z"},
            "location": "Conference Room B",
            "description": "New team sync"
        }
        response = await mock_mcp_client.create_calendar_event(event_data)
        assert response is not None
        assert "status" in response
        assert response["status"] == "success"
        assert "data" in response
        assert "id" in response["data"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_mcp_client):
        """Test error handling in MCP client"""
        # Mock an error response
        mock_mcp_client.list_gmail_messages.return_value = {
            "status": "error",
            "error": {
                "code": 500,
                "message": "Internal Server Error"
            }
        }
        
        # Test error handling
        response = await mock_mcp_client.list_gmail_messages()
        assert response is not None
        assert "status" in response
        assert response["status"] == "error"
        assert "error" in response
        assert response["error"]["code"] == 500
        
        # Reset the mock
        mock_mcp_client.list_gmail_messages.return_value = {
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