"""
Chat endpoints for messaging and conversation management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import json

from app.core.services.chat_service import ChatService
from app.api.dependencies import (
    get_chat_service, 
    get_current_user_id,
    validate_session_access,
    validate_message_access
)

router = APIRouter()


@router.post("/sessions")
async def create_chat_session(
    session_type: str = "chat",
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a new chat session."""
    try:
        session = await chat_service.create_chat_session(
            user_id=current_user_id,
            session_type=session_type
        )
        
        return session
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create chat session: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    message: str,
    message_type: str = "text",
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send a message in a chat session."""
    try:
        result = await chat_service.send_message(
            user_id=current_user_id,
            session_id=session_id,
            message=message,
            message_type=message_type
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send message: {str(e)}"
        )


@router.post("/sessions/{session_id}/stream")
async def stream_message(
    session_id: str,
    message: str,
    message_type: str = "text",
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send a message and stream the response."""
    
    async def generate_stream():
        """Generate Server-Sent Events stream."""
        try:
            async for event in chat_service.stream_message(
                user_id=current_user_id,
                session_id=session_id,
                message=message,
                message_type=message_type
            ):
                # Format as Server-Sent Events
                yield f"data: {json.dumps(event)}\n\n"
                
        except Exception as e:
            error_event = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get chat history for a session."""
    try:
        history = await chat_service.get_chat_history(
            user_id=current_user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def end_chat_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """End a chat session."""
    try:
        success = await chat_service.end_chat_session(
            user_id=current_user_id,
            session_id=session_id
        )
        
        if success:
            return {"message": "Session ended successfully", "session_id": session_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to end session"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to end session: {str(e)}"
        )


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Delete a message from chat history."""
    try:
        success = await chat_service.delete_message(
            user_id=current_user_id,
            message_id=message_id
        )
        
        if success:
            return {"message": "Message deleted successfully", "message_id": message_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete message"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete message: {str(e)}"
        )


@router.get("/sessions/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get statistics for a chat session."""
    try:
        stats = await chat_service.get_session_stats(
            user_id=current_user_id,
            session_id=session_id
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get session stats: {str(e)}"
        )


@router.get("/")
async def get_user_chat_sessions(
    active_only: bool = True,
    current_user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get all chat sessions for the current user."""
    try:
        sessions = await chat_service.get_user_sessions(
            user_id=current_user_id,
            active_only=active_only
        )
        
        return {
            "sessions": sessions,
            "total_sessions": len(sessions),
            "user_id": current_user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user sessions: {str(e)}"
        ) 