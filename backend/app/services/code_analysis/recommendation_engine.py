"""
Intelligent code improvement recommendation engine.

This module provides pattern analysis, duplicate code detection, performance optimization,
and security vulnerability detection with actionable improvement recommendations.
"""

import ast
import re
import hashlib
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum

from app.models.quality import QualityIssue, IssueType, Severity
from app.services.code_analysis.base_analyzer import (
    CodeAnalyzer, AnalysisType, AnalysisContext, AnalysisResult, PythonASTAnalyzer
)


class RecommendationType(str, Enum):
    """Types of code improvement recommendations."""
    DUPLICATE_REMOVAL = "duplicate_removal"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_IMPROVEMENT = "security_improvement"
    REFACTORING = "refactoring"
    DESIGN_PATTERN = "design_pattern"
    CODE_SIMPLIFICATION = "code_simplification"
    MAINTAINABILITY = "maintainability"


@dataclass
class CodePattern:
    """Represents a detected code pattern."""
    pattern_type: str
    pattern_hash: str
    file_path: str
    start_line: int
    end_line: int
    code_snippet: str
    complexity_score: float = 0.0
    frequency: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DuplicateCodeBlock:
    """Represents a duplicate code block."""
    pattern_hash: str
    occurrences: List[CodePattern] = field(default_factory=list)
    similarity_score: float = 0.0
    lines_count: int = 0
    consolidation_suggestion: Optional[str] = None


