"""
Unit tests for Quality Metrics Collector

Tests comprehensive metric gathering, time-series storage, trend analysis,
and quality gate enforcement functionality.
"""

import pytest
import asyncio
import sqlite3
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from app.services.quality_metrics_collector import (
    QualityMetricsCollector,
    CodeAnalysisResult,
    TestMetricsResult,
    SecurityAnalysisResult,
    PerformanceAnalysisResult,
    QualityGateResult
)
from app.models.quality import QualityMetrics, QualityTrend
from app.core.quality_config import QualityThresholds


class TestQualityMetricsCollector:
    """Test suite for QualityMetricsCollector."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create the database schema
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # Create required tables
        cursor.execute("""
            CREATE TABLE quality_metrics (
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
        
        cursor.execute("""
            CREATE TABLE quality_trends (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                trend_direction TEXT,
                change_percentage REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE quality_gates (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                gate_name TEXT NOT NULL,
                criteria TEXT NOT NULL,
                passed BOOLEAN NOT NULL,
                score REAL,
                failed_criteria TEXT,
                warnings TEXT,
                evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE quality_standards (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                standard_name TEXT NOT NULL,
                standard_type TEXT NOT NULL,
                configuration TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        yield path
        
        # Cleanup
        os.unlink(path)
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with sample code."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create sample Python files
            (project_path / "main.py").write_text("""
# Main application module
import os
import sys
from typing import List, Dict

class DataProcessor:
    '''Process data with various methods.'''
    
    def __init__(self):
        self.data = []
    
    def process_data(self, items: List[str]) -> Dict[str, int]:
        '''Process a list of items and return counts.'''
        result = {}
        for item in items:
            if item in result:
                result[item] += 1
            else:
                result[item] = 1
        return result
    
    def complex_method(self, x, y, z):
        '''A method with high cyclomatic complexity.'''
        if x > 0:
            if y > 0:
                if z > 0:
                    return x + y + z
                else:
                    return x + y
            else:
                if z > 0:
                    return x + z
                else:
                    return x
        else:
            if y > 0:
                if z > 0:
                    return y + z
                else:
                    return y
            else:
                return z if z > 0 else 0

def main():
    processor = DataProcessor()
    data = ['a', 'b', 'a', 'c', 'b', 'a']
    result = processor.process_data(data)
    print(result)

if __name__ == "__main__":
    main()
""")
            
            (project_path / "utils.py").write_text("""
# Utility functions
import hashlib
import pickle
import subprocess

def insecure_hash(data):
    '''Use insecure MD5 hash - security issue.'''
    return hashlib.md5(data.encode()).hexdigest()

def dangerous_pickle(data):
    '''Dangerous pickle loading - security issue.'''
    return pickle.loads(data)

def shell_command(cmd):
    '''Execute shell command - potential security issue.'''
    return subprocess.call(cmd, shell=True)

def inefficient_loop(items):
    '''Inefficient nested loop - performance issue.'''
    result = []
    for i in items:
        for j in items:
            if i != j:
                result.append((i, j))
    return result
""")
            
            (project_path / "test_main.py").write_text("""
# Test file for main module
import unittest
from main import DataProcessor

class TestDataProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = DataProcessor()
    
    def test_process_data(self):
        '''Test data processing functionality.'''
        data = ['a', 'b', 'a']
        result = self.processor.process_data(data)
        self.assertEqual(result['a'], 2)
        self.assertEqual(result['b'], 1)
    
    def test_complex_method(self):
        '''Test complex method with various inputs.'''
        self.assertEqual(self.processor.complex_method(1, 1, 1), 3)
        self.assertEqual(self.processor.complex_method(0, 0, 0), 0)
        self.assertEqual(self.processor.complex_method(-1, 1, 1), 2)

if __name__ == '__main__':
    unittest.main()
""")
            
            yield str(project_path)
    
    @pytest.fixture
    def collector(self, temp_db):
        """Create a QualityMetricsCollector instance with temporary database."""
        return QualityMetricsCollector(db_path=temp_db)
    
    @pytest.mark.asyncio
    async def test_collect_comprehensive_metrics(self, collector, temp_project_dir):
        """Test comprehensive metrics collection."""
        project_id = "test_project_1"
        
        metrics = await collector.collect_comprehensive_metrics(project_id, temp_project_dir)
        
        assert metrics.project_id == project_id
        assert metrics.timestamp is not None
        assert metrics.lines_of_code > 0
        assert metrics.cyclomatic_complexity > 0
        assert metrics.maintainability_index >= 0
        assert metrics.technical_debt_ratio >= 0
        assert metrics.security_score >= 0
        assert metrics.performance_score >= 0
        assert metrics.duplicate_code_ratio >= 0
        assert metrics.comment_ratio >= 0
    
    @pytest.mark.asyncio
    async def test_collect_code_metrics(self, collector, temp_project_dir):
        """Test code metrics collection."""
        code_metrics = await collector._collect_code_metrics(temp_project_dir)
        
        assert isinstance(code_metrics, CodeAnalysisResult)
        assert code_metrics.lines_of_code > 50  # Should have substantial code
        assert code_metrics.function_count >= 4  # At least 4 functions in sample
        assert code_metrics.class_count >= 1   # At least 1 class
        assert code_metrics.cyclomatic_complexity > 1  # Complex method should increase this
        assert 0 <= code_metrics.comment_ratio <= 1
        assert 0 <= code_metrics.duplicate_code_ratio <= 1
        assert 0 <= code_metrics.maintainability_index <= 100
    
    @pytest.mark.asyncio
    async def test_collect_test_metrics(self, collector, temp_project_dir):
        """Test test metrics collection."""
        test_metrics = await collector._collect_test_metrics(temp_project_dir)
        
        assert isinstance(test_metrics, TestMetricsResult)
        assert test_metrics.test_count >= 2  # Should find test methods
        assert test_metrics.assertion_count >= 3  # Should find assertions
        assert 0 <= test_metrics.test_quality_score <= 100
        assert test_metrics.flaky_test_count >= 0
        assert test_metrics.slow_test_count >= 0
    
    @pytest.mark.asyncio
    async def test_collect_security_metrics(self, collector, temp_project_dir):
        """Test security metrics collection."""
        security_metrics = await collector._collect_security_metrics(temp_project_dir)
        
        assert isinstance(security_metrics, SecurityAnalysisResult)
        assert security_metrics.vulnerability_count > 0  # Sample has security issues
        assert security_metrics.high_vulnerabilities > 0  # MD5 and pickle issues
        assert 0 <= security_metrics.security_score <= 100
        assert security_metrics.critical_vulnerabilities >= 0
        assert security_metrics.medium_vulnerabilities >= 0
        assert security_metrics.low_vulnerabilities >= 0
    
    @pytest.mark.asyncio
    async def test_collect_performance_metrics(self, collector, temp_project_dir):
        """Test performance metrics collection."""
        perf_metrics = await collector._collect_performance_metrics(temp_project_dir)
        
        assert isinstance(perf_metrics, PerformanceAnalysisResult)
        # The sample code has subprocess.call which should be detected as blocking operation
        assert perf_metrics.blocking_operation_count > 0  # Sample has subprocess.call
        assert 0 <= perf_metrics.performance_score <= 100
        assert perf_metrics.memory_leak_indicators >= 0
        assert perf_metrics.inefficient_query_count >= 0
        assert perf_metrics.bottleneck_count >= 0
    
    @pytest.mark.asyncio
    async def test_store_metrics(self, collector, temp_db):
        """Test metrics storage in database."""
        metrics = QualityMetrics(
            project_id="test_project",
            code_coverage=85.5,
            cyclomatic_complexity=7.2,
            maintainability_index=78.3,
            technical_debt_ratio=0.03,
            test_quality_score=82.1,
            security_score=91.7,
            performance_score=76.4,
            lines_of_code=1250,
            duplicate_code_ratio=0.02,
            comment_ratio=0.15
        )
        
        await collector._store_metrics(metrics)
        
        # Verify storage
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quality_metrics WHERE project_id = ?", (metrics.project_id,))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        assert row[1] == metrics.project_id  # project_id
        assert row[3] == metrics.code_coverage  # code_coverage
        assert row[4] == metrics.cyclomatic_complexity  # cyclomatic_complexity
    
    @pytest.mark.asyncio
    async def test_update_trend_data(self, collector, temp_db):
        """Test trend data calculation and storage."""
        project_id = "test_project"
        
        # Store initial metrics
        initial_metrics = QualityMetrics(
            project_id=project_id,
            code_coverage=80.0,
            cyclomatic_complexity=8.0,
            maintainability_index=75.0,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        await collector._store_metrics(initial_metrics)
        
        # Store updated metrics
        updated_metrics = QualityMetrics(
            project_id=project_id,
            code_coverage=85.0,  # Improved
            cyclomatic_complexity=9.0,  # Worsened
            maintainability_index=75.0,  # Stable
            timestamp=datetime.now(timezone.utc)
        )
        await collector._store_metrics(updated_metrics)
        await collector._update_trend_data(updated_metrics)
        
        # Check trend data
        trends = await collector.get_quality_trends(project_id)
        
        assert len(trends) > 0
        
        # Find specific trends
        coverage_trend = next((t for t in trends if t.metric_name == 'code_coverage'), None)
        complexity_trend = next((t for t in trends if t.metric_name == 'cyclomatic_complexity'), None)
        maintainability_trend = next((t for t in trends if t.metric_name == 'maintainability_index'), None)
        
        assert coverage_trend is not None
        assert coverage_trend.trend_direction == 'up'
        assert coverage_trend.change_percentage > 0
        
        assert complexity_trend is not None
        assert complexity_trend.trend_direction == 'up'  # Higher complexity is worse, but trend is "up"
        
        assert maintainability_trend is not None
        assert maintainability_trend.trend_direction == 'stable'
    
    @pytest.mark.asyncio
    async def test_evaluate_quality_gates(self, collector, temp_db):
        """Test quality gate evaluation."""
        project_id = "test_project"
        
        # Insert default quality standards
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quality_standards 
            (id, project_id, standard_name, standard_type, configuration, is_active)
            VALUES (?, NULL, ?, ?, ?, ?)
        """, (
            "default_quality",
            "Default Quality Standards",
            "quality",
            '{"min_coverage": 80.0, "max_complexity": 10, "min_maintainability": 70.0, "max_technical_debt_ratio": 0.05, "min_test_quality": 75.0, "min_security_score": 85.0, "max_duplicate_ratio": 0.03}',
            True
        ))
        conn.commit()
        conn.close()
        
        # Test passing metrics
        passing_metrics = QualityMetrics(
            project_id=project_id,
            code_coverage=85.0,
            cyclomatic_complexity=8.0,
            maintainability_index=75.0,
            technical_debt_ratio=0.03,
            test_quality_score=80.0,
            security_score=90.0
        )
        
        result = await collector.evaluate_quality_gates(project_id, passing_metrics)
        
        assert isinstance(result, QualityGateResult)
        assert result.passed is True
        assert len(result.failed_criteria) == 0
        assert result.score > 0
        
        # Test failing metrics
        failing_metrics = QualityMetrics(
            project_id=project_id,
            code_coverage=70.0,  # Below threshold
            cyclomatic_complexity=15.0,  # Above threshold
            maintainability_index=60.0,  # Below threshold
            technical_debt_ratio=0.08,  # Above threshold
            test_quality_score=70.0,  # Below threshold
            security_score=80.0  # Below threshold
        )
        
        result = await collector.evaluate_quality_gates(project_id, failing_metrics)
        
        assert result.passed is False
        assert len(result.failed_criteria) > 0
        assert "Code coverage" in str(result.failed_criteria)
        assert "Cyclomatic complexity" in str(result.failed_criteria)
    
    @pytest.mark.asyncio
    async def test_get_metrics_history(self, collector, temp_db):
        """Test retrieving metrics history."""
        project_id = "test_project"
        
        # Store multiple metrics over time
        timestamps = [
            datetime.now(timezone.utc) - timedelta(days=5),
            datetime.now(timezone.utc) - timedelta(days=3),
            datetime.now(timezone.utc) - timedelta(days=1),
            datetime.now(timezone.utc)
        ]
        
        for i, timestamp in enumerate(timestamps):
            metrics = QualityMetrics(
                project_id=project_id,
                code_coverage=80.0 + i * 2,  # Improving over time
                cyclomatic_complexity=10.0 - i * 0.5,  # Improving over time
                timestamp=timestamp
            )
            await collector._store_metrics(metrics)
        
        # Get history
        history = await collector.get_metrics_history(project_id, days=7)
        
        assert len(history) == 4
        assert all(m.project_id == project_id for m in history)
        
        # Check chronological order
        for i in range(1, len(history)):
            assert history[i].timestamp >= history[i-1].timestamp
        
        # Check improvement trend
        coverages = [m.code_coverage for m in history if m.code_coverage is not None]
        assert coverages == sorted(coverages)  # Should be increasing
    
    def test_calculate_cyclomatic_complexity(self, collector):
        """Test cyclomatic complexity calculation."""
        import ast
        
        # Simple function
        simple_code = """
def simple_function(x):
    return x + 1
"""
        tree = ast.parse(simple_code)
        func_node = tree.body[0]
        complexity = collector._calculate_cyclomatic_complexity(func_node)
        assert complexity == 1  # Base complexity
        
        # Complex function with conditionals
        complex_code = """
def complex_function(x, y):
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x
    elif x < 0:
        return -x
    else:
        return 0
"""
        tree = ast.parse(complex_code)
        func_node = tree.body[0]
        complexity = collector._calculate_cyclomatic_complexity(func_node)
        assert complexity > 1  # Should have higher complexity
    
    def test_calculate_duplicate_ratio(self, collector):
        """Test duplicate code ratio calculation."""
        # No duplicates
        unique_blocks = ["def func1(): pass", "def func2(): return 1", "def func3(): return 2"]
        ratio = collector._calculate_duplicate_ratio(unique_blocks)
        assert ratio == 0.0
        
        # Some duplicates
        with_duplicates = ["def func(): pass", "def func(): pass", "def other(): return 1"]
        ratio = collector._calculate_duplicate_ratio(with_duplicates)
        assert ratio > 0.0
        assert ratio <= 1.0
    
    def test_calculate_maintainability_index(self, collector):
        """Test maintainability index calculation."""
        # High maintainability (low complexity, good comments)
        index = collector._calculate_maintainability_index(
            complexity=2.0, lines_of_code=100, comment_ratio=0.2
        )
        assert 0 <= index <= 100
        
        # Low maintainability (high complexity, no comments)
        low_index = collector._calculate_maintainability_index(
            complexity=20.0, lines_of_code=5000, comment_ratio=0.0
        )
        assert 0 <= low_index <= 100
        assert low_index < index  # Should be lower than high maintainability
    
    def test_calculate_technical_debt_ratio(self, collector):
        """Test technical debt ratio calculation."""
        # Low debt scenario
        good_code = CodeAnalysisResult(1000, 5.0, 80.0, 0.02, 0.15, 50, 10, 20)
        good_tests = TestMetricsResult(85.0, 30, 90, 85.0, 0, 0)
        good_security = SecurityAnalysisResult(90.0, 2, 0, 1, 1, 0)
        
        debt_ratio = collector._calculate_technical_debt_ratio(good_code, good_tests, good_security)
        assert 0 <= debt_ratio <= 1
        
        # High debt scenario
        bad_code = CodeAnalysisResult(1000, 25.0, 40.0, 0.15, 0.05, 50, 10, 20)
        bad_tests = TestMetricsResult(40.0, 5, 10, 30.0, 5, 3)
        bad_security = SecurityAnalysisResult(50.0, 20, 5, 8, 5, 2)
        
        high_debt_ratio = collector._calculate_technical_debt_ratio(bad_code, bad_tests, bad_security)
        assert high_debt_ratio > debt_ratio  # Should be higher debt
    
    def test_calculate_test_quality_score(self, collector):
        """Test test quality score calculation."""
        # Good test quality
        score = collector._calculate_test_quality_score(
            test_count=50, assertion_count=150, coverage=85.0
        )
        assert 0 <= score <= 100
        
        # Poor test quality
        poor_score = collector._calculate_test_quality_score(
            test_count=5, assertion_count=10, coverage=30.0
        )
        assert poor_score < score
        
        # No tests
        no_tests_score = collector._calculate_test_quality_score(
            test_count=0, assertion_count=0, coverage=0.0
        )
        assert no_tests_score == 0.0
    
    @pytest.mark.asyncio
    async def test_get_quality_trends_with_filters(self, collector, temp_db):
        """Test getting quality trends with metric name filter."""
        project_id = "test_project"
        
        # Store trend data for multiple metrics
        trends_data = [
            ("code_coverage", 80.0, "up", 5.0),
            ("code_coverage", 85.0, "up", 6.25),
            ("cyclomatic_complexity", 8.0, "down", -10.0),
            ("security_score", 90.0, "stable", 0.5)
        ]
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        for metric_name, value, direction, change in trends_data:
            cursor.execute("""
                INSERT INTO quality_trends 
                (id, project_id, metric_name, metric_value, timestamp, trend_direction, change_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"trend_{metric_name}_{value}",
                project_id,
                metric_name,
                value,
                datetime.now(timezone.utc).isoformat(),
                direction,
                change
            ))
        
        conn.commit()
        conn.close()
        
        # Get all trends
        all_trends = await collector.get_quality_trends(project_id)
        assert len(all_trends) == 4
        
        # Get filtered trends
        coverage_trends = await collector.get_quality_trends(project_id, metric_name="code_coverage")
        assert len(coverage_trends) == 2
        assert all(t.metric_name == "code_coverage" for t in coverage_trends)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_collection(self, collector):
        """Test error handling during metrics collection."""
        # Test with non-existent directory
        metrics = await collector.collect_comprehensive_metrics("test_project", "/non/existent/path")
        
        # Should return metrics object with default values, not crash
        assert metrics.project_id == "test_project"
        assert metrics.lines_of_code == 0 or metrics.lines_of_code is None
    
    @pytest.mark.asyncio
    async def test_concurrent_metrics_collection(self, collector, temp_project_dir):
        """Test concurrent metrics collection for multiple projects."""
        projects = [
            ("project_1", temp_project_dir),
            ("project_2", temp_project_dir),
            ("project_3", temp_project_dir)
        ]
        
        # Collect metrics concurrently
        tasks = [
            collector.collect_comprehensive_metrics(project_id, project_path)
            for project_id, project_path in projects
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for i, metrics in enumerate(results):
            assert metrics.project_id == f"project_{i+1}"
            assert metrics.lines_of_code > 0


if __name__ == "__main__":
    pytest.main([__file__])