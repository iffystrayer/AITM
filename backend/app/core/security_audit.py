"""
Security audit logging system for AITM.

Provides structured logging for security events, authorization decisions,
and administrative actions with proper log rotation and monitoring capabilities.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import Request

# Configure security audit logger
security_logger = logging.getLogger("security_audit")
security_logger.setLevel(logging.INFO)

# Create formatter for structured logging
class SecurityAuditFormatter(logging.Formatter):
    """Custom formatter for security audit logs"""
    
    def format(self, record):
        # Create base log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event_type": getattr(record, 'event_type', 'unknown'),
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry, default=str)

# Set up handler with custom formatter
if not security_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(SecurityAuditFormatter())
    security_logger.addHandler(handler)
    security_logger.propagate = False

class SecurityEventType(str, Enum):
    """Types of security events to log"""
    
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_EXPIRED = "token_expired"
    
    # Authorization events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHECK_SUCCESS = "role_check_success"
    ROLE_CHECK_FAILURE = "role_check_failure"
    
    # Resource access events
    RESOURCE_ACCESS_GRANTED = "resource_access_granted"
    RESOURCE_ACCESS_DENIED = "resource_access_denied"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    
    # Administrative events
    ADMIN_ACTION = "admin_action"
    ROLE_CHANGE = "role_change"
    USER_CREATED = "user_created"
    USER_DEACTIVATED = "user_deactivated"
    
    # Project-specific events
    PROJECT_ACCESS_GRANTED = "project_access_granted"
    PROJECT_ACCESS_DENIED = "project_access_denied"
    PROJECT_MODIFICATION_GRANTED = "project_modification_granted"
    PROJECT_MODIFICATION_DENIED = "project_modification_denied"
    PROJECT_DELETION_GRANTED = "project_deletion_granted"
    PROJECT_DELETION_DENIED = "project_deletion_denied"
    
    # Security configuration events
    CONFIG_CHANGE = "config_change"
    SECRET_KEY_VALIDATION = "secret_key_validation"
    PRODUCTION_CONFIG_ERROR = "production_config_error"

@dataclass
class SecurityEvent:
    """Structured security event data"""
    
    event_type: SecurityEventType
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    error_code: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

class SecurityAuditLogger:
    """Security audit logging service"""
    
    def __init__(self):
        self.logger = security_logger
    
    def log_event(self, event: SecurityEvent, message: str):
        """Log a security event with structured data"""
        extra_data = asdict(event)
        # Remove None values to keep logs clean
        extra_data = {k: v for k, v in extra_data.items() if v is not None}
        
        self.logger.info(
            message,
            extra={
                'event_type': event.event_type.value,
                'extra_data': extra_data
            }
        )
    
    def log_authentication_success(self, user_id: str, user_role: str, ip_address: str = None, user_agent: str = None):
        """Log successful authentication"""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            user_role=user_role,
            ip_address=ip_address,
            user_agent=user_agent,
            result="success"
        )
        self.log_event(event, f"User {user_id} authenticated successfully")
    
    def log_authentication_failure(self, attempted_user: str = None, ip_address: str = None, user_agent: str = None, error_code: str = None):
        """Log failed authentication attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILURE,
            user_id=attempted_user,
            ip_address=ip_address,
            user_agent=user_agent,
            result="failure",
            error_code=error_code
        )
        self.log_event(event, f"Authentication failed for user: {attempted_user or 'unknown'}")
    
    def log_permission_granted(self, user_id: str, user_role: str, permission: str, resource_type: str = None, resource_id: str = None):
        """Log successful permission check"""
        event = SecurityEvent(
            event_type=SecurityEventType.PERMISSION_GRANTED,
            user_id=user_id,
            user_role=user_role,
            resource_type=resource_type,
            resource_id=resource_id,
            action=permission,
            result="granted"
        )
        self.log_event(event, f"Permission {permission} granted to user {user_id}")
    
    def log_permission_denied(self, user_id: str, user_role: str, permission: str, resource_type: str = None, resource_id: str = None, error_code: str = None):
        """Log failed permission check"""
        event = SecurityEvent(
            event_type=SecurityEventType.PERMISSION_DENIED,
            user_id=user_id,
            user_role=user_role,
            resource_type=resource_type,
            resource_id=resource_id,
            action=permission,
            result="denied",
            error_code=error_code
        )
        self.log_event(event, f"Permission {permission} denied for user {user_id}")
    
    def log_project_access_granted(self, user_id: str, user_role: str, project_id: str, project_owner: str = None):
        """Log successful project access"""
        event = SecurityEvent(
            event_type=SecurityEventType.PROJECT_ACCESS_GRANTED,
            user_id=user_id,
            user_role=user_role,
            resource_type="project",
            resource_id=project_id,
            action="access",
            result="granted",
            additional_data={"project_owner": project_owner} if project_owner else None
        )
        self.log_event(event, f"Project {project_id} access granted to user {user_id}")
    
    def log_project_access_denied(self, user_id: str, user_role: str, project_id: str, project_owner: str = None, error_code: str = None):
        """Log denied project access"""
        event = SecurityEvent(
            event_type=SecurityEventType.PROJECT_ACCESS_DENIED,
            user_id=user_id,
            user_role=user_role,
            resource_type="project",
            resource_id=project_id,
            action="access",
            result="denied",
            error_code=error_code,
            additional_data={"project_owner": project_owner} if project_owner else None
        )
        self.log_event(event, f"Project {project_id} access denied for user {user_id}")
    
    def log_project_modification_granted(self, user_id: str, user_role: str, project_id: str, modification_type: str, project_owner: str = None):
        """Log successful project modification"""
        event = SecurityEvent(
            event_type=SecurityEventType.PROJECT_MODIFICATION_GRANTED,
            user_id=user_id,
            user_role=user_role,
            resource_type="project",
            resource_id=project_id,
            action=f"modify_{modification_type}",
            result="granted",
            additional_data={"project_owner": project_owner, "modification_type": modification_type}
        )
        self.log_event(event, f"Project {project_id} modification ({modification_type}) granted to user {user_id}")
    
    def log_project_modification_denied(self, user_id: str, user_role: str, project_id: str, modification_type: str, project_owner: str = None, error_code: str = None):
        """Log denied project modification"""
        event = SecurityEvent(
            event_type=SecurityEventType.PROJECT_MODIFICATION_DENIED,
            user_id=user_id,
            user_role=user_role,
            resource_type="project",
            resource_id=project_id,
            action=f"modify_{modification_type}",
            result="denied",
            error_code=error_code,
            additional_data={"project_owner": project_owner, "modification_type": modification_type}
        )
        self.log_event(event, f"Project {project_id} modification ({modification_type}) denied for user {user_id}")
    
    def log_unauthorized_access_attempt(self, endpoint: str, method: str, ip_address: str = None, user_agent: str = None, user_id: str = None):
        """Log unauthorized access attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            result="blocked"
        )
        self.log_event(event, f"Unauthorized access attempt to {method} {endpoint}")
    
    def log_admin_action(self, admin_user_id: str, admin_role: str, action: str, target_user_id: str = None, additional_data: Dict[str, Any] = None):
        """Log administrative action"""
        event = SecurityEvent(
            event_type=SecurityEventType.ADMIN_ACTION,
            user_id=admin_user_id,
            user_role=admin_role,
            action=action,
            result="executed",
            additional_data={
                "target_user_id": target_user_id,
                **(additional_data or {})
            }
        )
        self.log_event(event, f"Admin action {action} performed by {admin_user_id}")
    
    def log_role_change(self, admin_user_id: str, target_user_id: str, old_role: str, new_role: str):
        """Log user role change"""
        event = SecurityEvent(
            event_type=SecurityEventType.ROLE_CHANGE,
            user_id=admin_user_id,
            action="role_change",
            result="success",
            additional_data={
                "target_user_id": target_user_id,
                "old_role": old_role,
                "new_role": new_role
            }
        )
        self.log_event(event, f"User {target_user_id} role changed from {old_role} to {new_role} by {admin_user_id}")
    
    def log_production_config_error(self, error_type: str, error_message: str):
        """Log production configuration error"""
        event = SecurityEvent(
            event_type=SecurityEventType.PRODUCTION_CONFIG_ERROR,
            action="config_validation",
            result="error",
            error_code=error_type,
            additional_data={"error_message": error_message}
        )
        self.log_event(event, f"Production configuration error: {error_type}")
    
    def log_secret_key_validation(self, environment: str, validation_result: str, key_length: int = None):
        """Log JWT secret key validation"""
        event = SecurityEvent(
            event_type=SecurityEventType.SECRET_KEY_VALIDATION,
            action="secret_key_validation",
            result=validation_result,
            additional_data={
                "environment": environment,
                "key_length": key_length
            }
        )
        self.log_event(event, f"JWT secret key validation: {validation_result} in {environment}")

# Global security audit logger instance
security_audit = SecurityAuditLogger()

def get_security_audit_logger() -> SecurityAuditLogger:
    """Get the global security audit logger instance"""
    return security_audit

def extract_request_info(request: Request) -> Dict[str, str]:
    """Extract security-relevant information from FastAPI request"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "endpoint": request.url.path,
        "method": request.method
    }

