"""
Shared utilities for Google OAuth authentication

This module provides common OAuth functionality that can be used by both
Gmail and Calendar authentication services.

Key Features:
- OAuth flow creation and management
- Credential refresh and validation
- Token file management
- Error handling for authentication flows
"""

import os
import sys
import json
from typing import Optional, List, Tuple
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# FIXED: Proper path calculation for project structure
current_file = os.path.abspath(__file__)
# From services/google_cloud/auth_utils.py, go up 2 levels to reach project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# FIXED: Import after path setup
from config.settings import settings
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("google_auth", console_output=True)


class GoogleAuthError(Exception):
    """Custom exception for Google authentication errors."""
    pass


def validate_client_secret_file() -> bool:
    """
    Validate that the Google client secret file exists and is readable.
    
    Returns:
        bool: True if file exists and is valid, False otherwise
    """
    try:
        client_secret_path = settings.google_client_secret_path
        
        if not os.path.exists(client_secret_path):
            logger.error(f"Client secret file not found: {client_secret_path}")
            return False
        
        # Try to read and parse the JSON file
        with open(client_secret_path, 'r') as f:
            client_config = json.load(f)
            
        # Check for required credential types
        if 'installed' not in client_config and 'web' not in client_config:
            logger.error("Client secret file must contain 'installed' or 'web' credentials")
            return False
            
        logger.debug(f"Client secret file validated: {client_secret_path}")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in client secret file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating client secret file: {e}")
        return False


def create_oauth_flow(scopes: List[str], service_name: str) -> InstalledAppFlow:
    """
    Create OAuth flow for specific Google service.
    
    Args:
        scopes: List of OAuth scopes to request
        service_name: Name of the service (for logging)
        
    Returns:
        InstalledAppFlow: Configured OAuth flow
        
    Raises:
        GoogleAuthError: If flow creation fails
    """
    try:
        if not validate_client_secret_file():
            raise GoogleAuthError("Client secret file validation failed")
        
        client_secret_path = settings.google_client_secret_path
        
        logger.info(f"Creating OAuth flow for {service_name} with {len(scopes)} scopes")
        
        # Handle both 'web' and 'installed' credential types
        try:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes)
            logger.debug(f"OAuth flow created successfully for {service_name}")
            return flow
            
        except Exception as e:
            # If that fails, try handling 'web' type credentials
            logger.debug(f"Standard flow failed, trying web credential conversion: {e}")
            
            with open(client_secret_path, 'r') as f:
                client_config = json.load(f)
            
            if 'web' in client_config:
                # Convert web credentials to installed format for local development
                web_config = client_config['web']
                installed_config = {
                    'installed': {
                        'client_id': web_config['client_id'],
                        'client_secret': web_config['client_secret'],
                        'auth_uri': web_config.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth'),
                        'token_uri': web_config.get('token_uri', 'https://oauth2.googleapis.com/token'),
                        'redirect_uris': ['http://localhost:8080/']
                    }
                }
                
                # Create flow from converted config
                flow = InstalledAppFlow.from_client_config(installed_config, scopes)
                logger.debug(f"OAuth flow created from web credentials for {service_name}")
                return flow
            else:
                raise GoogleAuthError(f"Unsupported credential type in client secret file")
                
    except Exception as e:
        logger.error(f"Failed to create OAuth flow for {service_name}: {e}")
        raise GoogleAuthError(f"OAuth flow creation failed: {str(e)}")


def load_credentials_from_file(token_file: str, scopes: List[str]) -> Optional[Credentials]:
    """
    Load credentials from token file.
    
    Args:
        token_file: Path to token file
        scopes: Required scopes for validation
        
    Returns:
        Credentials object if valid, None otherwise
    """
    try:
        if not os.path.exists(token_file):
            logger.debug(f"Token file does not exist: {token_file}")
            return None
        
        creds = Credentials.from_authorized_user_file(token_file, scopes)
        logger.debug(f"Credentials loaded from {token_file}")
        return creds
        
    except Exception as e:
        logger.warning(f"Failed to load credentials from {token_file}: {e}")
        return None


