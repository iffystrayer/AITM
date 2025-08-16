#!/usr/bin/env python3
"""
Comprehensive demo of the AutoFixEngine with Python formatters.
This script demonstrates the complete auto-fix workflow including:
- Black formatting
- isort import organization  
- autopep8 PEP 8 fixes
- Safety validation
- Rollback functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.code_analysis.auto_fix_engine import AutoFixEngine
from app.services.code_analysis.base_analyzer import AnalysisContext
from app.models.quality import QualityIssue, IssueType, Severity, FixType, SafetyLevel
from app.core.quality_config import QualityConfigManager


def create_sample_problematic_code():
    """Create sample Python code with various quality issues."""
    return '''import sys,os
import requests
from myapp.models import User
import json
from django.db import models
import asyncio

def badly_formatted_function(x,y,z):
    if x>0:
        result=x+y+z
        return result
    else:
        return None

class PoorlyFormattedClass:
    def __init__(self,name,age):
        self.name=name
        self.age=age
    
    def get_info(self):
        return f"{self.name} is {self.age} years old"
    
    def process_data(self,data):
        if data:
            processed=[]
            for item in data:
                if item['status']=='active':
                    processed.append(item)
            return processed
        return []

async def async_function(param1,param2):
    result=await some_async_operation(param1,param2)
    return result

# Some trailing whitespace issues   
def function_with_whitespace():   
    x = 1    
    y = 2   
    return x + y    
'''


def create_quality_issues():
    """Create a list of quality issues that can be fixed."""
    return [
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
        ),
        QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="trailing_whitespace",
            description="Trailing whitespace"
        ),
        QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="spacing",
            description="Spacing issues"
        )
    ]


def demonstrate_individual_fixers():
    """Demonstrate each fixer individually."""
    print("🔧 Individual Fixer Demonstrations")
    print("=" * 50)
    
    engine = AutoFixEngine()
    problematic_code = create_sample_problematic_code()
    
    context = AnalysisContext(
        project_id="demo",
        file_path="demo.py",
        file_content=problematic_code,
        language="python"
    )
    
    # Test each fixer type
    fixer_types = [
        ("Black Formatter", "formatting"),
        ("isort Formatter", "import_order"),
        ("Trailing Whitespace", "trailing_whitespace"),
        ("Multiple Blank Lines", "multiple_blank_lines")
    ]
    
    for fixer_name, category in fixer_types:
        print(f"\n🔨 Testing {fixer_name}")
        
        issue = QualityIssue(
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category=category,
            description=f"{fixer_name} issue"
        )
        
        fixable_issues = engine.analyze_fixable_issues([issue], context)
        
        if fixable_issues:
            print(f"  ✅ Found {len(fixable_issues)} fixable issues")
            
            for fixable_issue in fixable_issues:
                print(f"    - Confidence: {fixable_issue.confidence}")
                print(f"    - Description: {fixable_issue.fix_description}")
                print(f"    - Requires backup: {fixable_issue.requires_backup}")
        else:
            print(f"  ⚠️  No fixable issues found for {fixer_name}")


def demonstrate_complete_workflow():
    """Demonstrate the complete auto-fix workflow."""
    print("\n\n🚀 Complete Auto-Fix Workflow Demonstration")
    print("=" * 50)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        problematic_code = create_sample_problematic_code()
        temp_file.write(problematic_code)
        temp_path = temp_file.name
    
    try:
        print(f"📁 Created temporary file: {temp_path}")
        
        # Create AutoFixEngine with custom configuration
        config_manager = QualityConfigManager()
        engine = AutoFixEngine(config_manager)
        
        # Configure for aggressive fixing
        engine.configure({
            "safety_level": "moderate",
            "max_fixes_per_file": 20,
            "fixer_configs": {
                "BlackFormatter": {
                    "line_length": 88,
                    "skip_string_normalization": False
                },
                "IsortFormatter": {
                    "profile": "black",
                    "line_length": 88
                }
            }
        })
        
        print("⚙️  Engine configured with moderate safety level")
        
        # Create context
        context = AnalysisContext(
            project_id="demo",
            file_path=temp_path,
            file_content=problematic_code,
            language="python"
        )
        
        # Create quality issues
        issues = create_quality_issues()
        print(f"🔍 Created {len(issues)} quality issues to fix")
        
        # Analyze fixable issues
        fixable_issues = engine.analyze_fixable_issues(issues, context)
        print(f"📊 Found {len(fixable_issues)} fixable issues")
        
        if fixable_issues:
            # Show fixable issues details
            print("\n📋 Fixable Issues Details:")
            for i, fixable_issue in enumerate(fixable_issues, 1):
                print(f"  {i}. {fixable_issue.fix_description}")
                print(f"     - Confidence: {fixable_issue.confidence:.2f}")
                print(f"     - Fix Type: {fixable_issue.fix_type.value}")
                print(f"     - Requires Backup: {fixable_issue.requires_backup}")
            
            # Create checkpoint
            checkpoint_id = engine.create_fix_checkpoint([temp_path])
            print(f"\n💾 Created checkpoint: {checkpoint_id}")
            
            # Apply fixes
            print("\n🔧 Applying fixes...")
            fix_result = engine.apply_fixes(fixable_issues, context, backup_enabled=True)
            
            # Show results
            print(f"\n📈 Fix Application Results:")
            print(f"  - Attempted: {fix_result.fixes_attempted}")
            print(f"  - Applied: {fix_result.fixes_applied}")
            print(f"  - Failed: {fix_result.fixes_failed}")
            print(f"  - Skipped: {fix_result.fixes_skipped}")
            print(f"  - Success: {fix_result.success}")
            print(f"  - Execution Time: {fix_result.execution_time:.3f}s")
            
            if fix_result.backup_path:
                print(f"  - Backup Created: {fix_result.backup_path}")
            
            # Validate fixes
            if fix_result.success and fix_result.final_content:
                is_valid = engine.validate_fixes(fix_result, context)
                print(f"  - Validation: {'✅ Passed' if is_valid else '❌ Failed'}")
                
                # Show fixed code preview
                print("\n📝 Fixed Code Preview:")
                lines = fix_result.final_content.split('\n')
                for i, line in enumerate(lines[:20], 1):
                    print(f"  {i:2d}: {line}")
                if len(lines) > 20:
                    print(f"  ... ({len(lines) - 20} more lines)")
                
                # Write fixed content to file
                with open(temp_path, 'w') as f:
                    f.write(fix_result.final_content)
                
                # Demonstrate safety validation
                print("\n🛡️  Safety Validation Demonstration:")
                for fixable_issue in fixable_issues[:3]:  # Test first 3 issues
                    validation_result = engine.validate_fix_safety(fixable_issue, context)
                    print(f"  Fix: {fixable_issue.fix_description}")
                    print(f"    - Safe: {validation_result['is_safe']}")
                    print(f"    - Confidence: {validation_result['confidence']:.2f}")
                    print(f"    - Warnings: {len(validation_result['warnings'])}")
                    print(f"    - Errors: {len(validation_result['errors'])}")
                
                # Demonstrate rollback
                print("\n🔄 Demonstrating Rollback Functionality:")
                restore_result = engine.restore_from_checkpoint(checkpoint_id)
                
                if restore_result['success']:
                    print("  ✅ Rollback successful!")
                    print(f"    - Restored files: {len(restore_result['restored_files'])}")
                    
                    # Verify rollback
                    with open(temp_path, 'r') as f:
                        restored_content = f.read()
                    
                    if restored_content == problematic_code:
                        print("  ✅ File content restored correctly")
                    else:
                        print("  ❌ File content not restored correctly")
                else:
                    print(f"  ❌ Rollback failed: {restore_result['errors']}")
            
            else:
                print("  ⚠️  No fixes were successfully applied")
        
        else:
            print("  ⚠️  No fixable issues found")
        
        # Show engine statistics
        print(f"\n📊 Engine Statistics:")
        stats = engine.get_engine_stats()
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    - {sub_key}: {sub_value}")
            elif isinstance(value, list):
                print(f"  {key}: {len(value)} items")
                for item in value[:5]:  # Show first 5 items
                    print(f"    - {item}")
                if len(value) > 5:
                    print(f"    ... and {len(value) - 5} more")
            else:
                print(f"  {key}: {value}")
    
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        print(f"\n🧹 Cleaned up temporary file: {temp_path}")


def demonstrate_error_handling():
    """Demonstrate error handling and edge cases."""
    print("\n\n⚠️  Error Handling and Edge Cases")
    print("=" * 50)
    
    engine = AutoFixEngine()
    
    # Test with invalid Python code
    invalid_code = '''def broken_function(
    return "missing closing parenthesis"
'''
    
    context = AnalysisContext(
        project_id="demo",
        file_path="broken.py",
        file_content=invalid_code,
        language="python"
    )
    
    issue = QualityIssue(
        issue_type=IssueType.STYLE,
        severity=Severity.LOW,
        category="formatting",
        description="Formatting issue on broken code"
    )
    
    print("🔍 Testing with syntactically invalid Python code...")
    fixable_issues = engine.analyze_fixable_issues([issue], context)
    
    if fixable_issues:
        print(f"  📊 Found {len(fixable_issues)} fixable issues")
        
        # Try to apply fixes
        fix_result = engine.apply_fixes(fixable_issues, context, backup_enabled=False)
        
        print(f"  📈 Results:")
        print(f"    - Success: {fix_result.success}")
        print(f"    - Applied: {fix_result.fixes_applied}")
        print(f"    - Failed: {fix_result.fixes_failed}")
        
        if fix_result.error_message:
            print(f"    - Error: {fix_result.error_message}")
        
        # Test validation
        if fix_result.final_content:
            is_valid = engine.validate_fixes(fix_result, context)
            print(f"    - Validation: {'✅ Passed' if is_valid else '❌ Failed'}")
    else:
        print("  ⚠️  No fixable issues found (expected for broken code)")


def main():
    """Run the complete AutoFixEngine demonstration."""
    print("🎯 AutoFixEngine Comprehensive Demo")
    print("=" * 60)
    print("This demo showcases the complete auto-fix functionality including:")
    print("- Python-specific formatters (Black, isort, autopep8)")
    print("- Safety validation and rollback mechanisms")
    print("- Error handling and edge cases")
    print("- Complete workflow from issue detection to fix application")
    print()
    
    try:
        demonstrate_individual_fixers()
        demonstrate_complete_workflow()
        demonstrate_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ AutoFixEngine demonstration completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  🔧 Multiple Python formatters (Black, isort, autopep8)")
        print("  🛡️  Safety validation with syntax checking")
        print("  💾 Checkpoint and rollback functionality")
        print("  📊 Comprehensive fix analysis and reporting")
        print("  ⚙️  Configurable safety levels and fix limits")
        print("  🔄 Robust error handling")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())