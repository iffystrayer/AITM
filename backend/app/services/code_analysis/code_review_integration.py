"""
Automated code review integration system.
Implements pre-commit hooks, pull request integration, and quality gate enforcement.
"""

import os
import json
import subprocess
import tempfile
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from enum import Enum

from .scanning_framework import CodeScanningFramework, ScanConfiguration, ScanResult
from .auto_fix_engine import AutoFixEngine, FixApplicationResult
from ..quality_issue_tracker import QualityIssueTracker
from app.models.quality import QualityIssue, Severity, IssueStatus
from app.core.quality_config import QualityConfigManager


class ReviewStatus(str, Enum):
    """Status of code review checks."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    BLOCKED = "blocked"


class QualityGateResult(str, Enum):
    """Result of quality gate evaluation."""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL_PASS = "conditional_pass"


@dataclass
class QualityGate:
    """Configuration for quality gates."""
    name: str
    description: str
    max_critical_issues: int = 0
    max_high_issues: int = 5
    max_medium_issues: int = 20
    min_test_coverage: float = 80.0
    max_complexity_score: float = 10.0
    max_technical_debt_ratio: float = 0.1
    block_on_security_issues: bool = True
    allow_auto_fix_bypass: bool = True
    required_approvals: int = 1


@dataclass
class PreCommitResult:
    """Result of pre-commit quality checks."""
    status: ReviewStatus
    issues_found: int
    issues_fixed: int
    issues_remaining: int
    execution_time: float
    scan_result: Optional[ScanResult] = None
    fix_result: Optional[FixApplicationResult] = None
    quality_gate_result: Optional[QualityGateResult] = None
    messages: List[str] = field(default_factory=list)
    blocking_issues: List[QualityIssue] = field(default_factory=list)


@dataclass
class PullRequestAnalysis:
    """Analysis result for pull request."""
    pr_id: str
    project_id: str
    base_branch: str
    head_branch: str
    changed_files: List[str]
    analysis_timestamp: datetime
    overall_status: ReviewStatus
    quality_gate_result: QualityGateResult
    new_issues: List[QualityIssue]
    fixed_issues: List[QualityIssue]
    quality_score_change: float
    coverage_change: float
    complexity_change: float
    recommendations: List[str]
    auto_fixes_applied: int
    manual_review_required: bool


class GitHookManager:
    """Manages Git hooks for quality checks."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.hooks_dir = self.repo_path / ".git" / "hooks"
        self.quality_hooks_dir = self.repo_path / ".quality-hooks"
    
    def install_pre_commit_hook(self, hook_script: str) -> bool:
        """Install pre-commit hook script."""
        try:
            # Ensure hooks directory exists
            self.hooks_dir.mkdir(exist_ok=True)
            self.quality_hooks_dir.mkdir(exist_ok=True)
            
            # Write the hook script
            hook_path = self.hooks_dir / "pre-commit"
            with open(hook_path, 'w') as f:
                f.write(hook_script)
            
            # Make executable
            os.chmod(hook_path, 0o755)
            
            return True
            
        except Exception as e:
            print(f"Failed to install pre-commit hook: {e}")
            return False
    
    def install_pre_push_hook(self, hook_script: str) -> bool:
        """Install pre-push hook script."""
        try:
            hook_path = self.hooks_dir / "pre-push"
            with open(hook_path, 'w') as f:
                f.write(hook_script)
            
            os.chmod(hook_path, 0o755)
            return True
            
        except Exception as e:
            print(f"Failed to install pre-push hook: {e}")
            return False
    
    def uninstall_hooks(self) -> bool:
        """Remove quality hooks."""
        try:
            hooks_to_remove = ["pre-commit", "pre-push"]
            
            for hook_name in hooks_to_remove:
                hook_path = self.hooks_dir / hook_name
                if hook_path.exists():
                    hook_path.unlink()
            
            # Remove quality hooks directory
            if self.quality_hooks_dir.exists():
                shutil.rmtree(self.quality_hooks_dir)
            
            return True
            
        except Exception as e:
            print(f"Failed to uninstall hooks: {e}")
            return False
    
    def get_changed_files(self, base_ref: str = "HEAD") -> List[str]:
        """Get list of changed files."""
        try:
            # Get staged files for pre-commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split('\n') if f.strip()]
            
            return []
            
        except Exception as e:
            print(f"Failed to get changed files: {e}")
            return []


