"""
Unit tests for the recommendation engine.

Tests cover pattern analysis, duplicate code detection, performance optimization,
and security vulnerability detection with accuracy validation.
"""

import ast
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.services.code_analysis.recommendation_engine import (
    RecommendationEngine,
    DuplicateCodeDetector,
    PerformanceAnalyzer,
    SecurityAnalyzer,
    PatternAnalyzer,
    RecommendationType,
    ImprovementRecommendation,
    CodePattern,
    DuplicateCodeBlock
)
from app.services.code_analysis.base_analyzer import AnalysisContext, AnalysisResult
from app.models.quality import IssueType, Severity


class TestRecommendationEngine:
    """Test the main recommendation engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RecommendationEngine()
        self.context = AnalysisContext(
            project_id="test_project",
            file_path="test_file.py",
            file_content="",
            language="python"
        )
    
    def test_engine_initialization(self):
        """Test recommendation engine initialization."""
        assert self.engine.name == "RecommendationEngine"
        assert self.engine.analysis_type.value == "maintainability"
        assert isinstance(self.engine.duplicate_detector, DuplicateCodeDetector)
        assert isinstance(self.engine.performance_analyzer, PerformanceAnalyzer)
        assert isinstance(self.engine.security_analyzer, SecurityAnalyzer)
        assert isinstance(self.engine.pattern_analyzer, PatternAnalyzer)
    
    def test_configuration(self):
        """Test engine configuration."""
        config = {
            'min_duplicate_lines': 10,
            'min_similarity_threshold': 0.9,
            'max_complexity_threshold': 15
        }
        
        self.engine.configure(config)
        
        assert self.engine.min_duplicate_lines == 10
        assert self.engine.min_similarity_threshold == 0.9
        assert self.engine.max_complexity_threshold == 15
    
    def test_analyze_simple_code(self):
        """Test analysis of simple code without issues."""
        code = """
def simple_function():
    return "hello world"
"""
        self.context.file_content = code
        tree = ast.parse(code)
        result = AnalysisResult(
            analyzer_name="test",
            analysis_type=self.engine.analysis_type,
            context=self.context
        )
        
        self.engine._analyze_ast(tree, result)
        
        # Should have metrics even if no issues found
        assert 'total_recommendations' in result.metrics
        assert result.metrics['total_recommendations'] >= 0
    
    def test_analyze_code_with_duplicates(self):
        """Test analysis of code with duplicate functions."""
        code = """
def function_a():
    x = 1
    y = 2
    z = x + y
    return z

def function_b():
    x = 1
    y = 2
    z = x + y
    return z
"""
        self.context.file_content = code
        tree = ast.parse(code)
        result = AnalysisResult(
            analyzer_name="test",
            analysis_type=self.engine.analysis_type,
            context=self.context
        )
        
        self.engine._analyze_ast(tree, result)
        
        # Should detect duplicate functions
        duplicate_issues = [issue for issue in result.issues 
                          if issue.issue_type == IssueType.DUPLICATION]
        assert len(duplicate_issues) > 0
        assert result.metrics['duplicate_recommendations'] > 0
    
    def test_analyze_code_with_security_issues(self):
        """Test analysis of code with security vulnerabilities."""
        code = """
import os

def dangerous_function(user_input):
    os.system(user_input)
    eval(user_input)
    password = "hardcoded_secret"
    return password
"""
        self.context.file_content = code
        tree = ast.parse(code)
        result = AnalysisResult(
            analyzer_name="test",
            analysis_type=self.engine.analysis_type,
            context=self.context
        )
        
        self.engine._analyze_ast(tree, result)
        
        # Should detect security issues
        security_issues = [issue for issue in result.issues 
                         if issue.issue_type == IssueType.SECURITY]
        assert len(security_issues) > 0
        assert result.metrics['security_recommendations'] > 0
    
    def test_analyze_code_with_performance_issues(self):
        """Test analysis of code with performance problems."""
        code = """
