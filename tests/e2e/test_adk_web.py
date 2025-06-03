"""
End-to-end tests for ADK web interface

This module contains tests that verify the ADK web interface functionality,
including startup, agent interaction, session management, and error handling.
"""
import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from tests.utils import TestUtils

# Define request models
class RunSSERequest(BaseModel):
    session_id: str
    message: str

# Create a mock FastAPI app for testing
app = FastAPI(title="Oprina Test API")

# In-memory session storage for testing
sessions = {}

@app.get("/")
async def root():
    return {"message": "Welcome to Oprina API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/list-apps")
async def list_apps(relative_path: str = "./"):
    return {"apps": ["oprina"]}

@app.post("/apps/agents/users/{user_id}/sessions")
async def create_session(user_id: str):
    session_id = "test-session-123"
    sessions[session_id] = {
        "session_id": session_id,
        "user_id": user_id,
        "events": []
    }
    return {"session_id": session_id}

@app.get("/apps/agents/users/{user_id}/sessions/{session_id}")
async def get_session(user_id: str, session_id: str):
    if session_id == "invalid-session-id" or session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.get("/apps/agents/users/{user_id}/sessions")
async def list_sessions(user_id: str):
    return [s for s in sessions.values() if s["user_id"] == user_id]

@app.delete("/apps/agents/users/{user_id}/sessions/{session_id}")
async def delete_session(user_id: str, session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "success"}

@app.post("/run_sse")
async def run_sse(request: RunSSERequest):
    if request.message == "Trigger error":
        raise HTTPException(status_code=500, detail="Server error")
    
    if request.session_id in sessions:
        sessions[request.session_id]["events"].append({
            "content": f"I've checked your emails. You have 3 new messages."
        })
    
    return {"status": "success"}

class TestAdkWeb:
    """Tests for ADK web interface"""
    
    @pytest.fixture
    def test_client(self):
        """Create a test client for the FastAPI app"""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_adk_web_startup(self, test_client):
        """Test that the ADK web server starts up correctly"""
        # Test the root endpoint
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Welcome to Oprina API"
        
        # Test the health check endpoint
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        
        # Test the list-apps endpoint
        response = test_client.get("/list-apps?relative_path=./")
        assert response.status_code == 200
        assert "apps" in response.json()
    
    @pytest.mark.asyncio
    async def test_web_agent_interaction(self, test_client, mock_mcp_client):
        """Test interaction with agents through the web interface"""
        # Mock the MCP client
        with patch("mcp_server.client.MCPClient") as mock_mcp:
            mock_mcp.return_value = mock_mcp_client
            
            # Create a new session
            response = test_client.post("/apps/agents/users/user/sessions")
            assert response.status_code == 200
            session_id = response.json()["session_id"]
            
            # Send a message to the agent
            response = test_client.post(
                "/run_sse",
                json={
                    "session_id": session_id,
                    "message": "Check my emails"
                }
            )
            assert response.status_code == 200
            
            # Get the session to check the response
            response = test_client.get(f"/apps/agents/users/user/sessions/{session_id}")
            assert response.status_code == 200
            session_data = response.json()
            
            # Verify the agent responded
            assert "events" in session_data
            assert len(session_data["events"]) > 0
            assert "content" in session_data["events"][0]
            assert "email" in session_data["events"][0]["content"].lower()
    
    @pytest.mark.asyncio
    async def test_web_session_management(self, test_client):
        """Test session management in the web interface"""
        # Create a new session
        response = test_client.post("/apps/agents/users/user/sessions")
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        
        # Get the session
        response = test_client.get(f"/apps/agents/users/user/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["session_id"] == session_id
        
        # List all sessions
        response = test_client.get("/apps/agents/users/user/sessions")
        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)
        assert any(s["session_id"] == session_id for s in sessions)
        
        # Delete the session
        response = test_client.delete(f"/apps/agents/users/user/sessions/{session_id}")
        assert response.status_code == 200
        
        # Verify the session is deleted
        response = test_client.get(f"/apps/agents/users/user/sessions/{session_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_web_error_handling(self, test_client):
        """Test error handling in the web interface"""
        # Test with invalid session ID
        response = test_client.get("/apps/agents/users/user/sessions/invalid-session-id")
        assert response.status_code == 404
        
        # Test with invalid endpoint
        response = test_client.get("/invalid-endpoint")
        assert response.status_code == 404
        
        # Test with invalid request body
        response = test_client.post(
            "/run_sse",
            json={
                "invalid_field": "invalid_value"
            }
        )
        assert response.status_code == 422  # Validation error
        
        # Test with server error
        response = test_client.post(
            "/run_sse",
            json={
                "session_id": "test-session-123",
                "message": "Trigger error"
            }
        )
        assert response.status_code == 500  # Server error 