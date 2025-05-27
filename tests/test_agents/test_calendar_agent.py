# test_calendar_agent.py
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.voice.sub_agents.coordinator.sub_agents.calendar.agent import create_calendar_agent

async def test_enhanced_features():
    print("🧪 Testing Enhanced Calendar Agent Features...")
    
    agent, exit_stack = await create_calendar_agent()
    
    # FIXED: Handle both FunctionTool objects and direct functions
    agent_tool_names = []
    for tool in agent.tools:
        if hasattr(tool, 'func') and hasattr(tool.func, '__name__'):
            # This is a FunctionTool object
            agent_tool_names.append(tool.func.__name__)
        elif hasattr(tool, '__name__'):
            # This is a direct function
            agent_tool_names.append(tool.__name__)
        else:
            # Fallback for other tool types
            agent_tool_names.append(str(type(tool).__name__))
    
    # Check for agent-specific tools
    expected_agent_tools = [
        'check_calendar_availability',
        'manage_calendar_event', 
        'find_optimal_meeting_time',
        'analyze_schedule_patterns'
    ]
    
    print("🎯 Agent-Specific Tools Status:")
    for tool in expected_agent_tools:
        status = "✅" if tool in agent_tool_names else "❌"
        print(f"  {status} {tool}")
    
    # Check for Calendar MCP tools
    expected_mcp_tools = [
        'calendar_list_events',
        'calendar_create_event',
        'calendar_find_free_time',
        'calendar_get_current_time',
        'calendar_update_event',
        'calendar_delete_event',
        'calendar_list_calendars'
    ]
    
    print("\n📅 Calendar MCP Tools Status:")
    for tool in expected_mcp_tools:
        status = "✅" if tool in agent_tool_names else "❌"
        print(f"  {status} {tool}")
    
    # Check for shared tools
    expected_shared_tools = [
        'update_calendar_context',
        'get_calendar_context',
        'log_agent_action',
        'handle_agent_error',
        'update_session_state',
        'learn_from_interaction'
    ]
    
    print("\n🔧 Shared Tools Status:")
    for tool in expected_shared_tools:
        status = "✅" if tool in agent_tool_names else "❌"
        print(f"  {status} {tool}")
    
    print(f"\n📊 Tool Summary:")
    print(f"  Total Tools: {len(agent.tools)}")
    print(f"  Agent Tools Found: {sum(1 for tool in expected_agent_tools if tool in agent_tool_names)}/{len(expected_agent_tools)}")
    print(f"  MCP Tools Found: {sum(1 for tool in expected_mcp_tools if tool in agent_tool_names)}/{len(expected_mcp_tools)}")
    print(f"  Shared Tools Found: {sum(1 for tool in expected_shared_tools if tool in agent_tool_names)}/{len(expected_shared_tools)}")
    
    # Test MCP connection status
    from agents.voice.sub_agents.coordinator.sub_agents.calendar.mcp_integration import get_calendar_mcp_status
    mcp_status = get_calendar_mcp_status()
    print(f"\n📡 MCP Connection Status:")
    print(f"  Connected: {mcp_status.get('connected', False)}")
    print(f"  Tools Count: {mcp_status.get('tools_count', 0)}")
    print(f"  Integration Type: {mcp_status.get('integration_type', 'unknown')}")
    
    # List all tools for debugging
    print(f"\n📋 All Tool Names Found:")
    for i, tool_name in enumerate(agent_tool_names, 1):
        # Categorize for better display
        if tool_name in expected_agent_tools:
            category = "🧠 Agent"
        elif tool_name in expected_mcp_tools:
            category = "📅 MCP"
        elif tool_name in expected_shared_tools:
            category = "🔧 Shared"
        else:
            category = "❓ Other"
        
        print(f"  {i:2d}. {category} {tool_name}")
    
    # Test agent properties
    print(f"\n🤖 Agent Properties:")
    print(f"  Name: {agent.name}")
    print(f"  Model: {agent.model}")
    print(f"  Description: {agent.description[:100]}...")
    
    # Overall assessment
    agent_tools_ok = sum(1 for tool in expected_agent_tools if tool in agent_tool_names) >= 3
    mcp_tools_ok = sum(1 for tool in expected_mcp_tools if tool in agent_tool_names) >= 5
    shared_tools_ok = sum(1 for tool in expected_shared_tools if tool in agent_tool_names) >= 4
    
    print(f"\n🎯 Overall Assessment:")
    if agent_tools_ok and mcp_tools_ok and shared_tools_ok:
        print("  ✅ Calendar Agent is ready for Phase 6 (Coordinator Integration)!")
        success = True
    else:
        print("  ⚠️ Some tools missing - review configuration")
        success = False
    
    # Clean up
    if exit_stack:
        await exit_stack.aclose()
    
    print(f"\n{'✅ Test completed successfully!' if success else '❌ Test completed with issues'}")
    return success

async def test_calendar_agent_creation():
    """Simple test just for agent creation."""
    print("🧪 Testing Basic Calendar Agent Creation...")
    
    try:
        agent, exit_stack = await create_calendar_agent()
        
        print(f"✅ Agent created successfully: {agent.name}")
        print(f"📊 Total tools: {len(agent.tools)}")
        
        if exit_stack:
            await exit_stack.aclose()
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all calendar agent tests."""
    print("🚀 Running Calendar Agent Test Suite")
    print("=" * 50)
    
    # Test 1: Basic creation
    print("\n1️⃣ Testing Basic Agent Creation...")
    creation_success = await test_calendar_agent_creation()
    
    # Test 2: Enhanced features
    print("\n2️⃣ Testing Enhanced Features...")
    features_success = await test_enhanced_features()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Basic Creation: {'✅ Pass' if creation_success else '❌ Fail'}")
    print(f"  Enhanced Features: {'✅ Pass' if features_success else '❌ Fail'}")
    
    overall_success = creation_success and features_success
    
    if overall_success:
        print("\n🎉 All tests passed! Calendar Agent is ready!")
        print("✅ Ready for Phase 6: Coordinator Integration")
    else:
        print("\n⚠️ Some tests failed - please review issues")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)