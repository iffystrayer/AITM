#!/usr/bin/env python3
"""
Demo script to showcase the auto-fix engine.
"""

import tempfile
from pathlib import Path

from app.services.code_analysis import (
    AutoFixEngine, QualityIssueDetector, AnalysisContext
)
from app.models.quality import QualityIssue, IssueType, Severity


def demo_auto_fix_engine():
    """Demonstrate the auto-fix engine."""
    print("🔧 Auto-Fix Engine Demo")
    print("=" * 40)
    
    # Create a temporary file with issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        problematic_code = """import os
import sys   
import json


def hello():   
    print('world')   


    
def goodbye():
    print('bye')   
"""
        f.write(problematic_code)
        temp_file = f.name
    
    try:
        print(f"📄 Created test file: {temp_file}")
        print("📝 Original code:")
        print(problematic_code)
        print()
        
        # Create analysis context
        context = AnalysisContext(
            project_id="demo_project",
            file_path=temp_file,
            file_content=problematic_code,
            language="python"
        )
        
        # Detect issues first
        detector = QualityIssueDetector()
        analysis_result = detector.analyze(context)
        
        print(f"🔍 Found {len(analysis_result.issues)} issues:")
        for i, issue in enumerate(analysis_result.issues, 1):
            location = f"Line {issue.line_number}" if issue.line_number else "Unknown"
            print(f"  {i}. {issue.severity.value.upper()}: {issue.description} ({location})")
        print()
        
        # Initialize auto-fix engine
        engine = AutoFixEngine()
        
        print("🔧 Analyzing fixable issues...")
        fixable_issues = engine.analyze_fixable_issues(analysis_result.issues, context)
        
        print(f"✅ Found {len(fixable_issues)} fixable issues:")
        for i, fixable in enumerate(fixable_issues, 1):
            print(f"  {i}. {fixable.fix_description} (confidence: {fixable.confidence:.1f})")
        print()
        
        if fixable_issues:
            print("🚀 Applying fixes...")
            fix_result = engine.apply_fixes(fixable_issues, context, backup_enabled=False)
            
            print(f"📊 Fix Results:")
            print(f"  Attempted: {fix_result.fixes_attempted}")
            print(f"  Applied: {fix_result.fixes_applied}")
            print(f"  Failed: {fix_result.fixes_failed}")
            print(f"  Skipped: {fix_result.fixes_skipped}")
            print(f"  Success: {fix_result.success}")
            print()
            
            if fix_result.final_content and fix_result.final_content != problematic_code:
                print("✨ Fixed code:")
                print(fix_result.final_content)
                
                # Validate the fixes
                is_valid = engine.validate_fixes(fix_result, context)
                print(f"✅ Validation: {'PASSED' if is_valid else 'FAILED'}")
            else:
                print("ℹ️  No changes were made to the code.")
        else:
            print("ℹ️  No fixable issues found.")
        
        # Show engine stats
        print("\n📈 Engine Statistics:")
        stats = engine.get_engine_stats()
        print(f"  Total fixers: {stats['total_fixers']}")
        print(f"  Safety level: {stats['safety_level']}")
        print(f"  Available fixers: {', '.join(stats['available_fixers'])}")
        
        print("\n🎉 Demo completed successfully!")
        
    finally:
        # Clean up
        Path(temp_file).unlink()


if __name__ == "__main__":
    demo_auto_fix_engine()