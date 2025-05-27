# tests/test_google_mcp/test_mcp_bridge.py
"""
Test suite for MCP-ADK Bridge functionality.

Tests the bridge that converts Calvin's MCP tools into ADK FunctionTools
for use by agents.
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestMCPBridge(unittest.TestCase):
    """Test cases for MCP-ADK Bridge functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = project_root
    
    def test_bridge_import(self):
        """Test that MCP bridge can be imported successfully."""
        print("🌉 Testing MCP bridge import...")
        
        try:
            from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_bridge import (
                MCPADKBridge, get_mcp_bridge, get_gmail_tools_for_agent
            )
            print("   ✅ MCP bridge modules imported successfully")
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import MCP bridge: {e}")
    
    def test_bridge_initialization(self):
        """Test bridge initialization."""
        print("🔧 Testing bridge initialization...")
        
        from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_bridge import get_mcp_bridge
        
        bridge = get_mcp_bridge()
        self.assertIsNotNone(bridge)
        self.assertTrue(hasattr(bridge, 'get_gmail_tools'))
        self.assertTrue(hasattr(bridge, 'get_all_tools'))
        
        print("   ✅ Bridge initialized successfully")
    
    def test_tool_conversion(self):
        """Test conversion of MCP tools to ADK FunctionTools."""
        print("🔄 Testing tool conversion...")
        
        from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_bridge import get_mcp_bridge
        
        bridge = get_mcp_bridge()
        
        # Test getting all tools
        all_tools = bridge.get_all_tools()
        self.assertIsInstance(all_tools, list)
        print(f"   ✅ Converted {len(all_tools)} total tools")
        
        # Test getting Gmail tools specifically
        gmail_tools = bridge.get_gmail_tools()
        self.assertIsInstance(gmail_tools, list)
        print(f"   ✅ Converted {len(gmail_tools)} Gmail tools")
        
        # Verify tools are ADK FunctionTools
        if gmail_tools:
            from google.adk.tools import FunctionTool
            first_tool = gmail_tools[0]
            self.assertIsInstance(first_tool, FunctionTool)
            self.assertTrue(hasattr(first_tool, 'func'))
            print("   ✅ Tools are valid ADK FunctionTools")
    
    def test_convenience_functions(self):
        """Test convenience functions for agent use."""
        print("🎯 Testing convenience functions...")
        
        from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_bridge import (
            get_gmail_tools_for_agent, test_mcp_bridge_connection
        )
        
        # Test Gmail tools function
        gmail_tools = get_gmail_tools_for_agent()
        self.assertIsInstance(gmail_tools, list)
        print(f"   ✅ get_gmail_tools_for_agent returned {len(gmail_tools)} tools")
        
        # Test connection test function
        connection_test = test_mcp_bridge_connection()
        self.assertIsInstance(connection_test, dict)
        self.assertIn('bridge_initialized', connection_test)
        self.assertIn('total_tools_available', connection_test)
        
        print("   ✅ Connection test completed")
        print(f"       Bridge initialized: {connection_test['bridge_initialized']}")
        print(f"       Total tools: {connection_test['total_tools_available']}")
        print(f"       Gmail tools: {connection_test['gmail_tools_count']}")
    
    def test_tool_metadata(self):
        """Test that converted tools have proper metadata."""
        print("📋 Testing tool metadata...")
        
        from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_bridge import get_mcp_bridge
        
        bridge = get_mcp_bridge()
        gmail_tools = bridge.get_gmail_tools()
        
        if gmail_tools:
            # Test first Gmail tool metadata
            first_tool = gmail_tools[0]
            
            # Check function has name
            self.assertTrue(hasattr(first_tool.func, '__name__'))
            tool_name = first_tool.func.__name__
            self.assertIsInstance(tool_name, str)
            self.assertTrue(len(tool_name) > 0)
            
            # Check function has docstring
            self.assertTrue(hasattr(first_tool.func, '__doc__'))
            
            print(f"   ✅ Tool metadata verified for: {tool_name}")
            
            # Test tool info retrieval
            tool_info = bridge.get_tool_info(tool_name)
            self.assertIsInstance(tool_info, dict)
            self.assertIn('tool_info', tool_info)
            
            print("   ✅ Tool info retrieval working")
    
    def test_error_handling(self):
        """Test error handling in tool execution."""
        print("⚠️  Testing error handling...")
        
        from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_bridge import get_mcp_bridge
        
        bridge = get_mcp_bridge()
        
        # Test with invalid tool name
        tool_info = bridge.get_tool_info("nonexistent_tool")
        self.assertIsInstance(tool_info, dict)
        self.assertEqual(tool_info['tool_info'], {})
        
        print("   ✅ Error handling for invalid tools working")
        
        # Test tool execution with invalid parameters (if Gmail tools available)
        gmail_tools = bridge.get_gmail_tools()
        if gmail_tools:
            first_tool = gmail_tools[0]
            try:
                # This should fail gracefully due to authentication
                result = first_tool.func(invalid_param="test")
                self.assertIsInstance(result, dict)
                # Should return error result format
                if not result.get('success', True):
                    self.assertIn('error', result)
                    print("   ✅ Tool execution error handling working")
                else:
                    print("   ⚠️  Tool execution succeeded unexpectedly")
            except Exception:
                print("   ✅ Tool execution raises exceptions as expected")
    
    def test_bridge_singleton(self):
        """Test that bridge uses singleton pattern correctly."""
        print("🔄 Testing singleton pattern...")
        
        from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_bridge import get_mcp_bridge
        
        bridge1 = get_mcp_bridge()
        bridge2 = get_mcp_bridge()
        
        # Should be the same instance
        self.assertIs(bridge1, bridge2)
        print("   ✅ Singleton pattern working correctly")


def run_bridge_tests():
    """Run the MCP bridge test suite."""
    print("🌉 Running MCP-ADK Bridge Test Suite...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMCPBridge)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 50)
    if result.wasSuccessful():
        print("🎉 All MCP bridge tests passed!")
        return True
    else:
        print("❌ Some MCP bridge tests failed!")
        return False


if __name__ == "__main__":
    success = run_bridge_tests()
    sys.exit(0 if success else 1)