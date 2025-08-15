#!/usr/bin/env python3
"""
Database schema creation script for code quality tracking system.
Creates tables for quality metrics, issues, and fix tracking.
"""

import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path

def create_quality_database(db_path: str = "aitm.db"):
    """Create code quality tracking tables in the database."""
    
    # Ensure the database directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
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
                resolution_method TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Create quality_metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                code_coverage REAL,
                cyclomatic_complexity REAL,
                maintainability_index REAL,
                technical_debt_ratio REAL,
                test_quality_score REAL,
                security_score REAL,
                performance_score REAL,
                lines_of_code INTEGER,
                duplicate_code_ratio REAL,
                comment_ratio REAL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
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
                is_rolled_back BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (issue_id) REFERENCES quality_issues (id),
                FOREIGN KEY (project_id) REFERENCES projects (id)
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Create quality_scans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_scans (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                files_scanned INTEGER DEFAULT 0,
                issues_found INTEGER DEFAULT 0,
                fixes_applied INTEGER DEFAULT 0,
                scan_configuration TEXT,
                error_message TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Create quality_trends table for historical tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_trends (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                trend_direction TEXT,
                change_percentage REAL,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_issues_project ON quality_issues(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_issues_status ON quality_issues(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_issues_severity ON quality_issues(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_metrics_project ON quality_metrics(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_metrics_timestamp ON quality_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auto_fix_results_issue ON auto_fix_results(issue_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_scans_project ON quality_scans(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_trends_project_metric ON quality_trends(project_id, metric_name)")
        
        conn.commit()
        print("Code quality database tables created successfully!")
        
        # Insert default quality standards
        insert_default_standards(cursor)
        conn.commit()
        print("Default quality standards inserted successfully!")
        
    except Exception as e:
        print(f"Error creating quality database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def insert_default_standards(cursor):
    """Insert default quality standards configuration."""
    import json
    import uuid
    
    default_standards = [
        {
            'id': str(uuid.uuid4()),
            'project_id': None,  # Global standards
            'standard_name': 'Python Code Style',
            'standard_type': 'style',
            'configuration': json.dumps({
                'max_line_length': 88,
                'max_complexity': 10,
                'naming_conventions': {
                    'function': 'snake_case',
                    'variable': 'snake_case',
                    'class': 'PascalCase',
                    'constant': 'UPPER_CASE'
                },
                'import_order': ['standard', 'third_party', 'local'],
                'docstring_style': 'google'
            })
        },
        {
            'id': str(uuid.uuid4()),
            'project_id': None,
            'standard_name': 'Code Quality Thresholds',
            'standard_type': 'quality',
            'configuration': json.dumps({
                'min_coverage': 80.0,
                'max_complexity': 10,
                'min_maintainability': 70.0,
                'max_technical_debt_ratio': 0.05,
                'min_test_quality': 75.0,
                'min_security_score': 85.0
            })
        },
        {
            'id': str(uuid.uuid4()),
            'project_id': None,
            'standard_name': 'Auto-Fix Configuration',
            'standard_type': 'autofix',
            'configuration': json.dumps({
                'enabled_fix_types': ['formatting', 'imports', 'style'],
                'safety_level': 'conservative',
                'backup_enabled': True,
                'rollback_timeout': 3600,
                'excluded_patterns': ['*.min.js', '*.generated.*', 'migrations/*']
            })
        }
    ]
    
    for standard in default_standards:
        cursor.execute("""
            INSERT OR IGNORE INTO quality_standards 
            (id, project_id, standard_name, standard_type, configuration, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            standard['id'],
            standard['project_id'],
            standard['standard_name'],
            standard['standard_type'],
            standard['configuration'],
            True
        ))

if __name__ == "__main__":
    create_quality_database()