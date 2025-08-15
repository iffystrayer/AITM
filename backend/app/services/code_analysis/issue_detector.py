"""
Quality issue detection and categorization pipeline.
"""

import re
import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Callable, Pattern
from enum import Enum

from .base_analyzer import (
    CodeAnalyzer, AnalysisResult, AnalysisContext, AnalysisType,
    PythonASTAnalyzer, FileAnalyzer
)
from app.models.quality import QualityIssue, IssueType, Severity


class DetectionRule:
    """Represents a quality issue detection rule."""
    
    def __init__(self, rule_id: str, name: str, description: str,
                 issue_type: IssueType, severity: Severity,
                 pattern: Optional[str] = None,
                 ast_checker: Optional[Callable] = None,
                 languages: Optional[Set[str]] = None):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.issue_type = issue_type
        self.severity = severity
        self.pattern = re.compile(pattern) if pattern else None
        self.ast_checker = ast_checker
        self.languages = languages or set()
        self.enabled = True
        self.metadata: Dict[str, Any] = {}
    
    def matches_language(self, language: str) -> bool:
        """Check if rule applies to the given language."""
        return not self.languages or language in self.languages
    
    def check_pattern(self, content: str) -> List[Dict[str, Any]]:
        """Check pattern-based rule against content."""
        matches = []
        if not self.pattern:
            return matches
        
        for line_num, line in enumerate(content.split('\n'), 1):
            for match in self.pattern.finditer(line):
                matches.append({
                    'line_number': line_num,
                    'column_number': match.start() + 1,
                    'matched_text': match.group(),
                    'line_content': line
                })
        
        return matches
    
    def check_ast(self, tree: ast.AST, context: AnalysisContext) -> List[Dict[str, Any]]:
        """Check AST-based rule against parsed code."""
        if not self.ast_checker:
            return []
        
        try:
            return self.ast_checker(tree, context)
        except Exception as e:
            print(f"Error in AST checker for rule {self.rule_id}: {e}")
            return []


