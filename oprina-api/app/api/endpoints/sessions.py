"""
Session management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.core.services.chat_service import ChatService
from app.core.database.repositories.session_repository import SessionRepository
from app.api.dependencies import (
    get_chat_service, 
    get_session_repository,
    get_current_user_id,
    validate_session_access
)

router = APIRouter()


@router.get("/")
async def get_all_sessions(
    active_only: bool = True,
    session_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user_id: str = Depends(get_current_user_id),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Get all sessions for the current user."""
    try:
        sessions = await session_repo.get_user_sessions(
            user_id=current_user_id,
            active_only=active_only,
            session_type=session_type
        )
        
        # Apply pagination
        paginated_sessions = sessions[offset:offset + limit]
        
        return {
            "sessions": paginated_sessions,
            "total": len(sessions),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.get("/{session_id}")
async def get_session_details(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: dict = Depends(validate_session_access),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Get detailed information about a specific session."""
    try:
        # Get session details (already validated by dependency)
        session_details = session
        
        # Add additional metrics if needed
        session_details["permissions"] = {
            "can_read": True,
            "can_write": session_details.get("status") == "active",
            "can_delete": True
        }
        
        return session_details
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get session details: {str(e)}"
        )


@router.put("/{session_id}")
async def update_session(
    session_id: str,
    status: Optional[str] = None,
    session_type: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    session: dict = Depends(validate_session_access),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Update session information."""
    try:
        update_data = {}
        
        if status is not None:
            if status not in ["active", "inactive", "ended"]:
                raise ValueError("Invalid status. Must be 'active', 'inactive', or 'ended'")
            update_data["status"] = status
        
        if session_type is not None:
            update_data["session_type"] = session_type
        
        if not update_data:
            raise ValueError("No valid fields to update")
        
        updated_session = await session_repo.update_session(session_id, update_data)
        
        return {
            "message": "Session updated successfully",
            "session": updated_session
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: dict = Depends(validate_session_access),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Delete a session and all associated data."""
    try:
        # End the session through chat service (handles agent session cleanup)
        success = await chat_service.end_chat_session(
            user_id=current_user_id,
            session_id=session_id
        )
        
        if success:
            return {
                "message": "Session deleted successfully",
                "session_id": session_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete session"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    message_type: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    session: dict = Depends(validate_session_access),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get messages for a specific session."""
    try:
        history = await chat_service.get_chat_history(
            user_id=current_user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        messages = history.get("messages", [])
        
        # Filter by message type if specified
        if message_type:
            messages = [msg for msg in messages if msg.get("type") == message_type]
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total_messages": len(messages),
            "limit": limit,
            "offset": offset,
            "session_info": history.get("session_info", {})
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get session messages: {str(e)}"
        )


@router.get("/{session_id}/stats")
async def get_session_statistics(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: dict = Depends(validate_session_access),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get detailed statistics for a session."""
    try:
        stats = await chat_service.get_session_stats(
            user_id=current_user_id,
            session_id=session_id
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get session statistics: {str(e)}"
        )


@router.post("/{session_id}/archive")
async def archive_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: dict = Depends(validate_session_access),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Archive a session (set status to inactive but keep data)."""
    try:
        update_data = {"status": "inactive"}
        updated_session = await session_repo.update_session(session_id, update_data)
        
        return {
            "message": "Session archived successfully",
            "session_id": session_id,
            "status": updated_session.get("status")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to archive session: {str(e)}"
        )


@router.post("/{session_id}/restore")
async def restore_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Restore an archived session."""
    try:
        # Get session without validation (might be inactive)
        session = await session_repo.get_session_by_id(session_id)
        
        if not session or session.get("user_id") != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        update_data = {"status": "active"}
        updated_session = await session_repo.update_session(session_id, update_data)
        
        return {
            "message": "Session restored successfully",
            "session_id": session_id,
            "status": updated_session.get("status")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to restore session: {str(e)}"
        ) 