#!/usr/bin/env python3
"""
Demo script for Test Quality Analysis functionality.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.services.code_analysis.test_quality_analyzer import TestQualityAnalyzer
from app.services.code_analysis.base_analyzer import AnalysisContext
from app.models.quality import TestResult, TestCoverageData, FlakyTestData, TestStatus, TestType


def create_sample_test_files():
    """Create sample test files for demonstration."""
    samples = {
        "good_test.py": '''
import pytest
import unittest
from unittest.mock import Mock, patch

class TestUserService(unittest.TestCase):
    """Test suite for UserService functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user_service = UserService()
        self.mock_db = Mock()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.user_service = None
        self.mock_db = None
    
    def test_should_create_user_when_given_valid_data(self):
        """Test that user creation works with valid input data."""
        user_data = {"name": "John Doe", "email": "john@example.com"}
        
        result = self.user_service.create_user(user_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "John Doe")
        self.assertEqual(result.email, "john@example.com")
    
    def test_should_raise_error_when_given_invalid_email(self):
        """Test that invalid email raises appropriate error."""
        user_data = {"name": "John Doe", "email": "invalid-email"}
        
        with self.assertRaises(ValidationError):
            self.user_service.create_user(user_data)
    
    @patch('app.services.database.save_user')
    def test_should_save_user_to_database_when_created(self, mock_save):
        """Test that user is properly saved to database."""
        user_data = {"name": "Jane Doe", "email": "jane@example.com"}
        mock_save.return_value = True
        
        result = self.user_service.create_user(user_data)
        
        mock_save.assert_called_once()
        self.assertTrue(result.is_saved)

@pytest.fixture
def user_service():
    """Fixture providing UserService instance."""
    return UserService()

@pytest.fixture
def sample_user_data():
    """Fixture providing sample user data."""
    return {"name": "Test User", "email": "test@example.com"}

def test_should_authenticate_user_when_credentials_valid(user_service, sample_user_data):
    """Test user authentication with valid credentials."""
    user = user_service.create_user(sample_user_data)
    
    result = user_service.authenticate(user.email, "password123")
    
    assert result is not None
    assert result.is_authenticated
    assert result.user_id == user.id

def test_should_return_none_when_credentials_invalid(user_service):
    """Test authentication failure with invalid credentials."""
    result = user_service.authenticate("nonexistent@example.com", "wrongpassword")
    
    assert result is None
''',
        
        "problematic_test.py": '''
import unittest

class TestProblematic(unittest.TestCase):
    
    def test_bad(self):
        # No assertions, bad naming
        result = 2 + 2
        print(result)
    
    def test_another_bad(self):
        # Still no assertions
        x = [1, 2, 3]
        y = len(x)
    
    def test_overly_complex_logic(self):
        # Too complex for a test
        results = []
        for i in range(100):
            if i % 2 == 0:
                if i % 4 == 0:
                    if i % 8 == 0:
                        if i % 16 == 0:
                            results.append(i * 2)
                        else:
                            results.append(i + 1)
                    else:
                        results.append(i - 1)
                else:
                    results.append(i / 2)
            else:
                if i % 3 == 0:
                    results.append(i * 3)
                else:
                    results.append(i)
        
        # Finally some assertions, but way too many
        for i, result in enumerate(results):
            self.assertIsNotNone(result)
            self.assertIsInstance(result, (int, float))
            if i % 2 == 0:
                self.assertGreater(result, 0)
            else:
                self.assertGreaterEqual(result, 0)
    
    def test_no_docstring(self):
        self.assertEqual(1, 1)
        self.assertTrue(True)
        self.assertFalse(False)

def test_function_without_class():
    # No assertions again
    data = {"key": "value"}
    processed = process_data(data)
''',
        
        "empty_test.py": '''
# This file has no tests at all
def utility_function():
    return "not a test"

class UtilityClass:
    def method(self):
        pass
