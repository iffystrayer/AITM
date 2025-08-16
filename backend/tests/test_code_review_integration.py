"""
Integration tests for automated code review workflow.
Tests pre-commit hooks, pull request integration, and quality gate enforcement.
"""

import os
import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from app.services.code_analysis.code_review_integration import (
    CodeReviewWorkflowAutomation,
    PreCommitHookManager,
    PullRequestIntegration,
    QualityGateEvaluator,
    GitHookManager,
    QualityGate,
    QualityGateResult,
    ReviewStatus,
    PreCommitResult
)
from app.services.code_analysis.scanning_framework import ScanResult, ScanConfiguration
from app.models.quality import QualityIssue, Severity, IssueType, IssueStatus


class TestGitHookManager:
    """Test Git hook management functionality."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary Git repository for testing."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
        
        yield str(repo_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_install_pre_commit_hook(self, temp_repo):
        """Test installing pre-commit hook."""
        manager = GitHookManager(temp_repo)
        
        hook_script = """#!/bin/bash
echo "Running quality checks..."
exit 0
"""
        
        success = manager.install_pre_commit_hook(hook_script)
        assert success
        
        # Check hook file exists and is executable
        hook_path = Path(temp_repo) / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()
        assert os.access(hook_path, os.X_OK)
        
        # Check content
        with open(hook_path, 'r') as f:
            content = f.read()
        assert "Running quality checks..." in content
    
    def test_install_pre_push_hook(self, temp_repo):
        """Test installing pre-push hook."""
        manager = GitHookManager(temp_repo)
        
        hook_script = """#!/bin/bash
