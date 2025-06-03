# End-to-End Workflow Testing Plan

## Overview

This document outlines the testing strategy for the end-to-end workflow tests of the Oprina application. The tests are designed to verify that the application's components work together correctly in real-world scenarios.

## Test Structure

The end-to-end tests are organized into two main categories:

1. **Voice Workflow Tests** (`test_voice_workflows.py`)
   - Tests the voice agent's ability to handle various workflows
   - Verifies integration with other agents (email, calendar, content)
   - Tests error handling and recovery

2. **ADK Web Interface Tests** (`test_adk_web.py`)
   - Tests the web interface functionality
   - Verifies session management
   - Tests agent interaction through the web interface
   - Tests error handling in the web interface

## Test Cases

### Voice Workflow Tests

1. **Email Workflow** (`test_voice_email_workflow`)
   - Tests the voice agent's ability to handle email-related requests
   - Verifies that the email agent is called correctly
   - Checks that the response contains email-related content

2. **Calendar Workflow** (`test_voice_calendar_workflow`)
   - Tests the voice agent's ability to handle calendar-related requests
   - Verifies that the calendar agent is called correctly
   - Checks that the response contains calendar-related content

3. **Content Workflow** (`test_voice_content_workflow`)
   - Tests the voice agent's ability to handle content-related requests
   - Verifies that the content agent is called correctly
   - Checks that the response contains content-related information

4. **Complex Multi-Agent Workflow** (`test_complex_multi_agent_workflow`)
   - Tests the voice agent's ability to handle complex requests involving multiple agents
   - Verifies that the appropriate agents are called in the correct order
   - Checks that the response contains information from all relevant agents

5. **Error Handling** (`test_error_handling`)
   - Tests the voice agent's ability to handle errors gracefully
   - Verifies that appropriate error messages are returned
   - Checks that the system recovers from errors

### ADK Web Interface Tests

1. **Web Startup** (`test_adk_web_startup`)
   - Tests that the web server starts up correctly
   - Verifies that the health check endpoint returns the expected response
   - Checks that the list-apps endpoint returns the expected response

2. **Web Agent Interaction** (`test_web_agent_interaction`)
   - Tests interaction with agents through the web interface
   - Verifies that messages are sent to the agent correctly
   - Checks that responses from the agent are displayed correctly

3. **Web Session Management** (`test_web_session_management`)
   - Tests session management in the web interface
   - Verifies that sessions are created, retrieved, listed, and deleted correctly
   - Checks that session data is stored and retrieved correctly

4. **Web Error Handling** (`test_web_error_handling`)
   - Tests error handling in the web interface
   - Verifies that appropriate error responses are returned for invalid requests
   - Checks that server errors are handled gracefully

## Running the Tests

### Prerequisites

- Python 3.8 or higher
- All dependencies installed (see `requirements-test.txt`)
- ADK CLI installed and configured
- Google Cloud credentials configured (if using Vertex AI)

### Running All Tests

To run all end-to-end tests:

```bash
pytest tests/e2e/ -v
```

### Running Specific Test Files

To run a specific test file:

```bash
pytest tests/e2e/test_voice_workflows.py -v
pytest tests/e2e/test_adk_web.py -v
```

### Running Specific Test Cases

To run a specific test case:

```bash
pytest tests/e2e/test_voice_workflows.py::TestVoiceWorkflows::test_voice_email_workflow -v
pytest tests/e2e/test_adk_web.py::TestAdkWeb::test_web_agent_interaction -v
```

## Test Environment

The tests use the following environment variables:

- `MEMORY_SERVICE_TYPE=inmemory`
- `SESSION_SERVICE_TYPE=inmemory`
- `ADK_APP_NAME=oprina`
- `ENVIRONMENT=test`
- `DEBUG=true`

These variables are set in the `conftest.py` file.

## Mocking Strategy

The tests use the following mocking strategy:

- **MCP Client**: Mocked to avoid actual network calls
- **Speech Recognition**: Mocked to simulate voice input
- **Email Service**: Mocked to avoid actual email sending
- **Calendar Service**: Mocked to avoid actual calendar operations
- **Content Service**: Mocked to avoid actual content generation

## Test Data

The tests use the following test data:

- **Session Data**: Sample session data for testing session management
- **Audio Data**: Sample audio data for testing voice input
- **Email Content**: Sample email content for testing email workflows
- **Calendar Event**: Sample calendar event for testing calendar workflows

## Continuous Integration

These tests are designed to be run in a continuous integration environment. The following steps should be taken to integrate them into the CI pipeline:

1. Install dependencies
2. Set up the test environment
3. Run the tests
4. Report test results

## Troubleshooting

If you encounter issues with the tests, check the following:

1. **Environment Variables**: Ensure all required environment variables are set
2. **Dependencies**: Ensure all dependencies are installed
3. **Mocking**: Ensure all required services are properly mocked
4. **Test Data**: Ensure all required test data is available

## Future Improvements

The following improvements are planned for the end-to-end tests:

1. **More Test Cases**: Add more test cases to cover additional scenarios
2. **Performance Testing**: Add performance testing to measure response times
3. **Load Testing**: Add load testing to measure system performance under load
4. **Security Testing**: Add security testing to identify vulnerabilities 