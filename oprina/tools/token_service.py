# oprina/tools/token_service.py
"""
Lightweight token service for Vertex AI Agent.
Uses direct HTTP requests instead of Supabase client to avoid dependency conflicts.
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from oprina.services.logging.logger import setup_logger

logger = setup_logger("token_service")

class TokenService:
    """Minimal token service using only standard library HTTP."""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # ✅ ADD: Get encryption key for token decryption
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            logger.warning("ENCRYPTION_KEY not set - token decryption will fail")
            self._fernet = None
        else:
            try:
                key_bytes = base64.b64decode(self.encryption_key.encode())
                self._fernet = Fernet(key_bytes)
                logger.info("Encryption manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize encryption: {e}")
                self._fernet = None
    
        
        if not self.supabase_url:
            logger.error("SUPABASE_URL environment variable not set")
            raise ValueError("SUPABASE_URL must be set")
            
        if not self.service_key:
            logger.error("SUPABASE_SERVICE_KEY environment variable not set")
            raise ValueError("SUPABASE_SERVICE_KEY must be set")
        
        logger.info("TokenService initialized successfully")
    
    def get_user_tokens(self, user_id: str) -> Dict[str, Any]:
        """Get OAuth tokens for a user using direct HTTP request."""
        
        logger.info(f"Fetching tokens for user: {user_id}")
        
        # Construct Supabase REST API URL
        url = f"{self.supabase_url}/rest/v1/users"
        
        # Create request headers
        headers = {
            'apikey': self.service_key,
            'Authorization': f'Bearer {self.service_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Add query parameter for user ID
        query_url = f"{url}?id=eq.{user_id}&select=gmail_tokens,calendar_tokens"
        
        try:
            request = Request(query_url, headers=headers)
            
            with urlopen(request, timeout=10) as response:
                if response.getcode() != 200:
                    error_msg = f"HTTP {response.getcode()}: {response.read().decode()}"
                    logger.error(f"Database request failed: {error_msg}")
                    raise Exception(error_msg)
                
                data = json.loads(response.read().decode())
                
                if not data:
                    logger.warning(f"No user found with ID: {user_id}")
                    return {"gmail_tokens": None, "calendar_tokens": None}
                
                user_data = data[0]
                result = {
                    "gmail_tokens": user_data.get("gmail_tokens"),
                    "calendar_tokens": user_data.get("calendar_tokens")
                }
                
                # Log token availability (without exposing actual tokens)
                has_gmail = result["gmail_tokens"] is not None
                has_calendar = result["calendar_tokens"] is not None
                logger.info(f"User {user_id} tokens - Gmail: {has_gmail}, Calendar: {has_calendar}")
                
                return result
                
        except HTTPError as e:
            error_msg = f"Failed to fetch user tokens: HTTP {e.code} - {e.reason}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except URLError as e:
            error_msg = f"Failed to connect to database: {e.reason}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid response from database: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error fetching tokens: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def decrypt_tokens(self, encrypted_tokens: Optional[str]) -> Optional[Dict[str, Any]]:
        """Decrypt token data using Fernet encryption (matching backend)."""
        if not encrypted_tokens:
            return None
        
        try:
            # Parse the token data structure
            if isinstance(encrypted_tokens, str):
                token_data = json.loads(encrypted_tokens)
            elif isinstance(encrypted_tokens, dict):
                token_data = encrypted_tokens
            else:
                logger.warning(f"Unexpected token format: {type(encrypted_tokens)}")
                return None
            
            # Check if we have encryption capability
            if not self._fernet:
                logger.error("No encryption key available for token decryption")
                return None
            
            # Decrypt the encrypted fields
            decrypted_tokens = {}
            
            # Decrypt access_token
            if 'access_token' in token_data:
                try:
                    encrypted_access = token_data['access_token']
                    decoded_data = base64.b64decode(encrypted_access.encode())
                    decrypted_access = self._fernet.decrypt(decoded_data).decode()
                    decrypted_tokens['access_token'] = decrypted_access
                    logger.debug("Successfully decrypted access_token")
                except Exception as e:
                    logger.error(f"Failed to decrypt access_token: {e}")
                    return None
            
            # Decrypt refresh_token
            if 'refresh_token' in token_data:
                try:
                    encrypted_refresh = token_data['refresh_token']
                    decoded_data = base64.b64decode(encrypted_refresh.encode())
                    decrypted_refresh = self._fernet.decrypt(decoded_data).decode()
                    decrypted_tokens['refresh_token'] = decrypted_refresh
                    logger.debug("Successfully decrypted refresh_token")
                except Exception as e:
                    logger.error(f"Failed to decrypt refresh_token: {e}")
                    return None
            
            # Copy non-encrypted fields as-is
            for key, value in token_data.items():
                if key not in ['access_token', 'refresh_token']:
                    decrypted_tokens[key] = value
            
            logger.debug("Successfully decrypted token data")
            return decrypted_tokens
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode token JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing tokens: {e}")
            return None
    def test_connection(self) -> bool:
        """Test connection to Supabase database."""
        try:
            logger.info("Testing database connection...")
            
            # Simple test query to check connection
            url = f"{self.supabase_url}/rest/v1/users"
            headers = {
                'apikey': self.service_key,
                'Authorization': f'Bearer {self.service_key}',
                'Content-Type': 'application/json'
            }
            
            # Add limit to avoid large responses
            query_url = f"{url}?select=id&limit=1"
            
            request = Request(query_url, headers=headers)
            
            with urlopen(request, timeout=5) as response:
                if response.getcode() == 200:
                    logger.info("✅ Database connection successful")
                    return True
                else:
                    logger.error(f"❌ Database connection failed: HTTP {response.getcode()}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False

# Global instance
_token_service = None

def get_token_service() -> TokenService:
    """Get global token service instance."""
    global _token_service
    if _token_service is None:
        _token_service = TokenService()
    return _token_service

def test_token_service_with_user(user_id: str = "test_user") -> bool:
    """Test token service with a specific user."""
    try:
        logger.info(f"Testing token service with user: {user_id}")
        token_service = get_token_service()
        
        # Test connection first
        if not token_service.test_connection():
            return False
        
        # Test token retrieval
        tokens = token_service.get_user_tokens(user_id)
        
        gmail_available = tokens.get('gmail_tokens') is not None
        calendar_available = tokens.get('calendar_tokens') is not None
        
        logger.info(f"Token availability for {user_id}:")
        logger.info(f"  Gmail: {'✅' if gmail_available else '❌'}")
        logger.info(f"  Calendar: {'✅' if calendar_available else '❌'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Token service test failed: {e}")
        return False