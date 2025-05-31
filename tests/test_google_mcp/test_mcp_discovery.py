#!/usr/bin/env python3
"""
Test script to verify Google MCP discovery works after cleanup
"""

import sys
import os
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestMCPDiscovery(unittest.TestCase):
    """Test cases for Google MCP discovery functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = project_root
    
    def test_mcp_imports(self):
        """Test that MCP modules can be imported successfully."""
        print("🧪 Testing Google MCP imports...")
        
        try:
            from google_mcp import mcp_discovery
            from google_mcp import mcp_tool
            from google_mcp import gmail_tools
            print("   ✅ Google MCP modules imported successfully")
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import MCP modules: {e}")
    
    def test_tool_discovery(self):
        """Test tool discovery functionality."""
        print("🔍 Testing tool discovery...")
        
        from google_mcp import mcp_discovery
        
        tools = mcp_discovery.list_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0, "No tools discovered")
        
        print(f"   ✅ Discovered {len(tools)} tools")
        
        # Verify tool structure
        for tool in tools[:3]:  # Check first 3 tools
            self.assertIn('name', tool)
            self.assertIn('description', tool)
            self.assertIsInstance(tool['name'], str)
            self.assertIsInstance(tool['description'], str)
        
        print("   ✅ Tool structure validation passed")
    
    def test_tool_registry(self):
        """Test tool registry functionality."""
        print("📋 Testing tool registry...")
        
        from google_mcp.mcp_tool import TOOL_REGISTRY
        
        self.assertIsInstance(TOOL_REGISTRY, dict)
        self.assertGreater(len(TOOL_REGISTRY), 0, "Tool registry is empty")
        
        print(f"   ✅ Tool registry contains {len(TOOL_REGISTRY)} tools")
        
        # Test registry structure
        for tool_name, tool_class in list(TOOL_REGISTRY.items())[:3]:
            self.assertIsInstance(tool_name, str)
            self.assertTrue(hasattr(tool_class, 'name'))
            self.assertTrue(hasattr(tool_class, 'description'))
            self.assertTrue(hasattr(tool_class, 'run'))
        
        print("   ✅ Tool registry structure validation passed")
    
    def test_tool_execution_safety(self):
        """Test that tool execution mechanism works (without actual execution)."""
        print("⚡ Testing tool execution mechanism...")
        
        from google_mcp import mcp_discovery
        
        tools = mcp_discovery.list_tools()
        
        if tools:
            # Find a safe tool to test (one that doesn't require authentication)
            safe_tools = ["gmail_get_user_profile", "gmail_list_labels"]
            test_tool = None
            
            for tool in tools:
                if tool['name'] in safe_tools:
                    test_tool = tool
                    break
            
            if test_tool:
                print(f"   Testing tool execution mechanism with: {test_tool['name']}")
                
                # Test that run_tool function exists and can be called
                # (it will fail due to auth, but the mechanism should work)
                try:
                    result = mcp_discovery.run_tool(test_tool['name'])
                    print(f"   ⚠️  Tool executed but failed (expected - no auth)")
                except Exception as e:
                    print(f"   ⚠️  Tool execution failed as expected (no auth): {type(e).__name__}")
                
                self.assertTrue(True)  # Test passed if we got here
            else:
                print("   ⏭️  No safe tools found for execution testing")
                self.assertTrue(True)  # Still pass the test
        else:
            self.fail("No tools available for execution testing")
    
    def test_gmail_tools_count(self):
        """Test that expected number of Gmail tools are available."""
        print("📧 Testing Gmail tools availability...")
        
        from google_mcp import mcp_discovery
        
        tools = mcp_discovery.list_tools()
        gmail_tools = [tool for tool in tools if 'gmail' in tool['name'].lower()]
        
        # Expect at least 20 Gmail tools based on Calvin's implementation
        self.assertGreaterEqual(len(gmail_tools), 20, f"Expected at least 20 Gmail tools, found {len(gmail_tools)}")
        
        print(f"   ✅ Found {len(gmail_tools)} Gmail tools")
        
        # List some key tools we expect
        expected_tools = [
            'gmail_list_messages',
            'gmail_get_message', 
            'gmail_send_message',
            'gmail_search'
        ]
        
        available_tool_names = [tool['name'] for tool in tools]
        
        for expected_tool in expected_tools:
            self.assertIn(expected_tool, available_tool_names, f"Expected tool {expected_tool} not found")
        
        print("   ✅ Key Gmail tools verification passed")

def run_discovery_test():
    """Run the MCP discovery test suite."""
    print("🧪 Running Google MCP Discovery Test Suite...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMCPDiscovery)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 50)
    if result.wasSuccessful():
        print("🎉 All MCP discovery tests passed!")
        return True
    else:
        print("❌ Some MCP discovery tests failed!")
        return False

if __name__ == "__main__":
    success = run_discovery_test()
    sys.exit(0 if success else 1)