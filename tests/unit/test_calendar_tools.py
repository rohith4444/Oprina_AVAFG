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
for _ in range(0):  # Go up 4 levels from tests/unit/test_calendar_tools.py
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the functions we're testing
from oprina.tools_prod.calendar import (
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
        self.assertIn("Found", result) 
        self.assertIn("Test Meeting", result)
        
        # Check session state updates
        self.assertIn(CALENDAR_LAST_FETCH, self.mock_session.state)
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_LIST_START_DATE], "2024-01-15")
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_LIST_DAYS], 7)
        self.assertEqual(self.mock_session.state[CALENDAR_LAST_LIST_COUNT], 3)


    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_list_events_no_events(self, mock_get_service):
        """Test event listing when no events found"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock empty events list
        mock_service.events().list().execute.return_value = {'items': []}
        
        result = calendar_list_events(tool_context=self.mock_tool_context)
        
        self.assertIn("No upcoming events found", result)
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
        self.assertIn("updated successfully", result)
        
        # Check session state
        self.assertIn(CALENDAR_LAST_UPDATED_EVENT, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_EVENT_UPDATED_AT, self.mock_session.state)


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
        self.assertIn("has been deleted successfully", result)
        
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


    def test_format_event_time_datetime(self):
        """Test formatting event time with dateTime"""
        event_time = {
            'dateTime': '2024-01-15T14:00:00-05:00',
            'timeZone': 'America/New_York'
        }
        
        result = _format_event_time(event_time)
        self.assertIsInstance(result, str)
        self.assertIn("Monday", result)

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
        self.assertIn("found", result.lower())
        # Should use natural language for times
        self.assertNotIn("T", result)  # No ISO format
        self.assertNotIn("2024-01-15T", result)  # No technical timestamps
        
        # Should be readable/speakable
        result_lower = result.lower()
        self.assertTrue(
            any(word in result_lower for word in ['morning', 'afternoon', 'am', 'pm'])
        )

    # =============================================================================
    # Agent State Management Tests
    # =============================================================================


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

if __name__ == '__main__':
    unittest.main()
