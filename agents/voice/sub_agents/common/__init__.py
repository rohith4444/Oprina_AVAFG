"""
Common Components for Oprina Agents

Shared utilities and message types for agent communication.
"""

# Import core message types
from .message_types import (
    MessageType,
    AgentMessage,
    VoiceInput,
    EmailContext,
    TaskResult,
    create_voice_command_message,
    create_email_operation_message,
    validate_agent_message,
)

# Import essential tools
from .shared_tools import (
    update_session_state,
    update_agent_state,
    log_agent_action,
    handle_agent_error,
)

# Export the essentials
__all__ = [
    # Core message types
    "MessageType",
    "AgentMessage", 
    "VoiceInput",
    "EmailContext",
    "TaskResult",
    
    # Message helpers
    "create_voice_command_message",
    "create_email_operation_message", 
    "validate_agent_message",
    
    # Essential tools
    "update_session_state",
    "update_agent_state",
    "log_agent_action",
    "handle_agent_error",
]