"""
Core dependencies for AITM application

This module provides dependency injection functions for authentication,
database sessions, and other core functionality.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from JWT token.
    For now, this is a mock implementation that returns a default user.
    In a real implementation, this would validate JWT tokens and fetch user from database.
    """
    # In production, this would:
    # 1. Validate JWT token from credentials
    # 2. Extract user ID from token
    # 3. Fetch user from database
    # 4. Handle token expiration and validation errors
    
    if not credentials:
        # No authentication provided - return anonymous user for public endpoints
        return User(
            id="anonymous",
            email="anonymous@example.com",
            full_name="Anonymous User",
            is_active=True,
            is_superuser=False
        )
    
    # Mock authentication - in production, validate JWT token here
    try:
        # Simulate token validation
        token = credentials.credentials
        
        # For demo, accept any non-empty token
        if token and len(token) > 10:
            # Return mock authenticated user
            return User(
                id="user_001",
                email="user@aitm.com",
                full_name="AITM User",
                is_active=True,
                is_superuser=False
            )
        else:
            # Invalid token
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_prediction_service():
    """Dependency to get prediction service instance."""
    from app.services.prediction_service import RiskPredictionService
    return RiskPredictionService()


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (must be authenticated and active)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current superuser (must be authenticated, active, and have superuser privileges)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    This is useful for endpoints that work both with and without authentication.
    """
    try:
        return get_current_user(credentials, db)
    except Exception:
        return None
