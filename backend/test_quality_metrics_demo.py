#!/usr/bin/env python3
"""
Demo script for Quality Metrics Collector

This script demonstrates the comprehensive quality metrics collection,
trend analysis, and quality gate enforcement functionality.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

from app.services.quality_metrics_collector import QualityMetricsCollector
from app.models.quality import QualityMetrics


def create_sample_project():
    """Create a sample project with various code quality issues."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)
    
    # Create main application file
    (project_path / "main.py").write_text("""
# Main application module
import os
import sys
import hashlib  # Security issue: using MD5
import pickle   # Security issue: dangerous pickle
from typing import List, Dict

class DataProcessor:
    '''Process data with various methods.'''
    
    def __init__(self):
        self.data = []
        self.cache = {}  # Potential memory leak
    
    def process_data(self, items: List[str]) -> Dict[str, int]:
        '''Process a list of items and return counts.'''
        result = {}
        # Inefficient loop pattern
        for item in items:
            if item in result:
                result[item] += 1
            else:
                result[item] = 1
        return result
    
    def complex_method(self, x, y, z, a, b):
        '''A method with high cyclomatic complexity.'''
        if x > 0:
            if y > 0:
                if z > 0:
                    if a > 0:
                        if b > 0:
                            return x + y + z + a + b
                        else:
                            return x + y + z + a
                    else:
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
    
    def insecure_hash(self, data):
        '''Use insecure MD5 hash.'''
        return hashlib.md5(data.encode()).hexdigest()
    
    def dangerous_deserialize(self, data):
        '''Dangerous pickle loading.'''
        return pickle.loads(data)

def main():
    processor = DataProcessor()
    data = ['a', 'b', 'a', 'c', 'b', 'a']
    result = processor.process_data(data)
    print(result)

if __name__ == "__main__":
    main()
""")
    
    # Create utility module with more issues
    (project_path / "utils.py").write_text("""
# Utility functions with various quality issues
import subprocess
import time

def shell_command(cmd):
    '''Execute shell command - security issue.'''
    return subprocess.call(cmd, shell=True)

def inefficient_search(items, target):
    '''Inefficient nested loop.'''
    result = []
    for i in items:
        for j in items:
            if i == target and j == target:
                result.append((i, j))
    return result

def blocking_operation():
    '''Blocking operation that could cause performance issues.'''
    time.sleep(1)
    return "done"

# Duplicate function (same as in main.py)
def process_data(items):
    result = {}
    for item in items:
        if item in result:
            result[item] += 1
        else:
            result[item] = 1
    return result
""")
    
    # Create test file
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
        self.assertIn('a', result)
        self.assertIn('b', result)
    
    def test_complex_method(self):
        '''Test complex method with various inputs.'''
        self.assertEqual(self.processor.complex_method(1, 1, 1, 1, 1), 5)
        self.assertEqual(self.processor.complex_method(0, 0, 0, 0, 0), 0)
        self.assertEqual(self.processor.complex_method(-1, 1, 1, 0, 0), 2)
        self.assertIsInstance(self.processor.complex_method(1, 2, 3, 4, 5), int)
    
    def test_insecure_hash(self):
        '''Test hash function.'''
        result = self.processor.insecure_hash("test")
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)  # MD5 hash length

if __name__ == '__main__':
    unittest.main()
