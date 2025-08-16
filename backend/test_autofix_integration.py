#!/usr/bin/env python3
"""
Integration tests for the enhanced AutoFixEngine with Python formatters.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.code_analysis.auto_fix_engine import (
    AutoFixEngine, BlackFormatterFixer, IsortFormatterFixer, 
    Autopep8FormatterFixer, FixableIssue, FixApplicationResult
)
from app.services.code_analysis.base_analyzer import AnalysisContext
from app.models.quality import QualityIssue, IssueType, Severity, FixType, SafetyLevel
from app.core.quality_config import QualityConfigManager


def test_black_formatter_integration():
    """Test Black formatter integration."""
    print("Testing Black formatter integration...")
    
    # Sample poorly formatted Python code
    poorly_formatted_code = '''import os,sys
def badly_formatted_function(x,y,z):
    if x>0:
        result=x+y+z
        return result
    else:
        return None
'''
    
    # Create Black formatter
    black_fixer = BlackFormatterFixer()
    
    # Check if Black is available
    if not black_fixer._is_black_available():
        print("  ⚠️  Black not available, skipping test")
        return
    
    # Create context
    context = AnalysisContext(
        project_id="test",
        file_path="test.py",
        file_content=poorly_formatted_code,
        language="python"
    )
    
    # Create a formatting issue
    issue = QualityIssue(
        issue_type=IssueType.STYLE,
        severity=Severity.LOW,
        category="formatting",
        description="Poor code formatting"
    )
    
    # Test fix analysis
    fixable_issue = black_fixer.analyze_fixable_issue(issue, context)
    
    if fixable_issue:
        print("  ✅ Black formatter can fix the issue")
        print(f"  ✅ Confidence: {fixable_issue.confidence}")
        
        # Apply the fix
        fix_result = black_fixer.apply_fix(fixable_issue, context)
        
        if fix_result.success:
            print("  ✅ Black formatter applied successfully")
            print("  📝 Formatted code preview:")
            print("    " + fix_result.fixed_content.replace('\n', '\n    ')[:200] + "...")
        else:
            print(f"  ❌ Black formatter failed: {fix_result.error_message}")
    else:
        print("  ❌ Black formatter cannot fix the issue")


def test_isort_formatter_integration():
    """Test isort formatter integration."""
    print("\nTesting isort formatter integration...")
    
    # Sample code with poorly organized imports
    poorly_organized_imports = '''import sys
import requests
import os
from myapp.models import User
from django.db import models
import json
from myapp.utils import helper

def some_function():
    pass
'''
    
    # Create isort formatter
    isort_fixer = IsortFormatterFixer()
    
    # Check if isort is available
    if not isort_fixer._is_isort_available():
        print("  ⚠️  isort not available, skipping test")
        return
    
    # Create context
    context = AnalysisContext(
        project_id="test",
        file_path="test.py",
        file_content=poorly_organized_imports,
        language="python"
    )
    
    # Create an import issue
    issue = QualityIssue(
        issue_type=IssueType.STYLE,
        severity=Severity.LOW,
        category="import_order",
        description="Imports are not properly organized"
    )
    
    # Test fix analysis
    fixable_issue = isort_fixer.analyze_fixable_issue(issue, context)
    
    if fixable_issue:
        print("  ✅ isort formatter can fix the issue")
        print(f"  ✅ Confidence: {fixable_issue.confidence}")
        
        # Apply the fix
        fix_result = isort_fixer.apply_fix(fixable_issue, context)
        
        if fix_result.success:
            print("  ✅ isort formatter applied successfully")
            print("  📝 Organized imports preview:")
            print("    " + fix_result.fixed_content.replace('\n', '\n    ')[:300] + "...")
        else:
            print(f"  ❌ isort formatter failed: {fix_result.error_message}")
    else:
        print("  ❌ isort formatter cannot fix the issue")


def test_autopep8_formatter_integration():
    """Test autopep8 formatter integration."""
    print("\nTesting autopep8 formatter integration...")
    
    # Sample code with PEP 8 violations
    pep8_violations = '''def bad_function( x,y ):
    if x==1:
        return y+1
    elif x==2:
        return y+2
    else:
        return y
'''
    
    # Create autopep8 formatter
    autopep8_fixer = Autopep8FormatterFixer()
    
    # Check if autopep8 is available
    if not autopep8_fixer._is_autopep8_available():
        print("  ⚠️  autopep8 not available, skipping test")
        return
    
    # Create context
    context = AnalysisContext(
        project_id="test",
        file_path="test.py",
        file_content=pep8_violations,
        language="python"
    )
    
    # Create a PEP 8 issue
    issue = QualityIssue(
        issue_type=IssueType.STYLE,
        severity=Severity.LOW,
        category="pep8_violation",
        description="PEP 8 style violations"
    )
    
    # Test fix analysis
    fixable_issue = autopep8_fixer.analyze_fixable_issue(issue, context)
    
    if fixable_issue:
        print("  ✅ autopep8 formatter can fix the issue")
        print(f"  ✅ Confidence: {fixable_issue.confidence}")
        
        # Apply the fix
        fix_result = autopep8_fixer.apply_fix(fixable_issue, context)
        
        if fix_result.success:
            print("  ✅ autopep8 formatter applied successfully")
            print("  📝 Fixed code preview:")
            print("    " + fix_result.fixed_content.replace('\n', '\n    ')[:200] + "...")
        else:
            print(f"  ❌ autopep8 formatter failed: {fix_result.error_message}")
    else:
        print("  ❌ autopep8 formatter cannot fix the issue")


def test_complete_autofix_workflow():
    """Test the complete auto-fix workflow with multiple formatters."""
    print("\nTesting complete auto-fix workflow...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test_module.py"
        
        # Create a file with multiple issues
        problematic_code = '''import sys,os
import requests
from myapp import models
import json

def poorly_formatted_function(x,y,z):
    if x>0:
        result=x+y+z
        return result
    else:
        return None

class BadlyFormattedClass:
    def __init__(self,name,age):
        self.name=name
        self.age=age
    
    def get_info(self):
        return f"{self.name} is {self.age} years old"
'''
        
        # Write the problematic code to file
        test_file.write_text(problematic_code)
        
        # Create AutoFixEngine
        config_manager = QualityConfigManager()
        engine = AutoFixEngine(config_manager)
        
        # Create multiple quality issues
        issues = [
            QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="import_order",
                description="Imports are not properly organized"
            ),
            QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting",
                description="Code formatting issues"
            ),
            QualityIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="pep8_violation",
                description="PEP 8 violations"
            )
        ]
        
        # Create context
        context = AnalysisContext(
            project_id="test",
            file_path=str(test_file),
            file_content=problematic_code,
            language="python"
        )
        
        # Analyze fixable issues
        fixable_issues = engine.analyze_fixable_issues(issues, context)
        print(f"  📊 Found {len(fixable_issues)} fixable issues")
        
        if fixable_issues:
            # Create checkpoint before applying fixes
            checkpoint_id = engine.create_fix_checkpoint([str(test_file)])
            print(f"  💾 Created checkpoint: {checkpoint_id}")
            
            # Apply fixes
            fix_result = engine.apply_fixes(fixable_issues, context, backup_enabled=True)
            
            print(f"  📈 Fix Results:")
            print(f"    - Attempted: {fix_result.fixes_attempted}")
            print(f"    - Applied: {fix_result.fixes_applied}")
            print(f"    - Failed: {fix_result.fixes_failed}")
            print(f"    - Skipped: {fix_result.fixes_skipped}")
            print(f"    - Success: {fix_result.success}")
            
            if fix_result.success and fix_result.final_content:
                # Validate the fixes
                is_valid = engine.validate_fixes(fix_result, context)
                print(f"  ✅ Fix validation: {'Passed' if is_valid else 'Failed'}")
                
                # Write the fixed content to file
                test_file.write_text(fix_result.final_content)
                
                print("  📝 Fixed code preview:")
                preview_lines = fix_result.final_content.split('\n')[:15]
                for line in preview_lines:
                    print(f"    {line}")
                if len(fix_result.final_content.split('\n')) > 15:
                    print("    ...")
                
                # Test rollback functionality
                print("\n  🔄 Testing rollback functionality...")
                restore_result = engine.restore_from_checkpoint(checkpoint_id)
                
                if restore_result['success']:
                    print("  ✅ Rollback successful")
                    print(f"    - Restored files: {len(restore_result['restored_files'])}")
                    
                    # Verify rollback
                    restored_content = test_file.read_text()
                    if restored_content == problematic_code:
                        print("  ✅ File content restored correctly")
                    else:
                        print("  ❌ File content not restored correctly")
                else:
                    print(f"  ❌ Rollback failed: {restore_result['errors']}")
            
            else:
                print("  ❌ No fixes were successfully applied")
        else:
            print("  ⚠️  No fixable issues found")


def test_safety_validation():
    """Test the safety validation functionality."""
    print("\nTesting safety validation...")
    
    # Create a potentially unsafe fix
    original_code = '''def important_function(x):
    return x * 2
'''
    
    # Simulate a "fix" that breaks syntax
    broken_fixed_code = '''def important_function(x):
    return x * 2
    # Missing closing quote in next line
    print("broken syntax
'''
    
    # Create context
    context = AnalysisContext(
        project_id="test",
        file_path="test.py",
        file_content=original_code,
        language="python"
    )
    
    # Create a fixable issue with broken fix
    issue = QualityIssue(
        issue_type=IssueType.STYLE,
        severity=Severity.LOW,
        category="formatting",
        description="Test issue"
    )
    
    fixable_issue = FixableIssue(
        issue=issue,
        fix_type=FixType.FORMATTING,
        confidence=0.9,
        fix_description="Test fix",
        original_content=original_code,
        fixed_content=broken_fixed_code,
        line_range=(1, 3)
    )
    
    # Create engine and test safety validation
    engine = AutoFixEngine()
    validation_result = engine.validate_fix_safety(fixable_issue, context)
    
    print(f"  📊 Safety validation results:")
    print(f"    - Is safe: {validation_result['is_safe']}")
    print(f"    - Confidence: {validation_result['confidence']}")
    print(f"    - Warnings: {len(validation_result['warnings'])}")
    print(f"    - Errors: {len(validation_result['errors'])}")
    print(f"    - Checks performed: {validation_result['checks_performed']}")
    
    if validation_result['errors']:
        print("  📝 Errors found:")
        for error in validation_result['errors']:
            print(f"    - {error}")
    
    if not validation_result['is_safe']:
        print("  ✅ Safety validation correctly identified unsafe fix")
    else:
        print("  ❌ Safety validation failed to identify unsafe fix")


def main():
    """Run all integration tests."""
    print("🧪 AutoFixEngine Integration Tests")
    print("=" * 50)
    
    try:
        test_black_formatter_integration()
        test_isort_formatter_integration()
        test_autopep8_formatter_integration()
        test_complete_autofix_workflow()
        test_safety_validation()
        
        print("\n" + "=" * 50)
        print("✅ All integration tests completed!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())