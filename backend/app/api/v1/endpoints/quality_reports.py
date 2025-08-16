"""
Quality Reports API Endpoints

This module provides REST API endpoints for generating and managing
quality reports and analytics.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.services.quality_report_generator import (
    QualityReportGenerator, ReportConfiguration, ReportType, ReportFormat
)
from app.core.dependencies import get_current_user


router = APIRouter(prefix="/quality-reports", tags=["quality-reports"])


class ReportRequest(BaseModel):
    """Request model for generating quality reports."""
    report_type: ReportType
    format: ReportFormat = ReportFormat.JSON
    project_ids: List[str]
    team_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_trends: bool = True
    include_comparisons: bool = True
    include_recommendations: bool = True
    executive_level: bool = False
    custom_metrics: Optional[List[str]] = None


class ReportResponse(BaseModel):
    """Response model for generated reports."""
    report_id: str
    report_type: str
    format: str
    generated_at: str
    project_count: int
    content: Dict[str, Any]
    metadata: Dict[str, Any]


class ReportListItem(BaseModel):
    """Model for report list items."""
    report_id: str
    report_type: str
    format: str
    project_ids: List[str]
    generated_at: str
    generated_by: Optional[str] = None
    file_size: Optional[int] = None


@router.post("/generate", response_model=ReportResponse)
async def generate_quality_report(
    request: ReportRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Generate a comprehensive quality report.
    
    Args:
        request: Report generation request with configuration
        current_user: Current authenticated user
        
    Returns:
        Generated report with content and metadata
    """
    try:
        # Create report configuration
        date_range = None
        if request.start_date and request.end_date:
            date_range = (request.start_date, request.end_date)
        
        config = ReportConfiguration(
            report_type=request.report_type,
            format=request.format,
            project_ids=request.project_ids,
            team_ids=request.team_ids,
            date_range=date_range,
            include_trends=request.include_trends,
            include_comparisons=request.include_comparisons,
            include_recommendations=request.include_recommendations,
            executive_level=request.executive_level,
            custom_metrics=request.custom_metrics
        )
        
        # Generate report
        generator = QualityReportGenerator()
        report = await generator.generate_comprehensive_report(config)
        
        return ReportResponse(**report)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/executive-summary")
async def get_executive_summary(
    project_ids: List[str] = Query(..., description="List of project IDs"),
    days: int = Query(30, description="Number of days to analyze"),
    current_user: str = Depends(get_current_user)
):
    """
    Get executive-level quality summary for specified projects.
    
    Args:
        project_ids: List of project IDs to analyze
        days: Number of days to include in analysis
        current_user: Current authenticated user
        
    Returns:
        Executive summary with key metrics and recommendations
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=project_ids,
            date_range=(start_date, end_date),
            executive_level=True
        )
        
        generator = QualityReportGenerator()
        report = await generator.generate_comprehensive_report(config)
        
        return report['content']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate executive summary: {str(e)}")


@router.get("/trend-analysis")
async def get_trend_analysis(
    project_ids: List[str] = Query(..., description="List of project IDs"),
    metric_name: Optional[str] = Query(None, description="Specific metric to analyze"),
    days: int = Query(30, description="Number of days to analyze"),
    current_user: str = Depends(get_current_user)
):
    """
    Get trend analysis for quality metrics.
    
    Args:
        project_ids: List of project IDs to analyze
        metric_name: Specific metric to analyze (optional)
        days: Number of days to include in analysis
        current_user: Current authenticated user
        
    Returns:
        Trend analysis with predictions and insights
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        config = ReportConfiguration(
            report_type=ReportType.TREND_ANALYSIS,
            format=ReportFormat.JSON,
            project_ids=project_ids,
            date_range=(start_date, end_date),
            custom_metrics=[metric_name] if metric_name else None
        )
        
        generator = QualityReportGenerator()
        report = await generator.generate_comprehensive_report(config)
        
        return report['content']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate trend analysis: {str(e)}")


