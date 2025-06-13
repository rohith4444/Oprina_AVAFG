"""
Vertex AI Agent client for communicating with deployed Oprina agent.
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from vertexai import agent_engines
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class VertexAgentClient:
    """Client for communicating with deployed Vertex AI Agent."""
    
    def __init__(self):
        self._agent_app: Optional[Any] = None
        self._initialized = False
        self._agent_id = settings.VERTEX_AI_AGENT_ID
    
    async def initialize(self) -> None:
        """Initialize the agent client."""
        if self._initialized:
            return
        
        try:
            if not self._agent_id:
                raise ValueError("Vertex AI Agent ID must be configured")
            
            # Get the deployed agent directly by resource ID
            # The agent_engines.get() method handles project/location from the resource ID
            self._agent_app = agent_engines.get(self._agent_id)
            
            self._initialized = True
            logger.info(f"Agent client initialized for agent: {self._agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent client: {e}")
            raise
    
    async def create_session(self, user_id: str) -> Dict[str, Any]:
        """Create a new agent session for a user."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session_response = self._agent_app.create_session(user_id=user_id)
            
            session_data = {
                "vertex_session_id": session_response["id"],
                "user_id": user_id,
                "status": "active"
            }
            
            logger.info(f"Created agent session {session_response['id']} for user {user_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create agent session for user {user_id}: {e}")
            raise
    
    async def send_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """Send a message to the agent and get response."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Send message and get response
            response_events = []
            
            for event in self._agent_app.stream_query(
                user_id=user_id,
                session_id=session_id,
                message=message
            ):
                response_events.append(event)
            
            # Process the response events
            full_response = self._process_response_events(response_events)
            
            logger.info(f"Sent message to agent session {session_id}")
            
            return {
                "response": full_response,
                "session_id": session_id,
                "user_id": user_id,
                "message_sent": message
            }
            
        except Exception as e:
            logger.error(f"Failed to send message to agent: {e}")
            raise
    
    async def stream_message(
        self, 
        user_id: str, 
        session_id: str, 
        message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message to the agent and stream the response."""
        if not self._initialized:
            await self.initialize()
        
        try:
            for event in self._agent_app.stream_query(
                user_id=user_id,
                session_id=session_id,
                message=message
            ):
                yield {
                    "event": event,
                    "session_id": session_id,
                    "user_id": user_id
                }
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
            
            logger.info(f"Streamed message to agent session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to stream message to agent: {e}")
            raise
    
    def _process_response_events(self, events: list) -> str:
        """Process response events into a single response string."""
        response_parts = []
        
        for event in events:
            # Extract text content from event
            if hasattr(event, 'content'):
                response_parts.append(str(event.content))
            elif isinstance(event, dict) and 'content' in event:
                response_parts.append(str(event['content']))
            elif isinstance(event, str):
                response_parts.append(event)
            else:
                # Try to convert to string
                response_parts.append(str(event))
        
        return " ".join(response_parts).strip()
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy and responding."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Simple health check - just verify agent is accessible
            return self._agent_app is not None
            
        except Exception as e:
            logger.error(f"Agent health check failed: {e}")
            return False


# Global agent client instance
agent_client = VertexAgentClient() 