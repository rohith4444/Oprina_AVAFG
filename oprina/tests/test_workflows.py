"""
Tests for Cross-Agent Workflow Functions

Tests the multi-step workflows that coordinate between email_agent and calendar_agent
to accomplish complex user goals.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import workflow functions
from oprina.tools.workflows import (
    schedule_meeting_with_invitation,
    process_emails_for_deadlines_and_schedule,
    coordinate_email_reply_and_meeting
)

# Import coordination utilities
from oprina.common.utils import (
    start_workflow, update_workflow, get_workflow_data,
    pass_data_between_agents
)

# Import session keys
from oprina.common.session_keys import (
    MEETING_COORDINATION_ACTIVE, EMAIL_DEADLINES_FOUND,
    AVAILABILITY_CHECK_RESULTS
)


class TestWorkflowCoordination(unittest.TestCase):
    """Test suite for workflow coordination utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session
        self.mock_tool_context.state = {}

    def test_start_workflow(self):
        """Test workflow initialization"""
        workflow_data = {
            "total_steps": 3,
            "test_data": "sample"
        }
        
        workflow_id = start_workflow(self.mock_tool_context, "test_workflow", workflow_data)
        
        # Should return valid workflow ID
        self.assertIsInstance(workflow_id, str)
        self.assertIn("workflow_test_workflow", workflow_id)
        
        # Should store workflow state
        self.assertIn("active_workflow", self.mock_tool_context.state)
        self.assertEqual(self.mock_tool_context.state["active_workflow"], workflow_id)

    def test_update_workflow(self):
        """Test workflow progress updates"""
        # Start a workflow first
        workflow_data = {"total_steps": 2}
        workflow_id = start_workflow(self.mock_tool_context, "test_workflow", workflow_data)
        
        # Update with step result
        step_result = {"step": "completed_first_action", "result": "success"}
        success = update_workflow(self.mock_tool_context, workflow_id, step_result)
        
        self.assertTrue(success)
        
        # Check workflow state was updated
        workflow_key = f"workflow:{workflow_id}"
        workflow_state = self.mock_tool_context.state[workflow_key]
        self.assertEqual(workflow_state["steps_completed"], 1)
        self.assertEqual(workflow_state["current_step"], 2)

    def test_get_workflow_data(self):
        """Test workflow data retrieval"""
        # Start workflow
        workflow_data = {"test_field": "test_value"}
        workflow_id = start_workflow(self.mock_tool_context, "test_workflow", workflow_data)
        
        # Retrieve workflow data
        retrieved_data = get_workflow_data(self.mock_tool_context, workflow_id)
        
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data["name"], "test_workflow")
        self.assertEqual(retrieved_data["data"]["test_field"], "test_value")

    def test_pass_data_between_agents(self):
        """Test cross-agent data passing"""
        data = {"meeting_id": "12345", "attendee": "john@example.com"}
        
        success = pass_data_between_agents(
            self.mock_tool_context,
            "calendar_agent",
            "email_agent", 
            data,
            "meeting_invitation"
        )
        
        self.assertTrue(success)
        
        # Check transfer data was stored
        transfer_key = "transfer:calendar_agent_to_email_agent"
        self.assertIn(transfer_key, self.mock_tool_context.state)
        self.assertEqual(self.mock_tool_context.state[transfer_key]["data"], data)


class TestMeetingCoordinationWorkflow(unittest.TestCase):
    """Test meeting coordination workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_tool_context = Mock()
        self.mock_tool_context.state = {}

    @patch('oprina.tools.workflows.calendar_list_events')
    @patch('oprina.tools.workflows.calendar_create_event')
    @patch('oprina.tools.workflows.gmail_send_message')
    def test_schedule_meeting_success(self, mock_gmail_send, mock_calendar_create, mock_calendar_list):
        """Test successful meeting coordination"""
        # Mock successful operations
        mock_calendar_list.return_value = "Available time slots"
        mock_calendar_create.return_value = {"id": "event_123", "status": "confirmed"}
        mock_gmail_send.return_value = "Email sent successfully"
        
        result = schedule_meeting_with_invitation(
            attendee_email="john@example.com",
            meeting_subject="Project Meeting",
            tool_context=self.mock_tool_context
        )
        
        # Should succeed
        self.assertIn("Meeting coordination completed successfully", result)
        self.assertIn("john@example.com", result)

    @patch('oprina.tools.workflows.calendar_create_event')
    def test_schedule_meeting_calendar_failure(self, mock_calendar_create):
        """Test meeting coordination when calendar fails"""
        mock_calendar_create.return_value = {"error": "Calendar unavailable"}
        
        result = schedule_meeting_with_invitation(
            attendee_email="john@example.com", 
            meeting_subject="Test Meeting",
            tool_context=self.mock_tool_context
        )
        
        self.assertIn("Could not create calendar event", result)


class TestEmailProcessingWorkflow(unittest.TestCase):
    """Test email processing workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_tool_context = Mock()
        self.mock_tool_context.state = {}

    @patch('oprina.tools.workflows.gmail_list_messages')
    @patch('oprina.tools.workflows.calendar_list_events')
    def test_process_emails_success(self, mock_calendar_list, mock_gmail_list):
        """Test successful email deadline processing"""
        mock_gmail_list.return_value = "Found 10 emails"
        mock_calendar_list.return_value = "Calendar availability"
        
        result = process_emails_for_deadlines_and_schedule(
            tool_context=self.mock_tool_context
        )
        
        self.assertIn("Email Deadline Analysis Complete", result)
        self.assertIn("action items with deadlines", result)


