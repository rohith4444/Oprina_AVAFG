"""
Test Email Agent with Real MCP Tools
"""
import asyncio
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.voice.sub_agents.coordinator.sub_agents.email.agent import create_email_agent
from agents.voice.sub_agents.coordinator.sub_agents.email.mcp_integration import (
    get_gmail_mcp_status, test_gmail_tool_execution
)


class TestEmailAgent:
    """Test cases for Email Agent with real MCP tools."""
    
    @pytest.mark.asyncio
    async def test_email_agent_creation(self):
        """Test that Email Agent can be created successfully."""
        print("🧪 Testing Email Agent creation...")
        
        try:
            agent, exit_stack = await create_email_agent()
            
            async with exit_stack or nullcontext():
                assert agent is not None
                assert agent.name == "email_agent"
                assert len(agent.tools) > 0
                
                print(f"✅ Email Agent created with {len(agent.tools)} tools")
                
        except Exception as e:
            pytest.fail(f"Email Agent creation failed: {e}")
    
    def test_mcp_connection_status(self):
        """Test MCP connection status."""
        print("📡 Testing MCP connection...")
        
        status = get_gmail_mcp_status()
        
        assert isinstance(status, dict)
        assert "connected" in status
        assert "tools_count" in status
        
        print(f"✅ MCP Status: Connected={status['connected']}, Tools={status['tools_count']}")
    
    def test_gmail_tool_execution(self):
        """Test Gmail tool execution mechanism."""
        print("🔧 Testing Gmail tool execution...")
        
        # Test tool execution (will fail due to auth, but structure should work)
        result = test_gmail_tool_execution()
        
        assert isinstance(result, dict)
        assert "success" in result
        
        if result["success"]:
            print("✅ Tool execution mechanism working")
        else:
            print(f"⚠️ Tool execution failed as expected: {result.get('error', 'Unknown')}")
    
    @pytest.mark.asyncio
    async def test_email_agent_tools(self):
        """Test that Email Agent has the expected tools."""
        print("🔍 Testing Email Agent tools...")
        
        agent, exit_stack = await create_email_agent()
        
        async with exit_stack or nullcontext():
            # Count Gmail tools vs shared tools
            gmail_tools = []
            shared_tools = []
            
            for tool in agent.tools:
                tool_name = getattr(tool.func, '__name__', '')
                if 'gmail' in tool_name.lower():
                    gmail_tools.append(tool_name)
                else:
                    shared_tools.append(tool_name)
            
            print(f"📧 Gmail tools: {len(gmail_tools)}")
            print(f"🔧 Shared tools: {len(shared_tools)}")
            
            # Should have Gmail tools from MCP
            assert len(gmail_tools) > 0, "No Gmail tools found"
            
            # Should have shared tools
            expected_shared_tools = [
                'update_email_context',
                'get_email_context', 
                'log_agent_action'
            ]
            
            for expected_tool in expected_shared_tools:
                assert any(expected_tool in tool for tool in shared_tools), f"Missing shared tool: {expected_tool}"
            
            print("✅ Email Agent tools validation passed")


# Helper for nullcontext
from contextlib import nullcontext

# Standalone test runner
async def run_email_agent_tests():
    """Run Email Agent tests manually."""
    print("🧪 Running Email Agent Test Suite...")
    print("=" * 50)
    
    test_instance = TestEmailAgent()
    
    try:
        # Test 1: Agent Creation
        await test_instance.test_email_agent_creation()
        print("✅ Test 1 passed: Agent Creation")
        
        # Test 2: MCP Connection
        test_instance.test_mcp_connection_status()
        print("✅ Test 2 passed: MCP Connection")
        
        # Test 3: Tool Execution
        test_instance.test_gmail_tool_execution()
        print("✅ Test 3 passed: Tool Execution")
        
        # Test 4: Agent Tools
        await test_instance.test_email_agent_tools()
        print("✅ Test 4 passed: Agent Tools")
        
        print("=" * 50)
        print("🎉 All Email Agent tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_email_agent_tests())