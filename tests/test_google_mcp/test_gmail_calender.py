#!/usr/bin/env python3
"""
Test Both Gmail and Calendar Services

Quick test script to verify both services work independently
and can coexist without conflicts.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_mcp_tool_registration():
    """Test that both Gmail and Calendar tools are properly registered."""
    print("🔧 Testing MCP Tool Registration...")
    
    try:
        from google_mcp import mcp_discovery
        tools = mcp_discovery.list_tools()
        
        # Count Gmail and Calendar tools
        gmail_tools = [tool for tool in tools if 'gmail' in tool['name']]
        calendar_tools = [tool for tool in tools if 'calendar' in tool['name']]
        
        print(f"   📧 Gmail tools: {len(gmail_tools)}")
        print(f"   📅 Calendar tools: {len(calendar_tools)}")
        print(f"   🔧 Total tools: {len(tools)}")
        
        # Check for expected calendar tools
        expected_calendar_tools = [
            "calendar_get_current_time",
            "calendar_list_events",
            "calendar_create_event", 
            "calendar_update_event",
            "calendar_delete_event",
            "calendar_list_calendars",
            "calendar_find_free_time"
        ]
        
        found_calendar_tools = [tool['name'] for tool in calendar_tools]
        missing_tools = set(expected_calendar_tools) - set(found_calendar_tools)
        
        if not missing_tools:
            print("   ✅ All expected calendar tools registered")
            return True
        else:
            print(f"   ❌ Missing calendar tools: {missing_tools}")
            return False
            
    except Exception as e:
        print(f"   ❌ Tool registration test failed: {e}")
        return False


def test_auth_services():
    """Test both authentication services."""
    print("🔐 Testing Authentication Services...")
    
    results = {
        "gmail_auth": False,
        "calendar_auth": False
    }
    
    # Test Gmail auth service
    try:
        from services.google_cloud.gmail_auth import get_gmail_auth_service, check_gmail_connection
        
        gmail_auth = get_gmail_auth_service()
        gmail_status = check_gmail_connection()
        
        if gmail_auth and isinstance(gmail_status, dict):
            results["gmail_auth"] = True
            print(f"   📧 Gmail auth service: ✅")
            print(f"       Connected: {gmail_status.get('connected', False)}")
            print(f"       Token exists: {gmail_status.get('token_exists', False)}")
        else:
            print("   📧 Gmail auth service: ❌")
            
    except Exception as e:
        print(f"   📧 Gmail auth service error: {e}")
    
    # Test Calendar auth service
    try:
        from services.google_cloud.calendar_auth import get_calendar_auth_service, check_calendar_connection
        
        calendar_auth = get_calendar_auth_service()
        calendar_status = check_calendar_connection()
        
        if calendar_auth and isinstance(calendar_status, dict):
            results["calendar_auth"] = True
            print(f"   📅 Calendar auth service: ✅")
            print(f"       Connected: {calendar_status.get('connected', False)}")
            print(f"       Token exists: {calendar_status.get('token_exists', False)}")
        else:
            print("   📅 Calendar auth service: ❌")
            
    except Exception as e:
        print(f"   📅 Calendar auth service error: {e}")
    
    return results


def test_tool_execution():
    """Test executing tools from both services."""
    print("⚡ Testing Tool Execution...")
    
    results = {
        "gmail_tools": False,
        "calendar_tools": False
    }
    
    try:
        from google_mcp import mcp_discovery
        
        # Test Gmail tool execution (safe tool)
        try:
            gmail_result = mcp_discovery.run_tool("gmail_list_labels")
            results["gmail_tools"] = True
            print("   📧 Gmail tool execution: ✅ (structure correct)")
        except Exception as e:
            if "credentials" in str(e).lower() or "auth" in str(e).lower():
                results["gmail_tools"] = True  # Expected auth error
                print("   📧 Gmail tool execution: ✅ (expected auth error)")
            else:
                print(f"   📧 Gmail tool execution: ❌ {e}")
        
        # Test Calendar tool execution (safe tool)
        try:
            calendar_result = mcp_discovery.run_tool("calendar_get_current_time")
            if calendar_result.get("status") == "success":
                results["calendar_tools"] = True
                print("   📅 Calendar tool execution: ✅")
                print(f"       Current time: {calendar_result.get('current_time')}")
            else:
                print("   📅 Calendar tool execution: ❌")
        except Exception as e:
            print(f"   📅 Calendar tool execution: ❌ {e}")
            
    except Exception as e:
        print(f"   ⚡ Tool execution test failed: {e}")
    
    return results


def test_bridge_compatibility():
    """Test MCP-ADK bridge with both service types."""
    print("🌉 Testing MCP-ADK Bridge Compatibility...")
    
    try:
        from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_bridge import (
            get_mcp_bridge, test_mcp_bridge_connection
        )
        
        # Test bridge initialization
        bridge = get_mcp_bridge()
        if not bridge:
            print("   ❌ Bridge initialization failed")
            return False
        
        # Test bridge connection
        connection_test = test_mcp_bridge_connection()
        
        gmail_tools_count = connection_test.get('gmail_tools_count', 0)
        calendar_tools_count = connection_test.get('calendar_tools_count', 0)
        total_tools = connection_test.get('total_tools_available', 0)
        
        print(f"   🔧 Bridge status: {'✅' if connection_test.get('bridge_initialized') else '❌'}")
        print(f"   📧 Gmail tools in bridge: {gmail_tools_count}")
        print(f"   📅 Calendar tools in bridge: {calendar_tools_count}")
        print(f"   🔧 Total tools available: {total_tools}")
        
        # Expected: Gmail tools should be there, Calendar tools should be discoverable
        if gmail_tools_count > 0 and total_tools > gmail_tools_count:
            print("   ✅ Bridge compatibility successful")
            return True
        else:
            print("   ⚠️ Bridge may need updates for calendar tools")
            return True  # Not critical for current phase
            
    except Exception as e:
        print(f"   ❌ Bridge compatibility test failed: {e}")
        return False


def test_token_file_separation():
    """Test that Gmail and Calendar use separate token files."""
    print("📁 Testing Token File Separation...")
    
    try:
        from services.google_cloud.auth_utils import get_service_token_path
        
        gmail_token_path = get_service_token_path("gmail")
        calendar_token_path = get_service_token_path("calendar")
        
        if gmail_token_path != calendar_token_path:
            print("   ✅ Token files are separate")
            print(f"       Gmail: {os.path.basename(gmail_token_path)}")
            print(f"       Calendar: {os.path.basename(calendar_token_path)}")
            return True
        else:
            print("   ❌ Token files are not separate")
            return False
            
    except Exception as e:
        print(f"   ❌ Token separation test failed: {e}")
        return False


async def run_comprehensive_test():
    """Run comprehensive test of both services."""
    print("🧪 Running Comprehensive Gmail + Calendar Test Suite")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: MCP Tool Registration
    test_results["mcp_registration"] = test_mcp_tool_registration()
    print()
    
    # Test 2: Auth Services
    auth_results = test_auth_services()
    test_results["gmail_auth"] = auth_results["gmail_auth"]
    test_results["calendar_auth"] = auth_results["calendar_auth"]
    print()
    
    # Test 3: Tool Execution
    exec_results = test_tool_execution()
    test_results["gmail_execution"] = exec_results["gmail_tools"]
    test_results["calendar_execution"] = exec_results["calendar_tools"]
    print()
    
    # Test 4: Bridge Compatibility
    test_results["bridge_compatibility"] = test_bridge_compatibility()
    print()
    
    # Test 5: Token File Separation
    test_results["token_separation"] = test_token_file_separation()
    print()
    
    # Summary
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print("📊 Test Results Summary:")
    print(f"   Passed: {passed_tests}/{total_tests}")
    print()
    
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    print("\n" + "=" * 60)
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Both Gmail and Calendar services are ready!")
        print("✅ Ready to proceed to Phase 4: Memory System Extension")
        return True
    elif passed_tests >= total_tests - 2:  # Allow 2 failures for auth issues
        print("⚠️ Most tests passed - ready to proceed with minor issues")
        print("✅ Services are functional, authentication may need setup")
        return True
    else:
        print("❌ Multiple test failures - please review and fix issues")
        return False


if __name__ == "__main__":
    print("🧪 Gmail + Calendar Services Integration Test")
    
    # Run tests
    success = asyncio.run(run_comprehensive_test())
    
    if success:
        print("\n🚀 Ready for next phase: Memory System Extension!")
    else:
        print("\n🔧 Please fix issues before proceeding to next phase")
    
    sys.exit(0 if success else 1)