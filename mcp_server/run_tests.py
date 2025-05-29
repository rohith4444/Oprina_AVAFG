#!/usr/bin/env python3
"""
Script to run the Oprina MCP server tests.
"""

import os
import sys
import unittest
import logging
from dotenv import load_dotenv
from mcp_server.auth_manager import AuthManager
from mcp_server.tools.gmail_tool import GmailTool
from mcp_server.tools.calendar_tool import CalendarTool

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    try:
        logger.info("Running Oprina MCP server tests...")
        # Discover and run tests
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover('tests', pattern='test_*.py')
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        
        # Exit with non-zero code if tests failed
        sys.exit(not result.wasSuccessful())
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        sys.exit(1) 