'''
    }
    
    return samples


def create_sample_test_results():
    """Create sample test results for flaky test detection."""
    test_results = []
    
    # Stable test - always passes
    for i in range(20):
        test_results.append(TestResult(
            project_id="demo_project",
            test_file="test_stable.py",
            test_name="test_stable_functionality",
            test_type=TestType.UNIT,
            status=TestStatus.PASSED,
            execution_time=0.05 + (i * 0.001),  # Slight variation
            timestamp=datetime.now(timezone.utc) - timedelta(hours=i)
        ))
    
    # Flaky test - fails intermittently
    failure_pattern = [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0]
    for i, should_fail in enumerate(failure_pattern):
        status = TestStatus.FAILED if should_fail else TestStatus.PASSED
        error_msg = "Connection timeout" if should_fail else None
        
        test_results.append(TestResult(
            project_id="demo_project",
            test_file="test_flaky.py",
            test_name="test_network_dependent_operation",
            test_type=TestType.INTEGRATION,
            status=status,
            execution_time=0.2 + (i * 0.01),
            error_message=error_msg,
            stack_trace="Traceback: connection failed" if should_fail else None,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=i)
        ))
    
    # Slow test
    for i in range(10):
        test_results.append(TestResult(
            project_id="demo_project",
            test_file="test_performance.py",
            test_name="test_heavy_computation",
            test_type=TestType.PERFORMANCE,
            status=TestStatus.PASSED,
            execution_time=2.5 + (i * 0.1),  # Consistently slow
            timestamp=datetime.now(timezone.utc) - timedelta(hours=i)
        ))
    
    # Some failing tests
    for i in range(5):
        test_results.append(TestResult(
            project_id="demo_project",
            test_file="test_broken.py",
            test_name="test_broken_functionality",
            test_type=TestType.UNIT,
            status=TestStatus.FAILED,
            execution_time=0.01,
            error_message="AssertionError: Expected 5, got 4",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=i)
        ))
    
    return test_results


def create_sample_coverage_data():
    """Create sample coverage data."""
    return TestCoverageData(
        project_id="demo_project",
        file_path="src/",
        lines_total=1500,
        lines_covered=1200,
        lines_missed=300,
        coverage_percentage=80.0,
        branches_total=200,
        branches_covered=160,
        branch_coverage_percentage=80.0
    )


async def demo_test_quality_analysis():
    """Demonstrate test quality analysis functionality."""
    print("🧪 Test Quality Analysis Demo")
    print("=" * 50)
    
    analyzer = TestQualityAnalyzer()
    sample_files = create_sample_test_files()
    
    print("\n📁 Analyzing Sample Test Files:")
    print("-" * 30)
    
    all_results = []
    
    for filename, content in sample_files.items():
        print(f"\n📄 Analyzing {filename}:")
        
        context = AnalysisContext(
            project_id="demo_project",
            file_path=filename,
            file_content=content
        )
        
        result = analyzer.analyze(context)
        all_results.append(result)
        
        print(f"  ✅ Analysis completed: {result.success}")
        print(f"  📊 Metrics found: {len(result.metrics)}")
        print(f"  ⚠️  Issues found: {len(result.issues)}")
        print(f"  💡 Suggestions: {len(result.suggestions)}")
        
        # Show key metrics
        if 'total_tests' in result.metrics:
            print(f"  🧪 Total tests: {result.metrics['total_tests']}")
            print(f"  📈 Test density: {result.metrics.get('test_density', 0):.2f}%")
            print(f"  🎯 Assertion density: {result.metrics.get('assertion_density', 0):.2f}")
            print(f"  📚 Documentation coverage: {result.metrics.get('documentation_coverage', 0):.1f}%")
        
        # Show critical issues
        critical_issues = [issue for issue in result.issues if issue.severity.value in ['critical', 'high']]
        if critical_issues:
            print(f"  🚨 Critical/High issues:")
            for issue in critical_issues[:3]:  # Show first 3
                print(f"    - {issue.category}: {issue.description}")
        
        # Show suggestions
        if result.suggestions:
            print(f"  💡 Top suggestions:")
            for suggestion in result.suggestions[:2]:  # Show first 2
                print(f"    - {suggestion}")
    
    print("\n" + "=" * 50)
    print("🔍 Flaky Test Detection Demo")
    print("=" * 50)
    
    test_results = create_sample_test_results()
    print(f"\n📊 Analyzing {len(test_results)} test results...")
    
    flaky_tests = analyzer.detect_flaky_tests(test_results, threshold=0.15)
    
    print(f"\n🎯 Flaky Tests Detected: {len(flaky_tests)}")
    for flaky in flaky_tests:
        print(f"\n📄 {flaky.test_file}::{flaky.test_name}")
        print(f"  📊 Flakiness Score: {flaky.flakiness_score:.2%}")
        print(f"  🔄 Total Runs: {flaky.total_runs}")
        print(f"  ❌ Failed Runs: {flaky.failed_runs}")
        print(f"  🕒 Last Failure: {flaky.last_failure}")
        if flaky.failure_patterns:
            print(f"  🔍 Failure Patterns:")
            for pattern in flaky.failure_patterns[:3]:
                print(f"    - {pattern}")
    
    print("\n" + "=" * 50)
    print("⚡ Test Performance Analysis Demo")
    print("=" * 50)
    
    performance_metrics = analyzer.analyze_test_performance(test_results)
    
    print(f"\n📊 Performance Metrics:")
    print(f"  ⏱️  Average Execution Time: {performance_metrics.get('average_execution_time', 0):.3f}s")
    print(f"  🐌 Max Execution Time: {performance_metrics.get('max_execution_time', 0):.3f}s")
    print(f"  ⚡ Min Execution Time: {performance_metrics.get('min_execution_time', 0):.3f}s")
    print(f"  📈 95th Percentile: {performance_metrics.get('p95_execution_time', 0):.3f}s")
    print(f"  🐌 Slow Tests Count: {performance_metrics.get('slow_tests_count', 0)}")
    
    if performance_metrics.get('slow_tests'):
        print(f"\n🐌 Slowest Tests:")
        for slow_test in performance_metrics['slow_tests'][:5]:
            print(f"  - {slow_test['test_name']}: {slow_test['execution_time']:.3f}s")
    
    print("\n" + "=" * 50)
    print("📋 Comprehensive Test Quality Report")
    print("=" * 50)
    
    coverage_data = create_sample_coverage_data()
    
    quality_metrics = analyzer.generate_test_quality_report(
        "demo_project", test_results, coverage_data, flaky_tests
    )
    
    print(f"\n📊 Test Quality Summary:")
    print(f"  🧪 Total Tests: {quality_metrics.total_tests}")
    print(f"  ✅ Passing Tests: {quality_metrics.passing_tests}")
    print(f"  ❌ Failing Tests: {quality_metrics.failing_tests}")
    print(f"  ⏭️  Skipped Tests: {quality_metrics.skipped_tests}")
    print(f"  🔄 Flaky Tests: {quality_metrics.flaky_tests}")
    print(f"  📈 Success Rate: {quality_metrics.test_success_rate:.1f}%")
    print(f"  ⏱️  Average Execution Time: {quality_metrics.average_execution_time:.3f}s")
    print(f"  📊 Code Coverage: {quality_metrics.code_coverage:.1f}%")
    print(f"  🌿 Branch Coverage: {quality_metrics.branch_coverage:.1f}%")
    print(f"  🏆 Maintainability Score: {quality_metrics.test_maintainability_score:.1f}/100")
    
    print("\n" + "=" * 50)
    print("💡 Test Quality Recommendations")
    print("=" * 50)
    
    # Generate recommendations based on analysis
    recommendations = []
    
    if quality_metrics.test_success_rate < 90:
        recommendations.append("🎯 Improve test reliability - success rate is below 90%")
    
    if quality_metrics.code_coverage < 80:
        recommendations.append("📊 Increase code coverage - currently below 80%")
    
    if quality_metrics.flaky_tests > 0:
        recommendations.append(f"🔄 Fix {quality_metrics.flaky_tests} flaky test(s) to improve reliability")
    
    if quality_metrics.average_execution_time > 1.0:
        recommendations.append("⚡ Optimize slow tests to improve development velocity")
    
    # Add recommendations from file analysis
    for result in all_results:
        if result.suggestions:
            recommendations.extend(result.suggestions[:2])
    
    if recommendations:
        print("\n📝 Recommended Actions:")
        for i, rec in enumerate(recommendations[:8], 1):  # Show top 8
            print(f"  {i}. {rec}")
    else:
        print("\n🎉 Great job! Your tests are in excellent shape!")
    
    print("\n" + "=" * 50)
    print("✅ Demo Complete!")
    print("=" * 50)
    
    return {
        'analysis_results': all_results,
        'flaky_tests': flaky_tests,
        'performance_metrics': performance_metrics,
        'quality_metrics': quality_metrics,
        'recommendations': recommendations
    }


if __name__ == "__main__":
    print("Starting Test Quality Analysis Demo...")
    result = asyncio.run(demo_test_quality_analysis())
    print(f"\nDemo completed successfully! Analyzed {len(result['analysis_results'])} files.")