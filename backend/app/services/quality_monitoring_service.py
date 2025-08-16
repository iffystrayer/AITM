"""
Real-time Quality Monitoring Service

This service provides real-time monitoring of code quality metrics,
intelligent alerting, and WebSocket-based updates for live dashboard updates.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol

from ..models.quality import QualityMetrics, QualityIssue, QualityAlert, AlertSeverity, AlertType
from ..core.database import get_db
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class AlertCondition(Enum):
    """Types of alert conditions"""
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    TREND_DEGRADATION = "trend_degradation"
    REGRESSION_DETECTED = "regression_detected"
    IMPROVEMENT_ACHIEVED = "improvement_achieved"
    CRITICAL_ISSUE = "critical_issue"


@dataclass
class AlertThreshold:
    """Configuration for quality metric thresholds"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    trend_window_minutes: int = 60
    min_samples: int = 3
    enabled: bool = True


@dataclass
class QualityMonitoringConfig:
    """Configuration for quality monitoring"""
    websocket_port: int = 8765
    update_interval_seconds: int = 30
    alert_thresholds: List[AlertThreshold] = None
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = self._default_thresholds()
        if self.notification_channels is None:
            self.notification_channels = ["websocket", "database"]
    
    def _default_thresholds(self) -> List[AlertThreshold]:
        """Default quality thresholds"""
        return [
            AlertThreshold("code_coverage", 70.0, 50.0),
            AlertThreshold("cyclomatic_complexity", 10.0, 15.0),
            AlertThreshold("maintainability_index", 60.0, 40.0),
            AlertThreshold("technical_debt_ratio", 0.3, 0.5),
            AlertThreshold("test_quality_score", 70.0, 50.0),
            AlertThreshold("security_score", 80.0, 60.0),
        ]


