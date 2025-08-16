#!/usr/bin/env python3
"""
Demo script for automated code review integration.
Demonstrates pre-commit hooks, pull request integration, and quality gate enforcement.
"""

import asyncio
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

from app.services.code_analysis.code_review_integration import (
    CodeReviewWorkflowAutomation,
    PreCommitHookManager,
    PullRequestIntegration,
    QualityGateEvaluator,
    QualityGate,
    QualityGateResult,
    ReviewStatus
)
from app.services.code_analysis.scanning_framework import ScanConfiguration


def create_demo_project():
    """Create a demo project with various code quality issues."""
    temp_dir = tempfile.mkdtemp(prefix="code_review_demo_")
    project_path = Path(temp_dir)
    
    print(f"📁 Creating demo project at: {project_path}")
    
    # Initialize Git repository
    subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Demo User"], cwd=project_path, check=True)
    subprocess.run(["git", "config", "user.email", "demo@example.com"], cwd=project_path, check=True)
    
    # Create Python files with different quality levels
    
    # Good quality file
    good_file = project_path / "good_module.py"
    good_file.write_text('''"""
A well-structured Python module demonstrating good coding practices.
"""

from typing import List, Optional
import logging


logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes data with proper error handling and documentation."""
    
    def __init__(self, max_items: int = 1000):
        """Initialize the processor.
        
        Args:
            max_items: Maximum number of items to process
        """
        self.max_items = max_items
        self.processed_count = 0
    
    def process_items(self, items: List[str]) -> List[str]:
        """Process a list of items.
        
        Args:
            items: List of items to process
            
        Returns:
            List of processed items
            
        Raises:
            ValueError: If too many items provided
        """
        if len(items) > self.max_items:
            raise ValueError(f"Too many items: {len(items)} > {self.max_items}")
        
        processed = []
        for item in items:
            if item and item.strip():
                processed.append(item.strip().upper())
                self.processed_count += 1
        
        logger.info(f"Processed {len(processed)} items")
        return processed
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "max_items": self.max_items
        }


def main():
    """Main function."""
    processor = DataProcessor()
    items = ["hello", "world", "python"]
    result = processor.process_items(items)
    print(f"Processed: {result}")


if __name__ == "__main__":
    main()
''')
    
    # File with style issues
    style_issues_file = project_path / "style_issues.py"
    style_issues_file.write_text('''
# File with various style issues

import os,sys,json
from datetime import datetime,timezone

def   bad_function(  x,y,z  ):
    # Poor formatting and style
    result=x+y+z
    if result>10:
        print( "Result is greater than 10" )
    else:
        print("Result is less than or equal to 10")
    return result

class   BadClass:
    def __init__(self,value):
        self.value=value
    
    def process(self):
        # Very long line that exceeds recommended length and should be split into multiple lines for better readability
        return self.value * 2 + self.value * 3 + self.value * 4 + self.value * 5 + self.value * 6

def another_function():
    x = 1
    y = 2
    z = 3
    
    
    
    # Multiple blank lines above
    return x + y + z
''')
    
    # File with complexity issues
    complexity_file = project_path / "complex_code.py"
    complexity_file.write_text('''
def complex_function(data, mode, options, flags, settings):
    """A function with high cyclomatic complexity."""
    result = []
    
    if mode == "process":
        if options.get("validate"):
            if flags & 0x01:
                if settings["strict"]:
                    for item in data:
                        if isinstance(item, dict):
                            if "id" in item:
                                if item["id"] > 0:
                                    if "name" in item:
                                        if len(item["name"]) > 0:
                                            if item["name"].isalnum():
                                                result.append(item)
                                            else:
                                                if settings["allow_special"]:
                                                    result.append(item)
                                        else:
                                            if settings["allow_empty"]:
                                                result.append(item)
                                else:
                                    if settings["allow_negative_id"]:
                                        result.append(item)
                            else:
                                if settings["require_id"]:
                                    continue
                                else:
                                    result.append(item)
                        else:
                            if settings["allow_non_dict"]:
                                result.append(item)
                else:
                    result = data
            else:
                if flags & 0x02:
                    result = [item for item in data if item]
                else:
                    result = data
        else:
            result = data
    elif mode == "filter":
        if options.get("criteria"):
            result = [item for item in data if item.get("active", True)]
        else:
            result = data
    else:
        result = data
    
    return result
''')
    
    # File with security issues
    security_file = project_path / "security_issues.py"
    security_file.write_text('''
import os
import subprocess
import pickle

def unsafe_command_execution(user_input):
    """Unsafe command execution - security vulnerability."""
    # This is a security issue: command injection vulnerability
    command = f"ls {user_input}"
    result = os.system(command)
    return result

def unsafe_pickle_load(data):
    """Unsafe pickle deserialization - security vulnerability."""
    # This is a security issue: arbitrary code execution
    return pickle.loads(data)

def unsafe_eval(expression):
    """Unsafe eval usage - security vulnerability."""
    # This is a security issue: code injection
    return eval(expression)

def hardcoded_credentials():
    """Hardcoded credentials - security issue."""
    password = "admin123"  # Hardcoded password
    api_key = "sk-1234567890abcdef"  # Hardcoded API key
    return password, api_key

def sql_injection_risk(user_id):
    """SQL injection risk - security vulnerability."""
    # This would be a SQL injection vulnerability in real code
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query
''')
    
    # Create initial commit
    subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_path, check=True, capture_output=True)
    
    print("✅ Demo project created with various code quality scenarios")
    return str(project_path)


