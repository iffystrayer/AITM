"""
Automated code formatting and style fixing engine.
"""

import os
import re
import ast
import shutil
import tempfile
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from enum import Enum

from .base_analyzer import AnalysisContext
from app.models.quality import QualityIssue, AutoFixResult, FixType, SafetyLevel
from app.core.quality_config import QualityConfigManager


class FixStatus(str, Enum):
    """Status of fix application."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNSAFE = "unsafe"
    CONFLICT = "conflict"


@dataclass
class FixableIssue:
    """Represents an issue that can be automatically fixed."""
    issue: QualityIssue
    fix_type: FixType
    confidence: float  # 0.0 to 1.0
    fix_description: str
    original_content: str
    fixed_content: str
    line_range: Tuple[int, int]  # (start_line, end_line)
    requires_backup: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixApplicationResult:
    """Result of applying fixes to a file."""
    file_path: str
    fixes_attempted: int
    fixes_applied: int
    fixes_failed: int
    fixes_skipped: int
    backup_path: Optional[str] = None
    final_content: str = ""
    applied_fixes: List[AutoFixResult] = field(default_factory=list)
    failed_fixes: List[AutoFixResult] = field(default_factory=list)
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class CodeFixer(ABC):
    """Abstract base class for code fixers."""
    
    def __init__(self, name: str, fix_type: FixType, supported_languages: Set[str]):
        self.name = name
        self.fix_type = fix_type
        self.supported_languages = supported_languages
        self.configuration: Dict[str, Any] = {}
        self.safety_level = SafetyLevel.CONSERVATIVE
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the fixer with settings."""
        self.configuration.update(config)
        if 'safety_level' in config:
            self.safety_level = SafetyLevel(config['safety_level'])
    
    def supports_language(self, language: str) -> bool:
        """Check if fixer supports the given language."""
        return language in self.supported_languages
    
    def can_fix_issue(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        """Check if this fixer can handle the given issue."""
        return (self.supports_language(context.language) and 
                self._can_fix_implementation(issue, context))
    
    @abstractmethod
    def _can_fix_implementation(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        """Implementation-specific check for fixability."""
        pass
    
    def analyze_fixable_issue(self, issue: QualityIssue, context: AnalysisContext) -> Optional[FixableIssue]:
        """Analyze an issue and return a fixable issue if possible."""
        if not self.can_fix_issue(issue, context):
            return None
        
        return self._analyze_fixable_implementation(issue, context)
    
    @abstractmethod
    def _analyze_fixable_implementation(self, issue: QualityIssue, 
                                      context: AnalysisContext) -> Optional[FixableIssue]:
        """Implementation-specific analysis of fixable issue."""
        pass
    
    def apply_fix(self, fixable_issue: FixableIssue, context: AnalysisContext) -> AutoFixResult:
        """Apply a fix to the code."""
        start_time = datetime.now()
        
        try:
            result = self._apply_fix_implementation(fixable_issue, context)
            result.applied_at = datetime.now(timezone.utc)
            return result
            
        except Exception as e:
            return AutoFixResult(
                issue_id=fixable_issue.issue.id,
                project_id=context.project_id,
                file_path=context.file_path,
                fix_type=self.fix_type,
                success=False,
                error_message=str(e),
                applied_at=datetime.now(timezone.utc)
            )
    
    @abstractmethod
    def _apply_fix_implementation(self, fixable_issue: FixableIssue, 
                                context: AnalysisContext) -> AutoFixResult:
        """Implementation-specific fix application."""
        pass


class TrailingWhitespaceFixer(CodeFixer):
    """Fixes trailing whitespace issues."""
    
    def __init__(self):
        super().__init__("TrailingWhitespaceFixer", FixType.FORMATTING, set())  # All languages
    
    def supports_language(self, language: str) -> bool:
        """Support all languages for trailing whitespace fixes."""
        return True
    
    def _can_fix_implementation(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        return issue.category == "trailing_whitespace"
    
    def _analyze_fixable_implementation(self, issue: QualityIssue, 
                                      context: AnalysisContext) -> Optional[FixableIssue]:
        lines = context.file_content.split('\n')
        if issue.line_number and 1 <= issue.line_number <= len(lines):
            line_idx = issue.line_number - 1
            original_line = lines[line_idx]
            fixed_line = original_line.rstrip()
            
            if original_line != fixed_line:
                lines[line_idx] = fixed_line
                fixed_content = '\n'.join(lines)
                
                return FixableIssue(
                    issue=issue,
                    fix_type=self.fix_type,
                    confidence=1.0,  # Very safe fix
                    fix_description="Remove trailing whitespace",
                    original_content=context.file_content,
                    fixed_content=fixed_content,
                    line_range=(issue.line_number, issue.line_number),
                    requires_backup=False  # Safe fix
                )
        
        return None
    
    def _apply_fix_implementation(self, fixable_issue: FixableIssue, 
                                context: AnalysisContext) -> AutoFixResult:
        return AutoFixResult(
            issue_id=fixable_issue.issue.id,
            project_id=context.project_id,
            file_path=context.file_path,
            fix_type=self.fix_type,
            original_content=fixable_issue.original_content,
            fixed_content=fixable_issue.fixed_content,
            success=True
        )


class MultipleBlankLinesFixer(CodeFixer):
    """Fixes multiple consecutive blank lines."""
    
    def __init__(self):
        super().__init__("MultipleBlankLinesFixer", FixType.FORMATTING, set())  # All languages
    
    def supports_language(self, language: str) -> bool:
        """Support all languages for blank line fixes."""
        return True
    
    def _can_fix_implementation(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        return issue.category == "multiple_blank_lines"
    
    def _analyze_fixable_implementation(self, issue: QualityIssue, 
                                      context: AnalysisContext) -> Optional[FixableIssue]:
        # Replace multiple consecutive blank lines with single blank line
        fixed_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', context.file_content)
        
        if fixed_content != context.file_content:
            return FixableIssue(
                issue=issue,
                fix_type=self.fix_type,
                confidence=0.9,  # Generally safe
                fix_description="Reduce multiple blank lines to single blank line",
                original_content=context.file_content,
                fixed_content=fixed_content,
                line_range=(1, len(context.file_content.split('\n'))),
                requires_backup=False
            )
        
        return None
    
    def _apply_fix_implementation(self, fixable_issue: FixableIssue, 
                                context: AnalysisContext) -> AutoFixResult:
        return AutoFixResult(
            issue_id=fixable_issue.issue.id,
            project_id=context.project_id,
            file_path=context.file_path,
            fix_type=self.fix_type,
            original_content=fixable_issue.original_content,
            fixed_content=fixable_issue.fixed_content,
            success=True
        )


class PythonImportSorter(CodeFixer):
    """Sorts and organizes Python imports."""
    
    def __init__(self):
        super().__init__("PythonImportSorter", FixType.IMPORTS, {"python"})
    
    def _can_fix_implementation(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        return (issue.category in ["import_order", "unused_import"] and 
                context.language == "python")
    
    def _analyze_fixable_implementation(self, issue: QualityIssue, 
                                      context: AnalysisContext) -> Optional[FixableIssue]:
        try:
            # Parse the AST to find imports
            tree = ast.parse(context.file_content)
            imports = []
            other_nodes = []
            
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node)
                else:
                    other_nodes.append(node)
            
            if not imports:
                return None
            
            # Sort imports by category
            standard_imports = []
            third_party_imports = []
            local_imports = []
            
            for imp in imports:
                if isinstance(imp, ast.Import):
                    module_name = imp.names[0].name
                elif isinstance(imp, ast.ImportFrom):
                    module_name = imp.module or ""
                else:
                    continue
                
                if self._is_standard_library(module_name):
                    standard_imports.append(imp)
                elif self._is_local_import(module_name):
                    local_imports.append(imp)
                else:
                    third_party_imports.append(imp)
            
            # Generate sorted import section
            sorted_imports = []
            for import_group in [standard_imports, third_party_imports, local_imports]:
                if import_group:
                    sorted_imports.extend(import_group)
                    if import_group != local_imports:  # Don't add blank line after last group
                        sorted_imports.append(None)  # Placeholder for blank line
            
            # Reconstruct the file with sorted imports
            lines = context.file_content.split('\n')
            
            # Find the end of the import section
            import_end_line = 0
            for node in imports:
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    import_end_line = max(import_end_line, node.end_lineno)
            
            if import_end_line > 0:
                # Replace import section with sorted imports
                new_import_lines = []
                for imp in sorted_imports:
                    if imp is None:
                        new_import_lines.append("")  # Blank line
                    else:
                        new_import_lines.append(ast.unparse(imp))
                
                # Reconstruct file
                before_imports = lines[:imports[0].lineno - 1] if imports else []
                after_imports = lines[import_end_line:] if import_end_line < len(lines) else []
                
                new_lines = before_imports + new_import_lines + after_imports
                fixed_content = '\n'.join(new_lines)
                
                if fixed_content != context.file_content:
                    return FixableIssue(
                        issue=issue,
                        fix_type=self.fix_type,
                        confidence=0.8,  # Moderately safe
                        fix_description="Sort and organize imports",
                        original_content=context.file_content,
                        fixed_content=fixed_content,
                        line_range=(imports[0].lineno, import_end_line),
                        requires_backup=True
                    )
            
        except Exception as e:
            print(f"Error analyzing Python imports: {e}")
        
        return None
    
    def _apply_fix_implementation(self, fixable_issue: FixableIssue, 
                                context: AnalysisContext) -> AutoFixResult:
        return AutoFixResult(
            issue_id=fixable_issue.issue.id,
            project_id=context.project_id,
            file_path=context.file_path,
            fix_type=self.fix_type,
            original_content=fixable_issue.original_content,
            fixed_content=fixable_issue.fixed_content,
            success=True
        )
    
    def _is_standard_library(self, module_name: str) -> bool:
        """Check if module is part of Python standard library."""
        standard_modules = {
            'os', 'sys', 'json', 're', 'time', 'datetime', 'collections',
            'itertools', 'functools', 'pathlib', 'typing', 'dataclasses',
            'abc', 'enum', 'uuid', 'hashlib', 'tempfile', 'shutil',
            'subprocess', 'threading', 'asyncio', 'sqlite3', 'urllib',
            'http', 'email', 'xml', 'csv', 'configparser', 'logging'
        }
        
        base_module = module_name.split('.')[0]
        return base_module in standard_modules
    
    def _is_local_import(self, module_name: str) -> bool:
        """Check if module is a local import."""
        return module_name.startswith('.') or module_name.startswith('app.')


class ExternalFormatterFixer(CodeFixer):
    """Uses external formatting tools like black, prettier, etc."""
    
    def __init__(self, formatter_command: str, fix_type: FixType, 
                 supported_languages: Set[str]):
        super().__init__(f"ExternalFormatter_{formatter_command}", fix_type, supported_languages)
        self.formatter_command = formatter_command
        self.formatter_args: List[str] = []
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the external formatter."""
        super().configure(config)
        if 'formatter_args' in config:
            self.formatter_args = config['formatter_args']
    
    def _can_fix_implementation(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        # Can fix various formatting issues
        fixable_categories = {
            "long_line", "indentation", "spacing", "formatting",
            "style", "trailing_whitespace"
        }
        return issue.category in fixable_categories
    
    def _analyze_fixable_implementation(self, issue: QualityIssue, 
                                      context: AnalysisContext) -> Optional[FixableIssue]:
        # Check if formatter is available
        if not self._is_formatter_available():
            return None
        
        try:
            # Run formatter on content
            fixed_content = self._run_formatter(context.file_content, context.file_path)
            
            if fixed_content and fixed_content != context.file_content:
                return FixableIssue(
                    issue=issue,
                    fix_type=self.fix_type,
                    confidence=0.9,  # External formatters are generally reliable
                    fix_description=f"Format code using {self.formatter_command}",
                    original_content=context.file_content,
                    fixed_content=fixed_content,
                    line_range=(1, len(context.file_content.split('\n'))),
                    requires_backup=True
                )
            
        except Exception as e:
            print(f"Error running formatter {self.formatter_command}: {e}")
        
        return None
    
    def _apply_fix_implementation(self, fixable_issue: FixableIssue, 
                                context: AnalysisContext) -> AutoFixResult:
        return AutoFixResult(
            issue_id=fixable_issue.issue.id,
            project_id=context.project_id,
            file_path=context.file_path,
            fix_type=self.fix_type,
            original_content=fixable_issue.original_content,
            fixed_content=fixable_issue.fixed_content,
            success=True
        )
    
    def _is_formatter_available(self) -> bool:
        """Check if the formatter command is available."""
        try:
            result = subprocess.run([self.formatter_command, '--version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _run_formatter(self, content: str, file_path: str) -> Optional[str]:
        """Run the external formatter on the content."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix=Path(file_path).suffix, 
                                           delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Run formatter
                cmd = [self.formatter_command] + self.formatter_args + [temp_path]
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    # Read formatted content
                    with open(temp_path, 'r') as f:
                        return f.read()
                else:
                    print(f"Formatter failed: {result.stderr.decode()}")
                    return None
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"Error running formatter: {e}")
            return None


class AutoFixEngine:
    """Main engine for applying automatic fixes."""
    
    def __init__(self, config_manager: Optional[QualityConfigManager] = None):
        self.config_manager = config_manager or QualityConfigManager()
        self.fixers: List[CodeFixer] = []
        self.backup_directory = Path("backups")
        self.max_fixes_per_file = 50
        self.safety_level = SafetyLevel.CONSERVATIVE
        
        # Initialize default fixers
        self._initialize_default_fixers()
    
    def _initialize_default_fixers(self) -> None:
        """Initialize default code fixers."""
        # Basic formatting fixers
        self.add_fixer(TrailingWhitespaceFixer())
        self.add_fixer(MultipleBlankLinesFixer())
        self.add_fixer(PythonImportSorter())
        
        # External formatter fixers (if available)
        black_fixer = ExternalFormatterFixer("black", FixType.FORMATTING, {"python"})
        black_fixer.configure({"formatter_args": ["--line-length", "88", "--quiet"]})
        self.add_fixer(black_fixer)
        
        prettier_fixer = ExternalFormatterFixer("prettier", FixType.FORMATTING, 
                                               {"javascript", "typescript"})
        prettier_fixer.configure({"formatter_args": ["--write"]})
        self.add_fixer(prettier_fixer)
    
    def add_fixer(self, fixer: CodeFixer) -> None:
        """Add a code fixer to the engine."""
        self.fixers.append(fixer)
    
    def remove_fixer(self, fixer_name: str) -> bool:
        """Remove a fixer by name."""
        initial_count = len(self.fixers)
        self.fixers = [f for f in self.fixers if f.name != fixer_name]
        return len(self.fixers) < initial_count
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the auto-fix engine."""
        if 'safety_level' in config:
            self.safety_level = SafetyLevel(config['safety_level'])
        
        if 'max_fixes_per_file' in config:
            self.max_fixes_per_file = config['max_fixes_per_file']
        
        if 'backup_directory' in config:
            self.backup_directory = Path(config['backup_directory'])
        
        # Configure individual fixers
        if 'fixer_configs' in config:
            for fixer_name, fixer_config in config['fixer_configs'].items():
                for fixer in self.fixers:
                    if fixer.name == fixer_name:
                        fixer.configure(fixer_config)
    
    def analyze_fixable_issues(self, issues: List[QualityIssue], 
                             context: AnalysisContext) -> List[FixableIssue]:
        """Analyze issues and return those that can be automatically fixed."""
        fixable_issues = []
        
        for issue in issues:
            for fixer in self.fixers:
                if fixer.can_fix_issue(issue, context):
                    fixable_issue = fixer.analyze_fixable_issue(issue, context)
                    if fixable_issue:
                        # Check safety level
                        if self._is_fix_safe_enough(fixable_issue):
                            fixable_issues.append(fixable_issue)
                        break  # Only use first applicable fixer
        
        # Sort by confidence and safety
        fixable_issues.sort(key=lambda x: (-x.confidence, x.requires_backup))
        
        # Limit number of fixes
        return fixable_issues[:self.max_fixes_per_file]
    
    def apply_fixes(self, fixable_issues: List[FixableIssue], 
                   context: AnalysisContext, backup_enabled: bool = True) -> FixApplicationResult:
        """Apply fixes to a file."""
        start_time = datetime.now()
        
        result = FixApplicationResult(
            file_path=context.file_path,
            fixes_attempted=len(fixable_issues),
            fixes_applied=0,
            fixes_failed=0,
            fixes_skipped=0
        )
        
        try:
            # Create backup if needed
            if backup_enabled and any(fix.requires_backup for fix in fixable_issues):
                result.backup_path = self._create_backup(context.file_path, context.file_content)
            
            # Apply fixes in order
            current_content = context.file_content
            
            for fixable_issue in fixable_issues:
                try:
                    # Update context with current content
                    current_context = AnalysisContext(
                        project_id=context.project_id,
                        file_path=context.file_path,
                        file_content=current_content,
                        language=context.language
                    )
                    
                    # Find appropriate fixer
                    fixer = self._find_fixer_for_issue(fixable_issue)
                    if not fixer:
                        result.fixes_skipped += 1
                        continue
                    
                    # Apply fix
                    fix_result = fixer.apply_fix(fixable_issue, current_context)
                    
                    if fix_result.success and fix_result.fixed_content:
                        current_content = fix_result.fixed_content
                        result.applied_fixes.append(fix_result)
                        result.fixes_applied += 1
                    else:
                        result.failed_fixes.append(fix_result)
                        result.fixes_failed += 1
                        
                except Exception as e:
                    error_fix = AutoFixResult(
                        issue_id=fixable_issue.issue.id,
                        project_id=context.project_id,
                        file_path=context.file_path,
                        fix_type=fixable_issue.fix_type,
                        success=False,
                        error_message=str(e)
                    )
                    result.failed_fixes.append(error_fix)
                    result.fixes_failed += 1
            
            result.final_content = current_content
            result.success = result.fixes_failed == 0
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
        
        finally:
            result.execution_time = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def rollback_fixes(self, backup_path: str, target_path: str) -> bool:
        """Rollback fixes using backup file."""
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, target_path)
                return True
        except Exception as e:
            print(f"Error rolling back fixes: {e}")
        
        return False
    
    def validate_fixes(self, fix_result: FixApplicationResult, 
                      context: AnalysisContext) -> bool:
        """Validate that applied fixes don't break the code."""
        if not fix_result.final_content:
            return False
        
        # For Python files, try to parse the AST
        if context.language == "python":
            try:
                ast.parse(fix_result.final_content)
                return True
            except SyntaxError:
                return False
        
        # For other languages, basic validation
        return len(fix_result.final_content.strip()) > 0
    
    def _is_fix_safe_enough(self, fixable_issue: FixableIssue) -> bool:
        """Check if fix meets safety requirements."""
        if self.safety_level == SafetyLevel.AGGRESSIVE:
            return fixable_issue.confidence >= 0.5
        elif self.safety_level == SafetyLevel.MODERATE:
            return fixable_issue.confidence >= 0.7
        else:  # CONSERVATIVE
            return fixable_issue.confidence >= 0.9
    
    def _find_fixer_for_issue(self, fixable_issue: FixableIssue) -> Optional[CodeFixer]:
        """Find the appropriate fixer for a fixable issue."""
        for fixer in self.fixers:
            if fixer.fix_type == fixable_issue.fix_type:
                return fixer
        return None
    
    def _create_backup(self, file_path: str, content: str) -> str:
        """Create a backup of the file content."""
        self.backup_directory.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = Path(file_path).name
        backup_name = f"{file_name}.{timestamp}.backup"
        backup_path = self.backup_directory / backup_name
        
        with open(backup_path, 'w') as f:
            f.write(content)
        
        return str(backup_path)
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            'total_fixers': len(self.fixers),
            'fixers_by_type': {
                fix_type.value: len([f for f in self.fixers if f.fix_type == fix_type])
                for fix_type in FixType
            },
            'safety_level': self.safety_level.value,
            'max_fixes_per_file': self.max_fixes_per_file,
            'backup_directory': str(self.backup_directory),
            'available_fixers': [f.name for f in self.fixers]
        }