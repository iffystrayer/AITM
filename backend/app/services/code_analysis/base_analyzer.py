"""
Abstract base class for code analyzers with common functionality.
"""

import ast
import os
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union
from enum import Enum

from app.models.quality import QualityIssue, IssueType, Severity


class AnalysisType(str, Enum):
    """Types of code analysis."""
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DUPLICATION = "duplication"


@dataclass
class AnalysisContext:
    """Context information for code analysis."""
    project_id: str
    file_path: str
    file_content: str
    file_hash: str = ""
    language: str = ""
    encoding: str = "utf-8"
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize computed fields."""
        if not self.file_hash:
            self.file_hash = hashlib.md5(self.file_content.encode()).hexdigest()
        
        if not self.language:
            self.language = self._detect_language()
    
    def _detect_language(self) -> str:
        """Detect programming language from file extension."""
        ext = Path(self.file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.sql': 'sql',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.md': 'markdown',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell'
        }
        return language_map.get(ext, 'unknown')


@dataclass
class AnalysisResult:
    """Result of code analysis."""
    analyzer_name: str
    analysis_type: AnalysisType
    context: AnalysisContext
    issues: List[QualityIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    
    def add_issue(self, issue: QualityIssue) -> None:
        """Add a quality issue to the result."""
        issue.project_id = self.context.project_id
        issue.file_path = self.context.file_path
        self.issues.append(issue)
    
    def add_metric(self, name: str, value: Any) -> None:
        """Add a metric to the result."""
        self.metrics[name] = value
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion to the result."""
        self.suggestions.append(suggestion)
    
    def merge(self, other: 'AnalysisResult') -> 'AnalysisResult':
        """Merge another analysis result into this one."""
        if other.context.file_path != self.context.file_path:
            raise ValueError("Cannot merge results from different files")
        
        merged = AnalysisResult(
            analyzer_name=f"{self.analyzer_name}+{other.analyzer_name}",
            analysis_type=self.analysis_type,
            context=self.context,
            issues=self.issues + other.issues,
            metrics={**self.metrics, **other.metrics},
            suggestions=self.suggestions + other.suggestions,
            execution_time=self.execution_time + other.execution_time,
            success=self.success and other.success,
            error_message=self.error_message or other.error_message
        )
        
        return merged


