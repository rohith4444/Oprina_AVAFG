"""
Authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.core.services.user_service import UserService
from app.api.dependencies import get_user_service, get_current_user, get_optional_current_user
from app.api.models.requests import CreateUserRequest, UpdateUserRequest
from app.api.models.responses import UserResponse, AuthResponse

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register_user(
    user_data: CreateUserRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user or login existing user."""
    try:
        # Create or get existing user
        user = await user_service.create_or_get_user(user_data.dict())
        
        # Generate simple token for Phase 1
        # In production, this would be a proper JWT token
        token = f"user_{user['id']}"
        
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login_user(
    user_data: CreateUserRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Login user (same as register for Phase 1)."""
    try:
        # For Phase 1, login is the same as register
        # This will find existing user or create new one
        user = await user_service.create_or_get_user(user_data.dict())
        
        # Generate simple token for Phase 1
        token = f"user_{user['id']}"
        
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current authenticated user information."""
    return UserResponse(**current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user information."""
    try:
        user_id = current_user["id"]
        updated_user = await user_service.update_user(user_id, update_data.dict(exclude_none=True))
        
        return UserResponse(**updated_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update failed: {str(e)}"
        )


@router.post("/logout")
async def logout_user(
    current_user: dict = Depends(get_current_user)
):
    """Logout current user."""
    # For Phase 1, logout is just a confirmation
    # In production, you would invalidate the token
    return {"message": "Successfully logged out", "user_id": current_user["id"]}


@router.get("/validate")
async def validate_token(
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Validate authentication token."""
    if current_user:
        return {
            "valid": True,
            "user_id": current_user["id"],
            "email": current_user.get("email")
        }
    else:
        return {"valid": False}


@router.get("/stats")
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user statistics and activity."""
    try:
        user_id = current_user["id"]
        stats = await user_service.get_user_stats(user_id)
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user stats: {str(e)}"
        )


@router.put("/preferences")
async def update_user_preferences(
    preferences: dict,
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user preferences."""
    try:
        user_id = current_user["id"]
        updated_user = await user_service.update_user_preferences(user_id, preferences)
        
        return {
            "message": "Preferences updated successfully",
            "preferences": updated_user.get("preferences", {})
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.delete("/account")
async def deactivate_account(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Deactivate user account."""
    try:
        user_id = current_user["id"]
        success = await user_service.deactivate_user(user_id)
        
        if success:
            return {"message": "Account deactivated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate account"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deactivation failed: {str(e)}"
        ) 