def inefficient_function(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == data[j]:
                result.append(data[i])
    return result
"""
        self.context.file_content = code
        tree = ast.parse(code)
        result = AnalysisResult(
            analyzer_name="test",
            analysis_type=self.engine.analysis_type,
            context=self.context
        )
        
        self.engine._analyze_ast(tree, result)
        
        # Should detect performance issues
        performance_issues = [issue for issue in result.issues 
                            if issue.issue_type == IssueType.PERFORMANCE]
        assert len(performance_issues) > 0
        assert result.metrics['performance_recommendations'] > 0
    
    def test_recommendation_to_issue_conversion(self):
        """Test conversion of recommendations to quality issues."""
        recommendation = ImprovementRecommendation(
            id="test_rec",
            recommendation_type=RecommendationType.DUPLICATE_REMOVAL,
            title="Test recommendation",
            description="Test description",
            file_path="test.py",
            line_number=10,
            severity=Severity.MEDIUM,
            code_after="fixed code"
        )
        
        issue = self.engine._recommendation_to_issue(recommendation)
        
        assert issue.id == "test_rec"
        assert issue.issue_type == IssueType.DUPLICATION
        assert issue.severity == Severity.MEDIUM
        assert issue.category == "duplicate_removal"
        assert issue.line_number == 10
        assert issue.suggested_fix == "fixed code"
        assert issue.auto_fixable is True


class TestDuplicateCodeDetector:
    """Test the duplicate code detection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DuplicateCodeDetector()
        self.context = AnalysisContext(
            project_id="test_project",
            file_path="test_file.py",
            file_content="",
            language="python"
        )
    
    def test_detect_duplicate_functions(self):
        """Test detection of duplicate functions."""
        code = """
def func1():
    a = 1
    b = 2
    c = a + b
    return c

def func2():
    a = 1
    b = 2
    c = a + b
    return c
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.detector.detect_duplicates(tree, self.context)
        
        assert len(recommendations) > 0
        duplicate_rec = recommendations[0]
        assert duplicate_rec.recommendation_type == RecommendationType.DUPLICATE_REMOVAL
        assert "duplicate" in duplicate_rec.title.lower()
    
    def test_normalize_code(self):
        """Test code normalization for duplicate detection."""
        code1 = """
def test():
    # This is a comment
    x = 1    # Another comment
    y = 2
    return x + y
"""
        
        code2 = """
def test():
    x = 1
    y = 2
    return x + y
"""
        
        normalized1 = self.detector._normalize_code(code1)
        normalized2 = self.detector._normalize_code(code2)
        
        # Should be similar after normalization
        assert normalized1 == normalized2
    
    def test_calculate_complexity(self):
        """Test complexity calculation for code blocks."""
        code = """
def complex_function():
    if True:
        for i in range(10):
            try:
                if i > 5:
                    pass
            except Exception:
                pass
"""
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        complexity = self.detector._calculate_complexity(func_node)
        
        # Should detect multiple complexity points
        assert complexity > 1
    
    def test_no_duplicates_detected(self):
        """Test that unique code doesn't generate duplicate recommendations."""
        code = """
def unique_func1():
    return "hello"

def unique_func2():
    return "world"
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.detector.detect_duplicates(tree, self.context)
        
        # Should not detect duplicates in unique code
        assert len(recommendations) == 0
    
    def test_extract_code_blocks(self):
        """Test extraction of code blocks from AST."""
        code = """
class TestClass:
    def method1(self):
        pass
    
    def method2(self):
        if True:
            pass

def function1():
    for i in range(10):
        pass
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        blocks = self.detector._extract_code_blocks(tree, self.context)
        
        # Should extract class, methods, function, and control structures
        assert len(blocks) > 0
        pattern_types = {block.pattern_type for block in blocks}
        assert 'class' in pattern_types
        assert 'function' in pattern_types


class TestPerformanceAnalyzer:
    """Test the performance analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PerformanceAnalyzer()
        self.context = AnalysisContext(
            project_id="test_project",
            file_path="test_file.py",
            file_content="",
            language="python"
        )
    
    def test_detect_nested_loops(self):
        """Test detection of inefficient nested loops."""
        code = """
def nested_loop_function(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            result.append(data[i] + data[j])
    return result
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_performance(tree, self.context)
        
        # Should detect nested loop performance issue
        loop_recommendations = [r for r in recommendations 
                              if "loop" in r.title.lower()]
        assert len(loop_recommendations) > 0
    
    def test_detect_complex_comprehensions(self):
        """Test detection of complex list comprehensions."""
        code = """
def complex_comprehension():
    return [x for x in range(100) if x % 2 == 0 and x % 3 == 0 
            for y in range(x) if y > 10 and y < 50]
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_performance(tree, self.context)
        
        # Should detect complex comprehension
        comp_recommendations = [r for r in recommendations 
                              if "comprehension" in r.title.lower()]
        assert len(comp_recommendations) > 0
    
    def test_detect_inefficient_calls(self):
        """Test detection of inefficient function calls."""
        code = """
def inefficient_calls():
    result = []
    for i in range(1000):
        result.append(expensive_function())
    return result
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_performance(tree, self.context)
        
        # Should detect inefficient call pattern
        call_recommendations = [r for r in recommendations 
                              if "call" in r.title.lower()]
        assert len(call_recommendations) > 0
    
    def test_no_performance_issues(self):
        """Test that efficient code doesn't generate performance recommendations."""
        code = """
def efficient_function(data):
    return sum(data)
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_performance(tree, self.context)
        
        # Should not detect performance issues in efficient code
        assert len(recommendations) == 0


class TestSecurityAnalyzer:
    """Test the security analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SecurityAnalyzer()
        self.context = AnalysisContext(
            project_id="test_project",
            file_path="test_file.py",
            file_content="",
            language="python"
        )
    
    def test_detect_dangerous_calls(self):
        """Test detection of dangerous function calls."""
        code = """
import os

def dangerous_function(user_input):
    os.system(user_input)
    eval(user_input)
    exec(user_input)
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_security(tree, self.context)
        
        # Should detect multiple dangerous calls
        dangerous_recommendations = [r for r in recommendations 
                                   if "dangerous" in r.title.lower()]
        assert len(dangerous_recommendations) >= 3  # os.system, eval, exec
    
    def test_detect_hardcoded_secrets(self):
        """Test detection of hardcoded secrets."""
        code = """
def config():
    password = "secret123"
    api_key = "abc123def456"
    secret = "my_secret_key"
    return password, api_key, secret
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_security(tree, self.context)
        
        # Should detect hardcoded secrets
        secret_recommendations = [r for r in recommendations 
                                if "secret" in r.title.lower()]
        assert len(secret_recommendations) >= 3
    
    def test_detect_missing_input_validation(self):
        """Test detection of missing input validation."""
        code = """
def unvalidated_function(user_input, data):
    # No input validation
    return user_input + data

def validated_function(user_input):
    if not isinstance(user_input, str):
        raise ValueError("Invalid input")
    return user_input.upper()
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_security(tree, self.context)
        
        # Should detect missing validation in first function but not second
        validation_recommendations = [r for r in recommendations 
                                    if "validation" in r.title.lower()]
        assert len(validation_recommendations) >= 1
    
    def test_security_recommendation_severity(self):
        """Test that security recommendations have appropriate severity levels."""
        code = """
def critical_security_issue(user_input):
    eval(user_input)  # Critical
    password = "secret"  # High
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_security(tree, self.context)
        
        # Check severity levels
        critical_recs = [r for r in recommendations if r.severity == Severity.CRITICAL]
        high_recs = [r for r in recommendations if r.severity == Severity.HIGH]
        
        assert len(critical_recs) > 0  # eval should be critical
        assert len(high_recs) > 0     # hardcoded secret should be high


class TestPatternAnalyzer:
    """Test the pattern analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PatternAnalyzer()
        self.context = AnalysisContext(
            project_id="test_project",
            file_path="test_file.py",
            file_content="",
            language="python"
        )
    
    def test_detect_long_functions(self):
        """Test detection of long functions."""
        # Create a long function (more than 50 lines)
        lines = ["def long_function():"]
        lines.extend([f"    line_{i} = {i}" for i in range(60)])
        lines.append("    return sum(locals().values())")
        
        code = "\n".join(lines)
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_patterns(tree, self.context)
        
        # Should detect long function
        long_func_recs = [r for r in recommendations 
                         if "long function" in r.title.lower()]
        assert len(long_func_recs) > 0
    
    def test_detect_complex_conditions(self):
        """Test detection of complex conditional statements."""
        code = """
def complex_conditions(a, b, c, d, e):
    if a > 0 and b < 10 and c == 5 and d != 3 and e >= 7:
        return True
    return False
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_patterns(tree, self.context)
        
        # Should detect complex condition
        complex_cond_recs = [r for r in recommendations 
                           if "complex condition" in r.title.lower()]
        assert len(complex_cond_recs) > 0
    
    def test_detect_too_many_parameters(self):
        """Test detection of functions with too many parameters."""
        code = """
def too_many_params(a, b, c, d, e, f, g, h):
    return a + b + c + d + e + f + g + h
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_patterns(tree, self.context)
        
        # Should detect too many parameters
        param_recs = [r for r in recommendations 
                     if "parameters" in r.title.lower()]
        assert len(param_recs) > 0
    
    def test_detect_god_class(self):
        """Test detection of god classes with too many methods."""
        # Create a class with many methods
        methods = [f"    def method_{i}(self): pass" for i in range(25)]
        code = f"""
class GodClass:
{chr(10).join(methods)}
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_patterns(tree, self.context)
        
        # Should detect god class
        god_class_recs = [r for r in recommendations 
                         if "god class" in r.title.lower()]
        assert len(god_class_recs) > 0
    
    def test_no_pattern_issues(self):
        """Test that well-structured code doesn't generate pattern recommendations."""
        code = """
def simple_function(x, y):
    if x > y:
        return x
    return y

class SimpleClass:
    def method1(self):
        pass
    
    def method2(self):
        pass
"""
        self.context.file_content = code
        tree = ast.parse(code)
        
        recommendations = self.analyzer.analyze_patterns(tree, self.context)
        
        # Should not detect pattern issues in well-structured code
        assert len(recommendations) == 0


class TestImprovementRecommendation:
    """Test the ImprovementRecommendation data class."""
    
    def test_recommendation_creation(self):
        """Test creation of improvement recommendations."""
        rec = ImprovementRecommendation(
            id="test_rec",
            recommendation_type=RecommendationType.DUPLICATE_REMOVAL,
            title="Test Recommendation",
            description="Test description",
            file_path="test.py",
            line_number=10,
            severity=Severity.MEDIUM,
            impact_score=5.0,
            effort_estimate="medium",
            code_before="old code",
            code_after="new code",
            rationale="Test rationale",
            references=["http://example.com"],
            tags=["test", "recommendation"]
        )
        
        assert rec.id == "test_rec"
        assert rec.recommendation_type == RecommendationType.DUPLICATE_REMOVAL
        assert rec.title == "Test Recommendation"
        assert rec.severity == Severity.MEDIUM
        assert rec.impact_score == 5.0
        assert rec.effort_estimate == "medium"
        assert len(rec.references) == 1
        assert len(rec.tags) == 2
        assert isinstance(rec.created_at, datetime)


class TestCodePattern:
    """Test the CodePattern data class."""
    
    def test_pattern_creation(self):
        """Test creation of code patterns."""
        pattern = CodePattern(
            pattern_type="function",
            pattern_hash="abc123",
            file_path="test.py",
            start_line=10,
            end_line=20,
            code_snippet="def test(): pass",
            complexity_score=2.5,
            frequency=3
        )
        
        assert pattern.pattern_type == "function"
        assert pattern.pattern_hash == "abc123"
        assert pattern.start_line == 10
        assert pattern.end_line == 20
        assert pattern.complexity_score == 2.5
        assert pattern.frequency == 3


class TestDuplicateCodeBlock:
    """Test the DuplicateCodeBlock data class."""
    
    def test_duplicate_block_creation(self):
        """Test creation of duplicate code blocks."""
        pattern1 = CodePattern(
            pattern_type="function",
            pattern_hash="abc123",
            file_path="test1.py",
            start_line=10,
            end_line=20,
            code_snippet="def test(): pass"
        )
        
        pattern2 = CodePattern(
            pattern_type="function",
            pattern_hash="abc123",
            file_path="test2.py",
            start_line=15,
            end_line=25,
            code_snippet="def test(): pass"
        )
        
        duplicate = DuplicateCodeBlock(
            pattern_hash="abc123",
            occurrences=[pattern1, pattern2],
            similarity_score=0.95,
            lines_count=10,
            consolidation_suggestion="Extract to common function"
        )
        
        assert duplicate.pattern_hash == "abc123"
        assert len(duplicate.occurrences) == 2
        assert duplicate.similarity_score == 0.95
        assert duplicate.lines_count == 10
        assert duplicate.consolidation_suggestion is not None


if __name__ == "__main__":
    pytest.main([__file__])