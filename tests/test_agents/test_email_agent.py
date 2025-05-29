
from pathlib import Path
import sys, os , asyncio

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

#!/usr/bin/env python3
"""Direct test of Email Agent without coordinator dependencies"""

 
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# Add this at the very top of your test_email_agent.py:
import os
print(f"🔍 GOOGLE_GENAI_USE_VERTEXAI: {os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', 'NOT SET')}")

# Also check your settings:
from config.settings import settings
print(f"🔍 Settings GOOGLE_GENAI_USE_VERTEXAI: {settings.GOOGLE_GENAI_USE_VERTEXAI}")

async def test_email_agent_direct():
    """Test email agent directly without coordinator imports"""
    print("🧪 Testing Email Agent Directly...")
    
    try:
        # Import Gmail tools directly
        from agents.voice.sub_agents.coordinator.sub_agents.email.gmail_tools import GMAIL_TOOLS
        print(f"✅ Gmail tools imported: {len(GMAIL_TOOLS)} tools")
        
        # Import email agent components
        from agents.voice.sub_agents.coordinator.sub_agents.email.agent import create_email_agent
        print("✅ Email agent creator imported")

        from config.settings import settings
        print(f"🔍 EMAIL_MODEL Setting: {settings.EMAIL_MODEL}")
        print(f"🔍 GOOGLE_API_KEY Present: {bool(settings.GOOGLE_API_KEY)}")
        
        # Create email agent
        agent, create_runner = create_email_agent()
        print(f"✅ Email Agent created: {agent.name}")
        print(f"🔧 Tools: {len(agent.tools)}")
        print(f"✅ Email Agent created: {agent.name}")
        print(f"🔧 Tools: {len(agent.tools)}")

        # ADD THIS DEBUG CODE:
        print(f"🔍 Agent Model: {agent.model}")
        print(f"🔍 Model Type: {type(agent.model)}")
        if hasattr(agent.model, 'model'):
            print(f"🔍 Model Name: {agent.model.model}")
        if hasattr(agent.model, 'api_key'):
            print(f"🔍 API Key Present: {bool(agent.model.api_key)}")
            print(f"🔍 API Key Length: {len(agent.model.api_key) if agent.model.api_key else 0}")
        
        # Test runner creation
        try:
            from memory.adk_memory_manager import get_adk_memory_manager
            memory_manager = get_adk_memory_manager()
            runner = memory_manager.create_runner(agent)
            print(f"✅ ADK Runner created successfully")
            
            # Test basic session operation
            session_id = await memory_manager.create_session("test_user", {
                "user:name": "Test User",
                "user:gmail_connected": True
            })
            print(f"✅ Test session created: {session_id}")
            
            # Test agent execution
            events = await memory_manager.run_agent(
                agent=agent,
                user_id="test_user", 
                session_id=session_id,
                user_message="Check my Gmail connection status"
            )
            print(f"✅ Agent executed with {len(events)} events")

            for i, event in enumerate(events):
                print(f"   Event {i}: {event['author']} - {event['content'][:100]}...")
                if event['author'] == 'agent':
                    print(f"   Agent Response: {event['content']}")
            
            # Check session state
            session = await memory_manager.get_session("test_user", session_id)
            if session:
                email_result = session.state.get("email_result")
                print(f"✅ Session state updated:")
                print(f"   Email result: {email_result[:100] if email_result else 'None'}...")
                print(f"   Gmail connected: {session.state.get('user:gmail_connected')}")
            
            # Cleanup
            await memory_manager.delete_session("test_user", session_id)
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"⚠️ Runner test failed (expected if ADK not fully configured): {e}")
        
        print("\n🎉 Email Agent direct test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_email_agent_direct())