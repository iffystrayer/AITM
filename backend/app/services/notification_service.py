"""
Notification Service for Quality Alerts

This service handles sending notifications through various channels
when quality alerts are triggered.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..models.quality import QualityAlert, NotificationChannel, AlertSeverity, AlertType
from ..core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class NotificationMessage:
    """Represents a notification message"""
    alert: QualityAlert
    channel: NotificationChannel
    subject: str
    body: str
    formatted_body: str
    timestamp: datetime


class NotificationHandler(ABC):
    """Abstract base class for notification handlers"""
    
    @abstractmethod
    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send a notification message"""
        pass
    
    @abstractmethod
    def supports_channel_type(self, channel_type: str) -> bool:
        """Check if this handler supports the given channel type"""
        pass


class EmailNotificationHandler(NotificationHandler):
    """Email notification handler"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_host = smtp_config.get('host', 'localhost')
        self.smtp_port = smtp_config.get('port', 587)
        self.smtp_username = smtp_config.get('username')
        self.smtp_password = smtp_config.get('password')
        self.smtp_use_tls = smtp_config.get('use_tls', True)
        self.from_email = smtp_config.get('from_email', 'noreply@aitm.local')
    
    def supports_channel_type(self, channel_type: str) -> bool:
        return channel_type == "email"
    
    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send email notification"""
        try:
            to_emails = message.channel.configuration.get('to_emails', [])
            if not to_emails:
                logger.warning(f"No email addresses configured for channel {message.channel.name}")
                return False
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add plain text and HTML parts
            text_part = MIMEText(message.body, 'plain')
            html_part = MIMEText(message.formatted_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            await self._send_email_async(msg, to_emails)
            
            logger.info(f"Email notification sent for alert {message.alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    async def _send_email_async(self, msg: MIMEMultipart, to_emails: List[str]):
        """Send email asynchronously"""
        def send_email():
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg, to_addrs=to_emails)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, send_email)


