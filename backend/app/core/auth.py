"""
Authentication and authorization core functionality for AITM.

This module provides JWT token management, password hashing, and user authentication.
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import logging

logger = logging.getLogger(__name__)

def get_db_dependency():
    """Dependency function to get database session, avoiding circular imports."""
    from app.core.database import get_db
    return get_db

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_production_config():
    """
    Validate required security configuration in production environment.
    
    This function performs critical security validation during application startup:
    - Ensures SECRET_KEY is set in production environments
    - Validates the secret key meets minimum security requirements
    - Provides appropriate warnings for development environments
    
    Raises:
        RuntimeError: If SECRET_KEY is missing in production environment
        RuntimeError: If SECRET_KEY is too weak in production environment
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    logger.info(f"Validating JWT configuration for environment: {environment}")
    
    if environment == "production":
        # Check both SECRET_KEY and JWT_SECRET_KEY for compatibility
        secret_key = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
        
        if not secret_key:
            error_msg = (
                "CRITICAL SECURITY ERROR: SECRET_KEY environment variable is required in production environment. "
                "The SECRET_KEY is used to sign JWT tokens and must be a secure random string. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))' "
                "Then set it as an environment variable: export SECRET_KEY='your-generated-key'"
            )
            logger.critical(error_msg)
            
            # Log security audit event
            try:
                from app.core.security_audit import get_security_audit_logger
                audit_logger = get_security_audit_logger()
                audit_logger.log_production_config_error(
                    error_type="MISSING_SECRET_KEY",
                    error_message="SECRET_KEY environment variable is required in production"
                )
            except ImportError:
                # Security audit logging not available during early initialization
                pass
            
            raise RuntimeError(error_msg)
        
        # Validate secret key strength in production
        if len(secret_key) < 32:
            error_msg = (
                "CRITICAL SECURITY ERROR: SECRET_KEY is too short for production use. "
                f"Current length: {len(secret_key)} characters. Minimum required: 32 characters. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
        
        # Check for default/weak keys
        weak_keys = [
            "your-super-secret-jwt-key-change-this-in-production",
            "secret",
            "password",
            "123456",
            "changeme"
        ]
        
        if secret_key.lower() in [key.lower() for key in weak_keys]:
            error_msg = (
                "CRITICAL SECURITY ERROR: SECRET_KEY appears to be a default or weak value. "
                "Using weak keys in production compromises JWT token security. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("Production JWT configuration validated successfully")
        logger.info(f"SECRET_KEY length: {len(secret_key)} characters (meets security requirements)")
        
        # Log successful validation
        try:
            from app.core.security_audit import get_security_audit_logger
            audit_logger = get_security_audit_logger()
            audit_logger.log_secret_key_validation(
                environment=environment,
                validation_result="success",
                key_length=len(secret_key)
            )
        except ImportError:
            # Security audit logging not available during early initialization
            pass
        
    else:
        # Development environment warnings
        secret_key = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            logger.warning(
                "SECRET_KEY not set - a temporary key will be generated for this session. "
                "This is acceptable for development but user sessions will not persist across restarts. "
                "For persistent sessions in development, set SECRET_KEY environment variable."
            )
        else:
            logger.info(f"Using configured SECRET_KEY for development environment (length: {len(secret_key)} characters)")
            
        logger.info("Development environment: JWT configuration validation complete")


def get_jwt_secret_key() -> str:
    """
    Get JWT secret key with comprehensive validation and error handling.
    
    This function retrieves the JWT secret key used for token signing and validation.
    It enforces security requirements in production and provides fallbacks for development.
    
    Returns:
        str: The JWT secret key to use for token operations
        
    Raises:
        RuntimeError: If SECRET_KEY is missing or invalid in production environment
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    # Check both SECRET_KEY and JWT_SECRET_KEY for compatibility
    secret_key = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
    
    if environment == "production":
        if not secret_key:
            error_msg = (
                "CRITICAL SECURITY ERROR: SECRET_KEY environment variable is required in production. "
                "This error should have been caught during startup validation. "
                "Please ensure validate_production_config() is called during application startup."
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
        
        # Additional runtime validation for production
        if len(secret_key) < 32:
            error_msg = (
                "CRITICAL SECURITY ERROR: SECRET_KEY is too short for production use. "
                f"Current length: {len(secret_key)} characters. Minimum required: 32 characters."
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
            
        return secret_key
    else:
        # Development environment handling
        if not secret_key:
            generated_key = secrets.token_urlsafe(32)
            logger.warning(
                "No SECRET_KEY configured - generating temporary key for development session. "
                "User sessions will not persist across application restarts. "
                f"Generated key length: {len(generated_key)} characters"
            )
            return generated_key
        else:
            logger.debug(f"Using configured SECRET_KEY for development (length: {len(secret_key)} characters)")
            return secret_key


# JWT configuration
SECRET_KEY = get_jwt_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security scheme
security = HTTPBearer()

class AuthService:
    """Centralized authentication service"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
        
        # Log authentication service initialization (without exposing secret key)
        environment = os.getenv("ENVIRONMENT", "development").lower()
        logger.info(f"AuthService initialized for {environment} environment")
        logger.info(f"JWT Algorithm: {self.algorithm}")
        logger.info(f"Access token expiry: {self.access_token_expire_minutes} minutes")
        logger.info(f"Refresh token expiry: {self.refresh_token_expire_days} days")
        logger.info(f"Secret key configured: {'Yes' if self.secret_key else 'No'}")
        
        if environment == "production" and not self.secret_key:
            error_msg = "CRITICAL: AuthService initialized without secret key in production"
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)
    
    def create_access_token(
        self, 
        subject: str, 
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        if not self.secret_key:
            error_msg = "Cannot create access token: SECRET_KEY not configured"
            logger.critical(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service not properly configured"
            )
            
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Access token created successfully for subject: {subject}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token for subject {subject}: {e}")
            logger.error(f"Secret key configured: {'Yes' if self.secret_key else 'No'}")
            logger.error(f"Algorithm: {self.algorithm}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )
    
    def create_refresh_token(self, subject: str) -> str:
        """Create JWT refresh token."""
        if not self.secret_key:
            error_msg = "Cannot create refresh token: SECRET_KEY not configured"
            logger.critical(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service not properly configured"
            )
            
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Refresh token created successfully for subject: {subject}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token for subject {subject}: {e}")
            logger.error(f"Secret key configured: {'Yes' if self.secret_key else 'No'}")
            logger.error(f"Algorithm: {self.algorithm}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create refresh token"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        if not self.secret_key:
            error_msg = "Cannot verify token: SECRET_KEY not configured"
            logger.critical(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service not properly configured"
            )
            
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp is None:
                logger.warning("Token verification failed: missing expiration claim")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration"
                )
            
            if datetime.now(timezone.utc) > datetime.fromtimestamp(exp, timezone.utc):
                logger.debug("Token verification failed: token expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            logger.debug("Token verified successfully")
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.debug("Token verification failed: expired signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token verification failed: invalid token - {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except HTTPException:
            # Re-raise HTTP exceptions without additional logging
            raise
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            logger.error(f"Secret key configured: {'Yes' if self.secret_key else 'No'}")
            logger.error(f"Algorithm: {self.algorithm}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from refresh token."""
        payload = self.verify_token(refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        subject = payload.get("sub")
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Create new access token
        return self.create_access_token(subject)
    
    def get_current_user_from_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """Extract current user ID from JWT token."""
        try:
            payload = self.verify_token(credentials.credentials)
            user_id = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            
            # Verify it's an access token
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return user_id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error extracting user from token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

# Global auth service instance
auth_service = AuthService()

# Dependency functions for FastAPI
def get_auth_service() -> AuthService:
    """Dependency to get auth service instance."""
    return auth_service

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """FastAPI dependency to get current user ID from token."""
    return auth_service.get_current_user_from_token(credentials)

async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_dependency())
):
    """FastAPI dependency to get current user object from token."""
    from app.services.user_service import UserService
    from app.models.user import User
    
    user_service = UserService(auth_service)
    user = await user_service.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user

# Password strength validation
def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements."""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_upper and has_lower and has_digit and has_special

def get_password_requirements() -> Dict[str, str]:
    """Get password requirements for client validation."""
    return {
        "min_length": "8",
        "requirements": [
            "At least one uppercase letter",
            "At least one lowercase letter", 
            "At least one number",
            "At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
        ]
    }
