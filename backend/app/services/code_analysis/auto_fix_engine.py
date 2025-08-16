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


class BlackFormatterFixer(CodeFixer):
    """Python code formatter using Black."""
    
    def __init__(self):
        super().__init__("BlackFormatter", FixType.FORMATTING, {"python"})
        self.line_length = 88
        self.skip_string_normalization = False
        self.target_versions = set()
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure Black formatter."""
        super().configure(config)
        if 'line_length' in config:
            self.line_length = config['line_length']
        if 'skip_string_normalization' in config:
            self.skip_string_normalization = config['skip_string_normalization']
        if 'target_versions' in config:
            self.target_versions = set(config['target_versions'])
    
    def _can_fix_implementation(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        fixable_categories = {
            "long_line", "indentation", "spacing", "formatting",
            "style", "trailing_whitespace", "quote_style"
        }
        return issue.category in fixable_categories
    
    def _analyze_fixable_implementation(self, issue: QualityIssue, 
                                      context: AnalysisContext) -> Optional[FixableIssue]:
        if not self._is_black_available():
            return None
        
        try:
            fixed_content = self._format_with_black(context.file_content)
            
            if fixed_content and fixed_content != context.file_content:
                return FixableIssue(
                    issue=issue,
                    fix_type=self.fix_type,
                    confidence=0.95,  # Black is very reliable
                    fix_description="Format Python code with Black",
                    original_content=context.file_content,
                    fixed_content=fixed_content,
                    line_range=(1, len(context.file_content.split('\n'))),
                    requires_backup=True
                )
            
        except Exception as e:
            print(f"Error running Black formatter: {e}")
        
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
    
    def _is_black_available(self) -> bool:
        """Check if Black is available."""
        try:
            import black
            return True
        except ImportError:
            try:
                result = subprocess.run(['black', '--version'], 
                                      capture_output=True, timeout=5)
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
    
    def _format_with_black(self, content: str) -> Optional[str]:
        """Format content using Black."""
        try:
            # Try to use Black as a library first
            import black
            
            mode = black.FileMode(
                line_length=self.line_length,
                string_normalization=not self.skip_string_normalization,
                target_versions=self.target_versions
            )
            
            return black.format_str(content, mode=mode)
            
        except ImportError:
            # Fall back to command line
            return self._format_with_black_cli(content)
        except Exception as e:
            print(f"Error formatting with Black library: {e}")
            return self._format_with_black_cli(content)
    
    def _format_with_black_cli(self, content: str) -> Optional[str]:
        """Format content using Black CLI."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                cmd = ['black', '--line-length', str(self.line_length)]
                if self.skip_string_normalization:
                    cmd.append('--skip-string-normalization')
                cmd.append(temp_path)
                
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    with open(temp_path, 'r') as f:
                        return f.read()
                else:
                    print(f"Black CLI failed: {result.stderr.decode()}")
                    return None
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"Error running Black CLI: {e}")
            return None


