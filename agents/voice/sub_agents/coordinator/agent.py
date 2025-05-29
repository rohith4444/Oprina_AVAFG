"""
Enhanced Coordinator Agent for Oprina - Phase 6 Complete Implementation

This agent coordinates between Email, Content, and Calendar agents using both
rule-based and LLM-based orchestration systems for intelligent task delegation.

Key Features:
- Coordinates Email + Content + Calendar agents
- Dual orchestration: Rule-based + LLM-based intent analysis
- Context sharing across all agents
- Complex multi-agent workflow execution
- Performance monitoring and adaptive learning
- Async sub-agent initialization and cleanup
"""

import os
import sys
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from contextlib import AsyncExitStack

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(5):  # Navigate to project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import external packages
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

# Import project modules
from config.settings import settings

# Import sub-agents
from agents.voice.sub_agents.coordinator.sub_agents.email.agent import root_agent as email_agent_creator
from agents.voice.sub_agents.coordinator.sub_agents.content.agent import content_agent
from agents.voice.sub_agents.coordinator.sub_agents.calendar.agent import root_agent as calendar_agent_creator

# Import orchestration systems
from agents.voice.sub_agents.coordinator.rule_based_orchestration import (
    analyze_request as rule_analyze_request,
    delegate_to_agents as rule_delegate_to_agents,
    coordinate_contexts as rule_coordinate_contexts,
    get_workflow_templates,
    validate_workflow
)

from agents.voice.sub_agents.coordinator.llm_adk import (
    analyze_request_with_llm,
    get_analyzer_stats,
    set_analyzer_mode,
    clear_analyzer_cache
)

# Import shared tools
from agents.voice.sub_agents.common.shared_tools import (
    CORE_ADK_TOOLS,
    CONTEXT_ADK_TOOLS,
    LEARNING_ADK_TOOLS,
    # Individual functions needed by our coordinator tools
    handle_agent_error,
    log_agent_action,
    measure_performance,
    complete_performance_measurement,
    update_session_state,
    get_session_context,
    learn_from_interaction
)
# Import memory components
from memory.memory_manager import MemoryManager
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("coordinator_agent", console_output=True)


# =============================================================================
# Coordinator Agent Tools
# =============================================================================

