"""
Quality Monitoring API Endpoints

This module provides REST API endpoints for managing quality monitoring,
alerts, and real-time notifications.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ....models.quality import (
    QualityAlert, QualityAlertCreate, QualityAlertUpdate,
    NotificationChannel, NotificationChannelCreate,
    AlertType, AlertSeverity, AlertStatus
)
from ....services.quality_monitoring_service import (
    get_monitoring_service, QualityMonitoringConfig, AlertThreshold
)
from ....services.notification_service import get_notification_service
from ....core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality-monitoring", tags=["quality-monitoring"])


class MonitoringStatusResponse(BaseModel):
    """Response model for monitoring status"""
    active: bool
    connected_clients: int
    update_interval_seconds: int
    websocket_port: int
    last_update: Optional[str] = None


class AlertHistoryResponse(BaseModel):
    """Response model for alert history"""
    alerts: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int


class ThresholdConfigResponse(BaseModel):
    """Response model for threshold configuration"""
    thresholds: List[Dict[str, Any]]


class NotificationStatusResponse(BaseModel):
    """Response model for notification status"""
    channels: Dict[str, Dict[str, Any]]
    total_channels: int
    active_channels: int


@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(current_user: dict = Depends(get_current_user)):
    """Get the current status of the quality monitoring service"""
    try:
        monitoring_service = get_monitoring_service()
        
        return MonitoringStatusResponse(
            active=monitoring_service.monitoring_active,
            connected_clients=len(monitoring_service.connected_clients),
            update_interval_seconds=monitoring_service.config.update_interval_seconds,
            websocket_port=monitoring_service.config.websocket_port,
            last_update=datetime.now().isoformat() if monitoring_service.monitoring_active else None
        )
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")


@router.post("/start")
async def start_monitoring(current_user: dict = Depends(get_current_user)):
    """Start the quality monitoring service"""
    try:
        monitoring_service = get_monitoring_service()
        
        if monitoring_service.monitoring_active:
            return JSONResponse(
                content={"message": "Monitoring service is already active"},
                status_code=200
            )
        
        # Start monitoring in background task
        import asyncio
        asyncio.create_task(monitoring_service.start_monitoring())
        
        return JSONResponse(
            content={"message": "Monitoring service started successfully"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error starting monitoring service: {e}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring service")


@router.post("/stop")
async def stop_monitoring(current_user: dict = Depends(get_current_user)):
    """Stop the quality monitoring service"""
    try:
        monitoring_service = get_monitoring_service()
        
        if not monitoring_service.monitoring_active:
            return JSONResponse(
                content={"message": "Monitoring service is not active"},
                status_code=200
            )
        
        await monitoring_service.stop_monitoring()
        
        return JSONResponse(
            content={"message": "Monitoring service stopped successfully"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error stopping monitoring service: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring service")


@router.get("/alerts", response_model=AlertHistoryResponse)
async def get_alerts(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    alert_type: Optional[AlertType] = Query(None, description="Filter by alert type"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    hours: int = Query(24, description="Hours of history to retrieve"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(50, description="Page size"),
    current_user: dict = Depends(get_current_user)
):
    """Get alert history with filtering and pagination"""
    try:
        monitoring_service = get_monitoring_service()
        
        # Get alerts from service
        alerts = await monitoring_service.get_alert_history(project_id, hours)
        
        # Apply filters
        filtered_alerts = []
        for alert in alerts:
            if alert_type and alert.alert_type != alert_type:
                continue
            if severity and alert.severity != severity:
                continue
            if status and alert.status != status:
                continue
            filtered_alerts.append(alert)
        
        # Apply pagination
        total_count = len(filtered_alerts)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_alerts = filtered_alerts[start_idx:end_idx]
        
        # Convert to dict format
        alert_dicts = [alert.to_dict() for alert in paginated_alerts]
        
        return AlertHistoryResponse(
            alerts=alert_dicts,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@router.post("/alerts", response_model=Dict[str, str])
async def create_alert(
    alert_data: QualityAlertCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new quality alert"""
    try:
        # Create alert object
        alert = QualityAlert(
            project_id=alert_data.project_id,
            alert_type=alert_data.alert_type,
            severity=alert_data.severity,
            metric_name=alert_data.metric_name,
            current_value=alert_data.current_value,
            threshold_value=alert_data.threshold_value,
            message=alert_data.message,
            description=alert_data.description,
            created_at=datetime.now()
        )
        
        # Process alert through monitoring service
        monitoring_service = get_monitoring_service()
        await monitoring_service._process_alert(alert)
        
        return {"alert_id": alert.id, "message": "Alert created successfully"}
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.put("/alerts/{alert_id}", response_model=Dict[str, str])
async def update_alert(
    alert_id: str,
    alert_update: QualityAlertUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing alert"""
    try:
        monitoring_service = get_monitoring_service()
        
        # Find alert in history
        alert = None
        for a in monitoring_service.alert_history:
            if a.id == alert_id:
                alert = a
                break
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update alert fields
        if alert_update.status:
            alert.status = alert_update.status
            if alert_update.status == AlertStatus.RESOLVED:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                alert.resolved_by = alert_update.resolved_by
            elif alert_update.status == AlertStatus.ACKNOWLEDGED:
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = alert_update.acknowledged_by
        
        # Update in database
        await monitoring_service._update_alert_status(alert_id, alert.resolved)
        
        return {"message": "Alert updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert")


@router.post("/alerts/{alert_id}/resolve", response_model=Dict[str, str])
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark an alert as resolved"""
    try:
        monitoring_service = get_monitoring_service()
        success = await monitoring_service.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert resolved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@router.get("/thresholds", response_model=ThresholdConfigResponse)
async def get_thresholds(current_user: dict = Depends(get_current_user)):
    """Get current alert threshold configuration"""
    try:
        monitoring_service = get_monitoring_service()
        thresholds = monitoring_service.config.alert_thresholds
        
        threshold_dicts = []
        for threshold in thresholds:
            threshold_dicts.append({
                "metric_name": threshold.metric_name,
                "warning_threshold": threshold.warning_threshold,
                "critical_threshold": threshold.critical_threshold,
                "trend_window_minutes": threshold.trend_window_minutes,
                "min_samples": threshold.min_samples,
                "enabled": threshold.enabled
            })
        
        return ThresholdConfigResponse(thresholds=threshold_dicts)
    except Exception as e:
        logger.error(f"Error getting thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to get thresholds")


@router.put("/thresholds", response_model=Dict[str, str])
async def update_thresholds(
    thresholds: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user)
):
    """Update alert threshold configuration"""
    try:
        monitoring_service = get_monitoring_service()
        
        # Convert to AlertThreshold objects
        new_thresholds = []
        for threshold_data in thresholds:
            threshold = AlertThreshold(
                metric_name=threshold_data["metric_name"],
                warning_threshold=threshold_data["warning_threshold"],
                critical_threshold=threshold_data["critical_threshold"],
                trend_window_minutes=threshold_data.get("trend_window_minutes", 60),
                min_samples=threshold_data.get("min_samples", 3),
                enabled=threshold_data.get("enabled", True)
            )
            new_thresholds.append(threshold)
        
        # Update configuration
        monitoring_service.config.alert_thresholds = new_thresholds
        
        return {"message": "Thresholds updated successfully"}
    except Exception as e:
        logger.error(f"Error updating thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to update thresholds")