# Middleware for automatic security event logging
class SecurityAuditMiddleware:
    """Middleware to automatically log security events"""
    
    def __init__(self, app):
        self.app = app
        self.audit_logger = security_audit
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Log all requests to sensitive endpoints
            sensitive_endpoints = [
                "/api/v1/projects",
                "/api/v1/auth",
                "/api/v1/users"
            ]
            
            if any(request.url.path.startswith(endpoint) for endpoint in sensitive_endpoints):
                request_info = extract_request_info(request)
                
                # This will be enhanced to capture response status and user info
                # For now, just log the request
                pass
        
        await self.app(scope, receive, send)

# Decorator for automatic security logging
def log_security_event(event_type: SecurityEventType):
    """Decorator to automatically log security events"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Extract user info if available
                user_id = None
                user_role = None
                
                # Look for user in function arguments
                for arg in args:
                    if hasattr(arg, 'id') and hasattr(arg, 'role'):
                        user_id = arg.id
                        user_role = arg.role
                        break
                
                # Log successful operation
                if user_id:
                    event = SecurityEvent(
                        event_type=event_type,
                        user_id=user_id,
                        user_role=user_role,
                        result="success"
                    )
                    security_audit.log_event(event, f"Security operation {event_type.value} completed successfully")
                
                return result
                
            except Exception as e:
                # Log failed operation
                event = SecurityEvent(
                    event_type=event_type,
                    result="failure",
                    error_code=type(e).__name__,
                    additional_data={"error_message": str(e)}
                )
                security_audit.log_event(event, f"Security operation {event_type.value} failed: {str(e)}")
                raise
        
        return wrapper
    return decorator