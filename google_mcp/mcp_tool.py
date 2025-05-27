"""
Base Tool class and registry for MCP modular tools.

This file defines the core registry and base class for all modular tools in the MCP system.
- Tools are registered using the @register_tool decorator.
- The registry is used by the discovery system (see mcp_discovery.py) to list and invoke tools.
- The ADK agent and backend interact with tools via this registry and discovery system.
"""

# Global registry for all MCP tools
TOOL_REGISTRY = {}

def register_tool(cls):
    """
    Decorator to register a tool class in the MCP registry.
    Usage: decorate any Tool subclass with @register_tool to make it discoverable and callable.
    """
    TOOL_REGISTRY[cls.name] = cls
    return cls

class Tool:
    """
    Base class for all MCP tools.
    Each tool should define a unique name, description, and implement the run() method.
    Tools can be discovered and invoked via the registry (see mcp_discovery.py).
    """
    name = None
    description = None
    def __init__(self, **kwargs):
        self.config = kwargs
    def run(self, *args, **kwargs):
        raise NotImplementedError("Each tool must implement a run method.") 