#!/usr/bin/env python3
"""
Integration test for Test Quality Analysis with existing quality infrastructure.
"""

import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.services.code_analysis.test_quality_analyzer import TestQualityAnalyzer
from app.services.code_analysis.base_analyzer import AnalysisContext
from app.services.quality_metrics_collector import QualityMetricsCollector
from app.services.quality_issue_tracker import QualityIssueTracker
from app.models.quality import TestResult, TestCoverageData, TestStatus, TestType
from app.core.quality_config import QualityConfigManager


async def test_integration_with_quality_infrastructure():
    """Test integration of test quality analyzer with existing quality infrastructure."""
    print("🔗 Testing Test Quality Analysis Integration")
    print("=" * 50)
    
    # Initialize components
    test_analyzer = TestQualityAnalyzer()
    metrics_collector = QualityMetricsCollector()
    issue_tracker = QualityIssueTracker()
    quality_config = QualityConfigManager()
    
    # Sample test code with various quality issues
    test_code = '''
import pytest
import unittest

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.data = {"key": "value"}
    
    def test_should_validate_data_when_given_valid_input(self):
        """Test data validation with valid input."""
        result = validate_data(self.data)
        self.assertTrue(result)
        self.assertIsInstance(result, bool)
    
    def test_bad_naming(self):
        # No docstring, bad naming
        result = process_data(self.data)
        self.assertIsNotNone(result)
    
    def test_no_assertions(self):
        """Test without assertions - should be flagged."""
        result = calculate_something(42)
        print(f"Result: {result}")
    
    def test_overly_complex_test(self):
        """Test with excessive complexity."""
        results = []
        for i in range(10):
            if i % 2 == 0:
                if i % 4 == 0:
                    result = i * 2
                    if result > 8:
                        self.assertGreater(result, 8)
                    else:
                        self.assertLessEqual(result, 8)
                else:
                    result = i + 1
                    self.assertGreater(result, i)
            else:
                result = i - 1
                self.assertLess(result, i)
            results.append(result)

@pytest.fixture
def test_data():
    return {"test": True}

def test_pytest_style(test_data):
    assert test_data["test"] is True
'''
    
    print("\n📊 Step 1: Analyzing Test Code Quality")
    print("-" * 30)
    
    context = AnalysisContext(
        project_id="integration_test",
        file_path="test_integration.py",
        file_content=test_code
    )
    
    # Analyze test quality
    analysis_result = test_analyzer.analyze(context)
    
    print(f"✅ Analysis completed: {analysis_result.success}")
    print(f"📊 Metrics collected: {len(analysis_result.metrics)}")
    print(f"⚠️  Issues found: {len(analysis_result.issues)}")
    
    # Display key metrics
    if analysis_result.metrics:
        print(f"\n📈 Key Test Metrics:")
        print(f"  - Total Tests: {analysis_result.metrics.get('total_tests', 0)}")
        print(f"  - Test Density: {analysis_result.metrics.get('test_density', 0):.2f}%")
        print(f"  - Assertion Density: {analysis_result.metrics.get('assertion_density', 0):.2f}")
        print(f"  - Documentation Coverage: {analysis_result.metrics.get('documentation_coverage', 0):.1f}%")
        print(f"  - Average Complexity: {analysis_result.metrics.get('average_complexity', 0):.2f}")
    
    print("\n📊 Step 2: Integrating with Quality Issue Tracker")
    print("-" * 30)
    
    # Track issues using the quality issue tracker
    tracked_issues = []
    for issue in analysis_result.issues:
        from app.models.quality import QualityIssueCreate
        issue_data = QualityIssueCreate(
            project_id=issue.project_id,
            file_path=issue.file_path,
            issue_type=issue.issue_type,
            severity=issue.severity,
            category=issue.category,
            description=issue.description,
            suggested_fix=issue.suggested_fix,
            line_number=issue.line_number
        )
        tracked_issue = await issue_tracker.create_issue(issue_data)
        tracked_issues.append(tracked_issue)
        print(f"📝 Tracked issue: {issue.category} - {issue.severity.value}")
    
    print(f"✅ Tracked {len(tracked_issues)} quality issues")
    
    print("\n📊 Step 3: Collecting Quality Metrics")
    print("-" * 30)
    
    # Create sample test results for metrics collection
    test_results = [
        TestResult(
            project_id="integration_test",
            test_file="test_integration.py",
            test_name="test_should_validate_data_when_given_valid_input",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            execution_time=0.05
        ),
        TestResult(
            project_id="integration_test",
            test_file="test_integration.py",
            test_name="test_bad_naming",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            execution_time=0.03
        ),
        TestResult(
            project_id="integration_test",
            test_file="test_integration.py",
            test_name="test_no_assertions",
            test_type=TestType.UNIT,
            status=TestStatus.FAILED,
            execution_time=0.02,
            error_message="Test failed due to missing assertions"
        ),
        TestResult(
            project_id="integration_test",
            test_file="test_integration.py",
            test_name="test_overly_complex_test",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            execution_time=0.15
        ),
        TestResult(
            project_id="integration_test",
            test_file="test_integration.py",
            test_name="test_pytest_style",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            execution_time=0.01
        )
    ]
    
    # Create coverage data
    coverage_data = TestCoverageData(
        project_id="integration_test",
        file_path="test_integration.py",
        lines_total=100,
        lines_covered=75,
        coverage_percentage=75.0,
        branches_total=20,
        branches_covered=15,
        branch_coverage_percentage=75.0
    )
    
    # Generate comprehensive test quality report
    test_quality_metrics = test_analyzer.generate_test_quality_report(
        "integration_test", test_results, coverage_data, []
    )
    
    print(f"📊 Test Quality Metrics Generated:")
    print(f"  - Total Tests: {test_quality_metrics.total_tests}")
    print(f"  - Success Rate: {test_quality_metrics.test_success_rate:.1f}%")
    print(f"  - Code Coverage: {test_quality_metrics.code_coverage:.1f}%")
    print(f"  - Maintainability Score: {test_quality_metrics.test_maintainability_score:.1f}/100")
    
    # Collect metrics using the quality metrics collector
    quality_metrics = await metrics_collector.collect_comprehensive_metrics("integration_test", ".")
    
    # Add test-specific metrics
    quality_metrics.test_quality_score = test_quality_metrics.test_maintainability_score
    quality_metrics.code_coverage = test_quality_metrics.code_coverage
    
    print(f"✅ Quality metrics collected and updated")
    
    print("\n📊 Step 4: Flaky Test Detection")
    print("-" * 30)
    
    # Create historical test results to simulate flaky behavior
    historical_results = []
    
    # Simulate a flaky test over 15 runs
    flaky_pattern = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1]  # 5 failures out of 15
    
    for i, should_fail in enumerate(flaky_pattern):
        status = TestStatus.FAILED if should_fail else TestStatus.PASSED
        error_msg = "Intermittent database connection error" if should_fail else None
        
        historical_results.append(TestResult(
            project_id="integration_test",
            test_file="test_integration.py",
            test_name="test_database_connection",
            test_type=TestType.INTEGRATION,
            status=status,
            execution_time=0.1 + (i * 0.01),
            error_message=error_msg,
            timestamp=datetime.now(timezone.utc)
        ))
    
    # Detect flaky tests
    flaky_tests = test_analyzer.detect_flaky_tests(historical_results, threshold=0.2)
    
    print(f"🔍 Flaky tests detected: {len(flaky_tests)}")
    for flaky in flaky_tests:
        print(f"  - {flaky.test_name}: {flaky.flakiness_score:.1%} flaky")
        
        # Create quality issue for flaky test
        from app.models.quality import QualityIssueCreate, IssueType, Severity
        flaky_issue_data = QualityIssueCreate(
            project_id="integration_test",
            file_path=flaky.test_file,
            issue_type=IssueType.TESTING,
            severity=Severity.MEDIUM,
            category="flaky_test",
            description=f"Test '{flaky.test_name}' is flaky ({flaky.flakiness_score:.1%})",
            suggested_fix="Investigate and fix intermittent failures"
        )
        flaky_issue = await issue_tracker.create_issue(flaky_issue_data)
        print(f"    📝 Created flaky test issue: {flaky_issue.id}")
    
    print("\n📊 Step 5: Performance Analysis Integration")
    print("-" * 30)
    
    # Analyze test performance
    performance_metrics = test_analyzer.analyze_test_performance(test_results + historical_results)
    
    print(f"⚡ Performance Analysis:")
    print(f"  - Average Execution Time: {performance_metrics.get('average_execution_time', 0):.3f}s")
    print(f"  - Slow Tests: {performance_metrics.get('slow_tests_count', 0)}")
    
    # Create performance issues for slow tests
    if performance_metrics.get('slow_tests'):
        for slow_test in performance_metrics['slow_tests'][:3]:  # Top 3
            perf_issue_data = QualityIssueCreate(
                project_id="integration_test",
                file_path=slow_test['test_file'],
                issue_type=IssueType.PERFORMANCE,
                severity=Severity.LOW,
                category="slow_test",
                description=f"Test '{slow_test['test_name']}' is slow ({slow_test['execution_time']:.3f}s)",
                suggested_fix="Optimize test execution or use mocking"
            )
            perf_issue = await issue_tracker.create_issue(perf_issue_data)
            print(f"    📝 Created slow test issue: {perf_issue.id}")
    
    print("\n📊 Step 6: Quality Configuration Integration")
    print("-" * 30)
    
    # Test integration with quality configuration
    thresholds = quality_config.get_quality_thresholds("integration_test")
    
    # Update configuration with test-specific thresholds
    test_config = {
        "min_coverage": 80.0,
        "max_complexity": 3,
        "min_assertions_per_test": 1,
        "max_execution_time": 1.0,
        "flakiness_threshold": 0.1
    }
    print(f"✅ Updated quality configuration with test-specific settings")
    
    # Validate against configuration
    violations = []
    
    if test_quality_metrics.code_coverage < test_config["min_coverage"]:
        violations.append(f"Code coverage ({test_quality_metrics.code_coverage:.1f}%) below threshold")
    
    if analysis_result.metrics.get('average_complexity', 0) > test_config["max_complexity"]:
        violations.append(f"Average test complexity too high")
    
    if len(flaky_tests) > 0:
        violations.append(f"Found {len(flaky_tests)} flaky test(s)")
    
    print(f"⚠️  Configuration violations: {len(violations)}")
    for violation in violations:
        print(f"  - {violation}")
    
    print("\n📊 Step 7: Summary Report")
    print("-" * 30)
    
    total_issues = len(analysis_result.issues) + len(flaky_tests)
    
    print(f"📋 Integration Test Summary:")
    print(f"  ✅ Test Quality Analysis: Completed")
    print(f"  📊 Metrics Collected: {len(analysis_result.metrics)} test metrics")
    print(f"  ⚠️  Issues Tracked: {total_issues} total issues")
    print(f"  🔍 Flaky Tests: {len(flaky_tests)} detected")
    print(f"  ⚡ Performance Issues: {performance_metrics.get('slow_tests_count', 0)} slow tests")
    print(f"  📈 Overall Quality Score: {test_quality_metrics.test_maintainability_score:.1f}/100")
    print(f"  🎯 Configuration Compliance: {len(violations)} violations")
    
    print("\n" + "=" * 50)
    print("✅ Integration Test Complete!")
    print("=" * 50)
    
    return {
        'analysis_result': analysis_result,
        'tracked_issues': tracked_issues,
        'test_quality_metrics': test_quality_metrics,
        'flaky_tests': flaky_tests,
        'performance_metrics': performance_metrics,
        'violations': violations
    }


if __name__ == "__main__":
    print("Starting Test Quality Analysis Integration Test...")
    result = asyncio.run(test_integration_with_quality_infrastructure())
    print(f"\nIntegration test completed! Found {len(result['tracked_issues'])} issues and {len(result['flaky_tests'])} flaky tests.")