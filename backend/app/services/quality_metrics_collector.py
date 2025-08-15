"""
Quality Metrics Collection and Tracking System

This module implements comprehensive quality metrics collection, time-series storage,
trend analysis, and quality gate enforcement for the AITM platform.
"""

import asyncio
import sqlite3
import json
import os
import subprocess
import ast
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from statistics import mean, median

from app.models.quality import QualityMetrics, QualityTrend, Severity
from app.core.quality_config import QualityConfigManager, QualityThresholds


@dataclass
class CodeAnalysisResult:
    """Result of code analysis for metrics collection."""
    lines_of_code: int
    cyclomatic_complexity: float
    maintainability_index: float
    duplicate_code_ratio: float
    comment_ratio: float
    function_count: int
    class_count: int
    import_count: int


@dataclass
class TestMetricsResult:
    """Result of test analysis for quality metrics."""
    test_coverage: float
    test_count: int
    assertion_count: int
    test_quality_score: float
    flaky_test_count: int
    slow_test_count: int


@dataclass
class SecurityAnalysisResult:
    """Result of security analysis for quality metrics."""
    security_score: float
    vulnerability_count: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int


@dataclass
class PerformanceAnalysisResult:
    """Result of performance analysis for quality metrics."""
    performance_score: float
    bottleneck_count: int
    memory_leak_indicators: int
    inefficient_query_count: int
    blocking_operation_count: int


@dataclass
class QualityGateResult:
    """Result of quality gate evaluation."""
    passed: bool
    failed_criteria: List[str]
    warnings: List[str]
    score: float
    details: Dict[str, Any]