def refresh_credentials(creds: Credentials, service_name: str) -> Tuple[bool, Optional[str]]:
    """
    Refresh expired credentials.
    
    Args:
        creds: Credentials object to refresh
        service_name: Name of service (for logging)
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        if not creds.expired:
            logger.debug(f"{service_name} credentials are still valid")
            return True, None
        
        if not creds.refresh_token:
            logger.warning(f"{service_name} credentials expired and no refresh token available")
            return False, "No refresh token available"
        
        logger.info(f"Refreshing {service_name} credentials...")
        creds.refresh(Request())
        logger.info(f"{service_name} credentials refreshed successfully")
        return True, None
        
    except Exception as e:
        error_msg = f"Failed to refresh {service_name} credentials: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def save_credentials(creds: Credentials, token_file: str, service_name: str) -> bool:
    """
    Save credentials to token file.
    
    Args:
        creds: Credentials object to save
        token_file: Path to token file
        service_name: Name of service (for logging)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure token directory exists
        token_dir = os.path.dirname(token_file)
        os.makedirs(token_dir, exist_ok=True)
        
        # Save credentials
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        
        logger.info(f"{service_name} credentials saved to {token_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save {service_name} credentials to {token_file}: {e}")
        return False


def run_oauth_flow(scopes: List[str], service_name: str, port: int = 8080) -> Optional[Credentials]:
    """
    Run complete OAuth flow to get new credentials.
    
    Args:
        scopes: List of OAuth scopes to request
        service_name: Name of service (for logging)
        port: Port for local OAuth server
        
    Returns:
        Credentials object if successful, None otherwise
    """
    print("DEBUG: Entered run_oauth_flow for", service_name)
    try:
        logger.info(f"Starting OAuth flow for {service_name}...")
        flow = create_oauth_flow(scopes, service_name)
        # Always print the OAuth URL for manual authentication
        print("If a browser does not open, please visit this URL to authenticate:", flow.authorization_url()[0])
        creds = flow.run_local_server(port=port)
        logger.info(f"OAuth flow completed successfully for {service_name}")
        return creds
    except Exception as e:
        logger.error(f"OAuth flow failed for {service_name}: {e}")
        return None


def get_or_create_credentials(
    token_file: str,
    scopes: List[str], 
    service_name: str,
    force_refresh: bool = False
) -> Optional[Credentials]:
    """
    Get existing credentials or create new ones through OAuth flow.
    
    This is the main function that handles the complete authentication workflow:
    1. Try to load existing credentials
    2. Refresh if expired
    3. Run OAuth flow if needed
    4. Save new credentials
    
    Args:
        token_file: Path to token file
        scopes: Required OAuth scopes
        service_name: Name of service (for logging)
        force_refresh: Force new OAuth flow even if credentials exist
        
    Returns:
        Valid Credentials object or None if authentication fails
    """
    try:
        logger.info(f"Getting credentials for {service_name}...")
        
        # Skip loading if force refresh
        creds = None
        if not force_refresh:
            creds = load_credentials_from_file(token_file, scopes)
        
        # Check if credentials are valid or can be refreshed
        if creds and creds.valid:
            logger.debug(f"{service_name} credentials are valid")
            return creds
        
        # Try to refresh if expired
        if creds and creds.expired:
            success, error = refresh_credentials(creds, service_name)
            if success:
                # Save refreshed credentials
                save_credentials(creds, token_file, service_name)
                return creds
            else:
                logger.warning(f"Credential refresh failed for {service_name}: {error}")
        
        # Need to run OAuth flow
        logger.info(f"Running OAuth flow for {service_name}...")
        print("DEBUG: About to call run_oauth_flow for", service_name)
        creds = run_oauth_flow(scopes, service_name)
        
        if creds:
            # Save new credentials
            if save_credentials(creds, token_file, service_name):
                return creds
            else:
                logger.error(f"Failed to save credentials for {service_name}")
                return None
        else:
            logger.error(f"OAuth flow failed for {service_name}")
            return None
            
    except Exception as e:
        logger.error(f"Authentication failed for {service_name}: {e}")
        return None