class CodeAnalyzer(ABC):
    """Abstract base class for code analyzers."""
    
    def __init__(self, name: str, analysis_type: AnalysisType):
        self.name = name
        self.analysis_type = analysis_type
        self.supported_languages: Set[str] = set()
        self.configuration: Dict[str, Any] = {}
        self._cache: Dict[str, AnalysisResult] = {}
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the analyzer with settings."""
        self.configuration.update(config)
    
    def supports_language(self, language: str) -> bool:
        """Check if analyzer supports the given language."""
        return language in self.supported_languages or not self.supported_languages
    
    def supports_file(self, file_path: str) -> bool:
        """Check if analyzer supports the given file."""
        context = self._create_minimal_context(file_path)
        return self.supports_language(context.language)
    
    def _create_minimal_context(self, file_path: str) -> AnalysisContext:
        """Create minimal context for file type detection."""
        return AnalysisContext(
            project_id="",
            file_path=file_path,
            file_content=""
        )
    
    def analyze(self, context: AnalysisContext, use_cache: bool = True) -> AnalysisResult:
        """Analyze code and return results."""
        # Check cache first
        if use_cache and context.file_hash in self._cache:
            cached_result = self._cache[context.file_hash]
            return cached_result
        
        # Validate input
        if not self.supports_language(context.language):
            return AnalysisResult(
                analyzer_name=self.name,
                analysis_type=self.analysis_type,
                context=context,
                success=False,
                error_message=f"Language {context.language} not supported"
            )
        
        # Perform analysis
        start_time = datetime.now()
        try:
            result = self._analyze_implementation(context)
            result.execution_time = (datetime.now() - start_time).total_seconds()
            result.success = True
            
            # Cache result
            if use_cache:
                self._cache[context.file_hash] = result
            
            return result
            
        except Exception as e:
            return AnalysisResult(
                analyzer_name=self.name,
                analysis_type=self.analysis_type,
                context=context,
                execution_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error_message=str(e)
            )
    
    @abstractmethod
    def _analyze_implementation(self, context: AnalysisContext) -> AnalysisResult:
        """Implement specific analysis logic."""
        pass
    
    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size': len(self._cache),
            'cache_keys': list(self._cache.keys())
        }


class PythonASTAnalyzer(CodeAnalyzer):
    """Base class for Python AST-based analyzers."""
    
    def __init__(self, name: str, analysis_type: AnalysisType):
        super().__init__(name, analysis_type)
        self.supported_languages = {'python'}
    
    def _parse_ast(self, context: AnalysisContext) -> Optional[ast.AST]:
        """Parse Python code into AST."""
        try:
            return ast.parse(context.file_content, filename=context.file_path)
        except SyntaxError as e:
            # Create a syntax error issue
            issue = QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.CRITICAL,
                category="syntax_error",
                description=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                column_number=e.offset
            )
            
            result = AnalysisResult(
                analyzer_name=self.name,
                analysis_type=self.analysis_type,
                context=context
            )
            result.add_issue(issue)
            return None
    
    def _analyze_implementation(self, context: AnalysisContext) -> AnalysisResult:
        """Base implementation for Python AST analysis."""
        result = AnalysisResult(
            analyzer_name=self.name,
            analysis_type=self.analysis_type,
            context=context
        )
        
        tree = self._parse_ast(context)
        if tree is None:
            return result
        
        # Delegate to specific AST analysis
        self._analyze_ast(tree, result)
        return result
    
    @abstractmethod
    def _analyze_ast(self, tree: ast.AST, result: AnalysisResult) -> None:
        """Analyze AST and populate result."""
        pass


class FileAnalyzer(CodeAnalyzer):
    """Base class for file-level analyzers that don't need language parsing."""
    
    def __init__(self, name: str, analysis_type: AnalysisType):
        super().__init__(name, analysis_type)
        # Support all languages by default
        self.supported_languages = set()
    
    def _get_file_stats(self, context: AnalysisContext) -> Dict[str, Any]:
        """Get basic file statistics."""
        lines = context.file_content.split('\n')
        return {
            'total_lines': len(lines),
            'non_empty_lines': len([line for line in lines if line.strip()]),
            'comment_lines': self._count_comment_lines(lines, context.language),
            'file_size': len(context.file_content.encode(context.encoding))
        }
    
    def _count_comment_lines(self, lines: List[str], language: str) -> int:
        """Count comment lines based on language."""
        comment_prefixes = {
            'python': ['#'],
            'javascript': ['//', '/*', '*'],
            'typescript': ['//', '/*', '*'],
            'java': ['//', '/*', '*'],
            'cpp': ['//', '/*', '*'],
            'c': ['//', '/*', '*'],
            'csharp': ['//', '/*', '*'],
            'go': ['//'],
            'rust': ['//', '/*', '*'],
            'php': ['//', '/*', '*', '#'],
            'ruby': ['#'],
            'shell': ['#'],
            'sql': ['--', '/*', '*'],
            'html': ['<!--'],
            'css': ['/*', '*'],
            'yaml': ['#'],
            'json': []  # JSON doesn't have comments
        }
        
        prefixes = comment_prefixes.get(language, ['#', '//', '/*', '*'])
        count = 0
        
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(prefix) for prefix in prefixes):
                count += 1
        
        return count


class MultiLanguageAnalyzer(CodeAnalyzer):
    """Base class for analyzers that support multiple languages."""
    
    def __init__(self, name: str, analysis_type: AnalysisType, 
                 supported_languages: Set[str]):
        super().__init__(name, analysis_type)
        self.supported_languages = supported_languages
        self.language_handlers: Dict[str, callable] = {}
    
    def register_language_handler(self, language: str, handler: callable) -> None:
        """Register a handler for a specific language."""
        self.language_handlers[language] = handler
    
    def _analyze_implementation(self, context: AnalysisContext) -> AnalysisResult:
        """Route analysis to language-specific handler."""
        result = AnalysisResult(
            analyzer_name=self.name,
            analysis_type=self.analysis_type,
            context=context
        )
        
        handler = self.language_handlers.get(context.language)
        if handler:
            handler(context, result)
        else:
            # Use default analysis
            self._default_analysis(context, result)
        
        return result
    
    def _default_analysis(self, context: AnalysisContext, result: AnalysisResult) -> None:
        """Default analysis when no specific handler is available."""
        result.add_suggestion(f"No specific analysis available for {context.language}")