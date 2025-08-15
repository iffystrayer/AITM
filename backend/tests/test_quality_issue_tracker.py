"""
Integration tests for QualityIssueTracker.
Tests issue lifecycle management, priority-based routing, and resolution tracking.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.services.quality_issue_tracker import (
    QualityIssueTracker, IssuePriority, IssueCategory
)
from app.models.quality import (
    QualityIssue, QualityIssueCreate, QualityIssueUpdate,
    IssueType, Severity, IssueStatus
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create tables
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create quality_issues table
    cursor.execute("""
        CREATE TABLE quality_issues (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            line_number INTEGER,
            column_number INTEGER,
            issue_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            suggested_fix TEXT,
            auto_fixable BOOLEAN DEFAULT FALSE,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolved_by TEXT,
            resolution_method TEXT
        )
    """)
    
    # Create auto_fix_results table
    cursor.execute("""
        CREATE TABLE auto_fix_results (
            id TEXT PRIMARY KEY,
            issue_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            fix_type TEXT NOT NULL,
            original_content TEXT,
            fixed_content TEXT,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_by TEXT,
            rollback_id TEXT,
            is_rolled_back BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Create quality_standards table
    cursor.execute("""
        CREATE TABLE quality_standards (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            standard_name TEXT NOT NULL,
            standard_type TEXT NOT NULL,
            configuration TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield path
    
    # Cleanup
    os.unlink(path)


@pytest.fixture
def tracker(temp_db):
    """Create QualityIssueTracker instance with temp database."""
    return QualityIssueTracker(db_path=temp_db)


@pytest.fixture
def sample_issue_data():
    """Sample issue creation data."""
    return QualityIssueCreate(
        project_id="test-project-1",
        file_path="src/main.py",
        line_number=42,
        column_number=10,
        issue_type=IssueType.STYLE,
        severity=Severity.MEDIUM,
        category="formatting",
        description="Line too long (90 > 88 characters)",
        suggested_fix="Break line at appropriate point",
        auto_fixable=True
    )


class TestQualityIssueTracker:
    """Test suite for QualityIssueTracker."""
    
    @pytest.mark.asyncio
    async def test_create_issue_basic(self, tracker, sample_issue_data):
        """Test basic issue creation."""
        issue = await tracker.create_issue(sample_issue_data)
        
        assert issue.id is not None
        assert issue.project_id == sample_issue_data.project_id
        assert issue.file_path == sample_issue_data.file_path
        assert issue.issue_type == sample_issue_data.issue_type
        assert issue.severity == sample_issue_data.severity
        assert issue.status == IssueStatus.OPEN
        assert issue.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_issue_with_routing(self, tracker):
        """Test issue creation with automatic routing."""
        # Create critical security issue
        security_issue_data = QualityIssueCreate(
            project_id="test-project-1",
            file_path="src/auth.py",
            line_number=15,
            issue_type=IssueType.SECURITY,
            severity=Severity.CRITICAL,
            category="vulnerability",
            description="SQL injection vulnerability detected",
            auto_fixable=False
        )
        
        with patch.object(tracker, '_check_escalation') as mock_escalation:
            issue = await tracker.create_issue(security_issue_data)
            
            # Should trigger escalation for critical security issue
            mock_escalation.assert_called_once()
            
            # Check that category includes routing information
            assert "vulnerability" in issue.category
    
    @pytest.mark.asyncio
    async def test_update_issue_status(self, tracker, sample_issue_data):
        """Test updating issue status."""
        # Create issue
        issue = await tracker.create_issue(sample_issue_data)
        
        # Update to in progress
        updates = QualityIssueUpdate(
            status=IssueStatus.IN_PROGRESS,
            resolved_by="developer1"
        )
        
        updated_issue = await tracker.update_issue(issue.id, updates)
        
        assert updated_issue is not None
        assert updated_issue.status == IssueStatus.IN_PROGRESS
        assert updated_issue.resolved_by == "developer1"
        assert updated_issue.resolved_at is None  # Not resolved yet
    
    @pytest.mark.asyncio
    async def test_resolve_issue(self, tracker, sample_issue_data):
        """Test issue resolution."""
        # Create issue
        issue = await tracker.create_issue(sample_issue_data)
        
        # Resolve issue
        success = await tracker.resolve_issue(
            issue.id, 
            resolved_by="developer1",
            resolution_method="auto_fix"
        )
        
        assert success is True
        
        # Verify resolution
        resolved_issue = await tracker.get_issue_by_id(issue.id)
        assert resolved_issue.status == IssueStatus.RESOLVED
        assert resolved_issue.resolved_by == "developer1"
        assert resolved_issue.resolution_method == "auto_fix"
        assert resolved_issue.resolved_at is not None
    
    @pytest.mark.asyncio
    async def test_get_issues_with_filters(self, tracker):
        """Test getting issues with various filters."""
        # Create multiple issues
        issues_data = [
            QualityIssueCreate(
                project_id="project1",
                file_path="file1.py",
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting",
                description="Style issue 1"
            ),
            QualityIssueCreate(
                project_id="project1",
                file_path="file2.py",
                issue_type=IssueType.SECURITY,
                severity=Severity.HIGH,
                category="vulnerability",
                description="Security issue 1"
            ),
            QualityIssueCreate(
                project_id="project2",
                file_path="file3.py",
                issue_type=IssueType.PERFORMANCE,
                severity=Severity.MEDIUM,
                category="optimization",
                description="Performance issue 1"
            )
        ]
        
        created_issues = []
        for issue_data in issues_data:
            issue = await tracker.create_issue(issue_data)
            created_issues.append(issue)
        
        # Test filtering by project
        project1_issues = await tracker.get_issues(project_id="project1")
        assert len(project1_issues) == 2
        
        # Test filtering by severity
        high_severity_issues = await tracker.get_issues(severity=Severity.HIGH)
        assert len(high_severity_issues) == 1
        assert high_severity_issues[0].issue_type == IssueType.SECURITY
        
        # Test filtering by issue type
        style_issues = await tracker.get_issues(issue_type=IssueType.STYLE)
        assert len(style_issues) == 1
        assert style_issues[0].severity == Severity.LOW
        
        # Test filtering by status
        open_issues = await tracker.get_issues(status=IssueStatus.OPEN)
        assert len(open_issues) == 3  # All created issues are open
    
    @pytest.mark.asyncio
    async def test_get_resolution_metrics(self, tracker):
        """Test resolution metrics calculation."""
        # Create and resolve some issues
        issues_data = [
            QualityIssueCreate(
                project_id="project1",
                file_path="file1.py",
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting",
                description="Style issue 1",
                auto_fixable=True
            ),
            QualityIssueCreate(
                project_id="project1",
                file_path="file2.py",
                issue_type=IssueType.SECURITY,
                severity=Severity.HIGH,
                category="vulnerability",
                description="Security issue 1",
                auto_fixable=False
            )
        ]
        
        created_issues = []
        for issue_data in issues_data:
            issue = await tracker.create_issue(issue_data)
            created_issues.append(issue)
        
        # Resolve first issue
        await tracker.resolve_issue(created_issues[0].id, "developer1", "auto_fix")
        
        # Get metrics
        metrics = await tracker.get_resolution_metrics(project_id="project1")
        
        assert metrics.total_issues == 2
        assert metrics.resolved_issues == 1
        assert metrics.resolution_rate == 50.0
        assert metrics.issues_by_severity['low'] == 1
        assert metrics.issues_by_severity['high'] == 1
        assert metrics.issues_by_type['style'] == 1
        assert metrics.issues_by_type['security'] == 1
    
    @pytest.mark.asyncio
    async def test_escalate_stale_issues(self, tracker, temp_db):
        """Test escalation of stale issues."""
        # Create an old high-severity issue
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quality_issues 
            (id, project_id, file_path, issue_type, severity, category, 
             description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "old-issue-1",
            "project1",
            "old_file.py",
            "security",
            "high",
            "vulnerability",
            "Old security issue",
            "open",
            old_time.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Test escalation
        stale_issues = await tracker.escalate_stale_issues(hours_threshold=24)
        
        assert len(stale_issues) == 1
        assert stale_issues[0].id == "old-issue-1"
        assert stale_issues[0].severity == Severity.HIGH
    
    @pytest.mark.asyncio
    async def test_bulk_update_issues(self, tracker):
        """Test bulk updating multiple issues."""
        # Create multiple issues
        issues_data = [
            QualityIssueCreate(
                project_id="project1",
                file_path=f"file{i}.py",
                issue_type=IssueType.STYLE,
                severity=Severity.LOW,
                category="formatting",
                description=f"Style issue {i}"
            )
            for i in range(3)
        ]
        
        created_issues = []
        for issue_data in issues_data:
            issue = await tracker.create_issue(issue_data)
            created_issues.append(issue)
        
        # Bulk update to in progress
        issue_ids = [issue.id for issue in created_issues]
        updates = QualityIssueUpdate(
            status=IssueStatus.IN_PROGRESS,
            resolved_by="bulk_processor"
        )
        
        updated_count = await tracker.bulk_update_issues(issue_ids, updates)
        
        assert updated_count == 3
        
        # Verify all issues were updated
        for issue_id in issue_ids:
            updated_issue = await tracker.get_issue_by_id(issue_id)
            assert updated_issue.status == IssueStatus.IN_PROGRESS
            assert updated_issue.resolved_by == "bulk_processor"
    
    @pytest.mark.asyncio
    async def test_delete_issue(self, tracker, sample_issue_data):
        """Test issue deletion."""
        # Create issue
        issue = await tracker.create_issue(sample_issue_data)
        
        # Verify it exists
        found_issue = await tracker.get_issue_by_id(issue.id)
        assert found_issue is not None
        
        # Delete issue
        deleted = await tracker.delete_issue(issue.id)
        assert deleted is True
        
        # Verify it's gone
        found_issue = await tracker.get_issue_by_id(issue.id)
        assert found_issue is None
    
    def test_routing_rules_matching(self, tracker):
        """Test routing rule condition matching."""
        # Create test issue
        issue = QualityIssue(
            project_id="test",
            file_path="test.py",
            issue_type=IssueType.SECURITY,
            severity=Severity.CRITICAL,
            category="test",
            description="Test issue",
            auto_fixable=False
        )
        
        # Test matching conditions
        conditions = {
            "issue_type": "security",
            "severity": "critical"
        }
        
        matches = tracker._matches_conditions(issue, conditions)
        assert matches is True
        
        # Test non-matching conditions
        conditions = {
            "issue_type": "style",
            "severity": "critical"
        }
        
        matches = tracker._matches_conditions(issue, conditions)
        assert matches is False
        
        # Test list conditions
        conditions = {
            "severity": ["high", "critical"]
        }
        
        matches = tracker._matches_conditions(issue, conditions)
        assert matches is True
    
    @pytest.mark.asyncio
    async def test_issue_lifecycle_workflow(self, tracker, sample_issue_data):
        """Test complete issue lifecycle workflow."""
        # 1. Create issue
        issue = await tracker.create_issue(sample_issue_data)
        assert issue.status == IssueStatus.OPEN
        
        # 2. Move to in progress
        updates = QualityIssueUpdate(
            status=IssueStatus.IN_PROGRESS,
            resolved_by="developer1"
        )
        updated_issue = await tracker.update_issue(issue.id, updates)
        assert updated_issue.status == IssueStatus.IN_PROGRESS
        
        # 3. Resolve issue
        success = await tracker.resolve_issue(
            issue.id,
            resolved_by="developer1",
            resolution_method="manual_fix"
        )
        assert success is True
        
        # 4. Verify final state
        final_issue = await tracker.get_issue_by_id(issue.id)
        assert final_issue.status == IssueStatus.RESOLVED
        assert final_issue.resolved_by == "developer1"
        assert final_issue.resolution_method == "manual_fix"
        assert final_issue.resolved_at is not None
    
    @pytest.mark.asyncio
    async def test_priority_based_routing(self, tracker):
        """Test priority-based issue routing."""
        # Test critical security issue (should be URGENT)
        critical_security = QualityIssueCreate(
            project_id="test",
            file_path="auth.py",
            issue_type=IssueType.SECURITY,
            severity=Severity.CRITICAL,
            category="vulnerability",
            description="Critical security vulnerability"
        )
        
        issue = await tracker.create_issue(critical_security)
        # Category should contain priority information
        assert "vulnerability" in issue.category
        
        # Test low severity style issue (should be LOW priority)
        low_style = QualityIssueCreate(
            project_id="test",
            file_path="utils.py",
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="formatting",
            description="Minor formatting issue",
            auto_fixable=True
        )
        
        issue2 = await tracker.create_issue(low_style)
        assert "formatting" in issue2.category
    
    @pytest.mark.asyncio
    async def test_error_handling(self, tracker):
        """Test error handling in various scenarios."""
        # Test updating non-existent issue
        updates = QualityIssueUpdate(status=IssueStatus.RESOLVED)
        result = await tracker.update_issue("non-existent-id", updates)
        assert result is None
        
        # Test resolving non-existent issue
        success = await tracker.resolve_issue("non-existent-id", "developer1")
        assert success is False
        
        # Test getting non-existent issue
        issue = await tracker.get_issue_by_id("non-existent-id")
        assert issue is None
        
        # Test deleting non-existent issue
        deleted = await tracker.delete_issue("non-existent-id")
        assert deleted is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])