"""
Authentication API endpoints for AITM application.

This module provides endpoints for user authentication, registration,
token management, and user profile operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List, Optional
import logging

from app.core.database import get_db
from app.core.auth import AuthService, get_auth_service, get_current_user_id, get_password_requirements
from app.services.user_service import UserService
from app.models.user import UserCreate, UserUpdate, User

logger = logging.getLogger(__name__)
router = APIRouter()

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Request/Response Models
class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserRegistration(BaseModel):
    """User registration model"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
class PasswordChange(BaseModel):
    """Password change model"""
    current_password: str
    new_password: str

class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str

class UserProfile(BaseModel):
    """User profile update model"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

# Dependency to get user service
async def get_user_service(
    auth_service: AuthService = Depends(get_auth_service)
) -> UserService:
    """Dependency to get user service instance."""
    return UserService(auth_service)

# Dependency to get current user
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user_id: str = Depends(get_current_user_id)
) -> User:
    """Dependency to get current authenticated user."""
    user = await user_service.get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# Dependency to get current active user
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# Dependency to get current superuser
async def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Authentication endpoints
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistration,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user."""
    user_create = UserCreate(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False
    )
    
    try:
        user = await user_service.create_user(db, user_create)
        await db.commit()
        logger.info(f"New user registered: {user.email}")
        return user
    except Exception as e:
        await db.rollback()
        raise

@router.post("/login", response_model=TokenResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """Authenticate user and return JWT tokens."""
    try:
        # Authenticate user
        user = await user_service.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens with user claims
        additional_claims = {
            "email": user.email,
            "is_superuser": user.is_superuser,
            "full_name": user.full_name
        }
        
        access_token = auth_service.create_access_token(
            subject=user.id,
            additional_claims=additional_claims
        )
        refresh_token = auth_service.create_refresh_token(subject=user.id)
        
        logger.info(f"User logged in: {user.email}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=auth_service.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token and extract user ID
        payload = auth_service.verify_token(refresh_request.refresh_token)
        user_id = payload.get("sub")
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get user to include in new token
        user = await user_service.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        additional_claims = {
            "email": user.email,
            "is_superuser": user.is_superuser,
            "full_name": user.full_name
        }
        
        new_access_token = auth_service.create_access_token(
            subject=user.id,
            additional_claims=additional_claims
        )
        new_refresh_token = auth_service.create_refresh_token(subject=user.id)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=auth_service.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

# User profile endpoints
@router.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile."""
    return current_user

@router.put("/me", response_model=User)
async def update_current_user_profile(
    profile_update: UserProfile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user profile."""
    try:
        user_update = UserUpdate(
            email=profile_update.email,
            full_name=profile_update.full_name
        )
        
        updated_user = await user_service.update_user(db, current_user.id, user_update)
        await db.commit()
        
        logger.info(f"User profile updated: {current_user.email}")
        return updated_user
        
    except Exception as e:
        await db.rollback()
        raise

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Change current user password."""
    try:
        await user_service.change_password(
            db, 
            current_user.id, 
            password_change.current_password, 
            password_change.new_password
        )
        await db.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        await db.rollback()
        raise

# Password requirements endpoint
@router.get("/password-requirements")
async def get_password_requirements_endpoint():
    """Get password requirements for client-side validation."""
    return get_password_requirements()

# Admin user management endpoints
@router.get("/users", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Get list of users (admin only)."""
    return await user_service.get_users(db, skip, limit, include_inactive)

@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Create new user (admin only)."""
    try:
        user = await user_service.create_user(db, user_create)
        await db.commit()
        logger.info(f"User created by admin: {user.email}")
        return user
    except Exception as e:
        await db.rollback()
        raise

@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Get user by ID (admin only)."""
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Update user (admin only)."""
    try:
        updated_user = await user_service.update_user(db, user_id, user_update)
        await db.commit()
        logger.info(f"User updated by admin: {user_id}")
        return updated_user
    except Exception as e:
        await db.rollback()
        raise

@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Deactivate user (admin only)."""
    try:
        await user_service.delete_user(db, user_id)
        await db.commit()
        logger.info(f"User deactivated by admin: {user_id}")
        return {"message": "User deactivated successfully"}
    except Exception as e:
        await db.rollback()
        raise

@router.post("/users/{user_id}/activate", status_code=status.HTTP_200_OK)
async def activate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Activate user (admin only)."""
    try:
        await user_service.activate_user(db, user_id)
        await db.commit()
        logger.info(f"User activated by admin: {user_id}")
        return {"message": "User activated successfully"}
    except Exception as e:
        await db.rollback()
        raise

# System information endpoints
@router.get("/stats")
async def get_auth_stats(
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_superuser)
):
    """Get authentication system statistics (admin only)."""
    try:
        total_users = await user_service.get_user_count(db, active_only=False)
        active_users = await user_service.get_user_count(db, active_only=True)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "token_expiry_minutes": get_auth_service().access_token_expire_minutes,
            "refresh_token_expiry_days": get_auth_service().refresh_token_expire_days
        }
    except Exception as e:
        logger.error(f"Error getting auth stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve statistics"
        )
