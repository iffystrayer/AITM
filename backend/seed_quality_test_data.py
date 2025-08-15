#!/usr/bin/env python3
"""
Seed test data for code quality tracking system.
Creates sample quality issues, metrics, and fix results for testing.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import random


def seed_quality_test_data(db_path: str = "aitm.db"):
    """Seed the database with test data for quality tracking."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Use a fixed test project ID for seeding
        test_project_id = "test-project-quality-tracking"
        
        # Seed quality issues
        print("Seeding quality issues...")
        seed_quality_issues(cursor, test_project_id)
        
        # Seed quality metrics
        print("Seeding quality metrics...")
        seed_quality_metrics(cursor, test_project_id)
        
        # Seed auto-fix results
        print("Seeding auto-fix results...")
        seed_autofix_results(cursor, test_project_id)
        
        # Seed quality scans
        print("Seeding quality scans...")
        seed_quality_scans(cursor, test_project_id)
        
        # Seed quality trends
        print("Seeding quality trends...")
        seed_quality_trends(cursor, test_project_id)
        
        conn.commit()
        print("Quality test data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding quality test data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_quality_issues(cursor, project_id: str):
    """Seed sample quality issues."""
    
    sample_issues = [
        {
            'file_path': 'backend/app/services/threat_analysis.py',
            'line_number': 45,
            'issue_type': 'complexity',
            'severity': 'high',
            'category': 'cyclomatic_complexity',
            'description': 'Function has cyclomatic complexity of 15, exceeds threshold of 10',
            'suggested_fix': 'Break down the function into smaller, more focused functions',
            'auto_fixable': False
        },
        {
            'file_path': 'backend/app/models/analysis.py',
            'line_number': 23,
            'issue_type': 'style',
            'severity': 'medium',
            'category': 'line_length',
            'description': 'Line exceeds maximum length of 88 characters',
            'suggested_fix': 'Break line into multiple lines or use shorter variable names',
            'auto_fixable': True
        },
        {
            'file_path': 'frontend/src/lib/components/Dashboard.svelte',
            'line_number': 67,
            'issue_type': 'security',
            'severity': 'critical',
            'category': 'xss_vulnerability',
            'description': 'Potential XSS vulnerability: unescaped user input in HTML',
            'suggested_fix': 'Use proper HTML escaping or sanitization',
            'auto_fixable': False
        },
        {
            'file_path': 'backend/app/api/v1/endpoints/projects.py',
            'line_number': 12,
            'issue_type': 'style',
            'severity': 'low',
            'category': 'import_order',
            'description': 'Imports are not properly ordered according to PEP8',
            'suggested_fix': 'Reorder imports: standard library, third-party, local',
            'auto_fixable': True
        },
        {
            'file_path': 'backend/app/services/llm_service.py',
            'line_number': 89,
            'issue_type': 'performance',
            'severity': 'medium',
            'category': 'inefficient_loop',
            'description': 'Inefficient loop that could be optimized with list comprehension',
            'suggested_fix': 'Replace loop with list comprehension for better performance',
            'auto_fixable': True
        },
        {
            'file_path': 'backend/tests/test_threat_analysis.py',
            'line_number': 156,
            'issue_type': 'testing',
            'severity': 'medium',
            'category': 'missing_assertion',
            'description': 'Test method lacks proper assertions',
            'suggested_fix': 'Add assertions to verify expected behavior',
            'auto_fixable': False
        },
        {
            'file_path': 'frontend/src/routes/projects/+page.svelte',
            'line_number': 34,
            'issue_type': 'duplication',
            'severity': 'low',
            'category': 'duplicate_code',
            'description': 'Code block is duplicated in multiple components',
            'suggested_fix': 'Extract common code into a reusable component or utility',
            'auto_fixable': False
        }
    ]
    
    for i, issue_data in enumerate(sample_issues):
        issue_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
        
        # Some issues are resolved
        status = 'resolved' if i % 3 == 0 else 'open'
        resolved_at = created_at + timedelta(hours=random.randint(1, 48)) if status == 'resolved' else None
        
        cursor.execute("""
            INSERT INTO quality_issues 
            (id, project_id, file_path, line_number, issue_type, severity, category, 
             description, suggested_fix, auto_fixable, status, created_at, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            issue_id, project_id, issue_data['file_path'], issue_data['line_number'],
            issue_data['issue_type'], issue_data['severity'], issue_data['category'],
            issue_data['description'], issue_data['suggested_fix'], issue_data['auto_fixable'],
            status, created_at.isoformat(), resolved_at.isoformat() if resolved_at else None
        ))


def seed_quality_metrics(cursor, project_id: str):
    """Seed sample quality metrics over time."""
    
    # Generate metrics for the last 30 days
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    for day in range(30):
        timestamp = base_date + timedelta(days=day)
        
        # Simulate improving quality over time with some variance
        progress_factor = day / 30.0
        variance = random.uniform(-0.1, 0.1)
        
        metrics = {
            'code_coverage': min(100, 65 + (progress_factor * 20) + (variance * 10)),
            'cyclomatic_complexity': max(1, 8.5 - (progress_factor * 2) + (variance * 2)),
            'maintainability_index': min(100, 60 + (progress_factor * 25) + (variance * 15)),
            'technical_debt_ratio': max(0, 0.08 - (progress_factor * 0.03) + (variance * 0.02)),
            'test_quality_score': min(100, 70 + (progress_factor * 20) + (variance * 10)),
            'security_score': min(100, 75 + (progress_factor * 15) + (variance * 8)),
            'performance_score': min(100, 80 + (progress_factor * 15) + (variance * 5)),
            'lines_of_code': int(5000 + (progress_factor * 2000) + (variance * 500)),
            'duplicate_code_ratio': max(0, 0.05 - (progress_factor * 0.02) + (variance * 0.01)),
            'comment_ratio': min(1, 0.15 + (progress_factor * 0.10) + (variance * 0.05))
        }
        
        cursor.execute("""
            INSERT INTO quality_metrics 
            (id, project_id, timestamp, code_coverage, cyclomatic_complexity, 
             maintainability_index, technical_debt_ratio, test_quality_score, 
             security_score, performance_score, lines_of_code, duplicate_code_ratio, comment_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), project_id, timestamp.isoformat(),
            round(metrics['code_coverage'], 2),
            round(metrics['cyclomatic_complexity'], 2),
            round(metrics['maintainability_index'], 2),
            round(metrics['technical_debt_ratio'], 4),
            round(metrics['test_quality_score'], 2),
            round(metrics['security_score'], 2),
            round(metrics['performance_score'], 2),
            metrics['lines_of_code'],
            round(metrics['duplicate_code_ratio'], 4),
            round(metrics['comment_ratio'], 3)
        ))


