"""
Token client for deployed Vertex AI Agent to access user tokens via backend API.
"""

import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AgentTokenClient:
    """Client for getting user tokens from backend API."""
    
    def __init__(self):
        self.backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        self.api_key = os.getenv("INTERNAL_API_KEY", "agent-internal-key-change-in-production")
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def get_gmail_token(self, vertex_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Gmail token for user by Vertex AI session ID.
        
        Args:
            vertex_session_id: Vertex AI session ID
            
        Returns:
            Dict with token data or None if not available
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/v1/internal/tokens/gmail",
                json={"vertex_session_id": vertex_session_id},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                logger.info(f"Retrieved Gmail token for session {vertex_session_id}")
                return token_data
            elif response.status_code == 404:
                logger.info(f"Gmail not connected for session {vertex_session_id}")
                return None
            else:
                logger.error(f"Failed to get Gmail token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Gmail token for session {vertex_session_id}: {e}")
            return None
    
    def get_calendar_token(self, vertex_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Calendar token for user by Vertex AI session ID.
        
        Args:
            vertex_session_id: Vertex AI session ID
            
        Returns:
            Dict with token data or None if not available
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/v1/internal/tokens/calendar",
                json={"vertex_session_id": vertex_session_id},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                logger.info(f"Retrieved Calendar token for session {vertex_session_id}")
                return token_data
            elif response.status_code == 404:
                logger.info(f"Calendar not connected for session {vertex_session_id}")
                return None
            else:
                logger.error(f"Failed to get Calendar token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Calendar token for session {vertex_session_id}: {e}")
            return None
    
    def get_connection_status(self, vertex_session_id: str) -> Dict[str, bool]:
        """
        Get connection status for all services.
        
        Args:
            vertex_session_id: Vertex AI session ID
            
        Returns:
            Dict with service connection status
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/v1/internal/connection-status",
                json={"vertex_session_id": vertex_session_id},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                status_data = response.json()
                return {
                    "gmail": status_data.get("gmail", False),
                    "calendar": status_data.get("calendar", False)
                }
            else:
                logger.error(f"Failed to get connection status: {response.status_code}")
                return {"gmail": False, "calendar": False}
                
        except Exception as e:
            logger.error(f"Error getting connection status for session {vertex_session_id}: {e}")
            return {"gmail": False, "calendar": False}
    
    def validate_token(self, token_data: Dict[str, Any]) -> bool:
        """
        Validate if token is still valid.
        
        Args:
            token_data: Token data from get_*_token()
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not token_data or not token_data.get("access_token"):
            return False
        
        # Check expiration
        expires_at_str = token_data.get("expires_at")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if expires_at <= datetime.utcnow():
                    return False
            except Exception:
                return False
        
        return True

# Global instance
token_client = AgentTokenClient() 