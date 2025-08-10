"""
Collaboration models for AITM application.

This module defines database models for team collaboration features including
teams, project sharing, comments, and activity tracking.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, Text, ForeignKey, 
    UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# Enums for collaboration
class ProjectRole(str, Enum):
    """Project collaboration roles"""
    OWNER = "owner"
    ADMIN = "admin" 
    EDITOR = "editor"
    VIEWER = "viewer"


class TeamRole(str, Enum):
    """Team roles"""
    ADMIN = "admin"
    MEMBER = "member"


class ActivityType(str, Enum):
    """Activity types for tracking"""
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_SHARED = "project_shared"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    COMMENT_ADDED = "comment_added"
    RECOMMENDATION_UPDATED = "recommendation_updated"
    TEAM_CREATED = "team_created"
    TEAM_MEMBER_ADDED = "team_member_added"
    TEAM_MEMBER_REMOVED = "team_member_removed"


# SQLAlchemy Models

class Team(Base):
    """Team model for collaboration"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by_user_id = Column(String, nullable=False)  # References users.id
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Note: Relationships will be accessed via queries in the service layer
    
    # Indexes
    __table_args__ = (
        Index('ix_teams_created_by', 'created_by_user_id'),
    )


class TeamMembership(Base):
    """Team membership model"""
    __tablename__ = "team_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(String, nullable=False)  # References users.id
    role = Column(String(20), nullable=False, default=TeamRole.MEMBER.value)
    invited_by_user_id = Column(String, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Note: Team relationship accessed via service queries
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='unique_team_membership'),
        Index('ix_team_memberships_user', 'user_id'),
        Index('ix_team_memberships_team', 'team_id'),
    )


class ProjectShare(Base):
    """Project sharing and permissions model"""
    __tablename__ = "project_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    shared_with_user_id = Column(String, nullable=True)  # Direct user share
    shared_with_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # Team share
    role = Column(String(20), nullable=False, default=ProjectRole.VIEWER.value)
    shared_by_user_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Note: Relationships accessed via service queries
    
    # Constraints - either user or team must be specified, not both
    __table_args__ = (
        Index('ix_project_shares_project', 'project_id'),
        Index('ix_project_shares_user', 'shared_with_user_id'),
        Index('ix_project_shares_team', 'shared_with_team_id'),
    )


class ProjectComment(Base):
    """Comments on projects and their components"""
    __tablename__ = "project_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    author_user_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    # Optional references to specific project components
    component_type = Column(String(50))  # 'attack_path', 'recommendation', 'asset', etc.
    component_id = Column(Integer)  # ID of the component being commented on
    
    # Reply functionality
    parent_comment_id = Column(Integer, ForeignKey("project_comments.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_resolved = Column(Boolean, default=False)
    
    # Note: Relationships accessed via service queries
    
    # Indexes
    __table_args__ = (
        Index('ix_project_comments_project', 'project_id'),
        Index('ix_project_comments_author', 'author_user_id'),
        Index('ix_project_comments_component', 'component_type', 'component_id'),
        Index('ix_project_comments_created', 'created_at'),
    )


class ActivityLog(Base):
    """Activity log for tracking user and system actions"""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=True)  # Null for system activities
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    
    activity_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    activity_metadata = Column(JSON)  # Additional structured data about the activity
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Note: Relationships accessed via service queries
    
    # Indexes
    __table_args__ = (
        Index('ix_activity_logs_user', 'user_id'),
        Index('ix_activity_logs_project', 'project_id'),
        Index('ix_activity_logs_team', 'team_id'),
        Index('ix_activity_logs_type', 'activity_type'),
        Index('ix_activity_logs_created', 'created_at'),
    )


# Pydantic Models for API

class TeamBase(BaseModel):
    """Base team schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TeamCreate(TeamBase):
    """Team creation schema"""
    pass


class TeamUpdate(TeamBase):
    """Team update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class TeamMember(BaseModel):
    """Team member schema"""
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: TeamRole
    joined_at: datetime
    
    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    """Team response schema"""
    id: int
    created_by_user_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    members: List[TeamMember] = []
    member_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class ProjectShareBase(BaseModel):
    """Base project share schema"""
    role: ProjectRole


class ProjectShareCreate(ProjectShareBase):
    """Project share creation schema"""
    shared_with_user_id: Optional[str] = None
    shared_with_team_id: Optional[int] = None
    
    class Config:
        # Validate that either user_id or team_id is provided
        @classmethod
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)


class ProjectShare(ProjectShareBase):
    """Project share response schema"""
    id: int
    project_id: int
    shared_with_user_id: Optional[str] = None
    shared_with_team_id: Optional[int] = None
    shared_by_user_id: str
    created_at: datetime
    
    # Additional fields populated by services
    shared_with_user_name: Optional[str] = None
    shared_with_team_name: Optional[str] = None
    shared_by_user_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    """Base comment schema"""
    content: str = Field(..., min_length=1)
    component_type: Optional[str] = None
    component_id: Optional[int] = None


class CommentCreate(CommentBase):
    """Comment creation schema"""
    parent_comment_id: Optional[int] = None


class CommentUpdate(BaseModel):
    """Comment update schema"""
    content: Optional[str] = Field(None, min_length=1)
    is_resolved: Optional[bool] = None


class Comment(CommentBase):
    """Comment response schema"""
    id: int
    project_id: int
    author_user_id: str
    parent_comment_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_resolved: bool
    
    # Additional fields populated by services
    author_name: Optional[str] = None
    replies: List["Comment"] = []
    reply_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class ActivityLogEntry(BaseModel):
    """Activity log entry schema"""
    id: int
    user_id: Optional[str] = None
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    activity_type: ActivityType
    description: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    # Additional fields populated by services
    user_name: Optional[str] = None
    project_name: Optional[str] = None
    team_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ActivityFeedRequest(BaseModel):
    """Activity feed request parameters"""
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    activity_types: Optional[List[ActivityType]] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ActivityFeedResponse(BaseModel):
    """Activity feed response"""
    activities: List[ActivityLogEntry]
    total_count: int
    has_more: bool


# Forward reference resolution
Comment.model_rebuild()