""")
    
    return str(project_path)


async def demonstrate_quality_metrics():
    """Demonstrate quality metrics collection and analysis."""
    print("🔍 Quality Metrics Collector Demo")
    print("=" * 50)
    
    # Create sample project
    print("\n📁 Creating sample project with quality issues...")
    project_path = create_sample_project()
    project_id = "demo_project"
    
    # Initialize collector
    collector = QualityMetricsCollector()
    
    # Collect initial metrics
    print("\n📊 Collecting comprehensive quality metrics...")
    metrics1 = await collector.collect_comprehensive_metrics(project_id, project_path)
    
    print(f"\n📈 Initial Quality Metrics:")
    print(f"  • Lines of Code: {metrics1.lines_of_code}")
    print(f"  • Code Coverage: {metrics1.code_coverage:.1f}%")
    print(f"  • Cyclomatic Complexity: {metrics1.cyclomatic_complexity:.2f}")
    print(f"  • Maintainability Index: {metrics1.maintainability_index:.1f}")
    print(f"  • Technical Debt Ratio: {metrics1.technical_debt_ratio:.3f}")
    print(f"  • Test Quality Score: {metrics1.test_quality_score:.1f}")
    print(f"  • Security Score: {metrics1.security_score:.1f}")
    print(f"  • Performance Score: {metrics1.performance_score:.1f}")
    print(f"  • Duplicate Code Ratio: {metrics1.duplicate_code_ratio:.3f}")
    print(f"  • Comment Ratio: {metrics1.comment_ratio:.3f}")
    
    # Evaluate quality gates
    print("\n🚪 Evaluating quality gates...")
    gate_result = await collector.evaluate_quality_gates(project_id, metrics1)
    
    print(f"\n🎯 Quality Gate Results:")
    print(f"  • Status: {'✅ PASSED' if gate_result.passed else '❌ FAILED'}")
    print(f"  • Overall Score: {gate_result.score:.1f}/100")
    
    if gate_result.failed_criteria:
        print(f"  • Failed Criteria:")
        for criteria in gate_result.failed_criteria:
            print(f"    - {criteria}")
    
    if gate_result.warnings:
        print(f"  • Warnings:")
        for warning in gate_result.warnings:
            print(f"    - {warning}")
    
    # Simulate improvement by adding better code
    print("\n🔧 Simulating code improvements...")
    
    # Add a better implementation
    improved_file = Path(project_path) / "improved.py"
    improved_file.write_text("""
# Improved implementation with better practices
from typing import List, Dict, Counter
import hashlib

class ImprovedDataProcessor:
    '''
    Improved data processor with better practices.
    
    This class demonstrates:
    - Better documentation
    - Type hints
    - Secure hashing
    - Efficient algorithms
    '''
    
    def __init__(self):
        self.data: List[str] = []
    
    def process_data_efficiently(self, items: List[str]) -> Dict[str, int]:
        '''
        Process items efficiently using Counter.
        
        Args:
            items: List of items to count
            
        Returns:
            Dictionary with item counts
        '''
        return dict(Counter(items))
    
    def secure_hash(self, data: str) -> str:
        '''
        Create secure SHA-256 hash.
        
        Args:
            data: String to hash
            
        Returns:
            Hexadecimal hash string
        '''
        return hashlib.sha256(data.encode()).hexdigest()
    
    def simple_method(self, x: int, y: int) -> int:
        '''Simple method with low complexity.'''
        return x + y if x > 0 and y > 0 else 0
""")
    
    # Add comprehensive tests
    improved_test = Path(project_path) / "test_improved.py"
    improved_test.write_text("""
# Comprehensive tests for improved module
import unittest
from improved import ImprovedDataProcessor

class TestImprovedDataProcessor(unittest.TestCase):
    '''Comprehensive test suite for ImprovedDataProcessor.'''
    
    def setUp(self):
        '''Set up test fixtures.'''
        self.processor = ImprovedDataProcessor()
    
    def test_process_data_efficiently(self):
        '''Test efficient data processing.'''
        data = ['a', 'b', 'a', 'c', 'b', 'a']
        result = self.processor.process_data_efficiently(data)
        
        self.assertEqual(result['a'], 3)
        self.assertEqual(result['b'], 2)
        self.assertEqual(result['c'], 1)
        self.assertEqual(len(result), 3)
    
    def test_process_data_empty(self):
        '''Test processing empty data.'''
        result = self.processor.process_data_efficiently([])
        self.assertEqual(result, {})
    
    def test_secure_hash(self):
        '''Test secure hash function.'''
        result = self.processor.secure_hash("test")
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)  # SHA-256 hash length
        
        # Test consistency
        result2 = self.processor.secure_hash("test")
        self.assertEqual(result, result2)
    
    def test_simple_method(self):
        '''Test simple method with various inputs.'''
        self.assertEqual(self.processor.simple_method(1, 2), 3)
        self.assertEqual(self.processor.simple_method(-1, 2), 0)
        self.assertEqual(self.processor.simple_method(1, -2), 0)
        self.assertEqual(self.processor.simple_method(0, 0), 0)
    
    def test_initialization(self):
        '''Test processor initialization.'''
        self.assertIsInstance(self.processor.data, list)
        self.assertEqual(len(self.processor.data), 0)

