# Data Flows and Component Relationships

## System Overview

The AITM system follows a layered architecture with clear separation of concerns and well-defined data flows between components. This document maps the complete request/response flows, component dependencies, and user context propagation throughout the system.

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE[Svelte Frontend]
        FE --> |HTTP/HTTPS| API
    end
    
    subgraph "API Gateway Layer"
        API[FastAPI Application]
        CORS[CORS Middleware]
        ROUTER[API Router v1]
        
        API --> CORS
        CORS --> ROUTER
    end
    
    subgraph "Authentication Layer"
        AUTH[Auth Service]
        JWT[JWT Handler]
        SEC[Security Audit]
        
        ROUTER --> AUTH
        AUTH --> JWT
        AUTH --> SEC
    end
    
    subgraph "Authorization Layer"
        PERM[Permission Service]
        RBAC[Role-Based Access Control]
        OBJ[Object-Level Permissions]
        
        AUTH --> PERM
        PERM --> RBAC
        RBAC --> OBJ
    end
    
    subgraph "Service Layer"
        USER_SVC[User Service]
        COLLAB_SVC[Collaboration Service]
        ANALYTICS_SVC[Analytics Service]
        AI_SVC[Enhanced AI Service]
        
        OBJ --> USER_SVC
        OBJ --> COLLAB_SVC
        OBJ --> ANALYTICS_SVC
        OBJ --> AI_SVC
    end
    
    subgraph "Data Layer"
        DB[(SQLite Database)]
        MODELS[SQLAlchemy Models]
        
        USER_SVC --> MODELS
        COLLAB_SVC --> MODELS
        ANALYTICS_SVC --> MODELS
        AI_SVC --> MODELS
        MODELS --> DB
    end
```

## Request/Response Flow Analysis

### 1. Project Creation Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Perm
    participant Service
    participant DB
    participant Audit
    
    Client->>API: POST /api/v1/projects
    API->>Auth: Validate JWT Token
    Auth->>Auth: Extract User Context
    Auth->>Perm: Check CREATE_PROJECTS Permission
    Perm->>Perm: Validate User Role
    Perm->>Service: Execute with User Context
    Service->>Service: Validate Project Data
    Service->>DB: Create Project with owner_user_id
    DB->>Service: Return Created Project
    Service->>Audit: Log Project Creation
    Service->>API: Return Project Response
    API->>Client: HTTP 201 Created
```

**Data Flow Details:**
1. **Client Request**: Frontend sends project creation request with JWT token
2. **Authentication**: API validates JWT token and extracts user context
3. **Authorization**: Permission service validates CREATE_PROJECTS permission
4. **Service Processing**: Project service validates data and sets ownership
5. **Database Operation**: SQLAlchemy creates project record with owner_user_id
6. **Audit Logging**: Security audit logs project creation event
7. **Response**: API returns created project data to client

### 2. Project Access Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Perm
    participant Service
    participant DB
    participant Audit
    
    Client->>API: GET /api/v1/projects/{id}
    API->>Auth: Validate JWT Token
    Auth->>Auth: Extract User Context
    Auth->>Perm: Check VIEW_PROJECTS Permission
    Perm->>Service: Execute with User Context
    Service->>DB: Query Project by ID
    DB->>Service: Return Project Data
    Service->>Service: Validate Ownership/Admin Access
    alt Access Granted
        Service->>Audit: Log Access Granted
        Service->>API: Return Project Data
        API->>Client: HTTP 200 OK
    else Access Denied
        Service->>Audit: Log Access Denied
        Service->>API: Return 404 Not Found
        API->>Client: HTTP 404 Not Found
    end