class IsortFormatterFixer(CodeFixer):
    """Python import sorter using isort."""
    
    def __init__(self):
        super().__init__("IsortFormatter", FixType.IMPORTS, {"python"})
        self.profile = "black"  # Compatible with Black
        self.line_length = 88
        self.multi_line_output = 3
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure isort formatter."""
        super().configure(config)
        if 'profile' in config:
            self.profile = config['profile']
        if 'line_length' in config:
            self.line_length = config['line_length']
        if 'multi_line_output' in config:
            self.multi_line_output = config['multi_line_output']
    
    def _can_fix_implementation(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        fixable_categories = {
            "import_order", "unused_import", "import_formatting",
            "import_style", "import_grouping"
        }
        return issue.category in fixable_categories
    
    def _analyze_fixable_implementation(self, issue: QualityIssue, 
                                      context: AnalysisContext) -> Optional[FixableIssue]:
        if not self._is_isort_available():
            return None
        
        try:
            fixed_content = self._format_with_isort(context.file_content)
            
            if fixed_content and fixed_content != context.file_content:
                return FixableIssue(
                    issue=issue,
                    fix_type=self.fix_type,
                    confidence=0.9,  # isort is very reliable for imports
                    fix_description="Sort and organize Python imports with isort",
                    original_content=context.file_content,
                    fixed_content=fixed_content,
                    line_range=(1, len(context.file_content.split('\n'))),
                    requires_backup=True
                )
            
        except Exception as e:
            print(f"Error running isort formatter: {e}")
        
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
    
    def _is_isort_available(self) -> bool:
        """Check if isort is available."""
        try:
            import isort
            return True
        except ImportError:
            try:
                result = subprocess.run(['isort', '--version'], 
                                      capture_output=True, timeout=5)
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
    
    def _format_with_isort(self, content: str) -> Optional[str]:
        """Format content using isort."""
        try:
            # Try to use isort as a library first
            import isort
            
            config = isort.Config(
                profile=self.profile,
                line_length=self.line_length,
                multi_line_output=self.multi_line_output
            )
            
            return isort.code(content, config=config)
            
        except ImportError:
            # Fall back to command line
            return self._format_with_isort_cli(content)
        except Exception as e:
            print(f"Error formatting with isort library: {e}")
            return self._format_with_isort_cli(content)
    
    def _format_with_isort_cli(self, content: str) -> Optional[str]:
        """Format content using isort CLI."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                cmd = [
                    'isort', 
                    '--profile', self.profile,
                    '--line-length', str(self.line_length),
                    '--multi-line', str(self.multi_line_output),
                    temp_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    with open(temp_path, 'r') as f:
                        return f.read()
                else:
                    print(f"isort CLI failed: {result.stderr.decode()}")
                    return None
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"Error running isort CLI: {e}")
            return None


