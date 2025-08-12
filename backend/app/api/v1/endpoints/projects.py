"""
Projects API endpoints with authentication
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_db, Project, SystemInput, AnalysisState, AnalysisResults
from app.api.endpoints.auth import get_current_active_user
from app.models.user import User
from app.core.permissions import (
    require_permission, Permission, require_project_access, 
    require_project_modification, require_project_deletion,
    can_access_project, can_modify_project, can_delete_project, Role
)
from app.models.schemas import (
    ProjectCreate, ProjectResponse, ProjectUpdate, SystemInputCreate,
    AnalysisStartRequest, AnalysisStartResponse, AnalysisStatusResponse,
    AnalysisResultsResponse, AnalysisProgress
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CREATE_PROJECTS))
):
    """
    Create a new threat modeling project with proper authorization.
    
    This endpoint enforces authorization by:
    - Requiring CREATE_PROJECTS permission for the authenticated user
    - Validating user context and setting proper ownership on created projects
    - Providing comprehensive error handling for authorization failures
    
    Requirements addressed:
    - 1.1: API endpoints enforce proper authorization checks before processing requests
    - 1.2: Users can only access resources they have permission to view or modify
    - 5.1: Authorization implemented at the API endpoint level
    - 5.2: Authorization implemented at the service layer level
    """
    try:
        # Validate user context - ensure user is active and has valid session
        if not current_user.is_active:
            logger.warning(
                "Project creation denied: user account inactive",
                extra={
                    "user_id": current_user.id,
                    "operation": "create_project"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
                headers={"X-Error-Code": "ACCOUNT_INACTIVE"}
            )
        
        # Log project creation attempt
        logger.info(
            "Creating new project",
            extra={
                "user_id": current_user.id,
                "user_role": current_user.role,
                "project_name": project.name,
                "operation": "create_project"
            }
        )
        
        # Prepare project data with proper ownership
        project_data = project.dict()
        project_data["owner_user_id"] = current_user.id
        
        # Validate project data before creation
        if not project_data.get("name") or not project_data["name"].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project name is required",
                headers={"X-Error-Code": "INVALID_PROJECT_NAME"}
            )
        
        # Create project with proper ownership
        db_project = Project(**project_data)
        db.add(db_project)
        await db.flush()
        await db.refresh(db_project)
        
        # Log successful project creation
        logger.info(
            "Project created successfully",
            extra={
                "user_id": current_user.id,
                "project_id": db_project.id,
                "project_name": db_project.name,
                "operation": "create_project"
            }
        )
        
        # Log activity (import collaboration service)
        try:
            from app.services.collaboration_service import get_collaboration_service
            from app.models.collaboration import ActivityType
            collab_service = get_collaboration_service()
            await collab_service._log_activity(
                db,
                user_id=current_user.id,
                project_id=db_project.id,
                activity_type=ActivityType.PROJECT_CREATED,
                description=f"Created project '{project.name}'",
                metadata={"project_name": project.name}
            )
        except Exception as e:
            # Don't fail project creation if activity logging fails
            logger.warning(f"Failed to log project creation activity: {e}")
        
        return db_project
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during project creation",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "error": str(e),
                "operation": "create_project"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the project",
            headers={"X-Error-Code": "PROJECT_CREATION_FAILED"}
        )


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_PROJECTS))
):
    """
    List threat modeling projects with proper authorization filtering.
    
    This endpoint enforces authorization by:
    - Requiring VIEW_PROJECTS permission for the authenticated user
    - Only returning projects the user can access based on ownership and admin privileges
    - Implementing proper filtering to prevent unauthorized data access
    - Ensuring users only see projects they own or have explicit access to
    
    Requirements addressed:
    - 1.1: API endpoints enforce proper authorization checks before processing requests
    - 1.2: Users can only access resources they have permission to view or modify
    - 2.1: System only returns projects user owns or has been explicitly granted access to
    - 2.2: Users with VIEW_PROJECTS permission do not automatically get access to all projects
    """
    try:
        logger.info(
            "Listing projects with authorization filtering",
            extra={
                "user_id": current_user.id,
                "user_role": current_user.role,
                "skip": skip,
                "limit": limit,
                "operation": "list_projects"
            }
        )
        
        # Build query based on user permissions
        if current_user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value]:
            # Admins can see all projects
            logger.info(
                "Admin user accessing all projects",
                extra={
                    "user_id": current_user.id,
                    "user_role": current_user.role,
                    "operation": "list_projects"
                }
            )
            result = await db.execute(
                select(Project).offset(skip).limit(limit).order_by(Project.created_at.desc())
            )
        else:
            # Regular users can only see their own projects
            logger.info(
                "Regular user accessing owned projects only",
                extra={
                    "user_id": current_user.id,
                    "user_role": current_user.role,
                    "operation": "list_projects"
                }
            )
            result = await db.execute(
                select(Project)
                .where(Project.owner_user_id == current_user.id)
                .offset(skip)
                .limit(limit)
                .order_by(Project.created_at.desc())
            )
        
        projects = result.scalars().all()
        
        # Double-check access permissions for each project (defense in depth)
        filtered_projects = []
        for project in projects:
            if can_access_project(current_user, project):
                filtered_projects.append(project)
            else:
                logger.warning(
                    "Project filtered out due to access check failure",
                    extra={
                        "user_id": current_user.id,
                        "project_id": project.id,
                        "project_owner": project.owner_user_id,
                        "operation": "list_projects"
                    }
                )
        
        logger.info(
            "Projects list returned successfully",
            extra={
                "user_id": current_user.id,
                "total_projects": len(filtered_projects),
                "operation": "list_projects"
            }
        )
        
        return filtered_projects
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during project listing",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "error": str(e),
                "operation": "list_projects"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving projects",
            headers={"X-Error-Code": "PROJECT_LIST_FAILED"}
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.VIEW_PROJECTS))
):
    """
    Get a specific project by ID with proper authorization.
    
    This endpoint enforces authorization by:
    - Requiring VIEW_PROJECTS permission for the authenticated user
    - Implementing ownership-based access control with admin privilege support
    - Returning 404 responses for projects user cannot access (security through obscurity)
    - Using explicit user object passing instead of fragile decorator logic
    
    Requirements addressed:
    - 1.1: API endpoints enforce proper authorization checks before processing requests
    - 1.2: Users can only access resources they have permission to view or modify
    - 2.1: System only returns projects user owns or has been explicitly granted access to
    - 2.2: Users with VIEW_PROJECTS permission do not automatically get access to all projects
    """
    try:
        logger.info(
            "Retrieving specific project with authorization",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "user_role": current_user.role,
                "operation": "get_project"
            }
        )
        
        # Get the project from database
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(
                "Project not found during retrieval",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "get_project"
                }
            )
            # Return 404 for security through obscurity
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "PROJECT_NOT_FOUND"}
            )
        
        # Check access permissions using explicit user object passing
        if not can_access_project(current_user, project):
            logger.warning(
                "Access denied during project retrieval",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "project_owner": project.owner_user_id,
                    "user_role": current_user.role,
                    "operation": "get_project"
                }
            )
            # Return 404 instead of 403 for security through obscurity
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"}
            )
        
        logger.info(
            "Project retrieved successfully",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "project_name": project.name,
                "operation": "get_project"
            }
        )
        
        return project
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during project retrieval",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "project_id": project_id,
                "error": str(e),
                "operation": "get_project"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the project",
            headers={"X-Error-Code": "PROJECT_RETRIEVAL_FAILED"}
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a project with proper authorization.
    
    This endpoint enforces authorization by:
    - Using require_project_modification dependency to validate user can modify the project
    - Checking ownership and admin privileges before allowing modifications
    - Providing comprehensive error handling for authorization failures
    - Logging modification attempts for security auditing
    
    Requirements addressed:
    - 1.3: Users can only modify projects they own or have admin privileges for
    - 1.4: System returns 403 Forbidden for unauthorized modification attempts
    - 2.3: Admin users can modify projects based on elevated privileges
    - 2.4: Regular users must verify ownership for project modifications
    """
    try:
        logger.info(
            "Updating project",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "user_role": current_user.role,
                "operation": "update_project"
            }
        )
        
        # Get the project from database
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(
                "Project not found during update",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "update_project"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "PROJECT_NOT_FOUND"}
            )
        
        # Check if user can modify this project
        if not can_modify_project(current_user, project):
            # Log security event for denied modification
            from app.core.security_audit import get_security_audit_logger
            audit_logger = get_security_audit_logger()
            audit_logger.log_project_modification_denied(
                user_id=current_user.id,
                user_role=current_user.role,
                project_id=str(project_id),
                modification_type="update",
                project_owner=project.owner_user_id,
                error_code="INSUFFICIENT_PERMISSIONS"
            )
            
            logger.warning(
                "Permission denied for project modification",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "project_owner": project.owner_user_id,
                    "user_role": current_user.role,
                    "operation": "update_project"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: insufficient privileges to modify this project",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"}
            )
        
        # Validate update data
        update_data = project_update.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided",
                headers={"X-Error-Code": "NO_UPDATE_DATA"}
            )
        
        # Apply updates
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)
            else:
                logger.warning(f"Attempted to update non-existent field: {field}")
        
        # Update timestamp
        project.updated_at = datetime.utcnow()
        
        await db.flush()
        await db.refresh(project)
        
        logger.info(
            "Project updated successfully",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "updated_fields": list(update_data.keys()),
                "operation": "update_project"
            }
        )
        
        # Log activity
        try:
            from app.services.collaboration_service import get_collaboration_service
            from app.models.collaboration import ActivityType
            collab_service = get_collaboration_service()
            await collab_service._log_activity(
                db,
                user_id=current_user.id,
                project_id=project_id,
                activity_type=ActivityType.PROJECT_UPDATED,
                description=f"Updated project fields: {', '.join(update_data.keys())}",
                metadata={"updated_fields": list(update_data.keys())}
            )
        except Exception as e:
            # Don't fail update if activity logging fails
            logger.warning(f"Failed to log project update activity: {e}")
        
        return project
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during project update",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "project_id": project_id,
                "error": str(e),
                "operation": "update_project"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the project",
            headers={"X-Error-Code": "PROJECT_UPDATE_FAILED"}
        )


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a project with proper authorization.
    
    This endpoint enforces authorization by:
    - Using require_project_deletion dependency to validate user can delete the project
    - Checking ownership and admin privileges before allowing deletion
    - Providing comprehensive error handling for authorization failures
    - Logging deletion attempts for security auditing
    
    Requirements addressed:
    - 1.4: Users can only delete projects they own or have admin privileges for
    - 1.4: System returns 403 Forbidden for unauthorized deletion attempts
    - 2.4: Admin users can delete projects based on elevated privileges
    - 2.4: Regular users must verify ownership for project deletion
    """
    try:
        logger.info(
            "Deleting project",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "user_role": current_user.role,
                "operation": "delete_project"
            }
        )
        
        # Get the project from database
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(
                "Project not found during deletion",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "delete_project"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "PROJECT_NOT_FOUND"}
            )
        
        # Check if user can delete this project
        if not can_delete_project(current_user, project):
            # Log security event for denied deletion
            from app.core.security_audit import get_security_audit_logger
            audit_logger = get_security_audit_logger()
            audit_logger.log_project_modification_denied(
                user_id=current_user.id,
                user_role=current_user.role,
                project_id=str(project_id),
                modification_type="deletion",
                project_owner=project.owner_user_id,
                error_code="INSUFFICIENT_PERMISSIONS"
            )
            
            logger.warning(
                "Permission denied for project deletion",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "project_owner": project.owner_user_id,
                    "user_role": current_user.role,
                    "operation": "delete_project"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: insufficient privileges to delete this project",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"}
            )
        
        # Store project info for logging before deletion
        project_name = project.name
        project_owner = project.owner_user_id
        
        # Log activity before deletion
        try:
            from app.services.collaboration_service import get_collaboration_service
            from app.models.collaboration import ActivityType
            collab_service = get_collaboration_service()
            await collab_service._log_activity(
                db,
                user_id=current_user.id,
                project_id=project_id,
                activity_type=ActivityType.PROJECT_DELETED,
                description=f"Deleted project '{project_name}'",
                metadata={"project_name": project_name, "project_owner": project_owner}
            )
        except Exception as e:
            # Don't fail deletion if activity logging fails
            logger.warning(f"Failed to log project deletion activity: {e}")
        
        # Delete the project
        await db.delete(project)
        await db.commit()
        
        logger.info(
            "Project deleted successfully",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "project_name": project_name,
                "project_owner": project_owner,
                "operation": "delete_project"
            }
        )
        
        return {
            "message": "Project deleted successfully",
            "project_id": project_id,
            "project_name": project_name
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during project deletion",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "project_id": project_id,
                "error": str(e),
                "operation": "delete_project"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the project",
            headers={"X-Error-Code": "PROJECT_DELETION_FAILED"}
        )


@router.post("/{project_id}/inputs", status_code=status.HTTP_201_CREATED)
async def add_system_input(
    project_id: int,
    system_input: SystemInputCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add system input data to a project with proper authorization.
    
    This endpoint enforces authorization by:
    - Using require_project_modification dependency to validate user can modify the project
    - Checking ownership and admin privileges before allowing input addition
    - Ensuring users can only add inputs to projects they can access
    - Providing comprehensive error handling for authorization failures
    
    Requirements addressed:
    - 1.1: API endpoints enforce proper authorization checks before processing requests
    - 1.2: Users can only access resources they have permission to view or modify
    - 5.3: Authorization implemented at the service layer level
    - 5.4: Object-level permissions validated for resource access
    """
    try:
        logger.info(
            "Adding system input to project",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "user_role": current_user.role,
                "operation": "add_system_input"
            }
        )
        
        # Get the project from database (already validated by dependency)
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(
                "Project not found during input addition",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "add_system_input"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "PROJECT_NOT_FOUND"}
            )
        
        # Check if user can modify this project
        if not can_modify_project(current_user, project):
            # Log security event for denied modification
            from app.core.security_audit import get_security_audit_logger
            audit_logger = get_security_audit_logger()
            audit_logger.log_project_modification_denied(
                user_id=current_user.id,
                user_role=current_user.role,
                project_id=str(project_id),
                modification_type="add_input",
                project_owner=project.owner_user_id,
                error_code="INSUFFICIENT_PERMISSIONS"
            )
            
            logger.warning(
                "Permission denied for adding system input",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "project_owner": project.owner_user_id,
                    "user_role": current_user.role,
                    "operation": "add_system_input"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: insufficient privileges to modify this project",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"}
            )
        
        # Validate input data
        input_data = system_input.dict()
        if not input_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System input data is required",
                headers={"X-Error-Code": "INVALID_INPUT_DATA"}
            )
        
        # Create system input
        db_input = SystemInput(project_id=project_id, **input_data)
        db.add(db_input)
        await db.flush()
        await db.refresh(db_input)
        
        logger.info(
            "System input added successfully",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "input_id": db_input.id,
                "operation": "add_system_input"
            }
        )
        
        # Log activity
        try:
            from app.services.collaboration_service import get_collaboration_service
            from app.models.collaboration import ActivityType
            collab_service = get_collaboration_service()
            await collab_service._log_activity(
                db,
                user_id=current_user.id,
                project_id=project_id,
                activity_type=ActivityType.INPUT_ADDED,
                description="Added system input data",
                metadata={"input_id": db_input.id}
            )
        except Exception as e:
            # Don't fail input creation if activity logging fails
            logger.warning(f"Failed to log input addition activity: {e}")
        
        return {
            "message": "System input added successfully", 
            "input_id": db_input.id,
            "project_id": project_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during system input addition",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "project_id": project_id,
                "error": str(e),
                "operation": "add_system_input"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while adding system input",
            headers={"X-Error-Code": "INPUT_ADDITION_FAILED"}
        )


