"""
Test Quality Analyzer for comprehensive test assessment and coverage tracking.
"""

import ast
import re
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from app.services.code_analysis.base_analyzer import (
    PythonASTAnalyzer, AnalysisType, AnalysisContext, AnalysisResult
)
from app.models.quality import (
    QualityIssue, IssueType, Severity, TestResult, TestCoverageData, 
    FlakyTestData, TestQualityMetrics, TestType, TestStatus
)


@dataclass
class TestFunction:
    """Represents a test function found in code."""
    name: str
    file_path: str
    line_number: int
    test_type: TestType
    assertions_count: int = 0
    complexity: int = 1
    has_setup: bool = False
    has_teardown: bool = False
    dependencies: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class TestSuite:
    """Represents a test suite (test file or class)."""
    name: str
    file_path: str
    test_functions: List[TestFunction] = field(default_factory=list)
    setup_methods: List[str] = field(default_factory=list)
    teardown_methods: List[str] = field(default_factory=list)
    fixtures: List[str] = field(default_factory=list)


class TestQualityAnalyzer(PythonASTAnalyzer):
    """Analyzer for comprehensive test quality assessment."""
    
    def __init__(self):
        super().__init__("TestQualityAnalyzer", AnalysisType.TESTING)
        self.test_frameworks = {
            'pytest': ['pytest', 'test_', '_test'],
            'unittest': ['unittest', 'TestCase'],
            'nose': ['nose', 'test_'],
            'doctest': ['doctest']
        }
        self.assertion_patterns = [
            r'assert\s+',
            r'self\.assert\w+',
            r'self\.assertEqual',
            r'self\.assertTrue',
            r'self\.assertFalse',
            r'self\.assertRaises',
            r'pytest\.raises',
            r'expect\(',
            r'should\.',
        ]
        self.flaky_test_history: Dict[str, List[TestResult]] = defaultdict(list)
    
    def _analyze_ast(self, tree: ast.AST, result: AnalysisResult) -> None:
        """Analyze AST for test quality metrics."""
        visitor = TestQualityVisitor(result.context.file_path)
        visitor.visit(tree)
        
        # Analyze test functions
        test_suite = visitor.get_test_suite()
        self._analyze_test_suite(test_suite, result)
        
        # Calculate test quality metrics
        metrics = self._calculate_test_metrics(test_suite, result.context)
        for metric_name, metric_value in metrics.items():
            result.add_metric(metric_name, metric_value)
        
        # Generate quality issues
        self._generate_test_quality_issues(test_suite, result)
        
        # Add suggestions
        self._generate_test_suggestions(test_suite, result)
    
    def _analyze_test_suite(self, test_suite: TestSuite, result: AnalysisResult) -> None:
        """Analyze a test suite for quality issues."""
        if not test_suite.test_functions:
            # No tests found
            issue = QualityIssue(
                issue_type=IssueType.TESTING,
                severity=Severity.HIGH,
                category="missing_tests",
                description="No test functions found in test file",
                line_number=1
            )
            result.add_issue(issue)
            return
        
        # Analyze individual test functions
        for test_func in test_suite.test_functions:
            self._analyze_test_function(test_func, result)
    
    def _analyze_test_function(self, test_func: TestFunction, result: AnalysisResult) -> None:
        """Analyze individual test function quality."""
        # Check for assertions
        if test_func.assertions_count == 0:
            issue = QualityIssue(
                issue_type=IssueType.TESTING,
                severity=Severity.MEDIUM,
                category="missing_assertions",
                description=f"Test function '{test_func.name}' has no assertions",
                line_number=test_func.line_number,
                suggested_fix="Add appropriate assertions to verify test behavior"
            )
            result.add_issue(issue)
        
        # Check for excessive assertions (might indicate test doing too much)
        if test_func.assertions_count > 10:
            issue = QualityIssue(
                issue_type=IssueType.TESTING,
                severity=Severity.LOW,
                category="excessive_assertions",
                description=f"Test function '{test_func.name}' has {test_func.assertions_count} assertions",
                line_number=test_func.line_number,
                suggested_fix="Consider splitting into multiple focused test functions"
            )
            result.add_issue(issue)
        
        # Check for high complexity
        if test_func.complexity > 3:  # Lower threshold for tests
            issue = QualityIssue(
                issue_type=IssueType.TESTING,
                severity=Severity.MEDIUM,
                category="complex_test",
                description=f"Test function '{test_func.name}' has high complexity ({test_func.complexity})",
                line_number=test_func.line_number,
                suggested_fix="Simplify test logic or split into multiple tests"
            )
            result.add_issue(issue)
        
        # Check for missing docstring
        if not test_func.docstring:
            issue = QualityIssue(
                issue_type=IssueType.DOCUMENTATION,
                severity=Severity.LOW,
                category="missing_test_docstring",
                description=f"Test function '{test_func.name}' lacks documentation",
                line_number=test_func.line_number,
                suggested_fix="Add docstring explaining what the test verifies"
            )
            result.add_issue(issue)
    
    def _calculate_test_metrics(self, test_suite: TestSuite, context: AnalysisContext) -> Dict[str, Any]:
        """Calculate comprehensive test quality metrics."""
        metrics = {}
        
        if not test_suite.test_functions:
            return metrics
        
        # Basic counts
        total_tests = len(test_suite.test_functions)
        total_assertions = sum(tf.assertions_count for tf in test_suite.test_functions)
        
        # Test density (tests per 100 lines of code)
        lines_of_code = len(context.file_content.split('\n'))
        test_density = (total_tests / lines_of_code) * 100 if lines_of_code > 0 else 0
        
        # Assertion density
        assertion_density = total_assertions / total_tests if total_tests > 0 else 0
        
        # Complexity metrics
        avg_complexity = sum(tf.complexity for tf in test_suite.test_functions) / total_tests
        max_complexity = max(tf.complexity for tf in test_suite.test_functions)
        
        # Documentation coverage
        documented_tests = sum(1 for tf in test_suite.test_functions if tf.docstring)
        documentation_coverage = (documented_tests / total_tests) * 100
        
        # Test type distribution
        test_types = defaultdict(int)
        for tf in test_suite.test_functions:
            test_types[tf.test_type.value] += 1
        
        metrics.update({
            'total_tests': total_tests,
            'total_assertions': total_assertions,
            'test_density': test_density,
            'assertion_density': assertion_density,
            'average_complexity': avg_complexity,
            'max_complexity': max_complexity,
            'documentation_coverage': documentation_coverage,
            'test_type_distribution': dict(test_types),
            'has_setup_methods': len(test_suite.setup_methods) > 0,
            'has_teardown_methods': len(test_suite.teardown_methods) > 0,
            'fixture_count': len(test_suite.fixtures)
        })
        
        return metrics
    
    def _generate_test_quality_issues(self, test_suite: TestSuite, result: AnalysisResult) -> None:
        """Generate quality issues based on test analysis."""
        # Check for missing setup/teardown balance
        if test_suite.setup_methods and not test_suite.teardown_methods:
            issue = QualityIssue(
                issue_type=IssueType.TESTING,
                severity=Severity.MEDIUM,
                category="unbalanced_setup_teardown",
                description="Test suite has setup methods but no teardown methods",
                suggested_fix="Add corresponding teardown methods to clean up test state"
            )
            result.add_issue(issue)
        
        # Check for test naming conventions
        for test_func in test_suite.test_functions:
            if not self._follows_naming_convention(test_func.name):
                issue = QualityIssue(
                    issue_type=IssueType.TESTING,
                    severity=Severity.LOW,
                    category="test_naming_convention",
                    description=f"Test function '{test_func.name}' doesn't follow naming conventions",
                    line_number=test_func.line_number,
                    suggested_fix="Use descriptive names like 'test_should_do_something_when_condition'"
                )
                result.add_issue(issue)
    
    def _generate_test_suggestions(self, test_suite: TestSuite, result: AnalysisResult) -> None:
        """Generate improvement suggestions for tests."""
        if not test_suite.test_functions:
            result.add_suggestion("Add test functions to verify code behavior")
            return
        
        # Suggest test improvements
        if len(test_suite.test_functions) < 3:
            result.add_suggestion("Consider adding more test cases to improve coverage")
        
        avg_assertions = sum(tf.assertions_count for tf in test_suite.test_functions) / len(test_suite.test_functions)
        if avg_assertions < 1:
            result.add_suggestion("Add more assertions to strengthen test verification")
        
        if not test_suite.fixtures:
            result.add_suggestion("Consider using fixtures for test data setup")
        
        # Check for test types diversity
        test_types = set(tf.test_type for tf in test_suite.test_functions)
        if len(test_types) == 1 and TestType.UNIT in test_types:
            result.add_suggestion("Consider adding integration tests for broader coverage")
    
    def _follows_naming_convention(self, test_name: str) -> bool:
        """Check if test name follows good naming conventions."""
        # Should start with 'test_'
        if not test_name.startswith('test_'):
            return False
        
        # Should be descriptive (more than just 'test_something')
        parts = test_name.split('_')
        if len(parts) < 3:
            return False
        
        # Should contain action words
        action_words = ['should', 'when', 'given', 'then', 'if', 'returns', 'raises', 'creates', 'updates', 'deletes']
        return any(word in test_name.lower() for word in action_words)
    
    def analyze_test_coverage(self, project_path: str, coverage_file: Optional[str] = None) -> TestCoverageData:
        """Analyze test coverage from coverage reports."""
        coverage_data = TestCoverageData(project_id="", file_path=project_path)
        
        try:
            if coverage_file and Path(coverage_file).exists():
                # Parse coverage file (XML format)
                coverage_data = self._parse_coverage_xml(coverage_file)
            else:
                # Run coverage analysis
                coverage_data = self._run_coverage_analysis(project_path)
        except Exception as e:
            print(f"Error analyzing coverage: {e}")
        
        return coverage_data
    
    def _parse_coverage_xml(self, coverage_file: str) -> TestCoverageData:
        """Parse coverage data from XML file."""
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        coverage_data = TestCoverageData()
        
        # Parse coverage metrics
        for package in root.findall('.//package'):
            for class_elem in package.findall('classes/class'):
                filename = class_elem.get('filename', '')
                
                lines = class_elem.find('lines')
                if lines is not None:
                    lines_covered = int(lines.get('lines-covered', 0))
                    lines_valid = int(lines.get('lines-valid', 0))
                    
                    coverage_data.lines_covered += lines_covered
                    coverage_data.lines_total += lines_valid
                    coverage_data.lines_missed += (lines_valid - lines_covered)
        
        if coverage_data.lines_total > 0:
            coverage_data.coverage_percentage = (coverage_data.lines_covered / coverage_data.lines_total) * 100
        
        return coverage_data
    
    def _run_coverage_analysis(self, project_path: str) -> TestCoverageData:
        """Run coverage analysis using pytest-cov."""
        coverage_data = TestCoverageData(file_path=project_path)
        
        try:
            # Run pytest with coverage
            result = subprocess.run([
                'python', '-m', 'pytest', '--cov=' + project_path, 
                '--cov-report=json', '--cov-report=term-missing'
            ], capture_output=True, text=True, cwd=project_path)
            
            if result.returncode == 0:
                # Parse JSON coverage report
                coverage_json_path = Path(project_path) / 'coverage.json'
                if coverage_json_path.exists():
                    with open(coverage_json_path, 'r') as f:
                        coverage_json = json.load(f)
                    
                    totals = coverage_json.get('totals', {})
                    coverage_data.lines_total = totals.get('num_statements', 0)
                    coverage_data.lines_covered = totals.get('covered_lines', 0)
                    coverage_data.lines_missed = totals.get('missing_lines', 0)
                    coverage_data.coverage_percentage = totals.get('percent_covered', 0.0)
                    
                    # Branch coverage if available
                    coverage_data.branches_total = totals.get('num_branches', 0)
                    coverage_data.branches_covered = totals.get('covered_branches', 0)
                    if coverage_data.branches_total > 0:
                        coverage_data.branch_coverage_percentage = (
                            coverage_data.branches_covered / coverage_data.branches_total
                        ) * 100
        
        except Exception as e:
            print(f"Error running coverage analysis: {e}")
        
        return coverage_data
    
    def detect_flaky_tests(self, test_results: List[TestResult], 
                          threshold: float = 0.1) -> List[FlakyTestData]:
        """Detect flaky tests based on historical test results."""
        flaky_tests = []
        
        # Group test results by test name
        test_groups = defaultdict(list)
        for result in test_results:
            test_key = f"{result.test_file}::{result.test_name}"
            test_groups[test_key].append(result)
        
        # Analyze each test for flakiness
        for test_key, results in test_groups.items():
            if len(results) < 5:  # Need minimum runs to detect flakiness
                continue
            
            total_runs = len(results)
            failed_runs = sum(1 for r in results if r.status in [TestStatus.FAILED, TestStatus.ERROR])
            
            if failed_runs == 0:
                continue  # Stable test
            
            flakiness_score = failed_runs / total_runs
            
            if flakiness_score > threshold and flakiness_score < 0.9:  # Not completely broken
                # Extract failure patterns
                failure_patterns = []
                for result in results:
                    if result.status in [TestStatus.FAILED, TestStatus.ERROR] and result.error_message:
                        failure_patterns.append(result.error_message[:100])  # First 100 chars
                
                # Remove duplicates while preserving order
                unique_patterns = []
                seen = set()
                for pattern in failure_patterns:
                    if pattern not in seen:
                        unique_patterns.append(pattern)
                        seen.add(pattern)
                
                flaky_data = FlakyTestData(
                    test_file=results[0].test_file,
                    test_name=results[0].test_name,
                    total_runs=total_runs,
                    failed_runs=failed_runs,
                    flakiness_score=flakiness_score,
                    last_failure=max(r.timestamp for r in results if r.status in [TestStatus.FAILED, TestStatus.ERROR]),
                    failure_patterns=unique_patterns
                )
                
                flaky_tests.append(flaky_data)
        
        return flaky_tests
    
    def analyze_test_performance(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Analyze test performance metrics."""
        if not test_results:
            return {}
        
        execution_times = [r.execution_time for r in test_results if r.execution_time > 0]
        
        if not execution_times:
            return {}
        
        # Calculate performance metrics
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Find slow tests (> 95th percentile or > 1 second)
        sorted_times = sorted(execution_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_time
        
        # Use lower threshold for small datasets
        threshold = max(p95_time, 0.5) if len(execution_times) > 5 else 0.5
        
        slow_tests = [
            r for r in test_results 
            if r.execution_time > threshold
        ]
        
        return {
            'average_execution_time': avg_time,
            'max_execution_time': max_time,
            'min_execution_time': min_time,
            'p95_execution_time': p95_time,
            'slow_tests_count': len(slow_tests),
            'slow_tests': [
                {
                    'test_name': t.test_name,
                    'test_file': t.test_file,
                    'execution_time': t.execution_time
                }
                for t in slow_tests[:10]  # Top 10 slowest
            ]
        }
    
    def generate_test_quality_report(self, project_id: str, 
                                   test_results: List[TestResult],
                                   coverage_data: TestCoverageData,
                                   flaky_tests: List[FlakyTestData]) -> TestQualityMetrics:
        """Generate comprehensive test quality metrics."""
        if not test_results:
            return TestQualityMetrics(project_id=project_id)
        
        # Basic test metrics
        total_tests = len(test_results)
        passing_tests = sum(1 for r in test_results if r.status == TestStatus.PASSED)
        failing_tests = sum(1 for r in test_results if r.status == TestStatus.FAILED)
        skipped_tests = sum(1 for r in test_results if r.status == TestStatus.SKIPPED)
        
        test_success_rate = (passing_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Performance metrics
        execution_times = [r.execution_time for r in test_results if r.execution_time > 0]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Calculate test maintainability score (0-100)
        maintainability_score = self._calculate_test_maintainability_score(
            test_success_rate, coverage_data.coverage_percentage, len(flaky_tests), total_tests
        )
        
        return TestQualityMetrics(
            project_id=project_id,
            total_tests=total_tests,
            passing_tests=passing_tests,
            failing_tests=failing_tests,
            skipped_tests=skipped_tests,
            flaky_tests=len(flaky_tests),
            test_success_rate=test_success_rate,
            average_execution_time=avg_execution_time,
            code_coverage=coverage_data.coverage_percentage,
            branch_coverage=coverage_data.branch_coverage_percentage,
            test_density=0.0,  # Would need LOC count
            assertion_density=0.0,  # Would need assertion analysis
            test_maintainability_score=maintainability_score
        )
    
    def _calculate_test_maintainability_score(self, success_rate: float, coverage: float, 
                                            flaky_count: int, total_tests: int) -> float:
        """Calculate test maintainability score (0-100)."""
        # Base score from success rate and coverage
        base_score = (success_rate * 0.4) + (coverage * 0.4)
        
        # Penalty for flaky tests
        flaky_penalty = (flaky_count / total_tests) * 20 if total_tests > 0 else 0
        
        # Bonus for having tests at all
        test_bonus = min(total_tests / 10, 1) * 20  # Up to 20 points for having tests
        
        score = base_score + test_bonus - flaky_penalty
        return max(0, min(100, score))


class TestQualityVisitor(ast.NodeVisitor):
    """AST visitor for analyzing test code quality."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.test_functions: List[TestFunction] = []
        self.setup_methods: List[str] = []
        self.teardown_methods: List[str] = []
        self.fixtures: List[str] = []
        self.current_class = None
        self.assertion_patterns = [
            r'assert\s+',
            r'self\.assert\w+',
            r'pytest\.raises',
            r'expect\(',
        ]
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions to find test classes."""
        old_class = self.current_class
        self.current_class = node.name
        
        # Check if it's a test class
        if self._is_test_class(node):
            # Look for setup/teardown methods
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name in ['setUp', 'setup_method', 'setup_class']:
                        self.setup_methods.append(f"{self.current_class}.{item.name}")
                    elif item.name in ['tearDown', 'teardown_method', 'teardown_class']:
                        self.teardown_methods.append(f"{self.current_class}.{item.name}")
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions to find test functions."""
        if self._is_test_function(node):
            test_func = TestFunction(
                name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                test_type=self._determine_test_type(node),
                assertions_count=self._count_assertions(node),
                complexity=self._calculate_complexity(node),
                docstring=ast.get_docstring(node)
            )
            
            self.test_functions.append(test_func)
        
        # Check for fixtures (pytest)
        if self._is_fixture(node):
            fixture_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
            self.fixtures.append(fixture_name)
        
        self.generic_visit(node)
    
    def _is_test_class(self, node: ast.ClassDef) -> bool:
        """Check if class is a test class."""
        # Check class name
        if node.name.startswith('Test') or node.name.endswith('Test'):
            return True
        
        # Check inheritance
        for base in node.bases:
            if isinstance(base, ast.Name) and 'Test' in base.id:
                return True
            elif isinstance(base, ast.Attribute) and 'TestCase' in base.attr:
                return True
        
        return False
    
    def _is_test_function(self, node: ast.FunctionDef) -> bool:
        """Check if function is a test function."""
        # Check function name
        if node.name.startswith('test_'):
            return True
        
        # Check decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in ['test']:
                return True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id in ['pytest.mark.parametrize']:
                    return True
        
        return False
    
    def _is_fixture(self, node: ast.FunctionDef) -> bool:
        """Check if function is a pytest fixture."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'fixture':
                return True
            elif isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture':
                return True
        return False
    
    def _determine_test_type(self, node: ast.FunctionDef) -> TestType:
        """Determine the type of test based on name and content."""
        name_lower = node.name.lower()
        
        if 'integration' in name_lower or 'e2e' in name_lower:
            return TestType.INTEGRATION
        elif 'performance' in name_lower or 'perf' in name_lower:
            return TestType.PERFORMANCE
        elif 'security' in name_lower or 'auth' in name_lower:
            return TestType.SECURITY
        elif 'functional' in name_lower:
            return TestType.FUNCTIONAL
        else:
            return TestType.UNIT
    
    def _count_assertions(self, node: ast.FunctionDef) -> int:
        """Count assertions in test function."""
        assertion_count = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assertion_count += 1
            elif isinstance(child, ast.Call):
                # Check for assertion method calls
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr.startswith('assert'):
                        assertion_count += 1
                elif isinstance(child.func, ast.Name):
                    if child.func.id in ['expect', 'should']:
                        assertion_count += 1
        
        return assertion_count
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of test function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def get_test_suite(self) -> TestSuite:
        """Get the analyzed test suite."""
        return TestSuite(
            name=Path(self.file_path).stem,
            file_path=self.file_path,
            test_functions=self.test_functions,
            setup_methods=self.setup_methods,
            teardown_methods=self.teardown_methods,
            fixtures=self.fixtures
        )