@echo off
echo Running Oprina End-to-End Tests
echo ==============================

REM Set environment variables
set MEMORY_SERVICE_TYPE=inmemory
set SESSION_SERVICE_TYPE=inmemory
set ADK_APP_NAME=oprina
set ENVIRONMENT=test
set DEBUG=true

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH.
    exit /b 1
)

REM Check if pytest is installed
python -c "import pytest" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing pytest...
    pip install pytest pytest-asyncio
)

REM Run the tests
echo Running tests...
python tests/e2e/run_tests.py %*

REM Check the exit code
if %ERRORLEVEL% neq 0 (
    echo Tests failed with exit code %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
) else (
    echo All tests passed!
    exit /b 0
) 