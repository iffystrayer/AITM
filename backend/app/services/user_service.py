"""
User service for AITM application.

This module provides user management functionality including CRUD operations,
role management, and user profile handling.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import HTTPException, status
import logging

from app.models.user import UserTable, UserCreate, UserUpdate, User, UserInDB
from app.core.auth import AuthService, validate_password_strength

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management operations"""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    async def create_user(self, db: AsyncSession, user_create: UserCreate) -> User:
        """Create a new user."""
        try:
            # Validate password strength
            if not validate_password_strength(user_create.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password does not meet security requirements"
                )
            
            # Check if user already exists
            existing_user = await self.get_user_by_email(db, user_create.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Create user record
            user_id = str(uuid.uuid4())
            hashed_password = self.auth_service.get_password_hash(user_create.password)
            
            db_user = UserTable(
                id=user_id,
                email=user_create.email,
                hashed_password=hashed_password,
                full_name=user_create.full_name,
                is_active=user_create.is_active,
                is_superuser=user_create.is_superuser
            )
            
            db.add(db_user)
            await db.flush()
            await db.refresh(db_user)
            
            logger.info(f"Created new user: {user_create.email}")
            return db_user.to_pydantic()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create user"
            )
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            user = result.scalar_one_or_none()
            return user.to_pydantic() if user else None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[UserInDB]:
        """Get user by email (includes hashed password for authentication)."""
        try:
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            user = result.scalar_one_or_none()
            if user:
                return UserInDB(
                    id=user.id,
                    email=user.email,
                    hashed_password=user.hashed_password,
                    full_name=user.full_name,
                    is_active=user.is_active,
                    is_superuser=user.is_superuser,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_users(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[User]:
        """Get list of users."""
        try:
            query = select(UserTable)
            if not include_inactive:
                query = query.where(UserTable.is_active == True)
            query = query.offset(skip).limit(limit).order_by(UserTable.created_at.desc())
            
            result = await db.execute(query)
            users = result.scalars().all()
            return [user.to_pydantic() for user in users]
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    async def update_user(self, db: AsyncSession, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user information."""
        try:
            # Get existing user
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Prepare update data
            update_data = user_update.dict(exclude_unset=True)
            
            # Handle password update
            if "password" in update_data and update_data["password"]:
                if not validate_password_strength(update_data["password"]):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Password does not meet security requirements"
                    )
                update_data["hashed_password"] = self.auth_service.get_password_hash(update_data["password"])
                del update_data["password"]
            
            # Check for email uniqueness if email is being updated
            if "email" in update_data and update_data["email"] != db_user.email:
                existing_user = await self.get_user_by_email(db, update_data["email"])
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User with this email already exists"
                    )
            
            # Update user
            for field, value in update_data.items():
                setattr(db_user, field, value)
            
            await db.flush()
            await db.refresh(db_user)
            
            logger.info(f"Updated user: {user_id}")
            return db_user.to_pydantic()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not update user"
            )
    
    async def delete_user(self, db: AsyncSession, user_id: str) -> bool:
        """Delete user (soft delete by marking as inactive)."""
        try:
            result = await db.execute(
                update(UserTable)
                .where(UserTable.id == user_id)
                .values(is_active=False, updated_at=datetime.now(timezone.utc))
            )
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            logger.info(f"Deactivated user: {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not delete user"
            )
    
    async def activate_user(self, db: AsyncSession, user_id: str) -> bool:
        """Reactivate a deactivated user."""
        try:
            result = await db.execute(
                update(UserTable)
                .where(UserTable.id == user_id)
                .values(is_active=True, updated_at=datetime.now(timezone.utc))
            )
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            logger.info(f"Activated user: {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error activating user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not activate user"
            )
    
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password."""
        try:
            user = await self.get_user_by_email(db, email)
            if not user:
                return None
            
            if not user.is_active:
                return None
            
            if not self.auth_service.verify_password(password, user.hashed_password):
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}")
            return None
    
    async def change_password(
        self, 
        db: AsyncSession, 
        user_id: str, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """Change user password with current password verification."""
        try:
            # Get user with hashed password
            result = await db.execute(select(UserTable).where(UserTable.id == user_id))
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not self.auth_service.verify_password(current_password, db_user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Validate new password strength
            if not validate_password_strength(new_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password does not meet security requirements"
                )
            
            # Update password
            new_hashed_password = self.auth_service.get_password_hash(new_password)
            await db.execute(
                update(UserTable)
                .where(UserTable.id == user_id)
                .values(hashed_password=new_hashed_password, updated_at=datetime.now(timezone.utc))
            )
            
            logger.info(f"Password changed for user: {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not change password"
            )
    
    async def get_user_count(self, db: AsyncSession, active_only: bool = True) -> int:
        """Get total user count."""
        try:
            query = select(UserTable.id)
            if active_only:
                query = query.where(UserTable.is_active == True)
            
            result = await db.execute(query)
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return 0
