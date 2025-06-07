"""
Unit tests for Calendar tools - Testing individual Google Calendar API functions
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(4):  # Go up 4 levels from tests/unit/test_calendar_tools.py
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the functions we're testing
from oprina.tools.calendar import (
    calendar_create_event, calendar_list_events, calendar_update_event,
    calendar_delete_event, _parse_datetime, _format_event_time
)

# Import session key constants
from oprina.common.session_keys import (
    CALENDAR_CURRENT, CALENDAR_LAST_FETCH, CALENDAR_LAST_LIST_START_DATE,
    CALENDAR_LAST_LIST_DAYS, CALENDAR_LAST_LIST_COUNT,
    CALENDAR_LAST_EVENT_CREATED, CALENDAR_LAST_EVENT_CREATED_AT, 
    CALENDAR_LAST_CREATED_EVENT_ID, CALENDAR_LAST_UPDATED_EVENT,
    CALENDAR_LAST_EVENT_UPDATED_AT, CALENDAR_LAST_DELETED_EVENT,
    CALENDAR_LAST_DELETED_ID, CALENDAR_LAST_DELETED_AT
)


class TestCalendarTools(unittest.TestCase):
    """Test suite for Google Calendar API tools"""
    
    def setUp(self):
        """Set up test fixtures with mock tool context and session"""
        # Create mock session
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_session.id = "test_session_123"
        
        # Create mock tool context
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session
        self.mock_tool_context.invocation_id = "test_invocation_123"
        
        # Sample test data
        self.sample_event = {
            'id': 'test_event_123',
            'summary': 'Test Meeting',
            'start': {
                'dateTime': '2024-01-15T14:00:00-05:00',
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': '2024-01-15T15:00:00-05:00',
                'timeZone': 'America/New_York'
            },
            'location': 'Conference Room A',
            'description': 'Test meeting description',
            'htmlLink': 'https://calendar.google.com/event?eid=test123'
        }
        
        self.sample_events_list = {
            'items': [
                self.sample_event,
                {
                    'id': 'event_2',
                    'summary': 'Team Standup',
                    'start': {'dateTime': '2024-01-16T09:00:00-05:00'},
                    'end': {'dateTime': '2024-01-16T09:30:00-05:00'}
                },
                {
                    'id': 'event_3',
                    'summary': 'Client Call',
                    'start': {'dateTime': '2024-01-16T11:00:00-05:00'},
                    'end': {'dateTime': '2024-01-16T12:00:00-05:00'}
                }
            ]
        }

    # =============================================================================
    # Event Creation Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_create_event_success(self, mock_get_service):
        """Test successful event creation"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock calendar settings for timezone
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        
        # Mock successful event creation
        mock_service.events().insert().execute.return_value = self.sample_event
        
        result = calendar_create_event(
            summary="Test Meeting",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            description="Test description",
            location="Conference Room A",
            tool_context=self.mock_tool_context
        )
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn("Event 'Test Meeting' created successfully", result)
        
        # Check session state updates
        self.assertIn(CALENDAR_LAST_EVENT_CREATED, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_EVENT_CREATED_AT, self.mock_session.state)
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_CREATED_EVENT_ID], 'test_event_123')
        
        # Check event details in session
        event_data = self.mock_session.state[CALENDAR_LAST_EVENT_CREATED]
        self.assertEqual(event_data['summary'], 'Test Meeting')
        self.assertEqual(event_data['location'], 'Conference Room A')

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_create_event_no_service(self, mock_get_service):
        """Test event creation when Calendar not set up"""
        mock_get_service.return_value = None
        
        result = calendar_create_event(
            summary="Test Meeting",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            tool_context=self.mock_tool_context
        )
        
        self.assertIn("Calendar not set up", result)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_create_event_invalid_time(self, mock_get_service):
        """Test event creation with invalid time format"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        result = calendar_create_event(
            summary="Test Meeting",
            start_time="invalid-time",
            end_time="also-invalid",
            tool_context=self.mock_tool_context
        )
        
        self.assertIn("Invalid date/time format", result)

    # =============================================================================
    # Event Listing Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_list_events_success(self, mock_get_service):
        """Test successful event listing"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock successful event listing
        mock_service.events().list().execute.return_value = self.sample_events_list
        
        result = calendar_list_events(
            start_date="2024-01-15",
            days=7,
            tool_context=self.mock_tool_context
        )
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn("Upcoming events", result)
        self.assertIn("Test Meeting", result)
        
        # Check session state updates
        self.assertIn(CALENDAR_LAST_FETCH, self.mock_session.state)
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_LIST_START_DATE], "2024-01-15")
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_LIST_DAYS], 7)
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_LIST_COUNT], 3)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_list_events_default_params(self, mock_get_service):
        """Test event listing with default parameters (today, 7 days)"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.events().list().execute.return_value = self.sample_events_list
        
        result = calendar_list_events(tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        # Should use default 7 days
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_LIST_DAYS], 7)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_list_events_no_events(self, mock_get_service):
        """Test event listing when no events found"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock empty events list
        mock_service.events().list().execute.return_value = {'items': []}
        
        result = calendar_list_events(tool_context=self.mock_tool_context)
        
        self.assertIn("No events found", result)
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_LIST_COUNT], 0)

    # =============================================================================
    # Event Update Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_update_event_success(self, mock_get_service):
        """Test successful event update"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock getting existing event
        mock_service.events().get().execute.return_value = self.sample_event
        
        # Mock successful update
        updated_event = self.sample_event.copy()
        updated_event['summary'] = 'Updated Meeting'
        mock_service.events().update().execute.return_value = updated_event
        
        result = calendar_update_event(
            event_id="test_event_123",
            summary="Updated Meeting",
            tool_context=self.mock_tool_context
        )
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn("Event updated successfully", result)
        
        # Check session state
        self.assertIn(CALENDAR_LAST_UPDATED_EVENT, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_EVENT_UPDATED_AT, self.mock_session.state)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_update_event_with_time(self, mock_get_service):
        """Test event update with new time"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock calendar settings
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        
        # Mock getting and updating event
        mock_service.events().get().execute.return_value = self.sample_event
        mock_service.events().update().execute.return_value = self.sample_event
        
        result = calendar_update_event(
            event_id="test_event_123",
            start_time="2024-01-15 15:00",
            end_time="2024-01-15 16:00",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Event updated successfully", result)

    # =============================================================================
    # Event Deletion Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_delete_event_success(self, mock_get_service):
        """Test successful event deletion"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock getting event for deletion
        mock_service.events().get().execute.return_value = self.sample_event
        
        result = calendar_delete_event(
            event_id="test_event_123",
            confirm=True,
            tool_context=self.mock_tool_context
        )
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn("Event 'Test Meeting' deleted successfully", result)
        
        # Check session state
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_DELETED_ID], "test_event_123")
        self.assertIn(CALENDAR_LAST_DELETED_AT, self.mock_session.state)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_delete_event_no_confirm(self, mock_get_service):
        """Test event deletion without confirmation"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.events().get().execute.return_value = self.sample_event
        
        result = calendar_delete_event(
            event_id="test_event_123",
            confirm=False,
            tool_context=self.mock_tool_context
        )
        
        self.assertIn("Please confirm", result)

    # =============================================================================
    # Helper Function Tests
    # =============================================================================
    
    def test_parse_datetime_valid_formats(self):
        """Test parsing various valid datetime formats"""
        # Test ISO format
        result1 = _parse_datetime("2024-01-15T14:00:00")
        self.assertIsInstance(result1, datetime)
        self.assertEqual(result1.year, 2024)
        self.assertEqual(result1.hour, 14)
        
        # Test simple format
        result2 = _parse_datetime("2024-01-15 14:00")
        self.assertIsInstance(result2, datetime)
        
        # Test date only
        result3 = _parse_datetime("2024-01-15")
        self.assertIsInstance(result3, datetime)

    def test_parse_datetime_invalid_formats(self):
        """Test parsing invalid datetime formats"""
        # Test invalid format
        result1 = _parse_datetime("invalid-date")
        self.assertIsNone(result1)
        
        # Test empty string
        result2 = _parse_datetime("")
        self.assertIsNone(result2)
        
        # Test None
        result3 = _parse_datetime(None)
        self.assertIsNone(result3)

    def test_format_event_time_datetime(self):
        """Test formatting event time with dateTime"""
        event_time = {
            'dateTime': '2024-01-15T14:00:00-05:00',
            'timeZone': 'America/New_York'
        }
        
        result = _format_event_time(event_time)
        self.assertIsInstance(result, str)
        self.assertIn("2024", result)

    def test_format_event_time_date_only(self):
        """Test formatting all-day event time"""
        event_time = {
            'date': '2024-01-15'
        }
        
        result = _format_event_time(event_time)
        self.assertIsInstance(result, str)
        self.assertIn("All day", result)

    # =============================================================================
    # Error Handling Tests
    # =============================================================================
    
    def test_functions_without_tool_context(self):
        """Test that functions handle missing tool context gracefully"""
        # These should return error messages, not crash
        result1 = calendar_list_events(tool_context=None)
        result2 = calendar_create_event(
            summary="Test", 
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            tool_context=None
        )
        
        self.assertIsInstance(result1, str)
        self.assertIsInstance(result2, str)
        self.assertIn("Error", result1)
        self.assertIn("Error", result2)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_api_error_handling(self, mock_get_service):
        """Test handling of Calendar API errors"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Simulate API error
        mock_service.events().list().execute.side_effect = Exception("API Error")
        
        result = calendar_list_events(tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_event_not_found_error(self, mock_get_service):
        """Test handling when event is not found"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Simulate event not found
        mock_service.events().get().execute.side_effect = Exception("Event not found")
        
        result = calendar_update_event(
            event_id="nonexistent_event",
            summary="Updated",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    # =============================================================================
    # Session State Validation Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_session_state_consistency(self, mock_get_service):
        """Test that session state is consistently updated across operations"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Test event creation updates session
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        mock_service.events().insert().execute.return_value = self.sample_event
        
        calendar_create_event(
            summary="Test Meeting",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            tool_context=self.mock_tool_context
        )
        
        # Verify all expected session keys are present
        expected_keys = [
            CALENDAR_LAST_EVENT_CREATED,
            CALENDAR_LAST_EVENT_CREATED_AT,
            CALENDAR_LAST_CREATED_EVENT_ID
        ]
        
        for key in expected_keys:
            self.assertIn(key, self.mock_session.state)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_timezone_handling(self, mock_get_service):
        """Test proper timezone handling in events"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Test default timezone when settings fail
        mock_service.settings().list().execute.side_effect = Exception("Settings error")
        mock_service.events().insert().execute.return_value = self.sample_event
        
        result = calendar_create_event(
            summary="Test Meeting",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            tool_context=self.mock_tool_context
        )
        
        # Should still succeed with default timezone
        self.assertIn("created successfully", result)


# =============================================================================
# CALENDAR AGENT BEHAVIOR TESTS (NEW)
# =============================================================================

class TestCalendarAgentBehavior(unittest.TestCase):
    """Test suite for Calendar Agent behavior and integration"""
    
    def setUp(self):
        """Set up test fixtures for agent behavior testing"""
        # Create mock session
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_session.id = "test_session_123"
        
        # Create mock tool context
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session
        self.mock_tool_context.invocation_id = "test_invocation_123"
        
        # Sample event for agent testing
        self.sample_event = {
            'id': 'agent_test_event',
            'summary': 'Team Meeting - Project Discussion',
            'start': {'dateTime': '2024-01-15T14:00:00-05:00'},
            'end': {'dateTime': '2024-01-15T15:00:00-05:00'},
            'location': 'Conference Room A',
            'description': 'Weekly team sync for project updates'
        }

    # =============================================================================
    # Agent Configuration Tests
    # =============================================================================
    
    def test_calendar_agent_configuration(self):
        """Test that Calendar agent is properly configured"""
        from oprina.sub_agents.calendar.agent import calendar_agent
        
        # Test agent properties
        self.assertEqual(calendar_agent.name, "calendar_agent")
        self.assertEqual(calendar_agent.model, "gemini-2.0-flash")
        self.assertIn("Google Calendar operations", calendar_agent.description)
        
        # Test that agent has all expected tools
        tool_names = [tool.name for tool in calendar_agent.tools]
        expected_tools = [
            "calendar_create_event",
            "calendar_list_events", 
            "calendar_update_event",
            "calendar_delete_event"
        ]
        
        for tool_name in expected_tools:
            self.assertIn(tool_name, tool_names)

    def test_calendar_agent_instruction_content(self):
        """Test that Calendar agent instructions contain key behavior elements"""
        from oprina.sub_agents.calendar.agent import calendar_agent
        
        instruction = calendar_agent.instruction
        self.assertIsNotNone(instruction)
        
        # Check for key instruction components
        key_elements = [
            "Calendar Agent", "Event Creation", "Event Listing", 
            "Event Management", "Setup Management", "voice-friendly"
        ]
        
        for element in key_elements:
            self.assertIn(element, instruction)

    # =============================================================================
    # Agent Workflow Behavior Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_event_creation_workflow(self, mock_get_service):
        """Test agent's event creation workflow behavior"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock calendar settings and successful creation
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        mock_service.events().insert().execute.return_value = self.sample_event
        
        # Test agent workflow: create -> confirm -> track
        result = calendar_create_event(
            summary="Team Meeting",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            description="Weekly team sync",
            tool_context=self.mock_tool_context
        )
        
        # Agent should provide user-friendly confirmation
        self.assertIsInstance(result, str)
        self.assertIn("created successfully", result)
        self.assertIn("Team Meeting", result)
        
        # Should maintain workflow state
        self.assertIn(CALENDAR_LAST_EVENT_CREATED, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_CREATED_EVENT_ID, self.mock_session.state)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_natural_language_processing(self, mock_get_service):
        """Test agent's ability to handle natural language time formats"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock calendar settings
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        mock_service.events().insert().execute.return_value = self.sample_event
        
        # Test various time formats the agent should handle
        test_cases = [
            ("2024-01-15 14:00", "2024-01-15 15:00"),
            ("January 15, 2024 2:00 PM", "January 15, 2024 3:00 PM"),
        ]
        
        for start_time, end_time in test_cases:
            result = calendar_create_event(
                summary="Meeting with client",
                start_time=start_time,
                end_time=end_time,
                tool_context=self.mock_tool_context
            )
            
            # Should handle the format gracefully
            self.assertIsInstance(result, str)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_event_listing_workflow(self, mock_get_service):
        """Test agent's event listing workflow with voice-friendly output"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock events data
        events_data = {
            'items': [
                self.sample_event,
                {
                    'id': 'event_2',
                    'summary': 'Client Presentation',
                    'start': {'dateTime': '2024-01-15T16:00:00-05:00'},
                    'end': {'dateTime': '2024-01-15T17:30:00-05:00'},
                    'location': 'Client Office'
                }
            ]
        }
        mock_service.events().list().execute.return_value = events_data
        
        result = calendar_list_events(
            start_date="2024-01-15",
            days=1,
            tool_context=self.mock_tool_context
        )
        
        # Agent should provide voice-friendly results
        self.assertIn("upcoming events", result.lower())
        self.assertIn("Team Meeting", result)
        self.assertIn("Client Presentation", result)
        
        # Should include readable time format, not raw ISO
        self.assertNotIn("2024-01-15T14:00:00-05:00", result)
        
        # Should track listing in session
        self.assertIn(CALENDAR_LAST_FETCH, self.mock_session.state)

    # =============================================================================
    # Agent Error Recovery and Guidance Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_handles_setup_not_configured(self, mock_get_service):
        """Test agent behavior when calendar is not set up"""
        mock_get_service.return_value = None
        
        result = calendar_list_events(tool_context=self.mock_tool_context)
        
        # Agent should provide clear setup guidance
        self.assertIn("Calendar not set up", result)
        self.assertIn("python setup_calendar.py", result)
        
        # Should be voice-friendly guidance
        self.assertNotIn("Error:", result)  # No technical error messages

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_error_recovery_behavior(self, mock_get_service):
        """Test agent's error recovery and user guidance"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Simulate API error
        mock_service.events().list().execute.side_effect = Exception("API Error")
        
        result = calendar_list_events(tool_context=self.mock_tool_context)
        
        # Agent should provide user-friendly error handling
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)
        # Should not expose technical details
        self.assertNotIn("Exception", result)
        self.assertNotIn("Traceback", result)

    def test_agent_handles_invalid_input_gracefully(self):
        """Test agent handles invalid inputs without crashing"""
        # Test with invalid date formats
        result = calendar_create_event(
            summary="Test Meeting",
            start_time="invalid-date",
            end_time="also-invalid",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Invalid", result)

    # =============================================================================
    # Agent Voice Interface Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_voice_friendly_responses(self, mock_get_service):
        """Test that agent responses are optimized for voice interaction"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock events for voice-friendly testing
        events_data = {
            'items': [
                {
                    'id': 'event_1',
                    'summary': 'Morning Standup',
                    'start': {'dateTime': '2024-01-15T09:00:00-05:00'},
                    'end': {'dateTime': '2024-01-15T09:30:00-05:00'}
                },
                {
                    'id': 'event_2', 
                    'summary': 'Client Presentation',
                    'start': {'dateTime': '2024-01-15T14:00:00-05:00'},
                    'end': {'dateTime': '2024-01-15T15:30:00-05:00'}
                }
            ]
        }
        mock_service.events().list().execute.return_value = events_data
        
        result = calendar_list_events(
            start_date="2024-01-15",
            days=1,
            tool_context=self.mock_tool_context
        )
        
        # Voice-friendly characteristics
        self.assertIn("upcoming events", result.lower())
        # Should use natural language for times
        self.assertNotIn("T", result)  # No ISO format
        self.assertNotIn("2024-01-15T", result)  # No technical timestamps
        
        # Should be readable/speakable
        result_lower = result.lower()
        self.assertTrue(
            any(word in result_lower for word in ['morning', 'afternoon', 'am', 'pm'])
        )

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_contextual_responses(self, mock_get_service):
        """Test that agent provides contextual, voice-friendly responses"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock events data
        events_data = {
            'items': [
                {
                    'id': 'event_1',
                    'summary': 'Team Meeting',
                    'start': {'dateTime': '2024-01-15T09:00:00-05:00'},
                    'end': {'dateTime': '2024-01-15T10:00:00-05:00'},
                    'location': 'Conference Room A'
                }
            ]
        }
        mock_service.events().list().execute.return_value = events_data
        
        result = calendar_list_events(
            start_date="2024-01-15",
            days=1,
            tool_context=self.mock_tool_context
        )
        
        # Check for voice-friendly formatting
        self.assertIn("upcoming events", result.lower())
        self.assertIn("Team Meeting", result)
        # Should include readable time format, not raw ISO
        self.assertNotIn("2024-01-15T09:00:00-05:00", result)

    # =============================================================================
    # Agent Integration Workflow Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_workflow_create_then_list(self, mock_get_service):
        """Test agent workflow: create event then list events"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock calendar settings
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        
        # Step 1: Create event
        created_event = {
            'id': 'new_event_123',
            'summary': 'New Meeting',
            'start': {'dateTime': '2024-01-15T14:00:00-05:00'},
            'end': {'dateTime': '2024-01-15T15:00:00-05:00'}
        }
        mock_service.events().insert().execute.return_value = created_event
        
        create_result = calendar_create_event(
            summary="New Meeting",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            tool_context=self.mock_tool_context
        )
        
        # Step 2: List events should include the new event
        events_list = {
            'items': [created_event]
        }
        mock_service.events().list().execute.return_value = events_list
        
        list_result = calendar_list_events(
            start_date="2024-01-15",
            days=1,
            tool_context=self.mock_tool_context
        )
        
        # Verify workflow
        self.assertIn("created successfully", create_result)
        self.assertIn("New Meeting", list_result)
        
        # Check session continuity
        self.assertEqual(
            self.mock_session.state.get(CALENDAR_LAST_CREATED_EVENT_ID),
            'new_event_123'
        )

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_workflow_update_with_confirmation(self, mock_get_service):
        """Test agent workflow: update event with proper confirmation"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock existing event
        existing_event = {
            'id': 'event_123',
            'summary': 'Original Meeting',
            'start': {'dateTime': '2024-01-15T14:00:00-05:00'},
            'end': {'dateTime': '2024-01-15T15:00:00-05:00'}
        }
        
        updated_event = existing_event.copy()
        updated_event['summary'] = 'Updated Meeting'
        
        mock_service.events().get().execute.return_value = existing_event
        mock_service.events().update().execute.return_value = updated_event
        
        result = calendar_update_event(
            event_id="event_123",
            summary="Updated Meeting",
            tool_context=self.mock_tool_context
        )
        
        # Should provide clear confirmation
        self.assertIn("updated successfully", result)
        self.assertIn("Updated Meeting", result)

    # =============================================================================
    # Agent State Management Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_session_state_persistence(self, mock_get_service):
        """Test that agent properly maintains session state across operations"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock successful operations
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        
        created_event = {
            'id': 'event_123',
            'summary': 'Test Meeting'
        }
        mock_service.events().insert().execute.return_value = created_event
        
        # Perform operation
        calendar_create_event(
            summary="Test Meeting",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            tool_context=self.mock_tool_context
        )
        
        # Check that session state is properly maintained
        self.assertIn(CALENDAR_LAST_EVENT_CREATED, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_CREATED_EVENT_ID, self.mock_session.state)
        
        # State should be available for subsequent operations
        self.assertEqual(
            self.mock_session.state[CALENDAR_LAST_CREATED_EVENT_ID],
            'event_123'
        )

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_workflow_context_preservation(self, mock_get_service):
        """Test agent preserves workflow context across multiple steps"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Step 1: List events
        events_data = {'items': [self.sample_event]}
        mock_service.events().list().execute.return_value = events_data
        
        calendar_list_events(
            start_date="2024-01-15",
            days=1,
            tool_context=self.mock_tool_context
        )
        
        # Step 2: Update event
        updated_event = self.sample_event.copy()
        updated_event['summary'] = 'Updated Meeting'
        
        mock_service.events().get().execute.return_value = self.sample_event
        mock_service.events().update().execute.return_value = updated_event
        
        calendar_update_event(
            event_id="agent_test_event",
            summary="Updated Meeting",
            tool_context=self.mock_tool_context
        )
        
        # Verify workflow continuity in session state
        self.assertIn(CALENDAR_LAST_FETCH, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_UPDATED_EVENT_ID, self.mock_session.state)


class TestCalendarToolIntegration(unittest.TestCase):
    """Test integration between Calendar agent and individual tools"""
    
    def setUp(self):
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    def test_tool_registration_with_agent(self):
        """Test that all tools are properly registered with the agent"""
        tool_functions = [
            calendar_create_event,
            calendar_list_events,
            calendar_update_event,
            calendar_delete_event
        ]
        
        from oprina.sub_agents.calendar.agent import calendar_agent
        agent_tool_names = [tool.name for tool in calendar_agent.tools]
        
        for tool_func in tool_functions:
            self.assertIn(tool_func.__name__, agent_tool_names)

    def test_tool_error_propagation(self):
        """Test that tool errors are properly handled by the agent"""
        # Test with None tool context (simulates agent error)
        result = calendar_list_events(tool_context=None)
        
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_tool_session_sharing(self, mock_get_service):
        """Test that tools properly share session state"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock successful event creation
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        
        created_event = {'id': 'test_123', 'summary': 'Test'}
        mock_service.events().insert().execute.return_value = created_event
        
        # Create event
        calendar_create_event(
            summary="Test",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00", 
            tool_context=self.mock_tool_context
        )
        
        # Verify session state is shared
        self.assertIn(CALENDAR_LAST_CREATED_EVENT_ID, self.mock_session.state)
        
        # List events should access same session
        mock_service.events().list().execute.return_value = {'items': [created_event]}
        
        calendar_list_events(tool_context=self.mock_tool_context)
        
        # Both operations should have updated the same session
        self.assertIn(CALENDAR_LAST_FETCH, self.mock_session.state)


if __name__ == '__main__':
    unittest.main()