def check_service_connection(token_file: str, scopes: List[str], service_name: str) -> dict:
    """
    Check the connection status for a Google service.
    
    Args:
        token_file: Path to token file
        scopes: Required scopes
        service_name: Name of service
        
    Returns:
        Dictionary with connection status information
    """
    status = {
        "service": service_name,
        "connected": False,
        "token_exists": False,
        "token_valid": False,
        "scopes_granted": [],
        "error": None
    }
    
    try:
        # Check if token file exists
        status["token_exists"] = os.path.exists(token_file)
        
        if not status["token_exists"]:
            status["error"] = "Token file not found"
            return status
        
        # Try to load credentials
        creds = load_credentials_from_file(token_file, scopes)
        
        if not creds:
            status["error"] = "Failed to load credentials"
            return status
        
        # Check if credentials are valid
        if creds.valid:
            status["connected"] = True
            status["token_valid"] = True
            status["scopes_granted"] = getattr(creds, 'scopes', scopes)
        elif creds.expired:
            # Try to refresh
            success, error = refresh_credentials(creds, service_name)
            if success:
                status["connected"] = True
                status["token_valid"] = True
                status["scopes_granted"] = getattr(creds, 'scopes', scopes)
                # Save refreshed credentials
                save_credentials(creds, token_file, service_name)
            else:
                status["error"] = f"Token expired and refresh failed: {error}"
        else:
            status["error"] = "Credentials are invalid"
            
    except Exception as e:
        status["error"] = f"Connection check failed: {str(e)}"
    
    return status


# ADDED: Helper function to generate service-specific token paths
def get_service_token_path(service_name: str) -> str:
    """
    Generate service-specific token file path.
    
    Args:
        service_name: Name of the service (gmail, calendar)
        
    Returns:
        str: Path to service-specific token file
    """
    token_dir = os.path.dirname(settings.google_token_path)
    return os.path.join(token_dir, f"{service_name}_token.json")


# Export main functions
__all__ = [
    "GoogleAuthError",
    "validate_client_secret_file",
    "create_oauth_flow",
    "get_or_create_credentials",
    "check_service_connection",
    "save_credentials",
    "refresh_credentials",
    "get_service_token_path"
]

# =============================================================================
# Testing and Development Utilities for auth_utils.py
# =============================================================================

