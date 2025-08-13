#!/usr/bin/env python3
"""
Monitoring and Observability Setup Validation Script

This script validates the monitoring and observability configuration for the AITM system,
including health check endpoints, metrics collection, log aggregation, and alerting setup.
"""

import os
import sys
import json
import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringValidator:
    """Comprehensive monitoring and observability validator"""
    
    def __init__(self, base_url: str = "http://localhost", backend_port: int = 38527):
        self.base_url = base_url
        self.backend_port = backend_port
        self.validation_results = {}
        self.issues = []
        self.warnings = []
        
    async def validate_health_endpoints(self) -> Dict[str, str]:
        """Validate health check endpoints"""
        results = {}
        
        health_endpoints = [
            ("/api/v1/health", "Basic health check"),
            ("/api/v1/health/detailed", "Detailed health check"),
            ("/health", "Root health check")
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in health_endpoints:
                try:
                    url = f"{self.base_url}:{self.backend_port}{endpoint}"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'status' in data and data['status'] in ['healthy', 'degraded']:
                                results[endpoint] = f"✅ {description} - {data['status']}"
                            else:
                                results[endpoint] = f"⚠️ {description} - Invalid response format"
                                self.warnings.append(f"Health endpoint {endpoint} has invalid response format")
                        else:
                            results[endpoint] = f"❌ {description} - HTTP {response.status}"
                            self.issues.append(f"Health endpoint {endpoint} returned HTTP {response.status}")
                            
                except asyncio.TimeoutError:
                    results[endpoint] = f"❌ {description} - Timeout"
                    self.issues.append(f"Health endpoint {endpoint} timed out")
                except Exception as e:
                    results[endpoint] = f"❌ {description} - {str(e)}"
                    self.issues.append(f"Health endpoint {endpoint} failed: {str(e)}")
        
        return results
    
    def validate_docker_monitoring_config(self) -> Dict[str, str]:
        """Validate Docker monitoring configuration"""
        results = {}
        
        # Check if docker-compose.prod.yml exists and has monitoring services
        docker_compose_file = "docker-compose.prod.yml"
        if not os.path.exists(docker_compose_file):
            self.issues.append(f"Docker compose file {docker_compose_file} not found")
            results['docker_compose'] = "❌ Not found"
            return results
        
        try:
            with open(docker_compose_file, 'r') as f:
                content = f.read()
            
            # Check for monitoring services
            monitoring_services = [
                ('prometheus', 'Prometheus metrics collection'),
                ('grafana', 'Grafana dashboards'),
                ('loki', 'Log aggregation'),
                ('promtail', 'Log collection')
            ]
            
            for service, description in monitoring_services:
                if service in content:
                    results[service] = f"✅ {description} configured"
                else:
                    results[service] = f"⚠️ {description} not configured"
                    self.warnings.append(f"{description} service not found in Docker compose")
            
            # Check for health checks
            if 'healthcheck:' in content:
                results['health_checks'] = "✅ Container health checks configured"
            else:
                results['health_checks'] = "⚠️ Container health checks not configured"
                self.warnings.append("Container health checks not configured")
            
            # Check for resource limits
            if 'deploy:' in content and 'resources:' in content:
                results['resource_limits'] = "✅ Resource limits configured"
            else:
                results['resource_limits'] = "⚠️ Resource limits not configured"
                self.warnings.append("Container resource limits not configured")
                
        except Exception as e:
            self.issues.append(f"Failed to parse Docker compose file: {str(e)}")
            results['docker_compose'] = f"❌ Parse error: {str(e)}"
        
        return results
    
    async def validate_prometheus_metrics(self) -> Dict[str, str]:
        """Validate Prometheus metrics endpoint"""
        results = {}
        
        prometheus_endpoints = [
            (9090, "/metrics", "Prometheus metrics"),
            (self.backend_port, "/metrics", "Application metrics")
        ]
        
        async with aiohttp.ClientSession() as session:
            for port, endpoint, description in prometheus_endpoints:
                try:
                    url = f"{self.base_url}:{port}{endpoint}"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            if 'HELP' in content or 'TYPE' in content:
                                results[f"port_{port}"] = f"✅ {description} available"
                            else:
                                results[f"port_{port}"] = f"⚠️ {description} - Invalid format"
                                self.warnings.append(f"Metrics at port {port} have invalid format")
                        else:
                            results[f"port_{port}"] = f"❌ {description} - HTTP {response.status}"
                            self.issues.append(f"Metrics endpoint at port {port} returned HTTP {response.status}")
                            
                except Exception as e:
                    results[f"port_{port}"] = f"❌ {description} - {str(e)}"
                    # Don't treat as critical issue since services might not be running
                    self.warnings.append(f"Metrics endpoint at port {port} not accessible: {str(e)}")
        
        return results
    
    async def validate_grafana_setup(self) -> Dict[str, str]:
        """Validate Grafana dashboard setup"""
        results = {}
        
        # Check Grafana accessibility
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}:3000/api/health"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        results['grafana_api'] = "✅ Grafana API accessible"
                    else:
                        results['grafana_api'] = f"❌ Grafana API - HTTP {response.status}"
                        self.warnings.append(f"Grafana API returned HTTP {response.status}")
        except Exception as e:
            results['grafana_api'] = f"❌ Grafana API - {str(e)}"
            self.warnings.append(f"Grafana API not accessible: {str(e)}")
        
        # Check for Grafana configuration files
        grafana_config_paths = [
            "monitoring/grafana",
            "./monitoring/grafana/provisioning",
            "grafana/provisioning"
        ]
        
        grafana_config_found = False
        for path in grafana_config_paths:
            if os.path.exists(path):
                grafana_config_found = True
                results['grafana_config'] = f"✅ Configuration found at {path}"
                break
        
        if not grafana_config_found:
            results['grafana_config'] = "⚠️ Configuration directory not found"
            self.warnings.append("Grafana configuration directory not found")
        
        return results
    
    def validate_log_aggregation_config(self) -> Dict[str, str]:
        """Validate log aggregation configuration"""
        results = {}
        
        # Check for log configuration files
        log_config_files = [
            ("monitoring/loki-config.yml", "Loki configuration"),
            ("monitoring/promtail-config.yml", "Promtail configuration"),
            ("monitoring/prometheus.yml", "Prometheus configuration")
        ]
        
        for file_path, description in log_config_files:
            if os.path.exists(file_path):
                results[file_path.replace('/', '_')] = f"✅ {description} found"
            else:
                results[file_path.replace('/', '_')] = f"⚠️ {description} not found"
                self.warnings.append(f"{description} file not found at {file_path}")
        
        # Check for log directories
        log_directories = [
            ("logs", "Application logs directory"),
            ("./logs", "Local logs directory"),
            ("backend/logs", "Backend logs directory")
        ]
        
        for dir_path, description in log_directories:
            if os.path.exists(dir_path):
                results[dir_path.replace('/', '_')] = f"✅ {description} exists"
            else:
                results[dir_path.replace('/', '_')] = f"⚠️ {description} not found"
                # Not critical, directories can be created automatically
        
        return results
    
    def validate_alerting_configuration(self) -> Dict[str, str]:
        """Validate alerting configuration"""
        results = {}
        
        # Check for alerting configuration files
        alert_config_files = [
            ("monitoring/alert-rules.yml", "Prometheus alert rules"),
            ("monitoring/alertmanager.yml", "Alertmanager configuration"),
            (".env.prod", "Environment configuration for alerts")
        ]
        
        for file_path, description in alert_config_files:
            if os.path.exists(file_path):
                results[file_path.replace('/', '_').replace('.', '_')] = f"✅ {description} found"
                
                # Check content for specific alerting configurations
                if file_path == ".env.prod":
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        alert_configs = [
                            ('SMTP_HOST', 'Email alerting'),
                            ('SENTRY_DSN', 'Error tracking'),
                            ('CPU_THRESHOLD', 'CPU monitoring'),
                            ('MEMORY_THRESHOLD', 'Memory monitoring')
                        ]
                        
                        for config, desc in alert_configs:
                            if config in content:
                                results[f"alert_{config.lower()}"] = f"✅ {desc} configured"
                            else:
                                results[f"alert_{config.lower()}"] = f"⚠️ {desc} not configured"
                                
                    except Exception as e:
                        results['env_parse'] = f"❌ Failed to parse .env.prod: {str(e)}"
            else:
                results[file_path.replace('/', '_').replace('.', '_')] = f"⚠️ {description} not found"
                if 'alert-rules' in file_path or 'alertmanager' in file_path:
                    self.warnings.append(f"{description} not configured")
        
        return results
    
    def validate_security_audit_logging(self) -> Dict[str, str]:
        """Validate security audit logging setup"""
        results = {}
        
        # Check if security audit logging is implemented in the code
        security_audit_file = "backend/app/core/security_audit.py"
        if os.path.exists(security_audit_file):
            results['security_audit_code'] = "✅ Security audit logging implemented"
            
            try:
                with open(security_audit_file, 'r') as f:
                    content = f.read()
                
                # Check for key security logging features
                security_features = [
                    ('SecurityEventType', 'Event type enumeration'),
                    ('log_authentication_success', 'Authentication logging'),
                    ('log_permission_denied', 'Authorization logging'),
                    ('log_project_access', 'Resource access logging'),
                    ('SecurityAuditFormatter', 'Structured logging format')
                ]
                
                for feature, description in security_features:
                    if feature in content:
                        results[f"audit_{feature.lower()}"] = f"✅ {description}"
                    else:
                        results[f"audit_{feature.lower()}"] = f"⚠️ {description} not found"
                        self.warnings.append(f"Security audit feature {description} not implemented")
                        
            except Exception as e:
                results['security_audit_parse'] = f"❌ Failed to parse security audit file: {str(e)}"
        else:
            results['security_audit_code'] = "❌ Security audit logging not implemented"
            self.issues.append("Security audit logging not implemented")
        
        return results
    
    def validate_performance_monitoring(self) -> Dict[str, str]:
        """Validate performance monitoring setup"""
        results = {}
        
        # Check for performance monitoring configuration
        perf_configs = [
            ('PROMETHEUS_ENABLED', 'Prometheus metrics'),
            ('LANGSMITH_TRACING', 'LLM tracing'),
            ('HEALTH_CHECK_INTERVAL', 'Health check frequency'),
            ('RESPONSE_TIME_THRESHOLD', 'Response time monitoring')
        ]
        
        env_file = ".env.prod.example"  # Use example file for validation
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                
                for config, description in perf_configs:
                    if config in content:
                        results[f"perf_{config.lower()}"] = f"✅ {description} configured"
                    else:
                        results[f"perf_{config.lower()}"] = f"⚠️ {description} not configured"
                        
            except Exception as e:
                results['perf_config_parse'] = f"❌ Failed to parse performance config: {str(e)}"
        else:
            results['perf_config_file'] = "⚠️ Performance configuration file not found"
        
        return results
    
    async def run_validation(self) -> Dict:
        """Run complete monitoring and observability validation"""
        logger.info("Starting monitoring and observability validation...")
        
        # Run all validation checks
        validation_results = {
            'health_endpoints': await self.validate_health_endpoints(),
            'docker_monitoring': self.validate_docker_monitoring_config(),
            'prometheus_metrics': await self.validate_prometheus_metrics(),
            'grafana_setup': await self.validate_grafana_setup(),
            'log_aggregation': self.validate_log_aggregation_config(),
            'alerting_config': self.validate_alerting_configuration(),
            'security_audit': self.validate_security_audit_logging(),
            'performance_monitoring': self.validate_performance_monitoring()
        }
        
        # Generate recommendations
        recommendations = self.generate_monitoring_recommendations()
        
        # Determine overall status
        if self.issues:
            status = 'ISSUES_FOUND'
        elif self.warnings:
            status = 'WARNINGS'
        else:
            status = 'PASSED'
        
        return {
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'validation_results': validation_results,
            'issues': self.issues,
            'warnings': self.warnings,
            'recommendations': recommendations,
            'summary': {
                'total_checks': sum(len(category) for category in validation_results.values()),
                'issues_count': len(self.issues),
                'warnings_count': len(self.warnings)
            }
        }
    
    def generate_monitoring_recommendations(self) -> List[str]:
        """Generate monitoring recommendations"""
        recommendations = []
        
        if self.issues:
            recommendations.append("🚨 ISSUES FOUND - REQUIRE ATTENTION:")
            for issue in self.issues:
                recommendations.append(f"   • {issue}")
            recommendations.append("")
        
        if self.warnings:
            recommendations.append("⚠️ WARNINGS - RECOMMENDED IMPROVEMENTS:")
            for warning in self.warnings:
                recommendations.append(f"   • {warning}")
            recommendations.append("")
        
        # Additional monitoring recommendations
        recommendations.extend([
            "📊 MONITORING BEST PRACTICES:",
            "   • Set up automated health check monitoring",
            "   • Configure alert escalation procedures",
            "   • Implement SLA/SLO monitoring",
            "   • Set up capacity planning dashboards",
            "   • Configure log retention policies",
            "   • Implement distributed tracing",
            "   • Set up synthetic monitoring",
            "   • Configure backup monitoring",
            "   • Implement security event correlation",
            "   • Set up performance baseline monitoring",
            ""
        ])
        
        return recommendations
    
    def print_validation_report(self, results: Dict):
        """Print formatted validation report"""
        print("\n" + "="*80)
        print("📊 MONITORING AND OBSERVABILITY VALIDATION REPORT")
        print("="*80)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Status: {results['status']}")
        print(f"Base URL: {self.base_url}:{self.backend_port}")
        print()
        
        # Print validation results by category
        for category, checks in results['validation_results'].items():
            print(f"📋 {category.replace('_', ' ').title()}:")
            for check, result in checks.items():
                print(f"   {check.replace('_', ' ').title()}: {result}")
            print()
        
        # Print summary
        summary = results['summary']
        print(f"📊 SUMMARY:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   Issues: {summary['issues_count']}")
        print(f"   Warnings: {summary['warnings_count']}")
        print()
        
        # Print recommendations
        if results['recommendations']:
            for recommendation in results['recommendations']:
                print(recommendation)
        
        print("="*80)

async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate monitoring and observability setup')
    parser.add_argument('--base-url', default='http://localhost', help='Base URL for health checks')
    parser.add_argument('--backend-port', type=int, default=38527, help='Backend port')
    parser.add_argument('--output', help='Output file for JSON results')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    validator = MonitoringValidator(args.base_url, args.backend_port)
    results = await validator.run_validation()
    
    if not args.quiet:
        validator.print_validation_report(results)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    # Exit with appropriate code
    if results['status'] == 'ISSUES_FOUND':
        sys.exit(1)
    elif results['status'] == 'WARNINGS':
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())