@dataclass
class ImprovementRecommendation:
    """Represents a code improvement recommendation."""
    id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    severity: Severity = Severity.MEDIUM
    impact_score: float = 0.0
    effort_estimate: str = "medium"  # low, medium, high
    code_before: Optional[str] = None
    code_after: Optional[str] = None
    rationale: str = ""
    references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RecommendationEngine(PythonASTAnalyzer):
    """Main recommendation engine for code improvement suggestions."""
    
    def __init__(self):
        super().__init__("RecommendationEngine", AnalysisType.MAINTAINABILITY)
        self.duplicate_detector = DuplicateCodeDetector()
        self.performance_analyzer = PerformanceAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        
        # Configuration
        self.min_duplicate_lines = 3  # Reduced for better detection
        self.min_similarity_threshold = 0.8
        self.max_complexity_threshold = 10
        
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the recommendation engine."""
        super().configure(config)
        self.min_duplicate_lines = config.get('min_duplicate_lines', 3)
        self.min_similarity_threshold = config.get('min_similarity_threshold', 0.8)
        self.max_complexity_threshold = config.get('max_complexity_threshold', 10)
        
        # Configure sub-analyzers
        self.duplicate_detector.min_lines = self.min_duplicate_lines
        self.duplicate_detector.similarity_threshold = self.min_similarity_threshold
    
    def _analyze_ast(self, tree: ast.AST, result: AnalysisResult) -> None:
        """Analyze AST and generate improvement recommendations."""
        recommendations = []
        
        # Detect duplicate code patterns
        duplicate_recommendations = self.duplicate_detector.detect_duplicates(
            tree, result.context
        )
        recommendations.extend(duplicate_recommendations)
        
        # Analyze performance optimization opportunities
        performance_recommendations = self.performance_analyzer.analyze_performance(
            tree, result.context
        )
        recommendations.extend(performance_recommendations)
        
        # Detect security vulnerabilities
        security_recommendations = self.security_analyzer.analyze_security(
            tree, result.context
        )
        recommendations.extend(security_recommendations)
        
        # Analyze code patterns and suggest improvements
        pattern_recommendations = self.pattern_analyzer.analyze_patterns(
            tree, result.context
        )
        recommendations.extend(pattern_recommendations)
        
        # Convert recommendations to quality issues
        for rec in recommendations:
            issue = self._recommendation_to_issue(rec)
            result.add_issue(issue)
        
        # Add metrics
        result.add_metric('total_recommendations', len(recommendations))
        result.add_metric('duplicate_recommendations', 
                         len([r for r in recommendations 
                             if r.recommendation_type == RecommendationType.DUPLICATE_REMOVAL]))
        result.add_metric('performance_recommendations',
                         len([r for r in recommendations 
                             if r.recommendation_type == RecommendationType.PERFORMANCE_OPTIMIZATION]))
        result.add_metric('security_recommendations',
                         len([r for r in recommendations 
                             if r.recommendation_type == RecommendationType.SECURITY_IMPROVEMENT]))
    
    def _recommendation_to_issue(self, recommendation: ImprovementRecommendation) -> QualityIssue:
        """Convert a recommendation to a quality issue."""
        issue_type_map = {
            RecommendationType.DUPLICATE_REMOVAL: IssueType.DUPLICATION,
            RecommendationType.PERFORMANCE_OPTIMIZATION: IssueType.PERFORMANCE,
            RecommendationType.SECURITY_IMPROVEMENT: IssueType.SECURITY,
            RecommendationType.REFACTORING: IssueType.MAINTAINABILITY,
            RecommendationType.DESIGN_PATTERN: IssueType.MAINTAINABILITY,
            RecommendationType.CODE_SIMPLIFICATION: IssueType.COMPLEXITY,
            RecommendationType.MAINTAINABILITY: IssueType.MAINTAINABILITY
        }
        
        return QualityIssue(
            id=recommendation.id,
            issue_type=issue_type_map.get(recommendation.recommendation_type, IssueType.MAINTAINABILITY),
            severity=recommendation.severity,
            category=recommendation.recommendation_type.value,
            description=f"{recommendation.title}: {recommendation.description}",
            suggested_fix=recommendation.code_after,
            line_number=recommendation.line_number,
            auto_fixable=recommendation.code_after is not None
        )


class DuplicateCodeDetector:
    """Detects duplicate code blocks and suggests consolidation."""
    
    def __init__(self):
        self.min_lines = 3  # Reduced for better detection of smaller duplicates
        self.similarity_threshold = 0.8
    
    def detect_duplicates(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Detect duplicate code blocks in the AST."""
        recommendations = []
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(tree, context)
        
        # Find duplicates
        duplicates = self._find_duplicate_blocks(code_blocks)
        
        # Generate recommendations
        for duplicate in duplicates:
            if len(duplicate.occurrences) > 1:
                rec = self._create_duplicate_recommendation(duplicate, context)
                recommendations.append(rec)
        
        return recommendations
    
    def _extract_code_blocks(self, tree: ast.AST, context: AnalysisContext) -> List[CodePattern]:
        """Extract code blocks from AST for duplicate detection."""
        blocks = []
        
        class BlockExtractor(ast.NodeVisitor):
            def __init__(self, detector):
                self.detector = detector
                self.blocks = []
            
            def visit_FunctionDef(self, node):
                block = self._create_code_pattern(node, "function", context)
                if block:
                    self.blocks.append(block)
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                block = self._create_code_pattern(node, "class", context)
                if block:
                    self.blocks.append(block)
                self.generic_visit(node)
            
            def visit_If(self, node):
                block = self._create_code_pattern(node, "if_block", context)
                if block:
                    self.blocks.append(block)
                self.generic_visit(node)
            
            def visit_For(self, node):
                block = self._create_code_pattern(node, "for_loop", context)
                if block:
                    self.blocks.append(block)
                self.generic_visit(node)
            
            def visit_While(self, node):
                block = self._create_code_pattern(node, "while_loop", context)
                if block:
                    self.blocks.append(block)
                self.generic_visit(node)
            
            def _create_code_pattern(self, node, pattern_type, context):
                try:
                    # Get source segment or fallback to manual extraction
                    code_snippet = None
                    try:
                        code_snippet = ast.get_source_segment(context.file_content, node)
                    except (AttributeError, TypeError):
                        # Fallback for older Python versions or when source segment fails
                        lines = context.file_content.split('\n')
                        start_line = node.lineno - 1
                        end_line = getattr(node, 'end_lineno', node.lineno) - 1
                        if start_line < len(lines) and end_line < len(lines):
                            code_snippet = '\n'.join(lines[start_line:end_line + 1])
                    
                    if not code_snippet or len(code_snippet.split('\n')) < self.detector.min_lines:
                        return None
                    
                    # Normalize code for comparison
                    normalized = self.detector._normalize_code(code_snippet)
                    pattern_hash = hashlib.md5(normalized.encode()).hexdigest()
                    
                    return CodePattern(
                        pattern_type=pattern_type,
                        pattern_hash=pattern_hash,
                        file_path=context.file_path,
                        start_line=node.lineno,
                        end_line=getattr(node, 'end_lineno', node.lineno),
                        code_snippet=code_snippet,
                        complexity_score=self.detector._calculate_complexity(node)
                    )
                except Exception as e:
                    # For debugging - in production this would be logged
                    return None
        
        extractor = BlockExtractor(self)
        extractor.visit(tree)
        return extractor.blocks
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for duplicate detection."""
        try:
            # Parse the code to get structural information
            tree = ast.parse(code)
            
            # Create a structural signature instead of normalizing names
            signature_parts = []
            
            class StructureExtractor(ast.NodeVisitor):
                def __init__(self):
                    self.structure = []
                
                def visit_FunctionDef(self, node):
                    self.structure.append(f"function({len(node.args.args)})")
                    self.generic_visit(node)
                
                def visit_ClassDef(self, node):
                    self.structure.append("class")
                    self.generic_visit(node)
                
                def visit_If(self, node):
                    self.structure.append("if")
                    self.generic_visit(node)
                
                def visit_For(self, node):
                    self.structure.append("for")
                    self.generic_visit(node)
                
                def visit_While(self, node):
                    self.structure.append("while")
                    self.generic_visit(node)
                
                def visit_Assign(self, node):
                    self.structure.append(f"assign({len(node.targets)})")
                    self.generic_visit(node)
                
                def visit_Return(self, node):
                    self.structure.append("return")
                    self.generic_visit(node)
                
                def visit_BinOp(self, node):
                    op_name = type(node.op).__name__.lower()
                    self.structure.append(f"binop_{op_name}")
                    self.generic_visit(node)
            
            extractor = StructureExtractor()
            extractor.visit(tree)
            
            # Combine structural signature with simplified code
            structural_signature = "|".join(extractor.structure)
            
            # Also include simplified code content (without names)
            lines = []
            for line in code.split('\n'):
                # Remove comments
                if '#' in line:
                    line = line[:line.index('#')]
                # Normalize whitespace
                line = ' '.join(line.split())
                # Replace function/variable names with placeholders
                import re
                line = re.sub(r'\bdef\s+\w+\s*\(', 'def FUNC(', line)
                line = re.sub(r'\bclass\s+\w+\s*:', 'class CLASS:', line)
                if line:
                    lines.append(line)
            
            simplified_code = '\n'.join(lines)
            
            # Combine both for better duplicate detection
            return f"{structural_signature}\n---\n{simplified_code}"
            
        except Exception:
            # Fallback to simple normalization
            lines = []
            for line in code.split('\n'):
                # Remove comments
                if '#' in line:
                    line = line[:line.index('#')]
                # Normalize whitespace and function names
                line = ' '.join(line.split())
                import re
                line = re.sub(r'\bdef\s+\w+\s*\(', 'def FUNC(', line)
                line = re.sub(r'\bclass\s+\w+\s*:', 'class CLASS:', line)
                if line:
                    lines.append(line)
            return '\n'.join(lines)
    
    def _calculate_complexity(self, node: ast.AST) -> float:
        """Calculate complexity score for a code block."""
        complexity = 1  # Base complexity
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 1
            
            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_Try(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_ExceptHandler(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        visitor = ComplexityVisitor()
        visitor.visit(node)
        return visitor.complexity
    
    def _find_duplicate_blocks(self, blocks: List[CodePattern]) -> List[DuplicateCodeBlock]:
        """Find duplicate blocks based on pattern hash."""
        hash_groups = defaultdict(list)
        
        for block in blocks:
            hash_groups[block.pattern_hash].append(block)
        
        duplicates = []
        for pattern_hash, group in hash_groups.items():
            if len(group) > 1:
                duplicate = DuplicateCodeBlock(
                    pattern_hash=pattern_hash,
                    occurrences=group,
                    similarity_score=1.0,  # Exact match
                    lines_count=len(group[0].code_snippet.split('\n'))
                )
                duplicates.append(duplicate)
        
        return duplicates
    
    def _create_duplicate_recommendation(self, duplicate: DuplicateCodeBlock, 
                                       context: AnalysisContext) -> ImprovementRecommendation:
        """Create a recommendation for duplicate code removal."""
        occurrences = duplicate.occurrences
        first_occurrence = occurrences[0]
        
        # Generate consolidation suggestion
        if first_occurrence.pattern_type == "function":
            suggestion = self._suggest_function_extraction(duplicate)
        elif first_occurrence.pattern_type == "class":
            suggestion = self._suggest_class_refactoring(duplicate)
        else:
            suggestion = self._suggest_code_extraction(duplicate)
        
        return ImprovementRecommendation(
            id=f"dup_{duplicate.pattern_hash[:8]}",
            recommendation_type=RecommendationType.DUPLICATE_REMOVAL,
            title=f"Duplicate {first_occurrence.pattern_type} detected",
            description=f"Found {len(occurrences)} similar code blocks that could be consolidated",
            file_path=context.file_path,
            line_number=first_occurrence.start_line,
            severity=Severity.MEDIUM if len(occurrences) > 2 else Severity.LOW,
            impact_score=len(occurrences) * duplicate.lines_count * 0.1,
            effort_estimate="medium",
            code_before=first_occurrence.code_snippet,
            code_after=suggestion,
            rationale=f"Consolidating {len(occurrences)} duplicate blocks will improve maintainability and reduce code size",
            tags=["duplication", "refactoring", first_occurrence.pattern_type]
        )
    
    def _suggest_function_extraction(self, duplicate: DuplicateCodeBlock) -> str:
        """Suggest function extraction for duplicate functions."""
        return f"""# Extract common functionality into a shared function
