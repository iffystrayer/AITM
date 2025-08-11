# Design Document

## Overview

This design addresses critical security vulnerabilities in the AITM platform by implementing comprehensive API authorization and fixing permissive data access patterns. The current system has a fundamental security flaw where any authenticated user can access, modify, and delete all data in the system. This design provides a multi-layered security approach with proper authorization checks at the API, service, and data access layers.

## Architecture

### Current State Analysis

The audit revealed several critical issues:

1. **Missing API Authorization**: Project endpoints in `backend/app/api/v1/endpoints/projects.py` lack permission checks
2. **Permissive Data Access**: The `can_access_project` function allows any user with `VIEW_PROJECTS` permission to see all projects
3. **Fragile Permission Logic**: The `check_permission` decorator uses brittle logic to find user objects
4. **Insecure JWT Handling**: Missing `SECRET_KEY` environment variable validation in production

### Target Architecture

The solution implements a defense-in-depth approach with three security layers:

1. **API Layer**: FastAPI dependency injection for endpoint-level authorization
2. **Service Layer**: Business logic validation with explicit permission checks
3. **Data Layer**: Object-level permissions for resource access control

## Components and Interfaces

### 1. Enhanced Permission System

#### Current Permission Issues
- `can_access_project()` defaults to permissive access for users with `VIEW_PROJECTS`
- `check_permission` decorator has fragile user object discovery
- No object-level ownership validation

#### Enhanced Design
```python
# Object-level permission functions
def can_access_project(user: User, project: Project) -> bool:
    """Check if user can access a specific project with ownership validation"""
    
def can_modify_project(user: User, project: Project) -> bool:
    """Check if user can modify a specific project"""
    
def can_delete_project(user: User, project: Project) -> bool:
    """Check if user can delete a specific project"""

# Enhanced permission dependencies
def require_project_access(project_id: int):
    """Dependency factory for project access validation"""
    
def require_project_modification(project_id: int):
    """Dependency factory for project modification validation"""
```

### 2. Secure API Endpoints

#### Current State
- No authorization checks on project endpoints
- Direct database access without permission validation
- Missing user context in operations

#### Enhanced Design
```python
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_project_access(project_id))
):
    """Get project with proper authorization"""

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_project_modification(project_id))
):
    """Update project with ownership validation"""
```

### 3. Production Security Configuration

#### Current Issues
- JWT `SECRET_KEY` falls back to generated key on restart
- No production environment validation
- User sessions invalidated on deployment

#### Enhanced Design
```python
def validate_production_config():
    """Validate required security configuration in production"""
    if os.getenv("ENVIRONMENT") == "production":
        if not os.getenv("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY environment variable required in production")
```

## Data Models

### Project Ownership Model

The existing `Project` model already includes `owner_user_id` field, which will be leveraged for ownership-based access control:

```python
# Existing Project model structure
class Project:
    id: int
    owner_user_id: str  # Links to User.id
    name: str
    # ... other fields
```

### Permission Context Model

New context model for explicit permission passing:

```python
@dataclass
class PermissionContext:
    """Explicit permission context for service operations"""
    user: User
    requested_permission: Permission
    resource_id: Optional[int] = None
    resource_type: Optional[str] = None
```

## Error Handling

### Authorization Error Responses

Standardized error responses for authorization failures:

```python
# 401 Unauthorized - Missing or invalid authentication
{
    "detail": "Authentication required",
    "error_code": "AUTH_REQUIRED"
}

# 403 Forbidden - Insufficient permissions
{
    "detail": "Permission denied: edit_projects required",
    "error_code": "INSUFFICIENT_PERMISSIONS",
    "required_permission": "edit_projects"
}

# 404 Not Found - Resource doesn't exist or no access
{
    "detail": "Project not found",
    "error_code": "RESOURCE_NOT_FOUND"
}
```

### Security Event Logging

Enhanced logging for security events:

```python
# Permission denied events
logger.warning(
    "Permission denied",
    extra={
        "user_id": user.id,
        "requested_permission": permission.value,
        "resource_type": "project",
        "resource_id": project_id,
        "user_role": user.role
    }
)

# Unauthorized access attempts
logger.warning(
    "Unauthorized access attempt",
    extra={
        "endpoint": request.url.path,
        "method": request.method,
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host
    }
)
```

## Testing Strategy

### Unit Tests

1. **Permission Function Tests**
   - Test `can_access_project` with various user roles and ownership scenarios
   - Test `can_modify_project` with owner, admin, and unauthorized users
   - Test `can_delete_project` with proper permission validation

2. **Dependency Tests**
   - Test `require_project_access` dependency with valid and invalid scenarios
   - Test `require_project_modification` with ownership validation
   - Test error responses for unauthorized access

3. **Configuration Tests**
   - Test production environment validation
   - Test JWT secret key requirement enforcement
   - Test development mode fallback behavior

### Integration Tests

1. **API Endpoint Security Tests**
   - Test all project endpoints with unauthorized users
   - Test cross-user data access prevention
   - Test admin privilege escalation scenarios

2. **End-to-End Authorization Tests**
   - Test complete user workflows with proper authorization
   - Test multi-user scenarios with data isolation
   - Test role-based access control across all endpoints

### Security Tests

1. **Authorization Bypass Tests**
   - Attempt to access projects without authentication
   - Attempt to modify projects owned by other users
   - Test privilege escalation attempts

2. **Token Security Tests**
   - Test JWT token validation and expiration
   - Test refresh token security
   - Test production secret key enforcement

## Implementation Phases

### Phase 1: Core Permission System (Critical)
- Fix `can_access_project` to enforce ownership
- Implement object-level permission functions
- Add production configuration validation

### Phase 2: API Authorization (Critical)
- Add authorization dependencies to all project endpoints
- Implement explicit user context passing
- Add comprehensive error handling

### Phase 3: Enhanced Security (High)
- Implement security event logging
- Add rate limiting for failed authorization attempts
- Enhance JWT token security

### Phase 4: Testing & Validation (High)
- Comprehensive test suite for all authorization scenarios
- Security penetration testing
- Performance impact assessment

## Security Considerations

### Defense in Depth
- Multiple layers of authorization checks
- Explicit permission validation at each layer
- Fail-secure defaults (deny access when in doubt)

### Principle of Least Privilege
- Users can only access resources they own or have explicit permission for
- Admin privileges required for cross-user resource access
- Clear separation between user and admin operations

### Audit Trail
- All authorization decisions logged
- Failed access attempts tracked
- User activity monitoring for security analysis

### Production Hardening
- Required environment variable validation
- Secure JWT secret key management
- Protection against common attack vectors