if __name__ == '__main__':
    unittest.main()
""")
    
    # Collect improved metrics
    print("\n📊 Collecting metrics after improvements...")
    metrics2 = await collector.collect_comprehensive_metrics(project_id, project_path)
    
    print(f"\n📈 Improved Quality Metrics:")
    print(f"  • Lines of Code: {metrics2.lines_of_code} (was {metrics1.lines_of_code})")
    print(f"  • Code Coverage: {metrics2.code_coverage:.1f}% (was {metrics1.code_coverage:.1f}%)")
    print(f"  • Cyclomatic Complexity: {metrics2.cyclomatic_complexity:.2f} (was {metrics1.cyclomatic_complexity:.2f})")
    print(f"  • Maintainability Index: {metrics2.maintainability_index:.1f} (was {metrics1.maintainability_index:.1f})")
    print(f"  • Technical Debt Ratio: {metrics2.technical_debt_ratio:.3f} (was {metrics1.technical_debt_ratio:.3f})")
    print(f"  • Test Quality Score: {metrics2.test_quality_score:.1f} (was {metrics1.test_quality_score:.1f})")
    print(f"  • Security Score: {metrics2.security_score:.1f} (was {metrics1.security_score:.1f})")
    print(f"  • Performance Score: {metrics2.performance_score:.1f} (was {metrics1.performance_score:.1f})")
    
    # Show trends
    print("\n📈 Quality Trends Analysis:")
    trends = await collector.get_quality_trends(project_id)
    
    for trend in trends:
        direction_emoji = {"up": "📈", "down": "📉", "stable": "➡️"}.get(trend.trend_direction, "❓")
        print(f"  • {trend.metric_name}: {direction_emoji} {trend.change_percentage:+.1f}%")
    
    # Re-evaluate quality gates
    print("\n🚪 Re-evaluating quality gates...")
    gate_result2 = await collector.evaluate_quality_gates(project_id, metrics2)
    
    print(f"\n🎯 Updated Quality Gate Results:")
    print(f"  • Status: {'✅ PASSED' if gate_result2.passed else '❌ FAILED'}")
    print(f"  • Overall Score: {gate_result2.score:.1f}/100 (was {gate_result.score:.1f}/100)")
    
    if gate_result2.failed_criteria:
        print(f"  • Remaining Failed Criteria:")
        for criteria in gate_result2.failed_criteria:
            print(f"    - {criteria}")
    else:
        print("  • ✅ All quality gates now passing!")
    
    # Show metrics history
    print("\n📊 Metrics History:")
    history = await collector.get_metrics_history(project_id)
    
    print(f"  • Total measurements: {len(history)}")
    if len(history) >= 2:
        latest = history[-1]
        previous = history[-2]
        
        coverage_change = latest.code_coverage - previous.code_coverage if latest.code_coverage and previous.code_coverage else 0
        complexity_change = latest.cyclomatic_complexity - previous.cyclomatic_complexity if latest.cyclomatic_complexity and previous.cyclomatic_complexity else 0
        
        print(f"  • Coverage trend: {coverage_change:+.1f}%")
        print(f"  • Complexity trend: {complexity_change:+.2f}")
    
    print(f"\n✅ Demo completed! Sample project created at: {project_path}")
    print("\n🎉 Quality Metrics Collector successfully demonstrated:")
    print("  • Comprehensive metrics collection")
    print("  • Time-series storage and trend analysis")
    print("  • Quality gate enforcement")
    print("  • Historical tracking and comparison")


if __name__ == "__main__":
    asyncio.run(demonstrate_quality_metrics())