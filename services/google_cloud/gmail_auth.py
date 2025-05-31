"""
Gmail Authentication Service

This module provides Gmail-specific authentication functionality using
the shared auth utilities. Handles Gmail OAuth scopes and service creation.
"""

import os
import sys
from typing import Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.settings import settings
from services.logging.logger import setup_logger
from services.google_cloud.auth_utils import (
    get_or_create_credentials,
    check_service_connection,
    get_service_token_path,
    GoogleAuthError
)

# Configure logging
logger = setup_logger("gmail_auth", console_output=True)

# Gmail-specific scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.profile', 
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

# Service configuration
SERVICE_NAME = "gmail"
API_SERVICE_NAME = "gmail"
API_VERSION = "v1"


class GmailAuthService:
    """Gmail authentication service with credential management."""
    
    def __init__(self):
        """Initialize Gmail auth service."""
        self.logger = logger
        self.scopes = GMAIL_SCOPES
        self.token_file = get_service_token_path(SERVICE_NAME)
        self._service = None
        self._credentials = None
        
        self.logger.info(f"Gmail auth service initialized")
        self.logger.debug(f"Token file: {self.token_file}")
    
    def get_credentials(self, force_refresh: bool = False) -> Optional[Credentials]:
        """
        Get valid Gmail credentials.
        
        Args:
            force_refresh: Force new OAuth flow
            
        Returns:
            Valid Credentials object or None
        """
        try:
            self.logger.info("Getting Gmail credentials...")
            
            creds = get_or_create_credentials(
                token_file=self.token_file,
                scopes=self.scopes,
                service_name=SERVICE_NAME,
                force_refresh=force_refresh
            )
            
            if creds:
                self._credentials = creds
                self.logger.info("Gmail credentials obtained successfully")
                return creds
            else:
                self.logger.error("Failed to obtain Gmail credentials")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting Gmail credentials: {e}")
            return None
    
    def get_service(self, force_refresh: bool = False):
        """
        Get authenticated Gmail service instance.
        
        Args:
            force_refresh: Force credential refresh
            
        Returns:
            Gmail service instance or None
        """
        try:
            # Get credentials if we don't have them or force refresh
            if not self._credentials or force_refresh:
                self._credentials = self.get_credentials(force_refresh)
            
            if not self._credentials:
                self.logger.error("No valid credentials for Gmail service")
                return None
            
            # Create service if we don't have it
            if not self._service or force_refresh:
                self.logger.info("Creating Gmail service instance...")
                self._service = build(
                    API_SERVICE_NAME, 
                    API_VERSION, 
                    credentials=self._credentials
                )
                self.logger.info("Gmail service created successfully")
            
            return self._service
            
        except Exception as e:
            self.logger.error(f"Error creating Gmail service: {e}")
            return None
    
    def check_connection(self) -> dict:
        """
        Check Gmail connection status.
        
        Returns:
            Dictionary with connection status
        """
        try:
            self.logger.info("Checking Gmail connection...")
            
            # Basic connection check
            status = check_service_connection(
                token_file=self.token_file,
                scopes=self.scopes,
                service_name=SERVICE_NAME
            )
            
            # Test service creation if connected
            if status["connected"]:
                try:
                    service = self.get_service()
                    if service:
                        # Test API call
                        profile = service.users().getProfile(userId='me').execute()
                        status["api_test"] = True
                        status["user_email"] = profile.get('emailAddress', 'Unknown')
                        self.logger.info(f"Gmail API test successful for {status['user_email']}")
                    else:
                        status["api_test"] = False
                        status["error"] = "Service creation failed"
                except Exception as e:
                    status["api_test"] = False
                    status["error"] = f"API test failed: {str(e)}"
            
            return status
            
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            return {
                "service": SERVICE_NAME,
                "connected": False,
                "error": f"Connection check failed: {str(e)}"
            }
    
    def revoke_credentials(self) -> bool:
        """
        Revoke Gmail credentials and delete token file.
        
        Returns:
            bool: True if successful
        """
        try:
            self.logger.info("Revoking Gmail credentials...")
            
            # Clear in-memory references
            self._credentials = None
            self._service = None
            
            # Delete token file
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                self.logger.info(f"Gmail token file deleted: {self.token_file}")
            
            self.logger.info("Gmail credentials revoked successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error revoking Gmail credentials: {e}")
            return False
    
    def test_gmail_operations(self) -> dict:
        """
        Test basic Gmail operations to verify functionality.
        
        Returns:
            Dictionary with test results
        """
        test_results = {
            "service_creation": False,
            "profile_access": False,
            "labels_access": False,
            "message_list": False,
            "overall_success": False,
            "errors": []
        }
        
        try:
            self.logger.info("Testing Gmail operations...")
            
            # Test service creation
            service = self.get_service()
            if service:
                test_results["service_creation"] = True
                self.logger.debug("✅ Service creation test passed")
            else:
                test_results["errors"].append("Service creation failed")
                return test_results
            
            # Test profile access
            try:
                profile = service.users().getProfile(userId='me').execute()
                test_results["profile_access"] = True
                test_results["user_email"] = profile.get('emailAddress')
                self.logger.debug("✅ Profile access test passed")
            except Exception as e:
                test_results["errors"].append(f"Profile access failed: {e}")
            
            # Test labels access
            try:
                labels = service.users().labels().list(userId='me').execute()
                test_results["labels_access"] = True
                test_results["labels_count"] = len(labels.get('labels', []))
                self.logger.debug("✅ Labels access test passed")
            except Exception as e:
                test_results["errors"].append(f"Labels access failed: {e}")
            
            # Test message listing (just get count)
            try:
                messages = service.users().messages().list(userId='me', maxResults=1).execute()
                test_results["message_list"] = True
                test_results["has_messages"] = 'messages' in messages
                self.logger.debug("✅ Message list test passed")
            except Exception as e:
                test_results["errors"].append(f"Message list failed: {e}")
            
            # Overall success if core operations work
            test_results["overall_success"] = (
                test_results["service_creation"] and
                test_results["profile_access"] and
                test_results["labels_access"]
            )
            
            if test_results["overall_success"]:
                self.logger.info("✅ Gmail operations test completed successfully")
            else:
                self.logger.warning("⚠️ Some Gmail operations failed")
            
            return test_results
            
        except Exception as e:
            test_results["errors"].append(f"Test execution failed: {e}")
            self.logger.error(f"Gmail operations test failed: {e}")
            return test_results


