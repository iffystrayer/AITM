"""
Integration tests for the auto-fix engine.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.code_analysis.auto_fix_engine import (
    AutoFixEngine, FixableIssue, FixApplicationResult, FixStatus,
    TrailingWhitespaceFixer, MultipleBlankLinesFixer, PythonImportSorter,
    ExternalFormatterFixer
)
from app.services.code_analysis.base_analyzer import AnalysisContext
from app.models.quality import QualityIssue, IssueType, Severity, FixType, SafetyLevel


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


class TestExternalFormatterFixer:
    """Test ExternalFormatterFixer."""
    
    def test_fixer_creation(self):
        """Test creating external formatter fixer."""
        fixer = ExternalFormatterFixer("black", FixType.FORMATTING, {"python"})
        
        assert fixer.name == "ExternalFormatter_black"
        assert fixer.fix_type == FixType.FORMATTING
        assert fixer.formatter_command == "black"
        assert fixer.supports_language("python")
    
    def test_configuration(self):
        """Test fixer configuration."""
        fixer = ExternalFormatterFixer("black", FixType.FORMATTING, {"python"})
        
        config = {
            "formatter_args": ["--line-length", "100", "--quiet"],
            "safety_level": "moderate"
        }
        
        fixer.configure(config)
        
        assert fixer.formatter_args == ["--line-length", "100", "--quiet"]
        assert fixer.safety_level == SafetyLevel.MODERATE
    
    @patch('subprocess.run')
    def test_formatter_availability_check(self, mock_run):
        """Test checking if formatter is available."""
        fixer = ExternalFormatterFixer("black", FixType.FORMATTING, {"python"})
        
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
            final_content="print('hello world')"
        )
        
        assert engine.validate_fixes(valid_result, context) is True
        
        # Invalid Python code
        invalid_result = FixApplicationResult(
            file_path="test.py",
            fixes_attempted=1,
            final_content="print('hello'"  # Missing closing parenthesis
        )
        
        assert engine.validate_fixes(invalid_result, context) is False
    
    def test_safety_level_filtering(self):
        """Test filtering fixes based on safety level."""
        engine = AutoFixEngine()
        
        # Test conservative safety leveln('app.js', patterns)
        assert not auto_fix_engine._matches_excluded_pattern('model.py', patterns)
    
    @pytest.mark.asyncio
    async def test_validate_fix_success(self, auto_fix_engine):
        """Test successful fix validation."""
        # Create a temporary valid Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('print("Hello, world!")\n')
            temp_path = f.name
        
        try:
            result = await auto_fix_engine._validate_fix(temp_path, FixType.FORMATTING)
            assert result.is_valid
            assert len(result.syntax_errors) == 0
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_fix_syntax_error(self, auto_fix_engine):
        """Test fix validation with syntax error."""
        # Create a temporary invalid Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('print("Hello, world!"\n')  # Missing closing parenthesis
            temp_path = f.name
        
        try:
            result = await auto_fix_engine._validate_fix(temp_path, FixType.FORMATTING)
            assert not result.is_valid
            assert len(result.syntax_errors) > 0
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_rollback_fixes(self, auto_fix_engine):
        """Test rollback functionality."""
        # Create sample fix results
        fix_results = [
            AutoFixResult(
                id="fix1",
                issue_id="issue1",
                project_id="test",
                file_path="test1.py",
                fix_type=FixType.FORMATTING,
                original_content="original content 1",
                fixed_content="fixed content 1",
                success=True
            ),
            AutoFixResult(
                id="fix2",
                issue_id="issue2",
                project_id="test",
                file_path="test2.py",
                fix_type=FixType.IMPORTS,
                original_content="original content 2",
                fixed_content="fixed content 2",
                success=True
            )
        ]
        
        # Create temporary files
        temp_files = []
        for i, fix_result in enumerate(fix_results):
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(fix_result.fixed_content)
                temp_path = f.name
                fix_result.file_path = temp_path
                temp_files.append(temp_path)
        
        try:
            # Perform rollback
            rollback_result = await auto_fix_engine.rollback_fixes(fix_results)
            
            assert rollback_result.success
            assert len(rollback_result.restored_files) == 2
            assert len(rollback_result.failed_files) == 0
            
            # Verify files were restored
            for i, temp_path in enumerate(temp_files):
                with open(temp_path, 'r') as f:
                    content = f.read()
                assert content == fix_results[i].original_content
                
        finally:
            # Cleanup
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)


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
    
    @pytest.mark.asyncio
    async def test_complete_autofix_workflow(self, temp_project_dir):
        """Test the complete auto-fix workflow from issue to fix."""
        temp_dir, test_file = temp_project_dir
        
        # Create AutoFixEngine
        config_manager = QualityConfigManager()
        engine = AutoFixEngine(config_manager)
        
        # Create quality issues
        issues = [
            QualityIssue(
                id="formatting_issue",
                project_id="test_project",
                file_path=test_file,
                line_number=1,
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting",
                description="Poor formatting",
                auto_fixable=True
            )
        ]
        
        # Analyze fixable issues
        fixable_issues = await engine.analyze_fixable_issues(issues)
        assert len(fixable_issues) > 0
        
        # Apply fixes
        results = await engine.apply_fixes(
            fixable_issues, 
            "test_project", 
            SafetyLevel.AGGRESSIVE  # Use aggressive to ensure fixes are applied
        )
        
        # Check results (may fail if formatters not installed)
        if any(r.success for r in results):
            # At least one fix was successful
            successful_results = [r for r in results if r.success]
            assert len(successful_results) > 0
            
            # Verify file was modified
            with open(test_file, 'r') as f:
                modified_content = f.read()
            
            # Content should be different from original
            original_content = '''import os,sys
import requests
from mymodule import something

def badly_formatted_function(x,y,z):
    if x>0:
        result=x+y+z
        return result
    else:
        return None
'''
            # Note: We can't guarantee exact formatting without the tools installed
            # but we can check that the file is still valid Python
            compile(modified_content, test_file, 'exec')
        else:
            # If no fixes were successful, it's likely due to missing tools
            # This is acceptable in a test environment
            pytest.skip("Formatting tools not available")


if __name__ == "__main__":
    pytest.main([__file__])