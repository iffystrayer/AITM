"""
Unit tests for Quality Monitoring Service

Tests the core functionality of the quality monitoring service including
alert generation, threshold checking, and notification handling.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from app.services.quality_monitoring_service import (
    QualityMonitoringService,
    QualityMonitoringConfig,
    AlertThreshold,
    AlertCondition
)
from app.models.quality import (
    QualityMetrics,
    QualityAlert,
    AlertType,
    AlertSeverity,
    AlertStatus
)


@pytest.fixture
def monitoring_config():
    """Create a test monitoring configuration"""
    return QualityMonitoringConfig(
        websocket_port=8765,
        update_interval_seconds=10,
        alert_thresholds=[
            AlertThreshold("code_coverage", 70.0, 50.0),
            AlertThreshold("cyclomatic_complexity", 10.0, 15.0),
            AlertThreshold("maintainability_index", 60.0, 40.0),
        ]
    )


@pytest.fixture
def monitoring_service(monitoring_config):
    """Create a test monitoring service"""
    return QualityMonitoringService(monitoring_config)


@pytest.fixture
def sample_metrics():
    """Create sample quality metrics"""
    return QualityMetrics(
        project_id="test-project",
        timestamp=datetime.now(),
        code_coverage=65.0,  # Below warning threshold
        cyclomatic_complexity=8.0,  # Good
        maintainability_index=45.0,  # Below critical threshold
        technical_debt_ratio=0.2,
        test_quality_score=75.0,
        security_score=85.0
    )


class TestQualityMonitoringService:
    """Test cases for QualityMonitoringService"""
    
    def test_service_initialization(self, monitoring_config):
        """Test service initialization with configuration"""
        service = QualityMonitoringService(monitoring_config)
        
        assert service.config == monitoring_config
        assert not service.monitoring_active
        assert len(service.connected_clients) == 0
        assert len(service.alert_handlers) == 0
        assert len(service.last_metrics) == 0
        assert len(service.alert_history) == 0
    
    def test_default_configuration(self):
        """Test service initialization with default configuration"""
        service = QualityMonitoringService()
        
        assert service.config.websocket_port == 8765
        assert service.config.update_interval_seconds == 30
        assert len(service.config.alert_thresholds) > 0
        assert "websocket" in service.config.notification_channels
        assert "database" in service.config.notification_channels
    
    @pytest.mark.asyncio
    async def test_threshold_alert_generation(self, monitoring_service, sample_metrics):
        """Test threshold-based alert generation"""
        project_id = "test-project"
        
        # Mock database session
        with patch('app.services.quality_monitoring_service.get_db'):
            alerts = await monitoring_service._check_threshold_alerts(project_id, sample_metrics)
        
        # Should generate alerts for code_coverage (warning) and maintainability_index (warning)
        # Note: maintainability_index 45.0 is above critical threshold (40.0) but below warning (60.0)
        assert len(alerts) >= 2
        
        # Check code coverage warning alert
        coverage_alert = next((a for a in alerts if a.metric_name == "code_coverage"), None)
        assert coverage_alert is not None
        assert coverage_alert.severity == AlertSeverity.WARNING
        assert coverage_alert.alert_type == AlertType.THRESHOLD_VIOLATION
        assert coverage_alert.current_value == 65.0
        assert coverage_alert.threshold_value == 70.0
        
        # Check maintainability index warning alert
        maintainability_alert = next((a for a in alerts if a.metric_name == "maintainability_index"), None)
        assert maintainability_alert is not None
        assert maintainability_alert.severity == AlertSeverity.WARNING
        assert maintainability_alert.alert_type == AlertType.THRESHOLD_VIOLATION
        assert maintainability_alert.current_value == 45.0
        assert maintainability_alert.threshold_value == 60.0
    
    @pytest.mark.asyncio
    async def test_regression_alert_generation(self, monitoring_service, sample_metrics):
        """Test regression-based alert generation"""
        project_id = "test-project"
        
        # Set up previous metrics (better than current)
        previous_metrics = QualityMetrics(
            project_id=project_id,
            timestamp=datetime.now() - timedelta(minutes=5),
            code_coverage=85.0,  # Was better
            cyclomatic_complexity=6.0,  # Was better
            maintainability_index=75.0,  # Was better
            technical_debt_ratio=0.1,
            test_quality_score=90.0,
            security_score=95.0
        )
        
        monitoring_service.last_metrics[project_id] = previous_metrics
        
        with patch('app.services.quality_monitoring_service.get_db'):
            alerts = await monitoring_service._check_regression_alerts(project_id, sample_metrics)
        
        # Should detect regressions in multiple metrics
        assert len(alerts) > 0
        
        # Check for code coverage regression
        coverage_regression = next((a for a in alerts if a.metric_name == "code_coverage"), None)
        assert coverage_regression is not None
        assert coverage_regression.alert_type == AlertType.REGRESSION
        assert coverage_regression.previous_value == 85.0
        assert coverage_regression.current_value == 65.0
        assert coverage_regression.regression_percentage > 0
    
    @pytest.mark.asyncio
    async def test_trend_analysis(self, monitoring_service):
        """Test trend analysis for metric degradation"""
        project_id = "test-project"
        metric_name = "code_coverage"
        
        # Create declining trend data
        historical_metrics = []
        base_time = datetime.now() - timedelta(hours=1)
        
        for i in range(5):
            metrics = QualityMetrics(
                project_id=project_id,
                timestamp=base_time + timedelta(minutes=i*10),
                code_coverage=90.0 - (i * 5),  # Declining trend: 90, 85, 80, 75, 70
                cyclomatic_complexity=5.0,
                maintainability_index=80.0,
                technical_debt_ratio=0.1,
                test_quality_score=85.0,
                security_score=90.0
            )
            historical_metrics.append(metrics)
        
        current_metrics = QualityMetrics(
            project_id=project_id,
            timestamp=datetime.now(),
            code_coverage=65.0,  # Continuing decline
            cyclomatic_complexity=5.0,
            maintainability_index=80.0,
            technical_debt_ratio=0.1,
            test_quality_score=85.0,
            security_score=90.0
        )
        
        alert = await monitoring_service._analyze_metric_trend(
            project_id, metric_name, historical_metrics, current_metrics
        )
        
        assert alert is not None
        assert alert.alert_type == AlertType.TREND_DEGRADATION
        assert alert.metric_name == metric_name
        assert alert.trend_direction == "declining"
    
    @pytest.mark.asyncio
    async def test_alert_processing(self, monitoring_service):
        """Test alert processing and storage"""
        alert = QualityAlert(
            project_id="test-project",
            alert_type=AlertType.THRESHOLD_VIOLATION,
            severity=AlertSeverity.WARNING,
            metric_name="code_coverage",
            current_value=65.0,
            threshold_value=70.0,
            message="Code coverage below warning threshold"
        )
        
        # Mock database operations
        with patch('app.services.quality_monitoring_service.get_db'):
            await monitoring_service._process_alert(alert)
        
        # Alert should be added to history
        assert len(monitoring_service.alert_history) == 1
        assert monitoring_service.alert_history[0] == alert
    
    @pytest.mark.asyncio
    async def test_alert_resolution(self, monitoring_service):
        """Test alert resolution functionality"""
        alert = QualityAlert(
            id="test-alert-123",
            project_id="test-project",
            alert_type=AlertType.THRESHOLD_VIOLATION,
            severity=AlertSeverity.WARNING,
            metric_name="code_coverage",
            current_value=65.0,
            threshold_value=70.0,
            message="Test alert"
        )
        
        monitoring_service.alert_history.append(alert)
        
        # Mock database operations
        with patch('app.services.quality_monitoring_service.get_db'):
            success = await monitoring_service.resolve_alert("test-alert-123")
        
        assert success
        assert alert.resolved
        assert alert.resolved_at is not None
    
    def test_alert_handler_management(self, monitoring_service):
        """Test adding and removing alert handlers"""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        
        # Add handlers
        monitoring_service.add_alert_handler(handler1)
        monitoring_service.add_alert_handler(handler2)
        
        assert len(monitoring_service.alert_handlers) == 2
        assert handler1 in monitoring_service.alert_handlers
        assert handler2 in monitoring_service.alert_handlers
        
        # Remove handler
        monitoring_service.remove_alert_handler(handler1)
        
        assert len(monitoring_service.alert_handlers) == 1
        assert handler1 not in monitoring_service.alert_handlers
        assert handler2 in monitoring_service.alert_handlers
    
    @pytest.mark.asyncio
    async def test_alert_history_filtering(self, monitoring_service):
        """Test alert history filtering by project and time"""
        base_time = datetime.now()
        
        # Create test alerts
        alerts = [
            QualityAlert(
                id="alert-1",
                project_id="project-1",
                alert_type=AlertType.THRESHOLD_VIOLATION,
                severity=AlertSeverity.WARNING,
                metric_name="code_coverage",
                message="Test alert 1",
                created_at=base_time - timedelta(hours=2)
            ),
            QualityAlert(
                id="alert-2",
                project_id="project-2",
                alert_type=AlertType.REGRESSION,
                severity=AlertSeverity.CRITICAL,
                metric_name="security_score",
                message="Test alert 2",
                created_at=base_time - timedelta(hours=1)
            ),
            QualityAlert(
                id="alert-3",
                project_id="project-1",
                alert_type=AlertType.CRITICAL_ISSUE,
                severity=AlertSeverity.CRITICAL,
                metric_name="maintainability_index",
                message="Test alert 3",
                created_at=base_time - timedelta(minutes=30)
            )
        ]
        
        monitoring_service.alert_history.extend(alerts)
        
        # Test filtering by project
        project1_alerts = await monitoring_service.get_alert_history("project-1", 24)
        assert len(project1_alerts) == 2
        assert all(alert.project_id == "project-1" for alert in project1_alerts)
        
        # Test filtering by time
        recent_alerts = await monitoring_service.get_alert_history(None, 1)
        assert len(recent_alerts) >= 1  # At least alerts from last hour
        
        # Test combined filtering
        recent_project1_alerts = await monitoring_service.get_alert_history("project-1", 1)
        assert len(recent_project1_alerts) == 1
        assert recent_project1_alerts[0].id == "alert-3"


class TestAlertThreshold:
    """Test cases for AlertThreshold configuration"""
    
    def test_threshold_creation(self):
        """Test creating alert thresholds"""
        threshold = AlertThreshold(
            metric_name="code_coverage",
            warning_threshold=70.0,
            critical_threshold=50.0,
            trend_window_minutes=60,
            min_samples=3,
            enabled=True
        )
        
        assert threshold.metric_name == "code_coverage"
        assert threshold.warning_threshold == 70.0
        assert threshold.critical_threshold == 50.0
        assert threshold.trend_window_minutes == 60
        assert threshold.min_samples == 3
        assert threshold.enabled
    
    def test_threshold_defaults(self):
        """Test default threshold values"""
        threshold = AlertThreshold("test_metric", 80.0, 60.0)
        
        assert threshold.trend_window_minutes == 60
        assert threshold.min_samples == 3
        assert threshold.enabled


class TestQualityMonitoringConfig:
    """Test cases for QualityMonitoringConfig"""
    
    def test_config_creation(self):
        """Test creating monitoring configuration"""
        config = QualityMonitoringConfig(
            websocket_port=9000,
            update_interval_seconds=15
        )
        
        assert config.websocket_port == 9000
        assert config.update_interval_seconds == 15
        assert len(config.alert_thresholds) > 0  # Default thresholds
        assert "websocket" in config.notification_channels
        assert "database" in config.notification_channels
    
    def test_default_thresholds(self):
        """Test default threshold configuration"""
        config = QualityMonitoringConfig()
        thresholds = config.alert_thresholds
        
        # Check that all expected metrics have thresholds
        metric_names = [t.metric_name for t in thresholds]
        expected_metrics = [
            "code_coverage",
            "cyclomatic_complexity", 
            "maintainability_index",
            "technical_debt_ratio",
            "test_quality_score",
            "security_score"
        ]
        
        for metric in expected_metrics:
            assert metric in metric_names
        
        # Check threshold values are reasonable
        for threshold in thresholds:
            assert threshold.warning_threshold > 0
            assert threshold.critical_threshold > 0
            assert threshold.trend_window_minutes > 0
            assert threshold.min_samples > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])