echo "Running pre-push checks..."
exit 0
"""
        
        success = manager.install_pre_push_hook(hook_script)
        assert success
        
        hook_path = Path(temp_repo) / ".git" / "hooks" / "pre-push"
        assert hook_path.exists()
        assert os.access(hook_path, os.X_OK)
    
    def test_uninstall_hooks(self, temp_repo):
        """Test uninstalling hooks."""
        manager = GitHookManager(temp_repo)
        
        # Install hooks first
        manager.install_pre_commit_hook("#!/bin/bash\necho test")
        manager.install_pre_push_hook("#!/bin/bash\necho test")
        
        # Verify they exist
        pre_commit_path = Path(temp_repo) / ".git" / "hooks" / "pre-commit"
        pre_push_path = Path(temp_repo) / ".git" / "hooks" / "pre-push"
        assert pre_commit_path.exists()
        assert pre_push_path.exists()
        
        # Uninstall
        success = manager.uninstall_hooks()
        assert success
        
        # Verify they're removed
        assert not pre_commit_path.exists()
        assert not pre_push_path.exists()
    
    def test_get_changed_files(self, temp_repo):
        """Test getting changed files."""
        manager = GitHookManager(temp_repo)
        
        # Create and stage a file
        test_file = Path(temp_repo) / "test.py"
        test_file.write_text("print('hello')")
        
        subprocess.run(["git", "add", "test.py"], cwd=temp_repo, check=True)
        
        changed_files = manager.get_changed_files()
        assert "test.py" in changed_files


class TestQualityGateEvaluator:
    """Test quality gate evaluation logic."""
    
    @pytest.fixture
    def evaluator(self):
        return QualityGateEvaluator()
    
    @pytest.fixture
    def sample_scan_result(self):
        """Create a sample scan result for testing."""
        scan_result = Mock(spec=ScanResult)
        scan_result.issues_by_severity = {
            'critical': 1,
            'high': 3,
            'medium': 10,
            'low': 5
        }
        scan_result.issues_by_type = {
            'security': 1,
            'style': 8,
            'complexity': 5
        }
        scan_result.total_issues = 19
        
        # Mock analysis_results for auto-fix bypass logic
        mock_issue = Mock()
        mock_issue.auto_fixable = True
        mock_analysis_result = Mock()
        mock_analysis_result.issues = [mock_issue] * 5  # 5 auto-fixable issues
        scan_result.analysis_results = [mock_analysis_result]
        
        # Mock metrics
        metrics = Mock()
        metrics.cyclomatic_complexity = 8.5
        metrics.technical_debt_ratio = 0.08
        scan_result.metrics = metrics
        
        return scan_result
    
    def test_strict_gate_evaluation(self, evaluator, sample_scan_result):
        """Test strict quality gate evaluation."""
        result, reasons = evaluator.evaluate_gate("strict", sample_scan_result)
        
        # Should fail due to critical and high issues
        assert result == QualityGateResult.FAIL
        assert any("Critical issues" in reason for reason in reasons)
        assert any("High severity issues" in reason for reason in reasons)
        assert any("Security issues" in reason for reason in reasons)
    
    def test_standard_gate_evaluation(self, evaluator, sample_scan_result):
        """Test standard quality gate evaluation."""
        result, reasons = evaluator.evaluate_gate("standard", sample_scan_result)
        
        # Should get conditional pass due to auto-fixable issues
        assert result == QualityGateResult.CONDITIONAL_PASS
        assert any("Quality gate can pass with auto-fixes applied" in reason for reason in reasons)
    
    def test_lenient_gate_evaluation(self, evaluator, sample_scan_result):
        """Test lenient quality gate evaluation."""
        result, reasons = evaluator.evaluate_gate("lenient", sample_scan_result)
        
        # Should get conditional pass due to auto-fixable issues
        assert result == QualityGateResult.CONDITIONAL_PASS
        assert any("Quality gate can pass with auto-fixes applied" in reason for reason in reasons)
    
    def test_passing_gate_evaluation(self, evaluator):
        """Test quality gate that should pass."""
        # Create clean scan result
        clean_scan_result = Mock(spec=ScanResult)
        clean_scan_result.issues_by_severity = {
            'medium': 2,
            'low': 3
        }
        clean_scan_result.issues_by_type = {
            'style': 5
        }
        clean_scan_result.total_issues = 5
        
        # Mock analysis_results
        clean_scan_result.analysis_results = []
        
        metrics = Mock()
        metrics.cyclomatic_complexity = 6.0
        metrics.technical_debt_ratio = 0.03
        clean_scan_result.metrics = metrics
        
        result, reasons = evaluator.evaluate_gate("standard", clean_scan_result)
        
        assert result == QualityGateResult.PASS
        assert "All quality gate criteria met" in reasons[0]
    
    def test_coverage_gate_evaluation(self, evaluator, sample_scan_result):
        """Test quality gate with coverage requirements."""
        coverage_data = {'overall_coverage': 75.0}
        
        result, reasons = evaluator.evaluate_gate("standard", sample_scan_result, coverage_data)
        
        # Should get conditional pass due to auto-fixable issues, but coverage failure should be noted
        assert result == QualityGateResult.CONDITIONAL_PASS
        assert any("Test coverage" in reason for reason in reasons)
    
    def test_unknown_gate(self, evaluator, sample_scan_result):
        """Test evaluation with unknown quality gate."""
        result, reasons = evaluator.evaluate_gate("unknown", sample_scan_result)
        
        assert result == QualityGateResult.FAIL
        assert "Unknown quality gate" in reasons[0]


class TestPreCommitHookManager:
    """Test pre-commit hook management and execution."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_path, check=True)
        
        # Create some Python files
        (project_path / "good_file.py").write_text("""
def hello_world():
    print("Hello, World!")
    return True
""")
        
        (project_path / "bad_file.py").write_text("""
def   bad_function(  ):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20
    if x>10:
        print( "This is a very long line that exceeds the recommended line length and should be flagged by quality checks" )
    return x
""")
        
        yield str(project_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_manager(self, temp_project):
        """Create pre-commit manager with mocked dependencies."""
        manager = PreCommitHookManager(temp_project, "test-project")
        
        # Mock the scanner
        manager.scanner = Mock()
        manager.auto_fixer = Mock()
        manager.issue_tracker = Mock()
        manager.gate_evaluator = Mock()
        
        return manager
    
    @pytest.mark.asyncio
    async def test_run_pre_commit_checks_no_files(self, mock_manager):
        """Test pre-commit checks with no changed files."""
        # Mock no changed files
        mock_manager.git_manager.get_changed_files = Mock(return_value=[])
        
        result = await mock_manager.run_pre_commit_checks()
        
        assert result.status == ReviewStatus.PASSED
        assert result.issues_found == 0
        assert "No files to check" in result.messages
    
    @pytest.mark.asyncio
    async def test_run_pre_commit_checks_with_issues(self, mock_manager):
        """Test pre-commit checks with quality issues found."""
        # Mock changed files
        mock_manager.git_manager.get_changed_files = Mock(return_value=["test.py"])
        
        # Mock scan result with issues
        mock_scan_result = Mock(spec=ScanResult)
        mock_scan_result.total_issues = 5
        mock_scan_result.issues_by_severity = {'medium': 3, 'low': 2}
        mock_scan_result.issues_by_type = {'style': 5}
        mock_scan_result.analysis_results = []
        
        mock_manager.scanner.scan_project = AsyncMock(return_value=mock_scan_result)
        
        # Mock quality gate evaluation
        mock_manager.gate_evaluator.evaluate_gate = Mock(
            return_value=(QualityGateResult.PASS, ["All criteria met"])
        )
        
        result = await mock_manager.run_pre_commit_checks()
        
        assert result.status == ReviewStatus.PASSED
        assert result.issues_found == 5
        assert result.quality_gate_result == QualityGateResult.PASS
    
    @pytest.mark.asyncio
    async def test_run_pre_commit_checks_with_blocking_issues(self, mock_manager):
        """Test pre-commit checks with blocking issues."""
        mock_manager.git_manager.get_changed_files = Mock(return_value=["test.py"])
        
        # Create mock issues
        critical_issue = Mock(spec=QualityIssue)
        critical_issue.severity = Severity.CRITICAL
        critical_issue.auto_fixable = False
        
        mock_scan_result = Mock(spec=ScanResult)
        mock_scan_result.total_issues = 1
        mock_scan_result.issues_by_severity = {'critical': 1}
        mock_scan_result.issues_by_type = {'security': 1}
        
        # Mock analysis results
        mock_analysis_result = Mock()
        mock_analysis_result.issues = [critical_issue]
        mock_scan_result.analysis_results = [mock_analysis_result]
        
        mock_manager.scanner.scan_project = AsyncMock(return_value=mock_scan_result)
        
        # Mock quality gate failure
        mock_manager.gate_evaluator.evaluate_gate = Mock(
            return_value=(QualityGateResult.FAIL, ["Critical issues found"])
        )
        
        result = await mock_manager.run_pre_commit_checks()
        
        assert result.status == ReviewStatus.BLOCKED
        assert result.issues_found == 1
        assert result.quality_gate_result == QualityGateResult.FAIL
        assert len(result.blocking_issues) == 1
    
    def test_should_scan_file(self, mock_manager):
        """Test file scanning filter logic."""
        # Should scan Python files
        assert mock_manager._should_scan_file("test.py")
        assert mock_manager._should_scan_file("src/module.py")
        
        # Should not scan excluded files
        assert not mock_manager._should_scan_file("__pycache__/test.pyc")
        assert not mock_manager._should_scan_file("node_modules/package.js")
        assert not mock_manager._should_scan_file("image.jpg")
        assert not mock_manager._should_scan_file(".git/config")
    
    def test_install_hooks(self, mock_manager):
        """Test hook installation."""
        # Mock successful installation
        mock_manager.git_manager.install_pre_commit_hook = Mock(return_value=True)
        mock_manager.git_manager.install_pre_push_hook = Mock(return_value=True)
        
        success = mock_manager.install_hooks()
        
        assert success
        mock_manager.git_manager.install_pre_commit_hook.assert_called_once()
        mock_manager.git_manager.install_pre_push_hook.assert_called_once()
    
    def test_generate_pre_commit_script(self, mock_manager):
        """Test pre-commit script generation."""
        script = mock_manager._generate_pre_commit_script()
        
        assert "#!/bin/bash" in script
        assert "Running quality checks" in script
        assert mock_manager.project_path in script
        assert mock_manager.project_id in script
    
    def test_generate_pre_push_script(self, mock_manager):
        """Test pre-push script generation."""
        script = mock_manager._generate_pre_push_script()
        
        assert "#!/bin/bash" in script
        assert "comprehensive quality analysis" in script
        assert "strict" in script  # Should use strict quality gate


class TestPullRequestIntegration:
    """Test pull request integration functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project with Git history."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_path, check=True)
        
        # Create initial commit
        (project_path / "README.md").write_text("# Test Project")
        subprocess.run(["git", "add", "README.md"], cwd=project_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_path, check=True)
        
        # Create feature branch
        subprocess.run(["git", "checkout", "-b", "feature-branch"], cwd=project_path, check=True)
        (project_path / "feature.py").write_text("def new_feature(): pass")
        subprocess.run(["git", "add", "feature.py"], cwd=project_path, check=True)
        subprocess.run(["git", "commit", "-m", "Add feature"], cwd=project_path, check=True)
        
        yield str(project_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_pr_integration(self, temp_project):
        """Create PR integration with mocked dependencies."""
        integration = PullRequestIntegration(temp_project, "test-project")
        
        integration.scanner = Mock()
        integration.auto_fixer = Mock()
        integration.issue_tracker = Mock()
        integration.gate_evaluator = Mock()
        
        return integration
    
    @pytest.mark.asyncio
    async def test_analyze_pull_request_success(self, mock_pr_integration):
        """Test successful pull request analysis."""
        # Mock changed files
        mock_pr_integration._get_changed_files_between_branches = Mock(
            return_value=["feature.py"]
        )
        
        # Mock scan result
        mock_scan_result = Mock(spec=ScanResult)
        mock_scan_result.total_issues = 2
        mock_scan_result.issues_by_severity = {'medium': 2}
        mock_scan_result.issues_by_type = {'style': 2}
        
        # Mock issues
        issue1 = Mock(spec=QualityIssue)
        issue1.severity = Severity.MEDIUM
        issue1.auto_fixable = True
        
        issue2 = Mock(spec=QualityIssue)
        issue2.severity = Severity.MEDIUM
        issue2.auto_fixable = False
        
        mock_analysis_result = Mock()
        mock_analysis_result.issues = [issue1, issue2]
        mock_scan_result.analysis_results = [mock_analysis_result]
        
        mock_pr_integration.scanner.scan_project = AsyncMock(return_value=mock_scan_result)
        
        # Mock quality gate
        mock_pr_integration.gate_evaluator.evaluate_gate = Mock(
            return_value=(QualityGateResult.PASS, ["All criteria met"])
        )
        
        # Mock auto-fixes
        mock_fix_result = Mock()
        mock_fix_result.fixes_applied = 1
        mock_pr_integration._apply_auto_fixes_for_pr = AsyncMock(return_value=mock_fix_result)
        
        analysis = await mock_pr_integration.analyze_pull_request(
            "PR-123", "main", "feature-branch"
        )
        
        assert analysis.pr_id == "PR-123"
        assert analysis.base_branch == "main"
        assert analysis.head_branch == "feature-branch"
        assert analysis.overall_status == ReviewStatus.PASSED
        assert analysis.quality_gate_result == QualityGateResult.PASS
        assert len(analysis.new_issues) == 2
        assert analysis.auto_fixes_applied == 1
        assert not analysis.manual_review_required
    
    @pytest.mark.asyncio
    async def test_analyze_pull_request_with_blocking_issues(self, mock_pr_integration):
        """Test PR analysis with blocking issues."""
        mock_pr_integration._get_changed_files_between_branches = Mock(
            return_value=["security_issue.py"]
        )
        
        # Mock scan result with critical security issue
        critical_issue = Mock(spec=QualityIssue)
        critical_issue.severity = Severity.CRITICAL
        critical_issue.issue_type = IssueType.SECURITY
        critical_issue.auto_fixable = False
        
        mock_scan_result = Mock(spec=ScanResult)
        mock_scan_result.total_issues = 1
        mock_scan_result.issues_by_severity = {'critical': 1}
        mock_scan_result.issues_by_type = {'security': 1}
        
        mock_analysis_result = Mock()
        mock_analysis_result.issues = [critical_issue]
        mock_scan_result.analysis_results = [mock_analysis_result]
        
        mock_pr_integration.scanner.scan_project = AsyncMock(return_value=mock_scan_result)
        
        # Mock quality gate failure
        mock_pr_integration.gate_evaluator.evaluate_gate = Mock(
            return_value=(QualityGateResult.FAIL, ["Critical security issues found"])
        )
        
        analysis = await mock_pr_integration.analyze_pull_request(
            "PR-456", "main", "security-fix"
        )
        
        assert analysis.overall_status == ReviewStatus.BLOCKED
        assert analysis.quality_gate_result == QualityGateResult.FAIL
        assert analysis.manual_review_required
        assert any("security" in rec.lower() for rec in analysis.recommendations)
    
    def test_get_changed_files_between_branches(self, mock_pr_integration, temp_project):
        """Test getting changed files between branches."""
        # Switch back to main branch for comparison
        subprocess.run(["git", "checkout", "main"], cwd=temp_project, check=True)
        
        changed_files = mock_pr_integration._get_changed_files_between_branches(
            "main", "feature-branch"
        )
        
        assert "feature.py" in changed_files
    
    def test_requires_manual_review_logic(self, mock_pr_integration):
        """Test manual review requirement logic."""
        # Mock scan result with critical issues
        critical_scan = Mock(spec=ScanResult)
        critical_scan.issues_by_severity = {'critical': 1}
        critical_scan.issues_by_type = {'security': 0}
        critical_scan.total_issues = 1
        
        assert mock_pr_integration._requires_manual_review(
            critical_scan, QualityGateResult.PASS
        )
        
        # Mock scan result with security issues
        security_scan = Mock(spec=ScanResult)
        security_scan.issues_by_severity = {'medium': 1}
        security_scan.issues_by_type = {'security': 1}
        security_scan.total_issues = 1
        
        assert mock_pr_integration._requires_manual_review(
            security_scan, QualityGateResult.PASS
        )
        
        # Mock scan result with many issues
        complex_scan = Mock(spec=ScanResult)
        complex_scan.issues_by_severity = {'low': 25}
        complex_scan.issues_by_type = {'style': 25}
        complex_scan.total_issues = 25
        
        assert mock_pr_integration._requires_manual_review(
            complex_scan, QualityGateResult.PASS
        )
        
        # Mock clean scan result
        clean_scan = Mock(spec=ScanResult)
        clean_scan.issues_by_severity = {'low': 2}
        clean_scan.issues_by_type = {'style': 2}
        clean_scan.total_issues = 2
        
        assert not mock_pr_integration._requires_manual_review(
            clean_scan, QualityGateResult.PASS
        )
    
    @pytest.mark.asyncio
    async def test_create_pr_comment(self, mock_pr_integration):
        """Test PR comment generation."""
        # Create mock analysis
        mock_issue = Mock(spec=QualityIssue)
        mock_issue.severity = Severity.HIGH
        
        analysis = Mock()
        analysis.overall_status = ReviewStatus.WARNING
        analysis.quality_gate_result = QualityGateResult.CONDITIONAL_PASS
        analysis.new_issues = [mock_issue]
        analysis.auto_fixes_applied = 2
        analysis.recommendations = ["Fix high severity issues", "Apply auto-fixes"]
        analysis.manual_review_required = False
        
        comment = await mock_pr_integration.create_pr_comment(analysis)
        
        assert "⚠️ Code Quality Analysis" in comment
        assert "**Status:** Warning" in comment
        assert "**Quality Gate:** conditional_pass" in comment
        assert "**Issues Found:** 1" in comment
        assert "**Auto-fixes Applied:** 2" in comment
        assert "Fix high severity issues" in comment


class TestCodeReviewWorkflowAutomation:
    """Test complete code review workflow automation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_path, check=True)
        
        yield str(project_path)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def workflow_automation(self, temp_project):
        """Create workflow automation instance."""
        return CodeReviewWorkflowAutomation(temp_project, "test-project")
    
    @pytest.mark.asyncio
    async def test_setup_automated_workflow(self, workflow_automation):
        """Test setting up complete automated workflow."""
        # Mock successful hook installation
        workflow_automation.pre_commit_manager.install_hooks = Mock(return_value=True)
        
        success = await workflow_automation.setup_automated_workflow("standard")
        
        assert success
        workflow_automation.pre_commit_manager.install_hooks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_automated_workflow_failure(self, workflow_automation):
        """Test workflow setup failure."""
        # Mock failed hook installation
        workflow_automation.pre_commit_manager.install_hooks = Mock(return_value=False)
        
        success = await workflow_automation.setup_automated_workflow("standard")
        
        assert not success
    
    @pytest.mark.asyncio
    async def test_run_full_quality_check(self, workflow_automation):
        """Test running full quality check."""
        # Mock pre-commit check result
        mock_result = Mock(spec=PreCommitResult)
        mock_result.status = ReviewStatus.PASSED
        
        workflow_automation.pre_commit_manager.run_pre_commit_checks = AsyncMock(
            return_value=mock_result
        )
        
        result = await workflow_automation.run_full_quality_check("strict")
        
        assert result.status == ReviewStatus.PASSED
        workflow_automation.pre_commit_manager.run_pre_commit_checks.assert_called_once_with("strict")
    
    @pytest.mark.asyncio
    async def test_analyze_pr_for_merge(self, workflow_automation):
        """Test PR analysis for merge decision."""
        # Mock PR analysis result
        mock_analysis = Mock()
        mock_analysis.overall_status = ReviewStatus.PASSED
        mock_analysis.quality_gate_result = QualityGateResult.PASS
        
        workflow_automation.pr_integration.analyze_pull_request = AsyncMock(
            return_value=mock_analysis
        )
        
        analysis = await workflow_automation.analyze_pr_for_merge(
            "PR-789", "main", "feature", "standard"
        )
        
        assert analysis.overall_status == ReviewStatus.PASSED
        assert analysis.quality_gate_result == QualityGateResult.PASS
    
    def test_remove_automated_workflow(self, workflow_automation):
        """Test removing automated workflow."""
        # Mock successful uninstallation
        workflow_automation.pre_commit_manager.git_manager.uninstall_hooks = Mock(
            return_value=True
        )
        
        success = workflow_automation.remove_automated_workflow()
        
        assert success
        workflow_automation.pre_commit_manager.git_manager.uninstall_hooks.assert_called_once()


