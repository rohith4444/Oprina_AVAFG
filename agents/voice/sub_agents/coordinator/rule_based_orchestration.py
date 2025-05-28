# agents/voice/sub_agents/coordinator/orchestration.py
"""
Enhanced Coordinator Agent Orchestration - 3 Agent Support

This module provides orchestration logic for coordinating between Email, Content, 
and Calendar agents. Handles task delegation, workflow management, and context
coordination across all three specialized agents.

Updated for Phase 6: Now supports Email + Content + Calendar coordination
"""

import os
import sys
import json
import asyncio
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

from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("coordinator_orchestration", console_output=True)


class AgentType(Enum):
    """Types of available agents."""
    EMAIL = "email_agent"
    CONTENT = "content_agent"
    CALENDAR = "calendar_agent"


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"          # Single agent, single operation
    MODERATE = "moderate"      # Single agent, multiple operations
    COMPLEX = "complex"        # Multiple agents, sequential
    ADVANCED = "advanced"      # Multiple agents, parallel + sequential


class WorkflowType(Enum):
    """Types of multi-agent workflows."""
    EMAIL_ONLY = "email_only"
    CALENDAR_ONLY = "calendar_only"
    EMAIL_CONTENT = "email_content"
    CALENDAR_CONTENT = "calendar_content"
    EMAIL_CALENDAR = "email_calendar"
    ALL_AGENTS = "all_agents"


