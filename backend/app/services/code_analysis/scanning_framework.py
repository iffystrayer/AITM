"""
Main code scanning framework that orchestrates analysis components.
"""

import os
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_analyzer import CodeAnalyzer, AnalysisResult, AnalysisContext, AnalysisType
from .file_monitor import FileSystemMonitor, FileChangeEvent, RealTimeAnalysisCoordinator
from .issue_detector import IssueDetectionPipeline, QualityIssueDetector
from app.models.quality import QualityIssue, QualityMetrics
from app.core.quality_config import QualityConfigManager


@dataclass
class ScanConfiguration:
    """Configuration for code scanning."""
    project_id: str
    project_path: str
    file_patterns: List[str] = field(default_factory=lambda: ['**/*.py', '**/*.js', '**/*.ts'])
    excluded_patterns: List[str] = field(default_factory=lambda: [
        '**/node_modules/**', '**/__pycache__/**', '**/venv/**', 
        '**/.git/**', '**/dist/**', '**/build/**'
    ])
    max_file_size: int = 1024 * 1024  # 1MB
    parallel_workers: int = 4
    enable_real_time: bool = True
    cache_results: bool = True
    analysis_types: Set[AnalysisType] = field(default_factory=lambda: {
        AnalysisType.STYLE, AnalysisType.COMPLEXITY, AnalysisType.SECURITY
    })


