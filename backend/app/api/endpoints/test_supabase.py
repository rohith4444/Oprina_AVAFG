"""
Test endpoints for validating Supabase authentication integration.
Temporary endpoints for Phase 1 testing - remove after validation complete.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional

from app.api.dependencies import (
    get_current_user_supabase, 
    get_current_user_supabase_optional,
    get_user_repository
)
from app.core.database.repositories.user_repository import UserRepository
from app.utils.supabase_auth import test_supabase_connection, validate_supabase_token
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/supabase/connection")
async def test_connection():
    """
    Test basic Supabase connection.
    GET /api/v1/test/supabase/connection
    """
    try:
        is_connected = test_supabase_connection()
        
        return {
            "status": "success" if is_connected else "failed",
            "connected": is_connected,
            "message": "Supabase connection working" if is_connected else "Supabase connection failed"
        }
    except Exception as e:
        logger.error(f"Connection test error: {str(e)}")
        return {
            "status": "error",
            "connected": False,
            "message": f"Connection test failed: {str(e)}"
        }


@router.get("/supabase/validate-token")
async def test_token_validation(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """
    Test Supabase token validation with user sync.
    GET /api/v1/test/supabase/validate-token
    Headers: Authorization: Bearer <supabase_token>
    """
    try:
        return {
            "status": "success",
            "message": "Supabase token validation successful",
            "user": {
                "id": current_user.get("id"),
                "email": current_user.get("email"),
                "full_name": current_user.get("full_name"),
                "is_active": current_user.get("is_active"),
                "created_at": current_user.get("created_at"),
                "backend_sync": "User exists in backend database"
            }
        }
    except Exception as e:
        logger.error(f"Token validation test error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token validation test failed: {str(e)}"
        )


@router.get("/supabase/user-info")
async def get_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Get detailed user information from both Supabase and backend.
    GET /api/v1/test/supabase/user-info
    Headers: Authorization: Bearer <supabase_token>
    """
    try:
        # Get user from backend database
        backend_user = await user_repository.get_user_by_id(current_user["id"])
        
        return {
            "status": "success",
            "message": "User information retrieved successfully",
            "supabase_user": {
                "id": current_user.get("id"),
                "email": current_user.get("email"),
                "auth_source": "supabase"
            },
            "backend_user": {
                "id": backend_user.get("id") if backend_user else None,
                "email": backend_user.get("email") if backend_user else None,
                "full_name": backend_user.get("full_name") if backend_user else None,
                "created_at": backend_user.get("created_at") if backend_user else None,
                "last_login_at": backend_user.get("last_login_at") if backend_user else None,
                "exists_in_backend": backend_user is not None
            },
            "sync_status": "synced" if backend_user else "not_synced"
        }
    except Exception as e:
        logger.error(f"User info test error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User info retrieval failed: {str(e)}"
        )


@router.get("/supabase/optional-auth")
async def test_optional_auth(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_supabase_optional)
):
    """
    Test optional Supabase authentication.
    GET /api/v1/test/supabase/optional-auth
    Works with or without Authorization header.
    """
    if current_user:
        return {
            "status": "authenticated",
            "message": "User is authenticated",
            "user_email": current_user.get("email"),
            "user_id": current_user.get("id")
        }
    else:
        return {
            "status": "anonymous",
            "message": "No authentication provided",
            "user": None
        }


@router.post("/supabase/manual-token-test")
async def manual_token_test(token_data: Dict[str, str]):
    """
    Manually test a token without using dependencies.
    POST /api/v1/test/supabase/manual-token-test
    Body: {"token": "your_supabase_jwt_token"}
    """
    try:
        token = token_data.get("token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required in request body"
            )
        
        # Validate token directly
        supabase_user = validate_supabase_token(token)
        
        return {
            "status": "success",
            "message": "Manual token validation successful",
            "token_valid": True,
            "user_data": {
                "id": supabase_user.get("id"),
                "email": supabase_user.get("email"),
                "email_confirmed": supabase_user.get("email_confirmed_at") is not None,
                "created_at": supabase_user.get("created_at")
            }
        }
    except Exception as e:
        logger.error(f"Manual token test error: {str(e)}")
        return {
            "status": "error",
            "message": f"Token validation failed: {str(e)}",
            "token_valid": False,
            "error_details": str(e)
        }