@router.get("/{project_id}/inputs")
async def get_project_inputs(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all system inputs for a project with proper authorization.
    
    This endpoint enforces authorization by:
    - Using require_project_access dependency to validate user can access the project
    - Checking ownership and admin privileges before returning input data
    - Ensuring users can only view inputs for projects they can access
    - Providing comprehensive error handling for authorization failures
    
    Requirements addressed:
    - 1.1: API endpoints enforce proper authorization checks before processing requests
    - 1.2: Users can only access resources they have permission to view or modify
    - 5.3: Authorization implemented at the service layer level
    - 5.4: Object-level permissions validated for resource access
    """
    try:
        logger.info(
            "Retrieving project inputs",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "user_role": current_user.role,
                "operation": "get_project_inputs"
            }
        )
        
        # First, verify the project exists and user can access it
        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        
        if not project:
            logger.warning(
                "Project not found during input retrieval",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "get_project_inputs"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "PROJECT_NOT_FOUND"}
            )
        
        # Check if user can access this project
        if not can_access_project(current_user, project):
            # Log security event for denied access
            from app.core.security_audit import get_security_audit_logger
            audit_logger = get_security_audit_logger()
            audit_logger.log_project_access_denied(
                user_id=current_user.id,
                user_role=current_user.role,
                project_id=str(project_id),
                project_owner=project.owner_user_id,
                error_code="INSUFFICIENT_PERMISSIONS"
            )
            
            logger.warning(
                "Permission denied for project input access",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "project_owner": project.owner_user_id,
                    "user_role": current_user.role,
                    "operation": "get_project_inputs"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"}
            )
        
        # Get system inputs for the project
        result = await db.execute(
            select(SystemInput).where(SystemInput.project_id == project_id)
        )
        inputs = result.scalars().all()
        
        logger.info(
            "Project inputs retrieved successfully",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "input_count": len(inputs),
                "operation": "get_project_inputs"
            }
        )
        
        return {
            "data": inputs,
            "project_id": project_id,
            "count": len(inputs)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during project inputs retrieval",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "project_id": project_id,
                "error": str(e),
                "operation": "get_project_inputs"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving project inputs",
            headers={"X-Error-Code": "INPUT_RETRIEVAL_FAILED"}
        )


# Analysis endpoints
import json
import asyncio


@router.post("/{project_id}/analysis/start", response_model=AnalysisStartResponse)
async def start_analysis(
    project_id: int,
    request: AnalysisStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Start threat analysis for a project with proper authorization.
    
    This endpoint enforces authorization by:
    - Using require_project_modification dependency to validate user can modify the project
    - Checking ownership and admin privileges before allowing analysis start
    - Ensuring users can only start analysis for projects they can modify
    - Providing comprehensive error handling for authorization failures
    
    Requirements addressed:
    - 1.1: API endpoints enforce proper authorization checks before processing requests
    - 1.3: Users can only modify projects they own or have admin privileges for
    - 5.3: Authorization implemented at the service layer level
    - 5.4: Object-level permissions validated for resource access
    """
    try:
        logger.info(
            "Starting threat analysis",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "user_role": current_user.role,
                "operation": "start_analysis"
            }
        )
        
        # Verify project exists (already validated by dependency)
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(
                "Project not found during analysis start",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "start_analysis"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "PROJECT_NOT_FOUND"}
            )
        
        # Check if user can modify this project
        if not can_modify_project(current_user, project):
            # Log security event for denied modification
            from app.core.security_audit import get_security_audit_logger
            audit_logger = get_security_audit_logger()
            audit_logger.log_project_modification_denied(
                user_id=current_user.id,
                user_role=current_user.role,
                project_id=str(project_id),
                modification_type="start_analysis",
                project_owner=project.owner_user_id,
                error_code="INSUFFICIENT_PERMISSIONS"
            )
            
            logger.warning(
                "Permission denied for starting analysis",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "project_owner": project.owner_user_id,
                    "user_role": current_user.role,
                    "operation": "start_analysis"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: insufficient privileges to modify this project",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"}
            )
        
        # Verify system inputs exist
        if request.input_ids:
            input_result = await db.execute(
                select(SystemInput).where(
                    SystemInput.project_id == project_id,
                    SystemInput.id.in_(request.input_ids)
                )
            )
            inputs = input_result.scalars().all()
            if len(inputs) != len(request.input_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some input IDs not found"
                )
        
        # Check if analysis is already running
        state_result = await db.execute(
            select(AnalysisState).where(AnalysisState.project_id == project_id)
        )
        existing_state = state_result.scalar_one_or_none()
        
        if existing_state and existing_state.status == "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Analysis is already running for this project"
            )
        
        # Create or update analysis state
        now = datetime.utcnow()
        
        if existing_state:
            existing_state.status = "running"
            existing_state.current_phase = "system_analysis"
            existing_state.progress_percentage = 0.0
            existing_state.progress_message = "Initializing threat analysis..."
            existing_state.started_at = now
            existing_state.completed_at = None
            existing_state.error_message = None
            existing_state.configuration = json.dumps(request.config)
            existing_state.updated_at = now
        else:
            existing_state = AnalysisState(
                project_id=project_id,
                status="running",
                current_phase="system_analysis",
                progress_percentage=0.0,
                progress_message="Initializing threat analysis...",
                started_at=now,
                configuration=json.dumps(request.config)
            )
            db.add(existing_state)
        
        # Update project status
        project.status = "analyzing"
        project.updated_at = now
        
        await db.flush()
    
        # Start the analysis in the background
        asyncio.create_task(run_analysis_workflow(project_id, request.input_ids, request.config))
        
        logger.info(
            "Threat analysis started successfully",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "operation": "start_analysis"
            }
        )
        
        return AnalysisStartResponse(
            project_id=project_id,
            status="running",
            message="Threat analysis started successfully",
            started_at=now
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during analysis start",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "project_id": project_id,
                "error": str(e),
                "operation": "start_analysis"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while starting the analysis",
            headers={"X-Error-Code": "ANALYSIS_START_FAILED"}
        )