class TestCrossAgentIntegration(unittest.TestCase):
    """Test suite for cross-agent integration workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session
        self.mock_tool_context.state = {}

    @patch('oprina.tools.workflows.gmail_get_message')
    @patch('oprina.tools.workflows.gmail_send_message')
    @patch('oprina.tools.workflows.calendar_create_event')
    def test_coordinate_email_reply_and_meeting_success(self, mock_calendar_create, mock_gmail_send, mock_gmail_get):
        """Test successful email reply and meeting coordination"""
        # Mock email operations
        mock_gmail_get.return_value = """Email Details:
From: sarah@example.com
To: user@example.com
Subject: Project Update
Date: 2025-01-10

Content:
Let's discuss the project updates next week."""
        
        mock_gmail_send.side_effect = [
            "Reply sent successfully to sarah@example.com",
            "Meeting invitation sent successfully"
        ]
        
        # Mock calendar operation
        mock_calendar_create.return_value = {"id": "meeting_67890", "status": "confirmed"}
        
        result = coordinate_email_reply_and_meeting(
            email_reference="1",
            reply_message="Thanks for the update. Let's schedule a meeting to discuss.",
            schedule_follow_up=True,
            tool_context=self.mock_tool_context
        )
        
        # Should return success message
        self.assertIn("Reply sent to sarah@example.com", result)
        self.assertIn("Follow-up meeting scheduled", result)
        self.assertIn("Meeting invitation sent", result)
        
        # Should call all required functions
        mock_gmail_get.assert_called_once()
        self.assertEqual(mock_gmail_send.call_count, 2)  # Reply + invitation
        mock_calendar_create.assert_called_once()

    @patch('oprina.tools.workflows.gmail_get_message')
    @patch('oprina.tools.workflows.gmail_send_message')
    def test_coordinate_email_reply_without_meeting(self, mock_gmail_send, mock_gmail_get):
        """Test email reply coordination without follow-up meeting"""
        # Mock email operations
        mock_gmail_get.return_value = """Email Details:
From: sarah@example.com
Subject: Quick Question"""
        
        mock_gmail_send.return_value = "Reply sent successfully"
        
        result = coordinate_email_reply_and_meeting(
            email_reference="1",
            reply_message="Thanks for your question.",
            schedule_follow_up=False,
            tool_context=self.mock_tool_context
        )
        
        # Should only send reply, no meeting
        self.assertIn("Reply sent to sarah@example.com", result)
        self.assertNotIn("Follow-up meeting", result)
        
        # Should only call reply function once
        mock_gmail_send.assert_called_once()

    def test_coordinate_email_reply_invalid_context(self):
        """Test email reply coordination with invalid tool context"""
        result = coordinate_email_reply_and_meeting(
            email_reference="1",
            reply_message="Test reply",
            tool_context=None
        )
        
        # Should handle gracefully
        self.assertIn("Error coordinating email reply", result)


