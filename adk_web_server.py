from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import httpx
import uuid
from memory.adk_memory_manager import get_adk_memory_manager
from agents.root_agent import root_agent
from events.event import Event, EventActions, Content, Part
from agents.common.tool_context import ToolContext
from google.adk.events.event import Event
import logging

app = FastAPI(title="Oprina ADK Web Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store for demo (replace with ADK session service in prod)
sessions: Dict[str, Dict[str, Any]] = {}

# Monkey-patch Event to propagate tool_context from parent_event if present
def _patched_event_init(self, *args, **kwargs):
    parent_event = kwargs.get('parent_event')
    if parent_event and hasattr(parent_event, 'tool_context'):
        kwargs['tool_context'] = getattr(parent_event, 'tool_context', None)
    Event._original_init(self, *args, **kwargs)

if not hasattr(Event, '_original_init'):
    Event._original_init = Event.__init__
    Event.__init__ = _patched_event_init

class RunSSERequest(BaseModel):
    session_id: str
    message: str

@app.post("/apps/agents/users/{user_id}/sessions")
async def create_session(user_id: str):
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "session_id": session_id,
        "user_id": user_id,
        "events": []
    }
    # Optionally, create ADK session here
    return {"session_id": session_id}

@app.get("/apps/agents/users/{user_id}/sessions/{session_id}")
async def get_session(user_id: str, session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.get("/apps/agents/users/{user_id}/sessions")
async def list_sessions(user_id: str):
    return [s for s in sessions.values() if s["user_id"] == user_id]

@app.delete("/apps/agents/users/{user_id}/sessions/{session_id}")
async def delete_session(user_id: str, session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "success"}

@app.post("/run_sse")
async def run_sse(request: RunSSERequest):
    logger = logging.getLogger(__name__)
    logger.error(f"RUN_SSE: Received request with session_id={request.session_id}, message={request.message}")
    user_id = sessions.get(request.session_id, {}).get("user_id", "anonymous")
    session_id = request.session_id

    # Use ADK memory manager for session
    memory_manager = get_adk_memory_manager()
    session = await memory_manager.get_session(user_id, session_id)
    if not session:
        session_id = await memory_manager.create_session(user_id)
        session = await memory_manager.get_session(user_id, session_id)
    logger.error(f"RUN_SSE: Session retrieved/created: {session}")

    # Pass the actual session object, not a dict
    tool_context = {"session": session, "invocation_id": "run_sse"}
    logger.error(f"RUN_SSE: Created tool_context: {tool_context}")

    # Real ADK agent invocation with tool context
    try:
        # Create runner with tool context
        runner = memory_manager.create_runner(root_agent)
        logger.error(f"RUN_SSE: Created runner with root_agent: {root_agent}")

        # Create event with tool context
        event = Event(
            action=EventActions.CHAT,
            content=Content(parts=[Part(text=request.message)]),
            tool_context=tool_context  # Pass tool context in event
        )
        logger.error(f"RUN_SSE: Created event with tool_context: {event.tool_context}")

        # Process event with runner
        agent_responses = await runner.process(
            event=event,
            app_name=memory_manager.app_name,
            user_id=user_id,
            session_id=session_id
        )
        logger.error(f"RUN_SSE: Runner processed event, responses: {agent_responses}")
    except Exception as e:
        logger.error(f"RUN_SSE: Error processing event: {e}")
        agent_responses = [{"error": str(e)}]

    # Store event in session (in-memory for demo)
    if request.session_id in sessions:
        sessions[request.session_id]["events"].append({
            "content": f"Agent response: {agent_responses}"
        })

    return {"status": "success", "agent_responses": agent_responses}

# Health check
@app.get("/")
async def root():
    return {"message": "Oprina ADK Web Server is running"} 