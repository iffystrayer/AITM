"""
Collaboration API endpoints for AITM application.

This module provides endpoints for team management, project sharing,
comments, and activity tracking features.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.api.endpoints.auth import get_current_active_user, get_current_superuser
from app.models.user import User
from app.services.collaboration_service import CollaborationService, get_collaboration_service
from app.models.collaboration import (
    TeamResponse, TeamCreate, TeamUpdate, TeamMember,
    ProjectShare as ProjectShareResponse, ProjectShareCreate,
    Comment, CommentCreate, CommentUpdate,
    ActivityLogEntry, ActivityType, ActivityFeedRequest, ActivityFeedResponse,
    ProjectRole, TeamRole
)

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Team Management Endpoints

@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Create a new team"""
    try:
        team = await collab_service.create_team(db, team_data, current_user.id)
        await db.commit()
        logger.info(f"Team '{team_data.name}' created by user {current_user.id}")
        return team
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create team"
        )


@router.get("/teams", response_model=List[TeamResponse])
async def get_user_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get all teams for the current user"""
    try:
        teams = await collab_service.get_user_teams(db, current_user.id)
        return teams
    except Exception as e:
        logger.error(f"Error fetching user teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch teams"
        )


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get team details"""
    try:
        team = await collab_service.get_team(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check if user has access to this team
        user_teams = await collab_service.get_user_teams(db, current_user.id)
        user_team_ids = [t.id for t in user_teams]
        
        if team_id not in user_team_ids and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this team"
            )
        
        return team
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch team"
        )