class Autopep8FormatterFixer(CodeFixer):
    """Python code formatter using autopep8."""
    
    def __init__(self):
        super().__init__("Autopep8Formatter", FixType.FORMATTING, {"python"})
        self.max_line_length = 88
        self.aggressive_level = 1
        self.select_errors = []
        self.ignore_errors = []
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure autopep8 formatter."""
        super().configure(config)
        if 'max_line_length' in config:
            self.max_line_length = config['max_line_length']
        if 'aggressive_level' in config:
            self.aggressive_level = config['aggressive_level']
        if 'select_errors' in config:
            self.select_errors = config['select_errors']
        if 'ignore_errors' in config:
            self.ignore_errors = config['ignore_errors']
    
    def _can_fix_implementation(self, issue: QualityIssue, context: AnalysisContext) -> bool:
        fixable_categories = {
            "pep8_violation", "indentation", "spacing", "formatting",
            "style", "trailing_whitespace", "blank_lines"
        }
        return issue.category in fixable_categories
    
    def _analyze_fixable_implementation(self, issue: QualityIssue, 
                                      context: AnalysisContext) -> Optional[FixableIssue]:
        if not self._is_autopep8_available():
            return None
        
        try:
            fixed_content = self._format_with_autopep8(context.file_content)
            
            if fixed_content and fixed_content != context.file_content:
                return FixableIssue(
                    issue=issue,
                    fix_type=self.fix_type,
                    confidence=0.85,  # autopep8 is reliable but less opinionated than Black
                    fix_description="Fix PEP 8 violations with autopep8",
                    original_content=context.file_content,
                    fixed_content=fixed_content,
                    line_range=(1, len(context.file_content.split('\n'))),
                    requires_backup=True
                )
            
        except Exception as e:
            print(f"Error running autopep8 formatter: {e}")
        
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
    
    def _is_autopep8_available(self) -> bool:
        """Check if autopep8 is available."""
        try:
            import autopep8
            return True
        except ImportError:
            try:
                result = subprocess.run(['autopep8', '--version'], 
                                      capture_output=True, timeout=5)
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
    
    def _format_with_autopep8(self, content: str) -> Optional[str]:
        """Format content using autopep8."""
        try:
            # Try to use autopep8 as a library first
            import autopep8
            
            options = {
                'max_line_length': self.max_line_length,
                'aggressive': self.aggressive_level,
            }
            
            if self.select_errors:
                options['select'] = ','.join(self.select_errors)
            if self.ignore_errors:
                options['ignore'] = ','.join(self.ignore_errors)
            
            return autopep8.fix_code(content, options=options)
            
        except ImportError:
            # Fall back to command line
            return self._format_with_autopep8_cli(content)
        except Exception as e:
            print(f"Error formatting with autopep8 library: {e}")
            return self._format_with_autopep8_cli(content)
    
    def _format_with_autopep8_cli(self, content: str) -> Optional[str]:
        """Format content using autopep8 CLI."""
        try:
            cmd = [
                'autopep8',
                '--max-line-length', str(self.max_line_length),
                '--aggressive' * self.aggressive_level,
                '-'  # Read from stdin
            ]
            
            if self.select_errors:
                cmd.extend(['--select', ','.join(self.select_errors)])
            if self.ignore_errors:
                cmd.extend(['--ignore', ','.join(self.ignore_errors)])
            
            result = subprocess.run(cmd, input=content, text=True, 
                                  capture_output=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"autopep8 CLI failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"Error running autopep8 CLI: {e}")
            return None


class ExternalFormatterFixer(CodeFixer):
    """Generic external formatter for other languages."""
    
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
                    confidence=0.8,  # External formatters vary in reliability
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
        # Basic formatting fixers (language-agnostic)
        self.add_fixer(TrailingWhitespaceFixer())
        self.add_fixer(MultipleBlankLinesFixer())
        
        # Python-specific fixers
        self.add_fixer(PythonImportSorter())
        self.add_fixer(BlackFormatterFixer())
        self.add_fixer(IsortFormatterFixer())
        self.add_fixer(Autopep8FormatterFixer())
        
        # External formatter fixers for other languages
        prettier_fixer = ExternalFormatterFixer("prettier", FixType.FORMATTING, 
                                               {"javascript", "typescript", "json", "css", "html"})
        prettier_fixer.configure({"formatter_args": ["--write"]})
        self.add_fixer(prettier_fixer)
        
        # Additional external formatters
        rustfmt_fixer = ExternalFormatterFixer("rustfmt", FixType.FORMATTING, {"rust"})
        self.add_fixer(rustfmt_fixer)
        
        gofmt_fixer = ExternalFormatterFixer("gofmt", FixType.FORMATTING, {"go"})
        gofmt_fixer.configure({"formatter_args": ["-w"]})
        self.add_fixer(gofmt_fixer)
    
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
    
    def rollback_batch_fixes(self, fix_results: List[AutoFixResult]) -> Dict[str, Any]:
        """Rollback a batch of fixes using their backup information."""
        rollback_result = {
            'success': True,
            'restored_files': [],
            'failed_files': [],
            'errors': []
        }
        
        # Group fixes by file path
        files_to_restore = {}
        for fix_result in fix_results:
            if fix_result.success and hasattr(fix_result, 'backup_path') and fix_result.backup_path:
                files_to_restore[fix_result.file_path] = fix_result.backup_path
        
        # Restore each file
        for file_path, backup_path in files_to_restore.items():
            try:
                if self.rollback_fixes(backup_path, file_path):
                    rollback_result['restored_files'].append(file_path)
                else:
                    rollback_result['failed_files'].append(file_path)
                    rollback_result['errors'].append(f"Failed to restore {file_path}")
            except Exception as e:
                rollback_result['failed_files'].append(file_path)
                rollback_result['errors'].append(f"Error restoring {file_path}: {str(e)}")
        
        rollback_result['success'] = len(rollback_result['failed_files']) == 0
        return rollback_result
    
    def create_fix_checkpoint(self, file_paths: List[str]) -> str:
        """Create a checkpoint of multiple files before applying fixes."""
        checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        checkpoint_dir = self.backup_directory / f"checkpoint_{checkpoint_id}"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_manifest = {
            'checkpoint_id': checkpoint_id,
            'created_at': datetime.now().isoformat(),
            'files': {}
        }
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    # Create backup of the file
                    file_name = Path(file_path).name
                    backup_path = checkpoint_dir / file_name
                    shutil.copy2(file_path, backup_path)
                    
                    checkpoint_manifest['files'][file_path] = {
                        'backup_path': str(backup_path),
                        'original_size': os.path.getsize(file_path),
                        'original_mtime': os.path.getmtime(file_path)
                    }
            except Exception as e:
                print(f"Warning: Could not backup {file_path}: {e}")
        
        # Save manifest
        manifest_path = checkpoint_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            import json
            json.dump(checkpoint_manifest, f, indent=2)
        
        return checkpoint_id
    
    def restore_from_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restore files from a checkpoint."""
        checkpoint_dir = self.backup_directory / f"checkpoint_{checkpoint_id}"
        manifest_path = checkpoint_dir / "manifest.json"
        
        restore_result = {
            'success': True,
            'restored_files': [],
            'failed_files': [],
            'errors': []
        }
        
        try:
            if not manifest_path.exists():
                restore_result['success'] = False
                restore_result['errors'].append(f"Checkpoint {checkpoint_id} not found")
                return restore_result
            
            # Load manifest
            with open(manifest_path, 'r') as f:
                import json
                manifest = json.load(f)
            
            # Restore each file
            for original_path, file_info in manifest['files'].items():
                try:
                    backup_path = file_info['backup_path']
                    if os.path.exists(backup_path):
                        shutil.copy2(backup_path, original_path)
                        restore_result['restored_files'].append(original_path)
                    else:
                        restore_result['failed_files'].append(original_path)
                        restore_result['errors'].append(f"Backup not found: {backup_path}")
                except Exception as e:
                    restore_result['failed_files'].append(original_path)
                    restore_result['errors'].append(f"Error restoring {original_path}: {str(e)}")
            
            restore_result['success'] = len(restore_result['failed_files']) == 0
            
        except Exception as e:
            restore_result['success'] = False
            restore_result['errors'].append(f"Error reading checkpoint: {str(e)}")
        
        return restore_result
    
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
    
    def validate_fix_safety(self, fixable_issue: FixableIssue, 
                           context: AnalysisContext) -> Dict[str, Any]:
        """Perform comprehensive safety validation of a fix."""
        validation_result = {
            'is_safe': True,
            'confidence': fixable_issue.confidence,
            'warnings': [],
            'errors': [],
            'checks_performed': []
        }
        
        # Check 1: Syntax validation
        if context.language == "python":
            try:
                ast.parse(fixable_issue.fixed_content)
                validation_result['checks_performed'].append('syntax_check_passed')
            except SyntaxError as e:
                validation_result['is_safe'] = False
                validation_result['errors'].append(f"Syntax error after fix: {str(e)}")
                validation_result['checks_performed'].append('syntax_check_failed')
        
        # Check 2: Content length validation
        original_lines = len(fixable_issue.original_content.split('\n'))
        fixed_lines = len(fixable_issue.fixed_content.split('\n'))
        line_change_ratio = abs(fixed_lines - original_lines) / max(original_lines, 1)
        
        if line_change_ratio > 0.5:  # More than 50% line change
            validation_result['warnings'].append(
                f"Significant line count change: {original_lines} -> {fixed_lines}"
            )
        
        validation_result['checks_performed'].append('line_count_check')
        
        # Check 3: Import preservation (for Python)
        if context.language == "python" and fixable_issue.fix_type != FixType.IMPORTS:
            original_imports = self._extract_imports(fixable_issue.original_content)
            fixed_imports = self._extract_imports(fixable_issue.fixed_content)
            
            if original_imports != fixed_imports:
                validation_result['warnings'].append(
                    "Import statements were modified by non-import fix"
                )
        
        validation_result['checks_performed'].append('import_preservation_check')
        
        # Check 4: Function/class signature preservation
        if context.language == "python":
            original_signatures = self._extract_signatures(fixable_issue.original_content)
            fixed_signatures = self._extract_signatures(fixable_issue.fixed_content)
            
            if original_signatures != fixed_signatures:
                validation_result['warnings'].append(
                    "Function or class signatures may have been modified"
                )
        
        validation_result['checks_performed'].append('signature_preservation_check')
        
        # Adjust confidence based on warnings and errors
        if validation_result['errors']:
            validation_result['confidence'] = 0.0
        elif validation_result['warnings']:
            validation_result['confidence'] *= 0.8
        
        return validation_result
    
    def _extract_imports(self, content: str) -> Set[str]:
        """Extract import statements from Python code."""
        imports = set()
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.add(f"from {module} import {alias.name}")
        except SyntaxError:
            pass
        return imports
    
    def _extract_signatures(self, content: str) -> Set[str]:
        """Extract function and class signatures from Python code."""
        signatures = set()
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    signatures.add(f"def {node.name}({', '.join(args)})")
                elif isinstance(node, ast.ClassDef):
                    signatures.add(f"class {node.name}")
        except SyntaxError:
            pass
        return signatures
    
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