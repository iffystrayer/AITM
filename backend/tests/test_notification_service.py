"""
Unit tests for Notification Service

Tests the notification system functionality including
channel management, message formatting, and alert handling.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from app.services.notification_service import (
    NotificationService,
    NotificationMessage,
    EmailNotificationHandler,
    SlackNotificationHandler,
    WebhookNotificationHandler,
    WebSocketNotificationHandler
)
from app.models.quality import (
    QualityAlert,
    NotificationChannel,
    AlertType,
    AlertSeverity,
    AlertStatus
)


@pytest.fixture
def sample_alert():
    """Create a sample quality alert"""
    return QualityAlert(
        id="test-alert-123",
        project_id="test-project",
        alert_type=AlertType.THRESHOLD_VIOLATION,
        severity=AlertSeverity.WARNING,
        metric_name="code_coverage",
        current_value=65.0,
        threshold_value=70.0,
        message="Code coverage below warning threshold",
        description="Test alert for notification testing",
        created_at=datetime.now()
    )


@pytest.fixture
def email_channel():
    """Create an email notification channel"""
    return NotificationChannel(
        id="email-channel-1",
        name="Test Email Channel",
        channel_type="email",
        configuration={
            "to_emails": ["test@example.com", "admin@example.com"]
        },
        enabled=True,
        alert_types=[AlertType.THRESHOLD_VIOLATION, AlertType.REGRESSION],
        severity_levels=[AlertSeverity.CRITICAL, AlertSeverity.WARNING]
    )


@pytest.fixture
def slack_channel():
    """Create a Slack notification channel"""
    return NotificationChannel(
        id="slack-channel-1",
        name="Test Slack Channel",
        channel_type="slack",
        configuration={
            "webhook_url": "https://hooks.slack.com/services/test/webhook"
        },
        enabled=True,
        alert_types=[AlertType.THRESHOLD_VIOLATION],
        severity_levels=[AlertSeverity.CRITICAL, AlertSeverity.WARNING, AlertSeverity.INFO]
    )


@pytest.fixture
def webhook_channel():
    """Create a webhook notification channel"""
    return NotificationChannel(
        id="webhook-channel-1",
        name="Test Webhook Channel",
        channel_type="webhook",
        configuration={
            "url": "https://api.example.com/webhooks/alerts",
            "headers": {"Authorization": "Bearer test-token"}
        },
        enabled=True,
        alert_types=[AlertType.THRESHOLD_VIOLATION, AlertType.CRITICAL_ISSUE],
        severity_levels=[AlertSeverity.CRITICAL, AlertSeverity.WARNING]
    )


class TestNotificationService:
    """Test cases for NotificationService"""
    
    def test_service_initialization(self):
        """Test notification service initialization"""
        service = NotificationService()
        
        assert len(service.handlers) > 0  # Should have default handlers
        assert len(service.channels) == 0  # No channels registered initially
    
    @pytest.mark.asyncio
    async def test_channel_registration(self, email_channel):
        """Test registering and unregistering notification channels"""
        service = NotificationService()
        
        # Register channel
        await service.register_channel(email_channel)
        assert email_channel.id in service.channels
        assert service.channels[email_channel.id] == email_channel
        
        # Unregister channel
        await service.unregister_channel(email_channel.id)
        assert email_channel.id not in service.channels
    
    def test_handler_management(self):
        """Test adding and removing notification handlers"""
        service = NotificationService()
        initial_handler_count = len(service.handlers)
        
        # Add custom handler
        custom_handler = MagicMock()
        service.add_handler(custom_handler)
        
        assert len(service.handlers) == initial_handler_count + 1
        assert custom_handler in service.handlers
        
        # Remove handler
        service.remove_handler(custom_handler)
        assert len(service.handlers) == initial_handler_count
        assert custom_handler not in service.handlers
    
    def test_applicable_channels_filtering(self, sample_alert, email_channel, slack_channel):
        """Test finding applicable channels for an alert"""
        service = NotificationService()
        
        # Register channels
        service.channels[email_channel.id] = email_channel
        service.channels[slack_channel.id] = slack_channel
        
        # Test with matching alert
        applicable_channels = service._find_applicable_channels(sample_alert)
        
        # Both channels should match (both accept THRESHOLD_VIOLATION and WARNING)
        assert len(applicable_channels) == 2
        channel_ids = [c.id for c in applicable_channels]
        assert email_channel.id in channel_ids
        assert slack_channel.id in channel_ids
    
    def test_applicable_channels_filtering_by_type(self, email_channel, slack_channel):
        """Test filtering channels by alert type"""
        service = NotificationService()
        
        # Create alert with type not supported by email channel
        alert = QualityAlert(
            project_id="test-project",
            alert_type=AlertType.CRITICAL_ISSUE,  # Not in email_channel.alert_types
            severity=AlertSeverity.WARNING,
            metric_name="security_score",
            message="Critical security issue"
        )
        
        service.channels[email_channel.id] = email_channel
        service.channels[slack_channel.id] = slack_channel
        
        applicable_channels = service._find_applicable_channels(alert)
        
        # Only slack channel should match (it has THRESHOLD_VIOLATION in alert_types)
        # Actually, slack_channel also has alert_types restrictions, so no channels should match
        assert len(applicable_channels) == 0
    
    def test_applicable_channels_filtering_by_severity(self, email_channel):
        """Test filtering channels by severity level"""
        service = NotificationService()
        
        # Create INFO alert (not in email_channel.severity_levels)
        alert = QualityAlert(
            project_id="test-project",
            alert_type=AlertType.THRESHOLD_VIOLATION,
            severity=AlertSeverity.INFO,  # Not in email_channel.severity_levels
            metric_name="code_coverage",
            message="Info level alert"
        )
        
        service.channels[email_channel.id] = email_channel
        
        applicable_channels = service._find_applicable_channels(alert)
        
        # No channels should match
        assert len(applicable_channels) == 0
    
    def test_notification_message_creation(self, sample_alert, email_channel):
        """Test creating notification messages"""
        service = NotificationService()
        
        message = service._create_notification_message(sample_alert, email_channel)
        
        assert isinstance(message, NotificationMessage)
        assert message.alert == sample_alert
        assert message.channel == email_channel
        assert "Quality Alert" in message.subject
        assert "WARNING" in message.subject
        assert sample_alert.message in message.body
        assert sample_alert.project_id in message.body
        assert len(message.formatted_body) > len(message.body)  # HTML should be longer
    
    def test_text_body_formatting(self, sample_alert):
        """Test plain text body formatting"""
        service = NotificationService()
        
        body = service._create_text_body(sample_alert)
        
        assert sample_alert.project_id in body
        assert sample_alert.message in body
        assert "Current Value: 65.00" in body
        assert "Threshold: 70.00" in body
        assert "WARNING" in body
    
    def test_html_body_formatting(self, sample_alert):
        """Test HTML body formatting"""
        service = NotificationService()
        
        html_body = service._create_formatted_body(sample_alert)
        
        assert "<html>" in html_body
        assert "body style=" in html_body  # Check for body tag with style
        assert sample_alert.project_id in html_body
        assert sample_alert.message in html_body
        assert "Current Value:</strong> 65.00" in html_body
        assert "Threshold:</strong> 70.00" in html_body
    
    @pytest.mark.asyncio
    async def test_channel_status_reporting(self, email_channel, slack_channel):
        """Test getting channel status"""
        service = NotificationService()
        
        # Register channels
        await service.register_channel(email_channel)
        await service.register_channel(slack_channel)
        
        status = await service.get_channel_status()
        
        assert len(status) == 2
        assert email_channel.id in status
        assert slack_channel.id in status
        
        email_status = status[email_channel.id]
        assert email_status["name"] == email_channel.name
        assert email_status["type"] == email_channel.channel_type
        assert email_status["enabled"] == email_channel.enabled
        # Email handler might not be available without SMTP config
        assert "has_handler" in email_status


class TestEmailNotificationHandler:
    """Test cases for EmailNotificationHandler"""
    
    def test_handler_initialization(self):
        """Test email handler initialization"""
        smtp_config = {
            "host": "smtp.example.com",
            "port": 587,
            "username": "test@example.com",
            "password": "password",
            "use_tls": True,
            "from_email": "noreply@example.com"
        }
        
        handler = EmailNotificationHandler(smtp_config)
        
        assert handler.smtp_host == "smtp.example.com"
        assert handler.smtp_port == 587
        assert handler.smtp_username == "test@example.com"
        assert handler.smtp_password == "password"
        assert handler.smtp_use_tls == True
        assert handler.from_email == "noreply@example.com"
    
    def test_channel_type_support(self):
        """Test email handler channel type support"""
        handler = EmailNotificationHandler({})
        
        assert handler.supports_channel_type("email") == True
        assert handler.supports_channel_type("slack") == False
        assert handler.supports_channel_type("webhook") == False


class TestSlackNotificationHandler:
    """Test cases for SlackNotificationHandler"""
    
    def test_channel_type_support(self):
        """Test Slack handler channel type support"""
        handler = SlackNotificationHandler()
        
        assert handler.supports_channel_type("slack") == True
        assert handler.supports_channel_type("email") == False
        assert handler.supports_channel_type("webhook") == False
    
    def test_slack_payload_creation(self, sample_alert, slack_channel):
        """Test Slack message payload creation"""
        handler = SlackNotificationHandler()
        
        message = NotificationMessage(
            alert=sample_alert,
            channel=slack_channel,
            subject="Test Alert",
            body="Test message body",
            formatted_body="<html>Test</html>",
            timestamp=datetime.now()
        )
        
        payload = handler._create_slack_payload(message)
        
        assert "text" in payload
        assert "attachments" in payload
        assert len(payload["attachments"]) == 1
        
        attachment = payload["attachments"][0]
        assert "color" in attachment
        assert "title" in attachment
        assert "fields" in attachment
        
        # Check fields
        field_titles = [field["title"] for field in attachment["fields"]]
        assert "Project" in field_titles
        assert "Severity" in field_titles
        assert "Metric" in field_titles
        assert "Current Value" in field_titles


class TestWebhookNotificationHandler:
    """Test cases for WebhookNotificationHandler"""
    
    def test_channel_type_support(self):
        """Test webhook handler channel type support"""
        handler = WebhookNotificationHandler()
        
        assert handler.supports_channel_type("webhook") == True
        assert handler.supports_channel_type("email") == False
        assert handler.supports_channel_type("slack") == False


class TestWebSocketNotificationHandler:
    """Test cases for WebSocketNotificationHandler"""
    
    def test_channel_type_support(self):
        """Test WebSocket handler channel type support"""
        websocket_service = MagicMock()
        handler = WebSocketNotificationHandler(websocket_service)
        
        assert handler.supports_channel_type("websocket") == True
        assert handler.supports_channel_type("email") == False
        assert handler.supports_channel_type("slack") == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])