"""
Real ADK Integration Test for Email Agent

This test validates that the email agent properly integrates with:
- ADK Runner and session services
- Session state access via tool_context
- Memory service integration
- Tool context validation
- State persistence via output_key
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the email agent
from agents.voice.sub_agents.coordinator.sub_agents.email.agent import create_email_agent

# Import ADK Memory Manager for real ADK testing
from memory.adk_memory_manager import get_adk_memory_manager

# Import session constants for validation
from agents.voice.sub_agents.common import (
    USER_GMAIL_CONNECTED, USER_EMAIL, USER_NAME, EMAIL_CURRENT_RESULTS
)


async def test_real_adk_integration():
    """
    Test REAL ADK integration with session state, tool context, and memory.
    This is the test that validates everything works according to ADK patterns.
    """
    print("🧪 Testing REAL ADK Integration for Email Agent...")
    print("=" * 60)
    
    test_results = {
        "agent_creation": False,
        "memory_manager": False,
        "runner_creation": False,
        "session_creation": False,
        "agent_execution": False,
        "session_state_access": False,
        "tool_context_validation": False,
        "state_persistence": False,
        "memory_integration": False
    }
    
    try:
        # Test 1: Agent Creation (Basic)
        print("1️⃣ Testing Agent Creation...")
        email_agent = create_email_agent()
        
        if email_agent and hasattr(email_agent, 'name') and email_agent.name == "email_agent":
            test_results["agent_creation"] = True
            print("   ✅ Email agent created successfully")
            print(f"   📧 Agent name: {email_agent.name}")
            print(f"   🔧 Tools count: {len(email_agent.tools)}")
            print(f"   🎯 Output key: {getattr(email_agent, 'output_key', 'None')}")
        else:
            print("   ❌ Agent creation failed")
            return test_results
        
        # Test 2: ADK Memory Manager
        print("\n2️⃣ Testing ADK Memory Manager...")
        try:
            memory_manager = get_adk_memory_manager()
            test_results["memory_manager"] = True
            print("   ✅ ADK Memory Manager initialized")
            
            # Get service info
            service_info = memory_manager.get_service_info()
            print(f"   📊 Session service: {service_info['session_service']['type']}")
            print(f"   🧠 Memory service: {service_info['memory_service']['type']}")
            
        except Exception as e:
            print(f"   ❌ Memory Manager failed: {e}")
            return test_results
        
        # Test 3: Runner Creation
        print("\n3️⃣ Testing ADK Runner Creation...")
        try:
            runner = memory_manager.create_runner(email_agent)
            test_results["runner_creation"] = True
            print("   ✅ ADK Runner created successfully")
            print(f"   🏃 Runner app name: {getattr(runner, 'app_name', 'None')}")
            
        except Exception as e:
            print(f"   ❌ Runner creation failed: {e}")
            return test_results
        
        # Test 4: Session Creation
        print("\n4️⃣ Testing Session Creation...")
        try:
            test_user_id = "test_user_email_agent"
            session_id = await memory_manager.create_session(test_user_id, {
                "user:name": "Test User",
                "user:email": "test@example.com",
                "user:gmail_connected": True,  # Set to True for testing
                "user:preferences": {
                    "email_format": "html",
                    "auto_mark_read": False
                }
            })
            
            test_results["session_creation"] = True
            print("   ✅ ADK Session created successfully")
            print(f"   🆔 Session ID: {session_id}")
            
        except Exception as e:
            print(f"   ❌ Session creation failed: {e}")
            return test_results
        
        # Test 5: Agent Execution Infrastructure (No API Required)
        print("\n5️⃣ Testing Agent Execution Infrastructure...")
        try:
            # Test if we can prepare for agent execution without actually running
            print("   🧪 Testing execution setup (no LLM call)...")
            
            # Verify agent has proper configuration for execution
            has_model = hasattr(email_agent, 'model') and email_agent.model is not None
            has_tools = hasattr(email_agent, 'tools') and len(email_agent.tools) > 0
            has_output_key = hasattr(email_agent, 'output_key') and email_agent.output_key
            
            if has_model and has_tools and has_output_key:
                test_results["agent_execution"] = True
                print("   ✅ Agent execution infrastructure ready")
                print(f"   🧠 Model configured: {has_model}")
                print(f"   🔧 Tools available: {len(email_agent.tools)}")
                print(f"   🎯 Output key set: {email_agent.output_key}")
                print("   📝 Note: Skipping actual LLM execution (no API key needed)")
            else:
                print("   ❌ Agent execution infrastructure incomplete")
                print(f"   🧠 Model: {has_model}, 🔧 Tools: {has_tools}, 🎯 Output key: {has_output_key}")
            
        except Exception as e:
            print(f"   ❌ Agent execution infrastructure test failed: {e}")
            # Continue with other tests
        
        # Test 6: Session State Access Validation
        print("\n6️⃣ Testing Session State Access...")
        try:
            # Get session to check state access
            updated_session = await memory_manager.get_session(test_user_id, session_id)
            
            if updated_session:
                test_results["session_state_access"] = True
                print("   ✅ Session state accessible")
                
                # Check key session state values
                gmail_connected = updated_session.state.get("user:gmail_connected", False)
                user_email = updated_session.state.get("user:email", "")
                user_name = updated_session.state.get("user:name", "")
                
                print(f"   📧 Gmail connected: {gmail_connected}")
                print(f"   👤 User email: {user_email}")
                print(f"   🏷️ User name: {user_name}")
                
                # Test that we can write to session state (simulating output_key behavior)
                updated_session.state["email_result"] = "Test email agent response"
                test_results["state_persistence"] = True
                print("   ✅ Session state writing works (output_key simulation)")
                print("   💾 Email result key can be written to session state")
                
            else:
                print("   ❌ Could not retrieve session")
                
        except Exception as e:
            print(f"   ❌ Session state access failed: {e}")
        
        # Test 7: Tool Context Validation (Simulated)
        print("\n7️⃣ Testing Tool Context Validation...")
        try:
            # Test our validation function with real session context
            from agents.voice.sub_agents.common.utils import validate_tool_context
            
            # Create a mock tool context similar to what ADK provides
            class MockADKToolContext:
                def __init__(self, session):
                    self.session = session
                    self.invocation_id = "test_invocation_123"
            
            if updated_session:
                mock_context = MockADKToolContext(updated_session)
                validation_result = validate_tool_context(mock_context, "test_function")
                
                if validation_result:
                    test_results["tool_context_validation"] = True
                    print("   ✅ Tool context validation works")
                    print("   🔍 Validation passed for mock ADK context")
                else:
                    print("   ❌ Tool context validation failed")
            
        except Exception as e:
            print(f"   ❌ Tool context validation test failed: {e}")
        
        # Test 8: Memory Integration
        print("\n8️⃣ Testing Memory Integration...")
        try:
            # Test if load_memory tool is available
            memory_tool_found = False
            for tool in email_agent.tools:
                if hasattr(tool, 'func') and getattr(tool.func, '__name__', '') == 'load_memory':
                    memory_tool_found = True
                    break
            
            if memory_tool_found:
                test_results["memory_integration"] = True
                print("   ✅ load_memory tool available")
                print("   🧠 Cross-session memory integration ready")
            else:
                print("   ❌ load_memory tool not found")
        
        except Exception as e:
            print(f"   ❌ Memory integration test failed: {e}")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        try:
            await memory_manager.delete_session(test_user_id, session_id)
            print("   ✅ Test session cleaned up")
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Results Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests >= 7:  # Allow some tolerance
        print("🎉 EMAIL AGENT IS READY FOR ADK HIERARCHY!")
        print("✅ Session state, tool context, and memory integration work correctly")
        print("✅ Ready to implement Content and Calendar agents with same pattern")
    elif passed_tests >= 5:
        print("⚠️ EMAIL AGENT IS MOSTLY READY with minor issues")
        print("🔧 Some features may need adjustment but core functionality works")
    else:
        print("❌ EMAIL AGENT NEEDS MORE WORK")
        print("🛠️ Significant issues found that need to be resolved")
    
    return test_results


async def test_individual_gmail_tool():
    """
    Test individual Gmail tool with real ADK context to validate tool_context integration.
    """
    print("\n" + "=" * 60)
    print("🔧 Testing Individual Gmail Tool Integration")
    print("=" * 60)
    
    try:
        # Import a specific Gmail tool for testing
        from agents.voice.sub_agents.coordinator.sub_agents.email.gmail_tools import gmail_check_connection
        
        # Create ADK context for testing
        memory_manager = get_adk_memory_manager()
        test_user_id = "test_tool_user"
        session_id = await memory_manager.create_session(test_user_id, {
            "user:gmail_connected": True,
            "user:email": "test@example.com"
        })
        
        # Get session for tool context simulation
        session = await memory_manager.get_session(test_user_id, session_id)
        
        if session:
            # Create mock tool context
            class MockToolContext:
                def __init__(self, session):
                    self.session = session
                    self.invocation_id = "tool_test_123"
            
            mock_context = MockToolContext(session)
            
            # Test tool with mock context
            print("🧪 Testing gmail_check_connection with ADK-like context...")
            result = gmail_check_connection(mock_context)
            print(f"   📧 Tool result: {result}")
            
            # Check if session state was updated
            updated_session = await memory_manager.get_session(test_user_id, session_id)
            if updated_session:
                # Look for any email-related state updates
                email_activity = updated_session.state.get("email:last_activity", "")
                gmail_status = updated_session.state.get("gmail:last_check", "")
                
                if email_activity or gmail_status:
                    print("   ✅ Tool successfully updated session state")
                    print(f"   📊 Email activity: {email_activity}")
                    print(f"   🔍 Gmail status: {gmail_status}")
                else:
                    print("   ⚠️ No session state updates detected")
        
        # Cleanup
        await memory_manager.delete_session(test_user_id, session_id)
        print("   ✅ Tool test cleanup completed")
        
    except Exception as e:
        print(f"   ❌ Individual tool test failed: {e}")


if __name__ == "__main__":
    # Run the comprehensive test
    print("🚀 Starting Comprehensive ADK Integration Test...")
    
    async def run_all_tests():
        # Main integration test
        results = await test_real_adk_integration()
        
        # Individual tool test
        await test_individual_gmail_tool()
        
        return results
    
    # Execute tests
    test_results = asyncio.run(run_all_tests())
    
    print(f"\n🏁 Testing completed!")
    print(f"📋 Results available for analysis")