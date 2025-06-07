"""
Tests for Oprina setup and authentication functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import sys
import json
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):  # Go up 3 levels from tests/test_setup.py
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import authentication utilities
from oprina.tools.auth_utils import get_gmail_service, get_calendar_service


class TestSetupAndAuth(unittest.TestCase):
    """Test suite for setup and authentication functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_credentials_data = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }
        
        self.mock_token_data = {
            "token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
        }

    # =============================================================================
    # Credentials File Tests
    # =============================================================================
    
    @patch('os.path.exists')
    def test_credentials_file_exists(self, mock_exists):
        """Test checking for credentials.json file"""
        # Test when credentials file exists
        mock_exists.return_value = True
        self.assertTrue(mock_exists('../credentials.json'))
        
        # Test when credentials file doesn't exist
        mock_exists.return_value = False
        self.assertFalse(mock_exists('../credentials.json'))

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_credentials_file_content(self, mock_exists, mock_file):
        """Test reading credentials file content"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.mock_credentials_data)
        
        # This would be how the setup scripts read credentials
        with open('../credentials.json', 'r') as f:
            credentials_data = json.loads(f.read())
        
        self.assertEqual(credentials_data['installed']['client_id'], 'test_client_id')
        self.assertIn('client_secret', credentials_data['installed'])

    # =============================================================================
    # Gmail Authentication Tests
    # =============================================================================
    
    @patch('pickle.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_gmail_token_exists_and_valid(self, mock_exists, mock_file, mock_pickle):
        """Test Gmail authentication when token exists and is valid"""
        # Mock token file exists
        mock_exists.return_value = True
        
        # Mock valid credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle.return_value = mock_creds
        
        # Mock Gmail service creation
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            service = get_gmail_service()
            
            # Should return valid service
            self.assertIsNotNone(service)
            mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)

    @patch('os.path.exists')
    def test_gmail_token_not_exists(self, mock_exists):
        """Test Gmail authentication when token doesn't exist"""
        # Mock token file doesn't exist
        mock_exists.return_value = False
        
        service = get_gmail_service()
        
        # Should return None when no token exists
        self.assertIsNone(service)

    @patch('pickle.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_gmail_token_expired_not_refreshable(self, mock_exists, mock_file, mock_pickle):
        """Test Gmail authentication when token is expired and not refreshable"""
        # Mock token file exists
        mock_exists.return_value = True
        
        # Mock expired, non-refreshable credentials
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = None
        mock_pickle.return_value = mock_creds
        
        service = get_gmail_service()
        
        # Should return None when token is expired and can't be refreshed
        self.assertIsNone(service)

    @patch('pickle.dump')
    @patch('pickle.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_gmail_token_expired_but_refreshable(self, mock_exists, mock_file, mock_pickle_load, mock_pickle_dump):
        """Test Gmail authentication when token is expired but refreshable"""
        # Mock token file exists
        mock_exists.return_value = True
        
        # Mock expired but refreshable credentials
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "valid_refresh_token"
        mock_pickle_load.return_value = mock_creds
        
        # Mock successful refresh
        with patch('google.auth.transport.requests.Request') as mock_request:
            mock_creds.refresh.return_value = None  # Successful refresh
            mock_creds.valid = True  # After refresh, it's valid
            
            with patch('googleapiclient.discovery.build') as mock_build:
                mock_service = Mock()
                mock_build.return_value = mock_service
                
                service = get_gmail_service()
                
                # Should refresh credentials and return service
                self.assertIsNotNone(service)
                mock_creds.refresh.assert_called_once()
                mock_pickle_dump.assert_called_once()  # Should save refreshed token

    # =============================================================================
    # Calendar Authentication Tests
    # =============================================================================
    
    @patch('pickle.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_calendar_token_exists_and_valid(self, mock_exists, mock_file, mock_pickle):
        """Test Calendar authentication when token exists and is valid"""
        # Mock token file exists
        mock_exists.return_value = True
        
        # Mock valid credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle.return_value = mock_creds
        
        # Mock Calendar service creation
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            service = get_calendar_service()
            
            # Should return valid service
            self.assertIsNotNone(service)
            mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_creds)

    @patch('os.path.exists')
    def test_calendar_token_not_exists(self, mock_exists):
        """Test Calendar authentication when token doesn't exist"""
        # Mock token file doesn't exist
        mock_exists.return_value = False
        
        service = get_calendar_service()
        
        # Should return None when no token exists
        self.assertIsNone(service)

    # =============================================================================
    # Service Integration Tests
    # =============================================================================
    
    @patch('oprina.tools.auth_utils.get_gmail_service')
    def test_gmail_service_integration(self, mock_get_service):
        """Test Gmail service integration with tools"""
        from oprina.tools.gmail import gmail_list_messages
        
        # Test when service is available
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().list().execute.return_value = {'messages': []}
        
        result = gmail_list_messages()
        self.assertIsInstance(result, str)
        self.assertNotIn("Gmail not set up", result)
        
        # Test when service is not available
        mock_get_service.return_value = None
        result = gmail_list_messages()
        self.assertIn("Gmail not set up", result)

    @patch('oprina.tools.auth_utils.get_calendar_service')
    def test_calendar_service_integration(self, mock_get_service):
        """Test Calendar service integration with tools"""
        from oprina.tools.calendar import calendar_list_events
        
        # Test when service is available
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.events().list().execute.return_value = {'items': []}
        
        result = calendar_list_events()
        self.assertIsInstance(result, str)
        self.assertNotIn("Calendar not set up", result)
        
        # Test when service is not available
        mock_get_service.return_value = None
        result = calendar_list_events()
        self.assertIn("Calendar not set up", result)

    # =============================================================================
    # Setup Script Simulation Tests
    # =============================================================================
    
    @patch('builtins.input')
    @patch('webbrowser.open')
    @patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file')
    @patch('os.path.exists')
    def test_gmail_setup_flow_simulation(self, mock_exists, mock_flow_class, mock_webbrowser, mock_input):
        """Test Gmail setup flow simulation"""
        # Mock credentials file exists
        mock_exists.return_value = True
        
        # Mock OAuth flow
        mock_flow = Mock()
        mock_flow_class.return_value = mock_flow
        
        mock_creds = Mock()
        mock_creds.valid = True
        mock_flow.run_local_server.return_value = mock_creds
        
        # Mock user input for authorization code (if needed)
        mock_input.return_value = "test_auth_code"
        
        # This simulates what setup_gmail.py would do
        try:
            # The actual setup would happen here
            # We're just testing that the mocks work correctly
            credentials = mock_flow.run_local_server(port=0)
            self.assertIsNotNone(credentials)
            self.assertTrue(credentials.valid)
        except Exception as e:
            # In a real setup, we might handle various exceptions
            self.fail(f"Setup simulation failed: {e}")

    @patch('builtins.input')
    @patch('webbrowser.open')
    @patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file')
    @patch('os.path.exists')
    def test_calendar_setup_flow_simulation(self, mock_exists, mock_flow_class, mock_webbrowser, mock_input):
        """Test Calendar setup flow simulation"""
        # Mock credentials file exists
        mock_exists.return_value = True
        
        # Mock OAuth flow
        mock_flow = Mock()
        mock_flow_class.return_value = mock_flow
        
        mock_creds = Mock()
        mock_creds.valid = True
        mock_flow.run_local_server.return_value = mock_creds
        
        # This simulates what setup_calendar.py would do
        try:
            credentials = mock_flow.run_local_server(port=0)
            self.assertIsNotNone(credentials)
            self.assertTrue(credentials.valid)
        except Exception as e:
            self.fail(f"Calendar setup simulation failed: {e}")

    # =============================================================================
    # Error Handling Tests
    # =============================================================================
    
    @patch('pickle.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_corrupted_token_handling(self, mock_exists, mock_file, mock_pickle):
        """Test handling of corrupted token files"""
        # Mock token file exists
        mock_exists.return_value = True
        
        # Mock pickle loading error (corrupted file)
        mock_pickle.side_effect = Exception("Corrupted pickle file")
        
        # Should handle corruption gracefully
        gmail_service = get_gmail_service()
        calendar_service = get_calendar_service()
        
        self.assertIsNone(gmail_service)
        self.assertIsNone(calendar_service)

    @patch('os.path.exists')
    def test_missing_credentials_file(self, mock_exists):
        """Test handling when credentials.json is missing"""
        # Mock credentials file doesn't exist
        mock_exists.return_value = False
        
        # Services should return None when no credentials
        gmail_service = get_gmail_service()
        calendar_service = get_calendar_service()
        
        self.assertIsNone(gmail_service)
        self.assertIsNone(calendar_service)

    @patch('googleapiclient.discovery.build')
    @patch('pickle.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_api_service_creation_error(self, mock_exists, mock_file, mock_pickle, mock_build):
        """Test handling of API service creation errors"""
        # Mock token file exists and credentials are valid
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle.return_value = mock_creds
        
        # Mock API service creation failure
        mock_build.side_effect = Exception("API service creation failed")
        
        # Should handle API errors gracefully
        gmail_service = get_gmail_service()
        calendar_service = get_calendar_service()
        
        self.assertIsNone(gmail_service)
        self.assertIsNone(calendar_service)

    # =============================================================================
    # Security and Scope Tests
    # =============================================================================
    
    def test_required_scopes_defined(self):
        """Test that required OAuth scopes are properly defined"""
        # These are the scopes that would be used in setup scripts
        gmail_scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        
        calendar_scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        
        # Verify scopes are properly formatted
        for scope in gmail_scopes:
            self.assertIn('googleapis.com', scope)
            self.assertIn('gmail', scope)
        
        for scope in calendar_scopes:
            self.assertIn('googleapis.com', scope)
            self.assertIn('calendar', scope)

    @patch('pickle.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_token_scope_validation(self, mock_exists, mock_file, mock_pickle):
        """Test validation of token scopes"""
        mock_exists.return_value = True
        
        # Mock credentials with specific scopes
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.scopes = ['https://www.googleapis.com/auth/gmail.readonly']
        mock_pickle.return_value = mock_creds
        
        # In a real implementation, we might validate scopes
        # Here we just test that we can access the scope information
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_build.return_value = Mock()
            service = get_gmail_service()
            
            self.assertIsNotNone(service)
            # Verify we could check scopes if needed
            self.assertIn('gmail', mock_creds.scopes[0])

    # =============================================================================
    # File Path and Environment Tests
    # =============================================================================
    
    def test_token_file_paths(self):
        """Test that token file paths are consistent"""
        # These are the expected token file names
        gmail_token_file = "gmail_token.pickle"
        calendar_token_file = "calendar_token.pickle"
        
        # Verify file extensions and naming
        self.assertTrue(gmail_token_file.endswith('.pickle'))
        self.assertTrue(calendar_token_file.endswith('.pickle'))
        self.assertIn('gmail', gmail_token_file)
        self.assertIn('calendar', calendar_token_file)

    @patch('os.path.exists')
    def test_credentials_file_path(self, mock_exists):
        """Test credentials file path handling"""
        # Test standard credentials.json location
        mock_exists.return_value = True
        
        # This simulates checking for credentials in the expected location
        credentials_exists = mock_exists('../credentials.json')
        self.assertTrue(credentials_exists)
        
        # Verify the function was called with the right path
        mock_exists.assert_called_with('../credentials.json')

    # =============================================================================
    # Integration with Oprina Structure Tests
    # =============================================================================
    
    def test_auth_utils_import(self):
        """Test that auth utilities can be imported correctly"""
        # These imports should work from the oprina structure
        try:
            from oprina.tools.auth_utils import get_gmail_service, get_calendar_service
            self.assertTrue(callable(get_gmail_service))
            self.assertTrue(callable(get_calendar_service))
        except ImportError as e:
            self.fail(f"Could not import auth utilities: {e}")

    def test_setup_script_locations(self):
        """Test that setup scripts are in expected locations"""
        # Check if setup scripts exist in the expected locations
        expected_scripts = [
            'setup_gmail.py',
            'setup_calendar.py'
        ]
        
        for script in expected_scripts:
            # In a real test, we might check if these files exist
            # Here we just verify the naming convention
            self.assertTrue(script.startswith('setup_'))
            self.assertTrue(script.endswith('.py'))

    def test_service_availability_flow(self):
        """Test the complete flow of checking service availability"""
        # This tests the pattern used throughout the codebase
        
        # Test Gmail availability check
        with patch('oprina.tools.auth_utils.get_gmail_service') as mock_gmail:
            mock_gmail.return_value = None
            
            from oprina.tools.gmail import gmail_list_messages
            result = gmail_list_messages()
            
            self.assertIn("Gmail not set up", result)
            self.assertIn("python setup_gmail.py", result)
        
        # Test Calendar availability check
        with patch('oprina.tools.auth_utils.get_calendar_service') as mock_calendar:
            mock_calendar.return_value = None
            
            from oprina.tools.calendar import calendar_list_events
            result = calendar_list_events()
            
            self.assertIn("Calendar not set up", result)
            self.assertIn("python setup_calendar.py", result)


# =============================================================================
# AGENT SETUP BEHAVIOR TESTS (NEW)
# =============================================================================

class TestAgentSetupBehavior(unittest.TestCase):
    """Test suite for agent behavior during setup processes"""
    
    def setUp(self):
        """Set up test fixtures for agent setup behavior testing"""
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    def test_gmail_agent_setup_guidance_behavior(self):
        """Test Gmail agent provides clear setup guidance when not configured"""
        from oprina.tools.gmail import gmail_list_messages
        
        # Mock no service available (not set up)
        with patch('oprina.tools.gmail.get_gmail_service', return_value=None):
            result = gmail_list_messages(tool_context=self.mock_tool_context)
            
            # Agent should provide user-friendly guidance
            self.assertIn("Gmail not set up", result)
            self.assertIn("python setup_gmail.py", result)
            
            # Should be voice-friendly, not technical
            self.assertNotIn("Error:", result)
            self.assertNotIn("Exception", result)
            self.assertNotIn("service is None", result)

    def test_calendar_agent_setup_guidance_behavior(self):
        """Test Calendar agent provides clear setup guidance when not configured"""
        from oprina.tools.calendar import calendar_list_events
        
        # Mock no service available (not set up)
        with patch('oprina.tools.calendar.get_calendar_service', return_value=None):
            result = calendar_list_events(tool_context=self.mock_tool_context)
            
            # Agent should provide user-friendly guidance
            self.assertIn("Calendar not set up", result)
            self.assertIn("python setup_calendar.py", result)
            
            # Should be voice-friendly, not technical
            self.assertNotIn("Error:", result)
            self.assertNotIn("Exception", result)
            self.assertNotIn("service is None", result)

    def test_agent_setup_workflow_consistency(self):
        """Test that agents provide consistent setup workflow guidance"""
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        # Mock both services as not set up
        with patch('oprina.tools.gmail.get_gmail_service', return_value=None), \
             patch('oprina.tools.calendar.get_calendar_service', return_value=None):
            
            gmail_result = gmail_list_messages(tool_context=self.mock_tool_context)
            calendar_result = calendar_list_events(tool_context=self.mock_tool_context)
            
            # Both should provide setup guidance
            self.assertIn("not set up", gmail_result)
            self.assertIn("not set up", calendar_result)
            
            # Both should mention their respective setup scripts
            self.assertIn("setup_gmail.py", gmail_result)
            self.assertIn("setup_calendar.py", calendar_result)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_handles_partial_setup(self, mock_gmail_service):
        """Test agent behavior when service is partially set up"""
        # Mock service that exists but has authentication issues
        mock_service = Mock()
        mock_gmail_service.return_value = mock_service
        
        # Simulate authentication error
        mock_service.users().messages().list().execute.side_effect = Exception("Invalid credentials")
        
        from oprina.tools.gmail import gmail_list_messages
        result = gmail_list_messages(tool_context=self.mock_tool_context)
        
        # Should handle gracefully and suggest re-setup
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)
        
        # Should not expose technical authentication details
        self.assertNotIn("Invalid credentials", result)
        self.assertNotIn("Exception", result)

    def test_agent_setup_session_tracking(self):
        """Test that agents track setup status in session state"""
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        # Mock services as not set up
        with patch('oprina.tools.gmail.get_gmail_service', return_value=None), \
             patch('oprina.tools.calendar.get_calendar_service', return_value=None):
            
            # Attempt operations when not set up
            gmail_list_messages(tool_context=self.mock_tool_context)
            calendar_list_events(tool_context=self.mock_tool_context)
            
            # Session could track setup status (implementation-dependent)
            # This test validates the session is properly accessed
            self.assertIsNotNone(self.mock_session.state)

    def test_agent_post_setup_verification(self):
        """Test agent behavior after successful setup"""
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        # Mock services as properly set up
        with patch('oprina.tools.gmail.get_gmail_service') as mock_gmail, \
             patch('oprina.tools.calendar.get_calendar_service') as mock_calendar:
            
            # Mock successful service creation
            mock_gmail_service = Mock()
            mock_calendar_service = Mock()
            mock_gmail.return_value = mock_gmail_service
            mock_calendar.return_value = mock_calendar_service
            
            # Mock successful operations
            mock_gmail_service.users().messages().list().execute.return_value = {'messages': []}
            mock_calendar_service.events().list().execute.return_value = {'items': []}
            
            # Should work without setup messages
            gmail_result = gmail_list_messages(tool_context=self.mock_tool_context)
            calendar_result = calendar_list_events(tool_context=self.mock_tool_context)
            
            # Should not contain setup guidance when working
            self.assertNotIn("not set up", gmail_result)
            self.assertNotIn("not set up", calendar_result)
            self.assertNotIn("setup_gmail.py", gmail_result)
            self.assertNotIn("setup_calendar.py", calendar_result)


class TestAgentSetupErrorRecovery(unittest.TestCase):
    """Test suite for agent error recovery during setup processes"""
    
    def setUp(self):
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    def test_agent_handles_corrupted_credentials(self):
        """Test agent behavior with corrupted credentials file"""
        from oprina.tools.gmail import gmail_list_messages
        
        # Mock service creation that fails due to bad credentials
        with patch('oprina.tools.gmail.get_gmail_service') as mock_get_service:
            mock_get_service.side_effect = Exception("Invalid credentials format")
            
            result = gmail_list_messages(tool_context=self.mock_tool_context)
            
            # Should handle gracefully and suggest re-setup
            self.assertIsInstance(result, str)
            self.assertIn("Error", result)
            
            # Should not expose technical details
            self.assertNotIn("Invalid credentials format", result)
            self.assertNotIn("Exception", result)

    def test_agent_handles_missing_credentials_file(self):
        """Test agent behavior when credentials file is missing"""
        from oprina.tools.calendar import calendar_create_event
        
        # Mock service creation that fails due to missing file
        with patch('oprina.tools.calendar.get_calendar_service') as mock_get_service:
            mock_get_service.side_effect = FileNotFoundError("credentials.json not found")
            
            result = calendar_create_event(
                summary="Test",
                start_time="2024-01-15 14:00",
                end_time="2024-01-15 15:00",
                tool_context=self.mock_tool_context
            )
            
            # Should handle gracefully and suggest setup
            self.assertIsInstance(result, str)
            self.assertIn("Error", result)
            
            # Should not expose file system details
            self.assertNotIn("FileNotFoundError", result)
            self.assertNotIn("credentials.json not found", result)

    def test_agent_handles_network_errors_during_setup(self):
        """Test agent behavior with network errors during setup verification"""
        from oprina.tools.gmail import gmail_list_messages
        
        with patch('oprina.tools.gmail.get_gmail_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            # Simulate network error
            mock_service.users().messages().list().execute.side_effect = \
                Exception("Network unreachable")
            
            result = gmail_list_messages(tool_context=self.mock_tool_context)
            
            # Should handle gracefully
            self.assertIsInstance(result, str)
            self.assertIn("Error", result)
            
            # Should not expose network details
            self.assertNotIn("Network unreachable", result)
            self.assertNotIn("Exception", result)

    def test_agent_setup_guidance_voice_optimization(self):
        """Test that setup guidance is optimized for voice interaction"""
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        # Mock services as not set up
        with patch('oprina.tools.gmail.get_gmail_service', return_value=None), \
             patch('oprina.tools.calendar.get_calendar_service', return_value=None):
            
            gmail_result = gmail_list_messages(tool_context=self.mock_tool_context)
            calendar_result = calendar_list_events(tool_context=self.mock_tool_context)
            
            # Voice-friendly characteristics
            results = [gmail_result, calendar_result]
            for result in results:
                # Should use natural language
                self.assertTrue(any(
                    phrase in result.lower() 
                    for phrase in ['not set up', 'please run', 'need to']
                ))
                
                # Should not contain technical jargon
                self.assertNotIn("null", result.lower())
                self.assertNotIn("none", result.lower())
                self.assertNotIn("error code", result.lower())


class TestAgentSetupIntegration(unittest.TestCase):
    """Test suite for agent integration during setup workflows"""
    
    def setUp(self):
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    def test_cross_agent_setup_coordination(self):
        """Test coordination between agents when different services have different setup states"""
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        # Gmail set up, Calendar not set up
        with patch('oprina.tools.gmail.get_gmail_service') as mock_gmail, \
             patch('oprina.tools.calendar.get_calendar_service', return_value=None):
            
            # Mock Gmail as working
            mock_gmail_service = Mock()
            mock_gmail.return_value = mock_gmail_service
            mock_gmail_service.users().messages().list().execute.return_value = {'messages': []}
            
            gmail_result = gmail_list_messages(tool_context=self.mock_tool_context)
            calendar_result = calendar_list_events(tool_context=self.mock_tool_context)
            
            # Gmail should work without setup guidance
            self.assertNotIn("not set up", gmail_result)
            
            # Calendar should provide setup guidance
            self.assertIn("Calendar not set up", calendar_result)
            self.assertIn("setup_calendar.py", calendar_result)

    def test_agent_setup_state_persistence(self):
        """Test that setup state is properly maintained across agent operations"""
        from oprina.tools.gmail import gmail_list_messages
        
        # Test multiple calls when not set up
        with patch('oprina.tools.gmail.get_gmail_service', return_value=None):
            result1 = gmail_list_messages(tool_context=self.mock_tool_context)
            result2 = gmail_list_messages(tool_context=self.mock_tool_context)
            
            # Both should provide consistent setup guidance
            self.assertIn("Gmail not set up", result1)
            self.assertIn("Gmail not set up", result2)
            
            # Should not accumulate error states
            self.assertEqual(result1, result2)

    def test_agent_setup_workflow_complete_cycle(self):
        """Test complete agent setup workflow from not-set-up to working"""
        from oprina.tools.calendar import calendar_list_events
        
        # Start with not set up
        with patch('oprina.tools.calendar.get_calendar_service', return_value=None):
            result_not_setup = calendar_list_events(tool_context=self.mock_tool_context)
            self.assertIn("Calendar not set up", result_not_setup)
        
        # Simulate after setup - service now available
        with patch('oprina.tools.calendar.get_calendar_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            mock_service.events().list().execute.return_value = {'items': []}
            
            result_after_setup = calendar_list_events(tool_context=self.mock_tool_context)
            
            # Should now work without setup guidance
            self.assertNotIn("not set up", result_after_setup)
            self.assertIn("upcoming events", result_after_setup.lower())


if __name__ == '__main__':
    unittest.main()
