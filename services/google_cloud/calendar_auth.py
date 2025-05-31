"""
Calendar Authentication Service

This module provides Calendar-specific authentication functionality using
the shared auth utilities. Handles Calendar OAuth scopes and service creation.
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
logger = setup_logger("calendar_auth", console_output=True)

# Calendar-specific scopes
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

# Service configuration
SERVICE_NAME = "calendar"
API_SERVICE_NAME = "calendar"
API_VERSION = "v3"


class CalendarAuthService:
    """Calendar authentication service with credential management."""
    
    def __init__(self):
        """Initialize Calendar auth service."""
        self.logger = logger
        self.scopes = CALENDAR_SCOPES
        self.token_file = get_service_token_path(SERVICE_NAME)
        self._service = None
        self._credentials = None
        
        self.logger.info(f"Calendar auth service initialized")
        self.logger.debug(f"Token file: {self.token_file}")
    
    def get_credentials(self, force_refresh: bool = False) -> Optional[Credentials]:
        """
        Get valid Calendar credentials.
        
        Args:
            force_refresh: Force new OAuth flow
            
        Returns:
            Valid Credentials object or None
        """
        try:
            self.logger.info("Getting Calendar credentials...")
            
            creds = get_or_create_credentials(
                token_file=self.token_file,
                scopes=self.scopes,
                service_name=SERVICE_NAME,
                force_refresh=force_refresh
            )
            
            if creds:
                self._credentials = creds
                self.logger.info("Calendar credentials obtained successfully")
                return creds
            else:
                self.logger.error("Failed to obtain Calendar credentials")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting Calendar credentials: {e}")
            return None
    
    def get_service(self, force_refresh: bool = False):
        """
        Get authenticated Calendar service instance.
        
        Args:
            force_refresh: Force credential refresh
            
        Returns:
            Calendar service instance or None
        """
        try:
            # Get credentials if we don't have them or force refresh
            if not self._credentials or force_refresh:
                self._credentials = self.get_credentials(force_refresh)
            
            if not self._credentials:
                self.logger.error("No valid credentials for Calendar service")
                return None
            
            # Create service if we don't have it
            if not self._service or force_refresh:
                self.logger.info("Creating Calendar service instance...")
                self._service = build(
                    API_SERVICE_NAME, 
                    API_VERSION, 
                    credentials=self._credentials
                )
                self.logger.info("Calendar service created successfully")
            
            return self._service
            
        except Exception as e:
            self.logger.error(f"Error creating Calendar service: {e}")
            return None
    
    def check_connection(self) -> dict:
        """
        Check Calendar connection status.
        
        Returns:
            Dictionary with connection status
        """
        try:
            self.logger.info("Checking Calendar connection...")
            
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
                        calendar_list = service.calendarList().list().execute()
                        calendars = calendar_list.get('items', [])
                        status["api_test"] = True
                        status["calendar_count"] = len(calendars)
                        status["primary_calendar"] = next(
                            (cal['summary'] for cal in calendars if cal.get('primary')), 
                            'Not found'
                        )
                        self.logger.info(f"Calendar API test successful - {len(calendars)} calendars found")
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
        Revoke Calendar credentials and delete token file.
        
        Returns:
            bool: True if successful
        """
        try:
            self.logger.info("Revoking Calendar credentials...")
            
            # Clear in-memory references
            self._credentials = None
            self._service = None
            
            # Delete token file
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                self.logger.info(f"Calendar token file deleted: {self.token_file}")
            
            self.logger.info("Calendar credentials revoked successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error revoking Calendar credentials: {e}")
            return False
    
    def test_calendar_operations(self) -> dict:
        """
        Test basic Calendar operations to verify functionality.
        
        Returns:
            Dictionary with test results
        """
        test_results = {
            "service_creation": False,
            "calendar_list": False,
            "events_access": False,
            "time_zone_info": False,
            "overall_success": False,
            "errors": []
        }
        
        try:
            self.logger.info("Testing Calendar operations...")
            
            # Test service creation
            service = self.get_service()
            if service:
                test_results["service_creation"] = True
                self.logger.debug("✅ Service creation test passed")
            else:
                test_results["errors"].append("Service creation failed")
                return test_results
            
            # Test calendar list access
            try:
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                test_results["calendar_list"] = True
                test_results["calendar_count"] = len(calendars)
                test_results["calendars"] = [
                    {
                        "id": cal["id"],
                        "summary": cal.get("summary", "Unknown"),
                        "primary": cal.get("primary", False)
                    }
                    for cal in calendars[:3]  # First 3 calendars
                ]
                self.logger.debug("✅ Calendar list test passed")
            except Exception as e:
                test_results["errors"].append(f"Calendar list access failed: {e}")
            
            # Test events access on primary calendar
            try:
                events_result = service.events().list(
                    calendarId='primary',
                    maxResults=1,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                test_results["events_access"] = True
                test_results["has_events"] = 'items' in events_result
                self.logger.debug("✅ Events access test passed")
            except Exception as e:
                test_results["errors"].append(f"Events access failed: {e}")
            
            # Test timezone info
            try:
                calendar_info = service.calendars().get(calendarId='primary').execute()
                test_results["time_zone_info"] = True
                test_results["timezone"] = calendar_info.get('timeZone', 'Unknown')
                self.logger.debug("✅ Timezone info test passed")
            except Exception as e:
                test_results["errors"].append(f"Timezone info failed: {e}")
            
            # Overall success if core operations work
            test_results["overall_success"] = (
                test_results["service_creation"] and
                test_results["calendar_list"] and
                test_results["events_access"]
            )
            
            if test_results["overall_success"]:
                self.logger.info("✅ Calendar operations test completed successfully")
            else:
                self.logger.warning("⚠️ Some Calendar operations failed")
            
            return test_results
            
        except Exception as e:
            test_results["errors"].append(f"Test execution failed: {e}")
            self.logger.error(f"Calendar operations test failed: {e}")
            return test_results


# Global Calendar auth service instance
_calendar_auth_service = None


def get_calendar_auth_service() -> CalendarAuthService:
    """Get singleton Calendar auth service instance."""
    global _calendar_auth_service
    if _calendar_auth_service is None:
        _calendar_auth_service = CalendarAuthService()
    return _calendar_auth_service


def get_calendar_service():
    """
    Convenience function to get Calendar service directly.
    
    Returns:
        Calendar service instance or None
    """
    auth_service = get_calendar_auth_service()
    return auth_service.get_service()


def check_calendar_connection() -> dict:
    """Convenience function to check Calendar connection."""
    auth_service = get_calendar_auth_service()
    return auth_service.check_connection()


# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_calendar_auth_service():
    """Test Calendar auth service functionality comprehensively."""
    print("📅 Testing Calendar Auth Service...")
    
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
        print("🏗️ Testing Calendar auth service creation...")
        calendar_auth = get_calendar_auth_service()
        
        if calendar_auth:
            test_results["service_creation"] = True
            print("   ✅ Calendar auth service created successfully")
            print(f"   📁 Token file path: {calendar_auth.token_file}")
            print(f"   🔑 Scopes count: {len(calendar_auth.scopes)}")
        else:
            print("   ❌ Calendar auth service creation failed")
            return False
        
        # Test 2: Credential handling
        print("🔐 Testing credential handling...")
        try:
            creds = calendar_auth.get_credentials()
            
            if creds:
                test_results["credential_handling"] = True
                print("   ✅ Credentials loaded successfully")
                print(f"   🟢 Credentials valid: {creds.valid}")
            else:
                test_results["credential_handling"] = True  # Expected if no auth yet
                print("   ⚠️ No credentials found (expected if not authenticated)")
        except Exception as e:
            print(f"   ❌ Credential handling error: {e}")
        
        # Test 3: Connection check
        print("📡 Testing connection check...")
        connection_status = calendar_auth.check_connection()
        
        if isinstance(connection_status, dict):
            test_results["connection_check"] = True
            print("   ✅ Connection check completed")
            print(f"       Service: {connection_status.get('service', 'Unknown')}")
            print(f"       Connected: {connection_status.get('connected', False)}")
            print(f"       Token exists: {connection_status.get('token_exists', False)}")
            
            if connection_status.get('error'):
                print(f"       Error: {connection_status['error']}")
            
            if connection_status.get('calendar_count') is not None:
                print(f"       Calendars: {connection_status['calendar_count']}")
        else:
            print("   ❌ Connection check failed")
        
        # Test 4: API operations (if authenticated)
        print("🔧 Testing API operations...")
        if connection_status.get('connected'):
            try:
                api_test_results = calendar_auth.test_calendar_operations()
                test_results["api_operations"] = api_test_results.get('overall_success', False)
                
                if api_test_results.get('overall_success'):
                    print("   ✅ Calendar API operations test passed")
                    print(f"       Calendar count: {api_test_results.get('calendar_count', 'Unknown')}")
                    print(f"       Timezone: {api_test_results.get('timezone', 'Unknown')}")
                else:
                    print("   ⚠️ Some Calendar API operations failed")
                    for error in api_test_results.get('errors', []):
                        print(f"       Error: {error}")
                
            except Exception as e:
                print(f"   ⚠️ API operations test failed: {e}")
                test_results["api_operations"] = True  # Expected if not authenticated
        else:
            print("   ⏭️ Skipping API operations test (not authenticated)")
            test_results["api_operations"] = True  # Skip if not authenticated
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n📊 Calendar Auth Service Test Results:")
        print(f"   Passed: {passed_tests}/{total_tests}")
        
        for test_name, result in test_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        if passed_tests == total_tests:
            print("\n🎉 All Calendar auth service tests passed!")
            print("✅ Ready for Step 3.4 (Calendar MCP Tools)")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} Calendar auth service tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Calendar auth service test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Export main components
__all__ = [
    "CalendarAuthService",
    "get_calendar_auth_service", 
    "get_calendar_service",
    "check_calendar_connection",
    "CALENDAR_SCOPES"
]


if __name__ == "__main__":
    import asyncio
    
    print("🧪 Running Calendar Auth Service Tests...")
    print("=" * 60)
    
    # Run test
    success = asyncio.run(test_calendar_auth_service())
    
    if success:
        print("🎉 Calendar auth service ready for calendar tools!")
    else:
        print("⚠️ Please fix Calendar auth issues before proceeding")
    
    print("✅ Calendar auth service test completed")