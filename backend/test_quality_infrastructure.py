#!/usr/bin/env python3
"""
Test script to verify code quality infrastructure is working correctly.
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add the app directory to the path so we can import our models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from models.quality import QualityIssue, QualityMetrics, AutoFixResult, IssueType, Severity, FixType
from core.quality_config import QualityConfigManager


def test_database_tables():
    """Test that all quality tables exist and have data."""
    print("Testing database tables...")
    
    conn = sqlite3.connect("aitm.db")
    cursor = conn.cursor()
    
    try:
        # Test quality_issues table
        cursor.execute("SELECT COUNT(*) FROM quality_issues")
        issues_count = cursor.fetchone()[0]
        print(f"✓ Quality issues table: {issues_count} records")
        
        # Test quality_metrics table
        cursor.execute("SELECT COUNT(*) FROM quality_metrics")
        metrics_count = cursor.fetchone()[0]
        print(f"✓ Quality metrics table: {metrics_count} records")
        
        # Test auto_fix_results table
        cursor.execute("SELECT COUNT(*) FROM auto_fix_results")
        fixes_count = cursor.fetchone()[0]
        print(f"✓ Auto-fix results table: {fixes_count} records")
        
        # Test quality_standards table
        cursor.execute("SELECT COUNT(*) FROM quality_standards")
        standards_count = cursor.fetchone()[0]
        print(f"✓ Quality standards table: {standards_count} records")
        
        # Test quality_scans table
        cursor.execute("SELECT COUNT(*) FROM quality_scans")
        scans_count = cursor.fetchone()[0]
        print(f"✓ Quality scans table: {scans_count} records")
        
        # Test quality_trends table
        cursor.execute("SELECT COUNT(*) FROM quality_trends")
        trends_count = cursor.fetchone()[0]
        print(f"✓ Quality trends table: {trends_count} records")
        
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False
    finally:
        conn.close()


def test_quality_models():
    """Test that quality data models work correctly."""
    print("\nTesting quality models...")
    
    try:
        # Test QualityIssue model
        issue = QualityIssue(
            project_id="test-project",
            file_path="test.py",
            line_number=42,
            issue_type=IssueType.STYLE,
            severity=Severity.MEDIUM,
            category="line_length",
            description="Line too long",
            auto_fixable=True
        )
        
        issue_dict = issue.to_dict()
        restored_issue = QualityIssue.from_dict(issue_dict)
        assert restored_issue.file_path == issue.file_path
        print("✓ QualityIssue model serialization/deserialization works")
        
        # Test QualityMetrics model
        metrics = QualityMetrics(
            project_id="test-project",
            code_coverage=85.5,
            cyclomatic_complexity=7.2,
            maintainability_index=78.9
        )
        
        metrics_dict = metrics.to_dict()
        restored_metrics = QualityMetrics.from_dict(metrics_dict)
        assert restored_metrics.code_coverage == metrics.code_coverage
        print("✓ QualityMetrics model serialization/deserialization works")
        
        # Test AutoFixResult model
        fix_result = AutoFixResult(
            issue_id="test-issue",
            project_id="test-project",
            file_path="test.py",
            fix_type=FixType.FORMATTING,
            success=True
        )
        
        fix_dict = fix_result.to_dict()
        restored_fix = AutoFixResult.from_dict(fix_dict)
        assert restored_fix.success == fix_result.success
        print("✓ AutoFixResult model serialization/deserialization works")
        
        return True
        
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        return False


def test_quality_config():
    """Test quality configuration management."""
    print("\nTesting quality configuration...")
    
    try:
        config_manager = QualityConfigManager()
        
        # Test getting quality standards
        quality_config = config_manager.get_quality_standard(standard_type='quality')
        assert 'min_coverage' in quality_config
        print("✓ Quality standards retrieval works")
        
        # Test getting auto-fix configuration
        autofix_config = config_manager.get_autofix_config()
        assert autofix_config.safety_level is not None
        print("✓ Auto-fix configuration retrieval works")
        
        # Test getting quality thresholds
        thresholds = config_manager.get_quality_thresholds()
        assert thresholds.min_coverage > 0
        print("✓ Quality thresholds retrieval works")
        
        # Test listing quality standards
        standards = config_manager.list_quality_standards()
        assert len(standards) > 0
        print(f"✓ Quality standards listing works ({len(standards)} standards found)")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_sample_data_integrity():
    """Test that sample data is properly structured."""
    print("\nTesting sample data integrity...")
    
    conn = sqlite3.connect("aitm.db")
    cursor = conn.cursor()
    
    try:
        # Test that issues have valid types and severities
        cursor.execute("""
            SELECT DISTINCT issue_type, severity FROM quality_issues
        """)
        issue_data = cursor.fetchall()
        
        valid_types = [t.value for t in IssueType]
        valid_severities = [s.value for s in Severity]
        
        for issue_type, severity in issue_data:
            assert issue_type in valid_types, f"Invalid issue type: {issue_type}"
            assert severity in valid_severities, f"Invalid severity: {severity}"
        
        print("✓ Quality issues have valid types and severities")
        
        # Test that metrics are within reasonable ranges
        cursor.execute("""
            SELECT code_coverage, cyclomatic_complexity, maintainability_index
            FROM quality_metrics
            WHERE code_coverage IS NOT NULL
        """)
        metrics_data = cursor.fetchall()
        
        for coverage, complexity, maintainability in metrics_data:
            if coverage is not None:
                assert 0 <= coverage <= 100, f"Invalid coverage: {coverage}"
            if complexity is not None:
                assert complexity >= 0, f"Invalid complexity: {complexity}"
            if maintainability is not None:
                assert 0 <= maintainability <= 100, f"Invalid maintainability: {maintainability}"
        
        print("✓ Quality metrics are within valid ranges")
        
        # Test that auto-fix results have valid fix types
        cursor.execute("SELECT DISTINCT fix_type FROM auto_fix_results")
        fix_types = [row[0] for row in cursor.fetchall()]
        
        valid_fix_types = [ft.value for ft in FixType]
        for fix_type in fix_types:
            assert fix_type in valid_fix_types, f"Invalid fix type: {fix_type}"
        
        print("✓ Auto-fix results have valid fix types")
        
        return True
        
    except Exception as e:
        print(f"✗ Sample data integrity test failed: {e}")
        return False
    finally:
        conn.close()


def main():
    """Run all infrastructure tests."""
    print("Code Quality Infrastructure Test Suite")
    print("=" * 50)
    
    tests = [
        test_database_tables,
        test_quality_models,
        test_quality_config,
        test_sample_data_integrity
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Code quality infrastructure is ready.")
        return 0
    else:
        print("✗ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())