@router.get("/notifications/status", response_model=NotificationStatusResponse)
async def get_notification_status(current_user: dict = Depends(get_current_user)):
    """Get notification system status"""
    try:
        notification_service = get_notification_service()
        channel_status = await notification_service.get_channel_status()
        
        active_channels = sum(1 for status in channel_status.values() if status["enabled"])
        
        return NotificationStatusResponse(
            channels=channel_status,
            total_channels=len(channel_status),
            active_channels=active_channels
        )
    except Exception as e:
        logger.error(f"Error getting notification status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification status")


@router.post("/notifications/channels", response_model=Dict[str, str])
async def create_notification_channel(
    channel_data: NotificationChannelCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new notification channel"""
    try:
        # Create notification channel
        channel = NotificationChannel(
            name=channel_data.name,
            channel_type=channel_data.channel_type,
            configuration=channel_data.configuration,
            enabled=channel_data.enabled,
            alert_types=channel_data.alert_types,
            severity_levels=channel_data.severity_levels
        )
        
        # Register with notification service
        notification_service = get_notification_service()
        await notification_service.register_channel(channel)
        
        return {"channel_id": channel.id, "message": "Notification channel created successfully"}
    except Exception as e:
        logger.error(f"Error creating notification channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification channel")


@router.delete("/notifications/channels/{channel_id}", response_model=Dict[str, str])
async def delete_notification_channel(
    channel_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification channel"""
    try:
        notification_service = get_notification_service()
        await notification_service.unregister_channel(channel_id)
        
        return {"message": "Notification channel deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting notification channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification channel")


@router.post("/notifications/test/{channel_id}", response_model=Dict[str, str])
async def test_notification_channel(
    channel_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Send a test notification through a specific channel"""
    try:
        notification_service = get_notification_service()
        
        # Find the channel
        if channel_id not in notification_service.channels:
            raise HTTPException(status_code=404, detail="Notification channel not found")
        
        # Create a test alert
        test_alert = QualityAlert(
            project_id="test-project",
            alert_type=AlertType.THRESHOLD_VIOLATION,
            severity=AlertSeverity.INFO,
            metric_name="test_metric",
            current_value=50.0,
            threshold_value=70.0,
            message="This is a test notification to verify channel configuration",
            description="Test notification sent from the quality monitoring API"
        )
        
        # Send test notification
        results = await notification_service.send_alert_notification(test_alert)
        
        if results.get(channel_id, False):
            return {"message": "Test notification sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test notification")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test notification")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time quality monitoring updates"""
    await websocket.accept()
    
    monitoring_service = get_monitoring_service()
    monitoring_service.connected_clients.add(websocket)
    
    try:
        # Send welcome message with current status
        await monitoring_service._send_current_metrics(websocket)
        
        # Keep connection alive and handle client messages
        while True:
            try:
                message = await websocket.receive_text()
                await monitoring_service._handle_client_message(websocket, message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        monitoring_service.connected_clients.discard(websocket)