class QualityGateEvaluator:
    """Evaluates quality gates for merge decisions."""
    
    def __init__(self, config_manager: Optional[QualityConfigManager] = None):
        self.config_manager = config_manager or QualityConfigManager()
        self.default_gates = self._create_default_gates()
    
    def _create_default_gates(self) -> Dict[str, QualityGate]:
        """Create default quality gates."""
        return {
            "strict": QualityGate(
                name="Strict Quality Gate",
                description="High quality standards for production code",
                max_critical_issues=0,
                max_high_issues=0,
                max_medium_issues=5,
                min_test_coverage=90.0,
                max_complexity_score=8.0,
                max_technical_debt_ratio=0.05,
                block_on_security_issues=True,
                allow_auto_fix_bypass=False,
                required_approvals=2
            ),
            "standard": QualityGate(
                name="Standard Quality Gate",
                description="Balanced quality standards for regular development",
                max_critical_issues=0,
                max_high_issues=3,
                max_medium_issues=15,
                min_test_coverage=80.0,
                max_complexity_score=10.0,
                max_technical_debt_ratio=0.1,
                block_on_security_issues=True,
                allow_auto_fix_bypass=True,
                required_approvals=1
            ),
            "lenient": QualityGate(
                name="Lenient Quality Gate",
                description="Relaxed standards for experimental or legacy code",
                max_critical_issues=1,
                max_high_issues=10,
                max_medium_issues=50,
                min_test_coverage=60.0,
                max_complexity_score=15.0,
                max_technical_debt_ratio=0.2,
                block_on_security_issues=True,
                allow_auto_fix_bypass=True,
                required_approvals=1
            )
        }
    
    def evaluate_gate(self, gate_name: str, scan_result: ScanResult,
                     coverage_data: Optional[Dict[str, float]] = None) -> Tuple[QualityGateResult, List[str]]:
        """
        Evaluate a quality gate against scan results.
        
        Args:
            gate_name: Name of the quality gate to evaluate
            scan_result: Results from code scanning
            coverage_data: Optional test coverage data
            
        Returns:
            Tuple of (result, reasons)
        """
        gate = self.default_gates.get(gate_name)
        if not gate:
            return QualityGateResult.FAIL, [f"Unknown quality gate: {gate_name}"]
        
        reasons = []
        blocking_issues = []
        
        # Check issue counts by severity
        critical_count = scan_result.issues_by_severity.get('critical', 0)
        high_count = scan_result.issues_by_severity.get('high', 0)
        medium_count = scan_result.issues_by_severity.get('medium', 0)
        
        if critical_count > gate.max_critical_issues:
            blocking_issues.append(f"Critical issues: {critical_count} > {gate.max_critical_issues}")
        
        if high_count > gate.max_high_issues:
            blocking_issues.append(f"High severity issues: {high_count} > {gate.max_high_issues}")
        
        if medium_count > gate.max_medium_issues:
            blocking_issues.append(f"Medium severity issues: {medium_count} > {gate.max_medium_issues}")
        
        # Check security issues
        if gate.block_on_security_issues:
            security_count = scan_result.issues_by_type.get('security', 0)
            if security_count > 0:
                blocking_issues.append(f"Security issues found: {security_count}")
        
        # Check test coverage
        if coverage_data and 'overall_coverage' in coverage_data:
            coverage = coverage_data['overall_coverage']
            if coverage < gate.min_test_coverage:
                blocking_issues.append(f"Test coverage: {coverage:.1f}% < {gate.min_test_coverage}%")
        
        # Check complexity and technical debt
        if scan_result.metrics:
            if hasattr(scan_result.metrics, 'cyclomatic_complexity') and scan_result.metrics.cyclomatic_complexity is not None:
                complexity = scan_result.metrics.cyclomatic_complexity
                if complexity > gate.max_complexity_score:
                    blocking_issues.append(f"Complexity score: {complexity:.1f} > {gate.max_complexity_score}")
            
            if hasattr(scan_result.metrics, 'technical_debt_ratio') and scan_result.metrics.technical_debt_ratio is not None:
                debt_ratio = scan_result.metrics.technical_debt_ratio
                if debt_ratio > gate.max_technical_debt_ratio:
                    blocking_issues.append(f"Technical debt ratio: {debt_ratio:.2f} > {gate.max_technical_debt_ratio}")
        
        # Determine result
        if not blocking_issues:
            return QualityGateResult.PASS, ["All quality gate criteria met"]
        
        # Check if auto-fixes can resolve issues
        if gate.allow_auto_fix_bypass:
            auto_fixable_issues = sum(1 for result in scan_result.analysis_results 
                                    for issue in result.issues if issue.auto_fixable)
            
            if auto_fixable_issues >= len(blocking_issues):
                return QualityGateResult.CONDITIONAL_PASS, [
                    "Quality gate can pass with auto-fixes applied"
                ] + blocking_issues
        
        return QualityGateResult.FAIL, blocking_issues


