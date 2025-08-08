"""
AITM Report Generation API Endpoints

This module provides comprehensive API endpoints for report generation, management, 
scheduling, and export functionality.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import tempfile
import uuid

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Response, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.agents.report_generator import (
    ReportType, ReportFormat, ReportRequest, ReportContent, 
    report_orchestrator, create_sample_request
)
from app.services.report_formatter import report_formatter, format_report_async
from app.models.project import Project
from app.models.analysis import Analysis
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


# Pydantic Models for API
class ReportGenerationRequest(BaseModel):
    """Request model for report generation"""
    report_type: ReportType
    format: ReportFormat
    project_ids: List[str]
    date_range: Optional[Dict[str, str]] = None
    include_charts: bool = True
    include_mitre_mapping: bool = True
    include_recommendations: bool = True
    custom_sections: Optional[List[str]] = None
    audience_level: str = Field(default="technical", pattern="^(executive|technical|operational)$")
    branding: Optional[Dict[str, str]] = None
    
    @validator('project_ids')
    def validate_project_ids(cls, v):
        if not v:
            raise ValueError("At least one project ID must be provided")
        return v
    
    @validator('date_range')
    def validate_date_range(cls, v):
        if v:
            if 'start_date' not in v or 'end_date' not in v:
                raise ValueError("Date range must include both start_date and end_date")
            # Additional date validation could be added here
        return v


class ReportResponse(BaseModel):
    """Response model for generated reports"""
    report_id: str
    title: str
    report_type: ReportType
    format: ReportFormat
    status: str
    generated_at: datetime
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    metadata: Dict[str, Any]


class ReportListResponse(BaseModel):
    """Response model for report listing"""
    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int


class ReportScheduleRequest(BaseModel):
    """Request model for scheduled reports"""
    name: str
    description: Optional[str] = None
    report_request: ReportGenerationRequest
    schedule_cron: str  # Cron expression for scheduling
    email_recipients: List[str] = []
    is_active: bool = True


class ReportScheduleResponse(BaseModel):
    """Response model for scheduled reports"""
    schedule_id: str
    name: str
    description: Optional[str]
    report_type: ReportType
    schedule_cron: str
    is_active: bool
    created_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]


# In-memory storage for demo (in production, use database)
generated_reports: Dict[str, Dict[str, Any]] = {}
scheduled_reports: Dict[str, Dict[str, Any]] = {}


@router.get("/types", response_model=List[str])
async def get_report_types():
    """Get list of available report types"""
    try:
        supported_types = await report_orchestrator.list_supported_types()
        return [report_type.value for report_type in supported_types]
    except Exception as e:
        logger.error(f"Error getting report types: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report types")


@router.get("/formats", response_model=List[str])
async def get_report_formats():
    """Get list of supported report formats"""
    try:
        supported_formats = await report_formatter.get_supported_formats()
        return [format_type.value for format_type in supported_formats]
    except Exception as e:
        logger.error(f"Error getting report formats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report formats")


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a report asynchronously"""
    try:
        # Create unique report ID
        report_id = str(uuid.uuid4())
        
        # Convert request to internal format
        report_request = ReportRequest(
            report_type=request.report_type,
            format=request.format,
            project_ids=request.project_ids,
            date_range=request.date_range,
            include_charts=request.include_charts,
            include_mitre_mapping=request.include_mitre_mapping,
            include_recommendations=request.include_recommendations,
            custom_sections=request.custom_sections,
            audience_level=request.audience_level,
            branding=request.branding
        )
        
        # Store initial report status
        report_info = {
            "report_id": report_id,
            "status": "generating",
            "created_at": datetime.now(),
            "user_id": current_user.id if current_user else None,
            "request": report_request,
            "content": None,
            "formatted_content": None,
            "file_size": None
        }
        generated_reports[report_id] = report_info
        
        # Schedule background generation
        background_tasks.add_task(
            _generate_report_background,
            report_id,
            report_request
        )
        
        return ReportResponse(
            report_id=report_id,
            title=f"{request.report_type.value.replace('_', ' ').title()} Report",
            report_type=request.report_type,
            format=request.format,
            status="generating",
            generated_at=datetime.now(),
            download_url=f"/api/reports/{report_id}/download",
            preview_url=f"/api/reports/{report_id}/preview",
            metadata={
                "projects_count": len(request.project_ids),
                "audience_level": request.audience_level
            }
        )
    
    except Exception as e:
        logger.error(f"Error initiating report generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/{report_id}/status")
