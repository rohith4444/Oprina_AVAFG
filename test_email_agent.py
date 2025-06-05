"""
Test script to verify the email agent functionality.
"""

import asyncio
import sys
import os
import logging
from agents.voice.sub_agents.coordinator.sub_agents.email.agent import create_email_agent
from google.adk.runner import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.events.event import Event, EventActions
from google.genai.types import Content, Part
from agents.common.tool_context import ToolContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_email_agent():
    """Test the email agent functionality."""
    print("[TEST] Testing Email Agent...")
    
    # Create the email agent
    email_agent = create_email_agent()
    print("[OK] Email agent created")
    
    # Create services
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    
    # Create runner
    runner = Runner(
        agent=email_agent,
        app_name="test_app",
        session_service=session_service,
        memory_service=memory_service
    )
    print("[OK] Runner created")
    
    # Create a session
    session = await session_service.create_session(app_name="test_app", user_id="test_user")
    print(f"[OK] Session created: {session}")
    
    # Create tool context
    tool_context = ToolContext(session=session, invocation_id="test_invocation")
    print(f"[OK] Tool context created: {tool_context}")
    
    # Test Gmail connection
    print("\nTesting Gmail connection...")
    response = await runner.run("Check my Gmail connection")
    print(f"Gmail connection response: {response}")
    
    # Test listing messages
    print("\nTesting Gmail message listing...")
    response = await runner.run("List my unread emails")
    print(f"Gmail message listing response: {response}")
    
    # Test searching messages
    print("\nTesting Gmail message searching...")
    response = await runner.run("Search for emails from Google")
    print(f"Gmail message searching response: {response}")
    
    print("\n[OK] Email agent test completed")

if __name__ == "__main__":
    asyncio.run(test_email_agent()) 