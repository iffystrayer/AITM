"""
API endpoints for quality issue tracking and management.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.services.quality_issue_tracker import QualityIssueTracker, IssueResolutionMetrics
from app.models.quality import (
    QualityIssue, QualityIssueCreate, QualityIssueUpdate,
    IssueType, Severity, IssueStatus
)
from app.core.dependencies import get_current_user


router = APIRouter()


class IssueListResponse(BaseModel):
    """Response model for issue list."""
    issues: List[QualityIssue]
    total: int
    page: int
    page_size: int


class BulkUpdateRequest(BaseModel):
    """Request model for bulk issue updates."""
    issue_ids: List[str]
    updates: QualityIssueUpdate


class BulkUpdateResponse(BaseModel):
    """Response model for bulk updates."""
    updated_count: int
    failed_ids: List[str]


def get_issue_tracker() -> QualityIssueTracker:
    """Dependency to get QualityIssueTracker instance."""
    return QualityIssueTracker()


@router.post("/issues", response_model=QualityIssue)
async def create_quality_issue(
    issue_data: QualityIssueCreate,
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Create a new quality issue."""
    try:
        issue = await tracker.create_issue(issue_data)
        return issue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create issue: {str(e)}")


@router.get("/issues", response_model=IssueListResponse)
async def get_quality_issues(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[IssueStatus] = Query(None, description="Filter by status"),
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
    issue_type: Optional[IssueType] = Query(None, description="Filter by issue type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Get quality issues with filtering and pagination."""
    try:
        offset = (page - 1) * page_size
        issues = await tracker.get_issues(
            project_id=project_id,
            status=status,
            severity=severity,
            issue_type=issue_type,
            limit=page_size,
            offset=offset
        )
        
        # Get total count for pagination
        all_issues = await tracker.get_issues(
            project_id=project_id,
            status=status,
            severity=severity,
            issue_type=issue_type,
            limit=10000  # Large number to get all
        )
        
        return IssueListResponse(
            issues=issues,
            total=len(all_issues),
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get issues: {str(e)}")


@router.get("/issues/{issue_id}", response_model=QualityIssue)
async def get_quality_issue(
    issue_id: str,
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Get a specific quality issue by ID."""
    try:
        issue = await tracker.get_issue_by_id(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        return issue
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get issue: {str(e)}")


@router.put("/issues/{issue_id}", response_model=QualityIssue)
async def update_quality_issue(
    issue_id: str,
    updates: QualityIssueUpdate,
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Update a quality issue."""
    try:
        updated_issue = await tracker.update_issue(issue_id, updates)
        if not updated_issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        return updated_issue
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update issue: {str(e)}")


@router.post("/issues/{issue_id}/resolve", response_model=QualityIssue)
async def resolve_quality_issue(
    issue_id: str,
    resolved_by: str,
    resolution_method: str = "manual",
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Resolve a quality issue."""
    try:
        success = await tracker.resolve_issue(issue_id, resolved_by, resolution_method)
        if not success:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Return the updated issue
        resolved_issue = await tracker.get_issue_by_id(issue_id)
        return resolved_issue
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve issue: {str(e)}")


@router.delete("/issues/{issue_id}")
async def delete_quality_issue(
    issue_id: str,
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Delete a quality issue."""
    try:
        deleted = await tracker.delete_issue(issue_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Issue not found")
        return {"message": "Issue deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete issue: {str(e)}")


@router.post("/issues/bulk-update", response_model=BulkUpdateResponse)
async def bulk_update_issues(
    request: BulkUpdateRequest,
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Bulk update multiple issues."""
    try:
        updated_count = await tracker.bulk_update_issues(request.issue_ids, request.updates)
        
        # Calculate failed IDs (simplified - in real implementation you'd track individual failures)
        failed_count = len(request.issue_ids) - updated_count
        failed_ids = request.issue_ids[-failed_count:] if failed_count > 0 else []
        
        return BulkUpdateResponse(
            updated_count=updated_count,
            failed_ids=failed_ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk update issues: {str(e)}")


@router.get("/issues/metrics/resolution", response_model=IssueResolutionMetrics)
async def get_resolution_metrics(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Get issue resolution metrics."""
    try:
        metrics = await tracker.get_resolution_metrics(project_id=project_id, days=days)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/issues/escalation/stale")
async def get_stale_issues(
    hours_threshold: int = Query(24, ge=1, description="Hours threshold for stale issues"),
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Get stale issues that need escalation."""
    try:
        stale_issues = await tracker.escalate_stale_issues(hours_threshold=hours_threshold)
        return {
            "stale_issues": stale_issues,
            "count": len(stale_issues),
            "threshold_hours": hours_threshold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stale issues: {str(e)}")


@router.get("/issues/summary")
async def get_issues_summary(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    tracker: QualityIssueTracker = Depends(get_issue_tracker),
    current_user = Depends(get_current_user)
):
    """Get a summary of issues by status, severity, and type."""
    try:
        all_issues = await tracker.get_issues(project_id=project_id, limit=10000)
        
        # Calculate summary statistics
        status_counts = {}
        severity_counts = {}
        type_counts = {}
        auto_fixable_count = 0
        
        for issue in all_issues:
            # Count by status
            status = issue.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by severity
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by type
            issue_type = issue.issue_type.value
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
            
            # Count auto-fixable
            if issue.auto_fixable:
                auto_fixable_count += 1
        
        return {
            "total_issues": len(all_issues),
            "status_distribution": status_counts,
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "auto_fixable_count": auto_fixable_count,
            "auto_fixable_percentage": (auto_fixable_count / len(all_issues) * 100) if all_issues else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")