class PreCommitHookManager:
    """Manages pre-commit quality checks and auto-fixes."""
    
    def __init__(self, project_path: str, project_id: str):
        self.project_path = project_path
        self.project_id = project_id
        self.scanner = CodeScanningFramework()
        self.auto_fixer = AutoFixEngine()
        self.issue_tracker = QualityIssueTracker()
        self.gate_evaluator = QualityGateEvaluator()
        self.git_manager = GitHookManager(project_path)
    
    async def run_pre_commit_checks(self, quality_gate: str = "standard") -> PreCommitResult:
        """
        Run comprehensive pre-commit quality checks.
        
        Args:
            quality_gate: Name of quality gate to evaluate
            
        Returns:
            PreCommitResult with check results
        """
        start_time = datetime.now()
        
        try:
            # Get changed files
            changed_files = self.git_manager.get_changed_files()
            
            if not changed_files:
                return PreCommitResult(
                    status=ReviewStatus.PASSED,
                    issues_found=0,
                    issues_fixed=0,
                    issues_remaining=0,
                    execution_time=0.0,
                    messages=["No files to check"]
                )
            
            # Configure scan for changed files only
            config = ScanConfiguration(
                project_id=self.project_id,
                project_path=self.project_path,
                file_patterns=[f for f in changed_files if self._should_scan_file(f)]
            )
            
            # Run quality scan
            scan_result = await self.scanner.scan_project(config)
            
            # Apply auto-fixes if issues found
            fix_result = None
            if scan_result.total_issues > 0:
                fix_result = await self._apply_auto_fixes(scan_result)
            
            # Evaluate quality gate
            gate_result, gate_reasons = self.gate_evaluator.evaluate_gate(
                quality_gate, scan_result
            )
            
            # Determine overall status
            status = self._determine_status(scan_result, gate_result, fix_result)
            
            # Calculate remaining issues after fixes
            issues_remaining = scan_result.total_issues
            issues_fixed = 0
            
            if fix_result:
                issues_fixed = fix_result.fixes_applied
                issues_remaining = max(0, scan_result.total_issues - issues_fixed)
            
            # Collect blocking issues
            blocking_issues = []
            if gate_result == QualityGateResult.FAIL:
                blocking_issues = [
                    issue for result in scan_result.analysis_results
                    for issue in result.issues
                    if issue.severity in [Severity.CRITICAL, Severity.HIGH]
                ]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return PreCommitResult(
                status=status,
                issues_found=scan_result.total_issues,
                issues_fixed=issues_fixed,
                issues_remaining=issues_remaining,
                execution_time=execution_time,
                scan_result=scan_result,
                fix_result=fix_result,
                quality_gate_result=gate_result,
                messages=gate_reasons,
                blocking_issues=blocking_issues
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return PreCommitResult(
                status=ReviewStatus.FAILED,
                issues_found=0,
                issues_fixed=0,
                issues_remaining=0,
                execution_time=execution_time,
                messages=[f"Pre-commit check failed: {str(e)}"]
            )
    
    def _should_scan_file(self, file_path: str) -> bool:
        """Check if file should be scanned."""
        # Skip certain file types and directories
        skip_patterns = [
            '.git/', '__pycache__/', 'node_modules/', '.venv/',
            '.pyc', '.pyo', '.pyd', '.so', '.dylib', '.dll',
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx'
        ]
        
        for pattern in skip_patterns:
            if pattern in file_path:
                return False
        
        return True
    
    async def _apply_auto_fixes(self, scan_result: ScanResult) -> Optional[FixApplicationResult]:
        """Apply auto-fixes to issues found in scan."""
        try:
            # Collect all auto-fixable issues
            fixable_issues = []
            for result in scan_result.analysis_results:
                for issue in result.issues:
                    if issue.auto_fixable:
                        fixable_issues.append(issue)
            
            if not fixable_issues:
                return None
            
            # Apply fixes
            return await self.auto_fixer.apply_fixes_to_issues(fixable_issues)
            
        except Exception as e:
            print(f"Error applying auto-fixes: {e}")
            return None
    
    def _determine_status(self, scan_result: ScanResult, gate_result: QualityGateResult,
                         fix_result: Optional[FixApplicationResult]) -> ReviewStatus:
        """Determine overall pre-commit status."""
        if gate_result == QualityGateResult.PASS:
            return ReviewStatus.PASSED
        elif gate_result == QualityGateResult.CONDITIONAL_PASS:
            return ReviewStatus.WARNING
        else:
            # Check if critical issues remain
            critical_issues = scan_result.issues_by_severity.get('critical', 0)
            if critical_issues > 0:
                return ReviewStatus.BLOCKED
            else:
                return ReviewStatus.FAILED
    
    def install_hooks(self) -> bool:
        """Install pre-commit and pre-push hooks."""
        try:
            # Generate pre-commit hook script
            pre_commit_script = self._generate_pre_commit_script()
            
            # Generate pre-push hook script
            pre_push_script = self._generate_pre_push_script()
            
            # Install hooks
            success = (
                self.git_manager.install_pre_commit_hook(pre_commit_script) and
                self.git_manager.install_pre_push_hook(pre_push_script)
            )
            
            if success:
                print("Quality hooks installed successfully")
            
            return success
            
        except Exception as e:
            print(f"Failed to install hooks: {e}")
            return False
    
    def _generate_pre_commit_script(self) -> str:
        """Generate pre-commit hook script."""
        return f'''#!/bin/bash
# Auto-generated quality pre-commit hook

echo "Running quality checks..."

# Run Python quality checks
python -c "
import asyncio
import sys
import os
sys.path.append('{self.project_path}')

from backend.app.services.code_analysis.code_review_integration import PreCommitHookManager

async def main():
    manager = PreCommitHookManager('{self.project_path}', '{self.project_id}')
    result = await manager.run_pre_commit_checks()
    
    print(f'Quality check result: {{result.status.value}}')
    print(f'Issues found: {{result.issues_found}}')
    print(f'Issues fixed: {{result.issues_fixed}}')
    print(f'Issues remaining: {{result.issues_remaining}}')
    
    for message in result.messages:
        print(f'  {{message}}')
    
    if result.status in ['blocked', 'failed']:
        print('\\nCommit blocked due to quality issues.')
        print('Please fix the issues above and try again.')
        sys.exit(1)
    elif result.status == 'warning':
        print('\\nCommit allowed with warnings.')
        print('Consider addressing the issues above.')
    else:
        print('\\nQuality checks passed!')

asyncio.run(main())
"

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Pre-commit quality checks failed"
    exit 1
fi

echo "Pre-commit quality checks passed"
'''
    
    def _generate_pre_push_script(self) -> str:
        """Generate pre-push hook script."""
        return f'''#!/bin/bash
# Auto-generated quality pre-push hook

echo "Running comprehensive quality analysis before push..."

# Run full project scan with strict quality gate
python -c "
import asyncio
import sys
import os
sys.path.append('{self.project_path}')

from backend.app.services.code_analysis.code_review_integration import PreCommitHookManager

async def main():
    manager = PreCommitHookManager('{self.project_path}', '{self.project_id}')
    result = await manager.run_pre_commit_checks('strict')
    
    print(f'Quality analysis result: {{result.status.value}}')
    print(f'Issues found: {{result.issues_found}}')
    print(f'Issues remaining: {{result.issues_remaining}}')
    
    if result.status == 'blocked':
        print('\\nPush blocked due to critical quality issues.')
        sys.exit(1)
    elif result.status == 'failed':
        print('\\nPush blocked due to quality gate failure.')
        sys.exit(1)
    else:
        print('\\nQuality analysis passed!')

asyncio.run(main())
"

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Pre-push quality analysis failed"
    exit 1
fi

echo "Pre-push quality analysis passed"
'''


class PullRequestIntegration:
    """Integration with pull request workflows for automated quality analysis."""
    
    def __init__(self, project_path: str, project_id: str):
        self.project_path = project_path
        self.project_id = project_id
        self.scanner = CodeScanningFramework()
        self.auto_fixer = AutoFixEngine()
        self.issue_tracker = QualityIssueTracker()
        self.gate_evaluator = QualityGateEvaluator()
    
    async def analyze_pull_request(self, pr_id: str, base_branch: str, 
                                 head_branch: str, quality_gate: str = "standard") -> PullRequestAnalysis:
        """
        Analyze a pull request for quality issues and improvements.
        
        Args:
            pr_id: Pull request identifier
            base_branch: Base branch name
            head_branch: Head branch name
            quality_gate: Quality gate to evaluate against
            
        Returns:
            PullRequestAnalysis with comprehensive results
        """
        analysis_start = datetime.now(timezone.utc)
        
        try:
            # Get changed files between branches
            changed_files = self._get_changed_files_between_branches(base_branch, head_branch)
            
            # Scan changed files
            config = ScanConfiguration(
                project_id=self.project_id,
                project_path=self.project_path,
                file_patterns=changed_files
            )
            
            scan_result = await self.scanner.scan_project(config)
            
            # Apply auto-fixes
            auto_fixes_applied = 0
            if scan_result.total_issues > 0:
                fix_result = await self._apply_auto_fixes_for_pr(scan_result)
                if fix_result:
                    auto_fixes_applied = fix_result.fixes_applied
            
            # Evaluate quality gate
            gate_result, gate_reasons = self.gate_evaluator.evaluate_gate(
                quality_gate, scan_result
            )
            
            # Determine overall status
            overall_status = self._determine_pr_status(scan_result, gate_result)
            
            # Calculate quality metrics changes
            quality_score_change = self._calculate_quality_score_change(scan_result)
            
            # Generate recommendations
            recommendations = self._generate_pr_recommendations(scan_result, gate_result)
            
            # Determine if manual review is required
            manual_review_required = self._requires_manual_review(scan_result, gate_result)
            
            return PullRequestAnalysis(
                pr_id=pr_id,
                project_id=self.project_id,
                base_branch=base_branch,
                head_branch=head_branch,
                changed_files=changed_files,
                analysis_timestamp=analysis_start,
                overall_status=overall_status,
                quality_gate_result=gate_result,
                new_issues=[issue for result in scan_result.analysis_results for issue in result.issues],
                fixed_issues=[],  # Would need baseline comparison
                quality_score_change=quality_score_change,
                coverage_change=0.0,  # Would need coverage comparison
                complexity_change=0.0,  # Would need complexity comparison
                recommendations=recommendations,
                auto_fixes_applied=auto_fixes_applied,
                manual_review_required=manual_review_required
            )
            
        except Exception as e:
            # Return error analysis
            return PullRequestAnalysis(
                pr_id=pr_id,
                project_id=self.project_id,
                base_branch=base_branch,
                head_branch=head_branch,
                changed_files=[],
                analysis_timestamp=analysis_start,
                overall_status=ReviewStatus.FAILED,
                quality_gate_result=QualityGateResult.FAIL,
                new_issues=[],
                fixed_issues=[],
                quality_score_change=0.0,
                coverage_change=0.0,
                complexity_change=0.0,
                recommendations=[f"Analysis failed: {str(e)}"],
                auto_fixes_applied=0,
                manual_review_required=True
            )
    
    def _get_changed_files_between_branches(self, base_branch: str, head_branch: str) -> List[str]:
        """Get files changed between two branches."""
        try:
            result = subprocess.run([
                "git", "diff", "--name-only", f"{base_branch}...{head_branch}"
            ], cwd=self.project_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split('\n') if f.strip()]
            
            return []
            
        except Exception as e:
            print(f"Failed to get changed files: {e}")
            return []
    
    async def _apply_auto_fixes_for_pr(self, scan_result: ScanResult) -> Optional[FixApplicationResult]:
        """Apply auto-fixes for pull request analysis."""
        # Similar to pre-commit auto-fixes but may be more conservative
        try:
            fixable_issues = []
            for result in scan_result.analysis_results:
                for issue in result.issues:
                    if issue.auto_fixable and issue.severity not in [Severity.CRITICAL]:
                        fixable_issues.append(issue)
            
            if fixable_issues:
                return await self.auto_fixer.apply_fixes_to_issues(fixable_issues)
            
            return None
            
        except Exception as e:
            print(f"Error applying PR auto-fixes: {e}")
            return None
    
    def _determine_pr_status(self, scan_result: ScanResult, gate_result: QualityGateResult) -> ReviewStatus:
        """Determine pull request overall status."""
        if gate_result == QualityGateResult.PASS:
            return ReviewStatus.PASSED
        elif gate_result == QualityGateResult.CONDITIONAL_PASS:
            return ReviewStatus.WARNING
        else:
            critical_issues = scan_result.issues_by_severity.get('critical', 0)
            security_issues = scan_result.issues_by_type.get('security', 0)
            
            if critical_issues > 0 or security_issues > 0:
                return ReviewStatus.BLOCKED
            else:
                return ReviewStatus.FAILED
    
    def _calculate_quality_score_change(self, scan_result: ScanResult) -> float:
        """Calculate quality score change (simplified)."""
        if not scan_result.metrics:
            return 0.0
        
        # Simple calculation based on issues found
        # In a real implementation, this would compare against baseline
        issue_penalty = scan_result.total_issues * -0.5
        return max(-10.0, min(10.0, issue_penalty))
    
    def _generate_pr_recommendations(self, scan_result: ScanResult, 
                                   gate_result: QualityGateResult) -> List[str]:
        """Generate recommendations for pull request."""
        recommendations = []
        
        if gate_result == QualityGateResult.FAIL:
            recommendations.append("Address quality gate failures before merging")
        
        # Issue-specific recommendations
        critical_count = scan_result.issues_by_severity.get('critical', 0)
        if critical_count > 0:
            recommendations.append(f"Fix {critical_count} critical issues")
        
        security_count = scan_result.issues_by_type.get('security', 0)
        if security_count > 0:
            recommendations.append(f"Address {security_count} security issues")
        
        # Auto-fix recommendations
        auto_fixable = sum(1 for result in scan_result.analysis_results 
                          for issue in result.issues if issue.auto_fixable)
        if auto_fixable > 0:
            recommendations.append(f"Apply auto-fixes for {auto_fixable} issues")
        
        if not recommendations:
            recommendations.append("Code quality looks good!")
        
        return recommendations
    
    def _requires_manual_review(self, scan_result: ScanResult, 
                              gate_result: QualityGateResult) -> bool:
        """Determine if manual review is required."""
        # Require manual review for:
        # - Critical or security issues
        # - Quality gate failures
        # - Complex changes
        
        critical_issues = scan_result.issues_by_severity.get('critical', 0)
        security_issues = scan_result.issues_by_type.get('security', 0)
        
        return (
            critical_issues > 0 or
            security_issues > 0 or
            gate_result == QualityGateResult.FAIL or
            scan_result.total_issues > 20  # Arbitrary threshold for complex changes
        )
    
    async def create_pr_comment(self, analysis: PullRequestAnalysis) -> str:
        """Create a formatted comment for the pull request."""
        comment_parts = []
        
        # Header
        status_emoji = {
            ReviewStatus.PASSED: "✅",
            ReviewStatus.WARNING: "⚠️",
            ReviewStatus.FAILED: "❌",
            ReviewStatus.BLOCKED: "🚫"
        }
        
        emoji = status_emoji.get(analysis.overall_status, "❓")
        comment_parts.append(f"## {emoji} Code Quality Analysis")
        
        # Summary
        comment_parts.append(f"**Status:** {analysis.overall_status.value.title()}")
        comment_parts.append(f"**Quality Gate:** {analysis.quality_gate_result.value}")
        comment_parts.append(f"**Issues Found:** {len(analysis.new_issues)}")
        comment_parts.append(f"**Auto-fixes Applied:** {analysis.auto_fixes_applied}")
        
        # Issues breakdown
        if analysis.new_issues:
            comment_parts.append("\n### Issues Found")
            
            # Group by severity
            issues_by_severity = {}
            for issue in analysis.new_issues:
                severity = issue.severity.value
                if severity not in issues_by_severity:
                    issues_by_severity[severity] = []
                issues_by_severity[severity].append(issue)
            
            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                if severity in issues_by_severity:
                    issues = issues_by_severity[severity]
                    comment_parts.append(f"- **{severity.title()}:** {len(issues)} issues")
        
        # Recommendations
        if analysis.recommendations:
            comment_parts.append("\n### Recommendations")
            for rec in analysis.recommendations:
                comment_parts.append(f"- {rec}")
        
        # Manual review notice
        if analysis.manual_review_required:
            comment_parts.append("\n⚠️ **Manual review required** due to critical issues or quality gate failures.")
        
        return "\n".join(comment_parts)


class CodeReviewWorkflowAutomation:
    """Main class for automated code review workflow integration."""
    
    def __init__(self, project_path: str, project_id: str):
        self.project_path = project_path
        self.project_id = project_id
        self.pre_commit_manager = PreCommitHookManager(project_path, project_id)
        self.pr_integration = PullRequestIntegration(project_path, project_id)
    
    async def setup_automated_workflow(self, quality_gate: str = "standard") -> bool:
        """Set up complete automated code review workflow."""
        try:
            # Install Git hooks
            hooks_installed = self.pre_commit_manager.install_hooks()
            
            if hooks_installed:
                print(f"Automated code review workflow set up successfully")
                print(f"Quality gate: {quality_gate}")
                print("Pre-commit and pre-push hooks installed")
                return True
            else:
                print("Failed to install Git hooks")
                return False
                
        except Exception as e:
            print(f"Failed to set up automated workflow: {e}")
            return False
    
    async def run_full_quality_check(self, quality_gate: str = "standard") -> PreCommitResult:
        """Run a full quality check (can be used for CI/CD)."""
        return await self.pre_commit_manager.run_pre_commit_checks(quality_gate)
    
    async def analyze_pr_for_merge(self, pr_id: str, base_branch: str, 
                                 head_branch: str, quality_gate: str = "standard") -> PullRequestAnalysis:
        """Analyze pull request for merge decision."""
        return await self.pr_integration.analyze_pull_request(
            pr_id, base_branch, head_branch, quality_gate
        )
    
    def remove_automated_workflow(self) -> bool:
        """Remove automated code review workflow."""
        return self.pre_commit_manager.git_manager.uninstall_hooks()