"""
Unit tests for code analysis framework.
"""

import pytest
import tempfile
import os
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from app.services.code_analysis import (
    CodeAnalyzer, AnalysisResult, AnalysisContext, AnalysisType,
    FileSystemMonitor, FileChangeEvent, FileChangeType,
    QualityIssueDetector, IssueDetectionPipeline,
    CodeScanningFramework, ScanConfiguration, ScanResult
)
from app.models.quality import QualityIssue, IssueType, Severity


class TestAnalysisContext:
    """Test AnalysisContext functionality."""
    
    def test_context_creation(self):
        """Test creating analysis context."""
        context = AnalysisContext(
            project_id="test_project",
            file_path="test.py",
            file_content="print('hello')"
        )
        
        assert context.project_id == "test_project"
        assert context.file_path == "test.py"
        assert context.file_content == "print('hello')"
        assert context.language == "python"
        assert len(context.file_hash) == 32  # MD5 hash length
    
    def test_language_detection(self):
        """Test automatic language detection."""
        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.ts", "typescript"),
            ("test.java", "java"),
            ("test.cpp", "cpp"),
            ("test.unknown", "unknown")
        ]
        
        for file_path, expected_language in test_cases:
            context = AnalysisContext(
                project_id="test",
                file_path=file_path,
                file_content="test content"
            )
            assert context.language == expected_language


class TestAnalysisResult:
    """Test AnalysisResult functionality."""
    
    def test_result_creation(self):
        """Test creating analysis result."""
        context = AnalysisContext(
            project_id="test_project",
            file_path="test.py",
            file_content="print('hello')"
        )
        
        result = AnalysisResult(
            analyzer_name="test_analyzer",
            analysis_type=AnalysisType.STYLE,
            context=context
        )
        
        assert result.analyzer_name == "test_analyzer"
        assert result.analysis_type == AnalysisType.STYLE
        assert result.context == context
        assert result.success is True
        assert len(result.issues) == 0
        assert len(result.metrics) == 0
    
    def test_add_issue(self):
        """Test adding issues to result."""
        context = AnalysisContext(
            project_id="test_project",
            file_path="test.py",
            file_content="print('hello')"
        )
        
        result = AnalysisResult(
            analyzer_name="test_analyzer",
            analysis_type=AnalysisType.STYLE,
            context=context
        )
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            description="Test issue"
        )
        
        result.add_issue(issue)
        
        assert len(result.issues) == 1
        assert result.issues[0].project_id == "test_project"
        assert result.issues[0].file_path == "test.py"
    
    def test_merge_results(self):
        """Test merging analysis results."""
        context = AnalysisContext(
            project_id="test_project",
            file_path="test.py",
            file_content="print('hello')"
        )
        
        result1 = AnalysisResult(
            analyzer_name="analyzer1",
            analysis_type=AnalysisType.STYLE,
            context=context
        )
        result1.add_metric("metric1", 10)
        result1.add_suggestion("suggestion1")
        
        result2 = AnalysisResult(
            analyzer_name="analyzer2",
            analysis_type=AnalysisType.SECURITY,
            context=context
        )
        result2.add_metric("metric2", 20)
        result2.add_suggestion("suggestion2")
        
        merged = result1.merge(result2)
        
        assert merged.analyzer_name == "analyzer1+analyzer2"
        assert len(merged.metrics) == 2
        assert len(merged.suggestions) == 2
        assert merged.execution_time == result1.execution_time + result2.execution_time


class MockAnalyzer(CodeAnalyzer):
    """Mock analyzer for testing."""
    
    def __init__(self, name: str = "mock_analyzer"):
        super().__init__(name, AnalysisType.STYLE)
        self.supported_languages = {"python"}
        self.should_fail = False
        self.issues_to_return = []
    
    def _analyze_implementation(self, context: AnalysisContext) -> AnalysisResult:
        if self.should_fail:
            raise Exception("Mock analyzer failure")
        
        result = AnalysisResult(
            analyzer_name=self.name,
            analysis_type=self.analysis_type,
            context=context
        )
        
        for issue in self.issues_to_return:
            result.add_issue(issue)
        
        result.add_metric("lines_analyzed", len(context.file_content.split('\n')))
        return result


