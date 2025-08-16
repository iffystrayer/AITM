"""
Quality Reports Demo

Demonstrates the comprehensive quality reporting and analytics system capabilities.
"""

import asyncio
import json
import tempfile
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from app.services.quality_report_generator import (
    QualityReportGenerator, ReportConfiguration, ReportType, ReportFormat
)
from app.models.quality import (
    QualityMetrics, QualityIssue, QualityTrend, AutoFixResult,
    IssueType, Severity, IssueStatus, FixType
)


class QualityReportsDemo:
    """Demo class for quality reports system."""
    
    def __init__(self):
        self.temp_db = None
        self.generator = None
        self.demo_projects = {
            "ecommerce_platform": "E-commerce Platform",
            "mobile_app_backend": "Mobile App Backend", 
            "data_analytics_service": "Data Analytics Service",
            "user_management_api": "User Management API"
        }
    
    async def setup_demo_environment(self):
        """Set up demo environment with realistic data."""
        print("🔧 Setting up Quality Reports Demo Environment...")
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            self.temp_db = f.name
        
        self.generator = QualityReportGenerator(self.temp_db)
        
        # Create realistic demo data
        await self._create_demo_data()
        
        print("✅ Demo environment ready!")
        print(f"   Database: {self.temp_db}")
        print(f"   Projects: {len(self.demo_projects)}")
        print()
    
    async def _create_demo_data(self):
        """Create realistic demo data for quality reports."""
        import sqlite3
        
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        try:
            # Create quality metrics with realistic trends
            project_configs = {
                "ecommerce_platform": {
                    "base_coverage": 85,
                    "coverage_trend": 0.2,  # Improving
                    "base_complexity": 12,
                    "complexity_trend": -0.1,  # Improving
                    "base_debt": 0.25,
                    "debt_trend": -0.005,  # Improving
                    "base_security": 88,
                    "security_trend": 0.3,  # Improving
                    "issue_count": 25
                },
                "mobile_app_backend": {
                    "base_coverage": 78,
                    "coverage_trend": -0.1,  # Declining
                    "base_complexity": 15,
                    "complexity_trend": 0.15,  # Getting worse
                    "base_debt": 0.18,
                    "debt_trend": 0.003,  # Getting worse
                    "base_security": 82,
                    "security_trend": -0.2,  # Declining
                    "issue_count": 35
                },
                "data_analytics_service": {
                    "base_coverage": 92,
                    "coverage_trend": 0.05,  # Stable/slight improvement
                    "base_complexity": 8,
                    "complexity_trend": 0.02,  # Stable
                    "base_debt": 0.12,
                    "debt_trend": -0.001,  # Stable
                    "base_security": 95,
                    "security_trend": 0.1,  # Stable/improving
                    "issue_count": 12
                },
                "user_management_api": {
                    "base_coverage": 70,
                    "coverage_trend": 0.4,  # Rapidly improving
                    "base_complexity": 18,
                    "complexity_trend": -0.2,  # Improving
                    "base_debt": 0.35,
                    "debt_trend": -0.008,  # Improving
                    "base_security": 75,
                    "security_trend": 0.5,  # Rapidly improving
                    "issue_count": 45
                }
            }
            
            # Generate 60 days of historical data
            base_time = datetime.now(timezone.utc) - timedelta(days=60)
            
            for project_id, config in project_configs.items():
                for day in range(0, 60, 2):  # Every 2 days
                    timestamp = base_time + timedelta(days=day)
                    
                    # Calculate trending values
                    coverage = max(0, min(100, config["base_coverage"] + (day * config["coverage_trend"])))
                    complexity = max(1, config["base_complexity"] + (day * config["complexity_trend"]))
                    debt_ratio = max(0, min(1, config["base_debt"] + (day * config["debt_trend"])))
                    security_score = max(0, min(100, config["base_security"] + (day * config["security_trend"])))
                    
                    # Add some realistic noise
                    import random
                    coverage += random.uniform(-2, 2)
                    complexity += random.uniform(-0.5, 0.5)
                    debt_ratio += random.uniform(-0.01, 0.01)
                    security_score += random.uniform(-1, 1)
                    
                    # Ensure bounds
                    coverage = max(0, min(100, coverage))
                    complexity = max(1, complexity)
                    debt_ratio = max(0, min(1, debt_ratio))
                    security_score = max(0, min(100, security_score))
                    
                    # Calculate derived metrics
                    maintainability = 100 - (complexity * 3) - (debt_ratio * 50)
                    maintainability = max(0, min(100, maintainability))
                    
                    test_quality = coverage * 0.8 + random.uniform(5, 15)
                    test_quality = max(0, min(100, test_quality))
                    
                    performance_score = 85 + random.uniform(-10, 10)
                    performance_score = max(0, min(100, performance_score))
                    
                    lines_of_code = 8000 + hash(project_id) % 5000 + day * 10
                    duplicate_ratio = max(0, min(0.3, debt_ratio * 0.5 + random.uniform(-0.02, 0.02)))
                    comment_ratio = max(0, min(0.4, 0.15 + random.uniform(-0.05, 0.05)))
                    
                    metrics = QualityMetrics(
                        project_id=project_id,
                        timestamp=timestamp,
                        code_coverage=coverage,
                        cyclomatic_complexity=complexity,
                        maintainability_index=maintainability,
                        technical_debt_ratio=debt_ratio,
                        test_quality_score=test_quality,
                        security_score=security_score,
                        performance_score=performance_score,
                        lines_of_code=int(lines_of_code),
                        duplicate_code_ratio=duplicate_ratio,
                        comment_ratio=comment_ratio
                    )
                    
                    cursor.execute("""
                        INSERT INTO quality_metrics 
                        (id, project_id, timestamp, code_coverage, cyclomatic_complexity,
                         maintainability_index, technical_debt_ratio, test_quality_score,
                         security_score, performance_score, lines_of_code, 
                         duplicate_code_ratio, comment_ratio)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        metrics.id, metrics.project_id, metrics.timestamp.isoformat(),
                        metrics.code_coverage, metrics.cyclomatic_complexity,
                        metrics.maintainability_index, metrics.technical_debt_ratio,
                        metrics.test_quality_score, metrics.security_score,
                        metrics.performance_score, metrics.lines_of_code,
                        metrics.duplicate_code_ratio, metrics.comment_ratio
                    ))
            
            # Create realistic quality issues
            issue_templates = [
                ("SQL injection vulnerability in user input", IssueType.SECURITY, Severity.CRITICAL),
                ("Unused import statement", IssueType.STYLE, Severity.LOW),
                ("Function exceeds complexity threshold", IssueType.COMPLEXITY, Severity.MEDIUM),
                ("Missing test coverage for critical path", IssueType.TESTING, Severity.HIGH),
                ("Hardcoded credentials detected", IssueType.SECURITY, Severity.CRITICAL),
                ("Line length exceeds 120 characters", IssueType.STYLE, Severity.LOW),
                ("Duplicate code block detected", IssueType.MAINTAINABILITY, Severity.MEDIUM),
                ("Missing error handling", IssueType.PERFORMANCE, Severity.MEDIUM),
                ("Deprecated API usage", IssueType.MAINTAINABILITY, Severity.HIGH),
                ("Missing documentation", IssueType.DOCUMENTATION, Severity.LOW)
            ]
            
            for project_id, config in project_configs.items():
                issue_count = config["issue_count"]
                
                for i in range(issue_count):
                    template = issue_templates[i % len(issue_templates)]
                    description, issue_type, severity = template
                    
                    # Vary the description
                    description = f"{description} in {project_id.replace('_', ' ')}"
                    
                    # Some issues are resolved
                    is_resolved = i % 4 == 0  # 25% resolved
                    created_days_ago = i % 30 + 1
                    
                    issue = QualityIssue(
                        project_id=project_id,
                        file_path=f"src/{['models', 'services', 'controllers', 'utils', 'tests'][i % 5]}/{['main', 'auth', 'data', 'api', 'helper'][i % 5]}.py",
                        line_number=50 + (i * 7) % 200,
                        issue_type=issue_type,
                        severity=severity,
                        category=issue_type.value,
                        description=description,
                        auto_fixable=(issue_type in [IssueType.STYLE, IssueType.DOCUMENTATION] and severity in [Severity.LOW, Severity.MEDIUM]),
                        status=IssueStatus.RESOLVED if is_resolved else IssueStatus.OPEN,
                        created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago),
                        resolved_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago-2) if is_resolved else None,
                        resolved_by="developer" if is_resolved else None,
                        resolution_method="manual_fix" if is_resolved else None
                    )
                    
                    cursor.execute("""
                        INSERT INTO quality_issues 
                        (id, project_id, file_path, line_number, column_number, issue_type,
                         severity, category, description, suggested_fix, auto_fixable,
                         status, created_at, resolved_at, resolved_by, resolution_method)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        issue.id, issue.project_id, issue.file_path, issue.line_number,
                        issue.column_number, issue.issue_type.value, issue.severity.value,
                        issue.category, issue.description, issue.suggested_fix,
                        issue.auto_fixable, issue.status.value, issue.created_at.isoformat(),
                        issue.resolved_at.isoformat() if issue.resolved_at else None,
                        issue.resolved_by, issue.resolution_method
                    ))
            
            # Create auto-fix results
            for project_id in project_configs.keys():
                for i in range(8):  # 8 auto-fix attempts per project
                    fix_result = AutoFixResult(
                        project_id=project_id,
                        file_path=f"src/module_{i}.py",
                        fix_type=[FixType.FORMATTING, FixType.IMPORTS, FixType.STYLE][i % 3],
                        success=(i % 5 != 0),  # 80% success rate
                        applied_at=datetime.now(timezone.utc) - timedelta(days=i*2),
                        applied_by="auto_fix_system",
                        error_message="Syntax error prevented fix" if i % 5 == 0 else None
                    )
                    
                    cursor.execute("""
                        INSERT INTO auto_fix_results 
                        (id, issue_id, project_id, file_path, fix_type, original_content,
                         fixed_content, success, error_message, applied_at, applied_by,
                         rollback_id, is_rolled_back)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        fix_result.id, fix_result.issue_id, fix_result.project_id,
                        fix_result.file_path, fix_result.fix_type.value,
                        fix_result.original_content, fix_result.fixed_content,
                        fix_result.success, fix_result.error_message,
                        fix_result.applied_at.isoformat(), fix_result.applied_by,
                        fix_result.rollback_id, fix_result.is_rolled_back
                    ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    async def demo_executive_summary(self):
        """Demonstrate executive summary generation."""
        print("📊 EXECUTIVE SUMMARY DEMO")
        print("=" * 50)
        
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=list(self.demo_projects.keys()),
            executive_level=True
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        summary = report['content']['executive_summary']
        
        print(f"🎯 Overall Portfolio Health: {summary['overall_health_score']:.1f}/100 (Grade: {summary['quality_grade']})")
        print(f"🚨 Critical Issues: {summary['critical_issues']}")
        print(f"📈 Improvement Trend: {summary['improvement_trend'].title()}")
        print(f"⚠️  Risk Assessment: {summary['risk_assessment'].title()}")
        print(f"💰 Investment Priority: {summary['investment_priority'].title()}")
        
        print("\n🎯 Key Recommendations:")
        for i, rec in enumerate(summary['recommendations'][:5], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n📋 Detailed Project Breakdown:")
        for project in report['content']['detailed_projects']:
            print(f"   • {project['project_name']}: {project['health_score']:.1f}/100 ({project['critical_issues']} critical issues)")
        
        print()
        return report
    
    async def demo_trend_analysis(self):
        """Demonstrate trend analysis generation."""
        print("📈 TREND ANALYSIS DEMO")
        print("=" * 50)
        
        config = ReportConfiguration(
            report_type=ReportType.TREND_ANALYSIS,
            format=ReportFormat.JSON,
            project_ids=list(self.demo_projects.keys()),
            date_range=(
                datetime.now(timezone.utc) - timedelta(days=30),
                datetime.now(timezone.utc)
            )
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        content = report['content']
        
        print(f"📊 Overall Portfolio Trend: {content['overall_trend'].title()}")
        print(f"📅 Analysis Period: {content['analysis_period']}")
        print(f"🏗️  Projects Analyzed: {content['project_count']}")
        
        print("\n📈 Metric Trends:")
        for metric_name, analysis in content['trend_analysis'].items():
            direction_emoji = {"up": "📈", "down": "📉", "stable": "➡️"}.get(analysis['trend_direction'], "❓")
            print(f"   {direction_emoji} {metric_name.replace('_', ' ').title()}: {analysis['trend_direction']} ({analysis['change_rate']:+.1f}%)")
            if analysis.get('confidence_level', 0) > 0.7:
                print(f"      Confidence: {analysis['confidence_level']:.1%} | Prediction: {analysis.get('prediction', 'N/A')}")
        
        if 'insights' in content:
            print("\n💡 Key Insights:")
            for insight in content['insights']:
                print(f"   • {insight}")
        
        print()
        return report
    
    async def demo_comparative_analysis(self):
        """Demonstrate comparative analysis generation."""
        print("🔍 COMPARATIVE ANALYSIS DEMO")
        print("=" * 50)
        
        config = ReportConfiguration(
            report_type=ReportType.COMPARATIVE,
            format=ReportFormat.JSON,
            project_ids=list(self.demo_projects.keys())
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        analysis = report['content']['comparative_analysis']
        
        baseline_name = self.demo_projects[analysis['baseline_project']]
        print(f"📊 Baseline Project: {baseline_name}")
        print(f"🔄 Comparing {len(analysis['comparison_projects'])} other projects")
        
        print("\n🏆 Performance Rankings:")
        key_metrics = ['code_coverage', 'security_score', 'maintainability_index']
        for metric in key_metrics:
            if metric in analysis['performance_rankings']:
                ranking = analysis['performance_rankings'][metric]
                print(f"   {metric.replace('_', ' ').title()}:")
                for i, project_id in enumerate(ranking[:3], 1):  # Top 3
                    project_name = self.demo_projects[project_id]
                    medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
                    print(f"      {medal} {project_name}")
        
        print("\n✨ Best Practices Identified:")
        for practice in analysis['best_practices']:
            print(f"   • {practice}")
        
        print("\n🎯 Improvement Opportunities:")
        for opportunity in analysis['improvement_opportunities']:
            print(f"   • {opportunity}")
        
        if 'summary' in report['content']:
            summary = report['content']['summary']
            if 'top_performer' in summary:
                top_performer = self.demo_projects[summary['top_performer']['project_id']]
                print(f"\n🏆 Top Performer: {top_performer} ({summary['top_performer']['health_score']:.1f}/100)")
        
        print()
        return report
    
    async def demo_project_health(self):
        """Demonstrate project health analysis."""
        print("🏥 PROJECT HEALTH ANALYSIS DEMO")
        print("=" * 50)
        
        config = ReportConfiguration(
            report_type=ReportType.PROJECT_HEALTH,
            format=ReportFormat.JSON,
            project_ids=list(self.demo_projects.keys())
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        health_data = report['content']['project_health']
        portfolio = report['content']['portfolio_health']
        
        print(f"🏢 Portfolio Overview:")
        print(f"   Overall Health: {portfolio['overall_score']:.1f}/100")
        print(f"   Healthy Projects: {portfolio['healthy_projects']}/{portfolio['project_count']}")
        print(f"   At-Risk Projects: {portfolio['at_risk_projects']}")
        
        print(f"\n📋 Individual Project Health:")
        
        # Sort projects by health score
        sorted_projects = sorted(
            health_data.items(),
            key=lambda x: x[1]['health_score'],
            reverse=True
        )
        
        for project_id, data in sorted_projects:
            project_name = self.demo_projects[project_id]
            status_emoji = {
                'excellent': '🟢',
                'good': '🟡', 
                'fair': '🟠',
                'poor': '🔴',
                'critical': '🚨'
            }.get(data['health_status'], '❓')
            
            print(f"   {status_emoji} {project_name}: {data['health_score']:.1f}/100 ({data['health_status']})")
            print(f"      Issues: {data['issue_count']} total, {data['critical_issues']} critical")
            
            if data['risk_factors']:
                print(f"      Risk Factors: {', '.join(data['risk_factors'])}")
        
        print(f"\n💡 Health Recommendations:")
        for rec in report['content']['recommendations']:
            print(f"   • {rec}")
        
        print()
        return report
    
    async def demo_technical_debt(self):
        """Demonstrate technical debt analysis."""
        print("💳 TECHNICAL DEBT ANALYSIS DEMO")
        print("=" * 50)
        
        config = ReportConfiguration(
            report_type=ReportType.TECHNICAL_DEBT,
            format=ReportFormat.JSON,
            project_ids=list(self.demo_projects.keys())
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        debt_data = report['content']['technical_debt_analysis']
        portfolio = report['content']['portfolio_summary']
        
        print(f"💰 Portfolio Debt Summary:")
        print(f"   Average Debt Ratio: {portfolio['average_debt_ratio']:.1%}")
        print(f"   Total Estimated Hours: {portfolio['total_estimated_hours']:.0f}")
        print(f"   Estimated Cost: ${portfolio['estimated_cost']:,.0f}")
        print(f"   High-Debt Projects: {portfolio['projects_with_high_debt']}")
        
        print(f"\n📊 Project Debt Breakdown:")
        
        # Sort by priority score
        sorted_debt = sorted(
            debt_data.items(),
            key=lambda x: x[1]['priority_score'],
            reverse=True
        )
        
        for project_id, data in sorted_debt:
            project_name = self.demo_projects[project_id]
            level_emoji = {
                'low': '🟢',
                'moderate': '🟡',
                'high': '🟠', 
                'critical': '🔴'
            }.get(data['debt_level'], '❓')
            
            print(f"   {level_emoji} {project_name}:")
            print(f"      Debt Ratio: {data['debt_ratio']:.1%} ({data['debt_level']})")
            print(f"      Estimated Hours: {data['estimated_debt_hours']:.0f}")
            print(f"      Priority Score: {data['priority_score']:.1f}")
            
            if data['debt_sources']:
                print(f"      Sources: {', '.join(data['debt_sources'])}")
        
        print(f"\n🎯 Debt Reduction Priority:")
        for i, item in enumerate(report['content']['debt_reduction_priority'][:5], 1):
            project_name = self.demo_projects[item['project_id']]
            print(f"   {i}. {project_name} (Priority: {item['priority_score']:.1f})")
        
        print(f"\n💡 Debt Reduction Recommendations:")
        for rec in report['content']['recommendations']:
            print(f"   • {rec}")
        
        print()
        return report
    
    async def demo_multiple_formats(self):
        """Demonstrate report generation in multiple formats."""
        print("📄 MULTIPLE FORMATS DEMO")
        print("=" * 50)
        
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,  # Will be changed for each format
            project_ids=[list(self.demo_projects.keys())[0]]  # Single project for demo
        )
        
        formats = [
            (ReportFormat.JSON, "JSON"),
            (ReportFormat.CSV, "CSV"),
            (ReportFormat.HTML, "HTML"),
            (ReportFormat.MARKDOWN, "Markdown")
        ]
        
        for format_type, format_name in formats:
            print(f"\n📋 {format_name} Format Sample:")
            print("-" * 30)
            
            config.format = format_type
            report = await self.generator.generate_comprehensive_report(config)
            content = report['content']
            
            if format_type == ReportFormat.JSON:
                # Show formatted JSON snippet
                if isinstance(content, dict) and 'executive_summary' in content:
                    summary = content['executive_summary']
                    print(f"   Health Score: {summary.get('overall_health_score', 'N/A')}")
                    print(f"   Quality Grade: {summary.get('quality_grade', 'N/A')}")
                    print(f"   Critical Issues: {summary.get('critical_issues', 'N/A')}")
                else:
                    print("   JSON content generated successfully")
            
            elif format_type == ReportFormat.CSV:
                # Show CSV snippet
                if isinstance(content, str):
                    lines = content.split('\n')[:5]  # First 5 lines
                    for line in lines:
                        if line.strip():
                            print(f"   {line}")
                    if len(content.split('\n')) > 5:
                        print("   ...")
            
            elif format_type == ReportFormat.HTML:
                # Show HTML snippet
                if isinstance(content, str):
                    if "Quality Report" in content:
                        print("   ✅ HTML document with proper structure generated")
                        print("   Contains: DOCTYPE, head, body, styling")
                    else:
                        print("   HTML content generated")
            
            elif format_type == ReportFormat.MARKDOWN:
                # Show Markdown snippet
                if isinstance(content, str):
                    lines = content.split('\n')[:10]  # First 10 lines
                    for line in lines:
                        if line.strip():
                            print(f"   {line}")
                    if len(content.split('\n')) > 10:
                        print("   ...")
        
        print()
    
    async def demo_comprehensive_report(self):
        """Demonstrate comprehensive report with all sections."""
        print("📚 COMPREHENSIVE REPORT DEMO")
        print("=" * 50)
        
        config = ReportConfiguration(
            report_type=ReportType.COMPREHENSIVE,
            format=ReportFormat.JSON,
            project_ids=list(self.demo_projects.keys()),
            include_trends=True,
            include_comparisons=True,
            include_recommendations=True
        )
        
        print("🔄 Generating comprehensive report...")
        report = await self.generator.generate_comprehensive_report(config)
        
        comprehensive = report['content']['comprehensive_report']
        metadata = report['content']['report_metadata']
        
        print(f"✅ Report Generated Successfully!")
        print(f"   Report ID: {report['report_id']}")
        print(f"   Generated: {metadata['generated_at']}")
        print(f"   Projects: {metadata['project_count']}")
        print(f"   Period: {metadata['report_period']}")
        
        print(f"\n📋 Report Sections Included:")
        sections = [
            ('executive_summary', 'Executive Summary'),
            ('trend_analysis', 'Trend Analysis'),
            ('comparative_analysis', 'Comparative Analysis'),
            ('issue_summary', 'Issue Summary'),
            ('project_health', 'Project Health'),
            ('technical_debt', 'Technical Debt')
        ]
        
        for section_key, section_name in sections:
            if section_key in comprehensive:
                print(f"   ✅ {section_name}")
                
                # Show key metrics from each section
                section_data = comprehensive[section_key]
                
                if section_key == 'executive_summary':
                    print(f"      Health Score: {section_data.get('overall_health_score', 'N/A')}")
                elif section_key == 'trend_analysis':
                    print(f"      Overall Trend: {section_data.get('overall_trend', 'N/A')}")
                elif section_key == 'comparative_analysis':
                    baseline = section_data.get('baseline_project', 'N/A')
                    if baseline in self.demo_projects:
                        baseline = self.demo_projects[baseline]
                    print(f"      Baseline: {baseline}")
                elif section_key == 'issue_summary':
                    total_issues = section_data.get('total_issues', 'N/A')
                    print(f"      Total Issues: {total_issues}")
                elif section_key == 'project_health':
                    portfolio = section_data.get('portfolio_health', {})
                    print(f"      Portfolio Health: {portfolio.get('overall_score', 'N/A')}")
                elif section_key == 'technical_debt':
                    portfolio = section_data.get('portfolio_summary', {})
                    print(f"      Avg Debt Ratio: {portfolio.get('average_debt_ratio', 'N/A')}")
            else:
                print(f"   ❌ {section_name} (not included)")
        
        print()
        return report
    
    async def cleanup_demo_environment(self):
        """Clean up demo environment."""
        if self.temp_db and os.path.exists(self.temp_db):
            os.unlink(self.temp_db)
        print("🧹 Demo environment cleaned up")
    
    async def run_full_demo(self):
        """Run the complete quality reports demo."""
        print("🚀 QUALITY REPORTS SYSTEM DEMO")
        print("=" * 60)
        print("Demonstrating comprehensive quality reporting and analytics capabilities")
        print("=" * 60)
        
        try:
            await self.setup_demo_environment()
            
            # Run all demo sections
            demos = [
                ("Executive Summary", self.demo_executive_summary),
                ("Trend Analysis", self.demo_trend_analysis),
                ("Comparative Analysis", self.demo_comparative_analysis),
                ("Project Health", self.demo_project_health),
                ("Technical Debt", self.demo_technical_debt),
                ("Multiple Formats", self.demo_multiple_formats),
                ("Comprehensive Report", self.demo_comprehensive_report)
            ]
            
            for demo_name, demo_func in demos:
                try:
                    print(f"\n{'='*20} {demo_name.upper()} {'='*20}")
                    await demo_func()
                    print(f"✅ {demo_name} demo completed successfully")
                except Exception as e:
                    print(f"❌ {demo_name} demo failed: {e}")
            
            print("\n" + "=" * 60)
            print("🎉 QUALITY REPORTS DEMO COMPLETED!")
            print("=" * 60)
            print("\nKey Features Demonstrated:")
            print("• Executive-level quality summaries with grades and recommendations")
            print("• Trend analysis with predictions and confidence levels")
            print("• Comparative analysis across projects with rankings")
            print("• Project health assessment with risk factors")
            print("• Technical debt analysis with cost estimates")
            print("• Multiple export formats (JSON, CSV, HTML, Markdown)")
            print("• Comprehensive reports combining all analysis types")
            print("\nThe system provides actionable insights for:")
            print("• Development teams to improve code quality")
            print("• Project managers to track progress and risks")
            print("• Executives to make informed investment decisions")
            print("• Quality engineers to identify improvement opportunities")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
        finally:
            await self.cleanup_demo_environment()


async def main():
    """Run the quality reports demo."""
    demo = QualityReportsDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())