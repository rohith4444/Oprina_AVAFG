# End-to-End Tests for Oprina

This directory contains end-to-end tests for the Oprina application. These tests verify that the application's components work together correctly in real-world scenarios.

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

## Running the Tests

### Using the Test Runner Script

The easiest way to run the tests is to use the provided test runner script:

```bash
# Run all tests
python tests/e2e/run_tests.py

# Run specific test files
python tests/e2e/run_tests.py --files tests/e2e/test_voice_workflows.py tests/e2e/test_adk_web.py

# Run specific test cases
python tests/e2e/run_tests.py --cases tests/e2e/test_voice_workflows.py::TestVoiceWorkflows::test_voice_email_workflow

# Run tests in verbose mode
python tests/e2e/run_tests.py --verbose
```

### Using pytest Directly

You can also run the tests directly using pytest:

```bash
# Run all tests
pytest tests/e2e/

# Run specific test files
pytest tests/e2e/test_voice_workflows.py tests/e2e/test_adk_web.py

# Run specific test cases
pytest tests/e2e/test_voice_workflows.py::TestVoiceWorkflows::test_voice_email_workflow

# Run tests in verbose mode
pytest tests/e2e/ -v
```

## Test Reports

Test reports are generated in the `tests/e2e/reports` directory. Each report includes:

- Timestamp
- Exit code
- Test status (PASS/FAIL)
- Environment information

## Test Environment

The tests use the following environment variables:

- `MEMORY_SERVICE_TYPE=inmemory`
- `SESSION_SERVICE_TYPE=inmemory`
- `ADK_APP_NAME=oprina`
- `ENVIRONMENT=test`
- `DEBUG=true`

These variables are set automatically by the test runner script.

## Mocking Strategy

The tests use the following mocking strategy:

- **MCP Client**: Mocked to avoid actual network calls
- **Speech Recognition**: Mocked to simulate voice input
- **Email Service**: Mocked to avoid actual email sending
- **Calendar Service**: Mocked to avoid actual calendar operations
- **Content Service**: Mocked to avoid actual content generation

## Troubleshooting

If you encounter issues with the tests, check the following:

1. **Environment Variables**: Ensure all required environment variables are set
2. **Dependencies**: Ensure all dependencies are installed
3. **Mocking**: Ensure all required services are properly mocked
4. **Test Data**: Ensure all required test data is available

## Continuous Integration

These tests are designed to be run in a continuous integration environment. The following steps should be taken to integrate them into the CI pipeline:

1. Install dependencies
2. Set up the test environment
3. Run the tests
4. Report test results

## Test Plan

For a detailed test plan, see [TEST_PLAN.md](TEST_PLAN.md). 