@router.get("/{project_id}/analysis/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current analysis status for a project with proper authorization.
    
    This endpoint enforces authorization by:
    - Using require_project_access dependency to validate user can access the project
    - Checking ownership and admin privileges before returning analysis status
    - Ensuring users can only view analysis status for projects they can access
    - Providing comprehensive error handling for authorization failures
    
    Requirements addressed:
    - 1.1: API endpoints enforce proper authorization checks before processing requests
    - 1.2: Users can only access resources they have permission to view or modify
    - 5.3: Authorization implemented at the service layer level
    - 5.4: Object-level permissions validated for resource access
    """
    try:
        logger.info(
            "Getting analysis status",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "user_role": current_user.role,
                "operation": "get_analysis_status"
            }
        )
        
        # Verify project exists (already validated by dependency)
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(
                "Project not found during analysis status check",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "get_analysis_status"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "PROJECT_NOT_FOUND"}
            )
        
        # Check if user can access this project
        if not can_access_project(current_user, project):
            # Log security event for denied access
            from app.core.security_audit import get_security_audit_logger
            audit_logger = get_security_audit_logger()
            audit_logger.log_project_access_denied(
                user_id=current_user.id,
                user_role=current_user.role,
                project_id=str(project_id),
                project_owner=project.owner_user_id,
                error_code="INSUFFICIENT_PERMISSIONS"
            )
            
            logger.warning(
                "Permission denied for analysis status access",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "project_owner": project.owner_user_id,
                    "user_role": current_user.role,
                    "operation": "get_analysis_status"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"}
            )
    
        # Get analysis state
        state_result = await db.execute(
            select(AnalysisState).where(AnalysisState.project_id == project_id)
        )
        analysis_state = state_result.scalar_one_or_none()
        
        if not analysis_state:
            logger.info(
                "No analysis state found for project",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "get_analysis_status"
                }
            )
            return AnalysisStatusResponse(
                project_id=project_id,
                status="idle"
            )
        
        progress = None
        if analysis_state.status == "running":
            progress = AnalysisProgress(
                current_phase=analysis_state.current_phase,
                percentage=analysis_state.progress_percentage or 0.0,
                message=analysis_state.progress_message
            )
        
        logger.info(
            "Analysis status retrieved successfully",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "analysis_status": analysis_state.status,
                "operation": "get_analysis_status"
            }
        )
        
        return AnalysisStatusResponse(
            project_id=project_id,
            status=analysis_state.status,
            progress=progress,
            started_at=analysis_state.started_at,
            completed_at=analysis_state.completed_at,
            error_message=analysis_state.error_message
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during analysis status retrieval",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "project_id": project_id,
                "error": str(e),
                "operation": "get_analysis_status"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving analysis status",
            headers={"X-Error-Code": "ANALYSIS_STATUS_FAILED"}
        )


@router.get("/{project_id}/analysis/results", response_model=AnalysisResultsResponse)
async def get_analysis_results(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get analysis results for a project with proper authorization.
    
    This endpoint enforces authorization by:
    - Using require_project_access dependency to validate user can access the project
    - Checking ownership and admin privileges before returning analysis results
    - Ensuring users can only view analysis results for projects they can access
    - Providing comprehensive error handling for authorization failures
    
    Requirements addressed:
    - 1.1: API endpoints enforce proper authorization checks before processing requests
    - 1.2: Users can only access resources they have permission to view or modify
    - 5.3: Authorization implemented at the service layer level
    - 5.4: Object-level permissions validated for resource access
    """
    try:
        logger.info(
            "Getting analysis results",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "user_role": current_user.role,
                "operation": "get_analysis_results"
            }
        )
        
        # Verify project exists (already validated by dependency)
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(
                "Project not found during analysis results retrieval",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "get_analysis_results"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "PROJECT_NOT_FOUND"}
            )
        
        # Check if user can access this project
        if not can_access_project(current_user, project):
            # Log security event for denied access
            from app.core.security_audit import get_security_audit_logger
            audit_logger = get_security_audit_logger()
            audit_logger.log_project_access_denied(
                user_id=current_user.id,
                user_role=current_user.role,
                project_id=str(project_id),
                project_owner=project.owner_user_id,
                error_code="INSUFFICIENT_PERMISSIONS"
            )
            
            logger.warning(
                "Permission denied for analysis results access",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "project_owner": project.owner_user_id,
                    "user_role": current_user.role,
                    "operation": "get_analysis_results"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                headers={"X-Error-Code": "INSUFFICIENT_PERMISSIONS"}
            )
    
        # Get analysis results
        results_query = await db.execute(
            select(AnalysisResults).where(AnalysisResults.project_id == project_id)
        )
        analysis_results = results_query.scalar_one_or_none()
        
        if not analysis_results:
            logger.warning(
                "No analysis results found for project",
                extra={
                    "user_id": current_user.id,
                    "project_id": project_id,
                    "operation": "get_analysis_results"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No analysis results found for this project",
                headers={"X-Error-Code": "ANALYSIS_RESULTS_NOT_FOUND"}
            )
        
        # Parse JSON fields
        def safe_json_loads(json_str, default=None):
            if not json_str:
                return default or []
            try:
                return json.loads(json_str)
            except (json.JSONDecodeError, TypeError):
                return default or []
        
        logger.info(
            "Analysis results retrieved successfully",
            extra={
                "user_id": current_user.id,
                "project_id": project_id,
                "operation": "get_analysis_results"
            }
        )
        
        return AnalysisResultsResponse(
            project_id=project_id,
            overall_risk_score=analysis_results.overall_risk_score or 0.0,
            confidence_score=analysis_results.confidence_score or 0.0,
            executive_summary=safe_json_loads(analysis_results.executive_summary),
            attack_paths=safe_json_loads(analysis_results.attack_paths_data, []),
            identified_techniques=safe_json_loads(analysis_results.identified_techniques, []),
            recommendations=safe_json_loads(analysis_results.recommendations_data, []),
            system_analysis_results=safe_json_loads(analysis_results.system_analysis_results, []),
            control_evaluation_results=safe_json_loads(analysis_results.control_evaluation_results, []),
            full_report=safe_json_loads(analysis_results.full_report),
            created_at=analysis_results.created_at,
            updated_at=analysis_results.updated_at
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with comprehensive logging
        logger.error(
            "Unexpected error during analysis results retrieval",
            extra={
                "user_id": current_user.id if current_user else "unknown",
                "project_id": project_id,
                "error": str(e),
                "operation": "get_analysis_results"
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving analysis results",
            headers={"X-Error-Code": "ANALYSIS_RESULTS_FAILED"}
        )


# Background task for running analysis workflow
async def run_analysis_workflow(project_id: int, input_ids: List[int], config: dict):
    """Run the complete analysis workflow using AI agents"""
    from app.core.database import async_session
    from app.agents.system_analyst_agent import SystemAnalystAgent
    from app.agents.attack_mapper_agent import AttackMapperAgent, ControlEvaluationAgent
    from app.agents.report_generation_agent import ReportGenerationAgent
    from app.models.schemas import AgentTask
    import uuid
    
    async with async_session() as db:
        try:
            # Update status: Starting system analysis
            await update_analysis_progress(
                db, project_id, "system_analysis", 10, "Starting system analysis..."
            )
            
            # Step 1: System Analysis
            system_agent = SystemAnalystAgent()
            system_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="system_analyst",
                task_description="Analyze system architecture and identify components",
                input_data={
                    "project_id": project_id,
                    "input_ids": input_ids,
                    "config": config
                }
            )
            
            await update_analysis_progress(
                db, project_id, "system_analysis", 25, "Analyzing system components..."
            )
            
            system_response = await system_agent.process_task(system_task)
            if system_response.status != "success":
                await mark_analysis_failed(db, project_id, "System analysis failed")
                return
            
            # Step 2: Attack Mapping
            await update_analysis_progress(
                db, project_id, "attack_mapping", 40, "Mapping attack techniques..."
            )
            
            attack_agent = AttackMapperAgent()
            attack_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="attack_mapper",
                task_description="Map MITRE ATT&CK techniques to system",
                input_data={
                    "project_id": project_id,
                    "system_analysis": system_response.output_data
                }
            )
            
            attack_response = await attack_agent.process_task(attack_task)
            if attack_response.status != "success":
                await mark_analysis_failed(db, project_id, "Attack mapping failed")
                return
            
            # Step 3: Control Evaluation
            await update_analysis_progress(
                db, project_id, "control_evaluation", 65, "Evaluating security controls..."
            )
            
            control_agent = ControlEvaluationAgent()
            control_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="control_evaluator",
                task_description="Evaluate existing security controls",
                input_data={
                    "project_id": project_id,
                    "attack_analysis": attack_response.output_data
                }
            )
            
            control_response = await control_agent.process_task(control_task)
            if control_response.status != "success":
                await mark_analysis_failed(db, project_id, "Control evaluation failed")
                return
            
            # Step 4: Report Generation
            await update_analysis_progress(
                db, project_id, "report_generation", 85, "Generating comprehensive report..."
            )
            
            report_agent = ReportGenerationAgent()
            report_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_type="report_generator",
                task_description="Generate comprehensive threat modeling report",
                input_data={
                    "project_id": project_id,
                    "system_analysis": system_response.output_data,
                    "attack_analysis": attack_response.output_data,
                    "control_analysis": control_response.output_data
                }
            )
            
            report_response = await report_agent.process_task(report_task)
            if report_response.status != "success":
                await mark_analysis_failed(db, project_id, "Report generation failed")
                return
            
            # Step 5: Store Results
            await update_analysis_progress(
                db, project_id, "finalizing", 95, "Storing analysis results..."
            )
            
            await store_analysis_results(
                db, project_id, 
                system_response.output_data,
                attack_response.output_data,
                control_response.output_data,
                report_response.output_data
            )
            
            # Mark as completed
            await mark_analysis_completed(db, project_id)
            
        except Exception as e:
            await mark_analysis_failed(db, project_id, f"Analysis workflow failed: {str(e)}")
            import logging
            logging.error(f"Analysis workflow failed for project {project_id}: {str(e)}", exc_info=True)