class SlackNotificationHandler(NotificationHandler):
    """Slack notification handler"""
    
    def supports_channel_type(self, channel_type: str) -> bool:
        return channel_type == "slack"
    
    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send Slack notification"""
        try:
            webhook_url = message.channel.configuration.get('webhook_url')
            if not webhook_url:
                logger.warning(f"No webhook URL configured for Slack channel {message.channel.name}")
                return False
            
            # Create Slack message payload
            payload = self._create_slack_payload(message)
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert {message.alert.id}")
                        return True
                    else:
                        logger.error(f"Slack notification failed with status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def _create_slack_payload(self, message: NotificationMessage) -> Dict[str, Any]:
        """Create Slack message payload"""
        alert = message.alert
        
        # Choose color based on severity
        color_map = {
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.WARNING: "#ffaa00",
            AlertSeverity.INFO: "#0099ff"
        }
        color = color_map.get(alert.severity, "#cccccc")
        
        # Create attachment
        attachment = {
            "color": color,
            "title": message.subject,
            "text": message.body,
            "fields": [
                {
                    "title": "Project",
                    "value": alert.project_id,
                    "short": True
                },
                {
                    "title": "Severity",
                    "value": alert.severity.value.upper(),
                    "short": True
                },
                {
                    "title": "Metric",
                    "value": alert.metric_name,
                    "short": True
                },
                {
                    "title": "Current Value",
                    "value": f"{alert.current_value:.2f}" if alert.current_value else "N/A",
                    "short": True
                }
            ],
            "timestamp": int(alert.created_at.timestamp())
        }
        
        return {
            "text": f"Quality Alert: {alert.alert_type.value.replace('_', ' ').title()}",
            "attachments": [attachment]
        }


class WebhookNotificationHandler(NotificationHandler):
    """Generic webhook notification handler"""
    
    def supports_channel_type(self, channel_type: str) -> bool:
        return channel_type == "webhook"
    
    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send webhook notification"""
        try:
            webhook_url = message.channel.configuration.get('url')
            if not webhook_url:
                logger.warning(f"No webhook URL configured for channel {message.channel.name}")
                return False
            
            # Create webhook payload
            payload = {
                "alert": message.alert.to_dict(),
                "message": {
                    "subject": message.subject,
                    "body": message.body,
                    "formatted_body": message.formatted_body
                },
                "timestamp": message.timestamp.isoformat(),
                "channel": message.channel.name
            }
            
            # Add custom headers if configured
            headers = message.channel.configuration.get('headers', {})
            headers['Content-Type'] = 'application/json'
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, headers=headers) as response:
                    if 200 <= response.status < 300:
                        logger.info(f"Webhook notification sent for alert {message.alert.id}")
                        return True
                    else:
                        logger.error(f"Webhook notification failed with status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


class WebSocketNotificationHandler(NotificationHandler):
    """WebSocket notification handler (for real-time dashboard updates)"""
    
    def __init__(self, websocket_service):
        self.websocket_service = websocket_service
    
    def supports_channel_type(self, channel_type: str) -> bool:
        return channel_type == "websocket"
    
    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send WebSocket notification"""
        try:
            # This is handled by the monitoring service's WebSocket broadcasting
            # Just log that we would send it
            logger.info(f"WebSocket notification queued for alert {message.alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
            return False


class NotificationService:
    """Main notification service that coordinates all notification handlers"""
    
    def __init__(self):
        self.handlers: List[NotificationHandler] = []
        self.channels: Dict[str, NotificationChannel] = {}
        self._initialize_handlers()
    
    def _initialize_handlers(self):
        """Initialize notification handlers"""
        settings = get_settings()
        
        # Email handler
        if hasattr(settings, 'smtp_config'):
            self.handlers.append(EmailNotificationHandler(settings.smtp_config))
        
        # Slack handler
        self.handlers.append(SlackNotificationHandler())
        
        # Webhook handler
        self.handlers.append(WebhookNotificationHandler())
        
        # WebSocket handler (will be set by monitoring service)
        # self.handlers.append(WebSocketNotificationHandler(websocket_service))
    
    def add_handler(self, handler: NotificationHandler):
        """Add a custom notification handler"""
        self.handlers.append(handler)
    
    def remove_handler(self, handler: NotificationHandler):
        """Remove a notification handler"""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    async def register_channel(self, channel: NotificationChannel):
        """Register a notification channel"""
        self.channels[channel.id] = channel
        logger.info(f"Registered notification channel: {channel.name} ({channel.channel_type})")
    
    async def unregister_channel(self, channel_id: str):
        """Unregister a notification channel"""
        if channel_id in self.channels:
            del self.channels[channel_id]
            logger.info(f"Unregistered notification channel: {channel_id}")
    
    async def send_alert_notification(self, alert: QualityAlert) -> Dict[str, bool]:
        """Send notifications for an alert through all applicable channels"""
        results = {}
        
        # Find applicable channels
        applicable_channels = self._find_applicable_channels(alert)
        
        if not applicable_channels:
            logger.info(f"No applicable notification channels for alert {alert.id}")
            return results
        
        # Send notifications through each channel
        for channel in applicable_channels:
            try:
                # Find handler for this channel type
                handler = self._find_handler(channel.channel_type)
                if not handler:
                    logger.warning(f"No handler found for channel type: {channel.channel_type}")
                    results[channel.id] = False
                    continue
                
                # Create notification message
                message = self._create_notification_message(alert, channel)
                
                # Send notification
                success = await handler.send_notification(message)
                results[channel.id] = success
                
                if success:
                    logger.info(f"Notification sent successfully through channel {channel.name}")
                else:
                    logger.error(f"Failed to send notification through channel {channel.name}")
                    
            except Exception as e:
                logger.error(f"Error sending notification through channel {channel.name}: {e}")
                results[channel.id] = False
        
        return results
    
    def _find_applicable_channels(self, alert: QualityAlert) -> List[NotificationChannel]:
        """Find channels that should receive this alert"""
        applicable_channels = []
        
        for channel in self.channels.values():
            if not channel.enabled:
                continue
            
            # Check if channel accepts this alert type
            if channel.alert_types and alert.alert_type not in channel.alert_types:
                continue
            
            # Check if channel accepts this severity level
            if channel.severity_levels and alert.severity not in channel.severity_levels:
                continue
            
            applicable_channels.append(channel)
        
        return applicable_channels
    
    def _find_handler(self, channel_type: str) -> Optional[NotificationHandler]:
        """Find handler that supports the given channel type"""
        for handler in self.handlers:
            if handler.supports_channel_type(channel_type):
                return handler
        return None
    
    def _create_notification_message(self, alert: QualityAlert, 
                                   channel: NotificationChannel) -> NotificationMessage:
        """Create a notification message for the alert and channel"""
        # Create subject
        subject = f"Quality Alert: {alert.alert_type.value.replace('_', ' ').title()} - {alert.severity.value.upper()}"
        
        # Create body
        body = self._create_text_body(alert)
        
        # Create formatted body (HTML for email, etc.)
        formatted_body = self._create_formatted_body(alert)
        
        return NotificationMessage(
            alert=alert,
            channel=channel,
            subject=subject,
            body=body,
            formatted_body=formatted_body,
            timestamp=datetime.now()
        )
    
    def _create_text_body(self, alert: QualityAlert) -> str:
        """Create plain text notification body"""
        lines = [
            f"A quality alert has been triggered for project {alert.project_id}:",
            "",
            f"Alert Type: {alert.alert_type.value.replace('_', ' ').title()}",
            f"Severity: {alert.severity.value.upper()}",
            f"Metric: {alert.metric_name}",
            f"Message: {alert.message}",
            "",
            f"Details:",
        ]
        
        if alert.current_value is not None:
            lines.append(f"  Current Value: {alert.current_value:.2f}")
        
        if alert.threshold_value is not None:
            lines.append(f"  Threshold: {alert.threshold_value:.2f}")
        
        if alert.previous_value is not None:
            lines.append(f"  Previous Value: {alert.previous_value:.2f}")
        
        if alert.regression_percentage is not None:
            lines.append(f"  Regression: {alert.regression_percentage:.1f}%")
        
        if alert.trend_direction:
            lines.append(f"  Trend: {alert.trend_direction}")
        
        lines.extend([
            "",
            f"Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "Please review and take appropriate action."
        ])
        
        return "\n".join(lines)
    
    def _create_formatted_body(self, alert: QualityAlert) -> str:
        """Create formatted (HTML) notification body"""
        severity_colors = {
            AlertSeverity.CRITICAL: "#ff4444",
            AlertSeverity.WARNING: "#ffaa00",
            AlertSeverity.INFO: "#0099ff"
        }
        
        color = severity_colors.get(alert.severity, "#666666")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="border-left: 4px solid {color}; padding-left: 20px; margin: 20px 0;">
                <h2 style="color: {color}; margin-top: 0;">Quality Alert</h2>
                <p><strong>Project:</strong> {alert.project_id}</p>
                <p><strong>Alert Type:</strong> {alert.alert_type.value.replace('_', ' ').title()}</p>
                <p><strong>Severity:</strong> <span style="color: {color}; font-weight: bold;">{alert.severity.value.upper()}</span></p>
                <p><strong>Metric:</strong> {alert.metric_name}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                
                <h3>Details:</h3>
                <ul>
        """
        
        if alert.current_value is not None:
            html += f"<li><strong>Current Value:</strong> {alert.current_value:.2f}</li>"
        
        if alert.threshold_value is not None:
            html += f"<li><strong>Threshold:</strong> {alert.threshold_value:.2f}</li>"
        
        if alert.previous_value is not None:
            html += f"<li><strong>Previous Value:</strong> {alert.previous_value:.2f}</li>"
        
        if alert.regression_percentage is not None:
            html += f"<li><strong>Regression:</strong> {alert.regression_percentage:.1f}%</li>"
        
        if alert.trend_direction:
            html += f"<li><strong>Trend:</strong> {alert.trend_direction}</li>"
        
        html += f"""
                </ul>
                
                <p><strong>Created:</strong> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                
                <p style="margin-top: 30px; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                    Please review this alert and take appropriate action to address the quality issue.
                </p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def get_channel_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered channels"""
        status = {}
        
        for channel_id, channel in self.channels.items():
            handler = self._find_handler(channel.channel_type)
            
            status[channel_id] = {
                "name": channel.name,
                "type": channel.channel_type,
                "enabled": channel.enabled,
                "has_handler": handler is not None,
                "alert_types": [at.value for at in channel.alert_types],
                "severity_levels": [sl.value for sl in channel.severity_levels]
            }
        
        return status


# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get the global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service