class TestCodeAnalyzer:
    """Test CodeAnalyzer base class."""
    
    def test_analyzer_creation(self):
        """Test creating analyzer."""
        analyzer = MockAnalyzer("test_analyzer")
        
        assert analyzer.name == "test_analyzer"
        assert analyzer.analysis_type == AnalysisType.STYLE
        assert "python" in analyzer.supported_languages
    
    def test_language_support(self):
        """Test language support checking."""
        analyzer = MockAnalyzer()
        
        assert analyzer.supports_language("python") is True
        assert analyzer.supports_language("javascript") is False
    
    def test_file_support(self):
        """Test file support checking."""
        analyzer = MockAnalyzer()
        
        assert analyzer.supports_file("test.py") is True
        assert analyzer.supports_file("test.js") is False
    
    def test_successful_analysis(self):
        """Test successful analysis."""
        analyzer = MockAnalyzer()
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')\nprint('world')"
        )
        
        result = analyzer.analyze(context)
        
        assert result.success is True
        assert result.error_message is None
        assert result.metrics["lines_analyzed"] == 2
        assert result.execution_time > 0
    
    def test_failed_analysis(self):
        """Test failed analysis."""
        analyzer = MockAnalyzer()
        analyzer.should_fail = True
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')"
        )
        
        result = analyzer.analyze(context)
        
        assert result.success is False
        assert result.error_message == "Mock analyzer failure"
    
    def test_unsupported_language(self):
        """Test analysis with unsupported language."""
        analyzer = MockAnalyzer()
        context = AnalysisContext(
            project_id="test",
            file_path="test.js",
            file_content="console.log('hello')"
        )
        
        result = analyzer.analyze(context)
        
        assert result.success is False
        assert "not supported" in result.error_message
    
    def test_caching(self):
        """Test result caching."""
        analyzer = MockAnalyzer()
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')"
        )
        
        # First analysis
        result1 = analyzer.analyze(context, use_cache=True)
        assert result1.success is True
        
        # Second analysis should use cache
        result2 = analyzer.analyze(context, use_cache=True)
        assert result2.success is True
        
        # Results should be the same object (cached)
        assert result1 is result2
        
        # Analysis without cache should create new result
        result3 = analyzer.analyze(context, use_cache=False)
        assert result3 is not result1


class TestQualityIssueDetector:
    """Test QualityIssueDetector."""
    
    def test_detector_creation(self):
        """Test creating issue detector."""
        detector = QualityIssueDetector()
        
        assert detector.name == "QualityIssueDetector"
        assert detector.analysis_type == AnalysisType.STYLE
        assert len(detector.rules) > 0
    
    def test_long_line_detection(self):
        """Test detection of long lines."""
        detector = QualityIssueDetector()
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="x = " + "a" * 100  # Very long line
        )
        
        result = detector.analyze(context)
        
        assert result.success is True
        assert len(result.issues) > 0
        
        # Should find long line issue
        long_line_issues = [i for i in result.issues if i.category == "long_line"]
        assert len(long_line_issues) > 0
    
    def test_trailing_whitespace_detection(self):
        """Test detection of trailing whitespace."""
        detector = QualityIssueDetector()
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')   \nprint('world')"  # Trailing spaces
        )
        
        result = detector.analyze(context)
        
        assert result.success is True
        
        # Should find trailing whitespace issue
        whitespace_issues = [i for i in result.issues if i.category == "trailing_whitespace"]
        assert len(whitespace_issues) > 0
    
    def test_hardcoded_password_detection(self):
        """Test detection of hardcoded passwords."""
        detector = QualityIssueDetector()
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="password = 'secret123'"
        )
        
        result = detector.analyze(context)
        
        assert result.success is True
        
        # Should find hardcoded password issue
        password_issues = [i for i in result.issues if i.category == "hardcoded_password"]
        assert len(password_issues) > 0
        assert password_issues[0].severity == Severity.HIGH
    
    def test_missing_docstring_detection(self):
        """Test detection of missing docstrings."""
        detector = QualityIssueDetector()
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="""
def my_function():
    return 42

class MyClass:
    def method(self):
        pass
"""
        )
        
        result = detector.analyze(context)
        
        assert result.success is True
        
        # Should find missing docstring issues
        docstring_issues = [i for i in result.issues if i.category == "missing_docstring"]
        assert len(docstring_issues) >= 2  # Function and class
    
    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        detector = QualityIssueDetector()
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="def invalid_syntax(\n    pass"  # Missing closing parenthesis
        )
        
        result = detector.analyze(context)
        
        assert result.success is True
        
        # Should find syntax error issue
        syntax_issues = [i for i in result.issues if i.category == "syntax_error"]
        assert len(syntax_issues) > 0
        assert syntax_issues[0].severity == Severity.CRITICAL
    
    def test_rule_management(self):
        """Test rule management functionality."""
        detector = QualityIssueDetector()
        initial_rule_count = len(detector.rules)
        
        # Test disabling rule
        assert detector.disable_rule("long_line") is True
        assert detector.rules["long_line"].enabled is False
        
        # Test enabling rule
        assert detector.enable_rule("long_line") is True
        assert detector.rules["long_line"].enabled is True
        
        # Test removing rule
        assert detector.remove_rule("long_line") is True
        assert "long_line" not in detector.rules
        assert len(detector.rules) == initial_rule_count - 1


