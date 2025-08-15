#!/usr/bin/env python3
"""
Demo script for QualityIssueTracker functionality.
Shows issue creation, routing, lifecycle management, and resolution tracking.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.quality_issue_tracker import QualityIssueTracker
from app.models.quality import (
    QualityIssueCreate, QualityIssueUpdate,
    IssueType, Severity, IssueStatus
)


async def demo_quality_issue_tracker():
    """Demonstrate QualityIssueTracker functionality."""
    print("🔍 Quality Issue Tracker Demo")
    print("=" * 50)
    
    # Initialize tracker
    tracker = QualityIssueTracker("aitm.db")
    
    print("\n1. Creating various quality issues...")
    
    # Create different types of issues
    issues_data = [
        QualityIssueCreate(
            project_id="demo-project",
            file_path="src/auth.py",
            line_number=25,
            issue_type=IssueType.SECURITY,
            severity=Severity.CRITICAL,
            category="vulnerability",
            description="SQL injection vulnerability in login function",
            suggested_fix="Use parameterized queries",
            auto_fixable=False
        ),
        QualityIssueCreate(
            project_id="demo-project",
            file_path="src/utils.py",
            line_number=42,
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="formatting",
            description="Line too long (95 > 88 characters)",
            suggested_fix="Break line at appropriate point",
            auto_fixable=True
        ),
        QualityIssueCreate(
            project_id="demo-project",
            file_path="src/api.py",
            line_number=156,
            issue_type=IssueType.PERFORMANCE,
            severity=Severity.HIGH,
            category="optimization",
            description="N+1 query detected in user data retrieval",
            suggested_fix="Use eager loading or batch queries",
            auto_fixable=False
        ),
        QualityIssueCreate(
            project_id="demo-project",
            file_path="src/models.py",
            line_number=78,
            issue_type=IssueType.COMPLEXITY,
            severity=Severity.MEDIUM,
            category="refactoring",
            description="Function complexity too high (15 > 10)",
            suggested_fix="Break function into smaller methods",
            auto_fixable=False
        ),
        QualityIssueCreate(
            project_id="demo-project",
            file_path="tests/test_auth.py",
            line_number=12,
            issue_type=IssueType.TESTING,
            severity=Severity.MEDIUM,
            category="coverage",
            description="Missing test coverage for error handling",
            suggested_fix="Add tests for exception scenarios",
            auto_fixable=False
        )
    ]
    
    created_issues = []
    for i, issue_data in enumerate(issues_data, 1):
        issue = await tracker.create_issue(issue_data)
        created_issues.append(issue)
        print(f"   ✓ Issue {i}: {issue.issue_type.value} - {issue.severity.value} - {issue.description[:50]}...")
    
    print(f"\n   Created {len(created_issues)} issues with automatic priority routing")
    
    print("\n2. Demonstrating issue filtering and querying...")
    
    # Get issues by different filters
    all_issues = await tracker.get_issues(project_id="demo-project")
    print(f"   • Total issues in project: {len(all_issues)}")
    
    critical_issues = await tracker.get_issues(severity=Severity.CRITICAL)
    print(f"   • Critical issues: {len(critical_issues)}")
    
    security_issues = await tracker.get_issues(issue_type=IssueType.SECURITY)
    print(f"   • Security issues: {len(security_issues)}")
    
    auto_fixable = await tracker.get_issues(project_id="demo-project")
    auto_fixable_count = sum(1 for issue in auto_fixable if issue.auto_fixable)
    print(f"   • Auto-fixable issues: {auto_fixable_count}")
    
    print("\n3. Demonstrating issue lifecycle management...")
    
    # Move some issues through their lifecycle
    style_issue = next(issue for issue in created_issues if issue.issue_type == IssueType.STYLE)
    
    print(f"   • Moving style issue to IN_PROGRESS...")
    updates = QualityIssueUpdate(
        status=IssueStatus.IN_PROGRESS,
        resolved_by="developer1"
    )
    await tracker.update_issue(style_issue.id, updates)
    
    print(f"   • Resolving style issue (auto-fix applied)...")
    await tracker.resolve_issue(
        style_issue.id,
        resolved_by="auto_fix_engine",
        resolution_method="auto_fix"
    )
    
    # Resolve another issue manually
    complexity_issue = next(issue for issue in created_issues if issue.issue_type == IssueType.COMPLEXITY)
    print(f"   • Resolving complexity issue (manual refactoring)...")
    await tracker.resolve_issue(
        complexity_issue.id,
        resolved_by="developer2",
        resolution_method="manual_refactoring"
    )
    
    print("\n4. Demonstrating bulk operations...")
    
    # Get remaining open issues
    open_issues = await tracker.get_issues(
        project_id="demo-project",
        status=IssueStatus.OPEN
    )
    
    if len(open_issues) > 1:
        # Bulk update some issues to IN_PROGRESS
        issue_ids = [issue.id for issue in open_issues[:2]]
        bulk_updates = QualityIssueUpdate(
            status=IssueStatus.IN_PROGRESS,
            resolved_by="team_lead"
        )
        
        updated_count = await tracker.bulk_update_issues(issue_ids, bulk_updates)
        print(f"   • Bulk updated {updated_count} issues to IN_PROGRESS")
    
    print("\n5. Generating resolution metrics...")
    
    metrics = await tracker.get_resolution_metrics(project_id="demo-project")
    
    print(f"   📊 Resolution Metrics:")
    print(f"      • Total issues: {metrics.total_issues}")
    print(f"      • Resolved issues: {metrics.resolved_issues}")
    print(f"      • Resolution rate: {metrics.resolution_rate:.1f}%")
    print(f"      • Average resolution time: {metrics.average_resolution_time:.1f} hours")
    print(f"      • Auto-fix success rate: {metrics.auto_fix_success_rate:.1f}%")
    
    print(f"\n   📈 Issues by Severity:")
    for severity, count in metrics.issues_by_severity.items():
        print(f"      • {severity.title()}: {count}")
    
    print(f"\n   📋 Issues by Type:")
    for issue_type, count in metrics.issues_by_type.items():
        print(f"      • {issue_type.title()}: {count}")
    
    print("\n6. Demonstrating escalation detection...")
    
    # Check for stale issues (none should be found since we just created them)
    stale_issues = await tracker.escalate_stale_issues(hours_threshold=1)
    print(f"   • Stale issues found: {len(stale_issues)}")
    
    if stale_issues:
        for issue in stale_issues:
            print(f"     - {issue.id}: {issue.description[:50]}...")
    else:
        print("     (No stale issues - all recently created)")
    
    print("\n7. Final issue status summary...")
    
    # Get final status of all issues
    final_issues = await tracker.get_issues(project_id="demo-project")
    status_counts = {}
    
    for issue in final_issues:
        status = issue.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"   📋 Final Status Distribution:")
    for status, count in status_counts.items():
        print(f"      • {status.replace('_', ' ').title()}: {count}")
    
    print("\n8. Demonstrating issue details retrieval...")
    
    # Show details of a resolved issue
    resolved_issues = [issue for issue in final_issues if issue.status == IssueStatus.RESOLVED]
    if resolved_issues:
        issue = resolved_issues[0]
        print(f"   🔍 Resolved Issue Details:")
        print(f"      • ID: {issue.id}")
        print(f"      • File: {issue.file_path}:{issue.line_number}")
        print(f"      • Type: {issue.issue_type.value}")
        print(f"      • Severity: {issue.severity.value}")
        print(f"      • Description: {issue.description}")
        print(f"      • Resolved by: {issue.resolved_by}")
        print(f"      • Resolution method: {issue.resolution_method}")
        print(f"      • Created: {issue.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      • Resolved: {issue.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if issue.resolved_at else 'N/A'}")
    
    print("\n✅ Quality Issue Tracker Demo Complete!")
    print("=" * 50)
    print("\nKey Features Demonstrated:")
    print("• Automatic issue creation with priority routing")
    print("• Issue lifecycle management (open → in_progress → resolved)")
    print("• Priority-based categorization and routing")
    print("• Comprehensive filtering and querying")
    print("• Bulk operations for efficiency")
    print("• Resolution tracking and verification")
    print("• Metrics collection and analysis")
    print("• Escalation detection for stale issues")
    print("• Complete audit trail for all changes")


if __name__ == "__main__":
    asyncio.run(demo_quality_issue_tracker())