"""
User model for AITM application

This module defines the User model and related database schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    role: str = "viewer"


class UserCreate(UserBase):
    """User creation schema"""
    password: str


class UserUpdate(UserBase):
    """User update schema"""
    password: Optional[str] = None


class User(UserBase):
    """User response schema"""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(User):
    """User schema with hashed password (for internal use)"""
    hashed_password: str


# SQLAlchemy model
class UserTable(Base):
    """SQLAlchemy User model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(String(20), nullable=False, default="viewer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_pydantic(self) -> User:
        """Convert SQLAlchemy model to Pydantic model"""
        return User(
            id=self.id,
            email=self.email,
            full_name=self.full_name,
            is_active=self.is_active,
            is_superuser=self.is_superuser,
            role=self.role,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
