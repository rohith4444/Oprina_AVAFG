"""
User management endpoints for Oprina API.
Following the same pattern as auth endpoints with proper utils usage.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime

from app.api.dependencies import get_current_user, get_user_service
from app.api.models.requests.user import UpdateProfileRequest, ChangePasswordRequest
from app.api.models.responses.user import (
    UserProfileResponse, ProfileUpdateResponse, PasswordChangeResponse
)
from app.core.services.user_service import UserService
from app.utils.validation import validate_email, validate_password, sanitize_input
from app.utils.errors import ValidationError, AuthenticationError
from app.utils.logging import get_logger
from app.utils.encryption import verify_password

logger = get_logger(__name__)
router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user profile.
    
    Returns the complete user profile including:
    - Basic info (email, names)
    - Profile settings (work_type, ai_preferences)
    - System settings (timezone, language)
    - Account status
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Retrieving profile for user: {user_id}")
        
        # Get user profile
        user = await user_service.get_user(user_id)
        if not user:
            logger.warning(f"Profile request for non-existent user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert timestamps to ISO format if needed
        def format_timestamp(ts):
            if ts is None:
                return None
            if isinstance(ts, str):
                return ts
            return ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
        
        # Prepare response matching UserProfileResponse model
        profile_data = {
            "id": str(user.get("id")),
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "preferred_name": user.get("preferred_name"),
            "work_type": user.get("work_type"),
            "ai_preferences": user.get("ai_preferences"),
            "display_name": user.get("display_name"),
            "avatar_url": user.get("avatar_url"),
            "timezone": user.get("timezone", "UTC"),
            "language": user.get("language", "en"),
            "is_active": user.get("is_active", True),
            "is_verified": user.get("is_verified", False),
            "has_google_oauth": user.get("has_google_oauth", False),
            "has_microsoft_oauth": user.get("has_microsoft_oauth", False),
            "created_at": format_timestamp(user.get("created_at")),
            "updated_at": format_timestamp(user.get("updated_at")),
            "last_login_at": format_timestamp(user.get("last_login_at")),
            "last_activity_at": format_timestamp(user.get("last_activity_at")),
            "email_verified_at": format_timestamp(user.get("email_verified_at"))
        }
        
        logger.info(f"Profile retrieved successfully for user: {user_id}")
        return UserProfileResponse(**profile_data)
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to get user profile for {current_user.get('id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile. Please try again."
        )


@router.put("/me", response_model=ProfileUpdateResponse)
async def update_user_profile(
    profile_data: UpdateProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user profile.
    
    Updates the user's profile with data from your UI form:
    - Full Name
    - Preferred Name  
    - Work Type
    - AI Preferences
    - Optional: avatar_url, timezone, language
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Profile update attempt for user: {user_id}")
        
        # Convert request to dict and filter out None values
        update_data = profile_data.dict(exclude_unset=True)
        
        if not update_data:
            logger.warning(f"Profile update with no data for user: {user_id}")
            raise ValidationError("No data provided for update")
        
        # SANITIZE USER INPUTS using utils (same pattern as auth)
        sanitized_data = {}
        
        if "full_name" in update_data:
            if update_data["full_name"]:
                sanitized_data["full_name"] = sanitize_input(update_data["full_name"])
            else:
                sanitized_data["full_name"] = None
                
        if "preferred_name" in update_data:
            if update_data["preferred_name"]:
                sanitized_data["preferred_name"] = sanitize_input(update_data["preferred_name"])
            else:
                sanitized_data["preferred_name"] = None
                
        if "work_type" in update_data:
            if update_data["work_type"]:
                sanitized_data["work_type"] = sanitize_input(update_data["work_type"])
            else:
                sanitized_data["work_type"] = None
                
        if "ai_preferences" in update_data:
            if update_data["ai_preferences"]:
                sanitized_data["ai_preferences"] = sanitize_input(update_data["ai_preferences"])
            else:
                sanitized_data["ai_preferences"] = None
        
        # Copy other fields that don't need sanitization
        for field in ["avatar_url", "timezone", "language"]:
            if field in update_data:
                sanitized_data[field] = update_data[field]
        
        # Validate specific fields if provided
        if "avatar_url" in sanitized_data and sanitized_data["avatar_url"]:
            # Basic URL validation could be added here
            pass
        
        # Update user profile using service
        await user_service.update_user_profile(user_id, sanitized_data)
        
        logger.info(f"Profile updated successfully for user: {user_id}")
        
        return ProfileUpdateResponse(
            message="Profile updated successfully",
            updated_at=datetime.utcnow().isoformat()
        )
        
    except ValidationError as e:
        logger.warning(f"Profile update validation failed for user {current_user.get('id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update profile for user {current_user.get('id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile. Please try again."
        )


@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Change user password.
    
    This endpoint:
    1. Validates current password
    2. Validates new password strength using utils
    3. Verifies current password against hash
    4. Updates password with new hash
    5. Logs security event
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Password change attempt for user: {user_id}")
        
        # 1. VALIDATE NEW PASSWORD STRENGTH using utils (same as auth)
        validate_password(password_data.new_password)
        
        # 2. VERIFY PASSWORDS DON'T MATCH (already done in request model, but double-check)
        if password_data.new_password != password_data.confirm_new_password:
            raise ValidationError("New passwords do not match")
        
        # 3. GET CURRENT USER to verify current password
        user = await user_service.get_user(user_id)
        if not user:
            logger.error(f"Password change for non-existent user: {user_id}")
            raise AuthenticationError("User not found")
        
        # 4. CHECK IF USER HAS PASSWORD (not OAuth-only)
        if not user.get("password_hash"):
            logger.warning(f"Password change attempt for OAuth-only user: {user_id}")
            raise ValidationError("Cannot change password for OAuth-only account")
        
        # 5. VERIFY CURRENT PASSWORD using utils (same pattern as auth)
        if not verify_password(password_data.current_password, user["password_hash"]):
            logger.warning(f"Password change with incorrect current password for user: {user_id}")
            raise AuthenticationError("Current password is incorrect")
        
        # 6. HASH NEW PASSWORD using utils (same as auth)
        from app.utils.encryption import hash_password
        new_password_hash = hash_password(password_data.new_password)
        
        # 7. CHANGE PASSWORD using service with hashed password
        success = await user_service.change_user_password(
            user_id=user_id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            logger.error(f"Password change service failed for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
        
        # 7. LOG SECURITY EVENT
        logger.info(f"Password changed successfully for user: {user_id}")
        
        return PasswordChangeResponse(
            message="Password changed successfully",
            changed_at=datetime.utcnow().isoformat()
        )
        
    except ValidationError as e:
        logger.warning(f"Password change validation failed for user {current_user.get('id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthenticationError as e:
        logger.warning(f"Password change authentication failed for user {current_user.get('id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Password change failed for user {current_user.get('id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password. Please try again."
        )