"""
Unit tests for Gmail tools - Testing individual Gmail API functions
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(4):  # Go up 4 levels from tests/unit/test_gmail_tools.py
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the functions we're testing
from oprina.tools.gmail import (
    gmail_list_messages, gmail_get_message, gmail_search_messages,
    gmail_send_message, gmail_reply_to_message, gmail_mark_as_read,
    gmail_archive_message, gmail_delete_message, gmail_generate_email,
    gmail_summarize_message, gmail_analyze_sentiment, gmail_extract_action_items,
    gmail_generate_reply, gmail_confirm_and_send, gmail_confirm_and_reply,
    gmail_parse_subject_and_body, _extract_message_body
)

# Import session key constants
from oprina.common.session_keys import (
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_LAST_QUERY,
    EMAIL_RESULTS_COUNT, EMAIL_LAST_SENT_TO, EMAIL_LAST_SENT,
    EMAIL_LAST_MESSAGE_VIEWED, EMAIL_LAST_MESSAGE_VIEWED_AT,
    EMAIL_LAST_SENT_SUBJECT, EMAIL_LAST_SENT_ID,
    EMAIL_LAST_AI_SUMMARY, EMAIL_LAST_AI_SUMMARY_AT,
    EMAIL_LAST_SENTIMENT_ANALYSIS, EMAIL_LAST_SENTIMENT_ANALYSIS_AT,
    EMAIL_LAST_EXTRACTED_TASKS, EMAIL_LAST_TASK_EXTRACTION_AT,
    EMAIL_LAST_GENERATED_REPLY, EMAIL_LAST_REPLY_GENERATION_AT,
    EMAIL_LAST_GENERATED_EMAIL, EMAIL_LAST_EMAIL_GENERATION_AT,
    EMAIL_LAST_ARCHIVED, EMAIL_LAST_REPLY_SENT
)


class TestGmailTools(unittest.TestCase):
    """Test suite for Gmail API tools"""
    
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
        self.sample_message = {
            'id': 'test_message_123',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'Date', 'value': 'Mon, 01 Jan 2024 12:00:00 +0000'},
                    {'name': 'To', 'value': 'user@example.com'}
                ],
                'body': {'data': 'VGVzdCBtZXNzYWdlIGJvZHk='}  # Base64 encoded "Test message body"
            }
        }
        
        self.sample_messages_list = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'},
                {'id': 'msg3'}
            ]
        }

    # =============================================================================
    # Reading Tools Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_list_messages_success(self, mock_get_service):
        """Test successful email listing"""
        # Setup mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock API calls
        mock_service.users().messages().list().execute.return_value = self.sample_messages_list
        mock_service.users().messages().get().execute.return_value = self.sample_message
        
        # Test the function
        result = gmail_list_messages(query="test", max_results=5, tool_context=self.mock_tool_context)
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn("Found", result)
        
        # Check session state updates
        self.assertIn(EMAIL_LAST_FETCH, self.mock_session.state)
        self.assertEqual(self.mock_session.state[EMAIL_LAST_QUERY], "test")
        self.assertEqual(self.mock_session.state[EMAIL_RESULTS_COUNT], 3)
        self.assertIn(EMAIL_CURRENT_RESULTS, self.mock_session.state)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_list_messages_no_service(self, mock_get_service):
        """Test email listing when Gmail not set up"""
        mock_get_service.return_value = None
        
        result = gmail_list_messages(tool_context=self.mock_tool_context)
        
        self.assertIn("Gmail not set up", result)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_get_message_success(self, mock_get_service):
        """Test getting specific message"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = self.sample_message
        
        result = gmail_get_message("test_message_123", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Email Details:", result)
        self.assertIn("Test Subject", result)
        
        # Check session state
        self.assertEqual(self.mock_session.state[EMAIL_LAST_MESSAGE_VIEWED], "test_message_123")
        self.assertIn(EMAIL_LAST_MESSAGE_VIEWED_AT, self.mock_session.state)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_search_messages_success(self, mock_get_service):
        """Test email search functionality"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().list().execute.return_value = self.sample_messages_list
        mock_service.users().messages().get().execute.return_value = self.sample_message
        
        result = gmail_search_messages("from:test@example.com", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Found", result)

    # =============================================================================
    # Sending Tools Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_send_message_success(self, mock_get_service):
        """Test successful email sending"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock successful send
        mock_service.users().messages().send().execute.return_value = {'id': 'sent_123'}
        
        result = gmail_send_message(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("sent successfully", result)
        
        # Check session state
        self.assertEqual(self.mock_session.state[EMAIL_LAST_SENT_TO], "test@example.com")
        self.assertEqual(self.mock_session.state[EMAIL_LAST_SENT_SUBJECT], "Test Subject")
        self.assertEqual(self.mock_session.state[EMAIL_LAST_SENT_ID], "sent_123")

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_reply_to_message_success(self, mock_get_service):
        """Test successful reply to message"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock getting original message
        mock_service.users().messages().get().execute.return_value = self.sample_message
        # Mock successful reply
        mock_service.users().messages().send().execute.return_value = {'id': 'reply_123'}
        
        result = gmail_reply_to_message(
            message_id="test_message_123",
            reply_body="Test reply",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Reply sent", result)

    # =============================================================================
    # Organization Tools Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_mark_as_read_success(self, mock_get_service):
        """Test marking message as read"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        result = gmail_mark_as_read("test_message_123", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("marked as read", result)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_archive_message_success(self, mock_get_service):
        """Test archiving message"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        result = gmail_archive_message("test_message_123", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("archived", result)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_delete_message_success(self, mock_get_service):
        """Test deleting message"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        result = gmail_delete_message("test_message_123", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("deleted", result)

    # =============================================================================
    # AI Tools Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail._process_with_ai')
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_summarize_message_success(self, mock_get_service, mock_ai_process):
        """Test AI summarization of message"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = self.sample_message
        
        mock_ai_process.return_value = "This is a test summary"
        
        result = gmail_summarize_message("test_message_123", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Summary:", result)
        
        # Check session state
        self.assertEqual(self.mock_session.state[EMAIL_LAST_AI_SUMMARY], "This is a test summary")
        self.assertIn(EMAIL_LAST_AI_SUMMARY_AT, self.mock_session.state)

    @patch('oprina.tools.gmail._process_with_ai')
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_analyze_sentiment_success(self, mock_get_service, mock_ai_process):
        """Test AI sentiment analysis"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = self.sample_message
        
        mock_ai_process.return_value = "Positive sentiment"
        
        result = gmail_analyze_sentiment("test_message_123", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Sentiment Analysis:", result)
        
        # Check session state
        self.assertEqual(self.mock_session.state[EMAIL_LAST_SENTIMENT_ANALYSIS], "Positive sentiment")
        self.assertIn(EMAIL_LAST_SENTIMENT_ANALYSIS_AT, self.mock_session.state)

    @patch('oprina.tools.gmail._process_with_ai')
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_extract_action_items_success(self, mock_get_service, mock_ai_process):
        """Test AI action item extraction"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = self.sample_message
        
        mock_ai_process.return_value = "1. Review document\n2. Schedule meeting"
        
        result = gmail_extract_action_items("test_message_123", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Action Items:", result)
        
        # Check session state
        self.assertEqual(self.mock_session.state[EMAIL_LAST_EXTRACTED_TASKS], "1. Review document\n2. Schedule meeting")
        self.assertIn(EMAIL_LAST_TASK_EXTRACTION_AT, self.mock_session.state)

    @patch('oprina.tools.gmail._process_with_ai')
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_generate_reply_success(self, mock_get_service, mock_ai_process):
        """Test AI reply generation"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = self.sample_message
        
        mock_ai_process.return_value = "Thank you for your email. I will review and get back to you."
        
        result = gmail_generate_reply(
            "test_message_123", 
            "polite acknowledgment", 
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Generated Reply:", result)
        
        # Check session state
        self.assertEqual(self.mock_session.state[EMAIL_LAST_GENERATED_REPLY], 
                        "Thank you for your email. I will review and get back to you.")
        self.assertIn(EMAIL_LAST_REPLY_GENERATION_AT, self.mock_session.state)

    # =============================================================================
    # Composition Tools Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail._process_with_ai')
    def test_gmail_generate_email_success(self, mock_ai_process):
        """Test AI email generation"""
        mock_ai_process.return_value = "Subject: Meeting Request\n\nDear John,\n\nI would like to schedule a meeting..."
        
        result = gmail_generate_email(
            to="john@example.com",
            subject_intent="meeting request",
            email_intent="schedule project discussion",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Generated Email:", result)
        
        # Check session state
        self.assertIn(EMAIL_LAST_GENERATED_EMAIL, self.mock_session.state)
        self.assertIn(EMAIL_LAST_EMAIL_GENERATION_AT, self.mock_session.state)

    def test_gmail_parse_subject_and_body(self):
        """Test parsing AI generated email content"""
        ai_content = "Subject: Test Subject\n\nDear John,\n\nThis is the email body."
        
        subject, body = gmail_parse_subject_and_body(ai_content, tool_context=self.mock_tool_context)
        
        self.assertEqual(subject, "Test Subject")
        self.assertIn("Dear John", body)

    # =============================================================================
    # Workflow Tools Tests  
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_confirm_and_send_success(self, mock_get_service):
        """Test confirm and send workflow"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().send().execute.return_value = {'id': 'sent_123'}
        
        result = gmail_confirm_and_send(
            to="test@example.com",
            subject="Test",
            body="Test body",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Email sent", result)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_gmail_confirm_and_reply_success(self, mock_get_service):
        """Test confirm and reply workflow"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = self.sample_message
        mock_service.users().messages().send().execute.return_value = {'id': 'reply_123'}
        
        result = gmail_confirm_and_reply(
            message_id="test_message_123",
            reply_body="Test reply",
            tool_context=self.mock_tool_context
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Reply sent", result)

    # =============================================================================
    # Helper Function Tests
    # =============================================================================
    
    def test_extract_message_body_text(self):
        """Test extracting plain text from message body"""
        payload = {
            'body': {
                'data': 'VGVzdCBtZXNzYWdlIGJvZHk='  # Base64 for "Test message body"
            }
        }
        
        result = _extract_message_body(payload)
        self.assertEqual(result, "Test message body")

    def test_extract_message_body_multipart(self):
        """Test extracting text from multipart message"""
        payload = {
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {
                        'data': 'VGVzdCBtZXNzYWdl'  # Base64 for "Test message"
                    }
                },
                {
                    'mimeType': 'text/html',
                    'body': {
                        'data': 'PGh0bWw+VGVzdDwvaHRtbD4='  # Base64 for "<html>Test</html>"
                    }
                }
            ]
        }
        
        result = _extract_message_body(payload)
        self.assertIn("Test message", result)

    # =============================================================================
    # Error Handling Tests
    # =============================================================================
    
    def test_functions_without_tool_context(self):
        """Test that functions handle missing tool context gracefully"""
        # These should not crash even without tool context
        result1 = gmail_list_messages(tool_context=None)
        result2 = gmail_get_message("test_id", tool_context=None)
        
        self.assertIsInstance(result1, str)
        self.assertIsInstance(result2, str)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_api_error_handling(self, mock_get_service):
        """Test handling of Gmail API errors"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Simulate API error
        mock_service.users().messages().list().execute.side_effect = Exception("API Error")
        
        result = gmail_list_messages(tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)


# =============================================================================
# GMAIL AGENT BEHAVIOR TESTS (NEW)
# =============================================================================

class TestGmailAgentBehavior(unittest.TestCase):
    """Test suite for Gmail Agent behavior and integration"""
    
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
        
        # Sample email for agent testing
        self.sample_email = {
            'id': 'agent_test_msg',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'client@company.com'},
                    {'name': 'Subject', 'value': 'Meeting Request - Project Discussion'},
                    {'name': 'Date', 'value': 'Mon, 01 Jan 2024 12:00:00 +0000'},
                    {'name': 'To', 'value': 'user@company.com'}
                ],
                'body': {'data': 'TWVldGluZyByZXF1ZXN0IGZvciBwcm9qZWN0IGRpc2N1c3Npb24='}
            }
        }

    # =============================================================================
    # Agent Configuration Tests
    # =============================================================================
    
    def test_gmail_agent_configuration(self):
        """Test that Gmail agent is properly configured"""
        from oprina.sub_agents.email.agent import email_agent
        
        # Test agent properties
        self.assertEqual(email_agent.name, "email_agent")
        self.assertEqual(email_agent.model, "gemini-2.0-flash")
        self.assertIn("Gmail operations", email_agent.description)
        
        # Test that agent has all expected tools
        tool_names = [tool.name for tool in email_agent.tools]
        expected_tools = [
            "gmail_list_messages", "gmail_get_message", "gmail_search_messages",
            "gmail_send_message", "gmail_reply_to_message",
            "gmail_mark_as_read", "gmail_archive_message", "gmail_delete_message",
            "gmail_summarize_message", "gmail_analyze_sentiment", 
            "gmail_extract_action_items", "gmail_generate_reply",
            "gmail_generate_email", "gmail_confirm_and_send", "gmail_confirm_and_reply"
        ]
        
        for tool_name in expected_tools:
            self.assertIn(tool_name, tool_names)

    def test_gmail_agent_instruction_content(self):
        """Test that Gmail agent instructions contain key behavior elements"""
        from oprina.sub_agents.email.agent import email_agent
        
        instruction = email_agent.instruction
        self.assertIsNotNone(instruction)
        
        # Check for key instruction components
        key_elements = [
            "Email Agent", "Gmail operations", "AI-powered", 
            "workflow orchestration", "confirmation", "session state"
        ]
        
        for element in key_elements:
            self.assertIn(element, instruction)

    # =============================================================================
    # Agent Workflow Behavior Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_email_reading_workflow(self, mock_get_service):
        """Test agent's email reading workflow behavior"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock email search results
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }
        mock_service.users().messages().get().execute.return_value = self.sample_email
        
        # Test agent workflow: search -> present results -> offer actions
        result = gmail_search_messages("from:client@company.com", tool_context=self.mock_tool_context)
        
        # Agent should provide user-friendly results
        self.assertIsInstance(result, str)
        self.assertIn("Found", result)
        
        # Should maintain workflow state
        self.assertIn(EMAIL_CURRENT_RESULTS, self.mock_session.state)
        self.assertIn(EMAIL_LAST_QUERY, self.mock_session.state)

    @patch('oprina.tools.gmail._process_with_ai')
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_ai_content_processing_workflow(self, mock_get_service, mock_ai):
        """Test agent's AI content processing workflow"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = self.sample_email
        
        # Mock AI processing
        mock_ai.return_value = "Client wants to schedule project discussion meeting"
        
        # Test AI workflow: analyze -> process -> present insights
        result = gmail_summarize_message("agent_test_msg", tool_context=self.mock_tool_context)
        
        # Agent should provide actionable insights
        self.assertIn("Summary:", result)
        self.assertIn("Client wants to schedule", result)
        
        # Should track AI processing in session
        self.assertIn(EMAIL_LAST_AI_SUMMARY, self.mock_session.state)
        self.assertIn(EMAIL_LAST_AI_SUMMARY_AT, self.mock_session.state)

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_email_composition_workflow(self, mock_get_service):
        """Test agent's email composition workflow"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock successful send
        mock_service.users().messages().send().execute.return_value = {'id': 'sent_123'}
        
        # Test composition workflow: generate -> confirm -> send
        result = gmail_confirm_and_send(
            to="client@company.com",
            subject="Re: Meeting Request",
            body="Thank you for your meeting request. I'm available tomorrow at 2 PM.",
            tool_context=self.mock_tool_context
        )
        
        # Agent should provide confirmation and guidance
        self.assertIn("Email sent", result)
        
        # Should track composition in session
        self.assertIn(EMAIL_LAST_SENT_TO, self.mock_session.state)

    # =============================================================================
    # Agent Error Recovery and Guidance Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_handles_setup_not_configured(self, mock_get_service):
        """Test agent behavior when Gmail is not set up"""
        mock_get_service.return_value = None
        
        result = gmail_list_messages(tool_context=self.mock_tool_context)
        
        # Agent should provide clear setup guidance
        self.assertIn("Gmail not set up", result)
        self.assertIn("python setup_gmail.py", result)
        
        # Should be voice-friendly guidance
        self.assertNotIn("Error:", result)  # No technical error messages

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_error_recovery_behavior(self, mock_get_service):
        """Test agent's error recovery and user guidance"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Simulate API error
        mock_service.users().messages().list().execute.side_effect = Exception("API Error")
        
        result = gmail_list_messages(tool_context=self.mock_tool_context)
        
        # Agent should provide user-friendly error handling
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)
        # Should not expose technical details
        self.assertNotIn("Exception", result)
        self.assertNotIn("Traceback", result)

    def test_agent_handles_invalid_input_gracefully(self):
        """Test agent handles invalid inputs without crashing"""
        # Test with invalid message ID
        result = gmail_get_message("invalid-id", tool_context=self.mock_tool_context)
        
        self.assertIsInstance(result, str)
        # Should provide helpful guidance, not crash

    # =============================================================================
    # Agent Voice Interface Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_voice_friendly_responses(self, mock_get_service):
        """Test that agent responses are optimized for voice interaction"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock email data for voice testing
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}, {'id': 'msg3'}]
        }
        mock_service.users().messages().get().execute.return_value = self.sample_email
        
        result = gmail_list_messages(query="from:client", tool_context=self.mock_tool_context)
        
        # Voice-friendly characteristics
        self.assertIn("Found", result)
        
        # Should use natural language
        result_lower = result.lower()
        voice_indicators = ['found', 'from:', 'subject:']
        self.assertTrue(any(indicator in result_lower for indicator in voice_indicators))
        
        # Should not contain technical artifacts
        self.assertNotIn("{'", result)  # No dict representations
        self.assertNotIn("payload", result)  # No technical terms

    @patch('oprina.tools.gmail._process_with_ai')
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_ai_insights_voice_optimized(self, mock_get_service, mock_ai):
        """Test that AI insights are voice-optimized"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = self.sample_email
        
        # Mock AI with actionable insights
        mock_ai.return_value = "Action needed: Schedule meeting with client for project discussion"
        
        result = gmail_extract_action_items("agent_test_msg", tool_context=self.mock_tool_context)
        
        # Should present insights in speakable format
        self.assertIn("Action Items:", result)
        self.assertIn("Action needed", result)
        
        # Should be conversational
        self.assertNotIn("TODO:", result)  # Not technical
        self.assertNotIn("[]", result)     # Not list notation

    # =============================================================================
    # Agent State Management Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_session_state_persistence(self, mock_get_service):
        """Test that agent properly maintains session state across operations"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock email operations
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}]
        }
        mock_service.users().messages().get().execute.return_value = self.sample_email
        
        # Perform multiple operations
        gmail_list_messages(tool_context=self.mock_tool_context)
        gmail_get_message("msg1", tool_context=self.mock_tool_context)
        
        # Check session state continuity
        self.assertIn(EMAIL_LAST_FETCH, self.mock_session.state)
        self.assertIn(EMAIL_LAST_MESSAGE_VIEWED, self.mock_session.state)
        self.assertIn(EMAIL_CURRENT_RESULTS, self.mock_session.state)
        
        # State should be available for subsequent operations
        self.assertEqual(self.mock_session.state[EMAIL_LAST_MESSAGE_VIEWED], "msg1")

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_workflow_context_preservation(self, mock_get_service):
        """Test agent preserves workflow context across multiple steps"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Step 1: Search emails
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'workflow_msg'}]
        }
        mock_service.users().messages().get().execute.return_value = self.sample_email
        
        gmail_search_messages("meeting request", tool_context=self.mock_tool_context)
        
        # Step 2: Read specific email
        gmail_get_message("workflow_msg", tool_context=self.mock_tool_context)
        
        # Step 3: Archive email
        gmail_archive_message("workflow_msg", tool_context=self.mock_tool_context)
        
        # Verify workflow continuity in session state
        self.assertEqual(self.mock_session.state[EMAIL_LAST_QUERY], "meeting request")
        self.assertEqual(self.mock_session.state[EMAIL_LAST_MESSAGE_VIEWED], "workflow_msg")
        self.assertIn(EMAIL_LAST_ARCHIVED, self.mock_session.state)

    # =============================================================================
    # Agent Confirmation and Safety Tests
    # =============================================================================
    
    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_confirmation_workflow(self, mock_get_service):
        """Test agent's confirmation workflow for sending emails"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.users().messages().send().execute.return_value = {'id': 'confirmed_send'}
        
        # Test confirmation workflow
        result = gmail_confirm_and_send(
            to="test@example.com",
            subject="Test Subject",
            body="Test body content",
            tool_context=self.mock_tool_context
        )
        
        # Should indicate successful send after confirmation
        self.assertIn("Email sent", result)
        
        # Should track confirmed send in session
        self.assertIn(EMAIL_LAST_SENT_TO, self.mock_session.state)
        self.assertEqual(self.mock_session.state[EMAIL_LAST_SENT_TO], "test@example.com")

    @patch('oprina.tools.gmail.get_gmail_service')
    def test_agent_reply_confirmation_workflow(self, mock_get_service):
        """Test agent's reply confirmation workflow"""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock getting original message
        mock_service.users().messages().get().execute.return_value = self.sample_email
        # Mock successful reply
        mock_service.users().messages().send().execute.return_value = {'id': 'reply_sent'}
        
        result = gmail_confirm_and_reply(
            message_id="agent_test_msg",
            reply_body="Thank you for your meeting request.",
            tool_context=self.mock_tool_context
        )
        
        # Should confirm reply was sent
        self.assertIn("Reply sent", result)
        
        # Should track reply in session
        self.assertIn(EMAIL_LAST_REPLY_SENT, self.mock_session.state)


if __name__ == '__main__':
    unittest.main()