async def demo_quality_gate_evaluation():
    """Demonstrate quality gate evaluation with different scenarios."""
    print("\n" + "="*60)
    print("🚪 QUALITY GATE EVALUATION DEMO")
    print("="*60)
    
    evaluator = QualityGateEvaluator()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Clean Code",
            "issues_by_severity": {"low": 2},
            "issues_by_type": {"style": 2},
            "total_issues": 2
        },
        {
            "name": "Minor Issues",
            "issues_by_severity": {"medium": 5, "low": 10},
            "issues_by_type": {"style": 12, "complexity": 3},
            "total_issues": 15
        },
        {
            "name": "Security Issues",
            "issues_by_severity": {"high": 2, "medium": 3},
            "issues_by_type": {"security": 2, "style": 3},
            "total_issues": 5
        },
        {
            "name": "Critical Issues",
            "issues_by_severity": {"critical": 1, "high": 3, "medium": 8},
            "issues_by_type": {"security": 1, "complexity": 3, "style": 8},
            "total_issues": 12
        }
    ]
    
    gates = ["lenient", "standard", "strict"]
    
    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        print(f"   Issues: {scenario['total_issues']} total")
        print(f"   By severity: {scenario['issues_by_severity']}")
        print(f"   By type: {scenario['issues_by_type']}")
        
        # Mock scan result
        from unittest.mock import Mock
        from app.services.code_analysis.scanning_framework import ScanResult
        
        scan_result = Mock(spec=ScanResult)
        scan_result.issues_by_severity = scenario["issues_by_severity"]
        scan_result.issues_by_type = scenario["issues_by_type"]
        scan_result.total_issues = scenario["total_issues"]
        scan_result.metrics = None
        scan_result.analysis_results = []  # Mock empty analysis results
        
        for gate in gates:
            result, reasons = evaluator.evaluate_gate(gate, scan_result)
            
            status_emoji = {
                QualityGateResult.PASS: "✅",
                QualityGateResult.CONDITIONAL_PASS: "⚠️",
                QualityGateResult.FAIL: "❌"
            }
            
            emoji = status_emoji.get(result, "❓")
            print(f"   {gate.upper():>8} gate: {emoji} {result.value}")
            
            if result == QualityGateResult.FAIL and len(reasons) > 0:
                print(f"            Reasons: {reasons[0]}")