class TestIssueDetectionPipeline:
    """Test IssueDetectionPipeline."""
    
    def test_pipeline_creation(self):
        """Test creating detection pipeline."""
        pipeline = IssueDetectionPipeline()
        
        assert len(pipeline.detectors) > 0
        assert len(pipeline.filters) == 0
        assert len(pipeline.transformers) == 0
    
    def test_add_detector(self):
        """Test adding detector to pipeline."""
        pipeline = IssueDetectionPipeline()
        mock_detector = MockAnalyzer("mock")
        initial_count = len(pipeline.detectors)
        
        pipeline.add_detector(mock_detector)
        
        assert len(pipeline.detectors) == initial_count + 1
        assert mock_detector in pipeline.detectors
    
    def test_issue_detection(self):
        """Test issue detection through pipeline."""
        pipeline = IssueDetectionPipeline()
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="x = " + "a" * 100  # Long line
        )
        
        issues = pipeline.detect_issues(context)
        
        assert len(issues) > 0
        assert all(isinstance(issue, QualityIssue) for issue in issues)
    
    def test_filters(self):
        """Test issue filtering."""
        pipeline = IssueDetectionPipeline()
        
        # Add filter to exclude low severity issues
        def severity_filter(issue):
            return issue.severity != Severity.LOW
        
        pipeline.add_filter(severity_filter)
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="x = " + "a" * 100 + "   "  # Long line + trailing whitespace
        )
        
        issues = pipeline.detect_issues(context)
        
        # Should not contain low severity issues
        low_severity_issues = [i for i in issues if i.severity == Severity.LOW]
        assert len(low_severity_issues) == 0
    
    def test_transformers(self):
        """Test issue transformation."""
        pipeline = IssueDetectionPipeline()
        
        # Add transformer to mark all issues as auto-fixable
        def auto_fix_transformer(issue):
            issue.auto_fixable = True
            return issue
        
        pipeline.add_transformer(auto_fix_transformer)
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')   "  # Trailing whitespace
        )
        
        issues = pipeline.detect_issues(context)
        
        # All issues should be marked as auto-fixable
        assert all(issue.auto_fixable for issue in issues)


