"""
Shared Tools for Oprina Agents

This module provides common tools and utilities that can be used across
all agents in the Oprina system for consistent functionality.

Key Components:
- Memory Management Tools
- Session State Tools  
- Message Processing Tools
- Error Handling Tools
- Validation Tools
"""

import sys
import os
import uuid
import time
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from google.adk.tools.tool_context import ToolContext
from memory.memory_manager import MemoryManager
from services.logging.logger import setup_logger

# Import message types
from .message_types import (
    AgentMessage, MessageType, TaskResult, ResponseMetadata,
    validate_agent_message
)


# =============================================================================
# Memory Management Tools
# =============================================================================

def update_session_state(
    user_id: str,
    session_id: str,
    updates: Dict[str, Any],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to update session state from any agent.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        updates: State updates to apply
        tool_context: ADK tool context
        
    Returns:
        Result dictionary with success status
    """
    try:
        # Get memory manager instance
        memory_manager = MemoryManager()
        
        # Update session state
        success = memory_manager.update_session_context(user_id, session_id, updates)
        
        if success:
            # Update tool context state for immediate access
            for key, value in updates.items():
                tool_context.state[key] = value
        
        return {
            "success": success,
            "message": "Session state updated successfully" if success else "Failed to update session state",
            "updated_keys": list(updates.keys())
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating session state: {str(e)}",
            "error_type": type(e).__name__
        }


def get_session_context(
    user_id: str,
    session_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to get comprehensive session context.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Session context data
    """
    try:
        # Get memory manager instance
        memory_manager = MemoryManager()
        
        # Get session context
        context = memory_manager.get_session_context(user_id, session_id)
        
        return {
            "success": True,
            "context": context or {},
            "message": "Session context retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "context": {},
            "message": f"Error retrieving session context: {str(e)}",
            "error_type": type(e).__name__
        }


def update_agent_state(
    agent_name: str,
    agent_state: Dict[str, Any],
    session_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to update agent state in session memory.
    
    Args:
        agent_name: Name of the agent
        agent_state: Agent state updates
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Result dictionary
    """
    try:
        # Get memory manager instance
        memory_manager = MemoryManager()
        
        # Update agent state
        success = memory_manager.set_agent_coordination_data(
            session_id, agent_name, agent_state, persistent=True
        )
        
        return {
            "success": success,
            "message": f"Agent state updated for {agent_name}" if success else f"Failed to update agent state for {agent_name}",
            "agent_name": agent_name,
            "updated_keys": list(agent_state.keys())
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating agent state: {str(e)}",
            "error_type": type(e).__name__
        }


def store_conversation_message(
    message_type: str,
    content: str,
    user_id: str,
    session_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Tool to store conversation messages in chat history.
    
    Args:
        message_type: Type of message (user_voice, agent_response, etc.)
        content: Message content
        user_id: User identifier
        session_id: Session identifier
        metadata: Additional message metadata
        tool_context: ADK tool context
        
    Returns:
        Result dictionary with message ID
    """
    try:
        # Get memory manager instance
        memory_manager = MemoryManager()
        
        # Store message
        message_id = memory_manager.store_conversation_message(
            user_id, session_id, message_type, content, metadata
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "message": "Conversation message stored successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message_id": None,
            "message": f"Error storing conversation message: {str(e)}",
            "error_type": type(e).__name__
        }


# =============================================================================
# Email Context Tools
# =============================================================================

def update_email_context(
    email_context: Dict[str, Any],
    user_id: str,
    session_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to update email context in session state.
    
    Args:
        email_context: Email context updates
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Result dictionary
    """
    try:
        # Get memory manager instance
        memory_manager = MemoryManager()
        
        # Update email context
        success = memory_manager.update_email_context_across_services(
            user_id, session_id, email_context
        )
        
        # Also update tool context for immediate access
        if success:
            current_email_context = tool_context.state.get("current_email_context", {})
            current_email_context.update(email_context)
            tool_context.state["current_email_context"] = current_email_context
        
        return {
            "success": success,
            "message": "Email context updated successfully" if success else "Failed to update email context",
            "updated_keys": list(email_context.keys())
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating email context: {str(e)}",
            "error_type": type(e).__name__
        }


def get_email_context(
    user_id: str,
    session_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to get current email context.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Email context data
    """
    try:
        # Get memory manager instance
        memory_manager = MemoryManager()
        
        # Get email context with full details
        email_data = memory_manager.get_user_emails_with_context(user_id, session_id)
        
        return {
            "success": True,
            "email_context": email_data,
            "message": "Email context retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "email_context": {},
            "message": f"Error retrieving email context: {str(e)}",
            "error_type": type(e).__name__
        }


# =============================================================================
# Message Processing Tools
# =============================================================================

def create_agent_message(
    sender: str,
    recipient: str,
    message_type: str,
    payload: Dict[str, Any],
    session_id: str,
    requires_response: bool = False,
    priority: str = "normal",
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Tool to create properly formatted AgentMessage.
    
    Args:
        sender: Sender agent name
        recipient: Recipient agent name
        message_type: Message type string
        payload: Message payload data
        session_id: Session identifier
        requires_response: Whether response is required
        priority: Message priority
        tool_context: ADK tool context
        
    Returns:
        Formatted message dictionary
    """
    try:
        # Convert string to MessageType enum
        msg_type = MessageType(message_type)
        
        # Create AgentMessage
        message = AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=msg_type,
            payload=payload,
            session_id=session_id,
            requires_response=requires_response,
            priority=priority
        )
        
        # Validate message
        validation_errors = validate_agent_message(message)
        if validation_errors:
            return {
                "success": False,
                "message": f"Message validation failed: {', '.join(validation_errors)}",
                "errors": validation_errors
            }
        
        return {
            "success": True,
            "message": message.to_dict(),
            "message_id": message.message_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating agent message: {str(e)}",
            "error_type": type(e).__name__
        }


def log_agent_action(
    agent_name: str,
    action: str,
    details: Dict[str, Any],
    session_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to log agent actions for debugging and monitoring.
    
    Args:
        agent_name: Name of the agent performing action
        action: Action being performed
        details: Action details and parameters
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Log result
    """
    try:
        # Set up logger for the agent
        logger = setup_logger(f"agent_{agent_name}", console_output=True)
        
        # Create log entry
        log_entry = {
            "agent": agent_name,
            "action": action,
            "details": details,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the action
        logger.info(f"Agent {agent_name} performing {action}: {details}")
        
        # Store in session state for tracking
        agent_logs = tool_context.state.get("agent_logs", [])
        agent_logs.append(log_entry)
        
        # Keep only last 50 log entries to prevent state bloat
        if len(agent_logs) > 50:
            agent_logs = agent_logs[-50:]
        
        tool_context.state["agent_logs"] = agent_logs
        
        return {
            "success": True,
            "message": "Action logged successfully",
            "log_entry": log_entry
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error logging action: {str(e)}",
            "error_type": type(e).__name__
        }


# =============================================================================
# Validation and Error Handling Tools
# =============================================================================

def validate_user_context(
    user_id: str,
    session_id: str,
    required_fields: List[str],
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to validate that required user context is available.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        required_fields: List of required field names in session state
        tool_context: ADK tool context
        
    Returns:
        Validation result
    """
    try:
        missing_fields = []
        
        # Check required fields in tool context state
        for field in required_fields:
            if field not in tool_context.state or not tool_context.state[field]:
                missing_fields.append(field)
        
        is_valid = len(missing_fields) == 0
        
        return {
            "success": is_valid,
            "valid": is_valid,
            "missing_fields": missing_fields,
            "message": "All required fields present" if is_valid else f"Missing required fields: {', '.join(missing_fields)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "valid": False,
            "message": f"Error validating user context: {str(e)}",
            "error_type": type(e).__name__
        }


def handle_agent_error(
    agent_name: str,
    error: Exception,
    context: Dict[str, Any],
    session_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to handle and log agent errors consistently.
    
    Args:
        agent_name: Name of the agent where error occurred
        error: The exception that occurred
        context: Additional error context
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Error handling result
    """
    try:
        # Create error entry
        error_entry = {
            "agent": agent_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the error
        logger = setup_logger(f"agent_{agent_name}", console_output=True)
        logger.error(f"Agent {agent_name} error: {error_entry}")
        
        # Store in session state for tracking
        agent_errors = tool_context.state.get("agent_errors", [])
        agent_errors.append(error_entry)
        
        # Keep only last 20 error entries
        if len(agent_errors) > 20:
            agent_errors = agent_errors[-20:]
        
        tool_context.state["agent_errors"] = agent_errors
        
        return {
            "success": True,
            "message": "Error logged and handled",
            "error_entry": error_entry,
            "suggested_action": _get_error_suggestion(error)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error handling error: {str(e)}",
            "error_type": type(e).__name__
        }


def _get_error_suggestion(error: Exception) -> str:
    """Get suggested action based on error type."""
    error_suggestions = {
        "ConnectionError": "Check network connectivity and service endpoints",
        "TimeoutError": "Retry with longer timeout or check service availability",
        "AuthenticationError": "Verify credentials and authentication status",
        "ValidationError": "Check input parameters and data format",
        "PermissionError": "Verify user permissions and access rights",
        "KeyError": "Check required data fields are present",
        "ValueError": "Validate input data types and ranges",
        "TypeError": "Check data type compatibility"
    }
    
    error_type = type(error).__name__
    return error_suggestions.get(error_type, "Review error details and retry operation")


# =============================================================================
# Performance and Timing Tools
# =============================================================================

def measure_performance(
    operation_name: str,
    agent_name: str,
    session_id: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Tool to start performance measurement for an operation.
    
    Args:
        operation_name: Name of the operation being measured
        agent_name: Name of the agent performing operation
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Performance tracking data
    """
    try:
        start_time = time.time()
        
        # Create performance entry
        perf_entry = {
            "operation": operation_name,
            "agent": agent_name,
            "session_id": session_id,
            "start_time": start_time,
            "start_timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in tool context for completion tracking
        performance_tracking = tool_context.state.get("performance_tracking", {})
        tracking_id = f"{agent_name}_{operation_name}_{start_time}"
        performance_tracking[tracking_id] = perf_entry
        tool_context.state["performance_tracking"] = performance_tracking
        
        return {
            "success": True,
            "tracking_id": tracking_id,
            "message": f"Performance tracking started for {operation_name}",
            "start_time": start_time
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error starting performance tracking: {str(e)}",
            "error_type": type(e).__name__
        }


def complete_performance_measurement(
    tracking_id: str,
    result_status: str,
    additional_metrics: Optional[Dict[str, Any]] = None,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Tool to complete performance measurement.
    
    Args:
        tracking_id: Performance tracking ID from measure_performance
        result_status: success/failure/partial
        additional_metrics: Additional performance metrics
        tool_context: ADK tool context
        
    Returns:
        Performance measurement results
    """
    try:
        performance_tracking = tool_context.state.get("performance_tracking", {})
        
        if tracking_id not in performance_tracking:
            return {
                "success": False,
                "message": f"Performance tracking ID {tracking_id} not found"
            }
        
        perf_entry = performance_tracking[tracking_id]
        end_time = time.time()
        duration_ms = (end_time - perf_entry["start_time"]) * 1000
        
        # Complete the performance entry
        perf_entry.update({
            "end_time": end_time,
            "end_timestamp": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
            "result_status": result_status,
            "additional_metrics": additional_metrics or {}
        })
        
        # Log performance
        logger = setup_logger(f"agent_{perf_entry['agent']}", console_output=True)
        logger.info(f"Performance: {perf_entry['operation']} completed in {duration_ms:.2f}ms with status {result_status}")
        
        # Store in performance history
        perf_history = tool_context.state.get("performance_history", [])
        perf_history.append(perf_entry)
        
        # Keep only last 30 performance entries
        if len(perf_history) > 30:
            perf_history = perf_history[-30:]
        
        tool_context.state["performance_history"] = perf_history
        
        # Remove from active tracking
        del performance_tracking[tracking_id]
        tool_context.state["performance_tracking"] = performance_tracking
        
        return {
            "success": True,
            "duration_ms": duration_ms,
            "performance_entry": perf_entry,
            "message": f"Performance measurement completed: {duration_ms:.2f}ms"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error completing performance measurement: {str(e)}",
            "error_type": type(e).__name__
        }


# =============================================================================
# User Preference and Adaptive Tools
# =============================================================================

def get_user_preferences(
    user_id: str,
    session_id: str,
    preference_category: Optional[str] = None,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Tool to get user preferences for adaptive behavior.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        preference_category: Specific preference category (optional)
        tool_context: ADK tool context
        
    Returns:
        User preferences data
    """
    try:
        # Get memory manager instance
        memory_manager = MemoryManager()
        
        # Get adaptive settings
        adaptive_settings = memory_manager.get_adaptive_agent_settings(user_id, {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Filter by category if specified
        if preference_category and preference_category in adaptive_settings:
            preferences = {preference_category: adaptive_settings[preference_category]}
        else:
            preferences = adaptive_settings
        
        return {
            "success": True,
            "preferences": preferences,
            "message": "User preferences retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "preferences": {},
            "message": f"Error retrieving user preferences: {str(e)}",
            "error_type": type(e).__name__
        }


def learn_from_interaction(
    user_id: str,
    interaction_type: str,
    interaction_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Tool to learn from user interactions for improved personalization.
    
    Args:
        user_id: User identifier
        interaction_type: Type of interaction (voice_command, email_action, etc.)
        interaction_data: Interaction data to learn from
        context: Additional context for learning
        tool_context: ADK tool context
        
    Returns:
        Learning result
    """
    try:
        # Get memory manager instance
        memory_manager = MemoryManager()
        
        # Learn from the interaction
        success = memory_manager.learn_from_user_action(
            user_id, interaction_type, interaction_data, context
        )
        
        return {
            "success": success,
            "message": "Learning from interaction completed" if success else "Learning failed",
            "interaction_type": interaction_type
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error learning from interaction: {str(e)}",
            "error_type": type(e).__name__
        }


# =============================================================================
# Utility Functions
# =============================================================================

def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request-response tracking."""
    return f"corr_{uuid.uuid4().hex[:12]}"


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO string."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()


def safe_get_nested_value(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    try:
        value = data
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# =============================================================================
# Export All Tools
# =============================================================================

__all__ = [
    # Memory Management Tools
    "update_session_state",
    "get_session_context", 
    "update_agent_state",
    "store_conversation_message",
    
    # Email Context Tools
    "update_email_context",
    "get_email_context",
    
    # Message Processing Tools
    "create_agent_message",
    "log_agent_action",
    
    # Validation and Error Handling Tools
    "validate_user_context",
    "handle_agent_error",
    
    # Performance Tools
    "measure_performance",
    "complete_performance_measurement",
    
    # User Preference Tools
    "get_user_preferences",
    "learn_from_interaction",
    
    # Utility Functions
    "generate_correlation_id",
    "format_timestamp",
    "safe_get_nested_value",
    "truncate_string",
]