def extracted_common_function():
    # Common implementation here
    pass

# Replace duplicates with calls to the extracted function"""
    
    def _suggest_class_refactoring(self, duplicate: DuplicateCodeBlock) -> str:
        """Suggest class refactoring for duplicate classes."""
        return f"""# Create a base class with common functionality
class BaseClass:
    # Common implementation here
    pass

# Inherit from base class instead of duplicating code"""
    
    def _suggest_code_extraction(self, duplicate: DuplicateCodeBlock) -> str:
        """Suggest code extraction for duplicate code blocks."""
        return f"""# Extract duplicate code into a reusable function
def extracted_function():
    # Duplicate code implementation here
    pass

# Replace duplicate blocks with function calls"""


class PerformanceAnalyzer:
    """Analyzes code for performance optimization opportunities."""
    
    def analyze_performance(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Analyze code for performance issues and optimization opportunities."""
        recommendations = []
        
        class PerformanceVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.recommendations = []
            
            def visit_For(self, node):
                # Check for inefficient loops
                if self._is_inefficient_loop(node):
                    rec = self._create_loop_optimization_recommendation(node, context)
                    self.recommendations.append(rec)
                self.generic_visit(node)
            
            def visit_ListComp(self, node):
                # Check for complex list comprehensions
                if self._is_complex_comprehension(node):
                    rec = self._create_comprehension_optimization_recommendation(node, context)
                    self.recommendations.append(rec)
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # Check for inefficient function calls
                if self._is_inefficient_call(node):
                    rec = self._create_call_optimization_recommendation(node, context)
                    self.recommendations.append(rec)
                self.generic_visit(node)
            
            def _is_inefficient_loop(self, node):
                # Simple heuristic: nested loops with list operations
                return any(isinstance(child, ast.For) for child in ast.walk(node))
            
            def _is_complex_comprehension(self, node):
                # Check for nested comprehensions or complex conditions
                return len(list(ast.walk(node))) > 10
            
            def _is_inefficient_call(self, node):
                # Check for known inefficient patterns
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['append'] and len(node.args) > 0:
                        # Check if it's in a loop
                        return True
                return False
            
            def _create_loop_optimization_recommendation(self, node, context):
                return ImprovementRecommendation(
                    id=f"perf_loop_{node.lineno}",
                    recommendation_type=RecommendationType.PERFORMANCE_OPTIMIZATION,
                    title="Optimize nested loop performance",
                    description="Nested loops detected that could benefit from optimization",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=Severity.MEDIUM,
                    impact_score=5.0,
                    effort_estimate="medium",
                    rationale="Nested loops can cause O(n²) complexity. Consider using more efficient algorithms or data structures.",
                    tags=["performance", "loops", "complexity"]
                )
            
            def _create_comprehension_optimization_recommendation(self, node, context):
                return ImprovementRecommendation(
                    id=f"perf_comp_{node.lineno}",
                    recommendation_type=RecommendationType.PERFORMANCE_OPTIMIZATION,
                    title="Simplify complex list comprehension",
                    description="Complex list comprehension that could be optimized",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=Severity.LOW,
                    impact_score=2.0,
                    effort_estimate="low",
                    rationale="Complex comprehensions can be hard to read and may be slower than equivalent loops.",
                    tags=["performance", "comprehension", "readability"]
                )
            
            def _create_call_optimization_recommendation(self, node, context):
                return ImprovementRecommendation(
                    id=f"perf_call_{node.lineno}",
                    recommendation_type=RecommendationType.PERFORMANCE_OPTIMIZATION,
                    title="Optimize repeated function calls",
                    description="Function call pattern that could be optimized",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=Severity.LOW,
                    impact_score=3.0,
                    effort_estimate="low",
                    rationale="Repeated function calls in loops can be optimized by caching results or using bulk operations.",
                    tags=["performance", "function_calls", "optimization"]
                )
        
        visitor = PerformanceVisitor(self)
        visitor.visit(tree)
        return visitor.recommendations


class SecurityAnalyzer:
    """Analyzes code for security vulnerabilities and improvement opportunities."""
    
    def __init__(self):
        self.security_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'cursor\.execute\s*\(\s*["\'].*\+.*["\']'
            ],
            'command_injection': [
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(',
                r'eval\s*\(',
                r'exec\s*\('
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']'
            ]
        }
    
    def analyze_security(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Analyze code for security vulnerabilities."""
        recommendations = []
        
        # Check for dangerous function calls
        dangerous_calls = self._find_dangerous_calls(tree, context)
        recommendations.extend(dangerous_calls)
        
        # Check for hardcoded secrets
        hardcoded_secrets = self._find_hardcoded_secrets(tree, context)
        recommendations.extend(hardcoded_secrets)
        
        # Check for input validation issues
        input_validation = self._check_input_validation(tree, context)
        recommendations.extend(input_validation)
        
        return recommendations
    
    def _find_dangerous_calls(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Find potentially dangerous function calls."""
        recommendations = []
        
        class DangerousCallVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.recommendations = []
            
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec']:
                        rec = self._create_dangerous_call_recommendation(node, context, node.func.id)
                        self.recommendations.append(rec)
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['system'] and isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                        rec = self._create_dangerous_call_recommendation(node, context, 'os.system')
                        self.recommendations.append(rec)
                
                self.generic_visit(node)
            
            def _create_dangerous_call_recommendation(self, node, context, function_name):
                severity_map = {
                    'eval': Severity.CRITICAL,
                    'exec': Severity.CRITICAL,
                    'os.system': Severity.HIGH
                }
                
                return ImprovementRecommendation(
                    id=f"sec_call_{node.lineno}_{function_name.replace('.', '_')}",
                    recommendation_type=RecommendationType.SECURITY_IMPROVEMENT,
                    title=f"Dangerous function call: {function_name}",
                    description=f"Use of {function_name} can lead to code injection vulnerabilities",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=severity_map.get(function_name, Severity.HIGH),
                    impact_score=8.0,
                    effort_estimate="medium",
                    rationale=f"{function_name} can execute arbitrary code and should be avoided or used with extreme caution.",
                    tags=["security", "injection", "dangerous_function"],
                    references=[
                        "https://owasp.org/www-community/vulnerabilities/Code_Injection"
                    ]
                )
        
        visitor = DangerousCallVisitor(self)
        visitor.visit(tree)
        return visitor.recommendations
    
    def _find_hardcoded_secrets(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Find hardcoded secrets in the code."""
        recommendations = []
        
        # Use regex patterns to find potential secrets
        for pattern_type, patterns in self.security_patterns.items():
            if pattern_type == 'hardcoded_secrets':
                for pattern in patterns:
                    matches = re.finditer(pattern, context.file_content, re.IGNORECASE)
                    for match in matches:
                        line_number = context.file_content[:match.start()].count('\n') + 1
                        
                        rec = ImprovementRecommendation(
                            id=f"sec_secret_{line_number}",
                            recommendation_type=RecommendationType.SECURITY_IMPROVEMENT,
                            title="Hardcoded secret detected",
                            description="Hardcoded secrets should be moved to environment variables or secure configuration",
                            file_path=context.file_path,
                            line_number=line_number,
                            severity=Severity.HIGH,
                            impact_score=7.0,
                            effort_estimate="low",
                            rationale="Hardcoded secrets in source code can be exposed in version control and pose security risks.",
                            tags=["security", "secrets", "configuration"],
                            references=[
                                "https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password"
                            ]
                        )
                        recommendations.append(rec)
        
        return recommendations
    
    def _check_input_validation(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Check for missing input validation."""
        recommendations = []
        
        class InputValidationVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.recommendations = []
            
            def visit_FunctionDef(self, node):
                # Check if function parameters are validated
                if node.args.args and not self._has_input_validation(node):
                    rec = self._create_input_validation_recommendation(node, context)
                    self.recommendations.append(rec)
                
                self.generic_visit(node)
            
            def _has_input_validation(self, node):
                # Simple heuristic: look for isinstance, assert, or if statements
                for child in ast.walk(node):
                    if isinstance(child, (ast.Assert, ast.If)):
                        return True
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        if child.func.id in ['isinstance', 'type', 'len']:
                            return True
                return False
            
            def _create_input_validation_recommendation(self, node, context):
                return ImprovementRecommendation(
                    id=f"sec_validation_{node.lineno}",
                    recommendation_type=RecommendationType.SECURITY_IMPROVEMENT,
                    title="Missing input validation",
                    description=f"Function '{node.name}' should validate its input parameters",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=Severity.MEDIUM,
                    impact_score=4.0,
                    effort_estimate="low",
                    rationale="Input validation helps prevent security vulnerabilities and improves code robustness.",
                    tags=["security", "validation", "robustness"]
                )
        
        visitor = InputValidationVisitor(self)
        visitor.visit(tree)
        return visitor.recommendations


class PatternAnalyzer:
    """Analyzes code patterns and suggests design improvements."""
    
    def analyze_patterns(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Analyze code patterns and suggest improvements."""
        recommendations = []
        
        # Check for long functions
        long_functions = self._find_long_functions(tree, context)
        recommendations.extend(long_functions)
        
        # Check for complex conditions
        complex_conditions = self._find_complex_conditions(tree, context)
        recommendations.extend(complex_conditions)
        
        # Check for code smells
        code_smells = self._find_code_smells(tree, context)
        recommendations.extend(code_smells)
        
        return recommendations
    
    def _find_long_functions(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Find functions that are too long."""
        recommendations = []
        max_lines = 50  # Configurable threshold
        
        class LongFunctionVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.recommendations = []
            
            def visit_FunctionDef(self, node):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    function_length = node.end_lineno - node.lineno + 1
                    if function_length > max_lines:
                        rec = self._create_long_function_recommendation(node, context, function_length)
                        self.recommendations.append(rec)
                
                self.generic_visit(node)
            
            def _create_long_function_recommendation(self, node, context, length):
                return ImprovementRecommendation(
                    id=f"pattern_long_func_{node.lineno}",
                    recommendation_type=RecommendationType.REFACTORING,
                    title=f"Long function detected ({length} lines)",
                    description=f"Function '{node.name}' is {length} lines long and should be refactored",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=Severity.MEDIUM if length > 100 else Severity.LOW,
                    impact_score=length * 0.1,
                    effort_estimate="high" if length > 100 else "medium",
                    rationale="Long functions are harder to understand, test, and maintain. Consider breaking them into smaller functions.",
                    tags=["refactoring", "function_length", "maintainability"]
                )
        
        visitor = LongFunctionVisitor(self)
        visitor.visit(tree)
        return visitor.recommendations
    
    def _find_complex_conditions(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Find complex conditional statements."""
        recommendations = []
        
        class ComplexConditionVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.recommendations = []
            
            def visit_If(self, node):
                complexity = self._calculate_condition_complexity(node.test)
                if complexity > 3:  # Threshold for complex conditions
                    rec = self._create_complex_condition_recommendation(node, context, complexity)
                    self.recommendations.append(rec)
                
                self.generic_visit(node)
            
            def _calculate_condition_complexity(self, node):
                """Calculate complexity of a condition."""
                if isinstance(node, ast.BoolOp):
                    return 1 + sum(self._calculate_condition_complexity(value) for value in node.values)
                elif isinstance(node, ast.Compare):
                    return len(node.comparators)
                else:
                    return 1
            
            def _create_complex_condition_recommendation(self, node, context, complexity):
                return ImprovementRecommendation(
                    id=f"pattern_complex_cond_{node.lineno}",
                    recommendation_type=RecommendationType.CODE_SIMPLIFICATION,
                    title=f"Complex condition detected (complexity: {complexity})",
                    description="Complex conditional statement that could be simplified",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=Severity.LOW,
                    impact_score=complexity * 0.5,
                    effort_estimate="low",
                    rationale="Complex conditions are harder to understand and test. Consider extracting them into well-named variables or functions.",
                    tags=["simplification", "conditions", "readability"]
                )
        
        visitor = ComplexConditionVisitor(self)
        visitor.visit(tree)
        return visitor.recommendations
    
    def _find_code_smells(self, tree: ast.AST, context: AnalysisContext) -> List[ImprovementRecommendation]:
        """Find common code smells."""
        recommendations = []
        
        class CodeSmellVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.recommendations = []
            
            def visit_FunctionDef(self, node):
                # Check for too many parameters
                if len(node.args.args) > 5:
                    rec = self._create_too_many_params_recommendation(node, context)
                    self.recommendations.append(rec)
                
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                # Check for god classes (too many methods)
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    rec = self._create_god_class_recommendation(node, context, len(methods))
                    self.recommendations.append(rec)
                
                self.generic_visit(node)
            
            def _create_too_many_params_recommendation(self, node, context):
                return ImprovementRecommendation(
                    id=f"smell_params_{node.lineno}",
                    recommendation_type=RecommendationType.REFACTORING,
                    title=f"Too many parameters ({len(node.args.args)})",
                    description=f"Function '{node.name}' has too many parameters",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=Severity.LOW,
                    impact_score=len(node.args.args) * 0.2,
                    effort_estimate="medium",
                    rationale="Functions with many parameters are hard to use and maintain. Consider using parameter objects or builder patterns.",
                    tags=["refactoring", "parameters", "design"]
                )
            
            def _create_god_class_recommendation(self, node, context, method_count):
                return ImprovementRecommendation(
                    id=f"smell_god_class_{node.lineno}",
                    recommendation_type=RecommendationType.REFACTORING,
                    title=f"God class detected ({method_count} methods)",
                    description=f"Class '{node.name}' has too many responsibilities",
                    file_path=context.file_path,
                    line_number=node.lineno,
                    severity=Severity.MEDIUM,
                    impact_score=method_count * 0.1,
                    effort_estimate="high",
                    rationale="Classes with too many methods violate the Single Responsibility Principle. Consider splitting into smaller, focused classes.",
                    tags=["refactoring", "class_design", "solid_principles"]
                )
        
        visitor = CodeSmellVisitor(self)
        visitor.visit(tree)
        return visitor.recommendations