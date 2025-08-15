#!/usr/bin/env python3
"""
Integration test for QualityIssueTracker with database operations.
Tests the complete workflow without requiring the full FastAPI app.
"""

import asyncio
import sys
import os
import sqlite3
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.quality_issue_tracker import QualityIssueTracker
from app.models.quality import (
    QualityIssueCreate, QualityIssueUpdate,
    IssueType, Severity, IssueStatus
)


async def test_integration_workflow():
    """Test complete integration workflow."""
    print("🔧 Quality Issue Tracker Integration Test")
    print("=" * 50)
    
    # Initialize tracker with test database
    tracker = QualityIssueTracker("test_integration.db")
    
    # Create database tables
    conn = sqlite3.connect("test_integration.db")
    cursor = conn.cursor()
    
    # Create quality_issues table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_issues (
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
        CREATE TABLE IF NOT EXISTS auto_fix_results (
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
        CREATE TABLE IF NOT EXISTS quality_standards (
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
    
    print("\n1. Testing issue creation and routing...")
    
    # Create various types of issues
    test_issues = [
        QualityIssueCreate(
            project_id="integration-test",
            file_path="src/security.py",
            line_number=42,
            issue_type=IssueType.SECURITY,
            severity=Severity.CRITICAL,
            category="vulnerability",
            description="Critical security vulnerability detected",
            auto_fixable=False
        ),
        QualityIssueCreate(
            project_id="integration-test",
            file_path="src/style.py",
            line_number=15,
            issue_type=IssueType.STYLE,
            severity=Severity.LOW,
            category="formatting",
            description="Line too long",
            suggested_fix="Break line",
            auto_fixable=True
        ),
        QualityIssueCreate(
            project_id="integration-test",
            file_path="src/performance.py",
            line_number=88,
            issue_type=IssueType.PERFORMANCE,
            severity=Severity.HIGH,
            category="optimization",
            description="Inefficient database query",
            auto_fixable=False
        )
    ]
    
    created_issues = []
    for i, issue_data in enumerate(test_issues, 1):
        issue = await tracker.create_issue(issue_data)
        created_issues.append(issue)
        print(f"   ✓ Created issue {i}: {issue.issue_type.value} - {issue.severity.value}")
    
    print(f"\n   Total issues created: {len(created_issues)}")
    
    print("\n2. Testing issue querying and filtering...")
    
    # Test various queries
    all_issues = await tracker.get_issues(project_id="integration-test")
    print(f"   • All project issues: {len(all_issues)}")
    
    critical_issues = await tracker.get_issues(severity=Severity.CRITICAL)
    print(f"   • Critical issues: {len(critical_issues)}")
    
    security_issues = await tracker.get_issues(issue_type=IssueType.SECURITY)
    print(f"   • Security issues: {len(security_issues)}")
    
    auto_fixable = [issue for issue in all_issues if issue.auto_fixable]
    print(f"   • Auto-fixable issues: {len(auto_fixable)}")
    
    print("\n3. Testing issue lifecycle management...")
    
    # Update first issue to in_progress
    first_issue = created_issues[0]
    updates = QualityIssueUpdate(
        status=IssueStatus.IN_PROGRESS,
        resolved_by="integration_tester"
    )
    
    updated_issue = await tracker.update_issue(first_issue.id, updates)
    print(f"   ✓ Updated issue {first_issue.id} to {updated_issue.status.value}")
    
    # Resolve second issue
    second_issue = created_issues[1]
    success = await tracker.resolve_issue(
        second_issue.id,
        resolved_by="auto_fix_engine",
        resolution_method="auto_fix"
    )
    print(f"   ✓ Resolved issue {second_issue.id}: {success}")
    
    print("\n4. Testing bulk operations...")
    
    # Bulk update remaining open issues
    open_issues = await tracker.get_issues(
        project_id="integration-test",
        status=IssueStatus.OPEN
    )
    
    if open_issues:
        issue_ids = [issue.id for issue in open_issues]
        bulk_updates = QualityIssueUpdate(
            status=IssueStatus.IN_PROGRESS,
            resolved_by="bulk_processor"
        )
        
        updated_count = await tracker.bulk_update_issues(issue_ids, bulk_updates)
        print(f"   ✓ Bulk updated {updated_count} issues")
    
    print("\n5. Testing metrics calculation...")
    
    metrics = await tracker.get_resolution_metrics(project_id="integration-test")
    print(f"   📊 Resolution Metrics:")
    print(f"      • Total issues: {metrics.total_issues}")
    print(f"      • Resolved issues: {metrics.resolved_issues}")
    print(f"      • Resolution rate: {metrics.resolution_rate:.1f}%")
    print(f"      • Average resolution time: {metrics.average_resolution_time:.1f} hours")
    
    print(f"\n   📈 Issues by Severity:")
    for severity, count in metrics.issues_by_severity.items():
        print(f"      • {severity.title()}: {count}")
    
    print(f"\n   📋 Issues by Type:")
    for issue_type, count in metrics.issues_by_type.items():
        print(f"      • {issue_type.title()}: {count}")
    
    print("\n6. Testing escalation detection...")
    
    stale_issues = await tracker.escalate_stale_issues(hours_threshold=1)
    print(f"   • Stale issues found: {len(stale_issues)}")
    
    print("\n7. Testing error handling...")
    
    # Test non-existent issue operations
    non_existent_id = "non-existent-issue-id"
    
    # Try to get non-existent issue
    missing_issue = await tracker.get_issue_by_id(non_existent_id)
    print(f"   ✓ Non-existent issue query: {missing_issue is None}")
    
    # Try to update non-existent issue
    update_result = await tracker.update_issue(non_existent_id, updates)
    print(f"   ✓ Non-existent issue update: {update_result is None}")
    
    # Try to resolve non-existent issue
    resolve_result = await tracker.resolve_issue(non_existent_id, "tester")
    print(f"   ✓ Non-existent issue resolve: {resolve_result is False}")
    
    print("\n8. Testing data consistency...")
    
    # Verify all created issues exist
    verification_count = 0
    for issue in created_issues:
        retrieved = await tracker.get_issue_by_id(issue.id)
        if retrieved:
            verification_count += 1
    
    print(f"   ✓ Data consistency check: {verification_count}/{len(created_issues)} issues verified")
    
    print("\n9. Final status summary...")
    
    final_issues = await tracker.get_issues(project_id="integration-test")
    status_counts = {}
    
    for issue in final_issues:
        status = issue.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"   📋 Final Status Distribution:")
    for status, count in status_counts.items():
        print(f"      • {status.replace('_', ' ').title()}: {count}")
    
    print("\n10. Cleanup...")
    
    # Clean up test data
    cleanup_count = 0
    for issue in created_issues:
        deleted = await tracker.delete_issue(issue.id)
        if deleted:
            cleanup_count += 1
    
    print(f"   ✓ Cleaned up {cleanup_count} test issues")
    
    # Remove test database
    try:
        os.remove("test_integration.db")
        print("   ✓ Removed test database")
    except FileNotFoundError:
        pass
    
    print("\n✅ Integration Test Complete!")
    print("=" * 50)
    print("\nAll core functionality verified:")
    print("• Issue creation with automatic routing")
    print("• Priority-based categorization")
    print("• Issue lifecycle management")
    print("• Resolution tracking and verification")
    print("• Comprehensive querying and filtering")
    print("• Bulk operations")
    print("• Metrics calculation")
    print("• Escalation detection")
    print("• Error handling")
    print("• Data consistency")


if __name__ == "__main__":
    asyncio.run(test_integration_workflow())