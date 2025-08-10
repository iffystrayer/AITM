"""
Permission System for AITM

Provides role-based access control with granular permissions for different system operations.
Includes permission validation, role management, and access control decorators.
"""

import logging
from enum import Enum
from typing import Set, List, Dict, Optional, Callable, Any
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

class Permission(str, Enum):
    """System permissions enumeration"""
    
    # Project permissions
    CREATE_PROJECTS = "create_projects"
    VIEW_PROJECTS = "view_projects"
    EDIT_PROJECTS = "edit_projects"
    DELETE_PROJECTS = "delete_projects"
    
    # Analysis permissions
    RUN_ANALYSIS = "run_analysis"
    VIEW_ANALYSIS_RESULTS = "view_analysis_results"
    EXPORT_ANALYSIS = "export_analysis"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view_analytics"
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_TRENDS = "view_trends"
    VIEW_PREDICTIONS = "view_predictions"
    GENERATE_REPORTS = "generate_reports"
    EXPORT_DATA = "export_data"
    
    # User management permissions
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    MANAGE_ROLES = "manage_roles"
    
    # System permissions
    VIEW_SYSTEM_STATUS = "view_system_status"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    MANAGE_CACHE = "manage_cache"
    
    # API permissions
    ACCESS_API = "access_api"
    RATE_LIMIT_BYPASS = "rate_limit_bypass"

class Role(str, Enum):
    """System roles enumeration"""
    
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"

# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: {
        # Full system access
        Permission.CREATE_PROJECTS,
        Permission.VIEW_PROJECTS,
        Permission.EDIT_PROJECTS,
        Permission.DELETE_PROJECTS,
        Permission.RUN_ANALYSIS,
        Permission.VIEW_ANALYSIS_RESULTS,
        Permission.EXPORT_ANALYSIS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.VIEW_PREDICTIONS,
        Permission.GENERATE_REPORTS,
        Permission.EXPORT_DATA,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,
        Permission.MANAGE_ROLES,
        Permission.VIEW_SYSTEM_STATUS,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_LOGS,
        Permission.MANAGE_CACHE,
        Permission.ACCESS_API,
        Permission.RATE_LIMIT_BYPASS
    },
    
    Role.ADMIN: {
        # Administrative access
        Permission.CREATE_PROJECTS,
        Permission.VIEW_PROJECTS,
        Permission.EDIT_PROJECTS,
        Permission.DELETE_PROJECTS,
        Permission.RUN_ANALYSIS,
        Permission.VIEW_ANALYSIS_RESULTS,
        Permission.EXPORT_ANALYSIS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.VIEW_PREDICTIONS,
        Permission.GENERATE_REPORTS,
        Permission.EXPORT_DATA,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.VIEW_SYSTEM_STATUS,
        Permission.VIEW_LOGS,
        Permission.ACCESS_API
    },
    
    Role.ANALYST: {
        # Security analyst access
        Permission.CREATE_PROJECTS,
        Permission.VIEW_PROJECTS,
        Permission.EDIT_PROJECTS,
        Permission.RUN_ANALYSIS,
        Permission.VIEW_ANALYSIS_RESULTS,
        Permission.EXPORT_ANALYSIS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.VIEW_PREDICTIONS,
        Permission.GENERATE_REPORTS,
        Permission.EXPORT_DATA,
        Permission.ACCESS_API
    },
    
    Role.VIEWER: {
        # Read-only access
        Permission.VIEW_PROJECTS,
        Permission.VIEW_ANALYSIS_RESULTS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_TRENDS,
        Permission.ACCESS_API
    },
    
    Role.API_USER: {
        # API-only access
        Permission.ACCESS_API,
        Permission.VIEW_PROJECTS,
        Permission.VIEW_ANALYSIS_RESULTS,
        Permission.RUN_ANALYSIS
    }
}

class PermissionService:
    """Service for permission management and validation"""
    
    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS
    
    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """Get permissions for a specific role"""
        return self.role_permissions.get(role, set())
    
    def user_has_permission(self, user: User, permission: Permission) -> bool:
        """Check if a user has a specific permission"""
        if not user.is_active:
            return False
        
        user_role = Role(user.role) if user.role in [r.value for r in Role] else None
        if not user_role:
            return False
        
        user_permissions = self.get_role_permissions(user_role)
        return permission in user_permissions
    
    def user_has_any_permission(self, user: User, permissions: List[Permission]) -> bool:
        """Check if a user has any of the specified permissions"""
        return any(self.user_has_permission(user, perm) for perm in permissions)
    
    def user_has_all_permissions(self, user: User, permissions: List[Permission]) -> bool:
        """Check if a user has all of the specified permissions"""
        return all(self.user_has_permission(user, perm) for perm in permissions)
    
    def get_user_permissions(self, user: User) -> Set[Permission]:
        """Get all permissions for a user"""
        if not user.is_active:
            return set()
        
        user_role = Role(user.role) if user.role in [r.value for r in Role] else None
        if not user_role:
            return set()
        
        return self.get_role_permissions(user_role)
    
    def validate_permission_change(self, current_user: User, target_user: User, new_role: str) -> bool:
        """Validate if current user can change target user's role"""
        # Only super admins and admins can change roles
        if not self.user_has_permission(current_user, Permission.MANAGE_ROLES):
            return False
        
        # Super admins can change anyone's role
        if current_user.role == Role.SUPER_ADMIN.value:
            return True
        
        # Admins can't promote to super admin or modify other admins/super admins
        if (new_role == Role.SUPER_ADMIN.value or 
            target_user.role in [Role.SUPER_ADMIN.value, Role.ADMIN.value]):
            return False
        
        return True
    
    def get_available_roles(self, user: User) -> List[str]:
        """Get roles that a user can assign to others"""
        available_roles = []
        
        if self.user_has_permission(user, Permission.MANAGE_ROLES):
            if user.role == Role.SUPER_ADMIN.value:
                # Super admins can assign any role
                available_roles = [role.value for role in Role]
            elif user.role == Role.ADMIN.value:
                # Admins can assign roles except super admin
                available_roles = [
                    Role.ADMIN.value,
                    Role.ANALYST.value,
                    Role.VIEWER.value,
                    Role.API_USER.value
                ]
        
        return available_roles

