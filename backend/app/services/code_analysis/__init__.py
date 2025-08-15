"""
Code analysis services for quality tracking and automated fixes.
"""

from .base_analyzer import (
    CodeAnalyzer, AnalysisResult, AnalysisContext, AnalysisType,
    PythonASTAnalyzer, FileAnalyzer, MultiLanguageAnalyzer
)
from .file_monitor import (
    FileSystemMonitor, FileChangeEvent, FileChangeType,
    RealTimeAnalysisCoordinator
)
from .issue_detector import (
    QualityIssueDetector, IssueDetectionPipeline, DetectionRule,
    severity_filter, file_pattern_filter, issue_type_filter,
    add_auto_fix_suggestions, normalize_file_paths
)
from .scanning_framework import (
    CodeScanningFramework, ScanResult, ScanConfiguration
)
from .auto_fix_engine import (
    AutoFixEngine, FixableIssue, FixApplicationResult, FixStatus,
    CodeFixer, TrailingWhitespaceFixer, MultipleBlankLinesFixer,
    PythonImportSorter, ExternalFormatterFixer
)
from .recommendation_engine import (
    RecommendationEngine, DuplicateCodeDetector, PerformanceAnalyzer,
    SecurityAnalyzer, PatternAnalyzer, RecommendationType,
    ImprovementRecommendation, CodePattern, DuplicateCodeBlock
)

__all__ = [
    'CodeAnalyzer',
    'AnalysisResult', 
    'AnalysisContext',
    'AnalysisType',
    'PythonASTAnalyzer',
    'FileAnalyzer',
    'MultiLanguageAnalyzer',
    'FileSystemMonitor',
    'FileChangeEvent',
    'FileChangeType',
    'RealTimeAnalysisCoordinator',
    'QualityIssueDetector',
    'IssueDetectionPipeline',
    'DetectionRule',
    'severity_filter',
    'file_pattern_filter', 
    'issue_type_filter',
    'add_auto_fix_suggestions',
    'normalize_file_paths',
    'CodeScanningFramework',
    'ScanResult',
    'ScanConfiguration',
    'AutoFixEngine',
    'FixableIssue',
    'FixApplicationResult',
    'FixStatus',
    'CodeFixer',
    'TrailingWhitespaceFixer',
    'MultipleBlankLinesFixer',
    'PythonImportSorter',
    'ExternalFormatterFixer',
    'RecommendationEngine',
    'DuplicateCodeDetector',
    'PerformanceAnalyzer',
    'SecurityAnalyzer',
    'PatternAnalyzer',
    'RecommendationType',
    'ImprovementRecommendation',
    'CodePattern',
    'DuplicateCodeBlock'
]