#!/usr/bin/env python3
"""
Script to run end-to-end tests for the Oprina application.

This script sets up the test environment, runs the tests, and reports the results.
"""
import os
import sys
import argparse
import subprocess
import time
from datetime import datetime

def setup_environment():
    """Set up the test environment."""
    print("Setting up test environment...")
    
    # Set environment variables
    os.environ["MEMORY_SERVICE_TYPE"] = "inmemory"
    os.environ["SESSION_SERVICE_TYPE"] = "inmemory"
    os.environ["ADK_APP_NAME"] = "oprina"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG"] = "true"
    
    # Check if Google Cloud credentials are set
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("Warning: GOOGLE_APPLICATION_CREDENTIALS not set. Tests using Vertex AI may fail.")
    
    print("Test environment setup complete.")

def run_tests(test_files=None, test_cases=None, verbose=False):
    """Run the tests."""
    print("Running tests...")
    
    # Build the pytest command
    cmd = ["pytest"]
    
    if test_files:
        cmd.extend(test_files)
    else:
        cmd.append("tests/e2e/")
    
    if test_cases:
        cmd.extend(test_cases)
    
    if verbose:
        cmd.append("-v")
    
    # Add additional options
    cmd.extend(["--tb=short", "--capture=no"])
    
    # Run the tests
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    # Print the output
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    # Print the summary
    print(f"\nTests completed in {end_time - start_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    
    return result.returncode

def generate_report(exit_code):
    """Generate a test report."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"tests/e2e/reports/test_report_{timestamp}.txt"
    
    # Create the reports directory if it doesn't exist
    os.makedirs("tests/e2e/reports", exist_ok=True)
    
    # Write the report
    with open(report_file, "w") as f:
        f.write(f"Test Report - {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Exit code: {exit_code}\n")
        f.write(f"Status: {'PASS' if exit_code == 0 else 'FAIL'}\n\n")
        f.write("Environment:\n")
        f.write(f"  MEMORY_SERVICE_TYPE: {os.environ.get('MEMORY_SERVICE_TYPE')}\n")
        f.write(f"  SESSION_SERVICE_TYPE: {os.environ.get('SESSION_SERVICE_TYPE')}\n")
        f.write(f"  ADK_APP_NAME: {os.environ.get('ADK_APP_NAME')}\n")
        f.write(f"  ENVIRONMENT: {os.environ.get('ENVIRONMENT')}\n")
        f.write(f"  DEBUG: {os.environ.get('DEBUG')}\n")
        f.write(f"  GOOGLE_APPLICATION_CREDENTIALS: {'Set' if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') else 'Not set'}\n")
    
    print(f"Test report generated: {report_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run end-to-end tests for the Oprina application.")
    parser.add_argument("--files", nargs="+", help="Specific test files to run")
    parser.add_argument("--cases", nargs="+", help="Specific test cases to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run tests in verbose mode")
    args = parser.parse_args()
    
    # Set up the environment
    setup_environment()
    
    # Run the tests
    exit_code = run_tests(args.files, args.cases, args.verbose)
    
    # Generate the report
    generate_report(exit_code)
    
    # Return the exit code
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 