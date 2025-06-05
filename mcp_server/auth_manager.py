"""
MCP Authentication Manager

This module provides authentication management for the MCP server.
It uses the original auth service to avoid duplication.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple

# Import the original auth service to avoid duplication
from services.google_cloud.gmail_auth import GmailAuthService
from services.google_cloud.auth_utils import get_credentials_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPAuthManager:
    """
    Authentication manager for the MCP server.
    Uses the original auth service to avoid duplication.
    """
    
    def __init__(self):
        """Initialize the auth manager with the original auth service."""
        self.auth_service = GmailAuthService()
        self.credentials_path = get_credentials_path()
        self._ensure_credentials_exist()
    
    def _ensure_credentials_exist(self) -> None:
        """Ensure that credentials exist."""
        if not os.path.exists(self.credentials_path):
            logger.warning(f"Credentials not found at {self.credentials_path}")
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)
            # Create empty credentials file
            with open(self.credentials_path, 'w') as f:
                json.dump({}, f)
    
    def get_credentials(self) -> Dict[str, Any]:
        """
        Get the credentials from the original auth service.
        
        Returns:
            Dict[str, Any]: The credentials
        """
        return self.auth_service.get_credentials()
    
    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated using the original auth service.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self.auth_service.is_authenticated()
    
    def get_auth_url(self) -> str:
        """
        Get the authentication URL from the original auth service.
        
        Returns:
            str: The authentication URL
        """
        return self.auth_service.get_auth_url()
    
    def handle_auth_callback(self, code: str) -> Tuple[bool, str]:
        """
        Handle the authentication callback using the original auth service.
        
        Args:
            code (str): The authorization code
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        return self.auth_service.handle_auth_callback(code)
    
    def refresh_token(self) -> bool:
        """
        Refresh the token using the original auth service.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.auth_service.refresh_token()

# Create a singleton instance
auth_manager = MCPAuthManager() 