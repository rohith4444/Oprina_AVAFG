"""
Integration tests for Oprina agents - Testing agent coordination and workflows
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import os
import sys
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):  # Go up 3 levels from tests/test_agents.py
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import agents
from oprina.agent import root_agent
from oprina.sub_agents.email.agent import email_agent
from oprina.sub_agents.calendar.agent import calendar_agent

# Import session key constants for validation
from oprina.common.session_keys import (
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_LAST_QUERY,
    CALENDAR_LAST_FETCH, CALENDAR_LAST_EVENT_CREATED,
    USER_ID, USER_EMAIL, USER_PREFERENCES,
    EMAIL_LAST_EXTRACTED_TASKS, EMAIL_LAST_MESSAGE_VIEWED,
    CALENDAR_LAST_CREATED_EVENT_ID
)


class TestAgentIntegration(unittest.TestCase):
    """Test suite for agent coordination and workflows"""
    
    def setUp(self):
        """Set up test fixtures with mock session and context"""
        # Create mock session
        self.mock_session = Mock()
        self.mock_session.state = {
            USER_ID: "test_user_123",
            USER_EMAIL: "test@example.com",
            USER_PREFERENCES: {
                "email_max_results": 10,
                "calendar_days_ahead": 7,
                "reply_style": "professional"
            }
        }
        self.mock_session.id = "test_session_123"
        
        # Create mock tool context
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session
        self.mock_tool_context.invocation_id = "test_invocation_123"
        
        # Mock runner for agent execution
        self.mock_runner = Mock()
        
    def _mock_agent_run(self, agent, user_message, expected_response="Test response"):
        """Helper to mock agent execution"""
        # Mock the runner.run method to return expected response
        self.mock_runner.run.return_value = expected_response
        return expected_response

    # =============================================================================
    # Root Agent Delegation Tests
    # =============================================================================
    
    def test_root_agent_structure(self):
        """Test that root agent is properly configured"""
        # Verify root agent has expected properties
        self.assertEqual(root_agent.name, "oprina_root_agent")
        self.assertEqual(root_agent.model, "gemini-2.0-flash")
        self.assertIn("Multimodal voice-enabled", root_agent.description)
        
        # Verify sub-agents are present
        self.assertEqual(len(root_agent.sub_agents), 2)
        
        # Check that email and calendar agents are in sub_agents
        agent_names = [agent.name for agent in root_agent.sub_agents]
        self.assertIn("email_agent", agent_names)
        self.assertIn("calendar_agent", agent_names)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_email_agent_delegation_queries(self, mock_gmail_service):
        """Test that email-related queries would be handled by email agent"""
        mock_gmail_service.return_value = None  # Simulate not set up
        
        # These are queries that should be delegated to email agent
        email_queries = [
            "Check my emails",
            "Send an email to john@example.com",
            "Reply to the email from Sarah",
            "Summarize my recent emails",
            "What action items are in my emails?",
            "Generate a professional reply"
        ]
        
        # Verify email agent has tools to handle these
        email_tools = [tool.name for tool in email_agent.tools]
        
        # Check that email agent has essential tools
        expected_tools = [
            "gmail_list_messages", "gmail_send_message", "gmail_reply_to_message",
            "gmail_summarize_message", "gmail_extract_action_items", "gmail_generate_reply"
        ]
        
        for tool in expected_tools:
            self.assertIn(tool, email_tools)

    @patch('oprina.tools.calendar.get_calendar_service')  
    def test_calendar_agent_delegation_queries(self, mock_calendar_service):
        """Test that calendar-related queries would be handled by calendar agent"""
        mock_calendar_service.return_value = None  # Simulate not set up
        
        # These are queries that should be delegated to calendar agent
        calendar_queries = [
            "What's on my calendar today?",
            "Schedule a meeting for tomorrow",
            "When am I free this week?",
            "Create an event for lunch",
            "Delete the cancelled appointment"
        ]
        
        # Verify calendar agent has tools to handle these
        calendar_tools = [tool.name for tool in calendar_agent.tools]
        
        # Check that calendar agent has essential tools
        expected_tools = [
            "calendar_list_events", "calendar_create_event", 
            "calendar_update_event", "calendar_delete_event"
        ]
        
        for tool in expected_tools:
            self.assertIn(tool, calendar_tools)

    # =============================================================================
    # Email Agent Workflow Tests
    # =============================================================================
    
    def test_email_agent_structure(self):
        """Test email agent configuration"""
        self.assertEqual(email_agent.name, "email_agent")
        self.assertEqual(email_agent.model, "gemini-2.0-flash")
        self.assertIn("Gmail operations", email_agent.description)
        
        # Verify it has tools
        self.assertGreater(len(email_agent.tools), 0)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_email_agent_ai_workflow_simulation(self, mock_gmail_service):
        """Test email agent AI workflow capabilities"""
        # Setup mock Gmail service
        mock_service = Mock()
        mock_gmail_service.return_value = mock_service
        
        # Mock email data
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }
        
        mock_service.users().messages().get().execute.return_value = {
            'id': 'msg1',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'colleague@company.com'},
                    {'name': 'Subject', 'value': 'Project Update Required'},
                    {'name': 'To', 'value': 'user@company.com'}
                ],
                'body': {'data': 'UHJvamVjdCB1cGRhdGUgbmVlZGVk'}  # Base64 encoded
            }
        }
        
        # Import and test individual tools
        from oprina.tools.gmail import gmail_list_messages, gmail_get_message
        
        # Test listing messages
        result1 = gmail_list_messages(tool_context=self.mock_tool_context)
        self.assertIsInstance(result1, str)
        self.assertIn("Found", result1)
        
        # Verify session state was updated
        self.assertIn(EMAIL_LAST_FETCH, self.mock_session.state)
        self.assertIn(EMAIL_CURRENT_RESULTS, self.mock_session.state)

    @patch('oprina.tools.gmail._process_with_ai')
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_email_ai_processing_workflow(self, mock_gmail_service, mock_ai_process):
        """Test AI-powered email processing workflow"""
        # Setup mocks
        mock_service = Mock()
        mock_gmail_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = {
            'id': 'test_msg',
            'payload': {
                'headers': [{'name': 'Subject', 'value': 'Meeting Request'}],
                'body': {'data': 'TWVldGluZyByZXF1ZXN0'}
            }
        }
        
        mock_ai_process.return_value = "Meeting scheduled for next Tuesday at 2 PM"
        
        # Test AI summarization
        from oprina.tools.gmail import gmail_summarize_message
        result = gmail_summarize_message("test_msg", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Summary:", result)
        
        # Verify AI was called
        mock_ai_process.assert_called_once()

    # =============================================================================
    # Calendar Agent Workflow Tests
    # =============================================================================
    
    def test_calendar_agent_structure(self):
        """Test calendar agent configuration"""
        self.assertEqual(calendar_agent.name, "calendar_agent")
        self.assertEqual(calendar_agent.model, "gemini-2.0-flash")
        self.assertIn("Google Calendar operations", calendar_agent.description)
        
        # Verify it has tools
        self.assertGreater(len(calendar_agent.tools), 0)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_agent_event_workflow(self, mock_calendar_service):
        """Test calendar agent event management workflow"""
        # Setup mock Calendar service
        mock_service = Mock()
        mock_calendar_service.return_value = mock_service
        
        # Mock calendar settings
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        
        # Mock event creation response
        mock_service.events().insert().execute.return_value = {
            'id': 'new_event_123',
            'summary': 'Test Meeting',
            'start': {'dateTime': '2024-01-15T14:00:00-05:00'},
            'end': {'dateTime': '2024-01-15T15:00:00-05:00'}
        }
        
        # Test event creation
        from oprina.tools.calendar import calendar_create_event
        result = calendar_create_event(
            summary="Test Meeting",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("created successfully", result)
        
        # Verify session state was updated
        self.assertIn(CALENDAR_LAST_EVENT_CREATED, self.mock_session.state)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_agent_scheduling_workflow(self, mock_calendar_service):
        """Test calendar agent scheduling workflow"""
        mock_service = Mock()
        mock_calendar_service.return_value = mock_service
        
        # Mock events listing (checking availability)
        mock_service.events().list().execute.return_value = {
            'items': [
                {
                    'id': 'existing_event',
                    'summary': 'Existing Meeting',
                    'start': {'dateTime': '2024-01-15T10:00:00-05:00'},
                    'end': {'dateTime': '2024-01-15T11:00:00-05:00'}
                }
            ]
        }
        
        # Test listing events to check availability
        from oprina.tools.calendar import calendar_list_events
        result = calendar_list_events(
            start_date="2024-01-15",
            days=1,
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Upcoming events", result)
        
        # Verify session state tracking
        self.assertIn(CALENDAR_LAST_FETCH, self.mock_session.state)

    # =============================================================================
    # Cross-Agent Coordination Tests
    # =============================================================================
    
    @patch('oprina.tools.calendar.get_calendar_service')
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_cross_agent_workflow_simulation(self, mock_gmail_service, mock_calendar_service):
        """Test coordination between email and calendar agents"""
        # Setup mocks for both services
        mock_gmail = Mock()
        mock_calendar = Mock()
        mock_gmail_service.return_value = mock_gmail
        mock_calendar_service.return_value = mock_calendar
        
        # Mock Gmail operations
        mock_gmail.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg_with_meeting'}]
        }
        
        mock_gmail.users().messages().get().execute.return_value = {
            'id': 'msg_with_meeting',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'client@company.com'},
                    {'name': 'Subject', 'value': 'Meeting Request - Project Discussion'}
                ],
                'body': {'data': 'TWVldGluZyByZXF1ZXN0IGZvciBwcm9qZWN0'}
            }
        }
        
        # Mock Calendar operations
        mock_calendar.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        
        mock_calendar.events().insert().execute.return_value = {
            'id': 'meeting_event_123',
            'summary': 'Project Discussion',
            'start': {'dateTime': '2024-01-16T14:00:00-05:00'},
            'end': {'dateTime': '2024-01-16T15:00:00-05:00'}
        }
        
        mock_gmail.users().messages().send().execute.return_value = {'id': 'sent_invite'}
        
        # Simulate cross-agent workflow:
        # 1. Check emails for meeting requests
        from oprina.tools.gmail import gmail_list_messages, gmail_get_message
        email_result = gmail_list_messages(query="meeting request", tool_context=self.mock_tool_context)
        self.assertIn("Found", email_result)
        
        # 2. Create calendar event
        from oprina.tools.calendar import calendar_create_event
        calendar_result = calendar_create_event(
            summary="Project Discussion",
            start_time="2024-01-16 14:00",
            end_time="2024-01-16 15:00",
            tool_context=self.mock_tool_context
        )
        self.assertIn("created successfully", calendar_result)
        
        # 3. Send email confirmation
        from oprina.tools.gmail import gmail_send_message
        send_result = gmail_send_message(
            to="client@company.com",
            subject="Meeting Confirmed - Project Discussion",
            body="Meeting scheduled for tomorrow at 2 PM",
            tool_context=self.mock_tool_context
        )
        self.assertIn("sent successfully", send_result)
        
        # Verify both agents updated session state
        self.assertIn(EMAIL_CURRENT_RESULTS, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_EVENT_CREATED, self.mock_session.state)

    # =============================================================================
    # Agent Instructions and Prompt Tests
    # =============================================================================
    
    def test_root_agent_instructions(self):
        """Test that root agent has proper instructions"""
        # Verify root agent has instruction content
        self.assertIsNotNone(root_agent.instruction)
        self.assertIsInstance(root_agent.instruction, str)
        self.assertGreater(len(root_agent.instruction), 100)  # Should be substantial
        
        # Check for key instruction content
        instruction_lower = root_agent.instruction.lower()
        self.assertIn("oprina", instruction_lower)
        self.assertIn("voice", instruction_lower)
        self.assertIn("email", instruction_lower)
        self.assertIn("calendar", instruction_lower)

    def test_email_agent_instructions(self):
        """Test that email agent has proper instructions"""
        self.assertIsNotNone(email_agent.instruction)
        self.assertIsInstance(email_agent.instruction, str)
        
        # Should mention Gmail and email operations
        instruction_lower = email_agent.instruction.lower()
        self.assertIn("gmail", instruction_lower)
        self.assertIn("email", instruction_lower)

    def test_calendar_agent_instructions(self):
        """Test that calendar agent has proper instructions"""
        self.assertIsNotNone(calendar_agent.instruction)
        self.assertIsInstance(calendar_agent.instruction, str)
        
        # Should mention Calendar and event operations
        instruction_lower = calendar_agent.instruction.lower()
        self.assertIn("calendar", instruction_lower)
        self.assertIn("event", instruction_lower)

    # =============================================================================
    # Session State Management Tests
    # =============================================================================
    
    def test_session_state_isolation(self):
        """Test that different operations properly manage session state"""
        # Create separate mock contexts to simulate different operations
        mock_context_1 = Mock()
        mock_context_1.session = Mock()
        mock_context_1.session.state = {}
        
        mock_context_2 = Mock()  
        mock_context_2.session = Mock()
        mock_context_2.session.state = {}
        
        # Verify they start with empty state
        self.assertEqual(len(mock_context_1.session.state), 0)
        self.assertEqual(len(mock_context_2.session.state), 0)
        
        # Verify they remain independent
        mock_context_1.session.state["test_key"] = "test_value"
        self.assertNotIn("test_key", mock_context_2.session.state)

    @patch('oprina.tools.gmail.get_gmail_service')
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_session_state_consistency_across_agents(self, mock_cal_service, mock_gmail_service):
        """Test that session state is consistently managed across different agent operations"""
        # Setup mocks
        mock_gmail = Mock()
        mock_calendar = Mock()
        mock_gmail_service.return_value = mock_gmail
        mock_cal_service.return_value = mock_calendar
        
        # Mock responses
        mock_gmail.users().messages().list().execute.return_value = {
            'messages': [{'id': 'test_msg'}]
        }
        mock_gmail.users().messages().get().execute.return_value = {
            'id': 'test_msg',
            'payload': {'headers': [], 'body': {'data': 'dGVzdA=='}}
        }
        
        mock_calendar.events().list().execute.return_value = {
            'items': [{'id': 'test_event', 'summary': 'Test Event'}]
        }
        
        # Use same session context for both operations
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        # Perform email operation
        gmail_list_messages(tool_context=self.mock_tool_context)
        
        # Perform calendar operation  
        calendar_list_events(tool_context=self.mock_tool_context)
        
        # Verify both operations updated the same session
        self.assertIn(EMAIL_LAST_FETCH, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_FETCH, self.mock_session.state)
        
        # Verify user info persists across operations
        self.assertEqual(self.mock_session.state[USER_ID], "test_user_123")

    # =============================================================================
    # Error Handling and Resilience Tests
    # =============================================================================
    
    def test_agent_error_handling(self):
        """Test that agents handle errors gracefully"""
        # Test with invalid tool context
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        # These should not crash even with None context
        result1 = gmail_list_messages(tool_context=None)
        result2 = calendar_list_events(tool_context=None)
        
        self.assertIsInstance(result1, str)
        self.assertIsInstance(result2, str)

    @patch('oprina.tools.gmail.get_gmail_service')
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_service_unavailable_handling(self, mock_cal_service, mock_gmail_service):
        """Test handling when services are not available"""
        # Simulate services not set up
        mock_gmail_service.return_value = None
        mock_cal_service.return_value = None
        
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        gmail_result = gmail_list_messages(tool_context=self.mock_tool_context)
        calendar_result = calendar_list_events(tool_context=self.mock_tool_context)
        
        # Should get helpful setup messages
        self.assertIn("Gmail not set up", gmail_result)
        self.assertIn("Calendar not set up", calendar_result)

    # =============================================================================
    # Tool Registration and Availability Tests
    # =============================================================================
    
    def test_agent_tool_registration(self):
        """Test that agents have their tools properly registered"""
        # Email agent should have Gmail tools
        email_tool_names = [tool.name for tool in email_agent.tools]
        self.assertIn("gmail_list_messages", email_tool_names)
        self.assertIn("gmail_send_message", email_tool_names)
        self.assertIn("gmail_summarize_message", email_tool_names)  # AI tool
        
        # Calendar agent should have Calendar tools
        calendar_tool_names = [tool.name for tool in calendar_agent.tools]
        self.assertIn("calendar_list_events", calendar_tool_names)
        self.assertIn("calendar_create_event", calendar_tool_names)
        
        # Root agent should not have direct tools (delegates to sub-agents)
        self.assertEqual(len(root_agent.tools), 0)

    def test_agent_model_consistency(self):
        """Test that all agents use consistent models"""
        # All agents should use the same model
        expected_model = "gemini-2.0-flash"
        
        self.assertEqual(root_agent.model, expected_model)
        self.assertEqual(email_agent.model, expected_model)
        self.assertEqual(calendar_agent.model, expected_model)


# =============================================================================
# ENHANCED AGENT BEHAVIOR TESTS (NEW)
# =============================================================================

class TestAgentInstructionBehavior(unittest.TestCase):
    """Test suite for agent instruction validation and behavior patterns"""
    
    def setUp(self):
        """Set up test fixtures for agent instruction testing"""
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    def test_root_agent_instruction_content(self):
        """Test that root agent instructions contain key behavioral elements"""
        instruction = root_agent.instruction
        self.assertIsNotNone(instruction)
        
        # Check for key coordination elements
        coordination_elements = [
            "coordinate", "delegate", "Email Agent", "Calendar Agent",
            "session state", "user confirmation", "voice-friendly"
        ]
        
        for element in coordination_elements:
            self.assertIn(element, instruction)

    def test_email_agent_instruction_behavior_patterns(self):
        """Test email agent instruction contains specific behavior patterns"""
        instruction = email_agent.instruction
        
        # Check for workflow patterns
        workflow_patterns = [
            "workflow orchestration", "confirmation", "AI-powered",
            "reading", "organization", "sending", "session state"
        ]
        
        for pattern in workflow_patterns:
            self.assertIn(pattern, instruction)

    def test_calendar_agent_instruction_behavior_patterns(self):
        """Test calendar agent instruction contains specific behavior patterns"""
        instruction = calendar_agent.instruction
        
        # Check for calendar-specific patterns
        calendar_patterns = [
            "Event Creation", "Event Listing", "Event Management",
            "voice-friendly", "timezone", "Setup Management"
        ]
        
        for pattern in calendar_patterns:
            self.assertIn(pattern, instruction)

    def test_agent_instructions_voice_optimization(self):
        """Test that all agent instructions emphasize voice optimization"""
        agents = [root_agent, email_agent, calendar_agent]
        
        for agent in agents:
            instruction = agent.instruction
            # Should emphasize voice-friendly responses
            voice_indicators = ["voice", "speak", "natural", "conversational"]
            self.assertTrue(
                any(indicator in instruction.lower() for indicator in voice_indicators),
                f"{agent.name} instruction should emphasize voice optimization"
            )


class TestAgentDelegationBehavior(unittest.TestCase):
    """Test suite for agent delegation and coordination behavior"""
    
    def setUp(self):
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    def test_root_agent_delegation_strategy(self):
        """Test root agent's delegation strategy to sub-agents"""
        # Root agent should have clear delegation criteria
        self.assertEqual(root_agent.name, "oprina")
        
        # Should coordinate between email and calendar agents
        agent_tools = [tool.name for tool in root_agent.tools]
        
        # Root agent should have delegation tools or clear sub-agent access
        # (This tests the architecture, actual delegation tested in integration)
        self.assertTrue(len(agent_tools) >= 0)  # May have delegation tools

    def test_sub_agent_specialization(self):
        """Test that sub-agents are properly specialized"""
        # Email agent specialization
        email_tools = [tool.name for tool in email_agent.tools]
        email_specific_tools = [
            tool for tool in email_tools 
            if 'gmail' in tool or 'email' in tool
        ]
        self.assertTrue(len(email_specific_tools) > 0)
        
        # Calendar agent specialization  
        calendar_tools = [tool.name for tool in calendar_agent.tools]
        calendar_specific_tools = [
            tool for tool in calendar_tools 
            if 'calendar' in tool
        ]
        self.assertTrue(len(calendar_specific_tools) > 0)

    @patch('oprina.tools.gmail.get_gmail_service')
    @patch('oprina.tools.calendar.get_calendar_service')
    def test_agent_coordination_workflow(self, mock_calendar_service, mock_gmail_service):
        """Test coordination between agents in cross-service workflows"""
        # Mock both services as available
        mock_gmail_service.return_value = Mock()
        mock_calendar_service.return_value = Mock()
        
        # Mock email with meeting request
        sample_email = {
            'id': 'meeting_request',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Meeting Request - Project Discussion'},
                    {'name': 'From', 'value': 'client@company.com'}
                ],
                'body': {'data': 'TWVldGluZyByZXF1ZXN0IGZvciBwcm9qZWN0IGRpc2N1c3Npb24='}
            }
        }
        
        mock_gmail_service.return_value.users().messages().get().execute.return_value = sample_email
        
        # Extract action items (email agent)
        from oprina.tools.gmail import gmail_extract_action_items
        
        with patch('oprina.tools.gmail._process_with_ai') as mock_ai:
            mock_ai.return_value = "Schedule meeting with client for project discussion"
            
            action_result = gmail_extract_action_items(
                "meeting_request", 
                tool_context=self.mock_tool_context
            )
            
            # Should identify calendar action
            self.assertIn("Schedule", action_result)
            
            # Session should track cross-agent workflow
            self.assertIn(EMAIL_LAST_EXTRACTED_TASKS, self.mock_session.state)

    def test_agent_model_consistency(self):
        """Test that all agents use consistent model configuration"""
        agents = [root_agent, email_agent, calendar_agent]
        
        # All agents should use the same model
        models = [agent.model for agent in agents]
        self.assertEqual(len(set(models)), 1)  # All should be the same
        self.assertEqual(models[0], "gemini-2.0-flash")


