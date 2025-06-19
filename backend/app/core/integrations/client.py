"""
Vertex AI Agent client for communicating with deployed Oprina agent.
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from vertexai import agent_engines
from google import genai
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
        self._gemini_model: Optional[Any] = None

    def _setup_gemini(self):
        """One-time Gemini setup using new Gen AI SDK with Vertex AI."""
        try:
            
            
            # Get project and location from settings or environment
            project_id = getattr(self.settings, 'GOOGLE_CLOUD_PROJECT', None)
            location = getattr(self.settings, 'GOOGLE_CLOUD_LOCATION', None)  
            
            if not project_id:
                logger.error("GOOGLE_CLOUD_PROJECT must be set for Vertex AI")
                self._gemini_client = None
                return
            
            # Create Vertex AI client using new Gen AI SDK
            self._gemini_client = genai.Client(
                vertexai=True,
                project=project_id,
                location=location
            )
            
            logger.info(f"Gemini client initialized for Vertex AI project: {project_id}, location: {location}")
            
        except Exception as e:
            logger.error(f"Gemini setup failed: {e}")
            self._gemini_client = None
    
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

        logger.info(f"🔍 DEBUG: Final response: '{final_response}'")

        optimized_response = self.optimize_for_voice(final_response)
        
        # ADD THIS DEBUG LINE
        logger.info(f"🔍 DEBUG: Final response: '{optimized_response}'")
        
        return optimized_response
    
    def optimize_for_voice(self, text: str) -> str:
        """Make text voice-friendly using new Gen AI SDK."""
        logger.info(f"🔍 VOICE OPTIMIZATION: Method called with {len(text)} characters")
        
        if not hasattr(self, '_gemini_client'):
            self._setup_gemini()
        
        if not self._gemini_client:
            logger.error("🔍 VOICE OPTIMIZATION: No Gemini client available!")
            return text
        
        try:
            optimization_prompt = f"""
    Convert this text into natural, conversational speech for text-to-speech output:

    Original text: {text}

    Rules:
    1. Remove asterisks (*), formatting symbols, and technical punctuation
    2. Convert "From: email@domain.com" to "from [name]" 
    3. Convert timestamps to natural language (e.g., "today at 2 PM")
    4. Make email lists conversational: "You have 3 emails: one from John about..."
    5. Remove technical IDs and replace with natural references
    6. Keep the same information but make it sound natural when spoken
    7. Use casual, friendly tone
    8. If it's a list, introduce it naturally: "Here are your emails:" or "Your schedule shows:"

    Respond with ONLY the optimized text, no explanations.
    """
            
            # Use new Gen AI SDK API
            response = self._gemini_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=optimization_prompt
            )
            
            logger.info(f"🔍 VOICE OPTIMIZATION: Gemini response received")
            
            if response and response.text:
                optimized_text = response.text.strip()
                logger.info(f"🔍 VOICE OPTIMIZATION: Success - {len(text)} -> {len(optimized_text)} chars")
                return optimized_text
            else:
                logger.warning("🔍 VOICE OPTIMIZATION: Empty response from Gemini")
                return text
            
        except Exception as e:
            logger.error(f"🔍 VOICE OPTIMIZATION: Failed - {e}")
            return text
        

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