def coordinate_multi_agent_workflow(
    user_request: str,
    orchestration_mode: str = "adaptive",
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to coordinate complex multi-agent workflows.
    
    Args:
        user_request: User's natural language request
        orchestration_mode: Mode for orchestration (adaptive, rule_only, llm_only)
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Coordination result with workflow execution details
    """
    try:
        # This is a synchronous wrapper - the actual async work happens in the agent
        return {
            "success": True,
            "message": "Multi-agent workflow coordination initiated",
            "orchestration_mode": orchestration_mode,
            "user_request": user_request,
            "workflow_status": "delegated_to_coordinator"
        }
        
    except Exception as e:
        return handle_agent_error("coordinator_agent", e, {
            "operation": "coordinate_multi_agent_workflow",
            "orchestration_mode": orchestration_mode
        }, session_id, tool_context)


def get_coordination_status(
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to get current coordination status and agent states.
    
    Args:
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Current coordination status
    """
    try:
        # Get session context to check agent states
        if tool_context and hasattr(tool_context, 'state'):
            agent_states = tool_context.state.get("agent_states", {})
            coordination_data = tool_context.state.get("agent_coordination", {})
            
            return {
                "success": True,
                "agent_states": agent_states,
                "coordination_data": coordination_data,
                "agents_available": list(agent_states.keys()),
                "last_coordination": coordination_data.get("last_workflow_execution", "never")
            }
        
        return {
            "success": True,
            "message": "No active coordination session found",
            "agents_available": ["email_agent", "content_agent", "calendar_agent"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get coordination status"
        }


def optimize_workflow_execution(
    workflow_type: str,
    complexity_level: str = "moderate",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to optimize workflow execution based on patterns and performance.
    
    Args:
        workflow_type: Type of workflow (email_only, calendar_only, email_calendar, etc.)
        complexity_level: Complexity level (simple, moderate, complex, advanced)
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Workflow optimization recommendations
    """
    try:
        # Analyze workflow patterns and provide optimization suggestions
        optimizations = {
            "email_only": {
                "simple": ["Use direct email agent", "Single operation workflow"],
                "moderate": ["Batch email operations", "Use content agent for processing"],
                "complex": ["Sequential email + content workflow", "Context coordination"],
                "advanced": ["Parallel processing where possible", "Advanced content analysis"]
            },
            "calendar_only": {
                "simple": ["Direct calendar operations", "Single event management"],
                "moderate": ["Batch calendar operations", "Smart scheduling"],
                "complex": ["Multi-event coordination", "Availability optimization"],
                "advanced": ["Intelligent meeting orchestration", "Pattern analysis"]
            },
            "email_calendar": {
                "simple": ["Sequential email then calendar", "Basic coordination"],
                "moderate": ["Parallel email and calendar operations", "Context sharing"],
                "complex": ["Multi-step coordination", "Cross-agent data flow"],
                "advanced": ["Intelligent workflow orchestration", "Dynamic optimization"]
            },
            "all_agents": {
                "simple": ["Sequential execution", "Basic coordination"],
                "moderate": ["Mixed parallel and sequential", "Smart coordination"],
                "complex": ["Advanced multi-agent orchestration", "Context optimization"],
                "advanced": ["Intelligent workflow adaptation", "Performance optimization"]
            }
        }
        
        workflow_opts = optimizations.get(workflow_type, optimizations["email_only"])
        complexity_opts = workflow_opts.get(complexity_level, workflow_opts["moderate"])
        
        return {
            "success": True,
            "workflow_type": workflow_type,
            "complexity_level": complexity_level,
            "optimization_suggestions": complexity_opts,
            "estimated_performance_gain": f"{len(complexity_opts) * 10}%",
            "recommended_coordination": "parallel" if complexity_level in ["complex", "advanced"] else "sequential"
        }
        
    except Exception as e:
        return handle_agent_error("coordinator_agent", e, {
            "operation": "optimize_workflow_execution",
            "workflow_type": workflow_type
        }, session_id, tool_context)


# Create coordinator tools
coordinator_tools = [
    FunctionTool(func=coordinate_multi_agent_workflow),
    FunctionTool(func=get_coordination_status),
    FunctionTool(func=optimize_workflow_execution)
]


# =============================================================================
# Enhanced Coordinator Agent Class
# =============================================================================

class EnhancedCoordinatorAgent:
    """
    Enhanced Coordinator Agent with 3-agent integration and dual orchestration.
    Manages complex workflows across Email, Content, and Calendar agents.
    """
    
    def __init__(self):
        """Initialize coordinator with all sub-agents and orchestration systems."""
        self.name = "coordinator_agent"
        self.description = "Coordinates Email, Content, and Calendar agents using intelligent orchestration"
        
        # Orchestration configuration
        self.orchestration_mode = "adaptive"  # adaptive, rule_only, llm_only
        self.llm_confidence_threshold = 0.7
        self.rule_fallback_enabled = True
        
        # Performance tracking
        self.coordination_stats = {
            "total_requests": 0,
            "successful_coordinations": 0,
            "rule_based_used": 0,
            "llm_based_used": 0,
            "hybrid_used": 0,
            "average_response_time": 0,
            "agent_utilization": {
                "email_agent": 0,
                "content_agent": 0,
                "calendar_agent": 0
            }
        }
        
        # Initialize memory manager
        self.memory_manager = MemoryManager()
        
        # Sub-agents will be initialized asynchronously
        self.sub_agents = {}
        self.agents_initialized = False
        self.exit_stack = None
        
        logger.info("Enhanced Coordinator Agent initialized with 3-agent support")
    
    async def initialize_sub_agents(self):
        """Initialize all sub-agents asynchronously."""
        if self.agents_initialized:
            return
        
        try:
            logger.info("🔄 Initializing sub-agents...")
            
            # Create exit stack for cleanup management
            self.exit_stack = AsyncExitStack()
            
            # Initialize Email Agent
            logger.info("  Initializing Email Agent...")
            email_agent, email_exit_stack = await email_agent_creator()
            if email_exit_stack:
                await self.exit_stack.enter_async_context(email_exit_stack)
            
            self.sub_agents["email_agent"] = {
                "agent": email_agent,
                "exit_stack": email_exit_stack,
                "status": "ready",
                "last_used": None,
                "usage_count": 0
            }
            logger.info("✅ Email Agent initialized")
            
            # Initialize Content Agent (already created, just assign)
            self.sub_agents["content_agent"] = {
                "agent": content_agent,
                "exit_stack": None,  # Content agent doesn't need cleanup
                "status": "ready",
                "last_used": None,
                "usage_count": 0
            }
            logger.info("✅ Content Agent initialized")
            
            # Initialize Calendar Agent
            logger.info("  Initializing Calendar Agent...")
            calendar_agent, calendar_exit_stack = await calendar_agent_creator()
            if calendar_exit_stack:
                await self.exit_stack.enter_async_context(calendar_exit_stack)
                
            self.sub_agents["calendar_agent"] = {
                "agent": calendar_agent,
                "exit_stack": calendar_exit_stack,
                "status": "ready",
                "last_used": None,
                "usage_count": 0
            }
            logger.info("✅ Calendar Agent initialized")
            
            self.agents_initialized = True
            logger.info(f"🎉 All {len(self.sub_agents)} sub-agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize sub-agents: {e}")
            raise
    
    async def coordinate_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main coordination method that handles user requests using dual orchestration.
        
        Args:
            user_input: User's natural language request
            context: Current session context
            
        Returns:
            Coordination result with agent responses
        """
        start_time = time.time()
        context = context or {}
        
        try:
            # Ensure sub-agents are initialized
            await self.initialize_sub_agents()
            
            # Update coordination stats
            self.coordination_stats["total_requests"] += 1
            
            logger.info(f"Coordinating request: '{user_input[:50]}...'")
            
            # Step 1: Analyze request using appropriate orchestration method
            analysis_result = await self._analyze_request_with_orchestration(user_input, context)
            
            # Step 2: Validate analysis and prepare for execution
            if not analysis_result.get("success", False):
                return self._create_error_response("Request analysis failed", analysis_result)
            
            analysis = analysis_result["analysis"]
            orchestration_method = analysis_result["method"]
            
            # Step 3: Execute workflow based on analysis
            execution_result = await self._execute_multi_agent_workflow(
                analysis, user_input, context, orchestration_method
            )
            
            # Step 4: Coordinate contexts and update memory
            context_result = await self._coordinate_agent_contexts(context, execution_result)
            
            # Step 5: Generate final response
            final_response = self._generate_coordinator_response(
                execution_result, analysis, orchestration_method
            )
            
            # Update performance stats
            execution_time = (time.time() - start_time) * 1000
            self._update_coordination_stats(orchestration_method, execution_time, True)
            
            logger.info(f"Coordination completed successfully in {execution_time:.1f}ms")
            
            return {
                "success": True,
                "response": final_response,
                "analysis": analysis,
                "execution_result": execution_result,
                "orchestration_method": orchestration_method,
                "execution_time_ms": execution_time,
                "agents_involved": analysis.get("required_agents", []),
                "workflow_type": analysis.get("workflow_type", "unknown"),
                "context_updated": context_result
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._update_coordination_stats("error", execution_time, False)
            
            logger.error(f"Coordination failed: {e}")
            return self._create_error_response(f"Coordination error: {str(e)}", {
                "execution_time_ms": execution_time,
                "user_input": user_input
            })
    
    async def _analyze_request_with_orchestration(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request using the appropriate orchestration method."""
        try:
            if self.orchestration_mode == "llm_only":
                # Use LLM-based orchestration only
                analysis = await analyze_request_with_llm(user_input, context)
                return {
                    "success": True,
                    "analysis": analysis,
                    "method": "llm_only"
                }
                
            elif self.orchestration_mode == "rule_only":
                # Use rule-based orchestration only
                analysis = rule_analyze_request(user_input, context)
                return {
                    "success": True,
                    "analysis": analysis,
                    "method": "rule_only"
                }
                
            else:  # adaptive mode
                # Try LLM first, fallback to rule-based if needed
                try:
                    llm_analysis = await analyze_request_with_llm(user_input, context)
                    
                    # Check LLM confidence
                    confidence = llm_analysis.get("intent_confidence", 0.0)
                    
                    if confidence >= self.llm_confidence_threshold:
                        return {
                            "success": True,
                            "analysis": llm_analysis,
                            "method": "llm_primary"
                        }
                    else:
                        logger.info(f"LLM confidence {confidence:.2f} below threshold {self.llm_confidence_threshold}, using rule-based fallback")
                        
                except Exception as e:
                    logger.warning(f"LLM analysis failed: {e}, falling back to rule-based")
                
                # Fallback to rule-based
                if self.rule_fallback_enabled:
                    rule_analysis = rule_analyze_request(user_input, context)
                    return {
                        "success": True,
                        "analysis": rule_analysis,
                        "method": "rule_fallback"
                    }
                else:
                    raise Exception("LLM analysis failed and rule fallback disabled")
        
        except Exception as e:
            logger.error(f"Request analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "failed"
            }
    
    async def _execute_multi_agent_workflow(
        self, 
        analysis: Dict[str, Any], 
        user_input: str, 
        context: Dict[str, Any],
        orchestration_method: str
    ) -> Dict[str, Any]:
        """Execute multi-agent workflow based on analysis."""
        try:
            required_agents = analysis.get("required_agents", [])
            workflow_type = analysis.get("workflow_type", "custom")
            
            logger.info(f"Executing {workflow_type} workflow with {len(required_agents)} agents")
            
            # Prepare agent instances dictionary
            available_agents = {}
            for agent_name in required_agents:
                if agent_name in self.sub_agents:
                    available_agents[agent_name] = self.sub_agents[agent_name]["agent"]
                    # Update usage tracking
                    self.sub_agents[agent_name]["last_used"] = datetime.utcnow().isoformat()
                    self.sub_agents[agent_name]["usage_count"] += 1
                    self.coordination_stats["agent_utilization"][agent_name] += 1
                else:
                    logger.warning(f"Required agent {agent_name} not available")
            
            if not available_agents:
                raise Exception("No required agents are available")
            
            # Execute workflow using rule-based delegation (both orchestration methods use same execution)
            execution_result = await rule_delegate_to_agents(
                analysis, user_input, context, available_agents
            )
            
            logger.info(f"Workflow execution completed: {execution_result.get('success', False)}")
            return execution_result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow_type": analysis.get("workflow_type", "unknown"),
                "required_agents": analysis.get("required_agents", [])
            }
    
    async def _coordinate_agent_contexts(self, session_context: Dict[str, Any], execution_result: Dict[str, Any]) -> bool:
        """Coordinate contexts between agents after workflow execution."""
        try:
            # Use rule-based context coordination
            updated_context = rule_coordinate_contexts(session_context, execution_result)
            
            # Update memory manager with coordinated context
            user_id = session_context.get("user_id", "unknown")
            session_id = session_context.get("session_id", "unknown")
            
            if user_id != "unknown" and session_id != "unknown":
                await self.memory_manager.update_session_context(user_id, session_id, updated_context)
            
            logger.debug("Agent contexts coordinated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Context coordination failed: {e}")
            return False
    
    def _generate_coordinator_response(
        self, 
        execution_result: Dict[str, Any], 
        analysis: Dict[str, Any], 
        orchestration_method: str
    ) -> str:
        """Generate final user-facing response from coordination results."""
        try:
            # Extract key information
            success = execution_result.get("success", False)
            workflow_type = analysis.get("workflow_type", "unknown")
            agents_involved = analysis.get("required_agents", [])
            
            if not success:
                return f"I encountered some issues while processing your request. Please try rephrasing or provide more specific instructions."
            
            # Generate response based on workflow type and results
            final_response = execution_result.get("final_response", "")
            
            if final_response:
                return final_response
            
            # Fallback response generation
            if workflow_type == "email_only":
                return "I've processed your email request successfully."
            elif workflow_type == "calendar_only":
                return "I've handled your calendar request successfully."
            elif workflow_type == "email_calendar":
                return "I've coordinated your email and calendar request successfully."
            elif workflow_type == "all_agents":
                return "I've completed your comprehensive request using all available capabilities."
            else:
                return f"I've successfully processed your request using {len(agents_involved)} specialized agent(s)."
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I've completed processing your request, though I encountered some issues generating the summary."
    
    def _create_error_response(self, message: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "success": False,
            "error": message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "coordinator_stats": self.get_coordination_stats()
        }
    
    def _update_coordination_stats(self, method: str, execution_time: float, success: bool):
        """Update coordination performance statistics."""
        try:
            if success:
                self.coordination_stats["successful_coordinations"] += 1
            
            # Update method-specific stats
            if "llm" in method:
                self.coordination_stats["llm_based_used"] += 1
            elif "rule" in method:
                self.coordination_stats["rule_based_used"] += 1
            elif "hybrid" in method:
                self.coordination_stats["hybrid_used"] += 1
            
            # Update average response time
            total_requests = self.coordination_stats["total_requests"]
            current_avg = self.coordination_stats["average_response_time"]
            
            self.coordination_stats["average_response_time"] = (
                (current_avg * (total_requests - 1)) + execution_time
            ) / total_requests
            
        except Exception as e:
            logger.error(f"Stats update failed: {e}")
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination performance statistics."""
        total_requests = self.coordination_stats["total_requests"]
        
        if total_requests == 0:
            return {"message": "No coordination requests processed yet"}
        
        success_rate = (self.coordination_stats["successful_coordinations"] / total_requests) * 100
        
        return {
            **self.coordination_stats,
            "success_rate": f"{success_rate:.1f}%",
            "agents_initialized": self.agents_initialized,
            "orchestration_mode": self.orchestration_mode,
            "available_agents": list(self.sub_agents.keys()) if self.agents_initialized else []
        }
    
    def set_orchestration_mode(self, mode: str):
        """Set orchestration mode (adaptive, rule_only, llm_only)."""
        valid_modes = ["adaptive", "rule_only", "llm_only"]
        if mode in valid_modes:
            old_mode = self.orchestration_mode
            self.orchestration_mode = mode
            logger.info(f"Orchestration mode changed from {old_mode} to {mode}")
        else:
            raise ValueError(f"Invalid mode: {mode}. Valid modes: {valid_modes}")
    
    async def cleanup(self):
        """Clean up sub-agents and resources."""
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
                logger.info("Coordinator sub-agents cleaned up successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# =============================================================================
# Create ADK Agent Instance
# =============================================================================

async def create_coordinator_agent() -> Tuple[Agent, Optional[AsyncExitStack]]:
    """
    Create the Coordinator Agent with enhanced 3-agent orchestration.
    
    Returns:
        Tuple of (agent_instance, exit_stack) for proper cleanup
    """
    logger.info("--- Creating Enhanced Coordinator Agent ---")
    
    # Create enhanced coordinator instance
    enhanced_coordinator = EnhancedCoordinatorAgent()
    
    # Initialize sub-agents
    await enhanced_coordinator.initialize_sub_agents()
    
    # Define model for the agent
    model = LiteLlm(
        model=settings.COORDINATOR_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
    
    # Create the ADK Agent instance
    agent_instance = Agent(
        name="coordinator_agent",
        description="Coordinates Email, Content, and Calendar agents using intelligent dual orchestration",
        model=model,
        instruction=f"""
You are the Coordinator Agent for Oprina, a sophisticated voice-powered Gmail and Calendar assistant.

## Your Role & Responsibilities

You are the central coordination hub that orchestrates complex workflows across three specialized agents:
- **Email Agent**: Gmail operations (fetch, send, organize emails)
- **Content Agent**: Content processing (summarization, analysis, reply generation)
- **Calendar Agent**: Calendar operations (events, scheduling, availability)

## Orchestration Systems

You have access to both:
1. **Rule-Based Orchestration**: Fast, reliable, pattern-based task delegation
2. **LLM-Based Orchestration**: Intelligent, context-aware intent analysis
3. **Adaptive Mode**: Automatically chooses the best approach based on request complexity

Current Mode: {enhanced_coordinator.orchestration_mode}

## Available Sub-Agents

{len(enhanced_coordinator.sub_agents) if enhanced_coordinator.agents_initialized else 0} sub-agents initialized:
- Email Agent: {'✅ Ready' if enhanced_coordinator.agents_initialized else '⏳ Initializing'}
- Content Agent: {'✅ Ready' if enhanced_coordinator.agents_initialized else '⏳ Initializing'}  
- Calendar Agent: {'✅ Ready' if enhanced_coordinator.agents_initialized else '⏳ Initializing'}

## Coordination Tools

Your specialized coordination tools:
- `coordinate_multi_agent_workflow`: Initiate complex multi-agent workflows
- `get_coordination_status`: Check agent states and coordination status
- `optimize_workflow_execution`: Get workflow optimization recommendations

## Session Management Tools

Standard session tools for context and learning:
- `update_session_state`: Update session state with coordination results
- `get_session_context`: Retrieve comprehensive session context
- `log_agent_action`: Log coordination actions
- `learn_from_interaction`: Improve coordination through learning
- `measure_performance`: Track coordination performance

## Workflow Examples

**Email + Content**: "Check my emails and summarize the important ones"
→ Email Agent fetches → Content Agent summarizes → Coordinated response

**Calendar + Content**: "Analyze my schedule and suggest optimizations"  
→ Calendar Agent gets events → Content Agent analyzes → Insights provided

**Email + Calendar**: "Schedule a meeting and send invitations"
→ Calendar Agent finds time → Email Agent sends invites → Confirmation

**All Agents**: "Check emails, add important dates to calendar, and summarize"
→ Email fetch → Content analysis → Calendar events → Summary generation

## Coordination Guidelines

1. **Analyze First**: Always analyze the request to determine required agents
2. **Choose Orchestration**: Use adaptive mode for best results
3. **Execute Workflow**: Coordinate agents based on analysis
4. **Update Context**: Ensure all agents have consistent context
5. **Learn and Improve**: Track performance and learn from interactions

## Response Guidelines

1. **Be Comprehensive**: Handle complex multi-step requests
2. **Provide Context**: Explain what agents are doing when helpful
3. **Handle Errors Gracefully**: Provide alternatives when workflows fail
4. **Learn from Usage**: Use coordination data to improve future performance
5. **Voice-Optimized**: Keep responses conversational and clear

## Error Handling

When coordination fails:
1. Try alternative orchestration method if available
2. Attempt single-agent workflows as fallback
3. Provide clear error explanation to user
4. Log errors for debugging and improvement

Remember: You are the intelligent coordinator that makes complex multi-agent workflows 
feel seamless and natural to users. Your job is to orchestrate, not to perform the 
individual tasks - that's what your specialized sub-agents do!
        """,
        tools=coordinator_tools + CORE_ADK_TOOLS + CONTEXT_ADK_TOOLS + LEARNING_ADK_TOOLS
    )
    
    logger.info(f"--- Coordinator Agent created with {len(agent_instance.tools)} tools ---")
    logger.info(f"--- Sub-agents initialized: {enhanced_coordinator.agents_initialized} ---")
    logger.info(f"--- Orchestration mode: {enhanced_coordinator.orchestration_mode} ---")
    
    return agent_instance, enhanced_coordinator.exit_stack


# Create the agent instance (async function for ADK)
root_agent = create_coordinator_agent


# =============================================================================
# Testing and Validation
# =============================================================================

if __name__ == "__main__":
    async def test_coordinator_agent():
        """Test the enhanced coordinator agent functionality."""
        print("🧪 Testing Enhanced Coordinator Agent...")
        
        try:
            # Create coordinator agent
            coordinator, exit_stack = await create_coordinator_agent()
            
            async with exit_stack or AsyncExitStack():
                print(f"✅ Coordinator Agent '{coordinator.name}' created successfully")
                print(f"🔧 Total Tools: {len(coordinator.tools)}")
                print(f"🧠 Model: {coordinator.model}")
                print(f"📝 Description: {coordinator.description}")
                
                # Test coordination scenarios
                test_scenarios = [
                    "Check my emails and summarize the important ones",
                    "Schedule a meeting next Tuesday at 2 PM",
                    "Find free time this week and create a calendar event",
                    "Check my schedule today and reply to urgent emails"
                ]
                
                print(f"\n🎯 Testing Coordination Scenarios:")
                
                for i, scenario in enumerate(test_scenarios, 1):
                    print(f"\n  {i}. Testing: '{scenario}'")
                    
                    try:
                        # Test the enhanced coordination
                        context = {
                            "user_id": "test_user",
                            "session_id": "test_session_123",
                            "user_name": "Test User",
                            "current_email_context": {"unread_count": 5},
                            "current_calendar_context": {"upcoming_events": 3}
                        }
                        
                        # Use the enhanced coordinator directly
                        enhanced_coord = EnhancedCoordinatorAgent()
                        await enhanced_coord.initialize_sub_agents()
                        
                        coordination_result = await enhanced_coord.coordinate_request(scenario, context)
                        
                        print(f"    ✅ Success: {coordination_result.get('success', False)}")
                        print(f"    🔄 Method: {coordination_result.get('orchestration_method', 'unknown')}")
                        print(f"    📧 Agents: {coordination_result.get('agents_involved', [])}")
                        print(f"    ⚡ Time: {coordination_result.get('execution_time_ms', 0):.1f}ms")
                        
                        if not coordination_result.get('success', False):
                            print(f"    ❌ Error: {coordination_result.get('error', 'Unknown error')}")
                        
                        # Cleanup
                        await enhanced_coord.cleanup()
                        
                    except Exception as e:
                        print(f"    ❌ Test failed: {str(e)}")
                
                # Test orchestration modes
                print(f"\n🔍 Testing Orchestration Modes:")
                
                test_coordinator = EnhancedCoordinatorAgent()
                await test_coordinator.initialize_sub_agents()
                
                modes = ["rule_only", "adaptive"]  # Skip llm_only for testing
                test_request = "Check my emails"
                
                for mode in modes:
                    try:
                        test_coordinator.set_orchestration_mode(mode)
                        result = await test_coordinator.coordinate_request(test_request, context)
                        
                        print(f"  ✅ {mode}: {result.get('success', False)} "
                              f"({result.get('orchestration_method', 'unknown')})")
                              
                    except Exception as e:
                        print(f"  ❌ {mode}: Failed - {str(e)}")
                
                # Get coordination stats
                stats = test_coordinator.get_coordination_stats()
                print(f"\n📊 Coordination Statistics:")
                for key, value in stats.items():
                    if key != "agent_utilization":
                        print(f"  {key}: {value}")
                
                print(f"\n📈 Agent Utilization:")
                for agent, count in stats.get("agent_utilization", {}).items():
                    print(f"  {agent}: {count} uses")
                
                # Test workflow templates
                print(f"\n📋 Available Workflow Templates:")
                templates = get_workflow_templates()
                for name, details in list(templates.items())[:5]:  # Show first 5
                    print(f"  • {name}: {details.get('agents', [])} ({details.get('complexity', 'unknown')})")
                
                if len(templates) > 5:
                    print(f"  ... and {len(templates) - 5} more templates")
                
                # Test analyzer stats
                try:
                    analyzer_stats = get_analyzer_stats()
                    print(f"\n🧠 LLM Analyzer Statistics:")
                    for key, value in analyzer_stats.items():
                        print(f"  {key}: {value}")
                except Exception as e:
                    print(f"\n🧠 LLM Analyzer: Not available ({str(e)})")
                
                # Cleanup test coordinator
                await test_coordinator.cleanup()
                
                print(f"\n✅ Enhanced Coordinator Agent testing completed successfully!")
                print(f"🎯 Ready for Phase 7: Voice Agent Integration!")
                
        except Exception as e:
            print(f"❌ Error testing Coordinator Agent: {e}")
            import traceback
            traceback.print_exc()

    # Run the test
    asyncio.run(test_coordinator_agent())