class QualityIssueDetector(CodeAnalyzer):
    """Detects quality issues using configurable rules."""
    
    def __init__(self):
        super().__init__("QualityIssueDetector", AnalysisType.STYLE)
        self.rules: Dict[str, DetectionRule] = {}
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """Load default detection rules."""
        # Style rules
        self.add_rule(DetectionRule(
            rule_id="long_line",
            name="Line too long",
            description="Line exceeds maximum length",
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            pattern=r'^.{89,}$',  # Lines longer than 88 characters
            languages={'python'}
        ))
        
        self.add_rule(DetectionRule(
            rule_id="trailing_whitespace",
            name="Trailing whitespace",
            description="Line has trailing whitespace",
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            pattern=r'\s+$'
        ))
        
        self.add_rule(DetectionRule(
            rule_id="multiple_blank_lines",
            name="Multiple blank lines",
            description="Multiple consecutive blank lines",
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            pattern=r'\n\s*\n\s*\n'
        ))
        
        # Security rules
        self.add_rule(DetectionRule(
            rule_id="hardcoded_password",
            name="Hardcoded password",
            description="Potential hardcoded password found",
            issue_type=IssueType.SECURITY,
            severity=Severity.HIGH,
            pattern=r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']'
        ))
        
        self.add_rule(DetectionRule(
            rule_id="sql_injection_risk",
            name="SQL injection risk",
            description="Potential SQL injection vulnerability",
            issue_type=IssueType.SECURITY,
            severity=Severity.HIGH,
            pattern=r'(?i)(execute|query|select|insert|update|delete)\s*\(\s*["\'].*%.*["\']'
        ))
        
        # Performance rules
        self.add_rule(DetectionRule(
            rule_id="inefficient_loop",
            name="Inefficient loop",
            description="Potentially inefficient loop pattern",
            issue_type=IssueType.PERFORMANCE,
            severity=Severity.MEDIUM,
            pattern=r'for\s+\w+\s+in\s+range\(len\('
        ))
        
        # Documentation rules
        self.add_rule(DetectionRule(
            rule_id="missing_docstring",
            name="Missing docstring",
            description="Function or class missing docstring",
            issue_type=IssueType.DOCUMENTATION,
            severity=Severity.MEDIUM,
            ast_checker=self._check_missing_docstring,
            languages={'python'}
        ))
        
        # Complexity rules
        self.add_rule(DetectionRule(
            rule_id="too_many_arguments",
            name="Too many arguments",
            description="Function has too many arguments",
            issue_type=IssueType.COMPLEXITY,
            severity=Severity.MEDIUM,
            ast_checker=self._check_too_many_arguments,
            languages={'python'}
        ))
    
    def add_rule(self, rule: DetectionRule) -> None:
        """Add a detection rule."""
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a detection rule."""
        return self.rules.pop(rule_id, None) is not None
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a detection rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a detection rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def get_rules_for_language(self, language: str) -> List[DetectionRule]:
        """Get enabled rules for a specific language."""
        return [
            rule for rule in self.rules.values()
            if rule.enabled and rule.matches_language(language)
        ]
    
    def _analyze_implementation(self, context: AnalysisContext) -> AnalysisResult:
        """Detect quality issues in the code."""
        result = AnalysisResult(
            analyzer_name=self.name,
            analysis_type=self.analysis_type,
            context=context
        )
        
        applicable_rules = self.get_rules_for_language(context.language)
        
        # Parse AST for Python files
        tree = None
        if context.language == 'python':
            try:
                tree = ast.parse(context.file_content, filename=context.file_path)
            except SyntaxError as e:
                # Add syntax error as an issue
                issue = QualityIssue(
                    issue_type=IssueType.STYLE,
                    severity=Severity.CRITICAL,
                    category="syntax_error",
                    description=f"Syntax error: {e.msg}",
                    line_number=e.lineno,
                    column_number=e.offset
                )
                result.add_issue(issue)
                return result
        
        # Apply rules
        for rule in applicable_rules:
            try:
                # Pattern-based checks
                if rule.pattern:
                    matches = rule.check_pattern(context.file_content)
                    for match in matches:
                        issue = QualityIssue(
                            issue_type=rule.issue_type,
                            severity=rule.severity,
                            category=rule.rule_id,
                            description=rule.description,
                            line_number=match['line_number'],
                            column_number=match.get('column_number'),
                            suggested_fix=self._get_suggested_fix(rule, match)
                        )
                        result.add_issue(issue)
                
                # AST-based checks
                if rule.ast_checker and tree:
                    ast_matches = rule.check_ast(tree, context)
                    for match in ast_matches:
                        issue = QualityIssue(
                            issue_type=rule.issue_type,
                            severity=rule.severity,
                            category=rule.rule_id,
                            description=rule.description,
                            line_number=match.get('line_number'),
                            column_number=match.get('column_number'),
                            suggested_fix=self._get_suggested_fix(rule, match)
                        )
                        result.add_issue(issue)
                        
            except Exception as e:
                print(f"Error applying rule {rule.rule_id}: {e}")
        
        # Add metrics
        result.add_metric('rules_applied', len(applicable_rules))
        result.add_metric('issues_found', len(result.issues))
        result.add_metric('critical_issues', 
                         len([i for i in result.issues if i.severity == Severity.CRITICAL]))
        result.add_metric('high_issues', 
                         len([i for i in result.issues if i.severity == Severity.HIGH]))
        
        return result
    
    def _get_suggested_fix(self, rule: DetectionRule, match: Dict[str, Any]) -> Optional[str]:
        """Get suggested fix for a rule match."""
        fix_suggestions = {
            'trailing_whitespace': 'Remove trailing whitespace',
            'multiple_blank_lines': 'Remove extra blank lines',
            'long_line': 'Break line into multiple lines',
            'hardcoded_password': 'Use environment variables or secure configuration',
            'sql_injection_risk': 'Use parameterized queries',
            'inefficient_loop': 'Use direct iteration or list comprehension',
            'missing_docstring': 'Add docstring describing the function/class',
            'too_many_arguments': 'Consider using a configuration object or reducing parameters'
        }
        
        return fix_suggestions.get(rule.rule_id)
    
    def _check_missing_docstring(self, tree: ast.AST, context: AnalysisContext) -> List[Dict[str, Any]]:
        """Check for missing docstrings in functions and classes."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Skip private methods and special methods
                if node.name.startswith('_'):
                    continue
                
                # Check if docstring exists
                has_docstring = (
                    node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                )
                
                if not has_docstring:
                    issues.append({
                        'line_number': node.lineno,
                        'column_number': node.col_offset,
                        'node_type': type(node).__name__,
                        'node_name': node.name
                    })
        
        return issues
    
    def _check_too_many_arguments(self, tree: ast.AST, context: AnalysisContext) -> List[Dict[str, Any]]:
        """Check for functions with too many arguments."""
        issues = []
        max_args = self.configuration.get('max_arguments', 5)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_count = len(node.args.args)
                
                # Don't count 'self' for methods
                if arg_count > 0 and node.args.args[0].arg == 'self':
                    arg_count -= 1
                
                if arg_count > max_args:
                    issues.append({
                        'line_number': node.lineno,
                        'column_number': node.col_offset,
                        'arg_count': arg_count,
                        'function_name': node.name
                    })
        
        return issues


