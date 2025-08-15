#!/usr/bin/env python3
"""
Test script for Quality Issues API endpoints.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.models.quality import IssueType, Severity, IssueStatus


def test_quality_issues_api():
    """Test Quality Issues API endpoints."""
    print("🔧 Testing Quality Issues API")
    print("=" * 40)
    
    client = TestClient(app)
    
    # Test data
    test_issue = {
        "project_id": "test-api-project",
        "file_path": "src/test_api.py",
        "line_number": 25,
        "issue_type": "style",
        "severity": "medium",
        "category": "formatting",
        "description": "API test issue - line too long",
        "suggested_fix": "Break line appropriately",
        "auto_fixable": True
    }
    
    print("\n1. Testing issue creation...")
    
    # Create issue
    response = client.post("/api/v1/quality/issues", json=test_issue)
    
    if response.status_code == 200:
        created_issue = response.json()
        issue_id = created_issue["id"]
        print(f"   ✓ Created issue: {issue_id}")
        print(f"   ✓ Status: {created_issue['status']}")
        print(f"   ✓ Type: {created_issue['issue_type']}")
    else:
        print(f"   ✗ Failed to create issue: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    print("\n2. Testing issue retrieval...")
    
    # Get specific issue
    response = client.get(f"/api/v1/quality/issues/{issue_id}")
    
    if response.status_code == 200:
        retrieved_issue = response.json()
        print(f"   ✓ Retrieved issue: {retrieved_issue['id']}")
        print(f"   ✓ Description: {retrieved_issue['description']}")
    else:
        print(f"   ✗ Failed to retrieve issue: {response.status_code}")
    
    print("\n3. Testing issue listing...")
    
    # Get all issues
    response = client.get("/api/v1/quality/issues")
    
    if response.status_code == 200:
        issues_response = response.json()
        print(f"   ✓ Found {len(issues_response['issues'])} issues")
        print(f"   ✓ Total: {issues_response['total']}")
        print(f"   ✓ Page: {issues_response['page']}")
    else:
        print(f"   ✗ Failed to list issues: {response.status_code}")
    
    print("\n4. Testing issue filtering...")
    
    # Filter by project
    response = client.get(f"/api/v1/quality/issues?project_id={test_issue['project_id']}")
    
    if response.status_code == 200:
        filtered_issues = response.json()
        print(f"   ✓ Project filter: {len(filtered_issues['issues'])} issues")
    else:
        print(f"   ✗ Failed to filter issues: {response.status_code}")
    
    # Filter by severity
    response = client.get(f"/api/v1/quality/issues?severity={test_issue['severity']}")
    
    if response.status_code == 200:
        severity_filtered = response.json()
        print(f"   ✓ Severity filter: {len(severity_filtered['issues'])} issues")
    else:
        print(f"   ✗ Failed to filter by severity: {response.status_code}")
    
    print("\n5. Testing issue updates...")
    
    # Update issue status
    update_data = {
        "status": "in_progress",
        "resolved_by": "api_tester"
    }
    
    response = client.put(f"/api/v1/quality/issues/{issue_id}", json=update_data)
    
    if response.status_code == 200:
        updated_issue = response.json()
        print(f"   ✓ Updated issue status: {updated_issue['status']}")
        print(f"   ✓ Resolved by: {updated_issue['resolved_by']}")
    else:
        print(f"   ✗ Failed to update issue: {response.status_code}")
    
    print("\n6. Testing issue resolution...")
    
    # Resolve issue
    resolve_data = {
        "resolved_by": "api_tester",
        "resolution_method": "api_test"
    }
    
    response = client.post(f"/api/v1/quality/issues/{issue_id}/resolve", params=resolve_data)
    
    if response.status_code == 200:
        resolved_issue = response.json()
        print(f"   ✓ Resolved issue: {resolved_issue['status']}")
        print(f"   ✓ Resolution method: {resolved_issue['resolution_method']}")
    else:
        print(f"   ✗ Failed to resolve issue: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print("\n7. Testing metrics endpoint...")
    
    # Get resolution metrics
    response = client.get("/api/v1/quality/issues/metrics/resolution")
    
    if response.status_code == 200:
        metrics = response.json()
        print(f"   ✓ Total issues: {metrics['total_issues']}")
        print(f"   ✓ Resolved issues: {metrics['resolved_issues']}")
        print(f"   ✓ Resolution rate: {metrics['resolution_rate']:.1f}%")
    else:
        print(f"   ✗ Failed to get metrics: {response.status_code}")
    
    print("\n8. Testing summary endpoint...")
    
    # Get issues summary
    response = client.get("/api/v1/quality/issues/summary")
    
    if response.status_code == 200:
        summary = response.json()
        print(f"   ✓ Total issues: {summary['total_issues']}")
        print(f"   ✓ Status distribution: {summary['status_distribution']}")
        print(f"   ✓ Auto-fixable: {summary['auto_fixable_count']}")
    else:
        print(f"   ✗ Failed to get summary: {response.status_code}")
    
    print("\n9. Testing stale issues endpoint...")
    
    # Get stale issues
    response = client.get("/api/v1/quality/issues/escalation/stale?hours_threshold=1")
    
    if response.status_code == 200:
        stale_response = response.json()
        print(f"   ✓ Stale issues found: {stale_response['count']}")
        print(f"   ✓ Threshold: {stale_response['threshold_hours']} hours")
    else:
        print(f"   ✗ Failed to get stale issues: {response.status_code}")
    
    print("\n10. Testing cleanup...")
    
    # Delete the test issue
    response = client.delete(f"/api/v1/quality/issues/{issue_id}")
    
    if response.status_code == 200:
        print(f"   ✓ Deleted test issue: {issue_id}")
    else:
        print(f"   ✗ Failed to delete issue: {response.status_code}")
    
    print("\n✅ Quality Issues API Test Complete!")
    print("=" * 40)


if __name__ == "__main__":
    test_quality_issues_api()