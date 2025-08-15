#!/usr/bin/env python3
"""
Demo script to showcase the code scanning framework.
"""

import asyncio
import tempfile
from pathlib import Path

from app.services.code_analysis import (
    CodeScanningFramework, ScanConfiguration, AnalysisType
)


async def demo_code_scanning():
    """Demonstrate the code scanning framework."""
    print("🔍 Code Quality Scanning Framework Demo")
    print("=" * 50)
    
    # Create a temporary project with some test files
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create test files with various quality issues
        test_files = {
            "good_code.py": """
def calculate_area(radius):
    \"\"\"Calculate the area of a circle.\"\"\"
    import math
    return math.pi * radius ** 2


class Circle:
    \"\"\"A simple circle class.\"\"\"
    
    def __init__(self, radius):
        self.radius = radius
    
    def area(self):
        \"\"\"Calculate area.\"\"\"
        return calculate_area(self.radius)
""",
            "problematic_code.py": """
# This file has various quality issues
import os, sys, json, re, time, datetime, collections, itertools, functools

def very_long_function_name_that_exceeds_reasonable_limits_and_should_be_shortened():
    password = "hardcoded_secret_123"   
    x = "This line is way too long and exceeds the maximum line length limit that we have set for our code style guidelines and should be broken into multiple lines"
    
    
    
    # Multiple blank lines above
    
    for i in range(len(some_list)):  # Inefficient loop
        print(i)
    
    query = "SELECT * FROM users WHERE name = '%s'" % user_input  # SQL injection risk

class BadClass:
    def method_with_too_many_args(self, a, b, c, d, e, f, g, h):
        pass
        
    def method_without_docstring(self):
        return 42
""",
            "syntax_error.py": """
def broken_function(
    # Missing closing parenthesis
    return "This will cause a syntax error"
""",
            "empty_file.py": "",
            "javascript_file.js": """
// JavaScript file with some issues
function longFunctionNameThatExceedsReasonableLimits() {
    var password = 'hardcoded_password_123';
    console.log('This line is extremely long and should be broken into multiple lines to improve readability and maintainability');
}
"""
        }
        
        # Write test files
        for filename, content in test_files.items():
            file_path = project_path / filename
            file_path.write_text(content)
        
        print(f"📁 Created test project in: {project_path}")
        print(f"📄 Test files: {list(test_files.keys())}")
        print()
        
        # Initialize the scanning framework
        framework = CodeScanningFramework()
        
        # Add callbacks to show progress
        def on_scan_started(scan_result):
            print(f"🚀 Started scan: {scan_result.scan_id}")
        
        def on_file_analyzed(analysis_result):
            file_name = Path(analysis_result.context.file_path).name
            issue_count = len(analysis_result.issues)
            print(f"  📝 Analyzed {file_name}: {issue_count} issues found")
        
        def on_scan_completed(scan_result):
            print(f"✅ Completed scan: {scan_result.scan_id}")
            print(f"   Files scanned: {scan_result.files_scanned}")
            print(f"   Total issues: {scan_result.total_issues}")
        
        framework.add_scan_started_callback(on_scan_started)
        framework.add_file_analyzed_callback(on_file_analyzed)
        framework.add_scan_completed_callback(on_scan_completed)
        
        # Configure the scan
        config = ScanConfiguration(
            project_id="demo_project",
            project_path=str(project_path),
            file_patterns=["**/*.py", "**/*.js"],
            parallel_workers=2,
            analysis_types={AnalysisType.STYLE, AnalysisType.SECURITY, AnalysisType.COMPLEXITY}
        )
        
        print("🔍 Starting project scan...")
        print()
        
        # Run the scan
        scan_result = await framework.scan_project(config)
        
        print()
        print("📊 Scan Results Summary")
        print("-" * 30)
        print(f"Success: {scan_result.success}")
        print(f"Files scanned: {scan_result.files_scanned}")
        print(f"Files with issues: {scan_result.files_with_issues}")
        print(f"Total issues: {scan_result.total_issues}")
        print(f"Execution time: {scan_result.execution_time:.2f}s")
        
        if scan_result.issues_by_severity:
            print("\n🚨 Issues by Severity:")
            for severity, count in scan_result.issues_by_severity.items():
                print(f"  {severity.upper()}: {count}")
        
        if scan_result.issues_by_type:
            print("\n🏷️  Issues by Type:")
            for issue_type, count in scan_result.issues_by_type.items():
                print(f"  {issue_type.upper()}: {count}")
        
        # Show detailed issues for each file
        print("\n📋 Detailed Issues by File")
        print("-" * 40)
        
        for analysis_result in scan_result.analysis_results:
            file_name = Path(analysis_result.context.file_path).name
            if analysis_result.issues:
                print(f"\n📄 {file_name}:")
                for issue in analysis_result.issues[:5]:  # Show first 5 issues
                    location = f"Line {issue.line_number}" if issue.line_number else "Unknown"
                    print(f"  • {issue.severity.value.upper()}: {issue.description} ({location})")
                    if issue.suggested_fix:
                        print(f"    💡 Suggestion: {issue.suggested_fix}")
                
                if len(analysis_result.issues) > 5:
                    print(f"  ... and {len(analysis_result.issues) - 5} more issues")
            else:
                print(f"\n📄 {file_name}: ✅ No issues found")
        
        # Show quality metrics if available
        if scan_result.metrics:
            print("\n📈 Quality Metrics")
            print("-" * 20)
            metrics = scan_result.metrics
            if metrics.lines_of_code:
                print(f"Lines of code: {metrics.lines_of_code}")
            if metrics.technical_debt_ratio:
                print(f"Technical debt ratio: {metrics.technical_debt_ratio:.3f}")
            if metrics.security_score:
                print(f"Security score: {metrics.security_score:.1f}/100")
            if metrics.maintainability_index:
                print(f"Maintainability index: {metrics.maintainability_index:.1f}/100")
        
        print("\n🎉 Demo completed successfully!")
        
        # Test single file scanning
        print("\n" + "=" * 50)
        print("🔍 Single File Scan Demo")
        print("=" * 50)
        
        problematic_file = project_path / "problematic_code.py"
        print(f"📄 Scanning: {problematic_file.name}")
        
        file_result = await framework.scan_file(str(problematic_file), "demo_project")
        
        print(f"✅ Analysis completed: {file_result.success}")
        print(f"🚨 Issues found: {len(file_result.issues)}")
        print(f"⏱️  Execution time: {file_result.execution_time:.3f}s")
        
        if file_result.issues:
            print("\n📋 Issues found:")
            for i, issue in enumerate(file_result.issues[:3], 1):
                location = f"Line {issue.line_number}" if issue.line_number else "Unknown"
                print(f"  {i}. {issue.severity.value.upper()}: {issue.description} ({location})")
        
        print("\n🎉 Single file demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_code_scanning())