```

**Data Flow Details:**
1. **Client Request**: Frontend requests specific project by ID
2. **Authentication**: JWT token validated and user context extracted
3. **Permission Check**: VIEW_PROJECTS permission validated
4. **Database Query**: Project retrieved from database by ID
5. **Ownership Validation**: Service checks if user owns project or has admin privileges
6. **Access Decision**: Grant access if owned/admin, deny otherwise
7. **Audit Logging**: All access attempts logged for security monitoring
8. **Response**: Return project data or 404 for security through obscurity

### 3. User Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant UserSvc
    participant DB
    participant Audit
    
    Client->>API: POST /api/v1/auth/login
    API->>Auth: Process Login Request
    Auth->>UserSvc: Authenticate User
    UserSvc->>DB: Query User by Email
    DB->>UserSvc: Return User Data
    UserSvc->>UserSvc: Verify Password Hash
    alt Authentication Success
        UserSvc->>Auth: Return User Data
        Auth->>Auth: Generate JWT Tokens
        Auth->>Audit: Log Authentication Success
        Auth->>API: Return Tokens
        API->>Client: HTTP 200 with Tokens
    else Authentication Failure
        UserSvc->>Auth: Return None
        Auth->>Audit: Log Authentication Failure
        Auth->>API: Return Error
        API->>Client: HTTP 401 Unauthorized
    end
```

**Data Flow Details:**
1. **Login Request**: Client submits email/password credentials
2. **User Lookup**: User service queries database for user by email
3. **Password Verification**: BCrypt password hash verification
4. **Token Generation**: JWT access and refresh tokens created
5. **Audit Logging**: Authentication success/failure logged
6. **Response**: Tokens returned to client or error for failed authentication

## Component Dependencies

### Core Component Relationships

```mermaid
graph LR
    subgraph "Application Core"
        MAIN[main.py]
        CONFIG[config.py]
        LOGGING[logging.py]
    end
    
    subgraph "Authentication Components"
        AUTH[auth.py]
        PERM[permissions.py]
        DEPS[dependencies.py]
        AUDIT[security_audit.py]
    end
    
    subgraph "Data Components"
        DB[database.py]
        MODELS[models/]
        SCHEMAS[schemas.py]
    end
    
    subgraph "Service Components"
        USER_SVC[user_service.py]
        COLLAB_SVC[collaboration_service.py]
        ANALYTICS_SVC[analytics_service.py]
        AI_SVC[enhanced_ai_service.py]
    end
    
    subgraph "API Components"
        ROUTER[router.py]
        PROJECTS[projects.py]
        AUTH_EP[auth.py]
        COLLAB_EP[collaboration.py]
    end
    
    MAIN --> CONFIG
    MAIN --> LOGGING
    MAIN --> DB
    MAIN --> ROUTER
    
    AUTH --> CONFIG
    AUTH --> AUDIT
    PERM --> AUTH
    DEPS --> AUTH
    DEPS --> PERM
    
    MODELS --> DB
    SCHEMAS --> MODELS
    
    USER_SVC --> AUTH
    USER_SVC --> DB
    COLLAB_SVC --> DB
    ANALYTICS_SVC --> DB
    AI_SVC --> DB
    
    PROJECTS --> DEPS
    PROJECTS --> PERM
    PROJECTS --> USER_SVC
    AUTH_EP --> AUTH
    AUTH_EP --> USER_SVC
    COLLAB_EP --> COLLAB_SVC
    
    ROUTER --> PROJECTS
    ROUTER --> AUTH_EP
    ROUTER --> COLLAB_EP
```

### Dependency Analysis

#### Authentication Dependencies
- **auth.py** depends on: config.py, security_audit.py
- **permissions.py** depends on: auth.py, database.py, models/user.py
- **dependencies.py** depends on: auth.py, permissions.py, database.py
- **security_audit.py** has no dependencies (base component)

#### Service Dependencies
- **user_service.py** depends on: auth.py, models/user.py, database.py
- **collaboration_service.py** depends on: database.py, models/collaboration.py
- **analytics_service.py** depends on: database.py, models/analytics.py
- **enhanced_ai_service.py** depends on: database.py, llm_providers/

#### API Dependencies
- **projects.py** depends on: dependencies.py, permissions.py, user_service.py
- **auth.py** depends on: auth.py, user_service.py, security_audit.py
- **collaboration.py** depends on: collaboration_service.py, permissions.py

## User Context Flow

### User Context Propagation

