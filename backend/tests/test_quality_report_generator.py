"""
Unit tests for Quality Report Generator

Tests comprehensive quality report generation, analytics, and formatting.
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.services.quality_report_generator import (
    QualityReportGenerator, ReportConfiguration, ReportType, ReportFormat,
    ExecutiveSummary, ComparativeAnalysis, TrendAnalysis
)
from app.models.quality import (
    QualityMetrics, QualityIssue, QualityTrend, AutoFixResult,
    IssueType, Severity, IssueStatus, FixType
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def report_generator(temp_db):
    """Create a QualityReportGenerator instance for testing."""
    return QualityReportGenerator(temp_db)


@pytest.fixture
def sample_metrics():
    """Create sample quality metrics for testing."""
    return QualityMetrics(
        project_id="test_project_1",
        timestamp=datetime.now(timezone.utc),
        code_coverage=85.5,
        cyclomatic_complexity=8.2,
        maintainability_index=78.3,
        technical_debt_ratio=0.15,
        test_quality_score=82.1,
        security_score=91.7,
        performance_score=76.4,
        lines_of_code=5000,
        duplicate_code_ratio=0.08,
        comment_ratio=0.12
    )


@pytest.fixture
def sample_issues():
    """Create sample quality issues for testing."""
    return [
        QualityIssue(
            project_id="test_project_1",
            file_path="src/main.py",
            line_number=42,
            issue_type=IssueType.SECURITY,
            severity=Severity.CRITICAL,
            category="vulnerability",
            description="SQL injection vulnerability",
            auto_fixable=False,
            status=IssueStatus.OPEN
        ),
        QualityIssue(
            project_id="test_project_1",
            file_path="src/utils.py",
            line_number=15,
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="formatting",
            description="Line too long",
            auto_fixable=True,
            status=IssueStatus.OPEN
        ),
        QualityIssue(
            project_id="test_project_1",
            file_path="src/models.py",
            line_number=88,
            issue_type=IssueType.COMPLEXITY,
            severity=Severity.MEDIUM,
            category="complexity",
            description="Function too complex",
            auto_fixable=False,
            status=IssueStatus.RESOLVED,
            resolved_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
    ]


@pytest.fixture
def sample_trends():
    """Create sample quality trends for testing."""
    base_time = datetime.now(timezone.utc)
    return [
        QualityTrend(
            project_id="test_project_1",
            metric_name="code_coverage",
            metric_value=85.5,
            timestamp=base_time,
            trend_direction="up",
            change_percentage=5.2
        ),
        QualityTrend(
            project_id="test_project_1",
            metric_name="technical_debt_ratio",
            metric_value=0.15,
            timestamp=base_time,
            trend_direction="down",
            change_percentage=-8.1
        ),
        QualityTrend(
            project_id="test_project_1",
            metric_name="security_score",
            metric_value=91.7,
            timestamp=base_time,
            trend_direction="stable",
            change_percentage=0.5
        )
    ]


class TestQualityReportGenerator:
    """Test cases for QualityReportGenerator."""
    
    def test_initialization(self, temp_db):
        """Test report generator initialization."""
        generator = QualityReportGenerator(temp_db)
        assert generator.db_path == temp_db
        assert generator.metrics_collector is not None
    
    def test_calculate_project_health_score(self, report_generator, sample_metrics):
        """Test project health score calculation."""
        health_score = report_generator._calculate_project_health_score(sample_metrics)
        
        assert isinstance(health_score, float)
        assert 0 <= health_score <= 100
        assert health_score > 70  # Should be good based on sample metrics
    
    def test_calculate_quality_grade(self, report_generator):
        """Test quality grade calculation."""
        assert report_generator._calculate_quality_grade(95) == "A"
        assert report_generator._calculate_quality_grade(85) == "B"
        assert report_generator._calculate_quality_grade(75) == "C"
        assert report_generator._calculate_quality_grade(65) == "D"
        assert report_generator._calculate_quality_grade(45) == "F"
    
    def test_calculate_key_metrics_summary(self, report_generator, sample_metrics):
        """Test key metrics summary calculation."""
        metrics_list = [sample_metrics]
        summary = report_generator._calculate_key_metrics_summary(metrics_list)
        
        assert isinstance(summary, dict)
        assert 'code_coverage' in summary
        assert 'average' in summary['code_coverage']
        assert summary['code_coverage']['average'] == 85.5
    
    @pytest.mark.asyncio
    async def test_calculate_improvement_trend(self, report_generator, sample_trends):
        """Test improvement trend calculation."""
        from app.services.quality_report_generator import QualityReportData
        
        report_data = [QualityReportData(
            project_id="test_project_1",
            project_name="Test Project",
            report_date=datetime.now(timezone.utc),
            metrics=Mock(),
            issues=[],
            trends=sample_trends,
            auto_fixes=[]
        )]
        
        trend = await report_generator._calculate_improvement_trend(report_data)
        assert trend in ["improving", "declining", "stable"]
    
    @pytest.mark.asyncio
    async def test_generate_executive_recommendations(self, report_generator, sample_issues):
        """Test executive recommendations generation."""
        from app.services.quality_report_generator import QualityReportData
        
        report_data = [QualityReportData(
            project_id="test_project_1",
            project_name="Test Project",
            report_date=datetime.now(timezone.utc),
            metrics=Mock(
                code_coverage=60.0,
                technical_debt_ratio=0.4,
                security_score=70.0
            ),
            issues=sample_issues,
            trends=[],
            auto_fixes=[]
        )]
        
        recommendations = await report_generator._generate_executive_recommendations(report_data)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5
        assert any("critical" in rec.lower() for rec in recommendations)
    
    def test_assess_quality_risk(self, report_generator):
        """Test quality risk assessment."""
        assert report_generator._assess_quality_risk(30, 15) == "critical"
        assert report_generator._assess_quality_risk(50, 8) == "high"
        assert report_generator._assess_quality_risk(70, 2) == "medium"
        assert report_generator._assess_quality_risk(85, 0) == "low"
    
    def test_determine_investment_priority(self, report_generator):
        """Test investment priority determination."""
        assert report_generator._determine_investment_priority(40, 10, "declining") == "high"
        assert report_generator._determine_investment_priority(65, 2, "declining") == "medium"
        assert report_generator._determine_investment_priority(80, 0, "improving") == "low"
    
    @pytest.mark.asyncio
    async def test_analyze_metric_trend(self, report_generator, sample_trends):
        """Test metric trend analysis."""
        coverage_trends = [trend for trend in sample_trends if trend.metric_name == "code_coverage"]
        
        analysis = await report_generator._analyze_metric_trend("code_coverage", coverage_trends)
        
        assert isinstance(analysis, TrendAnalysis)
        assert analysis.metric_name == "code_coverage"
        assert analysis.trend_direction in ["up", "down", "stable"]
        assert isinstance(analysis.change_rate, float)
        assert 0 <= analysis.confidence_level <= 1
    
    def test_identify_best_practices(self, report_generator, sample_metrics):
        """Test best practices identification."""
        from app.services.quality_report_generator import QualityReportData
        
        report_data = [QualityReportData(
            project_id="test_project_1",
            project_name="Test Project",
            report_date=datetime.now(timezone.utc),
            metrics=sample_metrics,
            issues=[],
            trends=[],
            auto_fixes=[]
        )]
        
        performance_rankings = {
            "code_coverage": ["test_project_1"],
            "security_score": ["test_project_1"]
        }
        
        best_practices = report_generator._identify_best_practices(report_data, performance_rankings)
        
        assert isinstance(best_practices, list)
        # Should identify high coverage as best practice
        assert any("coverage" in practice.lower() for practice in best_practices)
    
    def test_identify_improvement_opportunities(self, report_generator, sample_issues):
        """Test improvement opportunities identification."""
        from app.services.quality_report_generator import QualityReportData
        
        report_data = [QualityReportData(
            project_id="test_project_1",
            project_name="Test Project",
            report_date=datetime.now(timezone.utc),
            metrics=Mock(
                code_coverage=60.0,
                cyclomatic_complexity=20.0
            ),
            issues=sample_issues,
            trends=[],
            auto_fixes=[]
        )]
        
        opportunities = report_generator._identify_improvement_opportunities(
            report_data, {}
        )
        
        assert isinstance(opportunities, list)
        assert any("coverage" in opp.lower() for opp in opportunities)
        assert any("complexity" in opp.lower() for opp in opportunities)
    
    def test_identify_top_performer(self, report_generator, sample_metrics):
        """Test top performer identification."""
        from app.services.quality_report_generator import QualityReportData
        
        report_data = [QualityReportData(
            project_id="test_project_1",
            project_name="Test Project",
            report_date=datetime.now(timezone.utc),
            metrics=sample_metrics,
            issues=[],
            trends=[],
            auto_fixes=[]
        )]
        
        top_performer = report_generator._identify_top_performer(report_data)
        
        assert isinstance(top_performer, dict)
        assert top_performer['project_id'] == "test_project_1"
        assert 'health_score' in top_performer
    
    def test_identify_projects_needing_attention(self, report_generator, sample_issues):
        """Test identification of projects needing attention."""
        from app.services.quality_report_generator import QualityReportData
        
        report_data = [QualityReportData(
            project_id="test_project_1",
            project_name="Test Project",
            report_date=datetime.now(timezone.utc),
            metrics=Mock(
                code_coverage=40.0,
                technical_debt_ratio=0.5,
                security_score=60.0
            ),
            issues=sample_issues,
            trends=[],
            auto_fixes=[]
        )]
        
        needs_attention = report_generator._identify_projects_needing_attention(report_data)
        
        assert isinstance(needs_attention, list)
        assert len(needs_attention) > 0
        assert needs_attention[0]['project_id'] == "test_project_1"
        assert 'reasons' in needs_attention[0]
    
    def test_generate_issue_recommendations(self, report_generator, sample_issues):
        """Test issue-based recommendations generation."""
        recommendations = report_generator._generate_issue_recommendations(sample_issues)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should recommend automated fixes for fixable issues
        assert any("automated" in rec.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_format_as_json(self, report_generator):
        """Test JSON formatting."""
        content = {"test": "data", "number": 42}
        formatted = await report_generator._format_report(content, ReportFormat.JSON)
        
        assert isinstance(formatted, str)
        parsed = json.loads(formatted)
        assert parsed == content
    
    @pytest.mark.asyncio
    async def test_format_as_csv(self, report_generator):
        """Test CSV formatting."""
        content = {
            "executive_summary": {
                "overall_health_score": 85.5,
                "quality_grade": "B",
                "critical_issues": 2
            }
        }
        
        formatted = await report_generator._format_report(content, ReportFormat.CSV)
        
        assert isinstance(formatted, str)
        assert "Metric,Value" in formatted
        assert "85.5" in formatted
        assert "B" in formatted
    
    @pytest.mark.asyncio
    async def test_format_as_html(self, report_generator):
        """Test HTML formatting."""
        content = {
            "executive_summary": {
                "overall_health_score": 85.5,
                "quality_grade": "B"
            },
            "project_health": {
                "test_project": {
                    "project_name": "Test Project",
                    "health_score": 85.5,
                    "health_status": "good",
                    "critical_issues": 0
                }
            }
        }
        
        formatted = await report_generator._format_report(content, ReportFormat.HTML)
        
        assert isinstance(formatted, str)
        assert "<!DOCTYPE html>" in formatted
        assert "Quality Report" in formatted
        assert "85.5" in formatted
    
    @pytest.mark.asyncio
    async def test_format_as_markdown(self, report_generator):
        """Test Markdown formatting."""
        content = {
            "executive_summary": {
                "overall_health_score": 85.5,
                "quality_grade": "B",
                "recommendations": ["Improve test coverage", "Reduce complexity"]
            },
            "project_health": {
                "test_project": {
                    "project_name": "Test Project",
                    "health_score": 85.5,
                    "health_status": "good",
                    "critical_issues": 0
                }
            }
        }
        
        formatted = await report_generator._format_report(content, ReportFormat.MARKDOWN)
        
        assert isinstance(formatted, str)
        assert "# Quality Report" in formatted
        assert "## Executive Summary" in formatted
        assert "85.5" in formatted
        assert "| Project |" in formatted


class TestReportGeneration:
    """Test cases for comprehensive report generation."""
    
    @pytest.mark.asyncio
    async def test_collect_project_data(self, report_generator):
        """Test project data collection."""
        with patch.object(report_generator, '_get_latest_metrics') as mock_metrics, \
             patch.object(report_generator, '_get_project_issues') as mock_issues, \
             patch.object(report_generator, '_get_project_trends') as mock_trends, \
             patch.object(report_generator, '_get_auto_fix_results') as mock_fixes, \
             patch.object(report_generator, '_get_test_metrics') as mock_test_metrics, \
             patch.object(report_generator, '_get_project_name') as mock_name:
            
            # Setup mocks
            mock_metrics.return_value = Mock()
            mock_issues.return_value = []
            mock_trends.return_value = []
            mock_fixes.return_value = []
            mock_test_metrics.return_value = None
            mock_name.return_value = "Test Project"
            
            data = await report_generator._collect_project_data("test_project", None)
            
            assert data is not None
            assert data.project_id == "test_project"
            assert data.project_name == "Test Project"
    
    @pytest.mark.asyncio
    async def test_generate_executive_summary_report(self, report_generator):
        """Test executive summary report generation."""
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=["test_project_1"]
        )
        
        with patch.object(report_generator, '_collect_project_data') as mock_collect:
            from app.services.quality_report_generator import QualityReportData
            
            mock_collect.return_value = QualityReportData(
                project_id="test_project_1",
                project_name="Test Project",
                report_date=datetime.now(timezone.utc),
                metrics=Mock(
                    code_coverage=85.0,
                    maintainability_index=80.0,
                    technical_debt_ratio=0.1,
                    security_score=90.0,
                    timestamp=datetime.now(timezone.utc)
                ),
                issues=[],
                trends=[],
                auto_fixes=[]
            )
            
            with patch.object(report_generator, '_store_report') as mock_store:
                mock_store.return_value = "test_report_id"
                
                report = await report_generator.generate_comprehensive_report(config)
                
                assert report['report_type'] == ReportType.EXECUTIVE_SUMMARY.value
                assert 'executive_summary' in report['content']
                assert 'overall_health_score' in report['content']['executive_summary']
    
    @pytest.mark.asyncio
    async def test_generate_trend_analysis_report(self, report_generator, sample_trends):
        """Test trend analysis report generation."""
        config = ReportConfiguration(
            report_type=ReportType.TREND_ANALYSIS,
            format=ReportFormat.JSON,
            project_ids=["test_project_1"]
        )
        
        with patch.object(report_generator, '_collect_project_data') as mock_collect:
            from app.services.quality_report_generator import QualityReportData
            
            mock_collect.return_value = QualityReportData(
                project_id="test_project_1",
                project_name="Test Project",
                report_date=datetime.now(timezone.utc),
                metrics=Mock(timestamp=datetime.now(timezone.utc)),
                issues=[],
                trends=sample_trends,
                auto_fixes=[]
            )
            
            with patch.object(report_generator, '_store_report') as mock_store:
                mock_store.return_value = "test_report_id"
                
                report = await report_generator.generate_comprehensive_report(config)
                
                assert report['report_type'] == ReportType.TREND_ANALYSIS.value
                assert 'trend_analysis' in report['content']
                assert 'overall_trend' in report['content']
    
    @pytest.mark.asyncio
    async def test_generate_comparative_analysis_report(self, report_generator):
        """Test comparative analysis report generation."""
        config = ReportConfiguration(
            report_type=ReportType.COMPARATIVE,
            format=ReportFormat.JSON,
            project_ids=["test_project_1", "test_project_2"]
        )
        
        with patch.object(report_generator, '_collect_project_data') as mock_collect:
            from app.services.quality_report_generator import QualityReportData
            
            def mock_collect_side_effect(project_id, date_range):
                return QualityReportData(
                    project_id=project_id,
                    project_name=f"Test Project {project_id[-1]}",
                    report_date=datetime.now(timezone.utc),
                    metrics=Mock(
                        code_coverage=80.0 if project_id == "test_project_1" else 70.0,
                        maintainability_index=85.0 if project_id == "test_project_1" else 75.0,
                        technical_debt_ratio=0.1,
                        security_score=90.0,
                        timestamp=datetime.now(timezone.utc)
                    ),
                    issues=[],
                    trends=[],
                    auto_fixes=[]
                )
            
            mock_collect.side_effect = mock_collect_side_effect
            
            with patch.object(report_generator, '_store_report') as mock_store:
                mock_store.return_value = "test_report_id"
                
                report = await report_generator.generate_comprehensive_report(config)
                
                assert report['report_type'] == ReportType.COMPARATIVE.value
                assert 'comparative_analysis' in report['content']
                assert 'baseline_project' in report['content']['comparative_analysis']
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_report_error_handling(self, report_generator):
        """Test error handling in comprehensive report generation."""
        config = ReportConfiguration(
            report_type=ReportType.COMPREHENSIVE,
            format=ReportFormat.JSON,
            project_ids=[]  # Empty project list should cause error
        )
        
        with pytest.raises(ValueError, match="No data available"):
            await report_generator.generate_comprehensive_report(config)


class TestDatabaseOperations:
    """Test cases for database operations."""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_report(self, report_generator):
        """Test storing and retrieving reports."""
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=["test_project"]
        )
        
        formatted_report = '{"test": "data"}'
        
        # Store report
        report_id = await report_generator._store_report(config, formatted_report)
        assert report_id is not None
        
        # Retrieve report
        retrieved_report = await report_generator.get_report(report_id)
        assert retrieved_report is not None
        assert retrieved_report['report_id'] == report_id
        assert retrieved_report['report_type'] == ReportType.EXECUTIVE_SUMMARY.value
    
    @pytest.mark.asyncio
    async def test_list_reports(self, report_generator):
        """Test listing reports."""
        # Store a test report first
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=["test_project"]
        )
        
        await report_generator._store_report(config, '{"test": "data"}')
        
        # List reports
        reports = await report_generator.list_reports()
        assert isinstance(reports, list)
        assert len(reports) > 0
        
        # Test filtering
        filtered_reports = await report_generator.list_reports(
            report_type=ReportType.EXECUTIVE_SUMMARY
        )
        assert all(r['report_type'] == ReportType.EXECUTIVE_SUMMARY.value for r in filtered_reports)
    
    @pytest.mark.asyncio
    async def test_delete_report(self, report_generator):
        """Test deleting reports."""
        # Store a test report first
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=["test_project"]
        )
        
        report_id = await report_generator._store_report(config, '{"test": "data"}')
        
        # Verify report exists
        report = await report_generator.get_report(report_id)
        assert report is not None
        
        # Delete report
        success = await report_generator.delete_report(report_id)
        assert success is True
        
        # Verify report is deleted
        deleted_report = await report_generator.get_report(report_id)
        assert deleted_report is None
    
    @pytest.mark.asyncio
    async def test_export_report(self, report_generator):
        """Test exporting reports in different formats."""
        # Store a test report first
        config = ReportConfiguration(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.JSON,
            project_ids=["test_project"]
        )
        
        test_content = {"executive_summary": {"overall_health_score": 85.5}}
        report_id = await report_generator._store_report(config, json.dumps(test_content))
        
        # Export as JSON
        json_export = await report_generator.export_report(report_id, ReportFormat.JSON)
        assert json_export is not None
        assert isinstance(json_export, str)
        
        # Export as CSV
        csv_export = await report_generator.export_report(report_id, ReportFormat.CSV)
        assert csv_export is not None
        assert isinstance(csv_export, str)
        assert "Metric,Value" in csv_export
        
        # Export as HTML
        html_export = await report_generator.export_report(report_id, ReportFormat.HTML)
        assert html_export is not None
        assert isinstance(html_export, str)
        assert "<!DOCTYPE html>" in html_export


if __name__ == "__main__":
    pytest.main([__file__])