# oprina/tools/token_service.py
"""
TEMPORARY DEBUG VERSION - NO DECRYPTION
========================================
This version reads tokens as PLAIN TEXT for debugging.
⚠️ DO NOT USE IN PRODUCTION!
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
    """Minimal token service - DEBUG VERSION WITHOUT DECRYPTION."""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # ⚠️ SKIP encryption setup for debug mode
        logger.warning("🚨 DEBUG MODE: TokenService running WITHOUT decryption!")
        self._fernet = None  # Explicitly disable encryption
        
        if not self.supabase_url:
            logger.error("SUPABASE_URL environment variable not set")
            raise ValueError("SUPABASE_URL must be set")
            
        if not self.service_key:
            logger.error("SUPABASE_SERVICE_KEY environment variable not set")
            raise ValueError("SUPABASE_SERVICE_KEY must be set")
        
        logger.info("TokenService initialized successfully (DEBUG MODE)")
    
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
                
                # 🔍 ENHANCED: Check if tokens are in debug mode (plain text)
                if has_gmail:
                    gmail_tokens = result["gmail_tokens"]
                    is_debug = gmail_tokens.get("debug_mode", False) if isinstance(gmail_tokens, dict) else False
                    logger.info(f"🔍 Gmail tokens debug mode: {is_debug}")
                    
                    if is_debug and isinstance(gmail_tokens, dict):
                        access_token = gmail_tokens.get("access_token", "")
                        refresh_token = gmail_tokens.get("refresh_token", "")
                        logger.info(f"🔍 Plain text tokens - access: {len(access_token)}, refresh: {len(refresh_token)}")
                
                if has_calendar:
                    calendar_tokens = result["calendar_tokens"]
                    is_debug = calendar_tokens.get("debug_mode", False) if isinstance(calendar_tokens, dict) else False
                    logger.info(f"🔍 Calendar tokens debug mode: {is_debug}")
                
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
    
    def decrypt_tokens(self, token_data) -> Optional[Dict[str, Any]]:
        """
        Process tokens - DEBUG VERSION (NO DECRYPTION).
        Returns plain text tokens if in debug mode, otherwise fails.
        """
        if not token_data:
            return None
        
        try:
            # Parse the token data structure
            if isinstance(token_data, str):
                parsed_tokens = json.loads(token_data)
            elif isinstance(token_data, dict):
                parsed_tokens = token_data
            else:
                logger.warning(f"Unexpected token format: {type(token_data)}")
                return None
            
            logger.debug(f"🔍 Token data structure: {list(parsed_tokens.keys())}")
            
            # ⚠️ CHECK FOR DEBUG MODE (plain text tokens)
            if parsed_tokens.get("debug_mode"):
                logger.info("✅ Found debug mode tokens - returning as plain text")
                
                # Verify required fields exist
                access_token = parsed_tokens.get("access_token")
                if access_token:
                    logger.info(f"✅ Plain text access_token found (length: {len(access_token)})")
                else:
                    logger.warning("⚠️ No access_token in debug tokens")
                
                refresh_token = parsed_tokens.get("refresh_token")
                if refresh_token:
                    logger.info(f"✅ Plain text refresh_token found (length: {len(refresh_token)})")
                else:
                    logger.warning("⚠️ No refresh_token in debug tokens")
                
                # Return the tokens as-is (already plain text)
                return parsed_tokens
            
            else:
                # ⚠️ These are encrypted tokens, but we're in debug mode
                logger.error("❌ Found encrypted tokens, but running in DEBUG mode!")
                logger.error("    Either:")
                logger.error("    1. Switch back to production TokenService, or")
                logger.error("    2. Reconnect services to generate debug tokens")
                return None
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to decode token JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error processing tokens: {type(e).__name__}: {str(e)}")
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
    
    def test_token_retrieval(self, user_id: str) -> Dict[str, Any]:
        """
        🧪 Test plain text token retrieval (DEBUG VERSION).
        """
        try:
            logger.info(f"🧪 Testing plain text token retrieval for user: {user_id}")
            
            # Get tokens from database
            tokens = self.get_user_tokens(user_id)
            
            results = {
                "gmail": {"exists": False, "readable": False, "error": None, "debug_mode": False},
                "calendar": {"exists": False, "readable": False, "error": None, "debug_mode": False}
            }
            
            # Test Gmail tokens
            gmail_tokens = tokens.get('gmail_tokens')
            if gmail_tokens:
                results["gmail"]["exists"] = True
                try:
                    processed = self.decrypt_tokens(gmail_tokens)  # Actually just processes plain text
                    if processed:
                        results["gmail"]["readable"] = True
                        results["gmail"]["debug_mode"] = processed.get("debug_mode", False)
                        
                        has_access = 'access_token' in processed and processed['access_token']
                        has_refresh = 'refresh_token' in processed and processed['refresh_token']
                        logger.info(f"🔍 Gmail tokens readable - access_token: {has_access}, refresh_token: {has_refresh}")
                    else:
                        results["gmail"]["error"] = "Processing returned None"
                except Exception as e:
                    results["gmail"]["error"] = str(e)
                    logger.error(f"🔍 Gmail token processing failed: {e}")
            
            # Test Calendar tokens
            calendar_tokens = tokens.get('calendar_tokens')
            if calendar_tokens:
                results["calendar"]["exists"] = True
                try:
                    processed = self.decrypt_tokens(calendar_tokens)  # Actually just processes plain text
                    if processed:
                        results["calendar"]["readable"] = True
                        results["calendar"]["debug_mode"] = processed.get("debug_mode", False)
                        
                        has_access = 'access_token' in processed and processed['access_token']
                        has_refresh = 'refresh_token' in processed and processed['refresh_token']
                        logger.info(f"🔍 Calendar tokens readable - access_token: {has_access}, refresh_token: {has_refresh}")
                    else:
                        results["calendar"]["error"] = "Processing returned None"
                except Exception as e:
                    results["calendar"]["error"] = str(e)
                    logger.error(f"🔍 Calendar token processing failed: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"🔍 Token retrieval test failed: {e}")
            return {"error": str(e)}

# Global instance
_token_service = None

def get_token_service() -> TokenService:
    """Get global token service instance."""
    global _token_service
    if _token_service is None:
        _token_service = TokenService()
    return _token_service

def test_token_service_with_user(user_id: str = "test_user") -> bool:
    """🧪 Test token service with plain text token testing."""
    try:
        logger.info(f"Testing DEBUG token service with user: {user_id}")
        logger.warning("🚨 This is DEBUG MODE - tokens will be plain text!")
        
        token_service = get_token_service()
        
        # Test connection first
        if not token_service.test_connection():
            logger.error("❌ Database connection test failed")
            return False
        
        # 🧪 Test plain text token retrieval
        retrieval_results = token_service.test_token_retrieval(user_id)
        
        if "error" in retrieval_results:
            logger.error(f"❌ Token retrieval test failed: {retrieval_results['error']}")
            return False
        
        # Log detailed results
        logger.info(f"🔍 Token retrieval test results for {user_id}:")
        
        success_count = 0
        total_services = 0
        
        for service, result in retrieval_results.items():
            if service in ["gmail", "calendar"]:
                total_services += 1
                exists = result.get("exists", False)
                readable = result.get("readable", False)
                debug_mode = result.get("debug_mode", False)
                error = result.get("error")
                
                if exists and readable:
                    success_count += 1
                
                status_emoji = "✅" if (exists and readable) else "❌" if exists else "⚪"
                logger.info(f"  {service.title()}: {status_emoji} Exists: {exists}, Readable: {readable}, Debug: {debug_mode}")
                
                if error:
                    logger.error(f"    Error: {error}")
        
        # Test passes if:
        # 1. No tokens exist (user hasn't connected yet), OR
        # 2. All existing tokens are readable
        no_tokens = total_services == 0 or success_count == 0
        all_readable = success_count == total_services
        
        overall_success = no_tokens or all_readable
        
        if overall_success:
            logger.info("✅ DEBUG token service test passed!")
            if success_count > 0:
                logger.info(f"   Successfully read {success_count} plain text token(s)")
        else:
            logger.error("❌ DEBUG token service test failed!")
            logger.error(f"   Only {success_count}/{total_services} tokens readable")
            
        return overall_success
        
    except Exception as e:
        logger.error(f"Token service test failed: {e}")
        return False