def seed_autofix_results(cursor, project_id: str):
    """Seed sample auto-fix results."""
    
    # Get some quality issues to create fixes for
    cursor.execute("""
        SELECT id, file_path FROM quality_issues 
        WHERE project_id = ? AND auto_fixable = 1
        LIMIT 5
    """, (project_id,))
    
    fixable_issues = cursor.fetchall()
    
    fix_types = ['formatting', 'imports', 'style', 'simple_refactor']
    
    for issue_id, file_path in fixable_issues:
        fix_id = str(uuid.uuid4())
        fix_type = random.choice(fix_types)
        success = random.choice([True, True, True, False])  # 75% success rate
        applied_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))
        
        original_content = "# Original code with style issues\ndef   badly_formatted_function( x,y ):\n    return x+y"
        fixed_content = "# Fixed code with proper formatting\ndef properly_formatted_function(x, y):\n    return x + y" if success else None
        error_message = None if success else "Fix failed: syntax error in generated code"
        
        cursor.execute("""
            INSERT INTO auto_fix_results 
            (id, issue_id, project_id, file_path, fix_type, original_content, 
             fixed_content, success, error_message, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fix_id, issue_id, project_id, file_path, fix_type,
            original_content, fixed_content, success, error_message,
            applied_at.isoformat()
        ))


def seed_quality_scans(cursor, project_id: str):
    """Seed sample quality scans."""
    
    scan_types = ['full_scan', 'incremental_scan', 'security_scan', 'style_scan']
    
    for i in range(10):
        scan_id = str(uuid.uuid4())
        scan_type = random.choice(scan_types)
        started_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 168))  # Last week
        
        # Most scans complete successfully
        status = random.choice(['completed', 'completed', 'completed', 'failed'])
        completed_at = started_at + timedelta(minutes=random.randint(5, 60)) if status == 'completed' else None
        
        files_scanned = random.randint(50, 500) if status == 'completed' else random.randint(10, 100)
        issues_found = random.randint(5, 50) if status == 'completed' else 0
        fixes_applied = random.randint(0, issues_found) if status == 'completed' else 0
        
        error_message = None if status == 'completed' else "Scan failed: timeout during analysis"
        
        cursor.execute("""
            INSERT INTO quality_scans 
            (id, project_id, scan_type, status, started_at, completed_at, 
             files_scanned, issues_found, fixes_applied, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_id, project_id, scan_type, status, started_at.isoformat(),
            completed_at.isoformat() if completed_at else None,
            files_scanned, issues_found, fixes_applied, error_message
        ))


def seed_quality_trends(cursor, project_id: str):
    """Seed sample quality trend data."""
    
    metrics = ['code_coverage', 'cyclomatic_complexity', 'maintainability_index', 
               'technical_debt_ratio', 'security_score']
    
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    for day in range(0, 30, 3):  # Every 3 days
        timestamp = base_date + timedelta(days=day)
        
        for metric in metrics:
            trend_id = str(uuid.uuid4())
            
            # Simulate different trend patterns
            if metric == 'code_coverage':
                value = 65 + (day * 0.8) + random.uniform(-2, 2)
                direction = 'up' if day > 15 else 'stable'
            elif metric == 'cyclomatic_complexity':
                value = 8.5 - (day * 0.1) + random.uniform(-0.5, 0.5)
                direction = 'down' if day > 10 else 'stable'
            elif metric == 'technical_debt_ratio':
                value = 0.08 - (day * 0.001) + random.uniform(-0.005, 0.005)
                direction = 'down'
            else:
                value = 70 + (day * 0.5) + random.uniform(-3, 3)
                direction = 'up'
            
            change_percentage = random.uniform(-5, 15) if direction == 'up' else random.uniform(-15, 5)
            
            cursor.execute("""
                INSERT INTO quality_trends 
                (id, project_id, metric_name, metric_value, timestamp, trend_direction, change_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                trend_id, project_id, metric, round(value, 3), 
                timestamp.isoformat(), direction, round(change_percentage, 2)
            ))


if __name__ == "__main__":
    seed_quality_test_data()