class QualityMetricsCollector:
    """
    Comprehensive quality metrics collection and tracking system.
    
    Handles:
    - Code quality metrics collection
    - Test quality analysis
    - Security metrics gathering
    - Performance metrics collection
    - Time-series storage and trend analysis
    - Quality gate enforcement
    """
    
    def __init__(self, db_path: str = "aitm.db"):
        self.db_path = db_path
        self.config_manager = QualityConfigManager(db_path)
        self._ensure_database_schema()
    
    def _ensure_database_schema(self):
        """Ensure required database tables exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Ensure quality_trends table exists
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
            
            # Ensure quality_gates table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_gates (
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
            
            conn.commit()
        finally:
            conn.close()
    
    async def collect_comprehensive_metrics(self, project_id: str, 
                                          project_path: str) -> QualityMetrics:
        """
        Collect comprehensive quality metrics for a project.
        
        Args:
            project_id: Unique identifier for the project
            project_path: File system path to the project
            
        Returns:
            QualityMetrics object with all collected metrics
        """
        try:
            # Collect different types of metrics in parallel
            tasks = [
                self._collect_code_metrics(project_path),
                self._collect_test_metrics(project_path),
                self._collect_security_metrics(project_path),
                self._collect_performance_metrics(project_path)
            ]
            
            code_metrics, test_metrics, security_metrics, perf_metrics = await asyncio.gather(
                *tasks, return_exceptions=True
            )
            
            # Handle any exceptions from parallel collection
            if isinstance(code_metrics, Exception):
                print(f"Code metrics collection failed: {code_metrics}")
                code_metrics = CodeAnalysisResult(0, 0, 0, 0, 0, 0, 0, 0)
            
            if isinstance(test_metrics, Exception):
                print(f"Test metrics collection failed: {test_metrics}")
                test_metrics = TestMetricsResult(0, 0, 0, 0, 0, 0)
            
            if isinstance(security_metrics, Exception):
                print(f"Security metrics collection failed: {security_metrics}")
                security_metrics = SecurityAnalysisResult(0, 0, 0, 0, 0, 0)
            
            if isinstance(perf_metrics, Exception):
                print(f"Performance metrics collection failed: {perf_metrics}")
                perf_metrics = PerformanceAnalysisResult(0, 0, 0, 0, 0)
            
            # Calculate technical debt ratio
            technical_debt_ratio = self._calculate_technical_debt_ratio(
                code_metrics, test_metrics, security_metrics
            )
            
            # Create comprehensive metrics object
            metrics = QualityMetrics(
                project_id=project_id,
                timestamp=datetime.now(timezone.utc),
                code_coverage=test_metrics.test_coverage,
                cyclomatic_complexity=code_metrics.cyclomatic_complexity,
                maintainability_index=code_metrics.maintainability_index,
                technical_debt_ratio=technical_debt_ratio,
                test_quality_score=test_metrics.test_quality_score,
                security_score=security_metrics.security_score,
                performance_score=perf_metrics.performance_score,
                lines_of_code=code_metrics.lines_of_code,
                duplicate_code_ratio=code_metrics.duplicate_code_ratio,
                comment_ratio=code_metrics.comment_ratio
            )
            
            # Store metrics in database
            await self._store_metrics(metrics)
            
            # Update trend data
            await self._update_trend_data(metrics)
            
            return metrics
            
        except Exception as e:
            print(f"Error collecting comprehensive metrics: {e}")
            # Return empty metrics object on error
            return QualityMetrics(project_id=project_id)
    
    async def _collect_code_metrics(self, project_path: str) -> CodeAnalysisResult:
        """Collect code quality metrics from source files."""
        python_files = list(Path(project_path).rglob("*.py"))
        
        if not python_files:
            return CodeAnalysisResult(0, 0, 0, 0, 0, 0, 0, 0)
        
        total_lines = 0
        total_complexity = 0
        total_functions = 0
        total_classes = 0
        total_imports = 0
        comment_lines = 0
        code_blocks = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count lines
                lines = content.split('\n')
                total_lines += len(lines)
                
                # Count comment lines
                comment_lines += sum(1 for line in lines 
                                   if line.strip().startswith('#') or 
                                      line.strip().startswith('"""') or
                                      line.strip().startswith("'''"))
                
                # Parse AST for complexity analysis
                try:
                    tree = ast.parse(content)
                    
                    # Count functions, classes, and imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            total_functions += 1
                            total_complexity += self._calculate_cyclomatic_complexity(node)
                        elif isinstance(node, ast.ClassDef):
                            total_classes += 1
                        elif isinstance(node, (ast.Import, ast.ImportFrom)):
                            total_imports += 1
                    
                    # Store code blocks for duplicate detection
                    code_blocks.extend(self._extract_code_blocks(tree))
                    
                except SyntaxError:
                    # Skip files with syntax errors
                    continue
                    
            except Exception as e:
                print(f"Error analyzing file {file_path}: {e}")
                continue
        
        # Calculate metrics
        avg_complexity = total_complexity / max(total_functions, 1)
        comment_ratio = comment_lines / max(total_lines, 1)
        duplicate_ratio = self._calculate_duplicate_ratio(code_blocks)
        maintainability_index = self._calculate_maintainability_index(
            avg_complexity, total_lines, comment_ratio
        )
        
        return CodeAnalysisResult(
            lines_of_code=total_lines,
            cyclomatic_complexity=avg_complexity,
            maintainability_index=maintainability_index,
            duplicate_code_ratio=duplicate_ratio,
            comment_ratio=comment_ratio,
            function_count=total_functions,
            class_count=total_classes,
            import_count=total_imports
        )
    
    async def _collect_test_metrics(self, project_path: str) -> TestMetricsResult:
        """Collect test quality metrics."""
        test_files = list(Path(project_path).rglob("test_*.py")) + \
                    list(Path(project_path).rglob("*_test.py"))
        
        if not test_files:
            return TestMetricsResult(0, 0, 0, 0, 0, 0)
        
        test_count = 0
        assertion_count = 0
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count test functions
                test_count += len(re.findall(r'def test_\w+', content))
                
                # Count assertions
                assertion_patterns = [
                    r'assert\s+',
                    r'\.assert\w+\(',
                    r'self\.assert\w+\(',
                    r'pytest\.raises'
                ]
                
                for pattern in assertion_patterns:
                    assertion_count += len(re.findall(pattern, content))
                    
            except Exception as e:
                print(f"Error analyzing test file {test_file}: {e}")
                continue
        
        # Try to get coverage from coverage.py if available
        coverage = await self._get_test_coverage(project_path)
        
        # Calculate test quality score
        test_quality_score = self._calculate_test_quality_score(
            test_count, assertion_count, coverage
        )
        
        return TestMetricsResult(
            test_coverage=coverage,
            test_count=test_count,
            assertion_count=assertion_count,
            test_quality_score=test_quality_score,
            flaky_test_count=0,  # Would need test execution history
            slow_test_count=0    # Would need test execution timing
        )
    
    async def _collect_security_metrics(self, project_path: str) -> SecurityAnalysisResult:
        """Collect security-related metrics."""
        python_files = list(Path(project_path).rglob("*.py"))
        
        vulnerability_patterns = {
            'critical': [
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
                r'subprocess\.call\s*\([^)]*shell\s*=\s*True'
            ],
            'high': [
                r'pickle\.loads?\s*\(',
                r'yaml\.load\s*\(',
                r'random\.random\s*\(',
                r'hashlib\.md5\s*\(',
                r'hashlib\.sha1\s*\('
            ],
            'medium': [
                r'input\s*\(',
                r'raw_input\s*\(',
                r'open\s*\([^)]*["\']w["\']',
                r'sql.*=.*%.*%'
            ],
            'low': [
                r'print\s*\(',
                r'logging\.debug\s*\(',
                r'TODO|FIXME|HACK'
            ]
        }
        
        vulnerability_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for severity, patterns in vulnerability_patterns.items():
                    for pattern in patterns:
                        vulnerability_counts[severity] += len(re.findall(pattern, content, re.IGNORECASE))
                        
            except Exception as e:
                print(f"Error analyzing security in file {file_path}: {e}")
                continue
        
        # Calculate security score (0-100, higher is better)
        total_vulnerabilities = sum(vulnerability_counts.values())
        critical_weight = vulnerability_counts['critical'] * 10
        high_weight = vulnerability_counts['high'] * 5
        medium_weight = vulnerability_counts['medium'] * 2
        low_weight = vulnerability_counts['low'] * 1
        
        weighted_score = critical_weight + high_weight + medium_weight + low_weight
        security_score = max(0, 100 - weighted_score)
        
        return SecurityAnalysisResult(
            security_score=security_score,
            vulnerability_count=total_vulnerabilities,
            critical_vulnerabilities=vulnerability_counts['critical'],
            high_vulnerabilities=vulnerability_counts['high'],
            medium_vulnerabilities=vulnerability_counts['medium'],
            low_vulnerabilities=vulnerability_counts['low']
        )
    
    async def _collect_performance_metrics(self, project_path: str) -> PerformanceAnalysisResult:
        """Collect performance-related metrics."""
        python_files = list(Path(project_path).rglob("*.py"))
        
        performance_issues = {
            'bottlenecks': [
                r'for\s+\w+\s+in\s+.*\.keys\(\)',
                r'\.append\s*\([^)]*for\s+',
                r'time\.sleep\s*\(',
                r'\.join\s*\(\s*\[.*for\s+'
            ],
            'memory_leaks': [
                r'global\s+\w+\s*=\s*\[',
                r'cache\s*=\s*\{',
                r'\.cache\s*\[',
                r'while\s+True:'
            ],
            'inefficient_queries': [
                r'\.filter\s*\(.*\.filter\s*\(',
                r'for\s+\w+\s+in\s+.*\.all\(\)',
                r'\.get\s*\(.*for\s+',
                r'SELECT.*FROM.*WHERE.*IN\s*\('
            ],
            'blocking_operations': [
                r'requests\.get\s*\(',
                r'requests\.post\s*\(',
                r'urllib\.request',
                r'socket\.connect\s*\(',
                r'time\.sleep\s*\(',
                r'subprocess\.call\s*\('
            ]
        }
        
        issue_counts = {key: 0 for key in performance_issues.keys()}
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for issue_type, patterns in performance_issues.items():
                    for pattern in patterns:
                        issue_counts[issue_type] += len(re.findall(pattern, content, re.IGNORECASE))
                        
            except Exception as e:
                print(f"Error analyzing performance in file {file_path}: {e}")
                continue
        
        # Calculate performance score (0-100, higher is better)
        total_issues = sum(issue_counts.values())
        performance_score = max(0, 100 - (total_issues * 2))
        
        return PerformanceAnalysisResult(
            performance_score=performance_score,
            bottleneck_count=issue_counts['bottlenecks'],
            memory_leak_indicators=issue_counts['memory_leaks'],
            inefficient_query_count=issue_counts['inefficient_queries'],
            blocking_operation_count=issue_counts['blocking_operations']
        )
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function node."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _extract_code_blocks(self, tree: ast.AST) -> List[str]:
        """Extract code blocks for duplicate detection."""
        blocks = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Convert function to string representation
                try:
                    block = ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
                    blocks.append(block)
                except:
                    continue
        
        return blocks
    
    def _calculate_duplicate_ratio(self, code_blocks: List[str]) -> float:
        """Calculate ratio of duplicate code blocks."""
        if len(code_blocks) < 2:
            return 0.0
        
        duplicates = 0
        seen = set()
        
        for block in code_blocks:
            # Normalize block (remove whitespace variations)
            normalized = re.sub(r'\s+', ' ', block.strip())
            if normalized in seen:
                duplicates += 1
            else:
                seen.add(normalized)
        
        return duplicates / len(code_blocks)
    
    def _calculate_maintainability_index(self, complexity: float, 
                                       lines_of_code: int, 
                                       comment_ratio: float) -> float:
        """Calculate maintainability index (0-100, higher is better)."""
        if lines_of_code == 0:
            return 100.0
        
        # Simplified maintainability index calculation
        # Based on Halstead complexity, cyclomatic complexity, and lines of code
        
        # Normalize inputs
        normalized_complexity = min(complexity / 10.0, 1.0)  # Cap at 10
        normalized_loc = min(lines_of_code / 1000.0, 1.0)    # Cap at 1000 LOC
        
        # Calculate index (higher comment ratio and lower complexity = higher maintainability)
        maintainability = 100 * (1 - normalized_complexity) * (1 - normalized_loc) * (1 + comment_ratio)
        
        return min(max(maintainability, 0), 100)
    
    def _calculate_technical_debt_ratio(self, code_metrics: CodeAnalysisResult,
                                      test_metrics: TestMetricsResult,
                                      security_metrics: SecurityAnalysisResult) -> float:
        """Calculate technical debt ratio (0-1, lower is better)."""
        debt_factors = []
        
        # Complexity debt
        if code_metrics.cyclomatic_complexity > 10:
            debt_factors.append((code_metrics.cyclomatic_complexity - 10) / 20)
        
        # Test coverage debt
        if test_metrics.test_coverage < 80:
            debt_factors.append((80 - test_metrics.test_coverage) / 80)
        
        # Security debt
        if security_metrics.security_score < 85:
            debt_factors.append((85 - security_metrics.security_score) / 85)
        
        # Duplicate code debt
        if code_metrics.duplicate_code_ratio > 0.05:
            debt_factors.append(code_metrics.duplicate_code_ratio)
        
        # Comment debt
        if code_metrics.comment_ratio < 0.1:
            debt_factors.append((0.1 - code_metrics.comment_ratio) / 0.1)
        
        return min(mean(debt_factors) if debt_factors else 0.0, 1.0)
    
    def _calculate_test_quality_score(self, test_count: int, 
                                    assertion_count: int, 
                                    coverage: float) -> float:
        """Calculate test quality score (0-100, higher is better)."""
        if test_count == 0:
            return 0.0
        
        # Factors for test quality
        coverage_score = coverage  # Already 0-100
        assertion_density = min((assertion_count / test_count) * 10, 100)  # Cap at 100
        test_density_score = min(test_count * 2, 100)  # More tests = better, cap at 100
        
        # Weighted average
        quality_score = (coverage_score * 0.5 + assertion_density * 0.3 + test_density_score * 0.2)
        
        return min(max(quality_score, 0), 100)
    
    async def _get_test_coverage(self, project_path: str) -> float:
        """Get test coverage using coverage.py if available."""
        try:
            # Try to run coverage if available
            result = subprocess.run(
                ['python', '-m', 'coverage', 'report', '--show-missing'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse coverage output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'TOTAL' in line:
                        # Extract percentage
                        match = re.search(r'(\d+)%', line)
                        if match:
                            return float(match.group(1))
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass
        
        return 0.0  # Default if coverage can't be determined
    
    async def _store_metrics(self, metrics: QualityMetrics):
        """Store metrics in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
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
            
            conn.commit()
            
        finally:
            conn.close()
    
    async def _update_trend_data(self, metrics: QualityMetrics):
        """Update trend data for the metrics."""
        # Get previous metrics for comparison
        previous_metrics = await self.get_previous_metrics(metrics.project_id)
        
        if not previous_metrics:
            return  # No previous data to compare
        
        # Calculate trends for each metric
        metric_comparisons = [
            ('code_coverage', metrics.code_coverage, previous_metrics.code_coverage),
            ('cyclomatic_complexity', metrics.cyclomatic_complexity, previous_metrics.cyclomatic_complexity),
            ('maintainability_index', metrics.maintainability_index, previous_metrics.maintainability_index),
            ('technical_debt_ratio', metrics.technical_debt_ratio, previous_metrics.technical_debt_ratio),
            ('test_quality_score', metrics.test_quality_score, previous_metrics.test_quality_score),
            ('security_score', metrics.security_score, previous_metrics.security_score),
            ('performance_score', metrics.performance_score, previous_metrics.performance_score)
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for metric_name, current_value, previous_value in metric_comparisons:
                if current_value is not None and previous_value is not None:
                    # Calculate trend direction and change percentage
                    change_percentage = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
                    
                    if abs(change_percentage) < 1:  # Less than 1% change
                        trend_direction = 'stable'
                    elif change_percentage > 0:
                        trend_direction = 'up'
                    else:
                        trend_direction = 'down'
                    
                    # Store trend data
                    trend = QualityTrend(
                        project_id=metrics.project_id,
                        metric_name=metric_name,
                        metric_value=current_value,
                        timestamp=metrics.timestamp,
                        trend_direction=trend_direction,
                        change_percentage=change_percentage
                    )
                    
                    cursor.execute("""
                        INSERT INTO quality_trends 
                        (id, project_id, metric_name, metric_value, timestamp, 
                         trend_direction, change_percentage)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trend.id, trend.project_id, trend.metric_name,
                        trend.metric_value, trend.timestamp.isoformat(),
                        trend.trend_direction, trend.change_percentage
                    ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    async def get_previous_metrics(self, project_id: str) -> Optional[QualityMetrics]:
        """Get the most recent previous metrics for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM quality_metrics 
                WHERE project_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1 OFFSET 1
            """, (project_id,))
            
            row = cursor.fetchone()
            if row:
                return QualityMetrics.from_dict({
                    'id': row[0],
                    'project_id': row[1],
                    'timestamp': row[2],
                    'code_coverage': row[3],
                    'cyclomatic_complexity': row[4],
                    'maintainability_index': row[5],
                    'technical_debt_ratio': row[6],
                    'test_quality_score': row[7],
                    'security_score': row[8],
                    'performance_score': row[9],
                    'lines_of_code': row[10],
                    'duplicate_code_ratio': row[11],
                    'comment_ratio': row[12]
                })
            
            return None
            
        finally:
            conn.close()
    
    async def get_quality_trends(self, project_id: str, 
                               metric_name: Optional[str] = None,
                               days: int = 30) -> List[QualityTrend]:
        """Get quality trends for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            if metric_name:
                cursor.execute("""
                    SELECT * FROM quality_trends 
                    WHERE project_id = ? AND metric_name = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                """, (project_id, metric_name, since_date.isoformat()))
            else:
                cursor.execute("""
                    SELECT * FROM quality_trends 
                    WHERE project_id = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                """, (project_id, since_date.isoformat()))
            
            trends = []
            for row in cursor.fetchall():
                trends.append(QualityTrend(
                    id=row[0],
                    project_id=row[1],
                    metric_name=row[2],
                    metric_value=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    trend_direction=row[5],
                    change_percentage=row[6]
                ))
            
            return trends
            
        finally:
            conn.close()
    
    async def evaluate_quality_gates(self, project_id: str, 
                                   metrics: QualityMetrics) -> QualityGateResult:
        """Evaluate quality gates against current metrics."""
        thresholds = self.config_manager.get_quality_thresholds(project_id)
        
        failed_criteria = []
        warnings = []
        
        # Check each threshold
        if metrics.code_coverage is not None and metrics.code_coverage < thresholds.min_coverage:
            failed_criteria.append(f"Code coverage {metrics.code_coverage:.1f}% below minimum {thresholds.min_coverage}%")
        
        if metrics.cyclomatic_complexity is not None and metrics.cyclomatic_complexity > thresholds.max_complexity:
            failed_criteria.append(f"Cyclomatic complexity {metrics.cyclomatic_complexity:.1f} above maximum {thresholds.max_complexity}")
        
        if metrics.maintainability_index is not None and metrics.maintainability_index < thresholds.min_maintainability:
            failed_criteria.append(f"Maintainability index {metrics.maintainability_index:.1f} below minimum {thresholds.min_maintainability}")
        
        if metrics.technical_debt_ratio is not None and metrics.technical_debt_ratio > thresholds.max_technical_debt_ratio:
            failed_criteria.append(f"Technical debt ratio {metrics.technical_debt_ratio:.3f} above maximum {thresholds.max_technical_debt_ratio}")
        
        if metrics.test_quality_score is not None and metrics.test_quality_score < thresholds.min_test_quality:
            failed_criteria.append(f"Test quality score {metrics.test_quality_score:.1f} below minimum {thresholds.min_test_quality}")
        
        if metrics.security_score is not None and metrics.security_score < thresholds.min_security_score:
            failed_criteria.append(f"Security score {metrics.security_score:.1f} below minimum {thresholds.min_security_score}")
        
        if metrics.duplicate_code_ratio is not None and metrics.duplicate_code_ratio > thresholds.max_duplicate_ratio:
            warnings.append(f"Duplicate code ratio {metrics.duplicate_code_ratio:.3f} above recommended maximum {thresholds.max_duplicate_ratio}")
        
        # Calculate overall score (0-100)
        scores = []
        if metrics.code_coverage is not None:
            scores.append(metrics.code_coverage)
        if metrics.maintainability_index is not None:
            scores.append(metrics.maintainability_index)
        if metrics.test_quality_score is not None:
            scores.append(metrics.test_quality_score)
        if metrics.security_score is not None:
            scores.append(metrics.security_score)
        if metrics.performance_score is not None:
            scores.append(metrics.performance_score)
        
        overall_score = mean(scores) if scores else 0
        
        # Quality gate passes if no failed criteria
        passed = len(failed_criteria) == 0
        
        result = QualityGateResult(
            passed=passed,
            failed_criteria=failed_criteria,
            warnings=warnings,
            score=overall_score,
            details={
                'thresholds_checked': len(failed_criteria) + len(warnings),
                'metrics_evaluated': len(scores),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Store quality gate result
        await self._store_quality_gate_result(project_id, result)
        
        return result
    
    async def _store_quality_gate_result(self, project_id: str, result: QualityGateResult):
        """Store quality gate evaluation result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO quality_gates 
                (id, project_id, gate_name, criteria, passed, score, 
                 failed_criteria, warnings, evaluated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                f"gate_{project_id}_{datetime.now().timestamp()}",
                project_id,
                "Standard Quality Gate",
                json.dumps(result.details),
                result.passed,
                result.score,
                json.dumps(result.failed_criteria),
                json.dumps(result.warnings)
            ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    async def get_metrics_history(self, project_id: str, days: int = 30) -> List[QualityMetrics]:
        """Get historical quality metrics for a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            cursor.execute("""
                SELECT * FROM quality_metrics 
                WHERE project_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (project_id, since_date.isoformat()))
            
            metrics_list = []
            for row in cursor.fetchall():
                metrics_list.append(QualityMetrics.from_dict({
                    'id': row[0],
                    'project_id': row[1],
                    'timestamp': row[2],
                    'code_coverage': row[3],
                    'cyclomatic_complexity': row[4],
                    'maintainability_index': row[5],
                    'technical_debt_ratio': row[6],
                    'test_quality_score': row[7],
                    'security_score': row[8],
                    'performance_score': row[9],
                    'lines_of_code': row[10],
                    'duplicate_code_ratio': row[11],
                    'comment_ratio': row[12]
                }))
            
            return metrics_list
            
        finally:
            conn.close()