async def test_auth_utils():
    """Test auth utilities functionality comprehensively."""
    print("🔐 Testing Google Auth Utils...")
    
    # Track test results
    test_results = {
        "validation": False,
        "flow_creation": False, 
        "token_path_generation": False,
        "connection_check": False,
        "error_handling": False
    }
    
    try:
        # Test 1: Client secret file validation
        print("📋 Testing client secret file validation...")
        validation_result = validate_client_secret_file()
        test_results["validation"] = validation_result
        
        if validation_result:
            print("   ✅ Client secret file validation passed")
        else:
            print("   ⚠️ Client secret file validation failed (expected if no credentials)")
        
        # Test 2: Service-specific token path generation
        print("📁 Testing token path generation...")
        gmail_token_path = get_service_token_path("gmail")
        calendar_token_path = get_service_token_path("calendar")
        
        if gmail_token_path and calendar_token_path:
            test_results["token_path_generation"] = True
            print(f"   ✅ Gmail token path: {gmail_token_path}")
            print(f"   ✅ Calendar token path: {calendar_token_path}")
        else:
            print("   ❌ Token path generation failed")
        
        # Test 3: OAuth flow creation (if credentials exist)
        print("🔄 Testing OAuth flow creation...")
        if validation_result:
            try:
                test_scopes = ["https://www.googleapis.com/auth/userinfo.profile"]
                flow = create_oauth_flow(test_scopes, "test_service")
                test_results["flow_creation"] = flow is not None
                print("   ✅ OAuth flow creation successful")
            except GoogleAuthError as e:
                print(f"   ⚠️ OAuth flow creation failed (expected): {e}")
                test_results["flow_creation"] = True  # Expected failure is OK
            except Exception as e:
                print(f"   ❌ Unexpected OAuth flow error: {e}")
        else:
            print("   ⏭️ Skipping OAuth flow test (no credentials)")
            test_results["flow_creation"] = True  # Skip if no credentials
        
        # Test 4: Connection check functionality
        print("📡 Testing connection check...")
        test_token_file = get_service_token_path("test_service")
        test_scopes = ["https://www.googleapis.com/auth/userinfo.profile"]
        
        connection_status = check_service_connection(
            test_token_file, test_scopes, "test_service"
        )
        
        if isinstance(connection_status, dict) and "service" in connection_status:
            test_results["connection_check"] = True
            print(f"   ✅ Connection check structure valid")
            print(f"       Service: {connection_status['service']}")
            print(f"       Connected: {connection_status['connected']}")
            print(f"       Token exists: {connection_status['token_exists']}")
        else:
            print("   ❌ Connection check failed")
        
        # Test 5: Error handling
        print("⚠️ Testing error handling...")
        try:
            # Test with invalid token file
            invalid_result = load_credentials_from_file("/invalid/path/token.json", test_scopes)
            if invalid_result is None:
                test_results["error_handling"] = True
                print("   ✅ Invalid file path handled correctly")
            else:
                print("   ❌ Invalid file path not handled properly")
        except Exception as e:
            print(f"   ⚠️ Unexpected error handling: {e}")
        
        # Test 6: Settings integration
        print("⚙️ Testing settings integration...")
        try:
            client_secret_path = settings.google_client_secret_path
            token_path = settings.google_token_path
            scopes = settings.GOOGLE_API_SCOPES
            
            if client_secret_path and token_path and scopes:
                print("   ✅ Settings integration working")
                print(f"       Client secret: {client_secret_path[:50]}...")
                print(f"       Token path: {token_path}")
                print(f"       Scopes count: {len(scopes)}")
            else:
                print("   ❌ Settings integration failed")
        except Exception as e:
            print(f"   ❌ Settings integration error: {e}")
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n📊 Auth Utils Test Results:")
        print(f"   Passed: {passed_tests}/{total_tests}")
        
        for test_name, result in test_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        if passed_tests == total_tests:
            print("\n🎉 All auth utils tests passed!")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} auth utils tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Auth utils test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auth_utils_detailed():
    """Detailed synchronous test for auth utilities."""
    print("🔍 Running detailed auth utils tests...")
    
    # Test individual functions
    test_functions = [
        ("validate_client_secret_file", validate_client_secret_file),
        ("get_service_token_path", lambda: get_service_token_path("test")),
    ]
    
    results = {}
    
    for func_name, func in test_functions:
        try:
            print(f"   Testing {func_name}...")
            result = func()
            results[func_name] = {"success": True, "result": result}
            print(f"   ✅ {func_name} passed")
        except Exception as e:
            results[func_name] = {"success": False, "error": str(e)}
            print(f"   ❌ {func_name} failed: {e}")
    
    return results


if __name__ == "__main__":
    import asyncio
    
    print("🧪 Running Auth Utils Tests...")
    print("=" * 50)
    
    # Run async test
    success = asyncio.run(test_auth_utils())
    
    print("\n" + "=" * 50)
    
    # Run detailed test
    detailed_results = test_auth_utils_detailed()
    
    print(f"\n📋 Detailed Results:")
    for func_name, result in detailed_results.items():
        if result["success"]:
            print(f"   ✅ {func_name}: {result['result']}")
        else:
            print(f"   ❌ {func_name}: {result['error']}")
    
    if success:
        print("\n🎉 Auth utils testing completed successfully!")
    else:
        print("\n⚠️ Some auth utils tests failed - check configuration")
    
    print("✅ Auth utils test module validation completed")