# Global permission service instance
permission_service = PermissionService()

def get_permission_service() -> PermissionService:
    """Dependency to get permission service instance"""
    return permission_service

# FastAPI dependencies
def require_permission(permission: Permission):
    """Dependency factory to require a specific permission"""
    def dependency(current_user: User = Depends(get_current_user)):
        if not permission_service.user_has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required"
            )
        return current_user
    return dependency

def require_any_permission(*permissions: Permission):
    """Dependency factory to require any of the specified permissions"""
    def dependency(current_user: User = Depends(get_current_user)):
        if not permission_service.user_has_any_permission(current_user, list(permissions)):
            perm_names = [p.value for p in permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: One of {perm_names} required"
            )
        return current_user
    return dependency

def require_all_permissions(*permissions: Permission):
    """Dependency factory to require all of the specified permissions"""
    def dependency(current_user: User = Depends(get_current_user)):
        if not permission_service.user_has_all_permissions(current_user, list(permissions)):
            perm_names = [p.value for p in permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: All of {perm_names} required"
            )
        return current_user
    return dependency

def require_role(role: Role):
    """Dependency factory to require a specific role"""
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role != role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role denied: {role.value} role required"
            )
        return current_user
    return dependency

def require_active_user():
    """Dependency to ensure user is active"""
    def dependency(current_user: User = Depends(get_current_user)):
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        return current_user
    return dependency

# Decorators for non-FastAPI functions
def check_permission(permission: Permission):
    """Decorator to check permissions for regular functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to find user in kwargs or args
            user = kwargs.get('current_user') or kwargs.get('user')
            if not user:
                # Look for user in first few args
                for arg in args[:3]:
                    if isinstance(arg, User):
                        user = arg
                        break
            
            if not user:
                raise ValueError("User not found in function arguments")
            
            if not permission_service.user_has_permission(user, permission):
                raise PermissionError(f"Permission denied: {permission.value} required")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Project-specific permission checks
def can_access_project(user: User, project) -> bool:
    """Check if user can access a specific project"""
    # Basic permission check
    if not permission_service.user_has_permission(user, Permission.VIEW_PROJECTS):
        return False
    
    # Project owners can always access their projects
    if hasattr(project, 'owner_id') and project.owner_id == user.id:
        return True
    
    # Admins and super admins can access all projects
    if user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value]:
        return True
    
    # For now, allow access if user has basic view permission
    # In the future, you might implement more granular project-level permissions
    return True

def can_modify_project(user: User, project) -> bool:
    """Check if user can modify a specific project"""
    if not permission_service.user_has_permission(user, Permission.EDIT_PROJECTS):
        return False
    
    # Project owners can modify their projects
    if hasattr(project, 'owner_id') and project.owner_id == user.id:
        return True
    
    # Admins and super admins can modify all projects
    if user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value]:
        return True
    
    return False

def can_delete_project(user: User, project) -> bool:
    """Check if user can delete a specific project"""
    if not permission_service.user_has_permission(user, Permission.DELETE_PROJECTS):
        return False
    
    # Project owners can delete their projects
    if hasattr(project, 'owner_id') and project.owner_id == user.id:
        return True
    
    # Only admins and super admins can delete others' projects
    if user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value]:
        return True
    
    return False

# Permission utilities
class PermissionChecker:
    """Utility class for permission checks"""
    
    def __init__(self, user: User):
        self.user = user
        self.service = permission_service
    
    def has(self, permission: Permission) -> bool:
        """Check if user has permission"""
        return self.service.user_has_permission(self.user, permission)
    
    def has_any(self, *permissions: Permission) -> bool:
        """Check if user has any of the permissions"""
        return self.service.user_has_any_permission(self.user, list(permissions))
    
    def has_all(self, *permissions: Permission) -> bool:
        """Check if user has all permissions"""
        return self.service.user_has_all_permissions(self.user, list(permissions))
    
    def is_admin(self) -> bool:
        """Check if user is admin or super admin"""
        return self.user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value]
    
    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.user.role == Role.SUPER_ADMIN.value
    
    def can_access_project(self, project) -> bool:
        """Check if user can access project"""
        return can_access_project(self.user, project)
    
    def can_modify_project(self, project) -> bool:
        """Check if user can modify project"""
        return can_modify_project(self.user, project)
    
    def can_delete_project(self, project) -> bool:
        """Check if user can delete project"""
        return can_delete_project(self.user, project)

def get_permission_checker(user: User) -> PermissionChecker:
    """Get permission checker for a user"""
    return PermissionChecker(user)

# Lazy import for get_current_user to avoid circular imports
def get_current_user():
    """Lazy import get_current_user from auth module"""
    from app.core.auth import auth_service
    return auth_service.get_current_user_from_token
