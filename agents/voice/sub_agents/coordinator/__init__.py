"""
Coordinator Agent Package

This package contains the Coordinator Agent responsible for orchestrating 
complex workflows across Email, Content, and Calendar agents using intelligent
dual orchestration (rule-based + LLM-based).

Key Features:
- 3-agent coordination (Email + Content + Calendar)
- Dual orchestration systems (Rule-based + LLM-based)
- Adaptive workflow execution (Sequential, Parallel, Mixed)
- Context coordination across agents
- Performance monitoring and optimization
- Advanced multi-agent workflow templates

Architecture:
- agent.py: Main coordinator agent with enhanced coordination logic
- rule_based_orchestration.py: Fast, reliable pattern-based orchestration
- llm_based_orchestration.py: Intelligent context-aware orchestration
- sub_agents/: Email, Content, and Calendar specialized agents

Usage:
    from agents.voice.sub_agents.coordinator import coordinator_agent
    
    # The coordinator automatically initializes and manages all sub-agents
    # and provides intelligent orchestration for complex multi-agent workflows
"""

from .agent import root_agent as coordinator_agent

# Export version and metadata
__version__ = "3.0.0"
__author__ = "Oprina Team"
__description__ = "Enhanced Coordinator Agent with 3-agent orchestration support"

# Export the main coordinator agent
__all__ = ["coordinator_agent"]

# Optional: Export orchestration utilities for advanced usage
try:
    from .rule_based_orchestration import (
        analyze_request,
        get_workflow_templates,
        validate_workflow
    )
    from .llm_based_orchestration import (
        analyze_request_with_llm,
        get_analyzer_stats,
        set_analyzer_mode
    )
    
    # Add orchestration utilities to exports
    __all__.extend([
        "analyze_request",
        "analyze_request_with_llm", 
        "get_workflow_templates",
        "validate_workflow",
        "get_analyzer_stats",
        "set_analyzer_mode"
    ])
    
except ImportError as e:
    # Graceful degradation if orchestration modules have issues
    print(f"Warning: Some orchestration utilities not available: {e}")

# Coordinator capabilities summary
COORDINATOR_CAPABILITIES = {
    "sub_agents": ["email_agent", "content_agent", "calendar_agent"],
    "orchestration_modes": ["adaptive", "rule_only", "llm_only"],
    "workflow_types": [
        "email_only", "calendar_only", "email_content", 
        "calendar_content", "email_calendar", "all_agents"
    ],
    "execution_patterns": ["sequential", "parallel", "mixed"],
    "complexity_levels": ["simple", "moderate", "complex", "advanced"],
    "features": [
        "Multi-agent coordination",
        "Intelligent orchestration", 
        "Context sharing",
        "Performance monitoring",
        "Adaptive learning",
        "Error recovery"
    ]
}

def get_coordinator_info():
    """Get comprehensive coordinator information."""
    return {
        "name": "Enhanced Coordinator Agent",
        "version": __version__,
        "description": __description__,
        "capabilities": COORDINATOR_CAPABILITIES,
        "sub_agents_count": len(COORDINATOR_CAPABILITIES["sub_agents"]),
        "orchestration_systems": 2,  # Rule-based + LLM-based
        "workflow_templates": "20+",
        "status": "Production Ready"
    }

# Module-level initialization message
print(f"🤖 Coordinator Agent Package v{__version__} loaded")
print(f"   ├── Sub-agents: {len(COORDINATOR_CAPABILITIES['sub_agents'])}")
print(f"   ├── Orchestration: {len(COORDINATOR_CAPABILITIES['orchestration_modes'])} modes")
print(f"   └── Workflow types: {len(COORDINATOR_CAPABILITIES['workflow_types'])}")

# Development and testing utilities
def test_coordinator_package():
    """Quick test of coordinator package functionality."""
    print("\n🧪 Testing Coordinator Package...")
    
    try:
        # Test coordinator agent import
        from .agent import root_agent
        print("✅ Coordinator agent import successful")
        
        # Test orchestration imports
        from .rule_based_orchestration import coordinator_orchestration
        print("✅ Rule-based orchestration import successful")
        
        from .llm_based_orchestration import llm_intent_analyzer
        print("✅ LLM-based orchestration import successful")
        
        # Test sub-agent imports
        try:
            from .sub_agents.email import email_agent_creator
            print("✅ Email agent import successful")
        except ImportError as e:
            print(f"⚠️  Email agent import issue: {e}")
            
        try:
            from .sub_agents.content import content_agent
            print("✅ Content agent import successful")
        except ImportError as e:
            print(f"⚠️  Content agent import issue: {e}")
            
        try:
            from .sub_agents.calendar import calendar_agent_creator
            print("✅ Calendar agent import successful")
        except ImportError as e:
            print(f"⚠️  Calendar agent import issue: {e}")
        
        print("🎉 Coordinator package test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Coordinator package test failed: {e}")
        return False

# Auto-run test in development
if __name__ == "__main__":
    test_coordinator_package()
    info = get_coordinator_info()
    print(f"\n📋 Coordinator Info:")
    for key, value in info.items():
        print(f"   {key}: {value}")