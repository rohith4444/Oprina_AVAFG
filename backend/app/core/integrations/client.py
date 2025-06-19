"""
Vertex AI Agent client for communicating with deployed Oprina agent.
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from vertexai import agent_engines
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class VertexAgentClient:
    """Client for communicating with deployed Vertex AI Agent."""
    
    def __init__(self):
        self._agent_app: Optional[Any] = None
        self._initialized = False
        self.settings = get_settings()
        self._agent_id = self.settings.VERTEX_AI_AGENT_ID
    
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
        """Create a new agent session with user context in state."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create the Vertex AI session
            session_response = self._agent_app.create_session(user_id=user_id)
            
            # Set initial session state with user context
            initial_state = {
                "user:id": user_id,
                "user:backend_url": self.settings.BACKEND_API_URL or "http://localhost:8000",
                "user:session_type": "multi_user",
                "gmail:connected": False,
                "calendar:connected": False,
            }
            
            # Update the session with initial state
            # Note: This may vary based on your Vertex AI agent implementation
            # If update_session_state doesn't exist, the session may already have the user_id accessible
            try:
                await self._agent_app.update_session_state(
                    session_id=session_response["id"],
                    state_updates=initial_state
                )
            except AttributeError:
                # If update_session_state method doesn't exist, log and continue
                # The user_id should still be accessible via session.user_id
                logger.info("Session state update method not available, relying on session.user_id")
            
            session_data = {
                "vertex_session_id": session_response["id"],
                "user_id": user_id,
                "status": "active"
            }
            
            logger.info(f"Created agent session {session_response['id']} for user {user_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create agent session for user {user_id}: {e}")

    
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
        
        # ADD THIS DEBUG LINE
        logger.info(f"🔍 DEBUG: Processing {len(events)} events")
        
        response_parts = []
        
        for i, event in enumerate(events):
            # ADD THIS DEBUG LINE  
            logger.info(f"🔍 DEBUG: Event {i} type: {type(event)}, content: {str(event)[:200]}...")
            
            extracted_text = self._extract_text_from_event(event)
            
            # ADD THIS DEBUG LINE
            logger.info(f"🔍 DEBUG: Extracted text: '{extracted_text}'")
            
            if extracted_text:
                response_parts.append(extracted_text)
        
        final_response = " ".join(response_parts).strip()
        
        # ADD THIS DEBUG LINE
        logger.info(f"🔍 DEBUG: Final response: '{final_response}'")
        
        return final_response

    def _extract_text_from_event(self, event) -> str:
        """Extract clean text from various event formats."""
        try:
            # Handle string events
            if isinstance(event, str):
                return event
            
            # Handle dict events
            if isinstance(event, dict):
                # NEW: Handle nested content structure
                if 'content' in event and isinstance(event['content'], dict):
                    content = event['content']
                    if 'parts' in content and isinstance(content['parts'], list):
                        text_parts = []
                        for part in content['parts']:
                            if isinstance(part, dict) and 'text' in part:
                                text_parts.append(str(part['text']))
                        if text_parts:
                            return " ".join(text_parts).strip()
                
                # Check for direct 'content' field
                if 'content' in event:
                    return str(event['content'])
                
                # Check for 'text' field  
                if 'text' in event:
                    return str(event['text'])
                
                # Check for direct 'parts' structure
                if 'parts' in event:
                    text_parts = []
                    for part in event['parts']:
                        if isinstance(part, dict) and 'text' in part:
                            text_parts.append(str(part['text']))
                    if text_parts:
                        return " ".join(text_parts).strip()
            
            # Handle objects with attributes
            if hasattr(event, 'content'):
                content = event.content
                # If content has parts
                if hasattr(content, 'parts'):
                    text_parts = []
                    for part in content.parts:
                        if hasattr(part, 'text'):
                            text_parts.append(str(part.text))
                    if text_parts:
                        return " ".join(text_parts).strip()
                else:
                    return str(content)
            
            # Handle objects with text attribute
            if hasattr(event, 'text'):
                return str(event.text)
            
            # Handle objects with parts attribute
            if hasattr(event, 'parts'):
                text_parts = []
                for part in event.parts:
                    if hasattr(part, 'text'):
                        text_parts.append(str(part.text))
                if text_parts:
                    return " ".join(text_parts).strip()
            
            return ""
            
        except Exception as e:
            logger.warning(f"Failed to extract text from event: {e}")
            return ""
    
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