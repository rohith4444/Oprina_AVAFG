#!/usr/bin/env python3
"""
Oprina Foundation Testing Script

This script tests all the foundation components you've set up in Step 1.1:
- Configuration loading
- Environment variables
- Dependencies
- Upstash Redis connection
- Supabase connection
- Project structure validation

Run this to ensure everything is working before proceeding to Step 1.2.

Usage:
    python test_foundation.py
    python test_foundation.py --verbose
    python test_foundation.py --fix-issues
"""

import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any
import asyncio
sys.path.insert(0, str(Path(__file__).parent))  # Add project root to path
from services.logging.logger import setup_logger


class FoundationTester:
    """Test all foundation components."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_results: Dict[str, Tuple[bool, str]] = {}
        self.project_root = Path(__file__).parent
        self.logger = setup_logger("foundation_test", console_output=True)
        self.logger.info("Foundation tester initialized")
        
    def log(self, message: str, level: str = "INFO"):
        """Log message using the logging server."""
        # Use text symbols instead of emojis for Windows compatibility
        if level == "SUCCESS":
            self.logger.info(f"[PASS] {message}")
        elif level == "ERROR":
            self.logger.error(f"[FAIL] {message}")
        else:
            self.logger.info(f"[INFO] {message}")
        
    def record_test(self, test_name: str, success: bool, message: str):
        """Record test result."""
        self.test_results[test_name] = (success, message)
        level = "SUCCESS" if success else "ERROR"
        self.log(f"{test_name}: {message}", level)
    
    def test_python_version(self) -> bool:
        """Test Python version compatibility."""
        try:
            if sys.version_info < (3, 9):
                self.record_test("Python Version", False, 
                    f"Python 3.9+ required, found {sys.version_info.major}.{sys.version_info.minor}")
                return False
            
            self.record_test("Python Version", True, 
                f"Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
            return True
        except Exception as e:
            self.record_test("Python Version", False, f"Error checking Python version: {e}")
            return False
    
    def test_project_structure(self) -> bool:
        """Test project structure is correct."""
        try:
            required_files = [
                ".env.example",
                "requirements.txt", 
                "config/settings.py",
                "memory/__init__.py",
                "agents/__init__.py"
            ]
            
            required_dirs = [
                "config",
                "memory", 
                "agents",
                "agents/voice",
                "agents/voice/sub_agents"
            ]
            
            missing_files = []
            missing_dirs = []
            
            for file_path in required_files:
                if not (self.project_root / file_path).exists():
                    missing_files.append(file_path)
            
            for dir_path in required_dirs:
                if not (self.project_root / dir_path).is_dir():
                    missing_dirs.append(dir_path)
            
            if missing_files or missing_dirs:
                issues = []
                if missing_files:
                    issues.append(f"Missing files: {', '.join(missing_files)}")
                if missing_dirs:
                    issues.append(f"Missing directories: {', '.join(missing_dirs)}")
                
                self.record_test("Project Structure", False, "; ".join(issues))
                return False
            
            self.record_test("Project Structure", True, "All required files and directories present")
            return True
            
        except Exception as e:
            self.record_test("Project Structure", False, f"Error checking structure: {e}")
            return False
    
    def test_environment_file(self) -> bool:
        """Test .env file exists and has required variables."""
        try:
            env_file = self.project_root / ".env"
            
            if not env_file.exists():
                self.record_test("Environment File", False, 
                    ".env file not found. Copy from .env.example and fill in values")
                return False
            
            # Check for required variables
            required_vars = [
                "SUPABASE_URL",
                "SUPABASE_ANON_KEY", 
                "GOOGLE_API_KEY",
                "UPSTASH_REDIS_REST_URL",
                "UPSTASH_REDIS_REST_TOKEN"
            ]
            
            env_content = env_file.read_text()
            missing_vars = []
            
            for var in required_vars:
                if var not in env_content or f"{var}=" not in env_content:
                    missing_vars.append(var)
            
            if missing_vars:
                self.record_test("Environment File", False,
                    f"Missing environment variables: {', '.join(missing_vars)}")
                return False
            
            self.record_test("Environment File", True, "All required environment variables present")
            return True
            
        except Exception as e:
            self.record_test("Environment File", False, f"Error checking .env file: {e}")
            return False
    
    def test_dependencies(self) -> bool:
        """Test that required dependencies are installed."""
        try:
            required_packages = [
                ("google-adk", "google.adk"),
                ("supabase", "supabase"),
                ("redis", "redis"),
                ("pydantic", "pydantic"),
                ("python-dotenv", "dotenv"),
                ("upstash-redis", "upstash_redis")
            ]
            
            missing_packages = []
            
            for package_name, import_name in required_packages:
                try:
                    __import__(import_name)
                    self.log(f"✓ {package_name} installed", "SUCCESS")
                except ImportError:
                    missing_packages.append(package_name)
                    self.log(f"✗ {package_name} missing", "ERROR")
            
            if missing_packages:
                self.record_test("Dependencies", False,
                    f"Missing packages: {', '.join(missing_packages)}. Run: pip install {' '.join(missing_packages)}")
                return False
            
            self.record_test("Dependencies", True, "All required dependencies installed")
            return True
            
        except Exception as e:
            self.record_test("Dependencies", False, f"Error checking dependencies: {e}")
            return False
    
    def test_configuration_loading(self) -> bool:
        """Test configuration loading."""
        try:
            # Add project root to path
            sys.path.insert(0, str(self.project_root))
            
            from config.settings import settings, print_configuration
            
            # Test that settings load without errors
            test_vars = [
                settings.SUPABASE_URL,
                settings.GOOGLE_API_KEY,
                settings.ADK_MODEL,
                settings.REDIS_PROVIDER
            ]
            
            if self.verbose:
                print("\n" + "="*50)
                print_configuration()
                print("="*50 + "\n")
            
            self.record_test("Configuration Loading", True, "Settings loaded successfully")
            return True
            
        except Exception as e:
            self.record_test("Configuration Loading", False, f"Configuration loading failed: {e}")
            if self.verbose:
                traceback.print_exc()
            return False
    
    async def test_upstash_redis(self) -> bool:
        """Test Upstash Redis connection."""
        try:
            self.logger.info("Starting Upstash Redis connection test")
            sys.path.insert(0, str(self.project_root))
            from config.settings import get_redis_client, test_redis_connection
            
            # Test connection
            connected = test_redis_connection()
            
            if not connected:
                self.record_test("Upstash Redis", False, 
                    "Cannot connect to Upstash Redis. Check your credentials and network")
                return False
            
            # Test basic operations
            client = get_redis_client()
            
            # Test set/get
            test_key = "oprina:test:foundation"
            test_value = "foundation_test_successful"
            
            if hasattr(client, 'set'):  # Regular Redis client
                client.set(test_key, test_value, ex=60)  # 60 second expiry
                retrieved = client.get(test_key)
            else:  # Upstash REST client
                client.set(test_key, test_value)
                retrieved = client.get(test_key)
            
            if retrieved != test_value:
                self.record_test("Upstash Redis", False, 
                    f"Redis set/get test failed. Set: {test_value}, Got: {retrieved}")
                return False
            
            # Clean up
            if hasattr(client, 'delete'):
                client.delete(test_key)
            else:
                client.delete([test_key])
            
            self.record_test("Upstash Redis", True, 
                "Connected successfully and basic operations work")
            self.logger.info(f"Redis test key set/get successful: {test_value}")
            return True
            
        except Exception as e:
            self.record_test("Upstash Redis", False, f"Redis test failed: {e}")
            if self.verbose:
                traceback.print_exc()
            return False
    
    async def test_supabase_connection(self) -> bool:
        """Test Supabase connection."""
        try:
            self.logger.info("Starting Supabase connection test")
            sys.path.insert(0, str(self.project_root))
            from config.settings import settings
            
            # Test Supabase client creation
            from supabase import create_client
            
            supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            
            # Test a simple query (this might fail if no tables exist, which is OK)
            try:
                # Try to query auth users (should work with anon key)
                result = supabase.auth.get_session()
                self.log("Supabase auth service accessible", "SUCCESS")
            except Exception as auth_e:
                self.log(f"Supabase auth test: {auth_e}", "INFO")
            
            self.record_test("Supabase Connection", True, 
                "Supabase client created successfully")
            self.logger.info(f"Supabase connected to: {settings.SUPABASE_URL}")
            return True
            
        except Exception as e:
            self.record_test("Supabase Connection", False, f"Supabase connection failed: {e}")
            if self.verbose:
                traceback.print_exc()
            return False
    
    def test_memory_package(self) -> bool:
        """Test memory package can be imported."""
        try:
            sys.path.insert(0, str(self.project_root))
            
            # Test memory package import
            import memory
            
            # Test that expected components exist
            expected_components = [
                'MemoryManager',
                'SessionMemoryService', 
                'ChatHistoryService',
                'LongTermMemoryService',
                'RedisCacheService'
            ]
            
            missing_components = []
            for component in expected_components:
                if not hasattr(memory, component):
                    missing_components.append(component)
            
            if missing_components:
                self.record_test("Memory Package", False,
                    f"Missing components: {', '.join(missing_components)}")
                return False
            
            self.record_test("Memory Package", True, "Memory package imports successfully")
            return True
            
        except Exception as e:
            self.record_test("Memory Package", False, f"Memory package import failed: {e}")
            if self.verbose:
                traceback.print_exc()
            return False
    
    def test_agents_package(self) -> bool:
        """Test agents package structure."""
        try:
            sys.path.insert(0, str(self.project_root))
            
            # Test agents package import
            import agents
            
            # Test voice agent import
            import agents.voice
            
            self.record_test("Agents Package", True, "Agents package structure is correct")
            return True
            
        except Exception as e:
            self.record_test("Agents Package", False, f"Agents package import failed: {e}")
            if self.verbose:
                traceback.print_exc()
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all foundation tests."""
        print("🧪 Starting Oprina Foundation Tests...\n")
        self.logger.info("="*60)
        self.logger.info("🧪 Starting Oprina Foundation Tests")
        self.logger.info("="*60)
        
        # Synchronous tests
        sync_tests = [
            self.test_python_version,
            self.test_project_structure,
            self.test_environment_file,
            self.test_dependencies,
            self.test_configuration_loading,
            self.test_memory_package,
            self.test_agents_package
        ]
        
        for test_func in sync_tests:
            test_func()
        
        # Asynchronous tests
        await self.test_upstash_redis()
        await self.test_supabase_connection()
        
        # Summary
        self.print_summary()
        self.logger.info("Foundation tests completed")
        # Return overall success
        return all(success for success, _ in self.test_results.values())
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("🧪 FOUNDATION TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for success, _ in self.test_results.values() if success)
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print()
        
        # Show failed tests
        failed_tests = [(name, msg) for name, (success, msg) in self.test_results.items() if not success]
        
        if failed_tests:
            print("❌ FAILED TESTS:")
            for name, message in failed_tests:
                print(f"   • {name}: {message}")
            print()
        
        # Show passed tests
        if self.verbose:
            passed_tests = [(name, msg) for name, (success, msg) in self.test_results.items() if success]
            if passed_tests:
                print("✅ PASSED TESTS:")
                for name, message in passed_tests:
                    print(f"   • {name}: {message}")
                print()
        
        # Next steps
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Foundation is ready. You can proceed to Step 1.2: Memory Foundation")
            print()
            print("Next steps:")
            print("1. Implement memory/redis_cache.py")
            print("2. Implement memory/session_memory.py") 
            print("3. Implement memory/chat_history.py")
            print("4. Implement memory/long_term_memory.py")
            print("5. Implement memory/memory_manager.py")
        else:
            print("⚠️  Some tests failed. Fix the issues above before proceeding.")
            print()
            print("Common fixes:")
            print("1. Copy .env.example to .env and fill in your credentials")
            print("2. Install missing dependencies: pip install -r requirements.txt")
            print("3. Check your Upstash Redis and Supabase credentials")
        
        print("="*60)


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Oprina foundation components")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fix-issues", action="store_true", help="Try to fix common issues")
    
    args = parser.parse_args()
    
    tester = FoundationTester(verbose=args.verbose)
    
    async def run_tests():
        success = await tester.run_all_tests()
        return 0 if success else 1
    
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()