class CoordinatorOrchestration:
    """
    Enhanced orchestration logic for 3-agent coordination.
    Handles task analysis, agent delegation, and workflow management.
    """
    
    def __init__(self):
        """Initialize orchestration with enhanced 3-agent support."""
        self.logger = logger
        self.logger.info("Initializing Enhanced Coordinator Orchestration (3-Agent Support)")
        
        # Agent capabilities mapping (enhanced)
        self.agent_capabilities = {
            AgentType.EMAIL: {
                "primary": [
                    "fetch_emails", "search_emails", "send_email", "reply_email",
                    "draft_email", "delete_email", "archive_email", "label_email",
                    "mark_read", "mark_important", "gmail_auth", "email_management"
                ],
                "keywords": [
                    "email", "gmail", "inbox", "send", "reply", "draft", "message",
                    "unread", "important", "archive", "delete", "compose"
                ],
                "context_types": ["email_context", "gmail_context"]
            },
            
            AgentType.CONTENT: {
                "primary": [
                    "summarize_email", "generate_reply", "analyze_content",
                    "optimize_voice", "extract_topics", "sentiment_analysis",
                    "content_generation", "text_processing"
                ],
                "keywords": [
                    "summarize", "summary", "analyze", "generate", "content",
                    "reply", "draft", "tone", "sentiment", "topics", "write"
                ],
                "context_types": ["content_context", "text_context"]
            },
            
            AgentType.CALENDAR: {
                "primary": [
                    "list_events", "create_event", "update_event", "delete_event",
                    "find_free_time", "check_availability", "schedule_meeting",
                    "calendar_auth", "analyze_schedule", "manage_calendar"
                ],
                "keywords": [
                    "calendar", "event", "meeting", "schedule", "appointment",
                    "free", "busy", "available", "time", "date", "book", "plan"
                ],
                "context_types": ["calendar_context", "schedule_context"]
            }
        }
        
        # Workflow patterns for multi-agent coordination
        self.workflow_patterns = {
            WorkflowType.EMAIL_CONTENT: {
                "description": "Email operations with content processing",
                "agents": [AgentType.EMAIL, AgentType.CONTENT],
                "patterns": [
                    "fetch_and_summarize", "compose_and_send", "reply_with_analysis",
                    "email_management_with_content"
                ]
            },
            
            WorkflowType.CALENDAR_CONTENT: {
                "description": "Calendar operations with content analysis",
                "agents": [AgentType.CALENDAR, AgentType.CONTENT],
                "patterns": [
                    "analyze_schedule_and_suggest", "create_event_with_details",
                    "schedule_analysis_with_insights"
                ]
            },
            
            WorkflowType.EMAIL_CALENDAR: {
                "description": "Coordinated email and calendar operations",
                "agents": [AgentType.EMAIL, AgentType.CALENDAR],
                "patterns": [
                    "schedule_and_invite", "email_to_calendar", "calendar_to_email",
                    "meeting_coordination", "availability_and_invite"
                ]
            },
            
            WorkflowType.ALL_AGENTS: {
                "description": "Complex workflows using all agents",
                "agents": [AgentType.EMAIL, AgentType.CONTENT, AgentType.CALENDAR],
                "patterns": [
                    "comprehensive_scheduling", "full_email_calendar_workflow",
                    "intelligent_meeting_management", "complete_assistant_workflow"
                ]
            }
        }
        
        # Common workflow templates
        self.workflow_templates = self._initialize_workflow_templates()
        
        self.logger.info("Enhanced Coordinator Orchestration initialized with 3-agent support")
    
    def _initialize_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize workflow templates for common multi-agent patterns."""
        return {
            # Email + Calendar Workflows
            "schedule_meeting_and_send_invites": {
                "type": WorkflowType.EMAIL_CALENDAR,
                "complexity": TaskComplexity.COMPLEX,
                "steps": [
                    {"agent": AgentType.CALENDAR, "action": "find_free_time", "parallel": False},
                    {"agent": AgentType.CALENDAR, "action": "create_event", "parallel": False},
                    {"agent": AgentType.EMAIL, "action": "send_invites", "parallel": False}
                ],
                "coordination": "sequential"
            },
            
            "email_to_calendar_event": {
                "type": WorkflowType.EMAIL_CALENDAR,
                "complexity": TaskComplexity.MODERATE,
                "steps": [
                    {"agent": AgentType.EMAIL, "action": "extract_meeting_details", "parallel": False},
                    {"agent": AgentType.CALENDAR, "action": "create_event", "parallel": False}
                ],
                "coordination": "sequential"
            },
            
            "check_availability_and_reply": {
                "type": WorkflowType.EMAIL_CALENDAR,
                "complexity": TaskComplexity.COMPLEX,
                "steps": [
                    {"agent": AgentType.CALENDAR, "action": "check_availability", "parallel": False},
                    {"agent": AgentType.EMAIL, "action": "compose_reply", "parallel": False},
                    {"agent": AgentType.EMAIL, "action": "send_reply", "parallel": False}
                ],
                "coordination": "sequential"
            },
            
            # Email + Content Workflows (existing, enhanced)
            "fetch_and_summarize_emails": {
                "type": WorkflowType.EMAIL_CONTENT,
                "complexity": TaskComplexity.MODERATE,
                "steps": [
                    {"agent": AgentType.EMAIL, "action": "fetch_emails", "parallel": False},
                    {"agent": AgentType.CONTENT, "action": "summarize_content", "parallel": False}
                ],
                "coordination": "sequential"
            },
            
            "compose_intelligent_reply": {
                "type": WorkflowType.EMAIL_CONTENT,
                "complexity": TaskComplexity.MODERATE,
                "steps": [
                    {"agent": AgentType.CONTENT, "action": "analyze_email", "parallel": False},
                    {"agent": AgentType.CONTENT, "action": "generate_reply", "parallel": False},
                    {"agent": AgentType.EMAIL, "action": "send_reply", "parallel": False}
                ],
                "coordination": "sequential"
            },
            
            # Calendar + Content Workflows
            "analyze_schedule_patterns": {
                "type": WorkflowType.CALENDAR_CONTENT,
                "complexity": TaskComplexity.MODERATE,
                "steps": [
                    {"agent": AgentType.CALENDAR, "action": "get_schedule_data", "parallel": False},
                    {"agent": AgentType.CONTENT, "action": "analyze_patterns", "parallel": False}
                ],
                "coordination": "sequential"
            },
            
            "create_detailed_event": {
                "type": WorkflowType.CALENDAR_CONTENT,
                "complexity": TaskComplexity.MODERATE,
                "steps": [
                    {"agent": AgentType.CONTENT, "action": "enhance_event_details", "parallel": False},
                    {"agent": AgentType.CALENDAR, "action": "create_event", "parallel": False}
                ],
                "coordination": "sequential"
            },
            
            # All Agents Workflows (Advanced)
            "comprehensive_meeting_management": {
                "type": WorkflowType.ALL_AGENTS,
                "complexity": TaskComplexity.ADVANCED,
                "steps": [
                    {"agent": AgentType.EMAIL, "action": "fetch_meeting_emails", "parallel": False},
                    {"agent": AgentType.CONTENT, "action": "extract_meeting_info", "parallel": False},
                    {"agent": AgentType.CALENDAR, "action": "find_optimal_time", "parallel": False},
                    {"agent": AgentType.CALENDAR, "action": "create_event", "parallel": False},
                    {"agent": AgentType.CONTENT, "action": "generate_invite_content", "parallel": True},
                    {"agent": AgentType.EMAIL, "action": "send_invites", "parallel": False}
                ],
                "coordination": "mixed"
            },
            
            "intelligent_daily_planning": {
                "type": WorkflowType.ALL_AGENTS,
                "complexity": TaskComplexity.ADVANCED,
                "steps": [
                    {"agent": AgentType.EMAIL, "action": "fetch_recent_emails", "parallel": True},
                    {"agent": AgentType.CALENDAR, "action": "get_today_events", "parallel": True},
                    {"agent": AgentType.CONTENT, "action": "analyze_priorities", "parallel": False},
                    {"agent": AgentType.CONTENT, "action": "generate_daily_summary", "parallel": False}
                ],
                "coordination": "mixed"
            }
        }
    
    # =============================================================================
    # Task Analysis and Agent Selection
    # =============================================================================
    
    def analyze_user_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze user request to determine required agents and workflow.
        Enhanced for 3-agent coordination.
        
        Args:
            user_input: User's natural language request
            context: Current session context
            
        Returns:
            Analysis result with agent assignments and workflow
        """
        try:
            user_input_lower = user_input.lower()
            context = context or {}
            
            # Extract keywords and intent
            detected_keywords = self._extract_keywords(user_input_lower)
            primary_intent = self._determine_primary_intent(user_input_lower, detected_keywords)
            
            # Determine required agents
            required_agents = self._determine_required_agents(detected_keywords, primary_intent)
            
            # Assess complexity
            complexity = self._assess_task_complexity(required_agents, detected_keywords, user_input)
            
            # Determine workflow type
            workflow_type = self._determine_workflow_type(required_agents)
            
            # Find matching workflow template
            workflow_template = self._find_workflow_template(primary_intent, workflow_type, complexity)
            
            # Generate execution plan
            execution_plan = self._generate_execution_plan(
                required_agents, workflow_template, primary_intent, detected_keywords, context
            )
            
            analysis_result = {
                "primary_intent": primary_intent,
                "detected_keywords": detected_keywords,
                "required_agents": [agent.value for agent in required_agents],
                "workflow_type": workflow_type.value if workflow_type else "custom",
                "complexity": complexity.value,
                "workflow_template": workflow_template,
                "execution_plan": execution_plan,
                "estimated_steps": len(execution_plan.get("steps", [])),
                "parallel_possible": any(step.get("parallel", False) for step in execution_plan.get("steps", [])),
                "context_coordination_needed": len(required_agents) > 1
            }
            
            self.logger.info(f"Request analysis: {len(required_agents)} agents, {complexity.value} complexity")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing user request: {e}")
            return self._get_fallback_analysis(user_input)
    
    def _extract_keywords(self, user_input: str) -> Dict[AgentType, List[str]]:
        """Extract keywords relevant to each agent type."""
        detected = {agent_type: [] for agent_type in AgentType}
        
        for agent_type, capabilities in self.agent_capabilities.items():
            for keyword in capabilities["keywords"]:
                if keyword in user_input:
                    detected[agent_type].append(keyword)
        
        return detected
    
    def _determine_primary_intent(self, user_input: str, keywords: Dict[AgentType, List[str]]) -> str:
        """Determine the primary intent from user input."""
        # Intent patterns (enhanced for calendar)
        intent_patterns = {
            # Email intents
            "fetch_emails": ["check email", "get email", "show email", "read email"],
            "send_email": ["send email", "compose email", "write email"],
            "reply_email": ["reply", "respond", "answer"],
            "manage_emails": ["organize email", "delete email", "archive"],
            
            # Calendar intents
            "schedule_meeting": ["schedule meeting", "book meeting", "arrange meeting"],
            "check_availability": ["check availability", "free time", "available"],
            "create_event": ["create event", "add event", "schedule", "book"],
            "view_calendar": ["show calendar", "check calendar", "view schedule"],
            "find_time": ["find time", "when available", "free slot"],
            
            # Combined intents
            "schedule_and_invite": ["schedule meeting and send", "book and invite"],
            "email_to_calendar": ["add to calendar", "create event from email"],
            "availability_reply": ["check schedule and reply", "availability and respond"],
            
            # Content intents
            "summarize": ["summarize", "summary", "brief"],
            "analyze": ["analyze", "analysis", "insights"],
            "generate_content": ["write", "compose", "generate", "create content"]
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in user_input for pattern in patterns):
                return intent
        
        # Fallback based on keyword density
        agent_scores = {agent: len(kw_list) for agent, kw_list in keywords.items()}
        if agent_scores[AgentType.EMAIL] > agent_scores[AgentType.CALENDAR]:
            return "email_general"
        elif agent_scores[AgentType.CALENDAR] > 0:
            return "calendar_general"
        else:
            return "general_assistance"
    
    def _determine_required_agents(self, keywords: Dict[AgentType, List[str]], intent: str) -> List[AgentType]:
        """Determine which agents are required based on keywords and intent."""
        required = []
        
        # Always include content agent for processing if other agents are involved
        include_content = False
        
        # Check email agent requirement
        if keywords[AgentType.EMAIL] or "email" in intent:
            required.append(AgentType.EMAIL)
            include_content = True
        
        # Check calendar agent requirement
        if keywords[AgentType.CALENDAR] or "calendar" in intent or "schedule" in intent or "meeting" in intent:
            required.append(AgentType.CALENDAR)
            include_content = True
        
        # Include content agent for multi-agent workflows or content-specific tasks
        if include_content or keywords[AgentType.CONTENT] or "content" in intent:
            if AgentType.CONTENT not in required:
                required.append(AgentType.CONTENT)
        
        # Specific multi-agent patterns
        multi_agent_intents = [
            "schedule_and_invite", "email_to_calendar", "availability_reply",
            "comprehensive_meeting_management", "intelligent_daily_planning"
        ]
        
        if any(ma_intent in intent for ma_intent in multi_agent_intents):
            # Ensure all relevant agents are included
            if AgentType.EMAIL not in required:
                required.append(AgentType.EMAIL)
            if AgentType.CALENDAR not in required:
                required.append(AgentType.CALENDAR)
            if AgentType.CONTENT not in required:
                required.append(AgentType.CONTENT)
        
        # Fallback: if no agents determined, use email as default
        if not required:
            required.append(AgentType.EMAIL)
            required.append(AgentType.CONTENT)
        
        return required
    
    def _assess_task_complexity(self, agents: List[AgentType], keywords: Dict[AgentType, List[str]], user_input: str) -> TaskComplexity:
        """Assess the complexity of the task based on multiple factors."""
        # Complexity indicators
        complexity_score = 0
        
        # Number of agents involved
        complexity_score += len(agents) * 2
        
        # Keyword density
        total_keywords = sum(len(kw_list) for kw_list in keywords.values())
        complexity_score += min(total_keywords, 10)
        
        # Complex operation indicators
        complex_indicators = [
            "and", "then", "after", "before", "while", "also", "plus",
            "schedule and send", "find and book", "check and reply"
        ]
        complexity_score += sum(2 for indicator in complex_indicators if indicator in user_input.lower())
        
        # Multi-step indicators
        multi_step_words = ["first", "then", "next", "finally", "after that"]
        complexity_score += sum(3 for word in multi_step_words if word in user_input.lower())
        
        # Determine complexity level
        if complexity_score <= 5:
            return TaskComplexity.SIMPLE
        elif complexity_score <= 10:
            return TaskComplexity.MODERATE
        elif complexity_score <= 15:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.ADVANCED
    
    def _determine_workflow_type(self, agents: List[AgentType]) -> Optional[WorkflowType]:
        """Determine workflow type based on required agents."""
        agent_set = set(agents)
        
        if agent_set == {AgentType.EMAIL}:
            return WorkflowType.EMAIL_ONLY
        elif agent_set == {AgentType.CALENDAR}:
            return WorkflowType.CALENDAR_ONLY
        elif agent_set == {AgentType.EMAIL, AgentType.CONTENT}:
            return WorkflowType.EMAIL_CONTENT
        elif agent_set == {AgentType.CALENDAR, AgentType.CONTENT}:
            return WorkflowType.CALENDAR_CONTENT
        elif agent_set == {AgentType.EMAIL, AgentType.CALENDAR}:
            return WorkflowType.EMAIL_CALENDAR
        elif len(agent_set) == 3:
            return WorkflowType.ALL_AGENTS
        else:
            return None
    
    def _find_workflow_template(self, intent: str, workflow_type: Optional[WorkflowType], complexity: TaskComplexity) -> Optional[str]:
        """Find matching workflow template."""
        if not workflow_type:
            return None
        
        # Intent to template mapping
        intent_mappings = {
            "schedule_and_invite": "schedule_meeting_and_send_invites",
            "email_to_calendar": "email_to_calendar_event",
            "availability_reply": "check_availability_and_reply",
            "fetch_emails": "fetch_and_summarize_emails",
            "summarize": "fetch_and_summarize_emails",
            "reply_email": "compose_intelligent_reply",
            "analyze_schedule": "analyze_schedule_patterns",
            "create_event": "create_detailed_event"
        }
        
        # Direct mapping
        if intent in intent_mappings:
            template_name = intent_mappings[intent]
            if template_name in self.workflow_templates:
                return template_name
        
        # Workflow type based selection
        type_templates = {
            WorkflowType.EMAIL_CALENDAR: ["schedule_meeting_and_send_invites", "email_to_calendar_event"],
            WorkflowType.EMAIL_CONTENT: ["fetch_and_summarize_emails", "compose_intelligent_reply"],
            WorkflowType.CALENDAR_CONTENT: ["analyze_schedule_patterns", "create_detailed_event"],
            WorkflowType.ALL_AGENTS: ["comprehensive_meeting_management", "intelligent_daily_planning"]
        }
        
        if workflow_type in type_templates:
            templates = type_templates[workflow_type]
            if templates:
                return templates[0]  # Return first matching template
        
        return None
    
    def _generate_execution_plan(
        self, 
        agents: List[AgentType], 
        template: Optional[str], 
        intent: str, 
        keywords: Dict[AgentType, List[str]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate execution plan for the task."""
        if template and template in self.workflow_templates:
            # Use predefined template
            return {
                "type": "template",
                "template_name": template,
                "steps": self.workflow_templates[template]["steps"],
                "coordination": self.workflow_templates[template]["coordination"]
            }
        else:
            # Generate custom execution plan
            return self._generate_custom_execution_plan(agents, intent, keywords, context)
    
    def _generate_custom_execution_plan(
        self, 
        agents: List[AgentType], 
        intent: str, 
        keywords: Dict[AgentType, List[str]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate custom execution plan when no template matches."""
        steps = []
        
        # Simple sequential execution based on typical patterns
        if AgentType.EMAIL in agents and AgentType.CALENDAR in agents:
            # Email + Calendar workflow
            if "schedule" in intent or "meeting" in intent:
                steps = [
                    {"agent": AgentType.CALENDAR, "action": "check_availability", "parallel": False},
                    {"agent": AgentType.CALENDAR, "action": "create_event", "parallel": False},
                    {"agent": AgentType.EMAIL, "action": "send_notification", "parallel": False}
                ]
            elif "email" in intent:
                steps = [
                    {"agent": AgentType.EMAIL, "action": "process_emails", "parallel": False},
                    {"agent": AgentType.CALENDAR, "action": "extract_dates", "parallel": False}
                ]
        
        elif AgentType.EMAIL in agents and AgentType.CONTENT in agents:
            # Email + Content workflow
            steps = [
                {"agent": AgentType.EMAIL, "action": "fetch_emails", "parallel": False},
                {"agent": AgentType.CONTENT, "action": "process_content", "parallel": False}
            ]
        
        elif AgentType.CALENDAR in agents and AgentType.CONTENT in agents:
            # Calendar + Content workflow
            steps = [
                {"agent": AgentType.CALENDAR, "action": "get_calendar_data", "parallel": False},
                {"agent": AgentType.CONTENT, "action": "analyze_schedule", "parallel": False}
            ]
        
        # Fallback: single agent execution
        if not steps and agents:
            primary_agent = agents[0]
            steps = [{"agent": primary_agent, "action": "process_request", "parallel": False}]
        
        return {
            "type": "custom",
            "steps": steps,
            "coordination": "sequential"
        }
    
    def _get_fallback_analysis(self, user_input: str) -> Dict[str, Any]:
        """Provide fallback analysis when main analysis fails."""
        return {
            "primary_intent": "general_assistance",
            "detected_keywords": {agent.value: [] for agent in AgentType},
            "required_agents": ["email_agent", "content_agent"],
            "workflow_type": "email_content",
            "complexity": "simple",
            "workflow_template": None,
            "execution_plan": {
                "type": "fallback",
                "steps": [{"agent": AgentType.EMAIL, "action": "process_request", "parallel": False}],
                "coordination": "sequential"
            },
            "estimated_steps": 1,
            "parallel_possible": False,
            "context_coordination_needed": False,
            "error": "Analysis failed, using fallback"
        }
    
    # =============================================================================
    # Task Delegation and Execution
    # =============================================================================
    
    async def delegate_task(
        self, 
        analysis: Dict[str, Any], 
        user_input: str, 
        context: Dict[str, Any],
        available_agents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delegate task to appropriate agents based on analysis.
        Enhanced for 3-agent coordination.
        
        Args:
            analysis: Result from analyze_user_request
            user_input: Original user input
            context: Session context
            available_agents: Dictionary of available agent instances
            
        Returns:
            Delegation result with agent responses
        """
        try:
            execution_plan = analysis.get("execution_plan", {})
            steps = execution_plan.get("steps", [])
            coordination_type = execution_plan.get("coordination", "sequential")
            
            if not steps:
                return {"success": False, "error": "No execution steps defined"}
            
            self.logger.info(f"Executing {len(steps)} steps with {coordination_type} coordination")
            
            # Execute based on coordination type
            if coordination_type == "sequential":
                return await self._execute_sequential_workflow(steps, user_input, context, available_agents)
            elif coordination_type == "parallel":
                return await self._execute_parallel_workflow(steps, user_input, context, available_agents)
            elif coordination_type == "mixed":
                return await self._execute_mixed_workflow(steps, user_input, context, available_agents)
            else:
                return await self._execute_sequential_workflow(steps, user_input, context, available_agents)
            
        except Exception as e:
            self.logger.error(f"Error in task delegation: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_attempted": False
            }
    
    async def _execute_sequential_workflow(
        self, 
        steps: List[Dict[str, Any]], 
        user_input: str, 
        context: Dict[str, Any], 
        available_agents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow steps sequentially."""
        results = []
        accumulated_context = context.copy()
        
        for i, step in enumerate(steps):
            try:
                agent_type = step["agent"]
                action = step["action"]
                
                # Get agent instance
                agent_key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)
                agent = available_agents.get(agent_key)
                
                if not agent:
                    self.logger.warning(f"Agent {agent_key} not available, skipping step {i+1}")
                    continue
                
                # Prepare agent input based on step and accumulated context
                agent_input = self._prepare_agent_input(step, user_input, accumulated_context, results)
                
                self.logger.info(f"Step {i+1}: Executing {action} on {agent_key}")
                
                # Execute agent action
                agent_result = await self._execute_agent_action(agent, agent_input, accumulated_context)
                
                # Process and store result
                step_result = {
                    "step": i + 1,
                    "agent": agent_key,
                    "action": action,
                    "success": agent_result.get("success", False),
                    "result": agent_result,
                    "execution_time": agent_result.get("execution_time", 0)
                }
                
                results.append(step_result)
                
                # Update accumulated context with results
                accumulated_context = self._update_context_with_result(
                    accumulated_context, agent_key, agent_result
                )
                
                # Stop on failure if critical step
                if not agent_result.get("success", False) and step.get("critical", False):
                    self.logger.warning(f"Critical step {i+1} failed, stopping workflow")
                    break
                
            except Exception as e:
                self.logger.error(f"Error in step {i+1}: {e}")
                results.append({
                    "step": i + 1,
                    "agent": agent_key,
                    "action": action,
                    "success": False,
                    "error": str(e)
                })
        
        return self._compile_workflow_results(results, "sequential")
    
    async def _execute_parallel_workflow(
        self, 
        steps: List[Dict[str, Any]], 
        user_input: str, 
        context: Dict[str, Any], 
        available_agents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow steps in parallel."""
        tasks = []
        
        for i, step in enumerate(steps):
            agent_type = step["agent"]
            agent_key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)
            agent = available_agents.get(agent_key)
            
            if agent:
                agent_input = self._prepare_agent_input(step, user_input, context, [])
                task = self._execute_agent_action_with_metadata(agent, agent_input, context, i+1, agent_key, step["action"])
                tasks.append(task)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "step": i + 1,
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return self._compile_workflow_results(processed_results, "parallel")
    
    async def _execute_mixed_workflow(
        self, 
        steps: List[Dict[str, Any]], 
        user_input: str, 
        context: Dict[str, Any], 
        available_agents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow with mixed parallel and sequential steps."""
        results = []
        accumulated_context = context.copy()
        
        # Group steps by parallel batches
        batches = self._group_steps_into_batches(steps)
        
        for batch_index, batch in enumerate(batches):
            if len(batch) == 1:
                # Sequential step
                step = batch[0]
                agent_type = step["agent"]
                agent_key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)
                agent = available_agents.get(agent_key)
                
                if agent:
                    agent_input = self._prepare_agent_input(step, user_input, accumulated_context, results)
                    agent_result = await self._execute_agent_action(agent, agent_input, accumulated_context)
                    
                    step_result = {
                        "batch": batch_index + 1,
                        "step": step.get("step_id", len(results) + 1),
                        "agent": agent_key,
                        "action": step["action"],
                        "success": agent_result.get("success", False),
                        "result": agent_result,
                        "execution_time": agent_result.get("execution_time", 0)
                    }
                    
                    results.append(step_result)
                    accumulated_context = self._update_context_with_result(
                        accumulated_context, agent_key, agent_result
                    )
            else:
                # Parallel batch
                tasks = []
                for step in batch:
                    agent_type = step["agent"]
                    agent_key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)
                    agent = available_agents.get(agent_key)
                    
                    if agent:
                        agent_input = self._prepare_agent_input(step, user_input, accumulated_context, results)
                        task = self._execute_agent_action_with_metadata(
                            agent, agent_input, accumulated_context, 
                            step.get("step_id", len(results) + 1), agent_key, step["action"]
                        )
                        tasks.append(task)
                
                # Execute parallel batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process batch results
                for result in batch_results:
                    if isinstance(result, Exception):
                        results.append({
                            "batch": batch_index + 1,
                            "success": False,
                            "error": str(result)
                        })
                    else:
                        results.append({**result, "batch": batch_index + 1})
        
        return self._compile_workflow_results(results, "mixed")
    
    def _group_steps_into_batches(self, steps: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group steps into parallel batches based on parallel flag."""
        batches = []
        current_batch = []
        
        for i, step in enumerate(steps):
            step["step_id"] = i + 1
            
            if step.get("parallel", False):
                current_batch.append(step)
                # If next step is not parallel or this is the last step, close batch
                if i == len(steps) - 1 or not steps[i + 1].get("parallel", False):
                    if current_batch:
                        batches.append(current_batch)
                        current_batch = []
            else:
                # Close any current parallel batch
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                # Add sequential step as single-item batch
                batches.append([step])
        
        return batches
    
    async def _execute_agent_action_with_metadata(
        self, 
        agent: Any, 
        agent_input: str, 
        context: Dict[str, Any], 
        step_id: int, 
        agent_key: str, 
        action: str
    ) -> Dict[str, Any]:
        """Execute agent action and return with metadata."""
        try:
            agent_result = await self._execute_agent_action(agent, agent_input, context)
            return {
                "step": step_id,
                "agent": agent_key,
                "action": action,
                "success": agent_result.get("success", False),
                "result": agent_result,
                "execution_time": agent_result.get("execution_time", 0)
            }
        except Exception as e:
            return {
                "step": step_id,
                "agent": agent_key,
                "action": action,
                "success": False,
                "error": str(e)
            }
    
    def _prepare_agent_input(
        self, 
        step: Dict[str, Any], 
        original_input: str, 
        context: Dict[str, Any], 
        previous_results: List[Dict[str, Any]]
    ) -> str:
        """Prepare input for agent based on step, context, and previous results."""
        action = step["action"]
        agent_type = step["agent"]
        
        # Base input from original user request
        agent_input = original_input
        
        # Action-specific input preparation
        if action in ["summarize_content", "analyze_content"]:
            # Content agent needs content to process
            if previous_results:
                for result in previous_results:
                    if result.get("agent") == "email_agent" and result.get("success"):
                        emails = result.get("result", {}).get("emails", [])
                        if emails:
                            agent_input = f"Summarize these emails: {json.dumps(emails[:3])}"
                            break
        
        elif action in ["send_invites", "send_notification"]:
            # Email agent needs event details from calendar
            if previous_results:
                for result in previous_results:
                    if result.get("agent") == "calendar_agent" and result.get("success"):
                        event_data = result.get("result", {})
                        agent_input = f"Send invitations for: {json.dumps(event_data)}"
                        break
        
        elif action in ["create_event", "schedule_meeting"]:
            # Calendar agent may need details from email or content processing
            email_context = context.get("current_email_context", {})
            if email_context:
                agent_input = f"{original_input} (Context: {json.dumps(email_context)})"
        
        elif action in ["extract_meeting_details", "extract_dates"]:
            # Extract specific information for calendar operations
            agent_input = f"Extract meeting/date information from: {original_input}"
        
        # Add relevant context
        agent_key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)
        if agent_key == "email_agent":
            email_context = context.get("current_email_context", {})
            if email_context:
                agent_input += f" [Email Context: {json.dumps(email_context)}]"
        
        elif agent_key == "calendar_agent":
            calendar_context = context.get("current_calendar_context", {})
            if calendar_context:
                agent_input += f" [Calendar Context: {json.dumps(calendar_context)}]"
        
        return agent_input
    
    async def _execute_agent_action(self, agent: Any, agent_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action on specific agent."""
        try:
            start_time = datetime.utcnow()
            
            # Execute agent (assuming agent has async generate method)
            if hasattr(agent, 'generate'):
                response = await agent.generate(agent_input)
            elif hasattr(agent, 'run'):
                response = await agent.run(agent_input)
            else:
                # Fallback: try calling agent directly
                response = await agent(agent_input)
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "response": response,
                "execution_time": execution_time,
                "agent_output": response
            }
            
        except Exception as e:
            self.logger.error(f"Agent execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0
            }
    
    def _update_context_with_result(
        self, 
        context: Dict[str, Any], 
        agent_key: str, 
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update context with agent result for next steps."""
        updated_context = context.copy()
        
        # Update agent-specific context
        if agent_key == "email_agent" and result.get("success"):
            email_context = updated_context.setdefault("current_email_context", {})
            agent_response = result.get("response", {})
            
            # Extract relevant email information
            if "emails" in str(agent_response):
                email_context["last_email_fetch"] = datetime.utcnow().isoformat()
                email_context["emails_processed"] = True
        
        elif agent_key == "calendar_agent" and result.get("success"):
            calendar_context = updated_context.setdefault("current_calendar_context", {})
            agent_response = result.get("response", {})
            
            # Extract relevant calendar information
            if "event" in str(agent_response) or "meeting" in str(agent_response):
                calendar_context["last_calendar_action"] = datetime.utcnow().isoformat()
                calendar_context["events_processed"] = True
        
        elif agent_key == "content_agent" and result.get("success"):
            content_context = updated_context.setdefault("current_content_context", {})
            agent_response = result.get("response", {})
            
            # Extract content processing results
            if "summary" in str(agent_response) or "analysis" in str(agent_response):
                content_context["last_content_processing"] = datetime.utcnow().isoformat()
                content_context["content_processed"] = True
        
        # Update workflow coordination data
        workflow_data = updated_context.setdefault("workflow_coordination", {})
        workflow_data[f"{agent_key}_last_result"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "success": result.get("success", False),
            "result_summary": str(result.get("response", ""))[:200]
        }
        
        return updated_context
    
    def _compile_workflow_results(self, results: List[Dict[str, Any]], coordination_type: str) -> Dict[str, Any]:
        """Compile final workflow results."""
        successful_steps = [r for r in results if r.get("success", False)]
        failed_steps = [r for r in results if not r.get("success", False)]
        
        total_execution_time = sum(r.get("execution_time", 0) for r in results)
        
        # Generate final response based on results
        final_response = self._generate_final_response(successful_steps, failed_steps)
        
        return {
            "success": len(successful_steps) > 0,
            "total_steps": len(results),
            "successful_steps": len(successful_steps),
            "failed_steps": len(failed_steps),
            "coordination_type": coordination_type,
            "total_execution_time_ms": total_execution_time,
            "final_response": final_response,
            "detailed_results": results,
            "workflow_summary": self._generate_workflow_summary(results, coordination_type)
        }
    
    def _generate_final_response(self, successful_steps: List[Dict[str, Any]], failed_steps: List[Dict[str, Any]]) -> str:
        """Generate final user-facing response based on workflow results."""
        if not successful_steps and failed_steps:
            return "I apologize, but I encountered issues completing your request. Please try again or provide more specific instructions."
        
        if not successful_steps:
            return "I wasn't able to complete any part of your request. Please check your instructions and try again."
        
        # Extract key information from successful steps
        response_parts = []
        
        for step in successful_steps:
            agent = step.get("agent", "")
            result = step.get("result", {})
            agent_response = result.get("response", "")
            
            if agent == "email_agent":
                if "emails" in str(agent_response).lower():
                    response_parts.append("Retrieved your emails successfully.")
                elif "sent" in str(agent_response).lower():
                    response_parts.append("Email sent successfully.")
            
            elif agent == "calendar_agent":
                if "event" in str(agent_response).lower():
                    response_parts.append("Calendar event processed successfully.")
                elif "available" in str(agent_response).lower():
                    response_parts.append("Checked your availability.")
            
            elif agent == "content_agent":
                if "summary" in str(agent_response).lower():
                    response_parts.append("Generated content summary.")
                elif "analysis" in str(agent_response).lower():
                    response_parts.append("Completed content analysis.")
        
        if failed_steps:
            response_parts.append(f"Note: {len(failed_steps)} step(s) had issues but the main task was completed.")
        
        return " ".join(response_parts) if response_parts else "Task completed successfully."
    
    def _generate_workflow_summary(self, results: List[Dict[str, Any]], coordination_type: str) -> Dict[str, Any]:
        """Generate workflow execution summary."""
        agents_used = list(set(r.get("agent", "") for r in results))
        actions_performed = [f"{r.get('agent', '')}: {r.get('action', '')}" for r in results if r.get("success")]
        
        return {
            "coordination_type": coordination_type,
            "agents_involved": agents_used,
            "total_agents": len(agents_used),
            "actions_completed": actions_performed,
            "execution_pattern": "parallel" if coordination_type == "parallel" else "sequential",
            "workflow_efficiency": len([r for r in results if r.get("success", False)]) / len(results) if results else 0
        }
    
    # =============================================================================
    # Context Coordination and State Management
    # =============================================================================
    
    def coordinate_agent_contexts(
        self, 
        session_context: Dict[str, Any], 
        workflow_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate contexts between agents after workflow execution.
        Ensures all agents have consistent view of session state.
        
        Args:
            session_context: Current session context
            workflow_results: Results from workflow execution
            
        Returns:
            Updated session context with coordinated agent states
        """
        try:
            updated_context = session_context.copy()
            
            # Extract successful results by agent
            successful_results = {}
            for result in workflow_results.get("detailed_results", []):
                if result.get("success", False):
                    agent = result.get("agent", "")
                    if agent not in successful_results:
                        successful_results[agent] = []
                    successful_results[agent].append(result)
            
            # Update email context
            if "email_agent" in successful_results:
                email_context = updated_context.setdefault("current_email_context", {})
                self._update_email_context_from_results(email_context, successful_results["email_agent"])
            
            # Update calendar context
            if "calendar_agent" in successful_results:
                calendar_context = updated_context.setdefault("current_calendar_context", {})
                self._update_calendar_context_from_results(calendar_context, successful_results["calendar_agent"])
            
            # Update content context
            if "content_agent" in successful_results:
                content_context = updated_context.setdefault("current_content_context", {})
                self._update_content_context_from_results(content_context, successful_results["content_agent"])
            
            # Update agent coordination metadata
            coordination_meta = updated_context.setdefault("agent_coordination", {})
            coordination_meta.update({
                "last_workflow_execution": datetime.utcnow().isoformat(),
                "workflow_type": workflow_results.get("coordination_type", "unknown"),
                "agents_involved": workflow_results.get("workflow_summary", {}).get("agents_involved", []),
                "last_workflow_success": workflow_results.get("success", False)
            })
            
            self.logger.info(f"Coordinated contexts for {len(successful_results)} agents")
            return updated_context
            
        except Exception as e:
            self.logger.error(f"Error coordinating agent contexts: {e}")
            return session_context
    
    def _update_email_context_from_results(self, email_context: Dict[str, Any], email_results: List[Dict[str, Any]]):
        """Update email context based on email agent results."""
        for result in email_results:
            action = result.get("action", "")
            agent_response = result.get("result", {}).get("response", "")
            
            if "fetch" in action or "get" in action:
                email_context["last_email_fetch"] = datetime.utcnow().isoformat()
                email_context["fetch_successful"] = True
            
            elif "send" in action:
                email_context["last_email_sent"] = datetime.utcnow().isoformat()
                email_context["send_successful"] = True
            
            elif "reply" in action:
                email_context["last_reply_sent"] = datetime.utcnow().isoformat()
                email_context["reply_successful"] = True
    
    def _update_calendar_context_from_results(self, calendar_context: Dict[str, Any], calendar_results: List[Dict[str, Any]]):
        """Update calendar context based on calendar agent results."""
        for result in calendar_results:
            action = result.get("action", "")
            agent_response = result.get("result", {}).get("response", "")
            
            if "create" in action or "schedule" in action:
                calendar_context["last_event_created"] = datetime.utcnow().isoformat()
                calendar_context["event_creation_successful"] = True
            
            elif "check" in action or "availability" in action:
                calendar_context["last_availability_check"] = datetime.utcnow().isoformat()
                calendar_context["availability_check_successful"] = True
            
            elif "find" in action or "free" in action:
                calendar_context["last_free_time_search"] = datetime.utcnow().isoformat()
                calendar_context["free_time_search_successful"] = True
    
    def _update_content_context_from_results(self, content_context: Dict[str, Any], content_results: List[Dict[str, Any]]):
        """Update content context based on content agent results."""
        for result in content_results:
            action = result.get("action", "")
            agent_response = result.get("result", {}).get("response", "")
            
            if "summarize" in action:
                content_context["last_summarization"] = datetime.utcnow().isoformat()
                content_context["summarization_successful"] = True
            
            elif "analyze" in action:
                content_context["last_analysis"] = datetime.utcnow().isoformat()
                content_context["analysis_successful"] = True
            
            elif "generate" in action:
                content_context["last_generation"] = datetime.utcnow().isoformat()
                content_context["generation_successful"] = True
    
    # =============================================================================
    # Multi-Agent Workflow Templates
    # =============================================================================
    
    def get_available_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get all available workflow templates."""
        return {
            name: {
                "description": template.get("description", ""),
                "agents": [agent.value for agent in template.get("agents", [])],
                "complexity": template.get("complexity", TaskComplexity.SIMPLE).value,
                "estimated_steps": len(template.get("steps", [])),
                "coordination_type": template.get("coordination", "sequential")
            }
            for name, template in self.workflow_templates.items()
        }
    
    def validate_workflow_feasibility(self, workflow_name: str, available_agents: List[str]) -> Dict[str, Any]:
        """Validate if a workflow can be executed with available agents."""
        if workflow_name not in self.workflow_templates:
            return {"feasible": False, "reason": "Workflow template not found"}
        
        template = self.workflow_templates[workflow_name]
        required_agents = set()
        
        for step in template.get("steps", []):
            agent_type = step["agent"]
            agent_key = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)
            required_agents.add(agent_key)
        
        missing_agents = required_agents - set(available_agents)
        
        return {
            "feasible": len(missing_agents) == 0,
            "required_agents": list(required_agents),
            "missing_agents": list(missing_agents),
            "workflow_complexity": template.get("complexity", TaskComplexity.SIMPLE).value
        }
    
    # =============================================================================
    # Performance and Monitoring
    # =============================================================================
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics."""
        return {
            "total_workflow_templates": len(self.workflow_templates),
            "supported_workflow_types": [wt.value for wt in WorkflowType],
            "supported_complexities": [tc.value for tc in TaskComplexity],
            "agent_types_supported": len(AgentType),
            "coordination_patterns": ["sequential", "parallel", "mixed"],
            "version": "3.0_enhanced"
        }


# =============================================================================
# Global Orchestration Instance
# =============================================================================

# Create global orchestration instance for coordinator agent
coordinator_orchestration = CoordinatorOrchestration()


# =============================================================================
# Export Functions for Coordinator Agent
# =============================================================================

def analyze_request(user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Analyze user request for agent delegation."""
    return coordinator_orchestration.analyze_user_request(user_input, context)


async def delegate_to_agents(
    analysis: Dict[str, Any], 
    user_input: str, 
    context: Dict[str, Any],
    available_agents: Dict[str, Any]
) -> Dict[str, Any]:
    """Delegate task to appropriate agents."""
    return await coordinator_orchestration.delegate_task(analysis, user_input, context, available_agents)


def coordinate_contexts(session_context: Dict[str, Any], workflow_results: Dict[str, Any]) -> Dict[str, Any]:
    """Coordinate agent contexts after workflow execution."""
    return coordinator_orchestration.coordinate_agent_contexts(session_context, workflow_results)


def get_workflow_templates() -> Dict[str, Dict[str, Any]]:
    """Get available workflow templates."""
    return coordinator_orchestration.get_available_workflows()


def validate_workflow(workflow_name: str, available_agents: List[str]) -> Dict[str, Any]:
    """Validate workflow feasibility."""
    return coordinator_orchestration.validate_workflow_feasibility(workflow_name, available_agents)


# =============================================================================
# Testing and Development Utilities
# =============================================================================

def test_orchestration():
    """Test orchestration functionality."""
    print("🧪 Testing Enhanced Coordinator Orchestration (3-Agent Support)...")
    
    # Test 1: Request analysis
    test_requests = [
        "Check my emails and summarize them",
        "Schedule a meeting with John next Tuesday at 2 PM",
        "Find a free time slot this week and send calendar invite",
        "Check my schedule and reply to urgent emails",
        "Create a detailed event and send invitations to the team"
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. Testing: '{request}'")
        analysis = analyze_request(request)
        
        print(f"   Agents required: {analysis.get('required_agents', [])}")
        print(f"   Workflow type: {analysis.get('workflow_type', 'unknown')}")
        print(f"   Complexity: {analysis.get('complexity', 'unknown')}")
        print(f"   Steps: {analysis.get('estimated_steps', 0)}")
    
    # Test 2: Workflow templates
    print(f"\n📋 Available Workflow Templates:")
    templates = get_workflow_templates()
    for name, details in templates.items():
        print(f"   • {name}: {details['agents']} ({details['complexity']})")
    
    # Test 3: Metrics
    print(f"\n📊 Orchestration Metrics:")
    metrics = coordinator_orchestration.get_orchestration_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Enhanced Orchestration testing completed!")


if __name__ == "__main__":
    test_orchestration()