class TestFileSystemMonitor:
    """Test FileSystemMonitor functionality."""
    
    def test_monitor_creation(self):
        """Test creating file system monitor."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = FileSystemMonitor(temp_dir, "test_project")
            
            assert monitor.project_path == Path(temp_dir).resolve()
            assert monitor.project_id == "test_project"
            assert monitor.is_monitoring is False
    
    def test_file_filtering(self):
        """Test file filtering logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = FileSystemMonitor(temp_dir, "test_project")
            
            # Should monitor Python files
            assert monitor.should_monitor_file("test.py") is True
            
            # Should not monitor cache files
            assert monitor.should_monitor_file("__pycache__/test.pyc") is False
            
            # Should not monitor files in ignored directories
            assert monitor.should_monitor_file("node_modules/package.js") is False
    
    def test_directory_filtering(self):
        """Test directory filtering logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = FileSystemMonitor(temp_dir, "test_project")
            
            # Should monitor regular directories
            assert monitor.should_monitor_directory("src") is True
            
            # Should not monitor ignored directories
            assert monitor.should_monitor_directory("__pycache__") is False
            assert monitor.should_monitor_directory(".git") is False
    
    def test_configuration(self):
        """Test monitor configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = FileSystemMonitor(temp_dir, "test_project")
            
            config = {
                'watched_extensions': ['.py', '.js'],
                'ignored_patterns': ['*.log'],
                'batch_size': 20
            }
            
            monitor.configure(config)
            
            assert monitor.watched_extensions == {'.py', '.js'}
            assert '*.log' in monitor.ignored_patterns
            assert monitor.batch_size == 20


class TestCodeScanningFramework:
    """Test CodeScanningFramework."""
    
    def test_framework_creation(self):
        """Test creating scanning framework."""
        framework = CodeScanningFramework()
        
        assert len(framework.analyzers) > 0
        assert framework.real_time_coordinator is None
    
    def test_analyzer_management(self):
        """Test analyzer management."""
        framework = CodeScanningFramework()
        mock_analyzer = MockAnalyzer("test_analyzer")
        
        # Add analyzer
        framework.add_analyzer(AnalysisType.SECURITY, mock_analyzer)
        
        security_analyzers = framework.get_analyzers(AnalysisType.SECURITY)
        assert mock_analyzer in security_analyzers
        
        # Remove analyzer
        assert framework.remove_analyzer(AnalysisType.SECURITY, "test_analyzer") is True
        
        security_analyzers = framework.get_analyzers(AnalysisType.SECURITY)
        assert mock_analyzer not in security_analyzers
    
    @pytest.mark.asyncio
    async def test_single_file_scan(self):
        """Test scanning a single file."""
        framework = CodeScanningFramework()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello world')\n")
            f.write("x = " + "a" * 100)  # Long line
            temp_file = f.name
        
        try:
            result = await framework.scan_file(temp_file, "test_project")
            
            assert result.success is True
            assert result.context.file_path == temp_file
            assert len(result.issues) > 0  # Should find long line issue
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_project_scan(self):
        """Test scanning an entire project."""
        framework = CodeScanningFramework()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = Path(temp_dir) / "test1.py"
            test_file1.write_text("print('hello')\n")
            
            test_file2 = Path(temp_dir) / "test2.py"
            test_file2.write_text("x = " + "a" * 100)  # Long line
            
            # Create ignored file
            ignored_dir = Path(temp_dir) / "__pycache__"
            ignored_dir.mkdir()
            ignored_file = ignored_dir / "test.pyc"
            ignored_file.write_text("compiled")
            
            config = ScanConfiguration(
                project_id="test_project",
                project_path=temp_dir,
                parallel_workers=2
            )
            
            result = await framework.scan_project(config)
            
            assert result.success is True
            assert result.files_scanned == 2  # Should scan 2 .py files
            assert result.total_issues > 0  # Should find issues
            assert result.metrics is not None
    
    def test_callback_management(self):
        """Test callback management."""
        framework = CodeScanningFramework()
        
        scan_started_called = False
        scan_completed_called = False
        file_analyzed_called = False
        issue_found_called = False
        
        def on_scan_started(scan_result):
            nonlocal scan_started_called
            scan_started_called = True
        
        def on_scan_completed(scan_result):
            nonlocal scan_completed_called
            scan_completed_called = True
        
        def on_file_analyzed(analysis_result):
            nonlocal file_analyzed_called
            file_analyzed_called = True
        
        def on_issue_found(issue):
            nonlocal issue_found_called
            issue_found_called = True
        
        framework.add_scan_started_callback(on_scan_started)
        framework.add_scan_completed_callback(on_scan_completed)
        framework.add_file_analyzed_callback(on_file_analyzed)
        framework.add_issue_found_callback(on_issue_found)
        
        stats = framework.get_framework_stats()
        assert stats['callback_counts']['scan_started'] == 1
        assert stats['callback_counts']['scan_completed'] == 1
        assert stats['callback_counts']['file_analyzed'] == 1
        assert stats['callback_counts']['issue_found'] == 1


