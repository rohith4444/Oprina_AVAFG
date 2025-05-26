"""
Tool discovery and invocation for MCP modular tools.

This file provides the discovery and invocation logic for all registered MCP tools.
- Imports all tool modules (e.g., gmail_tools) to ensure registration.
- Allows the backend and ADK agent to list available tools and call them by name.
- The agent uses list_tools() to discover capabilities and run_tool() to invoke tools with arguments.
"""
from mcp.mcp_tool import TOOL_REGISTRY
import mcp.gmail_tools  # Ensure all Gmail tools are registered

def list_tools():
    """
    Return a list of all registered tool names and descriptions.
    Used by the backend and agent to discover available capabilities.
    """
    return [
        {"name": cls.name, "description": cls.description}
        for cls in TOOL_REGISTRY.values()
    ]

def run_tool(tool_name, **kwargs):
    """
    Instantiate and run a tool by name with given arguments.
    Used by the backend and agent to invoke a tool dynamically.
    Args:
        tool_name (str): The registered name of the tool class (e.g., 'gmail_list_messages')
        **kwargs: Arguments to pass to the tool's run() method
    Returns:
        The result of the tool's run() method
    Raises:
        ValueError: If the tool is not found in the registry
    """
    tool_cls = TOOL_REGISTRY.get(tool_name)
    if not tool_cls:
        raise ValueError(f"Tool '{tool_name}' not found.")
    tool = tool_cls()
    return tool.run(**kwargs)

print('Registered tools:', list(TOOL_REGISTRY.keys())) 