# AITM System Architecture Documentation

## Overview

This document serves as the comprehensive architecture documentation for the AITM (AI-Powered Threat Modeler) system, specifically focusing on the implemented API Authorization Security system. The documentation is organized into three main sections that provide complete coverage of the system's security architecture, data flows, and technical decisions.

## Documentation Structure

### 1. Security Architecture Overview
**File**: `security-architecture-overview.md`

Provides a comprehensive overview of the four-layer security architecture implemented in the AITM system:

- **Executive Summary**: High-level security architecture overview
- **Security Layers Architecture**: Detailed breakdown of API, Service, Data, and JWT security layers
- **Security Component Interactions**: How security components work together
- **Security Audit and Monitoring**: Comprehensive logging and monitoring capabilities
- **Production Security Considerations**: Environment-specific security controls

**Key Highlights**:
- Multi-layered defense-in-depth security model
- Role-based access control with granular permissions
- Ownership-based resource access control
- Comprehensive security audit logging
- Production-hardened JWT token management

### 2. Data Flows and Component Relationships
**File**: `data-flows-and-components.md`

Maps the complete system architecture with detailed data flows and component relationships:

- **System Overview**: High-level architecture diagram
- **Request/Response Flow Analysis**: Detailed flow diagrams for key operations
- **Component Dependencies**: Complete dependency mapping
- **User Context Flow**: How user context propagates through the system
- **Integration Points**: Database and external service integrations
- **Security Context Flow**: Authorization decision flows

**Key Highlights**:
- Complete request/response flow documentation
- User context propagation throughout the system
- Component dependency analysis
- Database relationship mapping
- Security event flow documentation

### 3. Technical Decisions and Architecture Rationale
**File**: `technical-decisions-and-rationale.md`

Documents all major architectural decisions with rationale and alternatives considered:

- **Decision Framework**: Criteria used for architectural decisions
- **Core Architecture Decisions**: Multi-layered security, ownership-based access control
- **Technology Stack Decisions**: FastAPI, SQLAlchemy, JWT authentication
- **Security Implementation Decisions**: Security through obscurity, explicit user object passing
- **Performance and Scalability Decisions**: Async/await, connection pooling
- **Future Architecture Considerations**: Microservices readiness, API versioning

**Key Highlights**:
- Comprehensive decision documentation with rationale
- Alternatives considered and trade-offs evaluated
- Implementation impact assessment
- Future evolution planning
- Lessons learned and recommendations

## Architecture Summary

### Security Architecture
The AITM system implements a comprehensive four-layer security architecture:

1. **API Security Layer**: JWT validation, CORS configuration, request validation
2. **Service Security Layer**: RBAC, object-level permissions, user context management
3. **Data Security Layer**: Ownership validation, admin privileges, query filtering
4. **JWT Security Layer**: Token management, production validation, lifecycle management

### Key Security Features
- **Multi-layered Defense**: Four independent security layers provide comprehensive protection
- **Ownership-Based Access**: Users can only access resources they own (with admin override)
- **Role-Based Permissions**: Hierarchical role system with granular permission controls
- **Comprehensive Auditing**: All security events logged with structured data
- **Production Hardening**: Environment-specific security validation and controls

### Technology Stack
- **Framework**: FastAPI with async/await support
- **Database**: SQLAlchemy ORM with async support (SQLite dev, PostgreSQL-ready)
- **Authentication**: JWT tokens with comprehensive production validation
- **Security**: Custom RBAC system with object-level permissions
- **Monitoring**: Structured logging with security audit capabilities

### Data Flow Patterns
- **Authentication Flow**: JWT token validation → user context extraction → permission validation
- **Authorization Flow**: Permission check → resource access validation → ownership verification
- **Resource Access Flow**: API request → authentication → authorization → service logic → database query
- **Audit Flow**: Security event → structured logging → audit trail → monitoring

## Implementation Highlights

### Security Implementation
```python
# Multi-layer security validation
@router.get("/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_PROJECTS))
):
    # Layer 1: API authentication (handled by dependency)
    # Layer 2: Service authorization
    if not can_access_project(current_user, project):
        raise HTTPException(404, "Project not found")  # Security through obscurity
    # Layer 3: Data access with ownership validation
    # Layer 4: JWT security (handled in auth service)
```

