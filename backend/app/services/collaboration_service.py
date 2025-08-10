"""
Collaboration service for AITM application.

This module provides business logic for team management, project sharing,
comments, and activity tracking features.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc
from sqlalchemy.orm import selectinload

# Import models from collaboration module
from app.models.collaboration import (
    # SQLAlchemy models
    Team as TeamSQLModel,
    TeamMembership as TeamMembershipSQLModel, 
    ProjectShare as ProjectShareSQLModel,
    ProjectComment as ProjectCommentSQLModel,
    ActivityLog as ActivityLogSQLModel,
    # Pydantic models
    TeamResponse, TeamCreate, TeamUpdate, TeamMember,
    ProjectShare as ProjectShareResponse, ProjectShareCreate,
    Comment, CommentCreate, CommentUpdate,
    ActivityLogEntry, ActivityType, ActivityFeedRequest, ActivityFeedResponse,
    ProjectRole, TeamRole
)
from app.models.user import UserTable
from app.core.database import Project

logger = logging.getLogger(__name__)


class CollaborationService:
    """Service for handling collaboration features"""
    
    def __init__(self):
        self.logger = logger
    
    # Team Management
    
    async def create_team(
        self, 
        db: AsyncSession, 
        team_data: TeamCreate, 
        creator_user_id: str
    ) -> TeamResponse:
        """Create a new team and add creator as admin"""
        # Create team
        team_table = TeamSQLModel(
            name=team_data.name,
            description=team_data.description,
            created_by_user_id=creator_user_id
        )
        
        db.add(team_table)
        await db.flush()
        
        # Add creator as team admin
        membership = TeamMembershipSQLModel(
            team_id=team_table.id,
            user_id=creator_user_id,
            role=TeamRole.ADMIN.value,
            invited_by_user_id=creator_user_id
        )
        
        db.add(membership)
        await db.flush()
        
        # Log activity
        await self._log_activity(
            db,
            user_id=creator_user_id,
            team_id=team_table.id,
            activity_type=ActivityType.TEAM_CREATED,
            description=f"Created team '{team_data.name}'",
            metadata={"team_name": team_data.name}
        )
        
        # Return team with members
        return await self.get_team(db, team_table.id)
    
    async def get_team(self, db: AsyncSession, team_id: int) -> Optional[TeamResponse]:
        """Get team by ID with members"""
        result = await db.execute(
            select(TeamSQLModel).where(TeamSQLModel.id == team_id)
        )
        team_table = result.scalar_one_or_none()
        
        if not team_table:
            return None
        
        # Get memberships separately
        memberships_result = await db.execute(
            select(TeamMembershipSQLModel).where(TeamMembershipSQLModel.team_id == team_id)
        )
        memberships = memberships_result.scalars().all()
        
        # Get member details
        members = []
        for membership in memberships:
            user_result = await db.execute(
                select(UserTable).where(UserTable.id == membership.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if user:
                members.append(TeamMember(
                    user_id=membership.user_id,
                    full_name=user.full_name,
                    email=user.email,
                    role=TeamRole(membership.role),
                    joined_at=membership.joined_at
                ))
        
        return TeamResponse(
            id=team_table.id,
            name=team_table.name,
            description=team_table.description,
            created_by_user_id=team_table.created_by_user_id,
            is_active=team_table.is_active,
            created_at=team_table.created_at,
            updated_at=team_table.updated_at,
            members=members,
            member_count=len(members)
        )
    
    async def get_user_teams(self, db: AsyncSession, user_id: str) -> List[TeamResponse]:
        """Get all teams for a user"""
        result = await db.execute(
            select(TeamSQLModel)
            .join(TeamMembershipSQLModel)
            .where(
                and_(
                    TeamMembershipSQLModel.user_id == user_id,
                    TeamSQLModel.is_active == True
                )
            )
            .order_by(TeamSQLModel.name)
        )
        
        teams = []
        for team_table in result.scalars().all():
            team = await self.get_team(db, team_table.id)
            if team:
                teams.append(team)
        
        return teams
    
    async def add_team_member(
        self,
        db: AsyncSession,
        team_id: int,
        user_id: str,
        role: TeamRole,
        inviter_user_id: str
    ) -> bool:
        """Add a member to a team"""
        # Check if user is already a member
        existing_result = await db.execute(
            select(TeamMembershipSQLModel).where(
                and_(
                    TeamMembershipSQLModel.team_id == team_id,
                    TeamMembershipSQLModel.user_id == user_id
                )
            )
        )
        
        if existing_result.scalar_one_or_none():
            return False  # Already a member
        
        # Add membership
        membership = TeamMembershipSQLModel(
            team_id=team_id,
            user_id=user_id,
            role=role.value,
            invited_by_user_id=inviter_user_id
        )
        
        db.add(membership)
        
        # Get user name for activity log
        user_result = await db.execute(
            select(UserTable).where(UserTable.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        user_name = user.full_name or user.email if user else user_id
        
        # Log activity
        await self._log_activity(
            db,
            user_id=inviter_user_id,
            team_id=team_id,
            activity_type=ActivityType.TEAM_MEMBER_ADDED,
            description=f"Added {user_name} to team",
            metadata={
                "added_user_id": user_id,
                "added_user_name": user_name,
                "role": role.value
            }
        )
        
        return True
    
    async def remove_team_member(
        self,
        db: AsyncSession,
        team_id: int,
        user_id: str,
        remover_user_id: str
    ) -> bool:
        """Remove a member from a team"""
        result = await db.execute(
            delete(TeamMembershipSQLModel).where(
                and_(
                    TeamMembershipSQLModel.team_id == team_id,
                    TeamMembershipSQLModel.user_id == user_id
                )
            )
        )
        
        if result.rowcount == 0:
            return False
        
        # Get user name for activity log
        user_result = await db.execute(
            select(UserTable).where(UserTable.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        user_name = user.full_name or user.email if user else user_id
        
        # Log activity
        await self._log_activity(
            db,
            user_id=remover_user_id,
            team_id=team_id,
            activity_type=ActivityType.TEAM_MEMBER_REMOVED,
            description=f"Removed {user_name} from team",
            metadata={
                "removed_user_id": user_id,
                "removed_user_name": user_name
            }
        )
        
        return True
    
    # Project Sharing
    
    async def share_project(
        self,
        db: AsyncSession,
        project_id: int,
        share_data: ProjectShareCreate,
        sharer_user_id: str
    ) -> ProjectShareResponse:
        """Share a project with a user or team"""
        # Validate that either user or team is specified, not both
        if not (share_data.shared_with_user_id or share_data.shared_with_team_id):
            raise ValueError("Must specify either user_id or team_id")
        
        if share_data.shared_with_user_id and share_data.shared_with_team_id:
            raise ValueError("Cannot specify both user_id and team_id")
        
        # Create share record
        share_table = ProjectShareSQLModel(
            project_id=project_id,
            shared_with_user_id=share_data.shared_with_user_id,
            shared_with_team_id=share_data.shared_with_team_id,
            role=share_data.role.value,
            shared_by_user_id=sharer_user_id
        )
        
        db.add(share_table)
        await db.flush()
        
        # Log activity
        if share_data.shared_with_user_id:
            # Get user name
            user_result = await db.execute(
                select(UserTable).where(UserTable.id == share_data.shared_with_user_id)
            )
            user = user_result.scalar_one_or_none()
            shared_with_name = user.full_name or user.email if user else share_data.shared_with_user_id
        else:
            # Get team name
            team_result = await db.execute(
                select(TeamSQLModel).where(TeamSQLModel.id == share_data.shared_with_team_id)
            )
            team = team_result.scalar_one_or_none()
            shared_with_name = team.name if team else f"Team {share_data.shared_with_team_id}"
        
        await self._log_activity(
            db,
            user_id=sharer_user_id,
            project_id=project_id,
            activity_type=ActivityType.PROJECT_SHARED,
            description=f"Shared project with {shared_with_name}",
            metadata={
                "shared_with_type": "user" if share_data.shared_with_user_id else "team",
                "shared_with_name": shared_with_name,
                "role": share_data.role.value
            }
        )
        
        return await self.get_project_share(db, share_table.id)
    
    async def get_project_share(self, db: AsyncSession, share_id: int) -> Optional[ProjectShareResponse]:
        """Get project share by ID"""
        result = await db.execute(
            select(ProjectShareSQLModel).where(ProjectShareSQLModel.id == share_id)
        )
        share_table = result.scalar_one_or_none()
        
        if not share_table:
            return None
        
        # Get additional names for response
        shared_with_user_name = None
        shared_with_team_name = None
        shared_by_user_name = None
        
        if share_table.shared_with_user_id:
            user_result = await db.execute(
                select(UserTable).where(UserTable.id == share_table.shared_with_user_id)
            )
            user = user_result.scalar_one_or_none()
            shared_with_user_name = user.full_name or user.email if user else None
        
        if share_table.shared_with_team_id:
            team_result = await db.execute(
                select(TeamSQLModel).where(TeamSQLModel.id == share_table.shared_with_team_id)
            )
            team = team_result.scalar_one_or_none()
            shared_with_team_name = team.name if team else None
        
        # Get sharer name
        sharer_result = await db.execute(
            select(UserTable).where(UserTable.id == share_table.shared_by_user_id)
        )
        sharer = sharer_result.scalar_one_or_none()
        shared_by_user_name = sharer.full_name or sharer.email if sharer else None
        
        return ProjectShareResponse(
            id=share_table.id,
            project_id=share_table.project_id,
            shared_with_user_id=share_table.shared_with_user_id,
            shared_with_team_id=share_table.shared_with_team_id,
            role=ProjectRole(share_table.role),
            shared_by_user_id=share_table.shared_by_user_id,
            created_at=share_table.created_at,
            shared_with_user_name=shared_with_user_name,
            shared_with_team_name=shared_with_team_name,
            shared_by_user_name=shared_by_user_name
        )
    
    async def get_project_shares(self, db: AsyncSession, project_id: int) -> List[ProjectShareResponse]:
        """Get all shares for a project"""
        result = await db.execute(
            select(ProjectShareSQLModel)
            .where(ProjectShareSQLModel.project_id == project_id)
            .order_by(ProjectShareSQLModel.created_at)
        )
        
        shares = []
        for share_table in result.scalars().all():
            share = await self.get_project_share(db, share_table.id)
            if share:
                shares.append(share)
        
        return shares
    
    async def get_user_project_access(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: str
    ) -> Optional[ProjectRole]:
        """Get user's access level to a project"""
        # Check if user is the owner
        project_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            return None
        
        if project.owner_user_id == user_id:
            return ProjectRole.OWNER
        
        # Check direct shares
        direct_result = await db.execute(
            select(ProjectShareSQLModel).where(
                and_(
                    ProjectShareSQLModel.project_id == project_id,
                    ProjectShareSQLModel.shared_with_user_id == user_id
                )
            )
        )
        direct_share = direct_result.scalar_one_or_none()
        
        if direct_share:
            return ProjectRole(direct_share.role)
        
        # Check team shares
        team_result = await db.execute(
            select(ProjectShareSQLModel)
            .join(TeamMembershipSQLModel)
            .where(
                and_(
                    ProjectShareSQLModel.project_id == project_id,
                    ProjectShareSQLModel.shared_with_team_id == TeamMembershipSQLModel.team_id,
                    TeamMembershipSQLModel.user_id == user_id
                )
            )
        )
        team_share = team_result.scalar_one_or_none()
        
        if team_share:
            return ProjectRole(team_share.role)
        
        return None
    
    # Comments System
    
    async def add_comment(
        self,
        db: AsyncSession,
        project_id: int,
        comment_data: CommentCreate,
        author_user_id: str
    ) -> Comment:
        """Add a comment to a project"""
        comment_table = ProjectCommentSQLModel(
            project_id=project_id,
            author_user_id=author_user_id,
            content=comment_data.content,
            component_type=comment_data.component_type,
            component_id=comment_data.component_id,
            parent_comment_id=comment_data.parent_comment_id
        )
        
        db.add(comment_table)
        await db.flush()
        
        # Log activity
        component_desc = ""
        if comment_data.component_type and comment_data.component_id:
            component_desc = f" on {comment_data.component_type} #{comment_data.component_id}"
        elif comment_data.parent_comment_id:
            component_desc = f" (reply to comment #{comment_data.parent_comment_id})"
        
        await self._log_activity(
            db,
            user_id=author_user_id,
            project_id=project_id,
            activity_type=ActivityType.COMMENT_ADDED,
            description=f"Added comment{component_desc}",
            metadata={
                "comment_id": comment_table.id,
                "component_type": comment_data.component_type,
                "component_id": comment_data.component_id,
                "is_reply": bool(comment_data.parent_comment_id)
            }
        )
        
        return await self.get_comment(db, comment_table.id)
    
    async def get_comment(self, db: AsyncSession, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        result = await db.execute(
            select(ProjectCommentSQLModel).where(ProjectCommentSQLModel.id == comment_id)
        )
        comment_table = result.scalar_one_or_none()
        
        if not comment_table:
            return None
        
        # Get author name
        author_result = await db.execute(
            select(UserTable).where(UserTable.id == comment_table.author_user_id)
        )
        author = author_result.scalar_one_or_none()
        author_name = author.full_name or author.email if author else None
        
        # Get replies
        replies_result = await db.execute(
            select(ProjectCommentSQLModel)
            .where(ProjectCommentSQLModel.parent_comment_id == comment_id)
            .order_by(ProjectCommentSQLModel.created_at)
        )
        
        replies = []
        for reply_table in replies_result.scalars().all():
            reply = await self.get_comment(db, reply_table.id)
            if reply:
                replies.append(reply)
        
        return Comment(
            id=comment_table.id,
            project_id=comment_table.project_id,
            author_user_id=comment_table.author_user_id,
            content=comment_table.content,
            component_type=comment_table.component_type,
            component_id=comment_table.component_id,
            parent_comment_id=comment_table.parent_comment_id,
            created_at=comment_table.created_at,
            updated_at=comment_table.updated_at,
            is_resolved=comment_table.is_resolved,
            author_name=author_name,
            replies=replies,
            reply_count=len(replies)
        )
    
    async def get_project_comments(
        self,
        db: AsyncSession,
        project_id: int,
        component_type: Optional[str] = None,
        component_id: Optional[int] = None
    ) -> List[Comment]:
        """Get comments for a project, optionally filtered by component"""
        query = select(ProjectCommentSQLModel).where(
            and_(
                ProjectCommentSQLModel.project_id == project_id,
                ProjectCommentSQLModel.parent_comment_id.is_(None)  # Only top-level comments
            )
        )
        
        if component_type:
            query = query.where(ProjectCommentSQLModel.component_type == component_type)
        
        if component_id:
            query = query.where(ProjectCommentSQLModel.component_id == component_id)
        
        query = query.order_by(desc(ProjectCommentSQLModel.created_at))
        
        result = await db.execute(query)
        
        comments = []
        for comment_table in result.scalars().all():
            comment = await self.get_comment(db, comment_table.id)
            if comment:
                comments.append(comment)
        
        return comments
    
    # Activity Tracking
    
    async def get_activity_feed(
        self,
        db: AsyncSession,
        request: ActivityFeedRequest
    ) -> ActivityFeedResponse:
        """Get activity feed based on filters"""
        query = select(ActivityLogSQLModel)
        
        # Apply filters
        filters = []
        if request.project_id:
            filters.append(ActivityLogSQLModel.project_id == request.project_id)
        
        if request.team_id:
            filters.append(ActivityLogSQLModel.team_id == request.team_id)
        
        if request.activity_types:
            filters.append(ActivityLogSQLModel.activity_type.in_([t.value for t in request.activity_types]))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get paginated results
        query = query.order_by(desc(ActivityLogSQLModel.created_at))
        query = query.offset(request.offset).limit(request.limit)
        
        result = await db.execute(query)
        
        activities = []
        for activity_table in result.scalars().all():
            activity = await self._build_activity_entry(db, activity_table)
            activities.append(activity)
        
        has_more = request.offset + len(activities) < total_count
        
        return ActivityFeedResponse(
            activities=activities,
            total_count=total_count,
            has_more=has_more
        )
    
    async def _build_activity_entry(
        self, 
        db: AsyncSession, 
        activity_table: ActivityLogSQLModel
    ) -> ActivityLogEntry:
        """Build activity entry with additional names"""
        user_name = None
        project_name = None
        team_name = None
        
        # Get user name
        if activity_table.user_id:
            user_result = await db.execute(
                select(UserTable).where(UserTable.id == activity_table.user_id)
            )
            user = user_result.scalar_one_or_none()
            user_name = user.full_name or user.email if user else None
        
        # Get project name
        if activity_table.project_id:
            project_result = await db.execute(
                select(Project).where(Project.id == activity_table.project_id)
            )
            project = project_result.scalar_one_or_none()
            project_name = project.name if project else None
        
        # Get team name
        if activity_table.team_id:
            team_result = await db.execute(
                select(TeamSQLModel).where(TeamSQLModel.id == activity_table.team_id)
            )
            team = team_result.scalar_one_or_none()
            team_name = team.name if team else None
        
        return ActivityLogEntry(
            id=activity_table.id,
            user_id=activity_table.user_id,
            project_id=activity_table.project_id,
            team_id=activity_table.team_id,
            activity_type=ActivityType(activity_table.activity_type),
            description=activity_table.description,
            metadata=activity_table.activity_metadata,
            created_at=activity_table.created_at,
            user_name=user_name,
            project_name=project_name,
            team_name=team_name
        )
    
    async def _log_activity(
        self,
        db: AsyncSession,
        activity_type: ActivityType,
        description: str,
        user_id: Optional[str] = None,
        project_id: Optional[int] = None,
        team_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an activity"""
        activity = ActivityLogSQLModel(
            user_id=user_id,
            project_id=project_id,
            team_id=team_id,
            activity_type=activity_type.value,
            description=description,
            activity_metadata=metadata
        )
        
        db.add(activity)


# Global service instance
collaboration_service = CollaborationService()


def get_collaboration_service() -> CollaborationService:
    """Dependency to get collaboration service instance"""
    return collaboration_service