async def demo_pre_commit_hooks(project_path: str):
    """Demonstrate pre-commit hook functionality."""
    print("\n" + "="*60)
    print("🪝 PRE-COMMIT HOOKS DEMO")
    print("="*60)
    
    manager = PreCommitHookManager(project_path, "demo-project")
    
    print("📝 Installing pre-commit and pre-push hooks...")
    success = manager.install_hooks()
    
    if success:
        print("✅ Hooks installed successfully!")
        
        # Show hook files
        hooks_dir = Path(project_path) / ".git" / "hooks"
        pre_commit_hook = hooks_dir / "pre-commit"
        pre_push_hook = hooks_dir / "pre-push"
        
        if pre_commit_hook.exists():
            print(f"📄 Pre-commit hook created: {pre_commit_hook}")
            print("   Hook will run quality checks before each commit")
        
        if pre_push_hook.exists():
            print(f"📄 Pre-push hook created: {pre_push_hook}")
            print("   Hook will run comprehensive analysis before push")
    else:
        print("❌ Failed to install hooks")
    
    # Simulate pre-commit check
    print("\n🔍 Simulating pre-commit quality check...")
    
    # Stage some files
    subprocess.run(["git", "add", "style_issues.py"], cwd=project_path, capture_output=True)
    
    try:
        result = await manager.run_pre_commit_checks("standard")
        
        print(f"📊 Pre-commit check results:")
        print(f"   Status: {result.status.value}")
        print(f"   Issues found: {result.issues_found}")
        print(f"   Issues fixed: {result.issues_fixed}")
        print(f"   Issues remaining: {result.issues_remaining}")
        print(f"   Execution time: {result.execution_time:.2f}s")
        
        if result.quality_gate_result:
            print(f"   Quality gate: {result.quality_gate_result.value}")
        
        if result.messages:
            print("   Messages:")
            for msg in result.messages[:3]:  # Show first 3 messages
                print(f"     • {msg}")
        
        if result.blocking_issues:
            print(f"   Blocking issues: {len(result.blocking_issues)}")
        
    except Exception as e:
        print(f"❌ Pre-commit check failed: {e}")