async def get_report_status(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status of a report generation"""
    if report_id not in generated_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_info = generated_reports[report_id]
    
    # Check if user has access to this report
    if current_user and report_info.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "report_id": report_id,
        "status": report_info["status"],
        "created_at": report_info["created_at"],
        "completed_at": report_info.get("completed_at"),
        "error": report_info.get("error")
    }


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download a generated report"""
    if report_id not in generated_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_info = generated_reports[report_id]
    
    # Check if user has access to this report
    if current_user and report_info.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if report_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready for download")
    
    if not report_info.get("formatted_content"):
        raise HTTPException(status_code=500, detail="Report content not available")
    
    # Get content and format info
    formatted_content = report_info["formatted_content"]
    report_format = report_info["request"].format
    content = report_info.get("content")
    
    # Determine MIME type and filename
    if report_format == ReportFormat.PDF:
        media_type = "application/pdf"
        filename = f"report_{report_id}.pdf"
    elif report_format == ReportFormat.HTML:
        media_type = "text/html"
        filename = f"report_{report_id}.html"
    elif report_format == ReportFormat.DOCX:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"report_{report_id}.docx"
    elif report_format == ReportFormat.JSON:
        media_type = "application/json"
        filename = f"report_{report_id}.json"
    elif report_format == ReportFormat.MARKDOWN:
        media_type = "text/markdown"
        filename = f"report_{report_id}.md"
    else:
        media_type = "application/octet-stream"
        filename = f"report_{report_id}.txt"
    
    # Return streaming response
    if isinstance(formatted_content, bytes):
        from io import BytesIO
        return StreamingResponse(
            BytesIO(formatted_content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        from io import StringIO
        return StreamingResponse(
            StringIO(formatted_content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )


@router.get("/{report_id}/preview")
async def preview_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Preview a generated report (HTML only)"""
    if report_id not in generated_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_info = generated_reports[report_id]
    
    # Check if user has access to this report
    if current_user and report_info.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if report_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready for preview")
    
    content = report_info.get("content")
    if not content:
        raise HTTPException(status_code=500, detail="Report content not available")
    
    # Generate HTML preview regardless of original format
    try:
        html_content = await report_formatter.format_report(content, ReportFormat.HTML)
        return Response(content=html_content, media_type="text/html")
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate preview")


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_type: Optional[ReportType] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List generated reports for the current user"""
    # Filter reports for current user
    user_reports = []
    for report_id, report_info in generated_reports.items():
        if current_user and report_info.get("user_id") == current_user.id:
            if report_type and report_info["request"].report_type != report_type:
                continue
            if status and report_info["status"] != status:
                continue
            
            user_reports.append(ReportResponse(
                report_id=report_id,
                title=report_info.get("content", {}).get("title", f"Report {report_id}"),
                report_type=report_info["request"].report_type,
                format=report_info["request"].format,
                status=report_info["status"],
                generated_at=report_info["created_at"],
                file_size=report_info.get("file_size"),
                download_url=f"/api/reports/{report_id}/download" if report_info["status"] == "completed" else None,
                preview_url=f"/api/reports/{report_id}/preview" if report_info["status"] == "completed" else None,
                metadata={
                    "projects_count": len(report_info["request"].project_ids),
                    "audience_level": report_info["request"].audience_level
                }
            ))
    
    # Sort by creation date (newest first)
    user_reports.sort(key=lambda x: x.generated_at, reverse=True)
    
    # Paginate
    total = len(user_reports)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_reports = user_reports[start_idx:end_idx]
    
    return ReportListResponse(
        reports=paginated_reports,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a generated report"""
    if report_id not in generated_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_info = generated_reports[report_id]
    
    # Check if user has access to this report
    if current_user and report_info.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete the report
    del generated_reports[report_id]
    
    return {"message": "Report deleted successfully"}


@router.post("/schedule", response_model=ReportScheduleResponse)
async def schedule_report(
    request: ReportScheduleRequest,
    current_user: User = Depends(get_current_user)
):
    """Schedule a recurring report generation"""
    try:
        schedule_id = str(uuid.uuid4())
        
        # Validate cron expression (basic validation)
        if not _validate_cron_expression(request.schedule_cron):
            raise HTTPException(status_code=400, detail="Invalid cron expression")
        
        # Calculate next run time (simplified)
        next_run = _calculate_next_run(request.schedule_cron)
        
        schedule_info = {
            "schedule_id": schedule_id,
            "name": request.name,
            "description": request.description,
            "report_request": request.report_request,
            "schedule_cron": request.schedule_cron,
            "email_recipients": request.email_recipients,
            "is_active": request.is_active,
            "created_at": datetime.now(),
            "user_id": current_user.id if current_user else None,
            "last_run": None,
            "next_run": next_run
        }
        
        scheduled_reports[schedule_id] = schedule_info
        
        return ReportScheduleResponse(
            schedule_id=schedule_id,
            name=request.name,
            description=request.description,
            report_type=request.report_request.report_type,
            schedule_cron=request.schedule_cron,
            is_active=request.is_active,
            created_at=datetime.now(),
            last_run=None,
            next_run=next_run
        )
    
    except Exception as e:
        logger.error(f"Error scheduling report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule report: {str(e)}")


@router.get("/schedules", response_model=List[ReportScheduleResponse])
async def list_scheduled_reports(
    current_user: User = Depends(get_current_user)
):
    """List scheduled reports for the current user"""
    user_schedules = []
    
    for schedule_id, schedule_info in scheduled_reports.items():
        if current_user and schedule_info.get("user_id") == current_user.id:
            user_schedules.append(ReportScheduleResponse(
                schedule_id=schedule_id,
                name=schedule_info["name"],
                description=schedule_info.get("description"),
                report_type=schedule_info["report_request"].report_type,
                schedule_cron=schedule_info["schedule_cron"],
                is_active=schedule_info["is_active"],
                created_at=schedule_info["created_at"],
                last_run=schedule_info.get("last_run"),
                next_run=schedule_info.get("next_run")
            ))
    
    return user_schedules


@router.delete("/schedules/{schedule_id}")
async def delete_scheduled_report(
    schedule_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a scheduled report"""
    if schedule_id not in scheduled_reports:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    
    schedule_info = scheduled_reports[schedule_id]
    
    # Check if user has access to this schedule
    if current_user and schedule_info.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete the schedule
    del scheduled_reports[schedule_id]
    
    return {"message": "Scheduled report deleted successfully"}


@router.post("/sample")
async def generate_sample_report(
    report_type: ReportType = ReportType.EXECUTIVE_SUMMARY,
    format: ReportFormat = ReportFormat.HTML
):
    """Generate a sample report for testing/demonstration"""
    try:
        # Create sample request
        sample_request = create_sample_request(report_type)
        sample_request.format = format
        
        # Generate content
        content = await report_orchestrator.generate_report(sample_request)
        
        # Format content
        formatted_content = await format_report_async(content, format)
        
        if format == ReportFormat.HTML:
            return Response(content=formatted_content, media_type="text/html")
        elif format == ReportFormat.JSON:
            return Response(content=formatted_content, media_type="application/json")
        elif format == ReportFormat.MARKDOWN:
            return Response(content=formatted_content, media_type="text/markdown")
        else:
            # Return as downloadable file for binary formats
            if format == ReportFormat.PDF:
                media_type = "application/pdf"
                filename = f"sample_report.pdf"
            elif format == ReportFormat.DOCX:
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                filename = f"sample_report.docx"
            else:
                media_type = "application/octet-stream"
                filename = f"sample_report.{format.value}"
            
            from io import BytesIO
            return StreamingResponse(
                BytesIO(formatted_content) if isinstance(formatted_content, bytes) else BytesIO(formatted_content.encode()),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    
    except Exception as e:
        logger.error(f"Error generating sample report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate sample report: {str(e)}")


@router.get("/analytics")
async def get_report_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get analytics about report generation"""
    try:
        # Calculate analytics from generated reports
        user_reports = [
            report for report in generated_reports.values()
            if current_user and report.get("user_id") == current_user.id
        ]
        
        total_reports = len(user_reports)
        completed_reports = len([r for r in user_reports if r["status"] == "completed"])
        failed_reports = len([r for r in user_reports if r["status"] == "failed"])
        generating_reports = len([r for r in user_reports if r["status"] == "generating"])
        
        # Report type distribution
        type_distribution = {}
        for report in user_reports:
            report_type = report["request"].report_type.value
            type_distribution[report_type] = type_distribution.get(report_type, 0) + 1
        
        # Format distribution
        format_distribution = {}
        for report in user_reports:
            format_type = report["request"].format.value
            format_distribution[format_type] = format_distribution.get(format_type, 0) + 1
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_reports = [
            r for r in user_reports
            if r["created_at"] >= thirty_days_ago
        ]
        
        return {
            "summary": {
                "total_reports": total_reports,
                "completed_reports": completed_reports,
                "failed_reports": failed_reports,
                "generating_reports": generating_reports,
                "success_rate": (completed_reports / total_reports * 100) if total_reports > 0 else 0
            },
            "distributions": {
                "by_type": type_distribution,
                "by_format": format_distribution
            },
            "recent_activity": {
                "reports_last_30_days": len(recent_reports),
                "scheduled_reports": len([
                    s for s in scheduled_reports.values()
                    if current_user and s.get("user_id") == current_user.id and s["is_active"]
                ])
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting report analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


# Background task function
async def _generate_report_background(report_id: str, report_request: ReportRequest):
    """Background task to generate report"""
    try:
        logger.info(f"Starting background report generation for {report_id}")
        
        # Update status
        generated_reports[report_id]["status"] = "processing"
        
        # Generate report content
        content = await report_orchestrator.generate_report(report_request)
        
        # Store content
        generated_reports[report_id]["content"] = content
        
        # Format the content
        formatted_content = await format_report_async(content, report_request.format)
        
        # Store formatted content and metadata
        generated_reports[report_id]["formatted_content"] = formatted_content
        generated_reports[report_id]["status"] = "completed"
        generated_reports[report_id]["completed_at"] = datetime.now()
        
        # Calculate file size
        if isinstance(formatted_content, bytes):
            file_size = len(formatted_content)
        else:
            file_size = len(formatted_content.encode('utf-8'))
        generated_reports[report_id]["file_size"] = file_size
        
        logger.info(f"Report generation completed for {report_id}")
    
    except Exception as e:
        logger.error(f"Error in background report generation for {report_id}: {e}")
        generated_reports[report_id]["status"] = "failed"
        generated_reports[report_id]["error"] = str(e)


# Utility functions
def _validate_cron_expression(cron_expr: str) -> bool:
    """Basic validation of cron expression"""
    # This is a simplified validation - in production, use a proper cron library
    parts = cron_expr.split()
    return len(parts) == 5 or len(parts) == 6


def _calculate_next_run(cron_expr: str) -> datetime:
    """Calculate next run time from cron expression"""
    # Simplified calculation - in production, use croniter or similar library
    # For now, just return next hour as example
    return datetime.now() + timedelta(hours=1)