@pytest.mark.integration
class TestCodeReviewIntegrationE2E:
    """End-to-end integration tests for code review workflow."""
    
    @pytest.fixture
    def real_temp_project(self):
        """Create a real temporary project for E2E testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_path, check=True)
        
        # Create Python files with quality issues
        (project_path / "good_code.py").write_text('''
"""A well-formatted Python module."""

def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


def main():
    """Main function."""
    numbers = [1, 2, 3, 4, 5]
    result = calculate_sum(numbers)
    print(f"Sum: {result}")


if __name__ == "__main__":
    main()
''')
        
        (project_path / "bad_code.py").write_text('''
def   bad_function(  ):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20
    if x>10:
        print( "This is a very long line that exceeds the recommended line length and should be flagged by quality checks and needs to be split" )
    return x

def another_bad_function():
    # Missing docstring
    y = 1
    z = 2
    return y + z
''')
        
        yield str(project_path)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_e2e_pre_commit_workflow(self, real_temp_project):
        """Test end-to-end pre-commit workflow."""
        workflow = CodeReviewWorkflowAutomation(real_temp_project, "e2e-test")
        
        # Stage the bad file
        subprocess.run(["git", "add", "bad_code.py"], cwd=real_temp_project, check=True)
        
        # Run pre-commit checks
        result = await workflow.run_full_quality_check("lenient")
        
        # Should find issues but not necessarily block
        assert result.issues_found > 0
        assert result.execution_time > 0
        assert result.scan_result is not None
    
    @pytest.mark.asyncio
    async def test_e2e_quality_gate_enforcement(self, real_temp_project):
        """Test quality gate enforcement in realistic scenario."""
        evaluator = QualityGateEvaluator()
        
        # Create a scan result that should fail strict gate
        scan_result = Mock(spec=ScanResult)
        scan_result.issues_by_severity = {
            'critical': 1,  # Should fail strict gate
            'high': 2,
            'medium': 5
        }
        scan_result.issues_by_type = {
            'security': 1,  # Should always block
            'style': 7
        }
        scan_result.total_issues = 8
        scan_result.metrics = None
        scan_result.analysis_results = []  # Mock empty analysis results
        
        # Test strict gate
        result, reasons = evaluator.evaluate_gate("strict", scan_result)
        assert result == QualityGateResult.FAIL
        assert len(reasons) > 0
        
        # Test lenient gate (should still fail due to security)
        result, reasons = evaluator.evaluate_gate("lenient", scan_result)
        assert result == QualityGateResult.FAIL
        assert any("Security issues" in reason for reason in reasons)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])