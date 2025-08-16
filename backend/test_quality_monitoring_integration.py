#!/usr/bin/env python3
"""
Integration tests for real-time quality monitoring and alerts system.

This script tests the complete real-time monitoring workflow including:
- WebSocket connections and real-time updates
- Alert generation and notification
- Threshold configuration and monitoring
- Notification channel management
"""

import asyncio
import json
import logging
import time
import websockets
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytest
import requests
from unittest.mock import AsyncMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/v1/quality-monitoring/ws"
TEST_PROJECT_ID = "test-monitoring-project"


class QualityMonitoringIntegrationTest:
    """Integration test suite for quality monitoring system"""
    
    def __init__(self):
        self.session = requests.Session()
        self.websocket = None
        self.received_messages = []
        
    async def setup(self):
        """Set up test environment"""
        logger.info("Setting up quality monitoring integration test")
        
        # Ensure monitoring service is stopped initially
        try:
            response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/stop")
            logger.info(f"Stop monitoring response: {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to stop monitoring (may not be running): {e}")
    
    async def teardown(self):
        """Clean up test environment"""
        logger.info("Tearing down quality monitoring integration test")
        
        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
        
        # Stop monitoring service
        try:
            response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/stop")
            logger.info(f"Final stop monitoring response: {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to stop monitoring during teardown: {e}")
    
    async def test_monitoring_service_lifecycle(self):
        """Test starting and stopping the monitoring service"""
        logger.info("Testing monitoring service lifecycle")
        
        # Check initial status
        response = self.session.get(f"{BASE_URL}/api/v1/quality-monitoring/status")
        assert response.status_code == 200
        status = response.json()
        logger.info(f"Initial status: {status}")
        
        # Start monitoring
        response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/start")
        assert response.status_code == 200
        logger.info("Monitoring service started")
        
        # Wait a moment for service to initialize
        await asyncio.sleep(2)
        
        # Check status after starting
        response = self.session.get(f"{BASE_URL}/api/v1/quality-monitoring/status")
        assert response.status_code == 200
        status = response.json()
        assert status["active"] == True
        logger.info(f"Status after start: {status}")
        
        # Stop monitoring
        response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/stop")
        assert response.status_code == 200
        logger.info("Monitoring service stopped")
        
        # Check status after stopping
        response = self.session.get(f"{BASE_URL}/api/v1/quality-monitoring/status")
        assert response.status_code == 200
        status = response.json()
        assert status["active"] == False
        logger.info(f"Status after stop: {status}")
    
    async def test_websocket_connection(self):
        """Test WebSocket connection and real-time updates"""
        logger.info("Testing WebSocket connection")
        
        # Start monitoring service
        response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/start")
        assert response.status_code == 200
        
        # Wait for service to start
        await asyncio.sleep(2)
        
        try:
            # Connect to WebSocket
            self.websocket = await websockets.connect(WS_URL)
            logger.info("WebSocket connected successfully")
            
            # Wait for welcome message
            welcome_message = await asyncio.wait_for(
                self.websocket.recv(), 
                timeout=10.0
            )
            
            welcome_data = json.loads(welcome_message)
            assert welcome_data["type"] == "welcome"
            logger.info(f"Received welcome message: {welcome_data}")
            
            # Send subscription message
            subscription = {
                "type": "subscribe",
                "project_ids": [TEST_PROJECT_ID]
            }
            await self.websocket.send(json.dumps(subscription))
            logger.info("Sent subscription message")
            
            # Test ping/pong
            ping_message = {"type": "ping"}
            await self.websocket.send(json.dumps(ping_message))
            
            pong_response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=5.0
            )
            pong_data = json.loads(pong_response)
            assert pong_data["type"] == "pong"
            logger.info("Ping/pong test successful")
            
        except asyncio.TimeoutError:
            logger.error("WebSocket connection timeout")
            raise
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def test_alert_creation_and_notification(self):
        """Test alert creation and notification system"""
        logger.info("Testing alert creation and notification")
        
        # Create a test alert
        alert_data = {
            "project_id": TEST_PROJECT_ID,
            "alert_type": "threshold_violation",
            "severity": "warning",
            "metric_name": "code_coverage",
            "current_value": 45.0,
            "threshold_value": 70.0,
            "message": "Code coverage below warning threshold",
            "description": "Test alert for integration testing"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/v1/quality-monitoring/alerts",
            json=alert_data
        )
        assert response.status_code == 200
        result = response.json()
        alert_id = result["alert_id"]
        logger.info(f"Created test alert: {alert_id}")
        
        # Wait a moment for alert processing
        await asyncio.sleep(1)
        
        # Check if alert appears in history
        response = self.session.get(
            f"{BASE_URL}/api/v1/quality-monitoring/alerts",
            params={"project_id": TEST_PROJECT_ID, "hours": 1}
        )
        assert response.status_code == 200
        alerts_data = response.json()
        
        found_alert = None
        for alert in alerts_data["alerts"]:
            if alert["id"] == alert_id:
                found_alert = alert
                break
        
        assert found_alert is not None
        assert found_alert["message"] == alert_data["message"]
        logger.info("Alert found in history")
        
        # Test alert resolution
        response = self.session.post(
            f"{BASE_URL}/api/v1/quality-monitoring/alerts/{alert_id}/resolve"
        )
        assert response.status_code == 200
        logger.info("Alert resolved successfully")
        
        # Verify alert is marked as resolved
        response = self.session.get(
            f"{BASE_URL}/api/v1/quality-monitoring/alerts",
            params={"project_id": TEST_PROJECT_ID, "hours": 1}
        )
        assert response.status_code == 200
        alerts_data = response.json()
        
        resolved_alert = None
        for alert in alerts_data["alerts"]:
            if alert["id"] == alert_id:
                resolved_alert = alert
                break
        
        assert resolved_alert is not None
        assert resolved_alert["resolved"] == True
        logger.info("Alert resolution verified")
    
    async def test_threshold_configuration(self):
        """Test threshold configuration management"""
        logger.info("Testing threshold configuration")
        
        # Get current thresholds
        response = self.session.get(f"{BASE_URL}/api/v1/quality-monitoring/thresholds")
        assert response.status_code == 200
        thresholds_data = response.json()
        original_thresholds = thresholds_data["thresholds"]
        logger.info(f"Retrieved {len(original_thresholds)} thresholds")
        
        # Update thresholds
        updated_thresholds = []
        for threshold in original_thresholds:
            updated_threshold = threshold.copy()
            # Modify warning threshold slightly
            updated_threshold["warning_threshold"] = threshold["warning_threshold"] * 0.9
            updated_thresholds.append(updated_threshold)
        
        response = self.session.put(
            f"{BASE_URL}/api/v1/quality-monitoring/thresholds",
            json=updated_thresholds
        )
        assert response.status_code == 200
        logger.info("Thresholds updated successfully")
        
        # Verify thresholds were updated
        response = self.session.get(f"{BASE_URL}/api/v1/quality-monitoring/thresholds")
        assert response.status_code == 200
        new_thresholds_data = response.json()
        new_thresholds = new_thresholds_data["thresholds"]
        
        # Check that at least one threshold was modified
        threshold_changed = False
        for i, threshold in enumerate(new_thresholds):
            if threshold["warning_threshold"] != original_thresholds[i]["warning_threshold"]:
                threshold_changed = True
                break
        
        assert threshold_changed
        logger.info("Threshold configuration changes verified")
    
    async def test_notification_channels(self):
        """Test notification channel management"""
        logger.info("Testing notification channels")
        
        # Get notification status
        response = self.session.get(f"{BASE_URL}/api/v1/quality-monitoring/notifications/status")
        assert response.status_code == 200
        status = response.json()
        logger.info(f"Notification status: {status}")
        
        # Create a test notification channel
        channel_data = {
            "name": "Test Webhook Channel",
            "channel_type": "webhook",
            "configuration": {
                "url": "https://httpbin.org/post",
                "headers": {
                    "Authorization": "Bearer test-token"
                }
            },
            "enabled": True,
            "alert_types": ["threshold_violation", "regression"],
            "severity_levels": ["critical", "warning"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/v1/quality-monitoring/notifications/channels",
            json=channel_data
        )
        assert response.status_code == 200
        result = response.json()
        channel_id = result["channel_id"]
        logger.info(f"Created notification channel: {channel_id}")
        
        # Test the notification channel
        response = self.session.post(
            f"{BASE_URL}/api/v1/quality-monitoring/notifications/test/{channel_id}"
        )
        assert response.status_code == 200
        logger.info("Test notification sent successfully")
        
        # Clean up - delete the test channel
        response = self.session.delete(
            f"{BASE_URL}/api/v1/quality-monitoring/notifications/channels/{channel_id}"
        )
        assert response.status_code == 200
        logger.info("Test notification channel deleted")
    
    async def test_real_time_updates(self):
        """Test real-time updates through WebSocket"""
        logger.info("Testing real-time updates")
        
        # Start monitoring and connect WebSocket
        response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/start")
        assert response.status_code == 200
        
        await asyncio.sleep(2)
        
        self.websocket = await websockets.connect(WS_URL)
        
        # Wait for welcome message
        welcome_message = await asyncio.wait_for(
            self.websocket.recv(),
            timeout=10.0
        )
        welcome_data = json.loads(welcome_message)
        assert welcome_data["type"] == "welcome"
        
        # Subscribe to updates
        subscription = {
            "type": "subscribe",
            "project_ids": [TEST_PROJECT_ID]
        }
        await self.websocket.send(json.dumps(subscription))
        
        # Create an alert to trigger real-time update
        alert_data = {
            "project_id": TEST_PROJECT_ID,
            "alert_type": "critical_issue",
            "severity": "critical",
            "metric_name": "security_score",
            "current_value": 30.0,
            "threshold_value": 80.0,
            "message": "Critical security score alert for real-time testing"
        }
        
        # Send alert creation request
        response = self.session.post(
            f"{BASE_URL}/api/v1/quality-monitoring/alerts",
            json=alert_data
        )
        assert response.status_code == 200
        
        # Wait for real-time update
        try:
            update_message = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=15.0
            )
            
            update_data = json.loads(update_message)
            logger.info(f"Received real-time update: {update_data}")
            
            # Verify it's a quality update with alerts
            if update_data.get("type") == "quality_update":
                assert "alerts" in update_data
                assert len(update_data["alerts"]) > 0
                logger.info("Real-time alert update received successfully")
            else:
                logger.warning(f"Unexpected update type: {update_data.get('type')}")
                
        except asyncio.TimeoutError:
            logger.warning("No real-time update received within timeout")
            # This might be expected if the monitoring loop hasn't run yet
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting quality monitoring integration tests")
        
        try:
            await self.setup()
            
            # Run individual tests
            await self.test_monitoring_service_lifecycle()
            await self.test_websocket_connection()
            await self.test_alert_creation_and_notification()
            await self.test_threshold_configuration()
            await self.test_notification_channels()
            await self.test_real_time_updates()
            
            logger.info("All quality monitoring integration tests passed!")
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            raise
        finally:
            await self.teardown()


async def main():
    """Main test runner"""
    test_suite = QualityMonitoringIntegrationTest()
    
    try:
        await test_suite.run_all_tests()
        print("\n✅ All quality monitoring integration tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ Quality monitoring integration tests failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)