async def demo_pull_request_integration(project_path: str):
    """Demonstrate pull request integration."""
    print("\n" + "="*60)
    print("🔀 PULL REQUEST INTEGRATION DEMO")
    print("="*60)
    
    # Create a feature branch
    print("🌿 Creating feature branch...")
    subprocess.run(["git", "checkout", "-b", "feature/security-fixes"], 
                  cwd=project_path, check=True, capture_output=True)
    
    # Make some changes
    feature_file = Path(project_path) / "new_feature.py"
    feature_file.write_text('''
"""New feature with mixed quality."""

def new_feature_function(data):
    """Process data with some issues."""
    # This has some style issues but is functional
    result=[]
    for item in data:
        if item:
            result.append(item.upper())
    return result

def secure_function(user_input):
    """A more secure version of input processing."""
    # Better approach - validate input
    if not isinstance(user_input, str):
        raise ValueError("Input must be a string")
    
    # Sanitize input
    sanitized = user_input.strip()[:100]  # Limit length
    
    return sanitized
''')
    
    subprocess.run(["git", "add", "new_feature.py"], cwd=project_path, check=True, capture_output=True)
    
    # Check if there are changes to commit
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=project_path, capture_output=True)
    if result.returncode != 0:  # There are changes to commit
        try:
            subprocess.run(["git", "commit", "-m", "Add new feature with security improvements"], 
                          cwd=project_path, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git commit failed: {e}")
            # Check git status
            status_result = subprocess.run(["git", "status", "--porcelain"], 
                                         cwd=project_path, capture_output=True, text=True)
            print(f"Git status: {status_result.stdout}")
    else:
        print("⚠️ No changes to commit")
    
    # Switch back to main for PR analysis
    subprocess.run(["git", "checkout", "main"], cwd=project_path, check=True, capture_output=True)
    
    # Analyze the "pull request"
    print("🔍 Analyzing pull request...")
    
    pr_integration = PullRequestIntegration(project_path, "demo-project")
    
    try:
        analysis = await pr_integration.analyze_pull_request(
            "PR-123",
            "main",
            "feature/security-fixes",
            "standard"
        )
        
        print(f"📊 Pull Request Analysis Results:")
        print(f"   PR ID: {analysis.pr_id}")
        print(f"   Status: {analysis.overall_status.value}")
        print(f"   Quality Gate: {analysis.quality_gate_result.value}")
        print(f"   Changed Files: {len(analysis.changed_files)}")
        print(f"   New Issues: {len(analysis.new_issues)}")
        print(f"   Auto-fixes Applied: {analysis.auto_fixes_applied}")
        print(f"   Manual Review Required: {analysis.manual_review_required}")
        
        if analysis.changed_files:
            print("   Changed files:")
            for file in analysis.changed_files[:5]:  # Show first 5
                print(f"     • {file}")
        
        if analysis.recommendations:
            print("   Recommendations:")
            for rec in analysis.recommendations[:3]:  # Show first 3
                print(f"     • {rec}")
        
        # Generate PR comment
        print("\n💬 Generated PR Comment:")
        comment = await pr_integration.create_pr_comment(analysis)
        print("   " + "\n   ".join(comment.split("\n")[:15]))  # Show first 15 lines
        if len(comment.split("\n")) > 15:
            print("   ... (truncated)")
        
    except Exception as e:
        print(f"❌ PR analysis failed: {e}")


async def demo_complete_workflow(project_path: str):
    """Demonstrate complete automated workflow setup."""
    print("\n" + "="*60)
    print("🔄 COMPLETE WORKFLOW AUTOMATION DEMO")
    print("="*60)
    
    workflow = CodeReviewWorkflowAutomation(project_path, "demo-project")
    
    print("⚙️ Setting up automated workflow...")
    success = await workflow.setup_automated_workflow("standard")
    
    if success:
        print("✅ Automated workflow set up successfully!")
        print("   • Pre-commit hooks installed")
        print("   • Pre-push hooks installed")
        print("   • Quality gates configured")
        print("   • Integration ready for CI/CD")
    else:
        print("❌ Failed to set up automated workflow")
    
    # Run full quality check
    print("\n🔍 Running full project quality check...")
    try:
        result = await workflow.run_full_quality_check("standard")
        
        print(f"📊 Full Quality Check Results:")
        print(f"   Overall Status: {result.status.value}")
        print(f"   Total Issues: {result.issues_found}")
        print(f"   Auto-fixes Applied: {result.issues_fixed}")
        print(f"   Remaining Issues: {result.issues_remaining}")
        print(f"   Execution Time: {result.execution_time:.2f}s")
        
        if result.scan_result:
            print(f"   Files Scanned: {result.scan_result.files_scanned}")
            print(f"   Files with Issues: {result.scan_result.files_with_issues}")
            
            if result.scan_result.issues_by_severity:
                print("   Issues by Severity:")
                for severity, count in result.scan_result.issues_by_severity.items():
                    print(f"     {severity}: {count}")
        
    except Exception as e:
        print(f"❌ Full quality check failed: {e}")
    
    # Demonstrate workflow removal
    print("\n🗑️ Demonstrating workflow removal...")
    removed = workflow.remove_automated_workflow()
    if removed:
        print("✅ Automated workflow removed successfully")
    else:
        print("❌ Failed to remove automated workflow")


async def main():
    """Run the complete code review integration demo."""
    print("🚀 AUTOMATED CODE REVIEW INTEGRATION DEMO")
    print("=" * 60)
    print("This demo showcases automated code review integration features:")
    print("• Quality gate evaluation")
    print("• Pre-commit hooks")
    print("• Pull request integration")
    print("• Complete workflow automation")
    print("=" * 60)
    
    # Create demo project
    project_path = create_demo_project()
    
    try:
        # Run all demos
        await demo_quality_gate_evaluation()
        await demo_pre_commit_hooks(project_path)
        await demo_pull_request_integration(project_path)
        await demo_complete_workflow(project_path)
        
        print("\n" + "="*60)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Key Features Demonstrated:")
        print("• ✅ Quality gates with different strictness levels")
        print("• ✅ Pre-commit hooks for automatic quality checks")
        print("• ✅ Pull request analysis and recommendations")
        print("• ✅ Complete workflow automation setup")
        print("• ✅ Integration with Git workflows")
        print("\nThe automated code review integration is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up demo project: {project_path}")
        try:
            shutil.rmtree(project_path)
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    asyncio.run(main())