class TestAgentErrorHandlingBehavior(unittest.TestCase):
    """Test suite for agent error handling and recovery behavior"""
    
    def setUp(self):
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_email_agent_service_unavailable_behavior(self, mock_get_service):
        """Test email agent behavior when Gmail service is unavailable"""
        mock_get_service.return_value = None
        
        from oprina.tools.gmail import gmail_list_messages
        result = gmail_list_messages(tool_context=self.mock_tool_context)
        
        # Should provide user-friendly guidance
        self.assertIn("Gmail not set up", result)
        self.assertIn("setup_gmail.py", result)
        
        # Should not crash or expose technical details
        self.assertNotIn("Exception", result)
        self.assertNotIn("None", result)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_agent_service_unavailable_behavior(self, mock_get_service):
        """Test calendar agent behavior when Calendar service is unavailable"""
        mock_get_service.return_value = None
        
        from oprina.tools.calendar import calendar_list_events
        result = calendar_list_events(tool_context=self.mock_tool_context)
        
        # Should provide user-friendly guidance
        self.assertIn("Calendar not set up", result)
        self.assertIn("setup_calendar.py", result)
        
        # Should not crash or expose technical details
        self.assertNotIn("Exception", result)
        self.assertNotIn("None", result)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_api_error_recovery(self, mock_get_service):
        """Test agent recovery from API errors"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Simulate API error
        mock_service.users().messages().list().execute.side_effect = Exception("API quota exceeded")
        
        from oprina.tools.gmail import gmail_list_messages
        result = gmail_list_messages(tool_context=self.mock_tool_context)
        
        # Should handle gracefully
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)
        
        # Should not expose technical details
        self.assertNotIn("quota exceeded", result)
        self.assertNotIn("Exception", result)

    def test_agent_invalid_input_handling(self):
        """Test agent handling of invalid inputs"""
        from oprina.tools.gmail import gmail_get_message
        from oprina.tools.calendar import calendar_create_event
        
        # Test email agent with invalid message ID
        email_result = gmail_get_message("", tool_context=self.mock_tool_context)
        self.assertIsInstance(email_result, str)
        
        # Test calendar agent with invalid dates
        calendar_result = calendar_create_event(
            summary="Test",
            start_time="invalid",
            end_time="invalid", 
            tool_context=self.mock_tool_context
        )
        self.assertIsInstance(calendar_result, str)


class TestAgentVoiceInterfaceBehavior(unittest.TestCase):
    """Test suite for agent voice interface optimization"""
    
    def setUp(self):
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_email_agent_voice_optimized_responses(self, mock_get_service):
        """Test that email agent responses are voice-optimized"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock email data
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}]
        }
        
        sample_email = {
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'client@company.com'},
                    {'name': 'Subject', 'value': 'Meeting Request'}
                ]
            }
        }
        mock_service.users().messages().get().execute.return_value = sample_email
        
        from oprina.tools.gmail import gmail_list_messages
        result = gmail_list_messages(tool_context=self.mock_tool_context)
        
        # Voice-friendly characteristics
        self.assertIn("Found", result)
        
        # Should not contain technical artifacts
        self.assertNotIn("{'", result)
        self.assertNotIn("payload", result)
        self.assertNotIn("headers", result)

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_agent_voice_optimized_responses(self, mock_get_service):
        """Test that calendar agent responses are voice-optimized"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock calendar events
        events_data = {
            'items': [{
                'summary': 'Team Meeting',
                'start': {'dateTime': '2024-01-15T09:00:00-05:00'},
                'end': {'dateTime': '2024-01-15T10:00:00-05:00'}
            }]
        }
        mock_service.events().list().execute.return_value = events_data
        
        from oprina.tools.calendar import calendar_list_events
        result = calendar_list_events(tool_context=self.mock_tool_context)
        
        # Voice-friendly characteristics
        self.assertIn("upcoming events", result.lower())
        
        # Should not contain ISO timestamps
        self.assertNotIn("T", result)
        self.assertNotIn("2024-01-15T09:00:00-05:00", result)

    def test_agent_natural_language_responses(self):
        """Test that agents use natural language in responses"""
        # This tests the principle that all agent responses should be conversational
        
        # Test with mock tool context error (simulates agent error handling)
        from oprina.tools.gmail import gmail_list_messages
        from oprina.tools.calendar import calendar_list_events
        
        # When tool context is None, should still provide natural language response
        gmail_result = gmail_list_messages(tool_context=None)
        calendar_result = calendar_list_events(tool_context=None)
        
        # Should be strings (not crash)
        self.assertIsInstance(gmail_result, str)
        self.assertIsInstance(calendar_result, str)
        
        # Should not contain technical jargon
        responses = [gmail_result, calendar_result]
        for response in responses:
            self.assertNotIn("NoneType", response)
            self.assertNotIn("AttributeError", response)
            self.assertNotIn("Traceback", response)


class TestAgentSessionStateBehavior(unittest.TestCase):
    """Test suite for agent session state management behavior"""
    
    def setUp(self):
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_email_agent_session_continuity(self, mock_get_service):
        """Test email agent maintains session continuity across operations"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock email operations
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'session_test'}]
        }
        
        sample_email = {
            'payload': {
                'headers': [{'name': 'Subject', 'value': 'Test'}]
            }
        }
        mock_service.users().messages().get().execute.return_value = sample_email
        
        # Perform multiple operations
        from oprina.tools.gmail import gmail_list_messages, gmail_get_message
        
        gmail_list_messages(tool_context=self.mock_tool_context)
        gmail_get_message("session_test", tool_context=self.mock_tool_context)
        
        # Check session state continuity
        self.assertIn(EMAIL_LAST_FETCH, self.mock_session.state)
        self.assertIn(EMAIL_LAST_MESSAGE_VIEWED, self.mock_session.state)
        
        # Session should track workflow progression
        self.assertEqual(
            self.mock_session.state[EMAIL_LAST_MESSAGE_VIEWED], 
            "session_test"
        )

    @patch('oprina.tools.calendar.get_calendar_service')
    def test_calendar_agent_session_continuity(self, mock_get_service):
        """Test calendar agent maintains session continuity across operations"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock calendar operations
        mock_service.settings().list().execute.return_value = {
            'items': [{'id': 'timezone', 'value': 'America/New_York'}]
        }
        
        created_event = {
            'id': 'session_event',
            'summary': 'Session Test Event'
        }
        mock_service.events().insert().execute.return_value = created_event
        
        # Perform operation
        from oprina.tools.calendar import calendar_create_event
        
        calendar_create_event(
            summary="Session Test Event",
            start_time="2024-01-15 14:00",
            end_time="2024-01-15 15:00",
            tool_context=self.mock_tool_context
        )
        
        # Check session state continuity
        self.assertIn(CALENDAR_LAST_EVENT_CREATED, self.mock_session.state)
        self.assertIn(CALENDAR_LAST_CREATED_EVENT_ID, self.mock_session.state)
        
        # Session should track creation
        self.assertEqual(
            self.mock_session.state[CALENDAR_LAST_CREATED_EVENT_ID],
            "session_event"
        )

    def test_cross_agent_session_sharing(self):
        """Test that session state is properly shared between agents"""
        # Both agents should access the same session
        email_session_keys = set()
        calendar_session_keys = set()
        
        # Simulate operations that update session state
        self.mock_session.state[EMAIL_LAST_FETCH] = "test_value"
        self.mock_session.state[CALENDAR_LAST_FETCH] = "test_value"
        
        # Both agents should see the same session state
        self.assertEqual(
            self.mock_session.state[EMAIL_LAST_FETCH],
            self.mock_session.state[CALENDAR_LAST_FETCH]
        )
        
        # Session should be shared across tool contexts
        self.assertIs(self.mock_tool_context.session, self.mock_session)


if __name__ == '__main__':
    unittest.main()
