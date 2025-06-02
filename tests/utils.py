"""Testing utilities and helpers"""
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock

class TestUtils:
    """Utilities for testing"""
    
    @staticmethod
    def create_mock_events(count: int = 3) -> List[Dict[str, Any]]:
        """Create mock ADK events for testing"""
        events = []
        for i in range(count):
            events.append({
                "author": f"test_agent_{i}",
                "content": f"Test content {i}",
                "timestamp": 1234567890 + i,
                "is_final": i == count - 1
            })
        return events
    
    @staticmethod
    async def run_async_test(coro):
        """Helper for running async tests"""
        return await coro
    
    @staticmethod
    def assert_session_state_updated(session_state: Dict, expected_keys: List[str]):
        """Assert session state has expected keys"""
        for key in expected_keys:
            assert key in session_state, f"Expected key {key} not found in session state"
    
    @staticmethod
    def create_mock_adk_response(content: str, is_final: bool = True) -> Dict[str, Any]:
        """Create a mock ADK response"""
        return {
            "author": "test_agent",
            "content": content,
            "timestamp": 1234567890,
            "is_final": is_final
        }
    
    @staticmethod
    def create_mock_tool_result(tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock tool result"""
        return {
            "tool_name": tool_name,
            "result": result,
            "status": "success"
        }

# Export for easy import
__all__ = ["TestUtils"] 