```mermaid
graph TD
    JWT[JWT Token] --> AUTH[Auth Service]
    AUTH --> |Extract User ID| USER_ID[User ID]
    USER_ID --> |Database Lookup| USER_OBJ[User Object]
    USER_OBJ --> |Permission Check| PERM_CHECK[Permission Validation]
    PERM_CHECK --> |Service Call| SERVICE[Service Layer]
    SERVICE --> |Database Query| DB_QUERY[Database Operation]
    DB_QUERY --> |Ownership Filter| FILTERED[Filtered Results]
    FILTERED --> |Response| CLIENT[Client Response]
    
    AUTH --> |Log Event| AUDIT[Security Audit]
    PERM_CHECK --> |Log Decision| AUDIT
    SERVICE --> |Log Operation| AUDIT
```

### User Context Components

#### 1. JWT Token Structure
```json
{
  "sub": "user_123",
  "exp": 1642694400,
  "iat": 1642608000,
  "type": "access",
  "role": "analyst"
}
```

#### 2. User Object Structure
```python
class User:
    id: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role: str  # viewer, analyst, admin, super_admin
    created_at: datetime
    updated_at: datetime
```

#### 3. Permission Context
```python
class PermissionChecker:
    def __init__(self, user: User):
        self.user = user
        self.permissions = get_role_permissions(user.role)
    
    def can_access_project(self, project) -> bool:
        return (project.owner_user_id == user.id or 
                user.role in ['admin', 'super_admin'])
```

## Integration Points

### Database Integration

```mermaid
graph TB
    subgraph "Application Layer"
        API[API Endpoints]
        SVC[Service Layer]
    end
    
    subgraph "ORM Layer"
        SQLALCHEMY[SQLAlchemy ORM]
        MODELS[Database Models]
        SESSION[Async Session]
    end
    
    subgraph "Database Layer"
        SQLITE[(SQLite Database)]
        TABLES[Database Tables]
    end
    
    API --> SVC
    SVC --> SQLALCHEMY
    SQLALCHEMY --> MODELS
    MODELS --> SESSION
    SESSION --> SQLITE
    SQLITE --> TABLES
```

**Integration Details:**
- **Async Sessions**: All database operations use async SQLAlchemy sessions
- **Model Relationships**: SQLAlchemy relationships define foreign key constraints
- **Query Filtering**: Automatic filtering based on user context and permissions
- **Transaction Management**: Proper commit/rollback handling for data integrity

### External Service Integration

```mermaid
graph LR
    subgraph "AITM Core"
        API[API Layer]
        SVC[Service Layer]
    end
    
    subgraph "AI Services"
        OPENAI[OpenAI Provider]
        ANTHROPIC[Anthropic Provider]
        LLM[LLM Service]
    end
    
    subgraph "Security Services"
        MITRE[MITRE ATT&CK]
        AUDIT[Security Audit]
    end
    
    SVC --> LLM
    LLM --> OPENAI
    LLM --> ANTHROPIC
    SVC --> MITRE
    SVC --> AUDIT
```

**Integration Points:**
- **LLM Providers**: Pluggable AI service providers for threat analysis
- **MITRE ATT&CK**: Integration with MITRE framework for threat intelligence
- **Security Audit**: Centralized logging for all security events
- **Configuration**: Environment-based configuration for different integrations

## Data Model Relationships

### Core Entity Relationships

```mermaid
erDiagram
    User ||--o{ Project : owns
    Project ||--o{ SystemInput : contains
    Project ||--o{ Asset : has
    Project ||--o{ AttackPath : identifies
    Project ||--o{ Recommendation : generates
    Project ||--|| AnalysisState : tracks
    Project ||--|| AnalysisResults : produces
    
    User ||--o{ TeamMembership : participates
    Team ||--o{ TeamMembership : includes
    Project ||--o{ ProjectShare : shared_with
    Project ||--o{ ProjectComment : has_comments
    Project ||--o{ ActivityLog : logs_activity
    
    User {
        string id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        boolean is_superuser
        string role
        datetime created_at
        datetime updated_at
    }
    
    Project {
        int id PK
        string name
        text description
        string status
        string owner_user_id FK
        datetime created_at
        datetime updated_at
    }
    
    SystemInput {
        int id PK
        int project_id FK
        string input_type
        text content
        string filename
        datetime created_at
    }
```

