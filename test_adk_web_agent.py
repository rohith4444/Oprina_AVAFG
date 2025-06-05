"""
Test script to verify ADK Web agent discovery

This script tests if the root_agent and agent variables are properly exposed
for ADK Web to discover.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_agent_discovery():
    """Test if the agent is discoverable by ADK Web."""
    print("[TEST] Testing ADK Web Agent...")
    
    # Try importing from agents package
    try:
        from agents import root_agent, agent, _initialize_agent
        print("[OK] Successfully imported root_agent and agent from agents package")
        
        # Initialize the agent
        _initialize_agent()
        
        print(f"  - root_agent name: {root_agent.name}")
        print(f"  - agent name: {agent.name}")
    except ImportError as e:
        print("[FAIL] Failed to import from agents package: " + str(e))
    except Exception as e:
        print("[FAIL] Error accessing agent attributes: " + str(e))
    
    # Try importing directly from root_agent module
    try:
        from agents.root_agent import root_agent, agent
        print("[OK] Successfully imported root_agent and agent from agents.root_agent")
        print(f"  - root_agent name: {root_agent.name}")
        print(f"  - agent name: {agent.name}")
    except ImportError as e:
        print("[FAIL] Failed to import from agents.root_agent: " + str(e))
    except Exception as e:
        print("[FAIL] Error accessing agent attributes: " + str(e))
    
    # Check if agents/__init__.py exports the variables
    try:
        import agents
        print("[OK] Successfully imported agents package")
        print(f"  - Has root_agent: {hasattr(agents, 'root_agent')}")
        print(f"  - Has agent: {hasattr(agents, 'agent')}")
        
        # Initialize the agent
        agents._initialize_agent()
        
        if hasattr(agents, 'root_agent') and agents.root_agent is not None:
            print(f"  - root_agent name: {agents.root_agent.name}")
        if hasattr(agents, 'agent') and agents.agent is not None:
            print(f"  - agent name: {agents.agent.name}")
    except ImportError as e:
        print("[FAIL] Failed to import agents package: " + str(e))
    except Exception as e:
        print("[FAIL] Error accessing agent attributes: " + str(e))
    
    print("[INFO] ADK Web Agent test results:")
    print("[OK] ADK Web Agent test completed")

if __name__ == "__main__":
    test_agent_discovery() 