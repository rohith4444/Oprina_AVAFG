# Oprina Backend Testing Suite

This directory contains the testing suite for the Oprina backend, a voice-powered Gmail and Calendar assistant.

## Directory Structure

```
tests/
├── __init__.py                 # Test suite information
├── conftest.py                 # Pytest configuration & fixtures
├── requirements-test.txt       # Testing dependencies
├── utils.py                    # Testing utilities
│
├── integration/                # Phase 1 (Backend Lead)
│   ├── __init__.py
│   ├── test_agent_integration.py
│   ├── test_adk_runner.py
│   └── test_session_state.py
│
├── api_services/               # Phase 2 (MCP Dev)
│   ├── __init__.py
│   ├── test_google_cloud.py
│   ├── test_database.py
│   └── test_mcp_compatibility.py
│
├── e2e/                        # Phase 3 (Backend Lead)
│   ├── __init__.py
│   ├── test_voice_workflows.py
│   ├── test_adk_web.py
│   └── test_complete_workflows.py
│
├── error_edge_cases/           # Phase 5 (Frontend Dev)
│   ├── __init__.py
│   ├── test_error_handling.py
│   └── test_edge_cases.py
│
└── performance/                # Phase 4 (Later - All team)
    ├── __init__.py
    ├── test_performance.py
    └── test_load.py
```

## Test Phases

1. **Phase 1: Integration Testing (Backend Lead)**
   - Tests the integration between different components of the backend
   - Focuses on agent interactions, memory management, and session state

2. **Phase 2: API & Service Integration (MCP Developer)**
   - Tests the integration with external API services
   - Focuses on Google Cloud, database, and MCP compatibility

3. **Phase 3: End-to-End Workflows (Backend Lead)**
   - Tests complete workflows from user input to system response
   - Focuses on voice workflows, ADK web integration, and complete user journeys

4. **Phase 4: Performance Testing (All - After Frontend)**
   - Tests the system's performance under load
   - Focuses on response times, resource usage, and scalability

5. **Phase 5: Error & Edge Cases (Frontend Developer)**
   - Tests the system's behavior in error conditions and edge cases
   - Focuses on robust error handling and graceful degradation

## Setup

1. Install testing dependencies:
   ```bash
   pip install -r tests/requirements-test.txt
   ```

2. Configure test environment:
   ```bash
   # Copy test environment
   cp tests/.env.test .env.test
   ```

3. Run test setup validation:
   ```bash
   # Test pytest configuration
   pytest tests/ --collect-only
   ```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Categories
```bash
# Run integration tests
pytest tests/integration/

# Run API service tests
pytest tests/api_services/

# Run end-to-end tests
pytest tests/e2e/

# Run error and edge case tests
pytest tests/error_edge_cases/

# Run performance tests
pytest tests/performance/
```

### Run Specific Test Files
```bash
# Run a specific test file
pytest tests/integration/test_agent_integration.py
```

### Run Specific Tests
```bash
# Run tests matching a specific name
pytest -k "test_voice_agent"
```

### Run Tests with Coverage
```bash
# Run tests with coverage report
pytest --cov=. tests/
```

## Adding New Tests

When adding new tests, follow these guidelines:

1. Place tests in the appropriate directory based on the test phase
2. Use the existing fixtures in `conftest.py` when possible
3. Follow the naming convention: `test_*.py` for test files and `test_*` for test functions
4. Use descriptive test names that explain what is being tested
5. Add appropriate docstrings to explain the purpose of each test

## Troubleshooting

If you encounter issues with the tests, try the following:

1. Ensure all dependencies are installed
2. Check that the test environment is properly configured
3. Verify that the test database is accessible
4. Check the logs for any error messages

For more help, contact the backend lead or refer to the project documentation. 