### Relationship Details

#### User-Project Relationship
- **One-to-Many**: Each user can own multiple projects
- **Ownership**: Projects have owner_user_id foreign key to users.id
- **Access Control**: Ownership determines base access permissions
- **Admin Override**: Admin users can access all projects regardless of ownership

#### Project-Analysis Relationship
- **One-to-One**: Each project has one analysis state and one analysis result
- **State Tracking**: AnalysisState tracks current analysis progress
- **Result Storage**: AnalysisResults stores completed analysis data
- **Lifecycle Management**: State and results created/updated during analysis

#### Collaboration Relationships
- **Team Membership**: Many-to-many relationship between users and teams
- **Project Sharing**: Projects can be shared with teams or individual users
- **Activity Logging**: All project activities logged with user context
- **Comment System**: Users can comment on projects they have access to

## Security Context Flow

### Authorization Decision Flow

```mermaid
graph TD
    REQUEST[API Request] --> TOKEN[JWT Token Validation]
    TOKEN --> USER[User Context Extraction]
    USER --> PERM[Permission Check]
    PERM --> RESOURCE[Resource Access Check]
    
    RESOURCE --> OWNER{Is Owner?}
    OWNER -->|Yes| GRANT[Access Granted]
    OWNER -->|No| ADMIN{Is Admin?}
    ADMIN -->|Yes| GRANT
    ADMIN -->|No| DENY[Access Denied]
    
    GRANT --> AUDIT_SUCCESS[Log Success]
    DENY --> AUDIT_FAILURE[Log Failure]
    
    AUDIT_SUCCESS --> RESPONSE[Return Data]
    AUDIT_FAILURE --> ERROR[Return Error]
```

### Security Event Flow

```mermaid
graph LR
    EVENT[Security Event] --> LOGGER[Security Audit Logger]
    LOGGER --> FORMAT[JSON Formatting]
    FORMAT --> STREAM[Log Stream]
    STREAM --> FILE[Log File]
    STREAM --> MONITOR[Monitoring System]
    
    EVENT --> CONTEXT[Event Context]
    CONTEXT --> USER_INFO[User Information]
    CONTEXT --> RESOURCE_INFO[Resource Information]
    CONTEXT --> ACTION_INFO[Action Information]
    
    USER_INFO --> LOGGER
    RESOURCE_INFO --> LOGGER
    ACTION_INFO --> LOGGER
```

## Performance and Scalability Considerations

### Database Query Optimization
- **Indexed Queries**: Primary keys and foreign keys properly indexed
- **Filtered Queries**: Ownership-based filtering at database level
- **Async Operations**: Non-blocking database operations throughout
- **Connection Pooling**: SQLAlchemy connection pooling for efficiency

### Caching Strategy
- **User Context Caching**: JWT token validation results cached
- **Permission Caching**: Role-based permissions cached per user session
- **Static Data Caching**: MITRE ATT&CK data cached for performance
- **Query Result Caching**: Frequently accessed data cached appropriately

### Monitoring and Observability
- **Request Tracing**: Full request lifecycle tracking
- **Performance Metrics**: Response time and throughput monitoring
- **Error Tracking**: Comprehensive error logging and alerting
- **Security Monitoring**: Real-time security event monitoring

## Component Communication Patterns

### Synchronous Communication
- **API Endpoints**: HTTP request/response pattern
- **Service Calls**: Direct function calls within application
- **Database Operations**: Synchronous database queries with async/await
- **Authentication**: Real-time JWT validation and user lookup

### Asynchronous Communication
- **Background Tasks**: Analysis processing in background
- **Event Logging**: Asynchronous security event logging
- **Cache Updates**: Background cache refresh operations
- **Monitoring**: Asynchronous metrics collection

### Error Handling Patterns
- **Exception Propagation**: Structured exception handling throughout layers
- **Error Transformation**: Service errors transformed to appropriate HTTP responses
- **Audit Logging**: All errors logged with appropriate context
- **Client Communication**: Secure error messages without information leakage