async def update_analysis_progress(db: AsyncSession, project_id: int, phase: str, percentage: float, message: str):
    """Update analysis progress in database"""
    result = await db.execute(select(AnalysisState).where(AnalysisState.project_id == project_id))
    state = result.scalar_one_or_none()
    
    if state:
        state.current_phase = phase
        state.progress_percentage = percentage
        state.progress_message = message
        state.updated_at = datetime.utcnow()
        await db.commit()


async def mark_analysis_failed(db: AsyncSession, project_id: int, error_message: str):
    """Mark analysis as failed"""
    result = await db.execute(select(AnalysisState).where(AnalysisState.project_id == project_id))
    state = result.scalar_one_or_none()
    
    if state:
        state.status = "failed"
        state.error_message = error_message
        state.completed_at = datetime.utcnow()
        state.updated_at = datetime.utcnow()
        
    # Update project status
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project:
        project.status = "failed"
        project.updated_at = datetime.utcnow()
    
    await db.commit()


async def mark_analysis_completed(db: AsyncSession, project_id: int):
    """Mark analysis as completed"""
    result = await db.execute(select(AnalysisState).where(AnalysisState.project_id == project_id))
    state = result.scalar_one_or_none()
    
    if state:
        state.status = "completed"
        state.current_phase = "completed"
        state.progress_percentage = 100.0
        state.progress_message = "Analysis completed successfully"
        state.completed_at = datetime.utcnow()
        state.updated_at = datetime.utcnow()
        
    # Update project status
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project:
        project.status = "completed"
        project.updated_at = datetime.utcnow()
    
    await db.commit()