class IssueDetectionPipeline:
    """Pipeline for running multiple issue detectors."""
    
    def __init__(self):
        self.detectors: List[CodeAnalyzer] = []
        self.filters: List[Callable[[QualityIssue], bool]] = []
        self.transformers: List[Callable[[QualityIssue], QualityIssue]] = []
        
        # Default detectors
        self.add_detector(QualityIssueDetector())
    
    def add_detector(self, detector: CodeAnalyzer) -> None:
        """Add a quality issue detector to the pipeline."""
        self.detectors.append(detector)
    
    def add_filter(self, filter_func: Callable[[QualityIssue], bool]) -> None:
        """Add a filter to exclude certain issues."""
        self.filters.append(filter_func)
    
    def add_transformer(self, transformer: Callable[[QualityIssue], QualityIssue]) -> None:
        """Add a transformer to modify issues."""
        self.transformers.append(transformer)
    
    def detect_issues(self, context: AnalysisContext) -> List[QualityIssue]:
        """Run the detection pipeline and return all issues."""
        all_issues = []
        
        # Run all detectors
        for detector in self.detectors:
            if detector.supports_language(context.language):
                try:
                    result = detector.analyze(context)
                    if result.success:
                        all_issues.extend(result.issues)
                except Exception as e:
                    print(f"Error running detector {detector.name}: {e}")
        
        # Apply filters
        filtered_issues = []
        for issue in all_issues:
            include = True
            for filter_func in self.filters:
                try:
                    if not filter_func(issue):
                        include = False
                        break
                except Exception as e:
                    print(f"Error in issue filter: {e}")
            
            if include:
                filtered_issues.append(issue)
        
        # Apply transformers
        transformed_issues = []
        for issue in filtered_issues:
            transformed_issue = issue
            for transformer in self.transformers:
                try:
                    transformed_issue = transformer(transformed_issue)
                except Exception as e:
                    print(f"Error in issue transformer: {e}")
            
            transformed_issues.append(transformed_issue)
        
        return transformed_issues
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            'detector_count': len(self.detectors),
            'filter_count': len(self.filters),
            'transformer_count': len(self.transformers),
            'detectors': [d.name for d in self.detectors]
        }


# Common filters
def severity_filter(min_severity: Severity) -> Callable[[QualityIssue], bool]:
    """Create a filter that excludes issues below minimum severity."""
    severity_order = {
        Severity.INFO: 0,
        Severity.LOW: 1,
        Severity.MEDIUM: 2,
        Severity.HIGH: 3,
        Severity.CRITICAL: 4
    }
    
    min_level = severity_order[min_severity]
    
    def filter_func(issue: QualityIssue) -> bool:
        return severity_order.get(issue.severity, 0) >= min_level
    
    return filter_func


def file_pattern_filter(excluded_patterns: List[str]) -> Callable[[QualityIssue], bool]:
    """Create a filter that excludes issues from files matching patterns."""
    compiled_patterns = [re.compile(pattern) for pattern in excluded_patterns]
    
    def filter_func(issue: QualityIssue) -> bool:
        for pattern in compiled_patterns:
            if pattern.search(issue.file_path):
                return False
        return True
    
    return filter_func


def issue_type_filter(excluded_types: List[IssueType]) -> Callable[[QualityIssue], bool]:
    """Create a filter that excludes certain issue types."""
    def filter_func(issue: QualityIssue) -> bool:
        return issue.issue_type not in excluded_types
    
    return filter_func


# Common transformers
def add_auto_fix_suggestions(issue: QualityIssue) -> QualityIssue:
    """Add auto-fix suggestions to issues where applicable."""
    auto_fixable_categories = {
        'trailing_whitespace',
        'multiple_blank_lines',
        'long_line'
    }
    
    if issue.category in auto_fixable_categories:
        issue.auto_fixable = True
    
    return issue


def normalize_file_paths(base_path: str) -> Callable[[QualityIssue], QualityIssue]:
    """Create a transformer that normalizes file paths relative to base path."""
    def transformer(issue: QualityIssue) -> QualityIssue:
        if issue.file_path.startswith(base_path):
            issue.file_path = issue.file_path[len(base_path):].lstrip('/')
        return issue
    
    return transformer