class QualityMonitoringService:
    """Real-time quality monitoring and alerting service"""
    
    def __init__(self, config: QualityMonitoringConfig = None):
        self.config = config or QualityMonitoringConfig()
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.alert_handlers: List[Callable] = []
        self.monitoring_active = False
        self.last_metrics: Dict[str, QualityMetrics] = {}
        self.alert_history: List[QualityAlert] = []
        
    async def start_monitoring(self):
        """Start the real-time monitoring service"""
        logger.info("Starting quality monitoring service")
        self.monitoring_active = True
        
        # Start WebSocket server
        websocket_task = asyncio.create_task(
            self._start_websocket_server()
        )
        
        # Start monitoring loop
        monitoring_task = asyncio.create_task(
            self._monitoring_loop()
        )
        
        await asyncio.gather(websocket_task, monitoring_task)
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        logger.info("Stopping quality monitoring service")
        self.monitoring_active = False
        
        # Close all WebSocket connections
        if self.connected_clients:
            await asyncio.gather(
                *[client.close() for client in self.connected_clients],
                return_exceptions=True
            )
        self.connected_clients.clear()
    
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        async def handle_client(websocket, path):
            logger.info(f"New WebSocket client connected: {websocket.remote_address}")
            self.connected_clients.add(websocket)
            
            try:
                # Send current metrics to new client
                await self._send_current_metrics(websocket)
                
                # Keep connection alive
                async for message in websocket:
                    # Handle client messages if needed
                    await self._handle_client_message(websocket, message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"WebSocket client disconnected: {websocket.remote_address}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.connected_clients.discard(websocket)
        
        start_server = websockets.serve(
            handle_client,
            "localhost",
            self.config.websocket_port
        )
        
        logger.info(f"WebSocket server started on port {self.config.websocket_port}")
        await start_server
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect current metrics
                current_metrics = await self._collect_quality_metrics()
                
                # Check for alerts
                alerts = await self._check_alerts(current_metrics)
                
                # Send updates to connected clients
                if current_metrics or alerts:
                    await self._broadcast_updates(current_metrics, alerts)
                
                # Process alerts
                for alert in alerts:
                    await self._process_alert(alert)
                
                # Wait for next update cycle
                await asyncio.sleep(self.config.update_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _collect_quality_metrics(self) -> Dict[str, QualityMetrics]:
        """Collect current quality metrics from database"""
        try:
            async for session in get_db():
                # Get latest metrics for all projects
                # This would typically query the quality_metrics table
                # For now, return mock data structure
                return {}
        except Exception as e:
            logger.error(f"Error collecting quality metrics: {e}")
            return {}
    
    async def _check_alerts(self, current_metrics: Dict[str, QualityMetrics]) -> List[QualityAlert]:
        """Check for alert conditions in current metrics"""
        alerts = []
        
        for project_id, metrics in current_metrics.items():
            # Check threshold alerts
            threshold_alerts = await self._check_threshold_alerts(project_id, metrics)
            alerts.extend(threshold_alerts)
            
            # Check trend alerts
            trend_alerts = await self._check_trend_alerts(project_id, metrics)
            alerts.extend(trend_alerts)
            
            # Check regression alerts
            regression_alerts = await self._check_regression_alerts(project_id, metrics)
            alerts.extend(regression_alerts)
        
        return alerts
    
    async def _check_threshold_alerts(self, project_id: str, metrics: QualityMetrics) -> List[QualityAlert]:
        """Check for threshold-based alerts"""
        alerts = []
        
        for threshold in self.config.alert_thresholds:
            if not threshold.enabled:
                continue
                
            metric_value = getattr(metrics, threshold.metric_name, None)
            if metric_value is None:
                continue
            
            severity = None
            if metric_value < threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
            elif metric_value < threshold.warning_threshold:
                severity = AlertSeverity.WARNING
            
            if severity:
                alert = QualityAlert(
                    id=f"threshold_{project_id}_{threshold.metric_name}_{datetime.now().isoformat()}",
                    project_id=project_id,
                    alert_type=AlertType.THRESHOLD_VIOLATION,
                    severity=severity,
                    metric_name=threshold.metric_name,
                    current_value=metric_value,
                    threshold_value=threshold.critical_threshold if severity == AlertSeverity.CRITICAL else threshold.warning_threshold,
                    message=f"{threshold.metric_name} is {metric_value:.2f}, below {severity.value} threshold of {threshold.critical_threshold if severity == AlertSeverity.CRITICAL else threshold.warning_threshold}",
                    created_at=datetime.now(),
                    resolved=False
                )
                alerts.append(alert)
        
        return alerts
    
    async def _check_trend_alerts(self, project_id: str, metrics: QualityMetrics) -> List[QualityAlert]:
        """Check for trend-based alerts"""
        alerts = []
        
        # Get historical metrics for trend analysis
        historical_metrics = await self._get_historical_metrics(
            project_id, 
            timedelta(hours=1)
        )
        
        if len(historical_metrics) < 3:
            return alerts  # Not enough data for trend analysis
        
        # Analyze trends for each metric
        for threshold in self.config.alert_thresholds:
            if not threshold.enabled:
                continue
                
            trend_alert = await self._analyze_metric_trend(
                project_id, 
                threshold.metric_name, 
                historical_metrics, 
                metrics
            )
            
            if trend_alert:
                alerts.append(trend_alert)
        
        return alerts
    
    async def _check_regression_alerts(self, project_id: str, metrics: QualityMetrics) -> List[QualityAlert]:
        """Check for regression alerts"""
        alerts = []
        
        # Compare with previous metrics
        previous_metrics = self.last_metrics.get(project_id)
        if not previous_metrics:
            return alerts
        
        # Check for significant regressions
        regression_threshold = 0.1  # 10% regression threshold
        
        for threshold in self.config.alert_thresholds:
            current_value = getattr(metrics, threshold.metric_name, None)
            previous_value = getattr(previous_metrics, threshold.metric_name, None)
            
            if current_value is None or previous_value is None:
                continue
            
            # Calculate regression percentage
            if previous_value > 0:
                regression_pct = (previous_value - current_value) / previous_value
                
                if regression_pct > regression_threshold:
                    alert = QualityAlert(
                        id=f"regression_{project_id}_{threshold.metric_name}_{datetime.now().isoformat()}",
                        project_id=project_id,
                        alert_type=AlertType.REGRESSION,
                        severity=AlertSeverity.WARNING if regression_pct < 0.2 else AlertSeverity.CRITICAL,
                        metric_name=threshold.metric_name,
                        current_value=current_value,
                        previous_value=previous_value,
                        regression_percentage=regression_pct * 100,
                        message=f"{threshold.metric_name} regressed by {regression_pct*100:.1f}% from {previous_value:.2f} to {current_value:.2f}",
                        created_at=datetime.now(),
                        resolved=False
                    )
                    alerts.append(alert)
        
        return alerts
    
    async def _analyze_metric_trend(self, project_id: str, metric_name: str, 
                                  historical_metrics: List[QualityMetrics], 
                                  current_metrics: QualityMetrics) -> Optional[QualityAlert]:
        """Analyze trend for a specific metric"""
        values = []
        for metrics in historical_metrics:
            value = getattr(metrics, metric_name, None)
            if value is not None:
                values.append(value)
        
        current_value = getattr(current_metrics, metric_name, None)
        if current_value is not None:
            values.append(current_value)
        
        if len(values) < 3:
            return None
        
        # Simple trend analysis - check if consistently declining
        declining_count = 0
        for i in range(1, len(values)):
            if values[i] < values[i-1]:
                declining_count += 1
        
        # If more than 70% of samples show decline, trigger alert
        if declining_count / (len(values) - 1) > 0.7:
            return QualityAlert(
                id=f"trend_{project_id}_{metric_name}_{datetime.now().isoformat()}",
                project_id=project_id,
                alert_type=AlertType.TREND_DEGRADATION,
                severity=AlertSeverity.WARNING,
                metric_name=metric_name,
                current_value=current_value,
                trend_direction="declining",
                message=f"{metric_name} shows consistent declining trend",
                created_at=datetime.now(),
                resolved=False
            )
        
        return None
    
    async def _get_historical_metrics(self, project_id: str, 
                                    time_window: timedelta) -> List[QualityMetrics]:
        """Get historical metrics for trend analysis"""
        try:
            async for session in get_db():
                # Query historical metrics from database
                # This would typically query the quality_metrics table
                # For now, return empty list
                return []
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []
    
    async def _broadcast_updates(self, metrics: Dict[str, QualityMetrics], 
                               alerts: List[QualityAlert]):
        """Broadcast updates to all connected WebSocket clients"""
        if not self.connected_clients:
            return
        
        update_message = {
            "type": "quality_update",
            "timestamp": datetime.now().isoformat(),
            "metrics": {pid: asdict(m) for pid, m in metrics.items()},
            "alerts": [asdict(alert) for alert in alerts]
        }
        
        message = json.dumps(update_message)
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending update to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients
    
    async def _process_alert(self, alert: QualityAlert):
        """Process and handle an alert"""
        logger.info(f"Processing alert: {alert.message}")
        
        # Store alert in database
        await self._store_alert(alert)
        
        # Add to alert history
        self.alert_history.append(alert)
        
        # Trigger alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    async def _store_alert(self, alert: QualityAlert):
        """Store alert in database"""
        try:
            async for session in get_db():
                # Store alert in database
                # This would typically insert into quality_alerts table
                pass
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    async def _send_current_metrics(self, websocket: WebSocketServerProtocol):
        """Send current metrics to a new WebSocket client"""
        try:
            current_metrics = await self._collect_quality_metrics()
            
            welcome_message = {
                "type": "welcome",
                "timestamp": datetime.now().isoformat(),
                "current_metrics": {pid: asdict(m) for pid, m in current_metrics.items()},
                "recent_alerts": [asdict(alert) for alert in self.alert_history[-10:]]
            }
            
            await websocket.send(json.dumps(welcome_message))
        except Exception as e:
            logger.error(f"Error sending current metrics: {e}")
    
    async def _handle_client_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle messages from WebSocket clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                # Handle subscription to specific projects or metrics
                project_ids = data.get("project_ids", [])
                # Store subscription preferences for this client
                
            elif message_type == "unsubscribe":
                # Handle unsubscription
                pass
                
            elif message_type == "ping":
                # Respond to ping with pong
                await websocket.send(json.dumps({"type": "pong"}))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from client: {message}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    def add_alert_handler(self, handler: Callable[[QualityAlert], None]):
        """Add a custom alert handler"""
        self.alert_handlers.append(handler)
    
    def remove_alert_handler(self, handler: Callable[[QualityAlert], None]):
        """Remove an alert handler"""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)
    
    async def get_alert_history(self, project_id: str = None, 
                              hours: int = 24) -> List[QualityAlert]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_alerts = [
            alert for alert in self.alert_history
            if alert.created_at >= cutoff_time and 
            (project_id is None or alert.project_id == project_id)
        ]
        
        return filtered_alerts
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved"""
        for alert in self.alert_history:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                
                # Update in database
                await self._update_alert_status(alert_id, True)
                return True
        
        return False
    
    async def _update_alert_status(self, alert_id: str, resolved: bool):
        """Update alert status in database"""
        try:
            async for session in get_db():
                # Update alert status in database
                pass
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")


# Global monitoring service instance
_monitoring_service: Optional[QualityMonitoringService] = None


def get_monitoring_service() -> QualityMonitoringService:
    """Get the global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = QualityMonitoringService()
    return _monitoring_service


async def start_quality_monitoring():
    """Start the quality monitoring service"""
    service = get_monitoring_service()
    await service.start_monitoring()


async def stop_quality_monitoring():
    """Stop the quality monitoring service"""
    service = get_monitoring_service()
    await service.stop_monitoring()