### Permission System
```python
# Hierarchical role-based permissions
ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: {Permission.CREATE_PROJECTS, Permission.VIEW_PROJECTS, ...},
    Role.ADMIN: {Permission.CREATE_PROJECTS, Permission.VIEW_PROJECTS, ...},
    Role.ANALYST: {Permission.CREATE_PROJECTS, Permission.VIEW_PROJECTS, ...},
    Role.VIEWER: {Permission.VIEW_PROJECTS, ...}
}

# Ownership-based access control
def can_access_project(user: User, project) -> bool:
    return (project.owner_user_id == user.id or 
            user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value])
```

### Security Audit Logging
```python
# Structured security event logging
@dataclass
class SecurityEvent:
    event_type: SecurityEventType
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    result: Optional[str] = None
    error_code: Optional[str] = None

# Comprehensive audit trail
audit_logger.log_project_access_denied(
    user_id=current_user.id,
    project_id=str(project_id),
    error_code="INSUFFICIENT_PERMISSIONS"
)
```

## System Capabilities

### Current Capabilities
- **Secure Authentication**: JWT-based authentication with production validation
- **Granular Authorization**: Role-based permissions with object-level access control
- **Comprehensive Auditing**: Structured logging of all security events
- **Ownership-Based Access**: Strict resource ownership with administrative override
- **Production Ready**: Environment-specific security configuration and validation

### Security Controls
- **Authentication**: JWT token validation with secure key management
- **Authorization**: Multi-layer permission validation with RBAC
- **Access Control**: Ownership-based resource access with admin privileges
- **Audit Logging**: Comprehensive security event logging and monitoring
- **Error Handling**: Secure error responses with information disclosure prevention

### Scalability Features
- **Async Architecture**: Non-blocking I/O operations throughout the system
- **Connection Pooling**: Efficient database connection management
- **Stateless Authentication**: JWT tokens enable horizontal scaling
- **Service Boundaries**: Clear separation of concerns for future microservices

## Future Evolution

### Planned Enhancements
- **Team-Based Collaboration**: Enhanced sharing and collaboration features
- **Advanced Analytics**: Comprehensive security analytics and reporting
- **External Integrations**: SSO, LDAP, and enterprise system integration
- **Microservices Migration**: Service decomposition for independent scaling

### Scalability Roadmap
- **Horizontal Scaling**: Load balancing and service distribution
- **Database Scaling**: PostgreSQL migration and read replicas
- **Caching Layer**: Redis integration for performance optimization
- **Monitoring Enhancement**: Advanced monitoring and alerting capabilities

## Compliance and Security

### Security Standards
- **Defense in Depth**: Multi-layered security architecture
- **Principle of Least Privilege**: Minimal required permissions by default
- **Security by Design**: Security considerations integrated from the beginning
- **Comprehensive Auditing**: Full audit trail for compliance requirements

### Compliance Features
- **Audit Trails**: Comprehensive logging of all security-relevant events
- **Data Protection**: User data privacy and protection controls
- **Access Controls**: Granular permission system with administrative oversight
- **Security Monitoring**: Real-time monitoring of security events and violations

## Conclusion

The AITM system architecture represents a comprehensive, security-first approach to building a threat modeling platform. The multi-layered security architecture, combined with ownership-based access control and comprehensive auditing, provides a robust foundation for handling sensitive threat modeling data.

The architecture is designed for scalability and maintainability, with clear service boundaries and well-documented technical decisions. The comprehensive documentation ensures that the system can be effectively maintained and evolved as requirements change.

Key architectural strengths include:
- **Security**: Comprehensive multi-layer security architecture
- **Scalability**: Async architecture with clear service boundaries
- **Maintainability**: Well-documented decisions and clear separation of concerns
- **Compliance**: Comprehensive auditing and access control capabilities
- **Evolution**: Designed for future enhancement and microservices migration

This architecture documentation provides the foundation for continued development and serves as a reference for understanding the system's security model, data flows, and technical decisions.