async def store_analysis_results(db: AsyncSession, project_id: int, system_data: dict, 
                                attack_data: dict, control_data: dict, report_data: dict):
    """Store comprehensive analysis results"""
    # Check if results already exist
    result = await db.execute(select(AnalysisResults).where(AnalysisResults.project_id == project_id))
    analysis_results = result.scalar_one_or_none()
    
    # Calculate overall metrics
    overall_risk_score = report_data.get("metrics", {}).get("residual_risk", 0.5)
    confidence_score = min(
        system_data.get("confidence_score", 0.8),
        attack_data.get("confidence_score", 0.8),
        control_data.get("confidence_score", 0.8),
        report_data.get("confidence_score", 0.8)
    )
    
    now = datetime.utcnow()
    
    if analysis_results:
        # Update existing results
        analysis_results.overall_risk_score = overall_risk_score
        analysis_results.confidence_score = confidence_score
        analysis_results.executive_summary = json.dumps(report_data.get("executive_summary", {}))
        analysis_results.system_analysis_results = json.dumps([system_data])
        analysis_results.identified_techniques = json.dumps(attack_data.get("technique_mappings", []))
        analysis_results.attack_paths_data = json.dumps(attack_data.get("attack_paths", []))
        analysis_results.control_evaluation_results = json.dumps([control_data])
        analysis_results.recommendations_data = json.dumps(report_data.get("recommendations", {}).get("immediate_actions", []))
        analysis_results.full_report = json.dumps(report_data)
        analysis_results.updated_at = now
    else:
        # Create new results
        analysis_results = AnalysisResults(
            project_id=project_id,
            overall_risk_score=overall_risk_score,
            confidence_score=confidence_score,
            executive_summary=json.dumps(report_data.get("executive_summary", {})),
            system_analysis_results=json.dumps([system_data]),
            identified_techniques=json.dumps(attack_data.get("technique_mappings", [])),
            attack_paths_data=json.dumps(attack_data.get("attack_paths", [])),
            control_evaluation_results=json.dumps([control_data]),
            recommendations_data=json.dumps(report_data.get("recommendations", {}).get("immediate_actions", [])),
            full_report=json.dumps(report_data)
        )
        db.add(analysis_results)
    
    await db.commit()
