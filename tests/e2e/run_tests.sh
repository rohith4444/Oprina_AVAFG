#!/bin/bash

echo "Running Oprina End-to-End Tests"
echo "=============================="

# Set environment variables
export MEMORY_SERVICE_TYPE=inmemory
export SESSION_SERVICE_TYPE=inmemory
export ADK_APP_NAME=oprina
export ENVIRONMENT=test
export DEBUG=true

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH."
    exit 1
fi

# Check if pytest is installed
if ! python3 -c "import pytest" &> /dev/null; then
    echo "Installing pytest..."
    pip3 install pytest pytest-asyncio
fi

# Run the tests
echo "Running tests..."
python3 tests/e2e/run_tests.py "$@"

# Check the exit code
if [ $? -ne 0 ]; then
    echo "Tests failed with exit code $?."
    exit $?
else
    echo "All tests passed!"
    exit 0
fi 