@router.post("/teams/{team_id}/members")
async def add_team_member(
    team_id: int,
    user_id: str,
    role: TeamRole = TeamRole.MEMBER,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Add a member to a team"""
    try:
        # Check if current user has admin rights on the team
        team = await collab_service.get_team(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check permissions
        current_user_member = next(
            (m for m in team.members if m.user_id == current_user.id), 
            None
        )
        
        if not current_user_member or current_user_member.role != TeamRole.ADMIN:
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only team admins can add members"
                )
        
        success = await collab_service.add_team_member(
            db, team_id, user_id, role, current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a team member"
            )
        
        await db.commit()
        return {"message": "Member added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding team member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add team member"
        )


@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: int,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Remove a member from a team"""
    try:
        # Check if current user has admin rights on the team or is removing themselves
        team = await collab_service.get_team(db, team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check permissions
        current_user_member = next(
            (m for m in team.members if m.user_id == current_user.id), 
            None
        )
        
        can_remove = (
            current_user.is_superuser or
            (current_user_member and current_user_member.role == TeamRole.ADMIN) or
            user_id == current_user.id  # Users can remove themselves
        )
        
        if not can_remove:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove this member"
            )
        
        success = await collab_service.remove_team_member(
            db, team_id, user_id, current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in team"
            )
        
        await db.commit()
        return {"message": "Member removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing team member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove team member"
        )


# Project Sharing Endpoints

@router.post("/projects/{project_id}/share", response_model=ProjectShareResponse, status_code=status.HTTP_201_CREATED)
async def share_project(
    project_id: int,
    share_data: ProjectShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Share a project with a user or team"""
    try:
        # Check if current user has permission to share this project
        user_access = await collab_service.get_user_project_access(
            db, project_id, current_user.id
        )
        
        if not user_access or user_access not in [ProjectRole.OWNER, ProjectRole.ADMIN]:
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to share this project"
                )
        
        share = await collab_service.share_project(
            db, project_id, share_data, current_user.id
        )
        await db.commit()
        logger.info(f"Project {project_id} shared by user {current_user.id}")
        return share
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error sharing project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share project"
        )


@router.get("/projects/{project_id}/shares", response_model=List[ProjectShareResponse])
async def get_project_shares(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get all shares for a project"""
    try:
        # Check if current user has access to this project
        user_access = await collab_service.get_user_project_access(
            db, project_id, current_user.id
        )
        
        if not user_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        shares = await collab_service.get_project_shares(db, project_id)
        return shares
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project shares: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project shares"
        )


@router.get("/projects/{project_id}/access", response_model=dict)
async def get_user_project_access(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get current user's access level to a project"""
    try:
        access_level = await collab_service.get_user_project_access(
            db, project_id, current_user.id
        )
        
        return {
            "project_id": project_id,
            "user_id": current_user.id,
            "access_level": access_level.value if access_level else None,
            "has_access": access_level is not None
        }
        
    except Exception as e:
        logger.error(f"Error checking project access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check project access"
        )


# Comments Endpoints

@router.post("/projects/{project_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def add_comment(
    project_id: int,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Add a comment to a project"""
    try:
        # Check if current user has access to this project
        user_access = await collab_service.get_user_project_access(
            db, project_id, current_user.id
        )
        
        if not user_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        comment = await collab_service.add_comment(
            db, project_id, comment_data, current_user.id
        )
        await db.commit()
        logger.info(f"Comment added to project {project_id} by user {current_user.id}")
        return comment
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add comment"
        )


@router.get("/projects/{project_id}/comments", response_model=List[Comment])
async def get_project_comments(
    project_id: int,
    component_type: Optional[str] = Query(None),
    component_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get comments for a project"""
    try:
        # Check if current user has access to this project
        user_access = await collab_service.get_user_project_access(
            db, project_id, current_user.id
        )
        
        if not user_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        comments = await collab_service.get_project_comments(
            db, project_id, component_type, component_id
        )
        return comments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch comments"
        )


@router.get("/comments/{comment_id}", response_model=Comment)
async def get_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get a specific comment"""
    try:
        comment = await collab_service.get_comment(db, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Check if current user has access to the project
        user_access = await collab_service.get_user_project_access(
            db, comment.project_id, current_user.id
        )
        
        if not user_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this comment"
            )
        
        return comment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch comment"
        )


# Activity Feed Endpoints

@router.get("/activity", response_model=ActivityFeedResponse)
async def get_activity_feed(
    project_id: Optional[int] = Query(None),
    team_id: Optional[int] = Query(None),
    activity_types: Optional[List[ActivityType]] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get activity feed"""
    try:
        # If project_id is specified, check access
        if project_id:
            user_access = await collab_service.get_user_project_access(
                db, project_id, current_user.id
            )
            if not user_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this project's activities"
                )
        
        # If team_id is specified, check membership
        if team_id:
            user_teams = await collab_service.get_user_teams(db, current_user.id)
            user_team_ids = [t.id for t in user_teams]
            if team_id not in user_team_ids and not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this team's activities"
                )
        
        request = ActivityFeedRequest(
            project_id=project_id,
            team_id=team_id,
            activity_types=activity_types,
            limit=limit,
            offset=offset
        )
        
        feed = await collab_service.get_activity_feed(db, request)
        return feed
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching activity feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch activity feed"
        )


@router.get("/projects/{project_id}/activity", response_model=ActivityFeedResponse)
async def get_project_activity(
    project_id: int,
    activity_types: Optional[List[ActivityType]] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get activity feed for a specific project"""
    try:
        # Check access to project
        user_access = await collab_service.get_user_project_access(
            db, project_id, current_user.id
        )
        if not user_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
        
        request = ActivityFeedRequest(
            project_id=project_id,
            activity_types=activity_types,
            limit=limit,
            offset=offset
        )
        
        feed = await collab_service.get_activity_feed(db, request)
        return feed
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project activity"
        )


@router.get("/teams/{team_id}/activity", response_model=ActivityFeedResponse)
async def get_team_activity(
    team_id: int,
    activity_types: Optional[List[ActivityType]] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    collab_service: CollaborationService = Depends(get_collaboration_service)
):
    """Get activity feed for a specific team"""
    try:
        # Check team membership
        user_teams = await collab_service.get_user_teams(db, current_user.id)
        user_team_ids = [t.id for t in user_teams]
        if team_id not in user_team_ids and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this team"
            )
        
        request = ActivityFeedRequest(
            team_id=team_id,
            activity_types=activity_types,
            limit=limit,
            offset=offset
        )
        
        feed = await collab_service.get_activity_feed(db, request)
        return feed
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch team activity"
        )
