"""
Authentication endpoints

This module provides secure authentication endpoints using all available utils:
- Password hashing and verification (utils/encryption.py)
- Input validation (utils/validation.py)  
- JWT token management (utils/auth.py)
- Proper error handling and security
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from app.core.services.user_service import UserService
from app.api.dependencies import get_user_service, get_current_user, get_optional_current_user
from app.api.models.requests.auth import LoginRequest, RegisterRequest
from app.api.models.responses.auth import UserResponse, AuthResponse, TokenValidationResponse, LogoutResponse
from app.utils.auth import AuthManager
from app.utils.encryption import hash_password, verify_password
from app.utils.validation import validate_email, validate_password, sanitize_input
from app.utils.errors import ValidationError, AuthenticationError
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize AuthManager
auth_manager = AuthManager()


@router.post("/register", response_model=AuthResponse)
async def register_user(
    user_data: RegisterRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user with proper password security.
    
    This endpoint:
    1. Validates email format and password strength
    2. Checks user doesn't already exist
    3. Hashes password securely
    4. Creates user with all UI fields
    5. Generates JWT token
    6. Returns authentication response
    """
    try:
        # 1. VALIDATE EMAIL FORMAT using utils
        validated_email = validate_email(user_data.email)
        logger.info(f"Registration attempt for email: {validated_email}")
        
        # 2. VALIDATE PASSWORD STRENGTH using utils
        if user_data.password:
            validate_password(user_data.password)
            
            # Check password confirmation matches
            if user_data.password != user_data.confirm_password:
                raise ValidationError("Passwords do not match")
        else:
            raise ValidationError("Password is required for registration")
        
        # 3. SANITIZE USER INPUTS using utils
        full_name = sanitize_input(user_data.full_name) if user_data.full_name else None
        preferred_name = sanitize_input(user_data.preferred_name) if user_data.preferred_name else None
        work_type = sanitize_input(user_data.work_type) if user_data.work_type else None
        ai_preferences = sanitize_input(user_data.ai_preferences) if user_data.ai_preferences else None
        
        # 4. CHECK USER DOESN'T EXIST
        existing_user = await user_service.get_user_by_email(validated_email)
        if existing_user:
            logger.warning(f"Registration attempt for existing email: {validated_email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # 5. HASH PASSWORD using utils
        password_hash = hash_password(user_data.password)
        
        # 6. CREATE USER with all fields
        user_create_data = {
            "email": validated_email,
            "password_hash": password_hash,
            "full_name": full_name,
            "preferred_name": preferred_name,
            "work_type": work_type,
            "ai_preferences": ai_preferences,
            "is_active": True,
            "is_verified": False  # Email verification can be added later
        }
        
        user = await user_service.create_user(user_create_data)
        
        # 7. GENERATE JWT TOKEN using utils
        access_token = auth_manager.create_access_token(user['id'])
        
        # 8. LOG SUCCESSFUL REGISTRATION
        logger.info(f"User registered successfully: {user['id']}")
        
        # 9. RETURN AUTHENTICATION RESPONSE
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(**user),
            expires_in=auth_manager.token_expiry_hours * 3600  # Convert to seconds
        )
        
    except ValidationError as e:
        logger.warning(f"Registration validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Registration failed for {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=AuthResponse)
async def login_user(
    credentials: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Authenticate user with email and password.
    
    This endpoint:
    1. Validates email format
    2. Finds user by email
    3. Verifies password against hash
    4. Updates last login timestamp
    5. Generates new JWT token
    6. Returns authentication response
    """
    try:
        # 1. VALIDATE EMAIL FORMAT using utils
        validated_email = validate_email(credentials.email)
        logger.info(f"Login attempt for email: {validated_email}")
        
        # 2. VALIDATE PASSWORD PROVIDED
        if not credentials.password:
            raise AuthenticationError("Password is required")
        
        # 3. FIND USER BY EMAIL
        user = await user_service.get_user_by_email(validated_email)
        if not user:
            logger.warning(f"Login attempt for non-existent email: {validated_email}")
            # Don't reveal that user doesn't exist
            raise AuthenticationError("Invalid email or password")
        
        # 4. CHECK USER IS ACTIVE
        if not user.get('is_active', True):
            logger.warning(f"Login attempt for deactivated user: {user['id']}")
            raise AuthenticationError("Account has been deactivated")
        
        # 5. VERIFY PASSWORD using utils
        if not user.get('password_hash'):
            logger.warning(f"Login attempt for user without password: {user['id']}")
            raise AuthenticationError("Invalid email or password")
        
        if not verify_password(credentials.password, user['password_hash']):
            logger.warning(f"Login attempt with wrong password: {user['id']}")
            raise AuthenticationError("Invalid email or password")
        
        # 6. UPDATE LAST LOGIN using repository
        await user_service.update_last_login(user['id'])
        
        # 7. GENERATE JWT TOKEN using utils
        access_token = auth_manager.create_access_token(user['id'])
        
        # 8. LOG SUCCESSFUL LOGIN
        logger.info(f"User logged in successfully: {user['id']}")
        
        # 9. RETURN AUTHENTICATION RESPONSE
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(**user),
            expires_in=auth_manager.token_expiry_hours * 3600  # Convert to seconds
        )
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed for {credentials.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Login validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login failed for {credentials.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    current_user: dict = Depends(get_current_user)
):
    """
    Logout current user.
    
    For stateless JWT tokens, this is primarily a confirmation.
    In production, you could implement token blacklisting here.
    """
    try:
        user_id = current_user["id"]
        
        # Log logout event
        logger.info(f"User logged out: {user_id}")
        
        # In production, you could:
        # 1. Add token to blacklist table
        # 2. Update user's last_activity_at
        # 3. Invalidate refresh tokens
        
        return LogoutResponse(
            message="Successfully logged out",
            user_id=user_id,
            logged_out_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/validate", response_model=TokenValidationResponse)
async def validate_token(
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Validate authentication token.
    
    Returns token validity and user information if valid.
    Useful for frontend to check auth status.
    """
    try:
        if current_user:
            logger.debug(f"Token validated for user: {current_user['id']}")
            return TokenValidationResponse(
                valid=True,
                user_id=current_user["id"],
                email=current_user.get("email"),
                expires_at=None  # Could extract from JWT if needed
            )
        else:
            logger.debug("Token validation failed - invalid token")
            return TokenValidationResponse(
                valid=False,
                user_id=None,
                email=None,
                expires_at=None
            )
            
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return TokenValidationResponse(
            valid=False,
            user_id=None,
            email=None,
            expires_at=None
        )


@router.delete("/deactivate")
async def deactivate_account(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Deactivate user account (soft delete).
    
    This marks the account as inactive but preserves data.
    User will not be able to login after deactivation.
    """
    try:
        user_id = current_user["id"]
        
        # Deactivate user using service
        await user_service.deactivate_user(user_id)
        
        # Log deactivation
        logger.info(f"User account deactivated: {user_id}")
        
        return {
            "message": "Account deactivated successfully",
            "user_id": user_id,
            "deactivated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Account deactivation failed for {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deactivation failed. Please try again."
        )