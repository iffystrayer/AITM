"""
Integration tests for Quality Reports API

Tests the complete quality reporting and analytics system integration.
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


class QualityReportsIntegrationTest:
    """Integration test suite for quality reports system."""
    
    def __init__(self):
        self.temp_db = None
        self.generator = None
        self.test_projects = ["project_alpha", "project_beta", "project_gamma"]
    
    async def setup(self):
        """Set up test environment."""
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            self.temp_db = f.name
        
        # Create database schema first
        await self._create_database_schema()
        
        self.generator = QualityReportGenerator(self.temp_db)
        
        # Seed test data
        await self._seed_test_data()
        
        print("✅ Test environment set up successfully")
    
    async def cleanup(self):
        """Clean up test environment."""
        if self.temp_db and os.path.exists(self.temp_db):
            os.unlink(self.temp_db)
        print("✅ Test environment cleaned up")
    
    async def _create_database_schema(self):
        """Create database schema for testing."""
        import sqlite3
        
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        try:
            # Create quality_metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    code_coverage REAL,
                    cyclomatic_complexity REAL,
                    maintainability_index REAL,
                    technical_debt_ratio REAL,
                    test_quality_score REAL,
                    security_score REAL,
                    performance_score REAL,
                    lines_of_code INTEGER,
                    duplicate_code_ratio REAL,
                    comment_ratio REAL
                )
            """)
            
            # Create quality_issues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_issues (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    column_number INTEGER,
                    issue_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    suggested_fix TEXT,
                    auto_fixable BOOLEAN DEFAULT FALSE,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolved_by TEXT,
                    resolution_method TEXT
                )
            """)
            
            # Create auto_fix_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auto_fix_results (
                    id TEXT PRIMARY KEY,
                    issue_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    fix_type TEXT NOT NULL,
                    original_content TEXT,
                    fixed_content TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied_by TEXT,
                    rollback_id TEXT,
                    is_rolled_back BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create quality_trends table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_trends (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trend_direction TEXT,
                    change_percentage REAL
                )
            """)
            
            # Create quality_reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_reports (
                    id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL,
                    format TEXT NOT NULL,
                    project_ids TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    generated_by TEXT,
                    report_data TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    expires_at TIMESTAMP
                )
            """)
            
            conn.commit()
            
        finally:
            conn.close()
    
    async def _seed_test_data(self):
        """Seed database with test data."""
        import sqlite3
        
        conn = sqlite3.connect(self.temp_db)
        cursor = conn.cursor()
        
        try:
            # Create test quality metrics
            for i, project_id in enumerate(self.test_projects):
                base_time = datetime.now(timezone.utc) - timedelta(days=30)
                
                # Create multiple metrics entries for trend analysis
                for day in range(0, 30, 5):  # Every 5 days
                    timestamp = base_time + timedelta(days=day)
                    
                    # Simulate improving metrics for project_alpha
                    if project_id == "project_alpha":
                        coverage = 70 + (day * 0.5)  # Improving coverage
                        complexity = 12 - (day * 0.1)  # Decreasing complexity
                        debt_ratio = 0.3 - (day * 0.005)  # Decreasing debt
                        security_score = 80 + (day * 0.3)  # Improving security
                    # Simulate declining metrics for project_beta
                    elif project_id == "project_beta":
                        coverage = 85 - (day * 0.3)  # Declining coverage
                        complexity = 8 + (day * 0.1)  # Increasing complexity
                        debt_ratio = 0.15 + (day * 0.003)  # Increasing debt
                        security_score = 90 - (day * 0.2)  # Declining security
                    # Stable metrics for project_gamma
                    else:
                        coverage = 80 + (day * 0.05 if day % 2 == 0 else -0.05)  # Stable
                        complexity = 10 + (day * 0.02 if day % 3 == 0 else -0.02)  # Stable
                        debt_ratio = 0.2 + (day * 0.001 if day % 4 == 0 else -0.001)  # Stable
                        security_score = 85 + (day * 0.1 if day % 2 == 0 else -0.1)  # Stable
                    
                    metrics = QualityMetrics(
                        project_id=project_id,
                        timestamp=timestamp,
                        code_coverage=min(max(coverage, 0), 100),
                        cyclomatic_complexity=max(complexity, 1),
                        maintainability_index=75 + i * 5,
                        technical_debt_ratio=max(min(debt_ratio, 1), 0),
                        test_quality_score=80 + i * 3,
                        security_score=min(max(security_score, 0), 100),
                        performance_score=75 + i * 4,
                        lines_of_code=5000 + i * 1000,
                        duplicate_code_ratio=0.05 + i * 0.02,
                        comment_ratio=0.15 - i * 0.02
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
            
            # Create test quality issues
            issue_types = [IssueType.SECURITY, IssueType.STYLE, IssueType.COMPLEXITY, IssueType.TESTING]
            severities = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
            
            for i, project_id in enumerate(self.test_projects):
                # Create different numbers of issues per project
                issue_count = 10 + i * 5
                
                for j in range(issue_count):
                    issue = QualityIssue(
                        project_id=project_id,
                        file_path=f"src/module_{j % 5}.py",
                        line_number=10 + j * 5,
                        issue_type=issue_types[j % len(issue_types)],
                        severity=severities[j % len(severities)],
                        category=f"category_{j % 3}",
                        description=f"Test issue {j} in {project_id}",
                        auto_fixable=(j % 3 == 0),  # Every 3rd issue is auto-fixable
                        status=IssueStatus.RESOLVED if j % 4 == 0 else IssueStatus.OPEN,
                        created_at=datetime.now(timezone.utc) - timedelta(days=j),
                        resolved_at=datetime.now(timezone.utc) - timedelta(days=j-1) if j % 4 == 0 else None
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
            
            # Create test auto-fix results
            for i, project_id in enumerate(self.test_projects):
                for j in range(5):  # 5 auto-fix results per project
                    fix_result = AutoFixResult(
                        project_id=project_id,
                        file_path=f"src/module_{j}.py",
                        fix_type=FixType.FORMATTING if j % 2 == 0 else FixType.IMPORTS,
                        success=(j % 3 != 0),  # Most fixes succeed
                        applied_at=datetime.now(timezone.utc) - timedelta(days=j),
                        applied_by="test_user"
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
            print("✅ Test data seeded successfully")
            
        finally:
            conn.close()
    
    async def test_executive_summary_generation(self):
        """Test executive summary report generation."""
        print("\n🧪 Testing Executive Summary Generation...")
        
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=self.test_projects,
            executive_level=True
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        
        # Validate report structure
        assert 'executive_summary' in report['content']
        summary = report['content']['executive_summary']
        
        assert 'overall_health_score' in summary
        assert 'quality_grade' in summary
        assert 'critical_issues' in summary
        assert 'improvement_trend' in summary
        assert 'recommendations' in summary
        assert 'risk_assessment' in summary
        
        # Validate data types and ranges
        assert isinstance(summary['overall_health_score'], (int, float))
        assert 0 <= summary['overall_health_score'] <= 100
        assert summary['quality_grade'] in ['A', 'B', 'C', 'D', 'F']
        assert isinstance(summary['critical_issues'], int)
        assert summary['improvement_trend'] in ['improving', 'declining', 'stable']
        assert summary['risk_assessment'] in ['low', 'medium', 'high', 'critical']
        
        print(f"✅ Executive Summary: Health Score = {summary['overall_health_score']:.1f}, Grade = {summary['quality_grade']}")
        print(f"   Critical Issues: {summary['critical_issues']}, Trend: {summary['improvement_trend']}")
        
        return report
    
    async def test_trend_analysis_generation(self):
        """Test trend analysis report generation."""
        print("\n🧪 Testing Trend Analysis Generation...")
        
        config = ReportConfiguration(
            report_type=ReportType.TREND_ANALYSIS,
            format=ReportFormat.JSON,
            project_ids=self.test_projects,
            date_range=(
                datetime.now(timezone.utc) - timedelta(days=30),
                datetime.now(timezone.utc)
            )
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        
        # Validate report structure
        assert 'trend_analysis' in report['content']
        trends = report['content']['trend_analysis']
        
        # Should have trends for key metrics
        expected_metrics = ['code_coverage', 'cyclomatic_complexity', 'technical_debt_ratio', 'security_score']
        for metric in expected_metrics:
            if metric in trends:
                trend_data = trends[metric]
                assert 'trend_direction' in trend_data
                assert 'change_rate' in trend_data
                assert 'confidence_level' in trend_data
                assert trend_data['trend_direction'] in ['up', 'down', 'stable']
                assert isinstance(trend_data['change_rate'], (int, float))
                assert 0 <= trend_data['confidence_level'] <= 1
        
        assert 'overall_trend' in report['content']
        assert report['content']['overall_trend'] in ['improving', 'declining', 'stable']
        
        print(f"✅ Trend Analysis: Overall trend = {report['content']['overall_trend']}")
        print(f"   Analyzed {len(trends)} metrics with trends")
        
        return report
    
    async def test_comparative_analysis_generation(self):
        """Test comparative analysis report generation."""
        print("\n🧪 Testing Comparative Analysis Generation...")
        
        config = ReportConfiguration(
            report_type=ReportType.COMPARATIVE,
            format=ReportFormat.JSON,
            project_ids=self.test_projects
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        
        # Validate report structure
        assert 'comparative_analysis' in report['content']
        analysis = report['content']['comparative_analysis']
        
        assert 'baseline_project' in analysis
        assert 'comparison_projects' in analysis
        assert 'metric_comparisons' in analysis
        assert 'performance_rankings' in analysis
        
        # Validate baseline and comparisons
        assert analysis['baseline_project'] == self.test_projects[0]
        assert len(analysis['comparison_projects']) == len(self.test_projects) - 1
        
        # Validate metric comparisons
        comparisons = analysis['metric_comparisons']
        for metric_name, comparison_data in comparisons.items():
            assert 'baseline' in comparison_data
            assert 'comparisons' in comparison_data
            assert comparison_data['baseline']['project_id'] == self.test_projects[0]
        
        # Validate performance rankings
        rankings = analysis['performance_rankings']
        for metric_name, ranking in rankings.items():
            assert len(ranking) == len(self.test_projects)
            assert all(project in self.test_projects for project in ranking)
        
        print(f"✅ Comparative Analysis: Baseline = {analysis['baseline_project']}")
        print(f"   Compared {len(analysis['comparison_projects'])} projects across {len(comparisons)} metrics")
        
        return report
    
    async def test_project_health_analysis(self):
        """Test project health analysis generation."""
        print("\n🧪 Testing Project Health Analysis...")
        
        config = ReportConfiguration(
            report_type=ReportType.PROJECT_HEALTH,
            format=ReportFormat.JSON,
            project_ids=self.test_projects
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        
        # Validate report structure
        assert 'project_health' in report['content']
        health_data = report['content']['project_health']
        
        # Should have health data for all projects
        assert len(health_data) == len(self.test_projects)
        
        for project_id in self.test_projects:
            assert project_id in health_data
            project_health = health_data[project_id]
            
            assert 'health_score' in project_health
            assert 'health_status' in project_health
            assert 'risk_factors' in project_health
            assert 'metrics_summary' in project_health
            
            # Validate health score and status
            assert isinstance(project_health['health_score'], (int, float))
            assert 0 <= project_health['health_score'] <= 100
            assert project_health['health_status'] in ['excellent', 'good', 'fair', 'poor', 'critical']
            assert isinstance(project_health['risk_factors'], list)
        
        # Validate portfolio health
        assert 'portfolio_health' in report['content']
        portfolio = report['content']['portfolio_health']
        assert 'overall_score' in portfolio
        assert 'project_count' in portfolio
        assert portfolio['project_count'] == len(self.test_projects)
        
        print(f"✅ Project Health Analysis: {len(health_data)} projects analyzed")
        print(f"   Portfolio health score: {portfolio['overall_score']:.1f}")
        
        return report
    
    async def test_technical_debt_analysis(self):
        """Test technical debt analysis generation."""
        print("\n🧪 Testing Technical Debt Analysis...")
        
        config = ReportConfiguration(
            report_type=ReportType.TECHNICAL_DEBT,
            format=ReportFormat.JSON,
            project_ids=self.test_projects
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        
        # Validate report structure
        assert 'technical_debt_analysis' in report['content']
        debt_data = report['content']['technical_debt_analysis']
        
        # Should have debt analysis for all projects
        assert len(debt_data) == len(self.test_projects)
        
        for project_id in self.test_projects:
            assert project_id in debt_data
            project_debt = debt_data[project_id]
            
            assert 'debt_ratio' in project_debt
            assert 'debt_level' in project_debt
            assert 'estimated_debt_hours' in project_debt
            assert 'debt_sources' in project_debt
            
            # Validate debt metrics
            assert isinstance(project_debt['debt_ratio'], (int, float))
            assert 0 <= project_debt['debt_ratio'] <= 1
            assert project_debt['debt_level'] in ['low', 'moderate', 'high', 'critical']
            assert isinstance(project_debt['estimated_debt_hours'], (int, float))
            assert isinstance(project_debt['debt_sources'], list)
        
        # Validate portfolio summary
        assert 'portfolio_summary' in report['content']
        portfolio = report['content']['portfolio_summary']
        assert 'average_debt_ratio' in portfolio
        assert 'total_estimated_hours' in portfolio
        assert 'estimated_cost' in portfolio
        
        print(f"✅ Technical Debt Analysis: {len(debt_data)} projects analyzed")
        print(f"   Average debt ratio: {portfolio['average_debt_ratio']:.3f}")
        print(f"   Total estimated hours: {portfolio['total_estimated_hours']:.1f}")
        
        return report
    
    async def test_issue_summary_analysis(self):
        """Test issue summary analysis generation."""
        print("\n🧪 Testing Issue Summary Analysis...")
        
        config = ReportConfiguration(
            report_type=ReportType.ISSUE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=self.test_projects,
            date_range=(
                datetime.now(timezone.utc) - timedelta(days=30),
                datetime.now(timezone.utc)
            )
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        
        # Validate report structure
        assert 'issue_summary' in report['content']
        summary = report['content']['issue_summary']
        
        assert 'total_issues' in summary
        assert 'by_severity' in summary
        assert 'by_type' in summary
        assert 'by_status' in summary
        assert 'by_project' in summary
        assert 'auto_fixable' in summary
        
        # Validate issue counts
        assert isinstance(summary['total_issues'], int)
        assert summary['total_issues'] > 0
        
        # Validate categorizations
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if severity in summary['by_severity']:
                assert isinstance(summary['by_severity'][severity], int)
        
        for issue_type in ['security', 'style', 'complexity', 'testing']:
            if issue_type in summary['by_type']:
                assert isinstance(summary['by_type'][issue_type], int)
        
        # Validate project breakdown
        for project_id in self.test_projects:
            assert project_id in summary['by_project']
            assert isinstance(summary['by_project'][project_id], int)
        
        print(f"✅ Issue Summary Analysis: {summary['total_issues']} total issues")
        print(f"   Auto-fixable issues: {summary['auto_fixable']}")
        
        return report
    
    async def test_multiple_format_generation(self):
        """Test report generation in multiple formats."""
        print("\n🧪 Testing Multiple Format Generation...")
        
        formats_to_test = [ReportFormat.JSON, ReportFormat.CSV, ReportFormat.HTML, ReportFormat.MARKDOWN]
        
        for format_type in formats_to_test:
            config = ReportConfiguration(
                report_type=ReportType.EXECUTIVE_SUMMARY,
                format=format_type,
                project_ids=[self.test_projects[0]]  # Use single project for simplicity
            )
            
            report = await self.generator.generate_comprehensive_report(config)
            
            assert report['format'] == format_type.value
            assert 'content' in report
            
            # Validate format-specific content
            if format_type == ReportFormat.JSON:
                # Should be parseable JSON
                content_str = json.dumps(report['content'])
                json.loads(content_str)  # Should not raise exception
            elif format_type == ReportFormat.CSV:
                # Should contain CSV headers
                content = report['content']
                assert isinstance(content, str)
                assert "Metric,Value" in content
            elif format_type == ReportFormat.HTML:
                # Should contain HTML structure
                content = report['content']
                assert isinstance(content, str)
                assert "<!DOCTYPE html>" in content
                assert "<html>" in content
            elif format_type == ReportFormat.MARKDOWN:
                # Should contain Markdown headers
                content = report['content']
                assert isinstance(content, str)
                assert "# Quality Report" in content
                assert "## Executive Summary" in content
            
            print(f"   ✅ {format_type.value.upper()} format generated successfully")
        
        return True
    
    async def test_report_storage_and_retrieval(self):
        """Test report storage and retrieval operations."""
        print("\n🧪 Testing Report Storage and Retrieval...")
        
        # Generate and store a report
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=[self.test_projects[0]]
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        report_id = report['report_id']
        
        # Test retrieval
        retrieved_report = await self.generator.get_report(report_id)
        assert retrieved_report is not None
        assert retrieved_report['report_id'] == report_id
        
        # Test listing
        reports_list = await self.generator.list_reports()
        assert len(reports_list) > 0
        assert any(r['report_id'] == report_id for r in reports_list)
        
        # Test filtering
        filtered_reports = await self.generator.list_reports(
            report_type=ReportType.EXECUTIVE_SUMMARY
        )
        assert all(r['report_type'] == ReportType.EXECUTIVE_SUMMARY.value for r in filtered_reports)
        
        # Test export
        exported_json = await self.generator.export_report(report_id, ReportFormat.JSON)
        assert exported_json is not None
        
        exported_csv = await self.generator.export_report(report_id, ReportFormat.CSV)
        assert exported_csv is not None
        assert "Metric,Value" in exported_csv
        
        # Test deletion
        delete_success = await self.generator.delete_report(report_id)
        assert delete_success is True
        
        # Verify deletion
        deleted_report = await self.generator.get_report(report_id)
        assert deleted_report is None
        
        print("✅ Report storage and retrieval operations completed successfully")
        
        return True
    
    async def test_comprehensive_report_generation(self):
        """Test comprehensive report generation with all sections."""
        print("\n🧪 Testing Comprehensive Report Generation...")
        
        config = ReportConfiguration(
            report_type=ReportType.COMPREHENSIVE,
            format=ReportFormat.JSON,
            project_ids=self.test_projects,
            include_trends=True,
            include_comparisons=True,
            include_recommendations=True
        )
        
        report = await self.generator.generate_comprehensive_report(config)
        
        # Validate comprehensive report structure
        assert 'comprehensive_report' in report['content']
        comprehensive = report['content']['comprehensive_report']
        
        # Should contain all report types
        expected_sections = [
            'executive_summary',
            'trend_analysis',
            'comparative_analysis',
            'issue_summary',
            'project_health',
            'technical_debt'
        ]
        
        for section in expected_sections:
            assert section in comprehensive
            print(f"   ✅ {section.replace('_', ' ').title()} section included")
        
        # Validate metadata
        assert 'report_metadata' in report['content']
        metadata = report['content']['report_metadata']
        assert 'generated_at' in metadata
        assert 'project_count' in metadata
        assert metadata['project_count'] == len(self.test_projects)
        
        print(f"✅ Comprehensive report generated with {len(expected_sections)} sections")
        
        return report
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Starting Quality Reports Integration Tests")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Run individual test methods
            test_methods = [
                self.test_executive_summary_generation,
                self.test_trend_analysis_generation,
                self.test_comparative_analysis_generation,
                self.test_project_health_analysis,
                self.test_technical_debt_analysis,
                self.test_issue_summary_analysis,
                self.test_multiple_format_generation,
                self.test_report_storage_and_retrieval,
                self.test_comprehensive_report_generation
            ]
            
            results = []
            for test_method in test_methods:
                try:
                    result = await test_method()
                    results.append((test_method.__name__, True, result))
                except Exception as e:
                    print(f"❌ {test_method.__name__} failed: {e}")
                    results.append((test_method.__name__, False, str(e)))
            
            # Print summary
            print("\n" + "=" * 60)
            print("📊 Test Results Summary")
            print("=" * 60)
            
            passed = sum(1 for _, success, _ in results if success)
            total = len(results)
            
            for test_name, success, result in results:
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"{status} {test_name}")
                if not success:
                    print(f"   Error: {result}")
            
            print(f"\n🎯 Overall Results: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All integration tests passed successfully!")
                return True
            else:
                print("⚠️  Some tests failed. Please review the errors above.")
                return False
                
        except Exception as e:
            print(f"❌ Test setup failed: {e}")
            return False
        finally:
            await self.cleanup()


async def main():
    """Run the integration tests."""
    test_suite = QualityReportsIntegrationTest()
    success = await test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)