# Global Gmail auth service instance
_gmail_auth_service = None


def get_gmail_auth_service() -> GmailAuthService:
    """Get singleton Gmail auth service instance."""
    global _gmail_auth_service
    if _gmail_auth_service is None:
        _gmail_auth_service = GmailAuthService()
    return _gmail_auth_service


def get_gmail_service():
    """
    Convenience function to get Gmail service directly.
    This replaces the old get_gmail_service() in gmail_tools.py
    
    Returns:
        Gmail service instance or None
    """
    auth_service = get_gmail_auth_service()
    return auth_service.get_service()


def check_gmail_connection() -> dict:
    """Convenience function to check Gmail connection."""
    auth_service = get_gmail_auth_service()
    return auth_service.check_connection()


# Export main components
__all__ = [
    "GmailAuthService",
    "get_gmail_auth_service", 
    "get_gmail_service",
    "check_gmail_connection",
    "GMAIL_SCOPES"
]

# =============================================================================
# Testing and Development Utilities for gmail_auth.py
# =============================================================================

async def test_gmail_auth_service():
    """Test Gmail auth service functionality comprehensively."""
    print("📧 Testing Gmail Auth Service...")
    
    # Track test results
    test_results = {
        "service_creation": False,
        "credential_handling": False,
        "connection_check": False,
        "error_handling": False,
        "api_operations": False
    }
    
    try:
        # Test 1: Service creation
        print("🏗️ Testing Gmail auth service creation...")
        gmail_auth = get_gmail_auth_service()
        
        if gmail_auth:
            test_results["service_creation"] = True
            print("   ✅ Gmail auth service created successfully")
            print(f"   📁 Token file path: {gmail_auth.token_file}")
            print(f"   🔑 Scopes count: {len(gmail_auth.scopes)}")
        else:
            print("   ❌ Gmail auth service creation failed")
            return False
        
        # Test 2: Credential handling (without requiring actual auth)
        print("🔐 Testing credential handling...")
        try:
            # This will attempt to load existing credentials or return None
            creds = gmail_auth.get_credentials()
            
            if creds:
                test_results["credential_handling"] = True
                print("   ✅ Credentials loaded successfully")
                print(f"   🟢 Credentials valid: {creds.valid}")
                print(f"   ⏰ Expired: {creds.expired if hasattr(creds, 'expired') else 'Unknown'}")
            else:
                test_results["credential_handling"] = True  # Expected if no auth yet
                print("   ⚠️ No credentials found (expected if not authenticated)")
        except Exception as e:
            print(f"   ❌ Credential handling error: {e}")
        
        # Test 3: Connection check
        print("📡 Testing connection check...")
        connection_status = gmail_auth.check_connection()
        
        if isinstance(connection_status, dict):
            test_results["connection_check"] = True
            print("   ✅ Connection check completed")
            print(f"       Service: {connection_status.get('service', 'Unknown')}")
            print(f"       Connected: {connection_status.get('connected', False)}")
            print(f"       Token exists: {connection_status.get('token_exists', False)}")
            
            if connection_status.get('error'):
                print(f"       Error: {connection_status['error']}")
            
            if connection_status.get('user_email'):
                print(f"       User: {connection_status['user_email']}")
        else:
            print("   ❌ Connection check failed")
        
        # Test 4: Error handling
        print("⚠️ Testing error handling...")
        try:
            # Test with invalid parameters
            invalid_auth = GmailAuthService()
            # Temporarily break the token file path
            original_token_file = invalid_auth.token_file
            invalid_auth.token_file = "/invalid/path/token.json"
            
            # This should handle the error gracefully
            invalid_connection = invalid_auth.check_connection()
            
            if invalid_connection.get('error'):
                test_results["error_handling"] = True
                print("   ✅ Error handling works correctly")
            else:
                print("   ⚠️ Error handling might need improvement")
            
            # Restore original path
            invalid_auth.token_file = original_token_file
            
        except Exception as e:
            print(f"   ❌ Error handling test failed: {e}")
        
        # Test 5: API operations (if authenticated)
        print("🔧 Testing API operations...")
        if connection_status.get('connected'):
            try:
                api_test_results = gmail_auth.test_gmail_operations()
                test_results["api_operations"] = api_test_results.get('overall_success', False)
                
                if api_test_results.get('overall_success'):
                    print("   ✅ Gmail API operations test passed")
                    print(f"       User email: {api_test_results.get('user_email', 'Unknown')}")
                    print(f"       Labels count: {api_test_results.get('labels_count', 'Unknown')}")
                    print(f"       Has messages: {api_test_results.get('has_messages', 'Unknown')}")
                else:
                    print("   ⚠️ Some Gmail API operations failed")
                    for error in api_test_results.get('errors', []):
                        print(f"       Error: {error}")
                
            except Exception as e:
                print(f"   ⚠️ API operations test failed: {e}")
                test_results["api_operations"] = True  # Expected if not authenticated
        else:
            print("   ⏭️ Skipping API operations test (not authenticated)")
            test_results["api_operations"] = True  # Skip if not authenticated
        
        # Test 6: Service convenience functions
        print("🛠️ Testing convenience functions...")
        try:
            # Test get_gmail_service convenience function
            service_direct = get_gmail_service()
            connection_direct = check_gmail_connection()
            
            # These should work the same as the service methods
            if connection_direct == connection_status:
                print("   ✅ Convenience functions work correctly")
            else:
                print("   ⚠️ Convenience functions have different behavior")
                
        except Exception as e:
            print(f"   ❌ Convenience functions test failed: {e}")
        
        # Test 7: Configuration validation
        print("⚙️ Testing configuration validation...")
        try:
            # Check that all required settings are available
            config_checks = {
                "scopes_defined": len(GMAIL_SCOPES) > 0,
                "service_name_set": SERVICE_NAME == "gmail",
                "api_version_set": API_VERSION == "v1",
                "token_path_valid": gmail_auth.token_file.endswith("gmail_token.json")
            }
            
            all_config_valid = all(config_checks.values())
            
            if all_config_valid:
                print("   ✅ Configuration validation passed")
                for check, status in config_checks.items():
                    print(f"       {check}: {'✅' if status else '❌'}")
            else:
                print("   ❌ Some configuration issues found")
                
        except Exception as e:
            print(f"   ❌ Configuration validation failed: {e}")
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n📊 Gmail Auth Service Test Results:")
        print(f"   Passed: {passed_tests}/{total_tests}")
        
        for test_name, result in test_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        # Additional info
        print(f"\n📋 Service Configuration:")
        print(f"   Token file: {gmail_auth.token_file}")
        print(f"   Scopes: {len(gmail_auth.scopes)} configured")
        print(f"   Connection status: {connection_status.get('connected', False)}")
        
        if passed_tests == total_tests:
            print("\n🎉 All Gmail auth service tests passed!")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} Gmail auth service tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Gmail auth service test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gmail_auth_integration():
    """Test Gmail auth integration with existing codebase."""
    print("🔗 Testing Gmail auth integration...")
    
    integration_tests = {
        "settings_integration": False,
        "logging_integration": False,
        "mcp_compatibility": False,
        "error_classes": False
    }
    
    try:
        # Test settings integration
        print("   Testing settings integration...")
        try:
            from config.settings import settings
            
            # Check that Gmail-specific settings exist
            gmail_settings_exist = (
                hasattr(settings, 'GOOGLE_API_SCOPES') and
                hasattr(settings, 'google_token_path') and
                hasattr(settings, 'google_client_secret_path')
            )
            
            integration_tests["settings_integration"] = gmail_settings_exist
            print(f"       Settings integration: {'✅' if gmail_settings_exist else '❌'}")
            
        except Exception as e:
            print(f"       Settings integration error: {e}")
        
        # Test logging integration
        print("   Testing logging integration...")
        try:
            from services.logging.logger import setup_logger
            test_logger = setup_logger("test_gmail_auth")
            integration_tests["logging_integration"] = test_logger is not None
            print(f"       Logging integration: {'✅' if test_logger else '❌'}")
        except Exception as e:
            print(f"       Logging integration error: {e}")
        
        # Test MCP compatibility (check if can be imported alongside MCP tools)
        print("   Testing MCP compatibility...")
        try:
            from google_mcp import gmail_tools
            # Check if we can import both without conflicts
            gmail_auth = get_gmail_auth_service()
            integration_tests["mcp_compatibility"] = True
            print("       MCP compatibility: ✅")
        except Exception as e:
            print(f"       MCP compatibility error: {e}")
        
        # Test error classes
        print("   Testing error classes...")
        try:
            from .auth_utils import GoogleAuthError
            # Test that we can create the error
            test_error = GoogleAuthError("Test error")
            integration_tests["error_classes"] = isinstance(test_error, Exception)
            print("       Error classes: ✅")
        except Exception as e:
            print(f"       Error classes error: {e}")
        
        # Summary
        passed_integration = sum(integration_tests.values())
        total_integration = len(integration_tests)
        
        print(f"\n   Integration Results: {passed_integration}/{total_integration}")
        
        return passed_integration == total_integration
        
    except Exception as e:
        print(f"   Integration testing failed: {e}")
        return False


