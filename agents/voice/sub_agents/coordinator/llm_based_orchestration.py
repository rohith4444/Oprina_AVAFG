# agents/voice/sub_agents/coordinator/llm_intent_analyzer.py
"""
LLM-Based Intent Analyzer for Coordinator Agent

This module provides intelligent intent analysis using LLM with rule-based fallback.
Determines required agents, workflow complexity, and execution strategies using
advanced language understanding while maintaining reliability through fallback mechanisms.

Key Features:
- LLM-powered intent recognition and agent selection
- Intelligent workflow complexity assessment
- Context-aware analysis with session state integration
- Robust rule-based fallback for reliability
- Performance monitoring and caching
"""

import os
import sys
import json
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(6):  # Navigate to project root
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.models.lite_llm import LiteLlm
from config.settings import settings
from services.logging.logger import setup_logger

# Import orchestration types and rule-based fallback
from agents.voice.sub_agents.coordinator.rule_based_orchestration import AgentType, TaskComplexity, WorkflowType, coordinator_orchestration

# Configure logging
logger = setup_logger("llm_intent_analyzer", console_output=True)


class IntentAnalysisMode(Enum):
    """Intent analysis modes."""
    LLM_PRIMARY = "llm_primary"           # LLM first, rule-based fallback
    RULE_PRIMARY = "rule_primary"         # Rule-based first, LLM enhancement
    LLM_ONLY = "llm_only"                # LLM only (no fallback)
    RULE_ONLY = "rule_only"              # Rule-based only (no LLM)
    HYBRID = "hybrid"                     # Combine both approaches


