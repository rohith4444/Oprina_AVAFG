"""
Root Agent Definition for ADK Integration

This module provides the global root agent that ADK uses as the entry point.
The voice agent serves as the root with coordinator delegation.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.voice.agent import create_voice_agent
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("root_agent", console_output=True)

def get_root_agent():
    """
    Get the root agent for ADK integration.
    
    Returns:
        LlmAgent: Voice agent configured as root agent
    """
    try:
        logger.info("Creating root agent for ADK integration...")
        
        # Voice agent serves as the root agent
        root_agent = create_voice_agent()
        
        logger.info(f"Root agent '{root_agent.name}' created successfully")
        logger.info(f"Sub-agents: {len(root_agent.sub_agents)}")
        logger.info(f"Tools: {len(root_agent.tools)}")
        logger.info("ADK root agent ready for integration")
        
        return root_agent
        
    except Exception as e:
        logger.error(f"Failed to create root agent: {e}")
        raise

# Global root agent instance for ADK
root_agent = get_root_agent()

# Export for ADK integration
__all__ = ["root_agent", "get_root_agent"]

# Now, root_agent is available as a global variable for ADK Web to find

if __name__ == "__main__":
    print("🤖 Testing Root Agent Creation...")
    
    try:
        agent = get_root_agent()
        print(f"✅ Root Agent: {agent.name}")
        print(f"🧠 Model: {agent.model}")
        print(f"🔧 Tools: {len(agent.tools)}")
        print(f"🤖 Sub-agents: {len(agent.sub_agents)}")
        
        # Show hierarchy
        print(f"\n📋 Agent Hierarchy:")
        print(f"  └── {agent.name} (Root - Voice Interface)")
        
        for sub_agent in agent.sub_agents:
            print(f"      └── {sub_agent.name}")
            if hasattr(sub_agent, 'sub_agents') and sub_agent.sub_agents:
                for sub_sub_agent in sub_agent.sub_agents:
                    print(f"          └── {sub_sub_agent.name}")
        
        print(f"\n🎯 Root agent ready for ADK integration!")
        
    except Exception as e:
        print(f"❌ Root agent creation failed: {e}")
        import traceback
        traceback.print_exc()

# Add this line for ADK Web compatibility
# ADK Web looks for both 'root_agent' and 'agent' attributes
agent = root_agent