@router.get("/comparative-analysis")
async def get_comparative_analysis(
    project_ids: List[str] = Query(..., description="List of project IDs to compare"),
    baseline_project: Optional[str] = Query(None, description="Baseline project for comparison"),
    current_user: str = Depends(get_current_user)
):
    """
    Get comparative analysis between projects.
    
    Args:
        project_ids: List of project IDs to compare
        baseline_project: Baseline project for comparison (uses first project if not specified)
        current_user: Current authenticated user
        
    Returns:
        Comparative analysis with rankings and best practices
    """
    try:
        if len(project_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 projects required for comparison")
        
        # Reorder projects if baseline is specified
        if baseline_project and baseline_project in project_ids:
            project_ids = [baseline_project] + [pid for pid in project_ids if pid != baseline_project]
        
        config = ReportConfiguration(
            report_type=ReportType.COMPARATIVE,
            format=ReportFormat.JSON,
            project_ids=project_ids,
            include_comparisons=True
        )
        
        generator = QualityReportGenerator()
        report = await generator.generate_comprehensive_report(config)
        
        return report['content']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comparative analysis: {str(e)}")


@router.get("/project-health")
async def get_project_health(
    project_ids: List[str] = Query(..., description="List of project IDs"),
    current_user: str = Depends(get_current_user)
):
    """
    Get project health analysis.
    
    Args:
        project_ids: List of project IDs to analyze
        current_user: Current authenticated user
        
    Returns:
        Project health analysis with risk assessment
    """
    try:
        config = ReportConfiguration(
            report_type=ReportType.PROJECT_HEALTH,
            format=ReportFormat.JSON,
            project_ids=project_ids
        )
        
        generator = QualityReportGenerator()
        report = await generator.generate_comprehensive_report(config)
        
        return report['content']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate project health analysis: {str(e)}")


@router.get("/technical-debt")
async def get_technical_debt_analysis(
    project_ids: List[str] = Query(..., description="List of project IDs"),
    current_user: str = Depends(get_current_user)
):
    """
    Get technical debt analysis.
    
    Args:
        project_ids: List of project IDs to analyze
        current_user: Current authenticated user
        
    Returns:
        Technical debt analysis with reduction recommendations
    """
    try:
        config = ReportConfiguration(
            report_type=ReportType.TECHNICAL_DEBT,
            format=ReportFormat.JSON,
            project_ids=project_ids
        )
        
        generator = QualityReportGenerator()
        report = await generator.generate_comprehensive_report(config)
        
        return report['content']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate technical debt analysis: {str(e)}")


@router.get("/issue-summary")
async def get_issue_summary(
    project_ids: List[str] = Query(..., description="List of project IDs"),
    days: int = Query(30, description="Number of days to analyze"),
    current_user: str = Depends(get_current_user)
):
    """
    Get quality issue summary.
    
    Args:
        project_ids: List of project IDs to analyze
        days: Number of days to include in analysis
        current_user: Current authenticated user
        
    Returns:
        Issue summary with categorization and resolution statistics
    """
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        config = ReportConfiguration(
            report_type=ReportType.ISSUE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=project_ids,
            date_range=(start_date, end_date)
        )
        
        generator = QualityReportGenerator()
        report = await generator.generate_comprehensive_report(config)
        
        return report['content']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate issue summary: {str(e)}")


@router.get("/team-performance")
async def get_team_performance(
    project_ids: List[str] = Query(..., description="List of project IDs"),
    team_ids: Optional[List[str]] = Query(None, description="List of team IDs"),
    current_user: str = Depends(get_current_user)
):
    """
    Get team performance analysis.
    
    Args:
        project_ids: List of project IDs to analyze
        team_ids: List of team IDs to filter by (optional)
        current_user: Current authenticated user
        
    Returns:
        Team performance analysis with rankings and insights
    """
    try:
        config = ReportConfiguration(
            report_type=ReportType.TEAM_PERFORMANCE,
            format=ReportFormat.JSON,
            project_ids=project_ids,
            team_ids=team_ids
        )
        
        generator = QualityReportGenerator()
        report = await generator.generate_comprehensive_report(config)
        
        return report['content']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate team performance analysis: {str(e)}")


@router.get("/", response_model=List[ReportListItem])
async def list_quality_reports(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    limit: int = Query(50, description="Maximum number of reports to return"),
    offset: int = Query(0, description="Number of reports to skip"),
    current_user: str = Depends(get_current_user)
):
    """
    List previously generated quality reports.
    
    Args:
        project_id: Filter by project ID (optional)
        report_type: Filter by report type (optional)
        limit: Maximum number of reports to return
        offset: Number of reports to skip
        current_user: Current authenticated user
        
    Returns:
        List of report metadata
    """
    try:
        generator = QualityReportGenerator()
        reports = await generator.list_reports(
            project_id=project_id,
            report_type=report_type,
            limit=limit,
            offset=offset
        )
        
        return [ReportListItem(**report) for report in reports]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.get("/{report_id}")
async def get_quality_report(
    report_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific quality report by ID.
    
    Args:
        report_id: Report ID
        current_user: Current authenticated user
        
    Returns:
        Report content and metadata
    """
    try:
        generator = QualityReportGenerator()
        report = await generator.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.delete("/{report_id}")
async def delete_quality_report(
    report_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Delete a quality report.
    
    Args:
        report_id: Report ID
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        generator = QualityReportGenerator()
        success = await generator.delete_report(report_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"message": "Report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


@router.get("/export/{report_id}")
async def export_quality_report(
    report_id: str,
    format: ReportFormat = Query(ReportFormat.JSON, description="Export format"),
    current_user: str = Depends(get_current_user)
):
    """
    Export a quality report in specified format.
    
    Args:
        report_id: Report ID
        format: Export format
        current_user: Current authenticated user
        
    Returns:
        Exported report content
    """
    try:
        generator = QualityReportGenerator()
        exported_content = await generator.export_report(report_id, format)
        
        if not exported_content:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Set appropriate content type based on format
        content_types = {
            ReportFormat.JSON: "application/json",
            ReportFormat.CSV: "text/csv",
            ReportFormat.HTML: "text/html",
            ReportFormat.MARKDOWN: "text/markdown",
            ReportFormat.PDF: "application/pdf",
            ReportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        from fastapi.responses import Response
        return Response(
            content=exported_content,
            media_type=content_types.get(format, "text/plain"),
            headers={
                "Content-Disposition": f"attachment; filename=quality_report_{report_id}.{format.value}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")


@router.post("/schedule")
async def schedule_quality_report(
    request: ReportRequest,
    schedule_cron: str = Query(..., description="Cron expression for scheduling"),
    current_user: str = Depends(get_current_user)
):
    """
    Schedule automatic generation of quality reports.
    
    Args:
        request: Report generation request
        schedule_cron: Cron expression for scheduling
        current_user: Current authenticated user
        
    Returns:
        Scheduled report configuration
    """
    try:
        generator = QualityReportGenerator()
        scheduled_report = await generator.schedule_report(request, schedule_cron, current_user)
        
        return {
            "message": "Report scheduled successfully",
            "schedule_id": scheduled_report["schedule_id"],
            "next_run": scheduled_report["next_run"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule report: {str(e)}")


@router.get("/metrics/available")
async def get_available_metrics(
    current_user: str = Depends(get_current_user)
):
    """
    Get list of available quality metrics for reporting.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of available metrics with descriptions
    """
    try:
        metrics = [
            {
                "name": "code_coverage",
                "display_name": "Code Coverage",
                "description": "Percentage of code covered by tests",
                "unit": "percentage",
                "higher_is_better": True
            },
            {
                "name": "cyclomatic_complexity",
                "display_name": "Cyclomatic Complexity",
                "description": "Average cyclomatic complexity of functions",
                "unit": "number",
                "higher_is_better": False
            },
            {
                "name": "maintainability_index",
                "display_name": "Maintainability Index",
                "description": "Overall maintainability score",
                "unit": "score",
                "higher_is_better": True
            },
            {
                "name": "technical_debt_ratio",
                "display_name": "Technical Debt Ratio",
                "description": "Ratio of technical debt to total code",
                "unit": "ratio",
                "higher_is_better": False
            },
            {
                "name": "test_quality_score",
                "display_name": "Test Quality Score",
                "description": "Overall quality of test suite",
                "unit": "score",
                "higher_is_better": True
            },
            {
                "name": "security_score",
                "display_name": "Security Score",
                "description": "Security vulnerability assessment score",
                "unit": "score",
                "higher_is_better": True
            },
            {
                "name": "performance_score",
                "display_name": "Performance Score",
                "description": "Performance optimization score",
                "unit": "score",
                "higher_is_better": True
            }
        ]
        
        return {"metrics": metrics}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available metrics: {str(e)}")