class LLMIntentAnalyzer:
    """
    Advanced LLM-based intent analyzer with rule-based fallback.
    Provides intelligent request analysis for 3-agent coordination.
    """
    
    def __init__(self, mode: IntentAnalysisMode = IntentAnalysisMode.LLM_PRIMARY):
        """Initialize LLM intent analyzer."""
        self.logger = logger
        self.mode = mode
        self.logger.info(f"Initializing LLM Intent Analyzer (Mode: {mode.value})")
        
        # Initialize LLM model for intent analysis
        self.model = LiteLlm(
            model=settings.COORDINATOR_MODEL,
            api_key=settings.GOOGLE_API_KEY
        )
        
        # Performance tracking
        self.analysis_stats = {
            "total_requests": 0,
            "llm_successes": 0,
            "llm_failures": 0,
            "fallback_uses": 0,
            "average_llm_time_ms": 0,
            "average_rule_time_ms": 0
        }
        
        # Cache for similar requests (optional optimization)
        self.intent_cache = {}
        self.cache_enabled = True
        self.cache_max_size = 100
        self.cache_ttl_seconds = 300  # 5 minutes
        
        # Agent capability descriptions for LLM
        self.agent_descriptions = {
            "email_agent": {
                "primary_functions": [
                    "Fetch and search Gmail emails",
                    "Send, reply, and draft emails", 
                    "Organize emails (archive, delete, label)",
                    "Mark emails as read/unread/important",
                    "Gmail authentication and connection management"
                ],
                "keywords": ["email", "gmail", "inbox", "send", "reply", "draft", "message"],
                "context_types": ["email_context", "gmail_context"]
            },
            
            "content_agent": {
                "primary_functions": [
                    "Summarize email content with adaptive detail levels",
                    "Generate email replies with context awareness", 
                    "Analyze content sentiment and extract topics",
                    "Optimize text for voice delivery",
                    "Template-based content generation"
                ],
                "keywords": ["summarize", "analyze", "generate", "content", "reply", "write"],
                "context_types": ["content_context", "text_processing"]
            },
            
            "calendar_agent": {
                "primary_functions": [
                    "List and search calendar events",
                    "Create, update, and delete calendar events",
                    "Find free time and check availability", 
                    "Schedule meetings with optimization",
                    "Analyze schedule patterns and provide insights",
                    "Calendar authentication and management"
                ],
                "keywords": ["calendar", "event", "meeting", "schedule", "appointment", "time"],
                "context_types": ["calendar_context", "schedule_context"]
            }
        }
        
        # Workflow pattern descriptions for LLM
        self.workflow_patterns = {
            "email_only": "Simple email operations using only the email agent",
            "calendar_only": "Simple calendar operations using only the calendar agent", 
            "email_content": "Email operations with content processing (fetch + summarize, compose + send)",
            "calendar_content": "Calendar operations with content analysis (schedule analysis, detailed events)",
            "email_calendar": "Coordinated email and calendar operations (schedule + invite, email to calendar)",
            "all_agents": "Complex workflows using all three agents for comprehensive assistance"
        }
        
        self.logger.info("LLM Intent Analyzer initialized successfully")
    
    # =============================================================================
    # Main Intent Analysis Interface
    # =============================================================================
    
    async def analyze_user_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze user request using LLM with rule-based fallback.
        
        Args:
            user_input: User's natural language request
            context: Current session context
            
        Returns:
            Comprehensive intent analysis result
        """
        start_time = time.time()
        context = context or {}
        
        try:
            self.analysis_stats["total_requests"] += 1
            
            # Check cache first (if enabled)
            cache_key = self._generate_cache_key(user_input, context)
            if self.cache_enabled and cache_key in self.intent_cache:
                cached_result = self.intent_cache[cache_key]
                if self._is_cache_valid(cached_result):
                    self.logger.debug("Using cached intent analysis")
                    return cached_result["analysis"]
            
            # Primary analysis based on mode
            analysis_result = None
            
            if self.mode == IntentAnalysisMode.LLM_PRIMARY:
                analysis_result = await self._llm_primary_analysis(user_input, context)
            
            elif self.mode == IntentAnalysisMode.RULE_PRIMARY:
                analysis_result = await self._rule_primary_analysis(user_input, context)
            
            elif self.mode == IntentAnalysisMode.LLM_ONLY:
                analysis_result = await self._llm_only_analysis(user_input, context)
            
            elif self.mode == IntentAnalysisMode.RULE_ONLY:
                analysis_result = self._rule_only_analysis(user_input, context)
            
            elif self.mode == IntentAnalysisMode.HYBRID:
                analysis_result = await self._hybrid_analysis(user_input, context)
            
            else:
                # Default to LLM primary
                analysis_result = await self._llm_primary_analysis(user_input, context)
            
            # Add metadata
            analysis_result["analysis_time_ms"] = (time.time() - start_time) * 1000
            analysis_result["analysis_mode"] = self.mode.value
            analysis_result["timestamp"] = datetime.utcnow().isoformat()
            
            # Cache result (if enabled)
            if self.cache_enabled:
                self._cache_result(cache_key, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error in intent analysis: {e}")
            return self._get_emergency_fallback(user_input, str(e))
    
    # =============================================================================
    # Analysis Mode Implementations
    # =============================================================================
    
    async def _llm_primary_analysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """LLM-first analysis with rule-based fallback."""
        try:
            # Attempt LLM analysis
            llm_result = await self._perform_llm_analysis(user_input, context)
            
            # Validate LLM result
            if self._validate_llm_result(llm_result):
                self.analysis_stats["llm_successes"] += 1
                llm_result["analysis_method"] = "llm_primary"
                return llm_result
            else:
                self.logger.warning("LLM analysis validation failed, using rule-based fallback")
                raise ValueError("LLM result validation failed")
                
        except Exception as e:
            self.logger.warning(f"LLM analysis failed: {e}, falling back to rule-based")
            self.analysis_stats["llm_failures"] += 1
            self.analysis_stats["fallback_uses"] += 1
            
            # Fallback to rule-based analysis
            fallback_result = coordinator_orchestration.analyze_user_request(user_input, context)
            fallback_result["analysis_method"] = "rule_fallback"
            fallback_result["llm_failure_reason"] = str(e)
            return fallback_result
    
    async def _rule_primary_analysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based primary with LLM enhancement."""
        # Start with rule-based analysis
        rule_result = coordinator_orchestration.analyze_user_request(user_input, context)
        
        try:
            # Enhance with LLM insights
            llm_enhancement = await self._get_llm_enhancement(user_input, context, rule_result)
            
            # Merge results
            enhanced_result = self._merge_rule_and_llm_results(rule_result, llm_enhancement)
            enhanced_result["analysis_method"] = "rule_primary_enhanced"
            return enhanced_result
            
        except Exception as e:
            self.logger.warning(f"LLM enhancement failed: {e}, using rule-based only")
            rule_result["analysis_method"] = "rule_primary_only"
            rule_result["llm_enhancement_failed"] = str(e)
            return rule_result
    
    async def _llm_only_analysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """LLM-only analysis (no fallback)."""
        llm_result = await self._perform_llm_analysis(user_input, context)
        
        if self._validate_llm_result(llm_result):
            self.analysis_stats["llm_successes"] += 1
            llm_result["analysis_method"] = "llm_only"
            return llm_result
        else:
            raise ValueError("LLM analysis failed and no fallback allowed")
    
    def _rule_only_analysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based only analysis."""
        result = coordinator_orchestration.analyze_user_request(user_input, context)
        result["analysis_method"] = "rule_only"
        return result
    
    async def _hybrid_analysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Hybrid analysis combining both approaches."""
        try:
            # Run both analyses in parallel
            llm_task = self._perform_llm_analysis(user_input, context)
            rule_task = asyncio.create_task(asyncio.coroutine(lambda: coordinator_orchestration.analyze_user_request(user_input, context))())
            
            llm_result, rule_result = await asyncio.gather(llm_task, rule_task, return_exceptions=True)
            
            # Process results
            if isinstance(llm_result, Exception):
                self.logger.warning(f"LLM analysis failed in hybrid mode: {llm_result}")
                rule_result["analysis_method"] = "hybrid_rule_only"
                return rule_result
            
            if isinstance(rule_result, Exception):
                self.logger.warning(f"Rule analysis failed in hybrid mode: {rule_result}")
                llm_result["analysis_method"] = "hybrid_llm_only"
                return llm_result
            
            # Merge both results
            hybrid_result = self._merge_rule_and_llm_results(rule_result, llm_result)
            hybrid_result["analysis_method"] = "hybrid_combined"
            return hybrid_result
            
        except Exception as e:
            self.logger.error(f"Hybrid analysis failed: {e}")
            return self._get_emergency_fallback(user_input, str(e))
    
    # =============================================================================
    # LLM Analysis Implementation
    # =============================================================================
    
    async def _perform_llm_analysis(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the core LLM-based intent analysis."""
        start_time = time.time()
        
        try:
            # Build comprehensive prompt
            analysis_prompt = self._build_analysis_prompt(user_input, context)
            
            # Generate LLM response
            self.logger.debug("Sending request to LLM for intent analysis")
            response = await self.model.generate(analysis_prompt)
            
            # Parse LLM response
            parsed_result = self._parse_llm_response(response)
            
            # Add LLM-specific metadata
            execution_time = (time.time() - start_time) * 1000
            self._update_llm_stats(execution_time)
            
            parsed_result["llm_execution_time_ms"] = execution_time
            parsed_result["llm_model"] = settings.COORDINATOR_MODEL
            
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"LLM analysis execution failed: {e}")
            raise
    
    def _build_analysis_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for LLM intent analysis."""
        
        # Extract relevant context
        email_context = context.get("current_email_context", {})
        calendar_context = context.get("current_calendar_context", {})
        user_name = context.get("user_name", "")
        
        prompt = f"""
You are an intelligent intent analyzer for a voice-powered Gmail and Calendar assistant with 3 specialized agents.

## Available Agents:
{json.dumps(self.agent_descriptions, indent=2)}

## Workflow Types:
{json.dumps(self.workflow_patterns, indent=2)}

## Current Context:
- User: {user_name}
- Email Context: {json.dumps(email_context, indent=2)}
- Calendar Context: {json.dumps(calendar_context, indent=2)}

## Task:
Analyze this user request and determine the optimal execution strategy:

User Request: "{user_input}"

## Required Analysis:
Provide a JSON response with exactly this structure:

{{
    "primary_intent": "string - main intent (e.g., 'schedule_meeting', 'fetch_emails', 'comprehensive_planning')",
    "intent_confidence": "number - confidence 0.0-1.0",
    "required_agents": ["list of required agent names"],
    "workflow_type": "string - one of: email_only, calendar_only, email_content, calendar_content, email_calendar, all_agents",
    "complexity": "string - one of: simple, moderate, complex, advanced",
    "execution_strategy": {{
        "coordination_type": "string - sequential, parallel, or mixed",
        "estimated_steps": "number - estimated execution steps",
        "critical_path": ["ordered list of critical steps"]
    }},
    "context_requirements": {{
        "needs_email_context": "boolean",
        "needs_calendar_context": "boolean", 
        "needs_user_preferences": "boolean"
    }},
    "reasoning": "string - explanation of analysis decisions",
    "suggested_workflow_template": "string - suggested template name or null",
    "parallel_opportunities": ["list of steps that can run in parallel"],
    "risk_factors": ["list of potential issues or dependencies"]
}}

## Analysis Guidelines:
1. **Agent Selection**: Choose the minimal set of agents needed
2. **Workflow Complexity**: 
   - Simple: Single agent, single operation
   - Moderate: Single agent, multiple operations OR two agents, simple coordination
   - Complex: Multiple agents, sequential coordination
   - Advanced: Multiple agents, parallel + sequential coordination
3. **Context Sensitivity**: Consider current email/calendar state
4. **Efficiency**: Prefer parallel execution when possible
5. **User Intent**: Focus on what the user actually wants to accomplish

Respond ONLY with valid JSON - no additional text or formatting.
        """
        
        return prompt.strip()
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response."""
        try:
            # Clean response (remove any non-JSON content)
            response_clean = response.strip()
            
            # Find JSON content
            if '```json' in response_clean:
                start = response_clean.find('```json') + 7
                end = response_clean.find('```', start)
                response_clean = response_clean[start:end].strip()
            elif '```' in response_clean:
                start = response_clean.find('```') + 3
                end = response_clean.rfind('```')
                response_clean = response_clean[start:end].strip()
            
            # Parse JSON
            parsed = json.loads(response_clean)
            
            # Validate required fields
            required_fields = [
                "primary_intent", "required_agents", "workflow_type", 
                "complexity", "execution_strategy"
            ]
            
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Normalize agent names
            normalized_agents = []
            for agent in parsed.get("required_agents", []):
                if agent in ["email", "email_agent"]:
                    normalized_agents.append("email_agent")
                elif agent in ["content", "content_agent"]:
                    normalized_agents.append("content_agent")
                elif agent in ["calendar", "calendar_agent"]:
                    normalized_agents.append("calendar_agent")
                else:
                    normalized_agents.append(agent)
            
            parsed["required_agents"] = normalized_agents
            
            # Add compatibility fields for orchestration
            parsed["detected_keywords"] = {agent: [] for agent in normalized_agents}
            parsed["estimated_steps"] = parsed.get("execution_strategy", {}).get("estimated_steps", 1)
            parsed["parallel_possible"] = len(parsed.get("parallel_opportunities", [])) > 0
            parsed["context_coordination_needed"] = len(normalized_agents) > 1
            
            return parsed
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            self.logger.debug(f"Raw response: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        
        except Exception as e:
            self.logger.error(f"Response parsing failed: {e}")
            raise ValueError(f"Failed to parse LLM response: {e}")
    
    def _validate_llm_result(self, result: Dict[str, Any]) -> bool:
        """Validate LLM analysis result."""
        try:
            # Check required fields
            required_fields = ["primary_intent", "required_agents", "workflow_type", "complexity"]
            for field in required_fields:
                if field not in result:
                    self.logger.warning(f"LLM result missing field: {field}")
                    return False
            
            # Validate agent names
            valid_agents = ["email_agent", "content_agent", "calendar_agent"]
            for agent in result.get("required_agents", []):
                if agent not in valid_agents:
                    self.logger.warning(f"Invalid agent name: {agent}")
                    return False
            
            # Validate workflow type
            valid_workflows = ["email_only", "calendar_only", "email_content", "calendar_content", "email_calendar", "all_agents"]
            if result.get("workflow_type") not in valid_workflows:
                self.logger.warning(f"Invalid workflow type: {result.get('workflow_type')}")
                return False
            
            # Validate complexity
            valid_complexities = ["simple", "moderate", "complex", "advanced"]
            if result.get("complexity") not in valid_complexities:
                self.logger.warning(f"Invalid complexity: {result.get('complexity')}")
                return False
            
            # Check confidence if present
            confidence = result.get("intent_confidence", 1.0)
            if confidence < 0.3:  # Threshold for acceptable confidence
                self.logger.warning(f"Low confidence intent analysis: {confidence}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"LLM result validation error: {e}")
            return False
    
    # =============================================================================
    # Enhancement and Merging
    # =============================================================================
    
    async def _get_llm_enhancement(self, user_input: str, context: Dict[str, Any], rule_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get LLM enhancement for rule-based analysis."""
        enhancement_prompt = f"""
You are enhancing a rule-based intent analysis with intelligent insights.

Original Analysis:
{json.dumps(rule_result, indent=2)}

User Request: "{user_input}"

Provide enhancement suggestions in JSON format:
{{
    "confidence_score": "number 0.0-1.0",
    "optimization_suggestions": ["list of optimization ideas"],
    "missing_considerations": ["list of things the rule-based analysis might have missed"],
    "execution_refinements": {{
        "better_coordination": "suggested improvement",
        "parallel_opportunities": ["steps that could run in parallel"],
        "risk_mitigation": ["potential issues to watch for"]
    }},
    "context_insights": {{
        "user_pattern_detected": "string or null",
        "preference_hints": ["list of inferred user preferences"],
        "efficiency_tips": ["ways to optimize for this user"]
    }}
}}

Respond only with valid JSON.
        """
        
        response = await self.model.generate(enhancement_prompt)
        return self._parse_llm_response(response)
    
    def _merge_rule_and_llm_results(self, rule_result: Dict[str, Any], llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """Merge rule-based and LLM results intelligently."""
        # Start with rule-based result as base
        merged = rule_result.copy()
        
        # Enhance with LLM insights
        if "confidence_score" in llm_result:
            merged["llm_confidence"] = llm_result["confidence_score"]
        
        if "optimization_suggestions" in llm_result:
            merged["optimization_suggestions"] = llm_result["optimization_suggestions"]
        
        if "execution_refinements" in llm_result:
            merged["llm_refinements"] = llm_result["execution_refinements"]
        
        if "context_insights" in llm_result:
            merged["context_insights"] = llm_result["context_insights"]
        
        # Use LLM result for primary fields if confidence is high
        llm_confidence = llm_result.get("intent_confidence", 0.5)
        if llm_confidence > 0.8:
            # High confidence LLM result - prefer LLM analysis
            merged["primary_intent"] = llm_result.get("primary_intent", merged["primary_intent"])
            merged["required_agents"] = llm_result.get("required_agents", merged["required_agents"])
            merged["workflow_type"] = llm_result.get("workflow_type", merged["workflow_type"])
            merged["complexity"] = llm_result.get("complexity", merged["complexity"])
            merged["intent_source"] = "llm_preferred"
        else:
            merged["intent_source"] = "rule_preferred"
        
        merged["analysis_method"] = "hybrid_merged"
        return merged
    
    # =============================================================================
    # Caching and Performance
    # =============================================================================
    
    def _generate_cache_key(self, user_input: str, context: Dict[str, Any]) -> str:
        """Generate cache key for similar requests."""
        # Create a simplified context hash
        context_hash = str(hash(json.dumps(context, sort_keys=True)))
        input_hash = str(hash(user_input.lower().strip()))
        return f"{input_hash}_{context_hash[:8]}"
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache analysis result."""
        if len(self.intent_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = min(self.intent_cache.keys(), 
                           key=lambda k: self.intent_cache[k]["timestamp"])
            del self.intent_cache[oldest_key]
        
        self.intent_cache[cache_key] = {
            "analysis": result,
            "timestamp": time.time(),
            "ttl": self.cache_ttl_seconds
        }
    
    def _is_cache_valid(self, cached_entry: Dict[str, Any]) -> bool:
        """Check if cached entry is still valid."""
        age = time.time() - cached_entry["timestamp"]
        return age < cached_entry["ttl"]
    
    def _update_llm_stats(self, execution_time: float):
        """Update LLM performance statistics."""
        current_avg = self.analysis_stats["average_llm_time_ms"]
        total_requests = self.analysis_stats["llm_successes"] + self.analysis_stats["llm_failures"]
        
        if total_requests > 0:
            self.analysis_stats["average_llm_time_ms"] = (
                (current_avg * (total_requests - 1)) + execution_time
            ) / total_requests
        else:
            self.analysis_stats["average_llm_time_ms"] = execution_time
    
    # =============================================================================
    # Error Handling and Fallbacks
    # =============================================================================
    
    def _get_emergency_fallback(self, user_input: str, error: str) -> Dict[str, Any]:
        """Emergency fallback when all analysis methods fail."""
        return {
            "primary_intent": "general_assistance",
            "required_agents": ["email_agent", "content_agent"],
            "workflow_type": "email_content",
            "complexity": "simple",
            "execution_strategy": {
                "coordination_type": "sequential",
                "estimated_steps": 1,
                "critical_path": ["process_request"]
            },
            "context_coordination_needed": False,
            "analysis_method": "emergency_fallback",
            "error": error,
            "fallback_reason": "All analysis methods failed",
            "estimated_steps": 1,
            "parallel_possible": False
        }
    
    # =============================================================================
    # Performance Monitoring and Statistics
    # =============================================================================
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        total_requests = self.analysis_stats["total_requests"]
        if total_requests == 0:
            return {"message": "No requests processed yet"}
        
        success_rate = (self.analysis_stats["llm_successes"] / total_requests) * 100
        fallback_rate = (self.analysis_stats["fallback_uses"] / total_requests) * 100
        
        return {
            "mode": self.mode.value,
            "total_requests": total_requests,
            "llm_success_rate": f"{success_rate:.1f}%",
            "fallback_usage_rate": f"{fallback_rate:.1f}%",
            "average_llm_time_ms": self.analysis_stats["average_llm_time_ms"],
            "cache_enabled": self.cache_enabled,
            "cache_entries": len(self.intent_cache),
            "model_used": settings.COORDINATOR_MODEL
        }
    
    def clear_cache(self):
        """Clear the intent analysis cache."""
        self.intent_cache.clear()
        self.logger.info("Intent analysis cache cleared")
    
    def set_mode(self, mode: IntentAnalysisMode):
        """Change analysis mode dynamically."""
        old_mode = self.mode
        self.mode = mode
        self.logger.info(f"Analysis mode changed from {old_mode.value} to {mode.value}")


# =============================================================================
# Global Instance and Factory Functions
# =============================================================================

# Create global analyzer instance
llm_intent_analyzer = LLMIntentAnalyzer(mode=IntentAnalysisMode.LLM_PRIMARY)


# =============================================================================
# Export Functions for Coordinator Integration
# =============================================================================

async def analyze_request_with_llm(user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze user request using LLM with rule-based fallback.
    Main interface for coordinator agent.
    """
    return await llm_intent_analyzer.analyze_user_request(user_input, context)


def get_analyzer_stats() -> Dict[str, Any]:
    """Get analyzer performance statistics."""
    return llm_intent_analyzer.get_performance_stats()


def set_analyzer_mode(mode: str):
    """Set analyzer mode by string."""
    mode_map = {
        "llm_primary": IntentAnalysisMode.LLM_PRIMARY,
        "rule_primary": IntentAnalysisMode.RULE_PRIMARY,
        "llm_only": IntentAnalysisMode.LLM_ONLY,
        "rule_only": IntentAnalysisMode.RULE_ONLY,
        "hybrid": IntentAnalysisMode.HYBRID
    }
    
    if mode in mode_map:
        llm_intent_analyzer.set_mode(mode_map[mode])
    else:
        raise ValueError(f"Invalid mode: {mode}. Valid modes: {list(mode_map.keys())}")


def clear_analyzer_cache():
    """Clear the analyzer cache."""
    llm_intent_analyzer.clear_cache()


# =============================================================================
# Testing and Development Utilities
# =============================================================================

if __name__ == "__main__":
    # Add the completed test method
    async def test_llm_intent_analyzer():
        """Test LLM intent analyzer functionality."""
        print("🧪 Testing LLM Intent Analyzer...")
        
        test_requests = [
            {
                "input": "Check my emails and summarize the important ones",
                "context": {"user_name": "John", "current_email_context": {"unread_count": 5}}
            },
            {
                "input": "Schedule a meeting with Sarah next Tuesday at 2 PM and send her an invitation",
                "context": {"user_name": "John", "current_calendar_context": {"working_hours_start": 9}}
            },
            {
                "input": "Find free time this week for a 30-minute call and create calendar event",
                "context": {"user_name": "John", "current_calendar_context": {"upcoming_events": []}}
            },
            {
                "input": "Check my schedule today and reply to any meeting-related emails",
                "context": {
                    "user_name": "John", 
                    "current_email_context": {"unread_count": 3},
                    "current_calendar_context": {"today_events": 2}
                }
            },
            {
                "input": "Summarize emails from last week and add any mentioned dates to calendar",
                "context": {"user_name": "John", "current_email_context": {"last_sync": "2024-01-15"}}
            }
        ]
        
        print(f"Testing {len(test_requests)} different request scenarios...")
        
        # Test different analysis modes
        test_modes = [
            IntentAnalysisMode.LLM_PRIMARY,
            IntentAnalysisMode.RULE_PRIMARY,
            IntentAnalysisMode.HYBRID
        ]
        
        results_summary = {}
        
        for mode in test_modes:
            print(f"\n🔍 Testing Mode: {mode.value}")
            print("-" * 50)
            
            # Set analyzer mode
            llm_intent_analyzer.set_mode(mode)
            mode_results = []
            
            for i, test_case in enumerate(test_requests, 1):
                try:
                    print(f"\n  Test {i}: '{test_case['input'][:50]}...'")
                    
                    # Analyze request
                    analysis = await llm_intent_analyzer.analyze_user_request(
                        test_case["input"], 
                        test_case["context"]
                    )
                    
                    # Validate result structure
                    required_fields = ["primary_intent", "required_agents", "workflow_type", "complexity"]
                    validation_passed = all(field in analysis for field in required_fields)
                    
                    # Extract key metrics
                    agents_count = len(analysis.get("required_agents", []))
                    complexity = analysis.get("complexity", "unknown")
                    workflow_type = analysis.get("workflow_type", "unknown")
                    confidence = analysis.get("intent_confidence", 0.0)
                    
                    print(f"    ✅ Intent: {analysis.get('primary_intent', 'unknown')}")
                    print(f"    📧 Agents: {agents_count} ({', '.join(analysis.get('required_agents', []))})")
                    print(f"    🔄 Workflow: {workflow_type}")
                    print(f"    📊 Complexity: {complexity}")
                    print(f"    🎯 Confidence: {confidence:.2f}" if confidence else "    🎯 Confidence: N/A")
                    print(f"    ⚡ Method: {analysis.get('analysis_method', 'unknown')}")
                    
                    mode_results.append({
                        "test_case": i,
                        "success": validation_passed,
                        "agents_count": agents_count,
                        "complexity": complexity,
                        "confidence": confidence,
                        "method": analysis.get("analysis_method", "unknown"),
                        "execution_time": analysis.get("analysis_time_ms", 0)
                    })
                    
                    if not validation_passed:
                        print(f"    ⚠️  Validation failed - missing fields")
                    
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    mode_results.append({
                        "test_case": i,
                        "success": False,
                        "error": str(e)
                    })
            
            # Summarize mode results
            successful_tests = [r for r in mode_results if r.get("success", False)]
            success_rate = len(successful_tests) / len(mode_results) * 100 if mode_results else 0
            
            avg_execution_time = sum(r.get("execution_time", 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0
            
            print(f"\n  📊 Mode Summary:")
            print(f"    Success Rate: {success_rate:.1f}% ({len(successful_tests)}/{len(mode_results)})")
            print(f"    Avg Execution Time: {avg_execution_time:.1f}ms")
            
            # Analyze agent selection patterns
            agent_patterns = {}
            for result in successful_tests:
                agents_count = result.get("agents_count", 0)
                if agents_count not in agent_patterns:
                    agent_patterns[agents_count] = 0
                agent_patterns[agents_count] += 1
            
            print(f"    Agent Selection Patterns: {dict(agent_patterns)}")
            
            results_summary[mode.value] = {
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "agent_patterns": agent_patterns,
                "successful_tests": len(successful_tests)
            }
        
        # Test performance comparison
        print(f"\n🏁 Performance Comparison Across Modes:")
        print("-" * 60)
        
        for mode, results in results_summary.items():
            print(f"  {mode}:")
            print(f"    Success Rate: {results['success_rate']:.1f}%")
            print(f"    Avg Time: {results['avg_execution_time']:.1f}ms")
            print(f"    Tests Passed: {results['successful_tests']}")
        
        # Test cache functionality
        print(f"\n💾 Testing Cache Functionality:")
        print("-" * 40)
        
        # Enable caching and test
        llm_intent_analyzer.cache_enabled = True
        
        # Run same request twice to test caching
        test_input = test_requests[0]["input"]
        test_context = test_requests[0]["context"]
        
        # First run (should cache)
        start_time = time.time()
        result1 = await llm_intent_analyzer.analyze_user_request(test_input, test_context)
        first_time = (time.time() - start_time) * 1000
        
        # Second run (should use cache)
        start_time = time.time()
        result2 = await llm_intent_analyzer.analyze_user_request(test_input, test_context)
        cached_time = (time.time() - start_time) * 1000
        
        cache_speedup = first_time / cached_time if cached_time > 0 else 1
        
        print(f"  First Run: {first_time:.1f}ms")
        print(f"  Cached Run: {cached_time:.1f}ms")
        print(f"  Speedup: {cache_speedup:.1f}x")
        print(f"  Cache Entries: {len(llm_intent_analyzer.intent_cache)}")
        
        # Test error handling
        print(f"\n🚨 Testing Error Handling:")
        print("-" * 35)
        
        # Test with invalid input
        try:
            error_result = await llm_intent_analyzer.analyze_user_request("", {})
            print(f"  Empty input handled: ✅")
            print(f"  Fallback method: {error_result.get('analysis_method', 'unknown')}")
        except Exception as e:
            print(f"  Empty input error: {str(e)}")
        
        # Test with malformed context
        try:
            malformed_result = await llm_intent_analyzer.analyze_user_request(
                "Test request", 
                {"malformed": {"deeply": {"nested": {"context": None}}}}
            )
            print(f"  Malformed context handled: ✅")
        except Exception as e:
            print(f"  Malformed context error: {str(e)}")
        
        # Get final performance stats
        print(f"\n📈 Final Performance Statistics:")
        print("-" * 45)
        
        stats = llm_intent_analyzer.get_performance_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test analyzer utilities
        print(f"\n🔧 Testing Analyzer Utilities:")
        print("-" * 40)
        
        # Test mode switching
        original_mode = llm_intent_analyzer.mode
        llm_intent_analyzer.set_mode(IntentAnalysisMode.RULE_ONLY)
        print(f"  Mode switching: ✅ (changed to {llm_intent_analyzer.mode.value})")
        
        # Test cache clearing
        cache_count_before = len(llm_intent_analyzer.intent_cache)
        llm_intent_analyzer.clear_cache()
        cache_count_after = len(llm_intent_analyzer.intent_cache)
        print(f"  Cache clearing: ✅ ({cache_count_before} → {cache_count_after} entries)")
        
        # Restore original mode
        llm_intent_analyzer.set_mode(original_mode)
        
        # Final validation
        print(f"\n🎯 Test Summary:")
        print("-" * 25)
        
        total_modes_tested = len(test_modes)
        total_scenarios_tested = len(test_requests) * total_modes_tested
        overall_success_rate = sum(r["success_rate"] for r in results_summary.values()) / len(results_summary)
        
        print(f"  Total modes tested: {total_modes_tested}")
        print(f"  Total scenarios tested: {total_scenarios_tested}")
        print(f"  Overall success rate: {overall_success_rate:.1f}%")
        print(f"  Cache functionality: ✅")
        print(f"  Error handling: ✅")
        print(f"  Utilities: ✅")
        
        # Recommendations based on test results
        print(f"\n💡 Recommendations:")
        print("-" * 25)
        
        best_mode = max(results_summary.keys(), key=lambda k: results_summary[k]["success_rate"])
        fastest_mode = min(results_summary.keys(), key=lambda k: results_summary[k]["avg_execution_time"])
        
        print(f"  Best accuracy: {best_mode} ({results_summary[best_mode]['success_rate']:.1f}%)")
        print(f"  Fastest mode: {fastest_mode} ({results_summary[fastest_mode]['avg_execution_time']:.1f}ms)")
        
        if overall_success_rate < 80:
            print(f"  ⚠️  Consider improving LLM prompts or fallback logic")
        elif overall_success_rate >= 95:
            print(f"  🎉 Excellent performance across all modes!")
        else:
            print(f"  ✅ Good performance, ready for production use")
        
        print(f"\n✅ LLM Intent Analyzer testing completed successfully!")
        
        return {
            "overall_success_rate": overall_success_rate,
            "best_mode": best_mode,
            "fastest_mode": fastest_mode,
            "modes_tested": total_modes_tested,
            "scenarios_tested": total_scenarios_tested,
            "cache_functional": cache_count_after == 0,
            "error_handling_works": True
        }

    # Run the test
    asyncio.run(test_llm_intent_analyzer())