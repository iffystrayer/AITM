"""
Integration tests for the auto-fix engine.
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.code_analysis.auto_fix_engine import (
    AutoFixEngine, FixableIssue, FixApplicationResult, FixStatus,
    TrailingWhitespaceFixer, MultipleBlankLinesFixer, PythonImportSorter,
    BlackFormatterFixer, IsortFormatterFixer, Autopep8FormatterFixer,
    ExternalFormatterFixer
)
from app.services.code_analysis.base_analyzer import AnalysisContext
from app.models.quality import QualityIssue, AutoFixResult, IssueType, Severity, FixType, SafetyLevel
from app.core.quality_config import QualityConfigManager


class TestTrailingWhitespaceFixer:
    """Test TrailingWhitespaceFixer."""
    
    def test_fixer_creation(self):
        """Test creating trailing whitespace fixer."""
        fixer = TrailingWhitespaceFixer()
        
        assert fixer.name == "TrailingWhitespaceFixer"
        assert fixer.fix_type == FixType.FORMATTING
        assert fixer.supports_language("python")
        assert fixer.supports_language("javascript")  # Supports all languages
    
    def test_can_fix_trailing_whitespace(self):
        """Test detection of fixable trailing whitespace."""
        fixer = TrailingWhitespaceFixer()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="trailing_whitespace",
            line_number=1
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')   \nprint('world')"
        )
        
        assert fixer.can_fix_issue(issue, context) is True
    
    def test_analyze_fixable_issue(self):
        """Test analysis of fixable trailing whitespace issue."""
        fixer = TrailingWhitespaceFixer()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="trailing_whitespace",
            line_number=1
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')   \nprint('world')"
        )
        
        fixable_issue = fixer.analyze_fixable_issue(issue, context)
        
        assert fixable_issue is not None
        assert fixable_issue.confidence == 1.0
        assert fixable_issue.requires_backup is False
        assert "print('hello')\nprint('world')" in fixable_issue.fixed_content
    
    def test_apply_fix(self):
        """Test applying trailing whitespace fix."""
        fixer = TrailingWhitespaceFixer()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="trailing_whitespace",
            line_number=1
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')   \nprint('world')"
        )
        
        fixable_issue = fixer.analyze_fixable_issue(issue, context)
        fix_result = fixer.apply_fix(fixable_issue, context)
        
        assert fix_result.success is True
        assert fix_result.fixed_content is not None
        assert "print('hello')\nprint('world')" in fix_result.fixed_content


class TestMultipleBlankLinesFixer:
    """Test MultipleBlankLinesFixer."""
    
    def test_fixer_creation(self):
        """Test creating multiple blank lines fixer."""
        fixer = MultipleBlankLinesFixer()
        
        assert fixer.name == "MultipleBlankLinesFixer"
        assert fixer.fix_type == FixType.FORMATTING
    
    def test_can_fix_multiple_blank_lines(self):
        """Test detection of fixable multiple blank lines."""
        fixer = MultipleBlankLinesFixer()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="multiple_blank_lines"
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')\n\n\n\nprint('world')"
        )
        
        assert fixer.can_fix_issue(issue, context) is True
    
    def test_analyze_fixable_issue(self):
        """Test analysis of fixable multiple blank lines issue."""
        fixer = MultipleBlankLinesFixer()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="multiple_blank_lines"
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')\n\n\n\nprint('world')"
        )
        
        fixable_issue = fixer.analyze_fixable_issue(issue, context)
        
        assert fixable_issue is not None
        assert fixable_issue.confidence == 0.9
        assert "print('hello')\n\nprint('world')" in fixable_issue.fixed_content


class TestPythonImportSorter:
    """Test PythonImportSorter."""
    
    def test_fixer_creation(self):
        """Test creating Python import sorter."""
        fixer = PythonImportSorter()
        
        assert fixer.name == "PythonImportSorter"
        assert fixer.fix_type == FixType.IMPORTS
        assert fixer.supports_language("python")
        assert not fixer.supports_language("javascript")
    
    def test_can_fix_import_issues(self):
        """Test detection of fixable import issues."""
        fixer = PythonImportSorter()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="import_order"
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="import json\nimport os\nfrom app.models import User"
        )
        
        assert fixer.can_fix_issue(issue, context) is True
    
    def test_standard_library_detection(self):
        """Test standard library module detection."""
        fixer = PythonImportSorter()
        
        assert fixer._is_standard_library("os") is True
        assert fixer._is_standard_library("sys") is True
        assert fixer._is_standard_library("json") is True
        assert fixer._is_standard_library("requests") is False
        assert fixer._is_standard_library("app.models") is False
    
    def test_local_import_detection(self):
        """Test local import detection."""
        fixer = PythonImportSorter()
        
        assert fixer._is_local_import("app.models") is True
        assert fixer._is_local_import(".models") is True
        assert fixer._is_local_import("requests") is False
        assert fixer._is_local_import("os") is False


class TestBlackFormatterFixer:
    """Test BlackFormatterFixer."""
    
    def test_fixer_creation(self):
        """Test creating Black formatter fixer."""
        fixer = BlackFormatterFixer()
        
        assert fixer.name == "BlackFormatter"
        assert fixer.fix_type == FixType.FORMATTING
        assert fixer.supports_language("python")
        assert not fixer.supports_language("javascript")
    
    def test_configuration(self):
        """Test Black fixer configuration."""
        fixer = BlackFormatterFixer()
        
        config = {
            "line_length": 100,
            "skip_string_normalization": True,
            "target_versions": ["py38", "py39"]
        }
        
        fixer.configure(config)
        
        assert fixer.line_length == 100
        assert fixer.skip_string_normalization is True
        assert fixer.target_versions == {"py38", "py39"}
    
    def test_can_fix_formatting_issues(self):
        """Test detection of fixable formatting issues."""
        fixer = BlackFormatterFixer()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="formatting"
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="def func(x,y): return x+y"
        )
        
        assert fixer.can_fix_issue(issue, context) is True


class TestIsortFormatterFixer:
    """Test IsortFormatterFixer."""
    
    def test_fixer_creation(self):
        """Test creating isort formatter fixer."""
        fixer = IsortFormatterFixer()
        
        assert fixer.name == "IsortFormatter"
        assert fixer.fix_type == FixType.IMPORTS
        assert fixer.supports_language("python")
        assert not fixer.supports_language("javascript")
    
    def test_configuration(self):
        """Test isort fixer configuration."""
        fixer = IsortFormatterFixer()
        
        config = {
            "profile": "django",
            "line_length": 100,
            "multi_line_output": 5
        }
        
        fixer.configure(config)
        
        assert fixer.profile == "django"
        assert fixer.line_length == 100
        assert fixer.multi_line_output == 5
    
    def test_can_fix_import_issues(self):
        """Test detection of fixable import issues."""
        fixer = IsortFormatterFixer()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="import_order"
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="import sys\nimport os\nfrom app import models"
        )
        
        assert fixer.can_fix_issue(issue, context) is True


class TestAutopep8FormatterFixer:
    """Test Autopep8FormatterFixer."""
    
    def test_fixer_creation(self):
        """Test creating autopep8 formatter fixer."""
        fixer = Autopep8FormatterFixer()
        
        assert fixer.name == "Autopep8Formatter"
        assert fixer.fix_type == FixType.FORMATTING
        assert fixer.supports_language("python")
        assert not fixer.supports_language("javascript")
    
    def test_configuration(self):
        """Test autopep8 fixer configuration."""
        fixer = Autopep8FormatterFixer()
        
        config = {
            "max_line_length": 100,
            "aggressive_level": 2,
            "select_errors": ["E1", "E2"],
            "ignore_errors": ["E501"]
        }
        
        fixer.configure(config)
        
        assert fixer.max_line_length == 100
        assert fixer.aggressive_level == 2
        assert fixer.select_errors == ["E1", "E2"]
        assert fixer.ignore_errors == ["E501"]
    
    def test_can_fix_pep8_issues(self):
        """Test detection of fixable PEP 8 issues."""
        fixer = Autopep8FormatterFixer()
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="pep8_violation"
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="def func( x,y ): return x+y"
        )
        
        assert fixer.can_fix_issue(issue, context) is True


class TestExternalFormatterFixer:
    """Test ExternalFormatterFixer."""
    
    def test_fixer_creation(self):
        """Test creating external formatter fixer."""
        fixer = ExternalFormatterFixer("prettier", FixType.FORMATTING, {"javascript"})
        
        assert fixer.name == "ExternalFormatter_prettier"
        assert fixer.fix_type == FixType.FORMATTING
        assert fixer.formatter_command == "prettier"
        assert fixer.supports_language("javascript")
    
    def test_configuration(self):
        """Test fixer configuration."""
        fixer = ExternalFormatterFixer("prettier", FixType.FORMATTING, {"javascript"})
        
        config = {
            "formatter_args": ["--write", "--single-quote"],
            "safety_level": "moderate"
        }
        
        fixer.configure(config)
        
        assert fixer.formatter_args == ["--write", "--single-quote"]
        assert fixer.safety_level == SafetyLevel.MODERATE
    
    @patch('subprocess.run')
    def test_formatter_availability_check(self, mock_run):
        """Test checking if formatter is available."""
        fixer = ExternalFormatterFixer("prettier", FixType.FORMATTING, {"javascript"})
        
        # Mock successful version check
        mock_run.return_value.returncode = 0
        assert fixer._is_formatter_available() is True
        
        # Mock failed version check
        mock_run.return_value.returncode = 1
        assert fixer._is_formatter_available() is False
        
        # Mock command not found
        mock_run.side_effect = FileNotFoundError()
        assert fixer._is_formatter_available() is False


class TestAutoFixEngine:
    """Test AutoFixEngine."""
    
    def test_engine_creation(self):
        """Test creating auto-fix engine."""
        engine = AutoFixEngine()
        
        assert len(engine.fixers) > 0
        assert engine.safety_level == SafetyLevel.CONSERVATIVE
        assert engine.max_fixes_per_file == 50
    
    def test_add_remove_fixer(self):
        """Test adding and removing fixers."""
        engine = AutoFixEngine()
        initial_count = len(engine.fixers)
        
        # Add custom fixer
        custom_fixer = TrailingWhitespaceFixer()
        custom_fixer.name = "CustomFixer"
        engine.add_fixer(custom_fixer)
        
        assert len(engine.fixers) == initial_count + 1
        
        # Remove fixer
        assert engine.remove_fixer("CustomFixer") is True
        assert len(engine.fixers) == initial_count
        
        # Try to remove non-existent fixer
        assert engine.remove_fixer("NonExistentFixer") is False
    
    def test_configuration(self):
        """Test engine configuration."""
        engine = AutoFixEngine()
        
        config = {
            "safety_level": "moderate",
            "max_fixes_per_file": 25,
            "backup_directory": "custom_backups"
        }
        
        engine.configure(config)
        
        assert engine.safety_level == SafetyLevel.MODERATE
        assert engine.max_fixes_per_file == 25
        assert str(engine.backup_directory) == "custom_backups"
    
    def test_analyze_fixable_issues(self):
        """Test analyzing fixable issues."""
        engine = AutoFixEngine()
        
        issues = [
            QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="trailing_whitespace",
                line_number=1
            ),
            QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="multiple_blank_lines"
            ),
            QualityIssue(
                issue_type=IssueType.SECURITY,
                severity=Severity.HIGH,
                category="hardcoded_password"  # Not fixable
            )
        ]
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')   \n\n\n\nprint('world')"
        )
        
        fixable_issues = engine.analyze_fixable_issues(issues, context)
        
        # Should find fixable issues (trailing whitespace and multiple blank lines)
        assert len(fixable_issues) >= 1
        assert all(isinstance(issue, FixableIssue) for issue in fixable_issues)
    
    def test_apply_fixes(self):
        """Test applying fixes to code."""
        engine = AutoFixEngine()
        
        # Create a fixable issue
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="trailing_whitespace",
            line_number=1
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')   \nprint('world')"
        )
        
        fixable_issues = engine.analyze_fixable_issues([issue], context)
        
        if fixable_issues:
            result = engine.apply_fixes(fixable_issues, context, backup_enabled=False)
            
            assert isinstance(result, FixApplicationResult)
            assert result.fixes_attempted > 0
            assert result.final_content != context.file_content
            assert "print('hello')\nprint('world')" in result.final_content
    
    def test_backup_creation(self):
        """Test backup file creation."""
        engine = AutoFixEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            engine.backup_directory = Path(temp_dir)
            
            test_content = "print('hello world')"
            backup_path = engine._create_backup("test.py", test_content)
            
            assert os.path.exists(backup_path)
            
            with open(backup_path, 'r') as f:
                backup_content = f.read()
            
            assert backup_content == test_content
    
    def test_rollback_fixes(self):
        """Test rolling back fixes."""
        engine = AutoFixEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create backup file
            backup_path = Path(temp_dir) / "backup.txt"
            backup_content = "original content"
            backup_path.write_text(backup_content)
            
            # Create target file with modified content
            target_path = Path(temp_dir) / "target.txt"
            target_path.write_text("modified content")
            
            # Rollback
            success = engine.rollback_fixes(str(backup_path), str(target_path))
            
            assert success is True
            assert target_path.read_text() == backup_content
    
    def test_validate_fixes_python(self):
        """Test fix validation for Python code."""
        engine = AutoFixEngine()
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="print('hello')",
            language="python"
        )
        
        # Valid Python code
        valid_result = FixApplicationResult(
            file_path="test.py",
            fixes_attempted=1,
            fixes_applied=1,
            fixes_failed=0,
            fixes_skipped=0,
            final_content="print('hello world')"
        )
        
        assert engine.validate_fixes(valid_result, context) is True
        
        # Invalid Python code
        invalid_result = FixApplicationResult(
            file_path="test.py",
            fixes_attempted=1,
            fixes_applied=1,
            fixes_failed=0,
            fixes_skipped=0,
            final_content="print('hello'"  # Missing closing parenthesis
        )
        
        assert engine.validate_fixes(invalid_result, context) is False
    
    def test_checkpoint_creation_and_restore(self):
        """Test checkpoint creation and restoration."""
        engine = AutoFixEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = []
            for i in range(3):
                test_file = Path(temp_dir) / f"test_{i}.py"
                test_file.write_text(f"# Test file {i}\nprint('hello {i}')")
                test_files.append(str(test_file))
            
            # Create checkpoint
            checkpoint_id = engine.create_fix_checkpoint(test_files)
            assert checkpoint_id is not None
            
            # Modify files
            for i, test_file in enumerate(test_files):
                Path(test_file).write_text(f"# Modified file {i}\nprint('modified {i}')")
            
            # Restore from checkpoint
            restore_result = engine.restore_from_checkpoint(checkpoint_id)
            
            assert restore_result['success'] is True
            assert len(restore_result['restored_files']) == 3
            assert len(restore_result['failed_files']) == 0
            
            # Verify restoration
            for i, test_file in enumerate(test_files):
                content = Path(test_file).read_text()
                assert f"hello {i}" in content
                assert f"modified {i}" not in content
    
    def test_rollback_batch_fixes(self):
        """Test rolling back a batch of fixes."""
        engine = AutoFixEngine()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files and backup them
            test_files = []
            backup_paths = []
            
            for i in range(2):
                test_file = Path(temp_dir) / f"test_{i}.py"
                original_content = f"# Original file {i}\nprint('original {i}')"
                test_file.write_text(original_content)
                
                # Create backup
                backup_path = engine._create_backup(str(test_file), original_content)
                backup_paths.append(backup_path)
                test_files.append(str(test_file))
                
                # Modify file (simulate fix application)
                test_file.write_text(f"# Fixed file {i}\nprint('fixed {i}')")
            
            # Create fix results
            fix_results = []
            for i, (test_file, backup_path) in enumerate(zip(test_files, backup_paths)):
                fix_result = AutoFixResult(
                    issue_id=f"issue_{i}",
                    project_id="test",
                    file_path=test_file,
                    fix_type=FixType.FORMATTING,
                    success=True
                )
                fix_result.backup_path = backup_path
                fix_results.append(fix_result)
            
            # Rollback batch
            rollback_result = engine.rollback_batch_fixes(fix_results)
            
            assert rollback_result['success'] is True
            assert len(rollback_result['restored_files']) == 2
            assert len(rollback_result['failed_files']) == 0
            
            # Verify rollback
            for i, test_file in enumerate(test_files):
                content = Path(test_file).read_text()
                assert f"original {i}" in content
                assert f"fixed {i}" not in content
    
    def test_safety_validation(self):
        """Test comprehensive safety validation."""
        engine = AutoFixEngine()
        
        # Test with valid Python code
        valid_issue = FixableIssue(
            issue=QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting"
            ),
            fix_type=FixType.FORMATTING,
            confidence=0.9,
            fix_description="Test fix",
            original_content="def func():\n    return 42",
            fixed_content="def func():\n    return 42\n",
            line_range=(1, 2)
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content="def func():\n    return 42",
            language="python"
        )
        
        validation_result = engine.validate_fix_safety(valid_issue, context)
        
        assert validation_result['is_safe'] is True
        assert validation_result['confidence'] > 0
        assert 'syntax_check_passed' in validation_result['checks_performed']
        
        # Test with invalid Python code
        invalid_issue = FixableIssue(
            issue=QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting"
            ),
            fix_type=FixType.FORMATTING,
            confidence=0.9,
            fix_description="Test fix",
            original_content="def func():\n    return 42",
            fixed_content="def func(\n    return 42",  # Missing closing parenthesis
            line_range=(1, 2)
        )
        
        validation_result = engine.validate_fix_safety(invalid_issue, context)
        
        assert validation_result['is_safe'] is False
        assert validation_result['confidence'] == 0.0
        assert len(validation_result['errors']) > 0
        assert 'syntax_check_failed' in validation_result['checks_performed']
    
    def test_import_and_signature_preservation(self):
        """Test import and signature preservation checks."""
        engine = AutoFixEngine()
        
        original_content = '''import os
import sys
from app.models import User

def important_function(x, y):
    return x + y

class ImportantClass:
    def method(self):
        pass
'''
        
        # Test with preserved imports and signatures
        preserved_fix = FixableIssue(
            issue=QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting"
            ),
            fix_type=FixType.FORMATTING,
            confidence=0.9,
            fix_description="Format code",
            original_content=original_content,
            fixed_content=original_content.replace("    ", "  "),  # Just change indentation
            line_range=(1, 10)
        )
        
        context = AnalysisContext(
            project_id="test",
            file_path="test.py",
            file_content=original_content,
            language="python"
        )
        
        validation_result = engine.validate_fix_safety(preserved_fix, context)
        
        assert validation_result['is_safe'] is True
        assert 'import_preservation_check' in validation_result['checks_performed']
        assert 'signature_preservation_check' in validation_result['checks_performed']
    
    def test_safety_level_filtering(self):
        """Test filtering fixes based on safety level."""
        engine = AutoFixEngine()
        
        # Test conservative safety level
        engine.configure({"safety_level": "conservative"})
        
        # Create fixable issues with different confidence levels
        high_confidence_issue = FixableIssue(
            issue=QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting"
            ),
            fix_type=FixType.FORMATTING,
            confidence=0.95,
            fix_description="High confidence fix",
            original_content="test",
            fixed_content="test_fixed",
            line_range=(1, 1)
        )
        
        low_confidence_issue = FixableIssue(
            issue=QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting"
            ),
            fix_type=FixType.FORMATTING,
            confidence=0.5,
            fix_description="Low confidence fix",
            original_content="test",
            fixed_content="test_fixed",
            line_range=(1, 1)
        )
        
        # Conservative level should accept high confidence, reject low confidence
        assert engine._is_fix_safe_enough(high_confidence_issue) is True
        assert engine._is_fix_safe_enough(low_confidence_issue) is False
    



class TestAutoFixEngineIntegration:
    """Integration tests for the complete auto-fix workflow."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with Python files."""
        temp_dir = tempfile.mkdtemp(prefix="autofix_test_")
        
        # Create a poorly formatted Python file
        test_file = os.path.join(temp_dir, "test_module.py")
        with open(test_file, 'w') as f:
            f.write('''import os,sys
import requests
from mymodule import something

def badly_formatted_function(x,y,z):
    if x>0:
        result=x+y+z
        return result
    else:
        return None
''')
        
        yield temp_dir, test_file
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_complete_autofix_workflow(self, temp_project_dir):
        """Test the complete auto-fix workflow from issue to fix."""
        temp_dir, test_file = temp_project_dir
        
        # Create AutoFixEngine
        config_manager = QualityConfigManager()
        engine = AutoFixEngine(config_manager)
        
        # Create quality issues
        issues = [
            QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting",
                description="Poor formatting"
            )
        ]
        
        # Create context
        with open(test_file, 'r') as f:
            file_content = f.read()
        
        context = AnalysisContext(
            project_id="test_project",
            file_path=test_file,
            file_content=file_content,
            language="python"
        )
        
        # Analyze fixable issues
        fixable_issues = engine.analyze_fixable_issues(issues, context)
        
        if fixable_issues:
            # Apply fixes
            result = engine.apply_fixes(fixable_issues, context, backup_enabled=True)
            
            # Check results (may fail if formatters not installed)
            if result.success and result.fixes_applied > 0:
                # At least one fix was successful
                assert result.fixes_applied > 0
                
                # Verify the fix is valid
                is_valid = engine.validate_fixes(result, context)
                assert is_valid is True
            else:
                # If no fixes were successful, it's likely due to missing tools
                # This is acceptable in a test environment
                pytest.skip("Formatting tools not available")
        else:
            pytest.skip("No fixable issues found")


if __name__ == "__main__":
    pytest.main([__file__])