class TestWorkflowErrorHandling(unittest.TestCase):
    """Test suite for workflow error handling and edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session
        self.mock_tool_context.state = {}

    def test_workflow_with_missing_session_state(self):
        """Test workflow functions with missing session state"""
        # Mock tool context without state
        mock_context = Mock()
        mock_context.session = Mock()
        # Intentionally don't set mock_context.state
        
        result = schedule_meeting_with_invitation(
            attendee_email="test@example.com",
            meeting_subject="Test Meeting",
            tool_context=mock_context
        )
        
        # Should handle gracefully
        self.assertIn("Error coordinating meeting", result)

    @patch('oprina.tools.workflows.gmail_send_message')
    def test_workflow_partial_success(self, mock_gmail_send):
        """Test workflow behavior when some steps succeed and others fail"""
        # Mock email failure
        mock_gmail_send.side_effect = Exception("Email service unavailable")
        
        with patch('oprina.tools.workflows.calendar_create_event') as mock_calendar_create:
            mock_calendar_create.return_value = {"id": "event_123", "status": "confirmed"}
            
            result = schedule_meeting_with_invitation(
                attendee_email="test@example.com",
                meeting_subject="Test Meeting",
                tool_context=self.mock_tool_context
            )
            
            # Should indicate what succeeded and what failed
            self.assertIn("Error coordinating meeting", result)

    def test_workflow_data_validation(self):
        """Test workflow functions with invalid input data"""
        # Test with empty attendee email
        result = schedule_meeting_with_invitation(
            attendee_email="",
            meeting_subject="Test Meeting",
            tool_context=self.mock_tool_context
        )
        
        # Should handle gracefully
        self.assertIsInstance(result, str)

    def test_workflow_state_persistence(self):
        """Test that workflow state persists correctly across operations"""
        # Start multiple workflows
        workflow_data_1 = {"total_steps": 2, "type": "meeting"}
        workflow_data_2 = {"total_steps": 3, "type": "email_processing"}
        
        workflow_id_1 = start_workflow(self.mock_tool_context, "meeting_workflow", workflow_data_1)
        workflow_id_2 = start_workflow(self.mock_tool_context, "email_workflow", workflow_data_2)
        
        # Both should be stored separately
        self.assertNotEqual(workflow_id_1, workflow_id_2)
        
        # Both should be retrievable
        data_1 = get_workflow_data(self.mock_tool_context, workflow_id_1)
        data_2 = get_workflow_data(self.mock_tool_context, workflow_id_2)
        
        self.assertEqual(data_1["data"]["type"], "meeting")
        self.assertEqual(data_2["data"]["type"], "email_processing")


class TestWorkflowIntegrationScenarios(unittest.TestCase):
    """Test suite for complete workflow integration scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_session = Mock()
        self.mock_session.state = {}
        self.mock_tool_context = Mock()
        self.mock_tool_context.session = self.mock_session
        self.mock_tool_context.state = {}

    @patch('oprina.tools.workflows.gmail_list_messages')
    @patch('oprina.tools.workflows.calendar_list_events')
    @patch('oprina.tools.workflows.calendar_create_event')
    @patch('oprina.tools.workflows.gmail_send_message')
    def test_complete_daily_workflow_scenario(self, mock_gmail_send, mock_calendar_create, 
                                            mock_calendar_list, mock_gmail_list):
        """Test a complete daily workflow scenario combining multiple operations"""
        # Mock successful operations
        mock_gmail_list.return_value = "Found recent emails with deadlines"
        mock_calendar_list.return_value = "Found available time slots"
        mock_calendar_create.return_value = {"id": "task_event_123"}
        mock_gmail_send.return_value = "Confirmation email sent"
        
        # Step 1: Process emails for deadlines
        deadline_result = process_emails_for_deadlines_and_schedule(
            days_to_check=5,
            tool_context=self.mock_tool_context
        )
        
        # Should succeed
        self.assertIn("Email Deadline Analysis Complete", deadline_result)
        
        # Step 2: Schedule a meeting with someone
        meeting_result = schedule_meeting_with_invitation(
            attendee_email="colleague@example.com",
            meeting_subject="Weekly Sync",
            tool_context=self.mock_tool_context
        )
        
        # Should also succeed and not interfere with previous workflow
        self.assertIn("Meeting coordination completed successfully", meeting_result)
        
        # Both workflows should have stored their data separately
        self.assertIn(EMAIL_DEADLINES_FOUND, self.mock_tool_context.state)
        self.assertIn(MEETING_COORDINATION_ACTIVE, self.mock_tool_context.state)

    def test_workflow_state_cleanup(self):
        """Test that completed workflows don't interfere with new ones"""
        # Start and complete a workflow
        workflow_data = {"total_steps": 1}
        workflow_id = start_workflow(self.mock_tool_context, "test_workflow", workflow_data)
        
        # Complete it
        update_workflow(self.mock_tool_context, workflow_id, {"step": "completed"})
        
        # Start a new workflow
        new_workflow_id = start_workflow(self.mock_tool_context, "new_workflow", workflow_data)
        
        # Should be different and independent
        self.assertNotEqual(workflow_id, new_workflow_id)
        self.assertEqual(self.mock_tool_context.state["active_workflow"], new_workflow_id)


if __name__ == '__main__':
    unittest.main() 