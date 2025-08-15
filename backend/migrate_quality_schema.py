#!/usr/bin/env python3
"""
Database migration script for code quality tracking system.
Handles schema updates and data migrations.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path


class QualityMigration:
    """Handles database migrations for quality tracking system."""
    
    def __init__(self, db_path: str = "aitm.db"):
        self.db_path = db_path
        self.migrations = [
            self.migration_001_initial_schema,
            self.migration_002_add_indexes,
            self.migration_003_add_trends_table,
            self.migration_004_add_scan_configuration,
        ]
    
    def get_current_version(self) -> int:
        """Get current migration version."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if migration table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='quality_migrations'
            """)
            
            if not cursor.fetchone():
                # Create migration tracking table
                cursor.execute("""
                    CREATE TABLE quality_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                """)
                conn.commit()
                return 0
            
            # Get latest migration version
            cursor.execute("SELECT MAX(version) FROM quality_migrations")
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
            
        finally:
            conn.close()
    
    def apply_migration(self, version: int, description: str):
        """Record a migration as applied."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO quality_migrations (version, description)
                VALUES (?, ?)
            """, (version, description))
            conn.commit()
            
        finally:
            conn.close()
    
    def migrate(self):
        """Apply all pending migrations."""
        current_version = self.get_current_version()
        print(f"Current migration version: {current_version}")
        
        for i, migration_func in enumerate(self.migrations):
            migration_version = i + 1
            
            if migration_version > current_version:
                print(f"Applying migration {migration_version}...")
                try:
                    description = migration_func()
                    self.apply_migration(migration_version, description)
                    print(f"Migration {migration_version} applied successfully")
                except Exception as e:
                    print(f"Migration {migration_version} failed: {e}")
                    raise
        
        print("All migrations applied successfully!")
    
    def migration_001_initial_schema(self) -> str:
        """Initial quality tracking schema."""
        conn = sqlite3.connect(self.db_path)
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
                    resolution_method TEXT
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
                    comment_ratio REAL
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
            return "Initial quality tracking schema"
            
        finally:
            conn.close()
    
    def migration_002_add_indexes(self) -> str:
        """Add database indexes for performance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_quality_issues_project ON quality_issues(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_quality_issues_status ON quality_issues(status)",
                "CREATE INDEX IF NOT EXISTS idx_quality_issues_severity ON quality_issues(severity)",
                "CREATE INDEX IF NOT EXISTS idx_quality_issues_type ON quality_issues(issue_type)",
                "CREATE INDEX IF NOT EXISTS idx_quality_metrics_project ON quality_metrics(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_quality_metrics_timestamp ON quality_metrics(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_auto_fix_results_issue ON auto_fix_results(issue_id)",
                "CREATE INDEX IF NOT EXISTS idx_auto_fix_results_project ON auto_fix_results(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_quality_standards_project ON quality_standards(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_quality_standards_type ON quality_standards(standard_type)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            return "Added database indexes for performance"
            
        finally:
            conn.close()
    
    def migration_003_add_trends_table(self) -> str:
        """Add quality trends tracking table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_trends (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trend_direction TEXT,
                    change_percentage REAL
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_quality_trends_project_metric 
                ON quality_trends(project_id, metric_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_quality_trends_timestamp 
                ON quality_trends(timestamp)
            """)
            
            conn.commit()
            return "Added quality trends tracking table"
            
        finally:
            conn.close()
    
    def migration_004_add_scan_configuration(self) -> str:
        """Add quality scans table and configuration fields."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
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
                    error_message TEXT
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_quality_scans_project 
                ON quality_scans(project_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_quality_scans_status 
                ON quality_scans(status)
            """)
            
            conn.commit()
            return "Added quality scans table and configuration"
            
        finally:
            conn.close()
    
    def rollback_migration(self, target_version: int):
        """Rollback to a specific migration version (for development)."""
        print(f"Rolling back to version {target_version}")
        
        # This is a simplified rollback - in production you'd want more sophisticated rollback logic
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM quality_migrations WHERE version > ?
            """, (target_version,))
            
            if target_version == 0:
                # Drop all quality tables
                tables = [
                    'quality_issues', 'quality_metrics', 'auto_fix_results',
                    'quality_standards', 'quality_trends', 'quality_scans'
                ]
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            conn.commit()
            print(f"Rolled back to version {target_version}")
            
        finally:
            conn.close()


def main():
    """Run migrations."""
    import sys
    
    migration = QualityMigration()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "rollback" and len(sys.argv) > 2:
            target_version = int(sys.argv[2])
            migration.rollback_migration(target_version)
        else:
            print("Usage: python migrate_quality_schema.py [rollback <version>]")
    else:
        migration.migrate()


if __name__ == "__main__":
    main()