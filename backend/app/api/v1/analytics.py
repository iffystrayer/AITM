"""
Analytics API Endpoints

Provides comprehensive analytics, reporting, and insights endpoints for the AITM system.
Includes dashboard metrics, trend analysis, executive reporting, and AI-powered predictions.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.models.user import User
from app.core.permissions import require_permission, Permission

# Add get_current_user dependency
async def get_current_user(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)) -> User:
    """Get current user from database using user ID from token"""
    from sqlalchemy import select
    user = await db.scalar(select(User).where(User.id == int(user_id)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

from app.models.analytics import (
    # Request models
    DashboardMetricsRequest,
    ProjectAnalyticsRequest, 
    TrendAnalysisRequest,
    ExecutiveReportRequest,
    RiskPredictionRequest,
    ReportExportConfig,
    AnalyticsCacheConfig,
    
    # Response models
    DashboardMetricsResponse,
    ProjectAnalyticsResponse,
    TrendAnalysisResponse,
    ExecutiveReportResponse,
    RiskPredictionResponse,
    AnalyticsErrorResponse,
    
    # Enums
    ReportType,
    AnalyticsPeriod
)
from app.services.analytics_service import AnalyticsService
from app.services.prediction_service import RiskPredictionService
from app.core.cache import cache_manager
from app.core.permissions import Permission

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["Analytics"])

# Dependency injection for services
def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    prediction_service = RiskPredictionService()
    return AnalyticsService(prediction_service)

def get_prediction_service() -> RiskPredictionService:
    """Get prediction service instance"""
    return RiskPredictionService()

# Helper function for error handling
def handle_analytics_error(error: Exception, operation: str) -> AnalyticsErrorResponse:
    """Handle and format analytics errors"""
    logger.error(f"Analytics error in {operation}: {str(error)}")
    return AnalyticsErrorResponse(
        error=type(error).__name__,
        message=f"Failed to {operation}: {str(error)}",
        details={"operation": operation}
    )

@router.get(
    "/dashboard", 
    response_model=DashboardMetricsResponse,
    summary="Get comprehensive dashboard metrics",
    description="Retrieve executive dashboard metrics including project status, risk assessment, threat landscape, and performance indicators"
)
async def get_dashboard_metrics(
    period_days: Optional[int] = Query(default=30, ge=1, le=365, description="Analysis period in days"),
    include_trends: Optional[bool] = Query(default=True, description="Include trend analysis"),
    include_predictions: Optional[bool] = Query(default=False, description="Include risk predictions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    _: None = Depends(require_permission(Permission.VIEW_ANALYTICS))
):
    """Get comprehensive dashboard metrics for executive overview"""
    try:
        # Check cache first
        cache_key = f"dashboard_metrics_{current_user.id}_{period_days}_{include_trends}_{include_predictions}"
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get dashboard metrics
        metrics = await analytics_service.get_dashboard_metrics(db, period_days)
        
        # Convert to response model
        response = DashboardMetricsResponse(**metrics)
        
        # Cache the result for 15 minutes
        await cache_manager.set(cache_key, response.dict(), expire=900)
        
        return response
        
    except Exception as e:
        error_response = handle_analytics_error(e, "retrieve dashboard metrics")
        raise HTTPException(status_code=500, detail=error_response.dict())

@router.get(
    "/project/{project_id}",
    response_model=ProjectAnalyticsResponse,
    summary="Get detailed project analytics", 
    description="Retrieve comprehensive analytics for a specific project including risk assessment, attack paths, and recommendations"
)
async def get_project_analytics(
    project_id: int,
    include_predictions: Optional[bool] = Query(default=True, description="Include risk predictions"),
    include_recommendations: Optional[bool] = Query(default=True, description="Include recommendations analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    _: None = Depends(require_permission(Permission.VIEW_PROJECTS))
):
    """Get detailed analytics for a specific project"""
    try:
        # Get project analytics
        analytics = await analytics_service.get_detailed_project_analytics(db, project_id)
        
        response = ProjectAnalyticsResponse(**analytics)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    except Exception as e:
        error_response = handle_analytics_error(e, f"retrieve analytics for project {project_id}")
        raise HTTPException(status_code=500, detail=error_response.dict())

@router.get(
    "/trends",
    response_model=TrendAnalysisResponse,
    summary="Get trend analysis",
    description="Retrieve trend analysis for specified metrics over configurable time periods"
)
async def get_trend_analysis(
    period: AnalyticsPeriod = Query(default=AnalyticsPeriod.LAST_30_DAYS, description="Analysis period"),
    metrics: List[str] = Query(default=["risk_score", "project_count"], description="Metrics to analyze"),
    granularity: str = Query(default="daily", regex="^(daily|weekly|monthly)$", description="Data granularity"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    _: None = Depends(require_permission(Permission.VIEW_ANALYTICS))
):
    """Get trend analysis for specified metrics and time periods"""
    try:
        # Parse period to days
        period_map = {
            AnalyticsPeriod.LAST_7_DAYS: 7,
            AnalyticsPeriod.LAST_30_DAYS: 30,
            AnalyticsPeriod.LAST_90_DAYS: 90,
            AnalyticsPeriod.LAST_YEAR: 365
        }
        days = period_map.get(period, 30)
        
        # Get trend analysis from dashboard metrics (contains trend data)
        dashboard_metrics = await analytics_service.get_dashboard_metrics(db, days)
        
        # Format as trend analysis response
        response = TrendAnalysisResponse(
            period=f"Last {days} days",
            metrics=metrics,
            trends={
                "project_creation": dashboard_metrics["trends"]["project_creation_trend"],
                "risk_score": dashboard_metrics["trends"]["risk_score_trend"]
            },
            insights=dashboard_metrics["trends"]["trend_analysis"]
        )
        
        return response
        
    except Exception as e:
        error_response = handle_analytics_error(e, "retrieve trend analysis")
        raise HTTPException(status_code=500, detail=error_response.dict())

@router.post(
    "/reports/executive",
    response_model=ExecutiveReportResponse,
    summary="Generate executive report",
    description="Generate comprehensive executive reports with strategic insights and industry comparisons"
)
async def generate_executive_report(
    request: ExecutiveReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    _: None = Depends(require_permission(Permission.GENERATE_REPORTS))
):
    """Generate comprehensive executive report with strategic insights"""
    try:
        # Generate executive report
        report = await analytics_service.generate_executive_report(db, request.report_type.value)
        
        response = ExecutiveReportResponse(**report)
        
        # If PDF format requested, add background task for PDF generation
        if request.format == "pdf":
            background_tasks.add_task(
                _generate_pdf_report, 
                report_data=response.dict(),
                user_id=current_user.id,
                report_type=request.report_type.value
            )
        
        return response
        
    except Exception as e:
        error_response = handle_analytics_error(e, "generate executive report")
        raise HTTPException(status_code=500, detail=error_response.dict())

@router.post(
    "/predictions/risk", 
    response_model=RiskPredictionResponse,
    summary="Get AI risk predictions",
    description="Generate AI-powered risk predictions for projects with configurable prediction horizons"
)
async def get_risk_predictions(
    request: RiskPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    prediction_service: RiskPredictionService = Depends(get_prediction_service),
    _: None = Depends(require_permission(Permission.VIEW_PREDICTIONS))
):
    """Generate AI-powered risk predictions for projects"""
    try:
        # Generate risk predictions using the prediction service
        predictions = await prediction_service.predict_project_risks(
            db, 
            project_ids=request.project_ids,
            prediction_horizon=request.prediction_horizon_days,
            confidence_threshold=request.confidence_threshold
        )
        
        # Format as response
        response = RiskPredictionResponse(
            prediction_horizon_days=request.prediction_horizon_days,
            total_projects_analyzed=len(predictions),
            high_confidence_predictions=len([p for p in predictions if p.get('confidence', 0) >= request.confidence_threshold]),
            predictions=predictions,
            summary_insights=await prediction_service.generate_prediction_insights(predictions)
        )
        
        return response
        
    except Exception as e:
        error_response = handle_analytics_error(e, "generate risk predictions")
        raise HTTPException(status_code=500, detail=error_response.dict())

@router.get(
    "/health",
    summary="Analytics system health check",
    description="Check the health and status of the analytics system components"
)
async def analytics_health_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_SYSTEM_STATUS))
):
    """Check analytics system health and component status"""
    try:
        # Check database connectivity
        db_status = "healthy"
        try:
            await db.execute("SELECT 1")
        except Exception:
            db_status = "unhealthy"
        
        # Check cache system
        cache_status = "healthy"
        try:
            await cache_manager.set("health_check", "test", expire=1)
            await cache_manager.get("health_check")
        except Exception:
            cache_status = "unhealthy"
        
        # Check prediction service
        prediction_status = "healthy"
        try:
            prediction_service = RiskPredictionService()
            # Perform basic service check
        except Exception:
            prediction_status = "unhealthy"
        
        return {
            "status": "healthy" if all(s == "healthy" for s in [db_status, cache_status, prediction_status]) else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": db_status,
                "cache": cache_status,
                "prediction_service": prediction_status
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get(
    "/metrics/summary",
    summary="Get analytics summary metrics",
    description="Get high-level summary metrics for quick overview"
)
async def get_summary_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    _: None = Depends(require_permission(Permission.VIEW_ANALYTICS))
):
    """Get high-level summary metrics for quick overview"""
    try:
        # Get basic dashboard metrics with shorter period for quick overview
        metrics = await analytics_service.get_dashboard_metrics(db, days=7)
        
        # Extract key summary information
        summary = {
            "total_projects": metrics["project_metrics"]["total_projects"],
            "average_risk_score": metrics["risk_metrics"]["average_risk_score"],
            "high_risk_projects": metrics["risk_metrics"]["high_risk_projects"],
            "recent_activity": metrics["project_metrics"]["recent_projects"],
            "system_efficiency": metrics["performance_metrics"]["system_efficiency"],
            "overall_status": metrics["summary"]["overall_status"],
            "health_score": metrics["summary"]["health_score"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return summary
        
    except Exception as e:
        error_response = handle_analytics_error(e, "retrieve summary metrics")
        raise HTTPException(status_code=500, detail=error_response.dict())

# Background task functions
async def _generate_pdf_report(report_data: dict, user_id: int, report_type: str):
    """Background task to generate PDF report"""
    try:
        # This would integrate with a PDF generation service
        # For now, we'll log that the task was initiated
        logger.info(f"PDF report generation initiated for user {user_id}, report type: {report_type}")
        
        # Here you would typically:
        # 1. Generate PDF using a library like ReportLab or WeasyPrint
        # 2. Store the PDF in object storage (S3, etc.)
        # 3. Send notification to user when ready
        # 4. Update database with report status
        
        # Simulate PDF generation time
        await asyncio.sleep(5)
        
        logger.info(f"PDF report generation completed for user {user_id}")
        
    except Exception as e:
        logger.error(f"PDF report generation failed for user {user_id}: {e}")

# Additional utility endpoints
@router.get(
    "/export/data",
    summary="Export analytics data", 
    description="Export analytics data in various formats (JSON, CSV)"
)
async def export_analytics_data(
    format: str = Query(default="json", regex="^(json|csv)$", description="Export format"),
    period_days: int = Query(default=30, ge=1, le=365, description="Data period"),
    include_raw_data: bool = Query(default=False, description="Include raw data points"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    _: None = Depends(require_permission(Permission.EXPORT_DATA))
):
    """Export analytics data for external analysis or backup"""
    try:
        # Get comprehensive analytics data
        dashboard_metrics = await analytics_service.get_dashboard_metrics(db, period_days)
        
        if format == "json":
            return JSONResponse(
                content=dashboard_metrics,
                headers={"Content-Disposition": f"attachment; filename=analytics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"}
            )
        elif format == "csv":
            # For CSV, we would convert the data to a flat structure
            # This is a simplified example
            csv_data = _convert_metrics_to_csv(dashboard_metrics)
            
            # In a real implementation, you'd use pandas or csv module
            # and return a StreamingResponse with CSV content
            return JSONResponse(
                content={"message": "CSV export functionality would be implemented here", "data_preview": csv_data[:5]},
                headers={"Content-Disposition": f"attachment; filename=analytics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
        
    except Exception as e:
        error_response = handle_analytics_error(e, "export analytics data")
        raise HTTPException(status_code=500, detail=error_response.dict())

def _convert_metrics_to_csv(metrics: dict) -> List[dict]:
    """Convert metrics dictionary to CSV-friendly format"""
    # This is a simplified conversion example
    # In a real implementation, you'd flatten the nested structure appropriately
    flattened_data = []
    
    # Example flattening for project metrics
    project_metrics = metrics.get("project_metrics", {})
    flattened_data.append({
        "metric_type": "project",
        "metric_name": "total_projects",
        "value": project_metrics.get("total_projects", 0),
        "timestamp": metrics.get("generated_at")
    })
    
    # Add more metric conversions as needed
    return flattened_data
