#!/usr/bin/env python3
"""
Quality Monitoring Real-time Demo

This script demonstrates the real-time quality monitoring and alerting system
by simulating quality metric changes and showing how alerts are generated
and notifications are sent.
"""

import asyncio
import json
import logging
import random
import time
import websockets
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Demo configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/v1/quality-monitoring/ws"
DEMO_PROJECT_ID = "demo-quality-project"


@dataclass
class QualityMetricsSnapshot:
    """Represents a quality metrics snapshot"""
    project_id: str
    timestamp: datetime
    code_coverage: float
    cyclomatic_complexity: float
    maintainability_index: float
    technical_debt_ratio: float
    test_quality_score: float
    security_score: float


class QualityMonitoringDemo:
    """Demo class for quality monitoring system"""
    
    def __init__(self):
        self.session = requests.Session()
        self.websocket = None
        self.demo_running = False
        self.metrics_history = []
        
    async def setup_demo(self):
        """Set up the demo environment"""
        logger.info("🚀 Setting up Quality Monitoring Demo")
        
        # Stop any existing monitoring
        try:
            response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/stop")
            logger.info("Stopped existing monitoring service")
        except Exception as e:
            logger.info("No existing monitoring service to stop")
        
        # Configure demo thresholds
        demo_thresholds = [
            {
                "metric_name": "code_coverage",
                "warning_threshold": 70.0,
                "critical_threshold": 50.0,
                "trend_window_minutes": 5,
                "min_samples": 3,
                "enabled": True
            },
            {
                "metric_name": "cyclomatic_complexity",
                "warning_threshold": 10.0,
                "critical_threshold": 15.0,
                "trend_window_minutes": 5,
                "min_samples": 3,
                "enabled": True
            },
            {
                "metric_name": "maintainability_index",
                "warning_threshold": 60.0,
                "critical_threshold": 40.0,
                "trend_window_minutes": 5,
                "min_samples": 3,
                "enabled": True
            },
            {
                "metric_name": "technical_debt_ratio",
                "warning_threshold": 0.3,
                "critical_threshold": 0.5,
                "trend_window_minutes": 5,
                "min_samples": 3,
                "enabled": True
            },
            {
                "metric_name": "test_quality_score",
                "warning_threshold": 70.0,
                "critical_threshold": 50.0,
                "trend_window_minutes": 5,
                "min_samples": 3,
                "enabled": True
            },
            {
                "metric_name": "security_score",
                "warning_threshold": 80.0,
                "critical_threshold": 60.0,
                "trend_window_minutes": 5,
                "min_samples": 3,
                "enabled": True
            }
        ]
        
        # Update thresholds
        response = self.session.put(
            f"{BASE_URL}/api/v1/quality-monitoring/thresholds",
            json=demo_thresholds
        )
        if response.status_code == 200:
            logger.info("✅ Demo thresholds configured")
        else:
            logger.warning(f"Failed to configure thresholds: {response.status_code}")
        
        # Create demo notification channel
        channel_data = {
            "name": "Demo Console Channel",
            "channel_type": "webhook",
            "configuration": {
                "url": "https://httpbin.org/post",
                "headers": {"Content-Type": "application/json"}
            },
            "enabled": True,
            "alert_types": ["threshold_violation", "regression", "critical_issue"],
            "severity_levels": ["critical", "warning", "info"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/v1/quality-monitoring/notifications/channels",
            json=channel_data
        )
        if response.status_code == 200:
            result = response.json()
            self.demo_channel_id = result["channel_id"]
            logger.info(f"✅ Demo notification channel created: {self.demo_channel_id}")
        else:
            logger.warning("Failed to create demo notification channel")
            self.demo_channel_id = None
        
        # Start monitoring service
        response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/start")
        if response.status_code == 200:
            logger.info("✅ Monitoring service started")
        else:
            logger.error(f"Failed to start monitoring service: {response.status_code}")
            return False
        
        # Wait for service to initialize
        await asyncio.sleep(3)
        
        return True
    
    async def connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        try:
            logger.info("🔌 Connecting to WebSocket...")
            self.websocket = await websockets.connect(WS_URL)
            
            # Wait for welcome message
            welcome_message = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=10.0
            )
            welcome_data = json.loads(welcome_message)
            logger.info(f"📨 Received welcome message: {welcome_data['type']}")
            
            # Subscribe to demo project updates
            subscription = {
                "type": "subscribe",
                "project_ids": [DEMO_PROJECT_ID]
            }
            await self.websocket.send(json.dumps(subscription))
            logger.info(f"📡 Subscribed to updates for project: {DEMO_PROJECT_ID}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect WebSocket: {e}")
            return False
    
    def generate_initial_metrics(self) -> QualityMetricsSnapshot:
        """Generate initial quality metrics"""
        return QualityMetricsSnapshot(
            project_id=DEMO_PROJECT_ID,
            timestamp=datetime.now(),
            code_coverage=85.0,
            cyclomatic_complexity=8.5,
            maintainability_index=75.0,
            technical_debt_ratio=0.15,
            test_quality_score=80.0,
            security_score=90.0
        )
    
    def simulate_quality_degradation(self, current_metrics: QualityMetricsSnapshot) -> QualityMetricsSnapshot:
        """Simulate gradual quality degradation"""
        # Simulate realistic quality changes
        degradation_factors = {
            'code_coverage': random.uniform(-2.0, -0.5),
            'cyclomatic_complexity': random.uniform(0.2, 0.8),
            'maintainability_index': random.uniform(-3.0, -1.0),
            'technical_debt_ratio': random.uniform(0.01, 0.03),
            'test_quality_score': random.uniform(-2.5, -0.5),
            'security_score': random.uniform(-1.5, -0.3)
        }
        
        new_metrics = QualityMetricsSnapshot(
            project_id=DEMO_PROJECT_ID,
            timestamp=datetime.now(),
            code_coverage=max(0, current_metrics.code_coverage + degradation_factors['code_coverage']),
            cyclomatic_complexity=min(20, current_metrics.cyclomatic_complexity + degradation_factors['cyclomatic_complexity']),
            maintainability_index=max(0, current_metrics.maintainability_index + degradation_factors['maintainability_index']),
            technical_debt_ratio=min(1.0, current_metrics.technical_debt_ratio + degradation_factors['technical_debt_ratio']),
            test_quality_score=max(0, current_metrics.test_quality_score + degradation_factors['test_quality_score']),
            security_score=max(0, current_metrics.security_score + degradation_factors['security_score'])
        )
        
        return new_metrics
    
    async def create_alert_for_metrics(self, metrics: QualityMetricsSnapshot):
        """Create alerts based on current metrics"""
        alerts_created = []
        
        # Check each metric against thresholds
        metric_checks = [
            ("code_coverage", metrics.code_coverage, 70.0, 50.0),
            ("cyclomatic_complexity", metrics.cyclomatic_complexity, 10.0, 15.0),
            ("maintainability_index", metrics.maintainability_index, 60.0, 40.0),
            ("technical_debt_ratio", metrics.technical_debt_ratio, 0.3, 0.5),
            ("test_quality_score", metrics.test_quality_score, 70.0, 50.0),
            ("security_score", metrics.security_score, 80.0, 60.0)
        ]
        
        for metric_name, current_value, warning_threshold, critical_threshold in metric_checks:
            severity = None
            threshold_value = None
            
            # For metrics where lower is worse (except complexity and debt ratio)
            if metric_name in ["cyclomatic_complexity", "technical_debt_ratio"]:
                if current_value > critical_threshold:
                    severity = "critical"
                    threshold_value = critical_threshold
                elif current_value > warning_threshold:
                    severity = "warning"
                    threshold_value = warning_threshold
            else:
                if current_value < critical_threshold:
                    severity = "critical"
                    threshold_value = critical_threshold
                elif current_value < warning_threshold:
                    severity = "warning"
                    threshold_value = warning_threshold
            
            if severity:
                alert_data = {
                    "project_id": DEMO_PROJECT_ID,
                    "alert_type": "threshold_violation",
                    "severity": severity,
                    "metric_name": metric_name,
                    "current_value": current_value,
                    "threshold_value": threshold_value,
                    "message": f"{metric_name.replace('_', ' ').title()} is {current_value:.2f}, {'above' if metric_name in ['cyclomatic_complexity', 'technical_debt_ratio'] else 'below'} {severity} threshold of {threshold_value}",
                    "description": f"Quality alert generated during demo simulation"
                }
                
                try:
                    response = self.session.post(
                        f"{BASE_URL}/api/v1/quality-monitoring/alerts",
                        json=alert_data
                    )
                    if response.status_code == 200:
                        result = response.json()
                        alerts_created.append(result["alert_id"])
                        logger.warning(f"🚨 {severity.upper()} ALERT: {alert_data['message']}")
                except Exception as e:
                    logger.error(f"Failed to create alert: {e}")
        
        return alerts_created
    
    async def listen_for_updates(self):
        """Listen for real-time WebSocket updates"""
        if not self.websocket:
            return
        
        try:
            while self.demo_running:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=1.0
                    )
                    
                    data = json.loads(message)
                    if data.get("type") == "quality_update":
                        if data.get("alerts"):
                            logger.info(f"📡 Real-time update: {len(data['alerts'])} new alerts")
                        if data.get("metrics"):
                            logger.info(f"📊 Real-time metrics update for {len(data['metrics'])} projects")
                    
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error receiving WebSocket message: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {e}")
    
    async def run_quality_simulation(self):
        """Run the main quality simulation"""
        logger.info("🎬 Starting quality degradation simulation")
        
        # Generate initial metrics
        current_metrics = self.generate_initial_metrics()
        self.metrics_history.append(current_metrics)
        
        logger.info(f"📊 Initial Quality Metrics for {DEMO_PROJECT_ID}:")
        logger.info(f"   Code Coverage: {current_metrics.code_coverage:.1f}%")
        logger.info(f"   Cyclomatic Complexity: {current_metrics.cyclomatic_complexity:.1f}")
        logger.info(f"   Maintainability Index: {current_metrics.maintainability_index:.1f}")
        logger.info(f"   Technical Debt Ratio: {current_metrics.technical_debt_ratio:.2f}")
        logger.info(f"   Test Quality Score: {current_metrics.test_quality_score:.1f}%")
        logger.info(f"   Security Score: {current_metrics.security_score:.1f}%")
        
        simulation_steps = 15
        step_delay = 3  # seconds between steps
        
        for step in range(1, simulation_steps + 1):
            if not self.demo_running:
                break
                
            logger.info(f"\n⏱️  Simulation Step {step}/{simulation_steps}")
            
            # Simulate quality degradation
            current_metrics = self.simulate_quality_degradation(current_metrics)
            self.metrics_history.append(current_metrics)
            
            # Log current metrics
            logger.info(f"📊 Updated Quality Metrics:")
            logger.info(f"   Code Coverage: {current_metrics.code_coverage:.1f}% (Δ{current_metrics.code_coverage - self.metrics_history[-2].code_coverage:+.1f})")
            logger.info(f"   Cyclomatic Complexity: {current_metrics.cyclomatic_complexity:.1f} (Δ{current_metrics.cyclomatic_complexity - self.metrics_history[-2].cyclomatic_complexity:+.1f})")
            logger.info(f"   Maintainability Index: {current_metrics.maintainability_index:.1f} (Δ{current_metrics.maintainability_index - self.metrics_history[-2].maintainability_index:+.1f})")
            logger.info(f"   Technical Debt Ratio: {current_metrics.technical_debt_ratio:.2f} (Δ{current_metrics.technical_debt_ratio - self.metrics_history[-2].technical_debt_ratio:+.2f})")
            logger.info(f"   Test Quality Score: {current_metrics.test_quality_score:.1f}% (Δ{current_metrics.test_quality_score - self.metrics_history[-2].test_quality_score:+.1f})")
            logger.info(f"   Security Score: {current_metrics.security_score:.1f}% (Δ{current_metrics.security_score - self.metrics_history[-2].security_score:+.1f})")
            
            # Check for alerts
            alerts = await self.create_alert_for_metrics(current_metrics)
            if alerts:
                logger.info(f"🚨 Generated {len(alerts)} alerts")
            
            # Wait before next step
            await asyncio.sleep(step_delay)
        
        logger.info("\n🏁 Quality simulation completed")
    
    async def show_final_summary(self):
        """Show final demo summary"""
        logger.info("\n📋 Demo Summary")
        logger.info("=" * 50)
        
        # Get final monitoring status
        response = self.session.get(f"{BASE_URL}/api/v1/quality-monitoring/status")
        if response.status_code == 200:
            status = response.json()
            logger.info(f"Monitoring Status: {'Active' if status['active'] else 'Inactive'}")
            logger.info(f"Connected Clients: {status['connected_clients']}")
        
        # Get alert history
        response = self.session.get(
            f"{BASE_URL}/api/v1/quality-monitoring/alerts",
            params={"project_id": DEMO_PROJECT_ID, "hours": 1}
        )
        if response.status_code == 200:
            alerts_data = response.json()
            total_alerts = alerts_data["total_count"]
            
            logger.info(f"Total Alerts Generated: {total_alerts}")
            
            # Count by severity
            severity_counts = {"critical": 0, "warning": 0, "info": 0}
            for alert in alerts_data["alerts"]:
                severity_counts[alert["severity"]] += 1
            
            logger.info(f"  Critical: {severity_counts['critical']}")
            logger.info(f"  Warning: {severity_counts['warning']}")
            logger.info(f"  Info: {severity_counts['info']}")
        
        # Show metrics progression
        if len(self.metrics_history) >= 2:
            initial = self.metrics_history[0]
            final = self.metrics_history[-1]
            
            logger.info("\nQuality Metrics Changes:")
            logger.info(f"  Code Coverage: {initial.code_coverage:.1f}% → {final.code_coverage:.1f}% ({final.code_coverage - initial.code_coverage:+.1f}%)")
            logger.info(f"  Cyclomatic Complexity: {initial.cyclomatic_complexity:.1f} → {final.cyclomatic_complexity:.1f} ({final.cyclomatic_complexity - initial.cyclomatic_complexity:+.1f})")
            logger.info(f"  Maintainability Index: {initial.maintainability_index:.1f} → {final.maintainability_index:.1f} ({final.maintainability_index - initial.maintainability_index:+.1f})")
            logger.info(f"  Technical Debt Ratio: {initial.technical_debt_ratio:.2f} → {final.technical_debt_ratio:.2f} ({final.technical_debt_ratio - initial.technical_debt_ratio:+.2f})")
            logger.info(f"  Test Quality Score: {initial.test_quality_score:.1f}% → {final.test_quality_score:.1f}% ({final.test_quality_score - initial.test_quality_score:+.1f}%)")
            logger.info(f"  Security Score: {initial.security_score:.1f}% → {final.security_score:.1f}% ({final.security_score - initial.security_score:+.1f}%)")
    
    async def cleanup_demo(self):
        """Clean up demo resources"""
        logger.info("\n🧹 Cleaning up demo resources")
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket connection closed")
        
        # Delete demo notification channel
        if hasattr(self, 'demo_channel_id') and self.demo_channel_id:
            try:
                response = self.session.delete(
                    f"{BASE_URL}/api/v1/quality-monitoring/notifications/channels/{self.demo_channel_id}"
                )
                if response.status_code == 200:
                    logger.info("Demo notification channel deleted")
            except Exception as e:
                logger.warning(f"Failed to delete demo notification channel: {e}")
        
        # Stop monitoring service
        try:
            response = self.session.post(f"{BASE_URL}/api/v1/quality-monitoring/stop")
            if response.status_code == 200:
                logger.info("Monitoring service stopped")
        except Exception as e:
            logger.warning(f"Failed to stop monitoring service: {e}")
    
    async def run_demo(self):
        """Run the complete demo"""
        logger.info("🎯 Quality Monitoring Real-time Demo Starting")
        logger.info("=" * 60)
        
        try:
            # Setup
            if not await self.setup_demo():
                logger.error("❌ Demo setup failed")
                return False
            
            # Connect WebSocket
            if not await self.connect_websocket():
                logger.error("❌ WebSocket connection failed")
                return False
            
            self.demo_running = True
            
            # Start WebSocket listener
            websocket_task = asyncio.create_task(self.listen_for_updates())
            
            # Run simulation
            await self.run_quality_simulation()
            
            # Stop WebSocket listener
            self.demo_running = False
            await websocket_task
            
            # Show summary
            await self.show_final_summary()
            
            logger.info("\n✅ Demo completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            return False
        finally:
            self.demo_running = False
            await self.cleanup_demo()


async def main():
    """Main demo runner"""
    demo = QualityMonitoringDemo()
    
    try:
        success = await demo.run_demo()
        if success:
            print("\n🎉 Quality Monitoring Demo completed successfully!")
            print("\nKey Features Demonstrated:")
            print("✅ Real-time quality monitoring")
            print("✅ Automatic alert generation")
            print("✅ WebSocket-based live updates")
            print("✅ Configurable thresholds")
            print("✅ Notification channels")
            print("✅ Alert management")
        else:
            print("\n❌ Demo failed - check logs for details")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Demo crashed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)