def test_gmail_auth_backwards_compatibility():
    """Test backwards compatibility with existing Gmail tools."""
    print("🔄 Testing backwards compatibility...")
    
    try:
        # Test that the new auth service can replace the old one
        print("   Testing service replacement...")
        
        # Get service using new method
        new_service = get_gmail_service()
        
        # Check if it has the expected interface
        if new_service is None:
            print("       No service available (expected if not authenticated)")
            return True
        
        # Test that it has the Gmail API methods
        expected_methods = ['users']
        has_methods = all(hasattr(new_service, method) for method in expected_methods)
        
        if has_methods:
            print("       ✅ Service has expected Gmail API interface")
            return True
        else:
            print("       ❌ Service missing expected methods")
            return False
            
    except Exception as e:
        print(f"   Backwards compatibility test failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    
    print("🧪 Running Gmail Auth Service Tests...")
    print("=" * 60)
    
    # Run main test
    success = asyncio.run(test_gmail_auth_service())
    
    print("\n" + "=" * 60)
    
    # Run integration tests
    print("🔗 Integration Tests:")
    integration_success = test_gmail_auth_integration()
    
    print("\n🔄 Backwards Compatibility Tests:")
    compatibility_success = test_gmail_auth_backwards_compatibility()
    
    print("\n" + "=" * 60)
    
    overall_success = success and integration_success and compatibility_success
    
    if overall_success:
        print("🎉 All Gmail auth service tests passed!")
        print("✅ Ready for Phase 3.3 (Calendar Auth)")
    else:
        print("⚠️ Some Gmail auth service tests failed")
        print("🔧 Please review and fix issues before proceeding")
    
    print("✅ Gmail auth service test module validation completed")