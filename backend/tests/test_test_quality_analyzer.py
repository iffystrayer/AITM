"""
Unit tests for TestQualityAnalyzer.
"""

import ast
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from app.services.code_analysis.test_quality_analyzer import (
    TestQualityAnalyzer, TestQualityVisitor, TestFunction, TestSuite
)
from app.services.code_analysis.base_analyzer import AnalysisContext
from app.models.quality import (
    TestResult, TestCoverageData, FlakyTestData, TestQualityMetrics,
    TestType, TestStatus, IssueType, Severity
)


class TestTestQualityAnalyzer:
    """Test cases for TestQualityAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = TestQualityAnalyzer()
        self.sample_test_code = '''
import pytest
import unittest

class TestExample(unittest.TestCase):
    def setUp(self):
        self.data = [1, 2, 3]
    
    def tearDown(self):
        self.data = None
    
    def test_should_add_numbers_when_given_valid_input(self):
        """Test that addition works correctly."""
        result = 2 + 3
        self.assertEqual(result, 5)
        self.assertGreater(result, 0)
    
    def test_without_assertions(self):
        """Test without any assertions."""
        result = 2 + 3
        # No assertions here
    
    def test_complex_logic(self):
        """Test with complex logic."""
        for i in range(10):
            if i % 2 == 0:
                result = i * 2
                if result > 10:
                    assert result > 10
                else:
                    assert result <= 10
            else:
                result = i + 1
                assert result > i

@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_pytest_style():
    """Pytest style test."""
    assert True

def test_performance_heavy_operation():
    """Performance test example."""
    import time
    time.sleep(0.1)
    assert True
'''
    
    def test_analyze_test_code_basic(self):
        """Test basic test code analysis."""
        context = AnalysisContext(
            project_id="test_project",
            file_path="test_example.py",
            file_content=self.sample_test_code
        )
        
        result = self.analyzer.analyze(context)
        
        assert result.success
        assert len(result.issues) > 0
        assert 'total_tests' in result.metrics
        assert result.metrics['total_tests'] > 0
    
    def test_detect_missing_assertions(self):
        """Test detection of tests without assertions."""
        context = AnalysisContext(
            project_id="test_project",
            file_path="test_example.py",
            file_content=self.sample_test_code
        )
        
        result = self.analyzer.analyze(context)
        
        # Should detect test without assertions
        missing_assertion_issues = [
            issue for issue in result.issues 
            if issue.category == "missing_assertions"
        ]
        assert len(missing_assertion_issues) > 0
        assert any("test_without_assertions" in issue.description for issue in missing_assertion_issues)
    
    def test_detect_complex_tests(self):
        """Test detection of overly complex tests."""
        context = AnalysisContext(
            project_id="test_project",
            file_path="test_example.py",
            file_content=self.sample_test_code
        )
        
        result = self.analyzer.analyze(context)
        
        # Should detect complex test
        complex_test_issues = [
            issue for issue in result.issues 
            if issue.category == "complex_test"
        ]
        assert len(complex_test_issues) > 0
    
    def test_calculate_test_metrics(self):
        """Test calculation of test quality metrics."""
        context = AnalysisContext(
            project_id="test_project",
            file_path="test_example.py",
            file_content=self.sample_test_code
        )
        
        result = self.analyzer.analyze(context)
        
        # Check that metrics are calculated
        assert 'total_tests' in result.metrics
        assert 'total_assertions' in result.metrics
        assert 'test_density' in result.metrics
        assert 'assertion_density' in result.metrics
        assert 'average_complexity' in result.metrics
        assert 'documentation_coverage' in result.metrics
        
        # Verify metric values make sense
        assert result.metrics['total_tests'] >= 4  # We have at least 4 test functions
        assert result.metrics['total_assertions'] > 0
        assert result.metrics['test_density'] > 0
    
    def test_test_naming_convention_check(self):
        """Test checking of test naming conventions."""
        bad_naming_code = '''
def test_bad():
    assert True

def test_also_bad():
    assert True

def test_should_do_something_when_condition():
    assert True
'''
        
        context = AnalysisContext(
            project_id="test_project",
            file_path="test_naming.py",
            file_content=bad_naming_code
        )
        
        result = self.analyzer.analyze(context)
        
        # Should detect bad naming
        naming_issues = [
            issue for issue in result.issues 
            if issue.category == "test_naming_convention"
        ]
        assert len(naming_issues) >= 2  # Two bad names
    
    def test_empty_test_file(self):
        """Test analysis of file with no tests."""
        empty_code = '''
def regular_function():
    return True

class RegularClass:
    def method(self):
        pass
'''
        
        context = AnalysisContext(
            project_id="test_project",
            file_path="not_a_test.py",
            file_content=empty_code
        )
        
        result = self.analyzer.analyze(context)
        
        # Should detect missing tests
        missing_test_issues = [
            issue for issue in result.issues 
            if issue.category == "missing_tests"
        ]
        assert len(missing_test_issues) > 0
    
    def test_detect_flaky_tests(self):
        """Test flaky test detection."""
        # Create test results with some flaky patterns
        test_results = []
        
        # Stable test
        for i in range(10):
            test_results.append(TestResult(
                project_id="test_project",
                test_file="test_stable.py",
                test_name="test_stable_function",
                status=TestStatus.PASSED,
                execution_time=0.1,
                timestamp=datetime.now(timezone.utc) - timedelta(days=i)
            ))
        
        # Flaky test (fails 30% of the time)
        for i in range(10):
            status = TestStatus.FAILED if i % 3 == 0 else TestStatus.PASSED
            error_msg = "Random failure" if status == TestStatus.FAILED else None
            
            test_results.append(TestResult(
                project_id="test_project",
                test_file="test_flaky.py",
                test_name="test_flaky_function",
                status=status,
                execution_time=0.2,
                error_message=error_msg,
                timestamp=datetime.now(timezone.utc) - timedelta(days=i)
            ))
        
        flaky_tests = self.analyzer.detect_flaky_tests(test_results, threshold=0.1)
        
        assert len(flaky_tests) == 1
        assert flaky_tests[0].test_name == "test_flaky_function"
        assert flaky_tests[0].flakiness_score > 0.1
        assert flaky_tests[0].total_runs == 10
        assert flaky_tests[0].failed_runs > 0
    
    def test_analyze_test_performance(self):
        """Test test performance analysis."""
        test_results = [
            TestResult(
                test_name="fast_test",
                test_file="test_perf.py",
                execution_time=0.01,
                status=TestStatus.PASSED
            ),
            TestResult(
                test_name="slow_test",
                test_file="test_perf.py",
                execution_time=2.5,
                status=TestStatus.PASSED
            ),
            TestResult(
                test_name="medium_test",
                test_file="test_perf.py",
                execution_time=0.5,
                status=TestStatus.PASSED
            )
        ]
        
        performance_metrics = self.analyzer.analyze_test_performance(test_results)
        
        assert 'average_execution_time' in performance_metrics
        assert 'max_execution_time' in performance_metrics
        assert 'slow_tests_count' in performance_metrics
        assert 'slow_tests' in performance_metrics
        
        assert performance_metrics['max_execution_time'] == 2.5
        assert performance_metrics['slow_tests_count'] >= 1
    
    @patch('subprocess.run')
    def test_run_coverage_analysis(self, mock_subprocess):
        """Test running coverage analysis."""
        # Mock subprocess result
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Coverage output"
        
        # Mock coverage.json file
        coverage_json = {
            "totals": {
                "num_statements": 100,
                "covered_lines": 85,
                "missing_lines": 15,
                "percent_covered": 85.0,
                "num_branches": 20,
                "covered_branches": 18
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=str(coverage_json).replace("'", '"'))):
            
            coverage_data = self.analyzer._run_coverage_analysis("/fake/path")
            
            assert coverage_data.lines_total == 100
            assert coverage_data.lines_covered == 85
            assert coverage_data.coverage_percentage == 85.0
    
    def test_generate_test_quality_report(self):
        """Test generation of comprehensive test quality report."""
        test_results = [
            TestResult(
                project_id="test_project",
                test_name="test_1",
                test_file="test_file.py",
                status=TestStatus.PASSED,
                execution_time=0.1
            ),
            TestResult(
                project_id="test_project",
                test_name="test_2",
                test_file="test_file.py",
                status=TestStatus.FAILED,
                execution_time=0.2
            ),
            TestResult(
                project_id="test_project",
                test_name="test_3",
                test_file="test_file.py",
                status=TestStatus.SKIPPED,
                execution_time=0.0
            )
        ]
        
        coverage_data = TestCoverageData(
            project_id="test_project",
            coverage_percentage=75.0,
            branch_coverage_percentage=80.0
        )
        
        flaky_tests = [
            FlakyTestData(
                project_id="test_project",
                test_name="flaky_test",
                test_file="test_flaky.py",
                flakiness_score=0.3
            )
        ]
        
        metrics = self.analyzer.generate_test_quality_report(
            "test_project", test_results, coverage_data, flaky_tests
        )
        
        assert metrics.project_id == "test_project"
        assert metrics.total_tests == 3
        assert metrics.passing_tests == 1
        assert metrics.failing_tests == 1
        assert metrics.skipped_tests == 1
        assert metrics.flaky_tests == 1
        assert metrics.code_coverage == 75.0
        assert metrics.branch_coverage == 80.0
        assert 0 <= metrics.test_maintainability_score <= 100


class TestTestQualityVisitor:
    """Test cases for TestQualityVisitor."""
    
    def test_visit_test_functions(self):
        """Test visiting and analyzing test functions."""
        code = '''
def test_simple():
    assert True

def test_with_assertions():
    assert 1 == 1
    assert 2 > 1
    
def regular_function():
    return True
'''
        
        tree = ast.parse(code)
        visitor = TestQualityVisitor("test_file.py")
        visitor.visit(tree)
        
        test_suite = visitor.get_test_suite()
        
        assert len(test_suite.test_functions) == 2
        assert test_suite.test_functions[0].name == "test_simple"
        assert test_suite.test_functions[1].name == "test_with_assertions"
        assert test_suite.test_functions[1].assertions_count == 2
    
    def test_visit_test_class(self):
        """Test visiting test classes."""
        code = '''
import unittest

class TestExample(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_method(self):
        self.assertEqual(1, 1)
'''
        
        tree = ast.parse(code)
        visitor = TestQualityVisitor("test_file.py")
        visitor.visit(tree)
        
        test_suite = visitor.get_test_suite()
        
        assert len(test_suite.test_functions) == 1
        assert len(test_suite.setup_methods) == 1
        assert len(test_suite.teardown_methods) == 1
        assert "TestExample.setUp" in test_suite.setup_methods
        assert "TestExample.tearDown" in test_suite.teardown_methods
    
    def test_detect_fixtures(self):
        """Test detection of pytest fixtures."""
        code = '''
import pytest

@pytest.fixture
def sample_data():
    return {"key": "value"}

@fixture
def another_fixture():
    return [1, 2, 3]

def test_using_fixture(sample_data):
    assert sample_data["key"] == "value"
'''
        
        tree = ast.parse(code)
        visitor = TestQualityVisitor("test_file.py")
        visitor.visit(tree)
        
        test_suite = visitor.get_test_suite()
        
        assert len(test_suite.fixtures) == 2
        assert "sample_data" in test_suite.fixtures
        assert "another_fixture" in test_suite.fixtures
    
    def test_calculate_complexity(self):
        """Test complexity calculation for test functions."""
        code = '''
def test_complex():
    for i in range(10):
        if i % 2 == 0:
            if i > 5:
                assert i > 5
            else:
                assert i <= 5
        else:
            assert i % 2 == 1
'''
        
        tree = ast.parse(code)
        visitor = TestQualityVisitor("test_file.py")
        visitor.visit(tree)
        
        test_suite = visitor.get_test_suite()
        
        assert len(test_suite.test_functions) == 1
        # Should have complexity > 1 due to loops and conditionals
        assert test_suite.test_functions[0].complexity > 1
    
    def test_determine_test_type(self):
        """Test determination of test types."""
        code = '''
def test_unit_function():
    assert True

def test_integration_workflow():
    assert True

def test_performance_benchmark():
    assert True

def test_security_validation():
    assert True
'''
        
        tree = ast.parse(code)
        visitor = TestQualityVisitor("test_file.py")
        visitor.visit(tree)
        
        test_suite = visitor.get_test_suite()
        
        test_types = {tf.name: tf.test_type for tf in test_suite.test_functions}
        
        assert test_types["test_unit_function"] == TestType.UNIT
        assert test_types["test_integration_workflow"] == TestType.INTEGRATION
        assert test_types["test_performance_benchmark"] == TestType.PERFORMANCE
        assert test_types["test_security_validation"] == TestType.SECURITY


class TestTestQualityIntegration:
    """Integration tests for test quality analysis."""
    
    def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        analyzer = TestQualityAnalyzer()
        
        test_code = '''
import pytest
import unittest

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()
    
    def test_should_add_numbers_when_given_valid_input(self):
        """Test addition functionality."""
        result = self.calc.add(2, 3)
        self.assertEqual(result, 5)
        self.assertIsInstance(result, int)
    
    def test_without_docstring(self):
        result = self.calc.subtract(5, 3)
        self.assertEqual(result, 2)
    
    def test_complex_calculation(self):
        for i in range(5):
            if i % 2 == 0:
                result = self.calc.multiply(i, 2)
                if result > 4:
                    self.assertGreater(result, 4)
                else:
                    self.assertLessEqual(result, 4)

@pytest.fixture
def calculator():
    return Calculator()

def test_pytest_style(calculator):
    assert calculator.add(1, 1) == 2
'''
        
        context = AnalysisContext(
            project_id="integration_test",
            file_path="test_calculator.py",
            file_content=test_code
        )
        
        result = analyzer.analyze(context)
        
        # Verify analysis completed successfully
        assert result.success
        assert len(result.issues) > 0
        assert len(result.metrics) > 0
        assert len(result.suggestions) > 0
        
        # Verify specific issues were detected
        issue_categories = {issue.category for issue in result.issues}
        assert "missing_test_docstring" in issue_categories
        assert "complex_test" in issue_categories
        
        # Verify metrics were calculated
        assert result.metrics['total_tests'] == 4
        assert result.metrics['fixture_count'] == 1
        assert result.metrics['has_setup_methods'] is True
    
    def test_coverage_and_flaky_test_integration(self):
        """Test integration of coverage analysis and flaky test detection."""
        analyzer = TestQualityAnalyzer()
        
        # Create test results with mixed outcomes
        test_results = []
        for i in range(20):
            # Create some flaky behavior
            status = TestStatus.FAILED if i % 7 == 0 else TestStatus.PASSED
            test_results.append(TestResult(
                project_id="integration_test",
                test_file="test_integration.py",
                test_name="test_flaky_behavior",
                status=status,
                execution_time=0.1 + (i * 0.01),
                error_message="Intermittent failure" if status == TestStatus.FAILED else None,
                timestamp=datetime.now(timezone.utc) - timedelta(hours=i)
            ))
        
        # Add some stable tests
        for i in range(10):
            test_results.append(TestResult(
                project_id="integration_test",
                test_file="test_integration.py",
                test_name="test_stable_behavior",
                status=TestStatus.PASSED,
                execution_time=0.05,
                timestamp=datetime.now(timezone.utc) - timedelta(hours=i)
            ))
        
        # Create coverage data
        coverage_data = TestCoverageData(
            project_id="integration_test",
            lines_total=200,
            lines_covered=160,
            coverage_percentage=80.0,
            branches_total=50,
            branches_covered=40,
            branch_coverage_percentage=80.0
        )
        
        # Detect flaky tests
        flaky_tests = analyzer.detect_flaky_tests(test_results, threshold=0.1)
        
        # Analyze performance
        performance_metrics = analyzer.analyze_test_performance(test_results)
        
        # Generate comprehensive report
        quality_metrics = analyzer.generate_test_quality_report(
            "integration_test", test_results, coverage_data, flaky_tests
        )
        
        # Verify integration results
        assert len(flaky_tests) == 1
        assert flaky_tests[0].test_name == "test_flaky_behavior"
        assert flaky_tests[0].flakiness_score > 0.1
        
        assert performance_metrics['average_execution_time'] > 0
        assert 'slow_tests' in performance_metrics
        
        assert quality_metrics.total_tests == 30
        assert quality_metrics.flaky_tests == 1
        assert quality_metrics.code_coverage == 80.0
        assert quality_metrics.test_maintainability_score > 0


if __name__ == "__main__":
    pytest.main([__file__])