class TestScanConfiguration:
    """Test ScanConfiguration."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = ScanConfiguration(
            project_id="test",
            project_path="/test/path"
        )
        
        assert config.project_id == "test"
        assert config.project_path == "/test/path"
        assert '**/*.py' in config.file_patterns
        assert '**/node_modules/**' in config.excluded_patterns
        assert config.max_file_size == 1024 * 1024
        assert config.parallel_workers == 4
        assert config.enable_real_time is True
        assert config.cache_results is True
        assert AnalysisType.STYLE in config.analysis_types


class TestScanResult:
    """Test ScanResult."""
    
    def test_result_creation(self):
        """Test creating scan result."""
        result = ScanResult(
            scan_id="test_scan",
            project_id="test_project",
            scan_type="full_project",
            started_at=datetime.now()
        )
        
        assert result.scan_id == "test_scan"
        assert result.project_id == "test_project"
        assert result.files_scanned == 0
        assert result.total_issues == 0
        assert result.success is True
    
    def test_add_analysis_result(self):
        """Test adding analysis results."""
        scan_result = ScanResult(
            scan_id="test_scan",
            project_id="test_project",
            scan_type="full_project",
            started_at=datetime.now()
        )
        
        context = AnalysisContext(
            project_id="test_project",
            file_path="test.py",
            file_content="print('hello')"
        )
        
        analysis_result = AnalysisResult(
            analyzer_name="test_analyzer",
            analysis_type=AnalysisType.STYLE,
            context=context
        )
        
        # Add some issues
        issue1 = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            description="Test issue 1"
        )
        issue2 = QualityIssue(
            issue_type=IssueType.SECURITY,
            severity=Severity.HIGH,
            description="Test issue 2"
        )
        
        analysis_result.add_issue(issue1)
        analysis_result.add_issue(issue2)
        
        scan_result.add_analysis_result(analysis_result)
        
        assert scan_result.files_scanned == 1
        assert scan_result.files_with_issues == 1
        assert scan_result.total_issues == 2
        assert scan_result.issues_by_severity['low'] == 1
        assert scan_result.issues_by_severity['high'] == 1
        assert scan_result.issues_by_type['style'] == 1
        assert scan_result.issues_by_type['security'] == 1
    
    def test_get_all_issues(self):
        """Test getting all issues from scan result."""
        scan_result = ScanResult(
            scan_id="test_scan",
            project_id="test_project",
            scan_type="full_project",
            started_at=datetime.now()
        )
        
        # Create two analysis results with issues
        for i in range(2):
            context = AnalysisContext(
                project_id="test_project",
                file_path=f"test{i}.py",
                file_content="print('hello')"
            )
            
            analysis_result = AnalysisResult(
                analyzer_name="test_analyzer",
                analysis_type=AnalysisType.STYLE,
                context=context
            )
            
            issue = QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                description=f"Test issue {i}"
            )
            
            analysis_result.add_issue(issue)
            scan_result.add_analysis_result(analysis_result)
        
        all_issues = scan_result.get_all_issues()
        assert len(all_issues) == 2
        assert all(isinstance(issue, QualityIssue) for issue in all_issues)
    
    def test_get_summary(self):
        """Test getting scan result summary."""
        scan_result = ScanResult(
            scan_id="test_scan",
            project_id="test_project",
            scan_type="full_project",
            started_at=datetime.now()
        )
        
        summary = scan_result.get_summary()
        
        assert summary['scan_id'] == "test_scan"
        assert summary['project_id'] == "test_project"
        assert summary['scan_type'] == "full_project"
        assert 'started_at' in summary
        assert summary['files_scanned'] == 0
        assert summary['success'] is True


if __name__ == "__main__":
    pytest.main([__file__])