@dataclass
class ScanResult:
    """Result of a code scanning operation."""
    scan_id: str
    project_id: str
    scan_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    files_scanned: int = 0
    files_with_issues: int = 0
    total_issues: int = 0
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    analysis_results: List[AnalysisResult] = field(default_factory=list)
    metrics: QualityMetrics = None
    success: bool = True
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def add_analysis_result(self, result: AnalysisResult) -> None:
        """Add an analysis result to the scan."""
        self.analysis_results.append(result)
        self.files_scanned += 1
        
        if result.issues:
            self.files_with_issues += 1
            self.total_issues += len(result.issues)
            
            # Update severity counts
            for issue in result.issues:
                severity = issue.severity.value
                self.issues_by_severity[severity] = self.issues_by_severity.get(severity, 0) + 1
                
                issue_type = issue.issue_type.value
                self.issues_by_type[issue_type] = self.issues_by_type.get(issue_type, 0) + 1
    
    def get_all_issues(self) -> List[QualityIssue]:
        """Get all issues from all analysis results."""
        all_issues = []
        for result in self.analysis_results:
            all_issues.extend(result.issues)
        return all_issues
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the scan results."""
        return {
            'scan_id': self.scan_id,
            'project_id': self.project_id,
            'scan_type': self.scan_type,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'files_scanned': self.files_scanned,
            'files_with_issues': self.files_with_issues,
            'total_issues': self.total_issues,
            'issues_by_severity': self.issues_by_severity,
            'issues_by_type': self.issues_by_type,
            'success': self.success,
            'execution_time': self.execution_time
        }


class CodeScanningFramework:
    """Main framework for orchestrating code quality scanning."""
    
    def __init__(self, config_manager: Optional[QualityConfigManager] = None):
        self.config_manager = config_manager or QualityConfigManager()
        self.analyzers: Dict[AnalysisType, List[CodeAnalyzer]] = {}
        self.issue_pipeline = IssueDetectionPipeline()
        self.real_time_coordinator: Optional[RealTimeAnalysisCoordinator] = None
        
        # Callbacks for scan events
        self.scan_started_callbacks: List[Callable[[ScanResult], None]] = []
        self.scan_completed_callbacks: List[Callable[[ScanResult], None]] = []
        self.file_analyzed_callbacks: List[Callable[[AnalysisResult], None]] = []
        self.issue_found_callbacks: List[Callable[[QualityIssue], None]] = []
        
        # Initialize default analyzers
        self._initialize_default_analyzers()
    
    def _initialize_default_analyzers(self) -> None:
        """Initialize default analyzers."""
        # Add the quality issue detector
        self.add_analyzer(AnalysisType.STYLE, QualityIssueDetector())
    
    def add_analyzer(self, analysis_type: AnalysisType, analyzer: CodeAnalyzer) -> None:
        """Add an analyzer for a specific analysis type."""
        if analysis_type not in self.analyzers:
            self.analyzers[analysis_type] = []
        self.analyzers[analysis_type].append(analyzer)
    
    def remove_analyzer(self, analysis_type: AnalysisType, analyzer_name: str) -> bool:
        """Remove an analyzer by name."""
        if analysis_type in self.analyzers:
            self.analyzers[analysis_type] = [
                a for a in self.analyzers[analysis_type] 
                if a.name != analyzer_name
            ]
            return True
        return False
    
    def get_analyzers(self, analysis_type: AnalysisType) -> List[CodeAnalyzer]:
        """Get analyzers for a specific analysis type."""
        return self.analyzers.get(analysis_type, [])
    
    def add_scan_started_callback(self, callback: Callable[[ScanResult], None]) -> None:
        """Add callback for scan started events."""
        self.scan_started_callbacks.append(callback)
    
    def add_scan_completed_callback(self, callback: Callable[[ScanResult], None]) -> None:
        """Add callback for scan completed events."""
        self.scan_completed_callbacks.append(callback)
    
    def add_file_analyzed_callback(self, callback: Callable[[AnalysisResult], None]) -> None:
        """Add callback for file analyzed events."""
        self.file_analyzed_callbacks.append(callback)
    
    def add_issue_found_callback(self, callback: Callable[[QualityIssue], None]) -> None:
        """Add callback for issue found events."""
        self.issue_found_callbacks.append(callback)
    
    async def scan_project(self, config: ScanConfiguration) -> ScanResult:
        """Scan an entire project for quality issues."""
        scan_result = ScanResult(
            scan_id=f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            project_id=config.project_id,
            scan_type="full_project",
            started_at=datetime.now(timezone.utc)
        )
        
        # Notify scan started
        for callback in self.scan_started_callbacks:
            try:
                callback(scan_result)
            except Exception as e:
                print(f"Error in scan started callback: {e}")
        
        try:
            # Find files to scan
            files_to_scan = self._find_files_to_scan(config)
            
            # Scan files in parallel
            with ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
                # Submit all file analysis tasks
                future_to_file = {
                    executor.submit(self._analyze_file_sync, file_path, config): file_path
                    for file_path in files_to_scan
                }
                
                # Process completed analyses
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        analysis_result = future.result()
                        if analysis_result:
                            scan_result.add_analysis_result(analysis_result)
                            
                            # Notify file analyzed
                            for callback in self.file_analyzed_callbacks:
                                try:
                                    callback(analysis_result)
                                except Exception as e:
                                    print(f"Error in file analyzed callback: {e}")
                            
                            # Notify issues found
                            for issue in analysis_result.issues:
                                for callback in self.issue_found_callbacks:
                                    try:
                                        callback(issue)
                                    except Exception as e:
                                        print(f"Error in issue found callback: {e}")
                                        
                    except Exception as e:
                        print(f"Error analyzing file {file_path}: {e}")
                        scan_result.success = False
                        if not scan_result.error_message:
                            scan_result.error_message = str(e)
            
            # Calculate metrics
            scan_result.metrics = self._calculate_project_metrics(scan_result)
            
        except Exception as e:
            scan_result.success = False
            scan_result.error_message = str(e)
        
        finally:
            scan_result.completed_at = datetime.now(timezone.utc)
            scan_result.execution_time = (
                scan_result.completed_at - scan_result.started_at
            ).total_seconds()
            
            # Notify scan completed
            for callback in self.scan_completed_callbacks:
                try:
                    callback(scan_result)
                except Exception as e:
                    print(f"Error in scan completed callback: {e}")
        
        return scan_result
    
    def _find_files_to_scan(self, config: ScanConfiguration) -> List[str]:
        """Find files to scan based on configuration."""
        project_path = Path(config.project_path)
        files_to_scan = []
        
        # Use glob patterns to find files
        for pattern in config.file_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file():
                    # Check if file should be excluded
                    should_exclude = False
                    for exclude_pattern in config.excluded_patterns:
                        if file_path.match(exclude_pattern):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        # Check file size
                        try:
                            if file_path.stat().st_size <= config.max_file_size:
                                files_to_scan.append(str(file_path))
                        except OSError:
                            continue
        
        return files_to_scan
    
    def _analyze_file_sync(self, file_path: str, config: ScanConfiguration) -> Optional[AnalysisResult]:
        """Synchronous wrapper for file analysis."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create analysis context
            context = AnalysisContext(
                project_id=config.project_id,
                file_path=file_path,
                file_content=content
            )
            
            # Run analysis
            return self._analyze_file_context(context, config)
            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def _analyze_file_context(self, context: AnalysisContext, 
                            config: ScanConfiguration) -> AnalysisResult:
        """Analyze a file using the configured analyzers."""
        combined_result = None
        
        # Run analyzers for each requested analysis type
        for analysis_type in config.analysis_types:
            analyzers = self.get_analyzers(analysis_type)
            
            for analyzer in analyzers:
                if analyzer.supports_language(context.language):
                    try:
                        result = analyzer.analyze(context, config.cache_results)
                        
                        if combined_result is None:
                            combined_result = result
                        else:
                            combined_result = combined_result.merge(result)
                            
                    except Exception as e:
                        print(f"Error running analyzer {analyzer.name}: {e}")
        
        # If no analyzers ran, create empty result
        if combined_result is None:
            combined_result = AnalysisResult(
                analyzer_name="no_analyzer",
                analysis_type=AnalysisType.STYLE,
                context=context
            )
        
        return combined_result
    
    def _calculate_project_metrics(self, scan_result: ScanResult) -> QualityMetrics:
        """Calculate project-level quality metrics."""
        metrics = QualityMetrics(
            project_id=scan_result.project_id,
            timestamp=scan_result.completed_at or datetime.now(timezone.utc)
        )
        
        if scan_result.files_scanned > 0:
            # Calculate basic metrics
            metrics.lines_of_code = sum(
                len(result.context.file_content.split('\n'))
                for result in scan_result.analysis_results
            )
            
            # Calculate issue density (issues per 1000 lines of code)
            if metrics.lines_of_code > 0:
                issue_density = (scan_result.total_issues / metrics.lines_of_code) * 1000
                metrics.technical_debt_ratio = min(issue_density / 100, 1.0)  # Normalize to 0-1
            
            # Calculate quality scores based on issue severity
            critical_issues = scan_result.issues_by_severity.get('critical', 0)
            high_issues = scan_result.issues_by_severity.get('high', 0)
            medium_issues = scan_result.issues_by_severity.get('medium', 0)
            low_issues = scan_result.issues_by_severity.get('low', 0)
            
            # Security score (based on security issues)
            security_issues = scan_result.issues_by_type.get('security', 0)
            if security_issues == 0:
                metrics.security_score = 100.0
            else:
                # Deduct points based on security issues
                metrics.security_score = max(0, 100 - (security_issues * 10))
            
            # Maintainability score (based on all issues)
            total_weighted_issues = (critical_issues * 4 + high_issues * 3 + 
                                   medium_issues * 2 + low_issues * 1)
            if total_weighted_issues == 0:
                metrics.maintainability_index = 100.0
            else:
                # Calculate maintainability based on weighted issues per file
                avg_weighted_issues = total_weighted_issues / scan_result.files_scanned
                metrics.maintainability_index = max(0, 100 - (avg_weighted_issues * 5))
        
        return metrics
    
    async def scan_file(self, file_path: str, project_id: str) -> AnalysisResult:
        """Scan a single file for quality issues."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            context = AnalysisContext(
                project_id=project_id,
                file_path=file_path,
                file_content=content
            )
            
            config = ScanConfiguration(
                project_id=project_id,
                project_path=str(Path(file_path).parent)
            )
            
            return self._analyze_file_context(context, config)
            
        except Exception as e:
            # Return error result
            context = AnalysisContext(
                project_id=project_id,
                file_path=file_path,
                file_content=""
            )
            
            return AnalysisResult(
                analyzer_name="file_scanner",
                analysis_type=AnalysisType.STYLE,
                context=context,
                success=False,
                error_message=str(e)
            )
    
    def enable_real_time_monitoring(self, project_path: str, project_id: str) -> None:
        """Enable real-time monitoring for a project."""
        if not self.real_time_coordinator:
            self.real_time_coordinator = RealTimeAnalysisCoordinator(project_id)
        
        monitor = self.real_time_coordinator.add_project_monitor(project_path)
        
        # Add callback to trigger analysis on file changes
        def on_file_change(event: FileChangeEvent):
            if event.event_type in ['modified', 'created']:
                asyncio.create_task(self._handle_real_time_analysis(event))
        
        monitor.add_change_callback(on_file_change)
        self.real_time_coordinator.start_monitoring()
    
    async def _handle_real_time_analysis(self, event: FileChangeEvent) -> None:
        """Handle real-time analysis of changed files."""
        try:
            result = await self.scan_file(event.file_path, 
                                        self.real_time_coordinator.project_id)
            
            # Notify callbacks
            for callback in self.file_analyzed_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    print(f"Error in real-time analysis callback: {e}")
                    
        except Exception as e:
            print(f"Error in real-time analysis: {e}")
    
    def disable_real_time_monitoring(self) -> None:
        """Disable real-time monitoring."""
        if self.real_time_coordinator:
            self.real_time_coordinator.stop_monitoring()
            self.real_time_coordinator = None
    
    def get_framework_stats(self) -> Dict[str, Any]:
        """Get framework statistics."""
        stats = {
            'analyzer_count': sum(len(analyzers) for analyzers in self.analyzers.values()),
            'analyzers_by_type': {
                analysis_type.value: len(analyzers)
                for analysis_type, analyzers in self.analyzers.items()
            },
            'callback_counts': {
                'scan_started': len(self.scan_started_callbacks),
                'scan_completed': len(self.scan_completed_callbacks),
                'file_analyzed': len(self.file_analyzed_callbacks),
                'issue_found': len(self.issue_found_callbacks)
            },
            'real_time_enabled': self.real_time_coordinator is not None
        }
        
        if self.real_time_coordinator:
            stats['real_time_stats'] = self.real_time_coordinator.get_stats()
        
        return stats