"""
Session management endpoints.
Simplified for voice-first chat sessions with proper repository integration and Vertex AI.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any

from app.api.dependencies import (
    get_current_user,
    get_session_repository,
    get_message_repository,
    get_agent_service  # ADDED FOR VERTEX AI INTEGRATION
)
from app.core.database.repositories.session_repository import SessionRepository
from app.core.database.repositories.message_repository import MessageRepository
from app.core.services.agent_service import AgentService  # ADDED IMPORT
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Helper function for session ownership validation
async def verify_session_ownership(
    session_id: str, 
    user_id: str, 
    session_repo: SessionRepository
) -> Dict[str, Any]:
    """Verify user owns the session and return session data."""
    session = await session_repo.get_session_by_id(session_id)
    if not session or session.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.post("/create")
async def create_session(
    title: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository),
    agent_service: AgentService = Depends(get_agent_service)  # ADDED VERTEX AI SERVICE
):
    """Create a new chat session with optional Vertex AI integration."""
    try:
        user_id = current_user["id"]
        
        # Prepare session data
        session_data = {
            "user_id": user_id,
            "status": "active",
            "title": title or "New Chat"
        }
        
        # Create session in database first
        session = await session_repo.create_session(session_data)
        session_id = session["id"]
        
        logger.info(f"Created database session {session_id} for user {user_id}")
        
        # Try to create Vertex AI session (graceful failure)
        vertex_integration = False
        vertex_session_id = None
        vertex_error = None
        
        try:
            agent_result = await agent_service.create_agent_session(user_id, session_id)
            vertex_integration = agent_result.get("vertex_integration", False)
            vertex_session_id = agent_result.get("agent_session_id")
            
            if vertex_integration:
                logger.info(f"Successfully integrated session {session_id} with Vertex AI: {vertex_session_id}")
            else:
                logger.warning(f"Vertex AI integration partially failed for session {session_id}")
                vertex_error = agent_result.get("vertex_error", "Unknown Vertex AI error")
                
        except Exception as e:
            logger.warning(f"Vertex AI integration failed for session {session_id}: {str(e)}")
            vertex_error = str(e)
        
        # Return session data regardless of Vertex AI success
        response_data = {
            "session_id": session_id,
            "user_id": user_id,
            "status": session["status"],
            "title": session["title"],
            "created_at": session["created_at"],
            "vertex_session_id": vertex_session_id,
            "vertex_integration": vertex_integration,
            "message": "Session created successfully"
        }
        
        # Add vertex error info if integration failed (useful for debugging)
        if not vertex_integration and vertex_error:
            response_data["vertex_error"] = vertex_error
        
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to create session for user {current_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/list")
async def get_user_sessions(
    active_only: bool = True,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository),
    message_repo: MessageRepository = Depends(get_message_repository)
):
    """Get all sessions for the current user."""
    try:
        user_id = current_user["id"]
        
        # Get user sessions (already ordered by last_activity_at DESC)
        sessions = await session_repo.get_user_sessions(
            user_id=user_id,
            active_only=active_only
        )
        
        # Apply limit if specified
        if limit > 0:
            sessions = sessions[:limit]
        
        # Enrich sessions with message counts
        enriched_sessions = []
        for session in sessions:
            session_id = session["id"]
            
            # Get message count for each session
            message_count = await message_repo.count_session_messages(session_id)
            
            enriched_sessions.append({
                "session_id": session_id,
                "title": session.get("title", "New Chat"),
                "status": session["status"],
                "created_at": session["created_at"],
                "last_activity_at": session["last_activity_at"],
                "message_count": message_count,
                "has_vertex_session": bool(session.get("vertex_session_id"))
            })
        
        return {
            "sessions": enriched_sessions,
            "total": len(enriched_sessions),
            "user_id": user_id,
            "active_only": active_only
        }
        
    except Exception as e:
        logger.error(f"Failed to get sessions for user {current_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.get("/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository),
    message_repo: MessageRepository = Depends(get_message_repository)
):
    """Get detailed information about a specific session."""
    try:
        user_id = current_user["id"]
        
        # Verify ownership and get session
        session = await verify_session_ownership(session_id, user_id, session_repo)
        
        # Get additional session metrics
        message_count = await message_repo.count_session_messages(session_id)
        
        # Get latest messages for preview
        latest_messages = await message_repo.get_latest_messages(session_id, limit=3)
        
        return {
            "session_id": session["id"],
            "title": session.get("title", "New Chat"),
            "status": session["status"],
            "created_at": session["created_at"],
            "last_activity_at": session["last_activity_at"],
            "updated_at": session["updated_at"],
            "vertex_session_id": session.get("vertex_session_id"),
            "message_count": message_count,
            "latest_messages": latest_messages,
            "permissions": {
                "can_read": True,
                "can_send_messages": session["status"] == "active",
                "can_delete": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id} details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session details"
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Delete a session (soft delete - sets status to 'deleted')."""
    try:
        user_id = current_user["id"]
        
        # Verify ownership
        session = await verify_session_ownership(session_id, user_id, session_repo)
        
        # Soft delete the session
        success = await session_repo.delete_session(session_id)
        
        if success:
            logger.info(f"Deleted session {session_id} for user {user_id}")
            return {
                "message": "Session deleted successfully",
                "session_id": session_id,
                "title": session.get("title", "New Chat")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete session"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )


@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    message_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository),
    message_repo: MessageRepository = Depends(get_message_repository)
):
    """Get messages for a specific session."""
    try:
        user_id = current_user["id"]
        
        # Verify ownership and get session
        session = await verify_session_ownership(session_id, user_id, session_repo)
        
        # Get messages for the session
        if message_type == "voice":
            messages = await message_repo.get_voice_messages(session_id)
        else:
            messages = await message_repo.get_session_messages(session_id, limit=limit)
        
        # Filter by message_type if specified and not voice
        if message_type and message_type != "voice":
            messages = [msg for msg in messages if msg.get("message_type") == message_type]
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total_messages": len(messages),
            "limit": limit,
            "message_type_filter": message_type,
            "session_info": {
                "title": session.get("title", "New Chat"),
                "status": session["status"],
                "created_at": session["created_at"],
                "last_activity_at": session["last_activity_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session messages"
        )


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """End a session gracefully (sets status to 'ended')."""
    try:
        user_id = current_user["id"]
        
        # Verify ownership
        session = await verify_session_ownership(session_id, user_id, session_repo)
        
        # Only end active sessions
        if session["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot end session with status: {session['status']}"
            )
        
        # End the session
        updated_session = await session_repo.end_session(session_id)
        
        logger.info(f"Ended session {session_id} for user {user_id}")
        
        return {
            "message": "Session ended successfully",
            "session_id": session_id,
            "title": session.get("title", "New Chat"),
            "status": updated_session["status"],
            "ended_at": updated_session["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end session"
        )