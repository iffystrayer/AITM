"""
Quality Issue Tracker with automatic issue lifecycle management.
Implements priority-based issue categorization and routing with resolution tracking.
"""

import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from app.models.quality import (
    QualityIssue, IssueType, Severity, IssueStatus,
    QualityIssueCreate, QualityIssueUpdate
)
from app.core.quality_config import QualityConfigManager


class IssuePriority(str, Enum):
    """Priority levels for issue routing and handling."""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueCategory(str, Enum):
    """Categories for issue classification."""
    BLOCKING = "blocking"
    REGRESSION = "regression"
    IMPROVEMENT = "improvement"
    MAINTENANCE = "maintenance"
    TECHNICAL_DEBT = "technical_debt"


@dataclass
class IssueRoutingRule:
    """Rule for routing issues based on criteria."""
    rule_id: str
    name: str
    conditions: Dict[str, Any]
    priority: IssuePriority
    category: IssueCategory
    auto_assign: Optional[str] = None
    escalation_threshold: Optional[int] = None  # hours


@dataclass
class IssueResolutionMetrics:
    """Metrics for issue resolution tracking."""
    total_issues: int
    resolved_issues: int
    average_resolution_time: float  # hours
    resolution_rate: float  # percentage
    issues_by_severity: Dict[str, int]
    issues_by_type: Dict[str, int]
    auto_fix_success_rate: float


class QualityIssueTracker:
    """
    Comprehensive quality issue tracking and management system.
    Provides automatic issue lifecycle management, priority-based routing,
    and resolution tracking with verification.
    """
    
    def __init__(self, db_path: str = "aitm.db"):
        self.db_path = db_path
        self.config_manager = QualityConfigManager(db_path)
        self.logger = logging.getLogger(__name__)
        self._routing_rules = self._load_default_routing_rules()
    
    def _load_default_routing_rules(self) -> List[IssueRoutingRule]:
        """Load default issue routing rules."""
        return [
            IssueRoutingRule(
                rule_id="critical_security",
                name="Critical Security Issues",
                conditions={"issue_type": "security", "severity": "critical"},
                priority=IssuePriority.URGENT,
                category=IssueCategory.BLOCKING,
                escalation_threshold=1
            ),
            IssueRoutingRule(
                rule_id="high_complexity",
                name="High Complexity Issues",
                conditions={"issue_type": "complexity", "severity": ["high", "critical"]},
                priority=IssuePriority.HIGH,
                category=IssueCategory.TECHNICAL_DEBT,
                escalation_threshold=24
            ),
            IssueRoutingRule(
                rule_id="performance_critical",
                name="Critical Performance Issues",
                conditions={"issue_type": "performance", "severity": "critical"},
                priority=IssuePriority.URGENT,
                category=IssueCategory.BLOCKING,
                escalation_threshold=4
            ),
            IssueRoutingRule(
                rule_id="style_formatting",
                name="Style and Formatting",
                conditions={"issue_type": "style", "auto_fixable": True},
                priority=IssuePriority.LOW,
                category=IssueCategory.MAINTENANCE
            ),
            IssueRoutingRule(
                rule_id="test_quality",
                name="Test Quality Issues",
                conditions={"issue_type": "testing"},
                priority=IssuePriority.MEDIUM,
                category=IssueCategory.IMPROVEMENT,
                escalation_threshold=72
            )
        ]
    
    async def create_issue(self, issue_data: QualityIssueCreate) -> QualityIssue:
        """
        Create a new quality issue with automatic categorization and routing.
        
        Args:
            issue_data: Issue creation data
            
        Returns:
            Created QualityIssue with assigned priority and category
        """
        # Create base issue
        issue = QualityIssue(
            project_id=issue_data.project_id,
            file_path=issue_data.file_path,
            line_number=issue_data.line_number,
            column_number=issue_data.column_number,
            issue_type=issue_data.issue_type,
            severity=issue_data.severity,
            category=issue_data.category,
            description=issue_data.description,
            suggested_fix=issue_data.suggested_fix,
            auto_fixable=issue_data.auto_fixable
        )
        
        # Apply routing rules for priority and categorization
        priority, category = self._apply_routing_rules(issue)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO quality_issues 
                (id, project_id, file_path, line_number, column_number, issue_type, 
                 severity, category, description, suggested_fix, auto_fixable, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue.id, issue.project_id, issue.file_path, issue.line_number,
                issue.column_number, issue.issue_type.value, issue.severity.value,
                f"{issue.category}|{priority.value}|{category.value}",  # Extended category
                issue.description, issue.suggested_fix, issue.auto_fixable,
                issue.status.value, issue.created_at.isoformat()
            ))
            
            conn.commit()
            
            # Log issue creation
            self.logger.info(f"Created quality issue {issue.id} with priority {priority.value}")
            
            # Check for immediate escalation
            await self._check_escalation(issue, priority)
            
            return issue
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to create quality issue: {e}")
            raise
        finally:
            conn.close()
    
    def _apply_routing_rules(self, issue: QualityIssue) -> Tuple[IssuePriority, IssueCategory]:
        """
        Apply routing rules to determine issue priority and category.
        
        Args:
            issue: Quality issue to categorize
            
        Returns:
            Tuple of (priority, category)
        """
        for rule in self._routing_rules:
            if self._matches_conditions(issue, rule.conditions):
                return rule.priority, rule.category
        
        # Default routing based on severity
        severity_priority_map = {
            Severity.CRITICAL: IssuePriority.URGENT,
            Severity.HIGH: IssuePriority.HIGH,
            Severity.MEDIUM: IssuePriority.MEDIUM,
            Severity.LOW: IssuePriority.LOW,
            Severity.INFO: IssuePriority.LOW
        }
        
        return severity_priority_map.get(issue.severity, IssuePriority.MEDIUM), IssueCategory.IMPROVEMENT
    
    def _matches_conditions(self, issue: QualityIssue, conditions: Dict[str, Any]) -> bool:
        """Check if issue matches routing rule conditions."""
        for key, expected_value in conditions.items():
            issue_value = getattr(issue, key, None)
            
            if issue_value is None:
                continue
            
            # Handle enum values
            if hasattr(issue_value, 'value'):
                issue_value = issue_value.value
            
            # Handle list of expected values
            if isinstance(expected_value, list):
                if issue_value not in expected_value:
                    return False
            else:
                if issue_value != expected_value:
                    return False
        
        return True
    
    async def _check_escalation(self, issue: QualityIssue, priority: IssuePriority):
        """Check if issue needs immediate escalation."""
        if priority == IssuePriority.URGENT:
            # Log urgent issue for immediate attention
            self.logger.warning(
                f"URGENT quality issue created: {issue.id} - {issue.description}"
            )
            # Here you could integrate with notification systems
    
    async def update_issue(self, issue_id: str, updates: QualityIssueUpdate) -> Optional[QualityIssue]:
        """
        Update a quality issue with automatic lifecycle management.
        
        Args:
            issue_id: ID of issue to update
            updates: Update data
            
        Returns:
            Updated QualityIssue or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get current issue
            cursor.execute("SELECT * FROM quality_issues WHERE id = ?", (issue_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Build update query
            update_fields = []
            update_values = []
            
            if updates.status is not None:
                update_fields.append("status = ?")
                update_values.append(updates.status.value)
                
                # Set resolved_at if status is resolved
                if updates.status in [IssueStatus.RESOLVED, IssueStatus.WONT_FIX]:
                    update_fields.append("resolved_at = ?")
                    update_values.append(datetime.now(timezone.utc).isoformat())
            
            if updates.resolved_by is not None:
                update_fields.append("resolved_by = ?")
                update_values.append(updates.resolved_by)
            
            if updates.resolution_method is not None:
                update_fields.append("resolution_method = ?")
                update_values.append(updates.resolution_method)
            
            if not update_fields:
                return self._row_to_issue(row)
            
            update_values.append(issue_id)
            
            cursor.execute(f"""
                UPDATE quality_issues 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, update_values)
            
            conn.commit()
            
            # Get updated issue
            cursor.execute("SELECT * FROM quality_issues WHERE id = ?", (issue_id,))
            updated_row = cursor.fetchone()
            
            if updated_row:
                updated_issue = self._row_to_issue(updated_row)
                
                # Log status change
                if updates.status is not None:
                    self.logger.info(f"Issue {issue_id} status changed to {updates.status.value}")
                
                return updated_issue
            
            return None
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to update quality issue {issue_id}: {e}")
            raise
        finally:
            conn.close()
    
    async def resolve_issue(self, issue_id: str, resolved_by: str, 
                          resolution_method: str = "manual") -> bool:
        """
        Mark an issue as resolved with verification.
        
        Args:
            issue_id: ID of issue to resolve
            resolved_by: Who resolved the issue
            resolution_method: How it was resolved
            
        Returns:
            True if successfully resolved
        """
        updates = QualityIssueUpdate(
            status=IssueStatus.RESOLVED,
            resolved_by=resolved_by,
            resolution_method=resolution_method
        )
        
        updated_issue = await self.update_issue(issue_id, updates)
        
        if updated_issue:
            # Verify resolution if possible
            await self._verify_resolution(updated_issue)
            return True
        
        return False
    
    async def _verify_resolution(self, issue: QualityIssue):
        """Verify that an issue resolution is valid."""
        # This could include re-scanning the file to ensure the issue is actually fixed
        # For now, we'll just log the resolution
        self.logger.info(f"Issue {issue.id} marked as resolved by {issue.resolved_by}")
    
    async def get_issues(self, project_id: Optional[str] = None,
                        status: Optional[IssueStatus] = None,
                        severity: Optional[Severity] = None,
                        issue_type: Optional[IssueType] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[QualityIssue]:
        """
        Get quality issues with filtering options.
        
        Args:
            project_id: Filter by project
            status: Filter by status
            severity: Filter by severity
            issue_type: Filter by issue type
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of matching QualityIssue objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build query with filters
            where_conditions = []
            params = []
            
            if project_id:
                where_conditions.append("project_id = ?")
                params.append(project_id)
            
            if status:
                where_conditions.append("status = ?")
                params.append(status.value)
            
            if severity:
                where_conditions.append("severity = ?")
                params.append(severity.value)
            
            if issue_type:
                where_conditions.append("issue_type = ?")
                params.append(issue_type.value)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            params.extend([limit, offset])
            
            cursor.execute(f"""
                SELECT * FROM quality_issues 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, params)
            
            return [self._row_to_issue(row) for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    async def get_issue_by_id(self, issue_id: str) -> Optional[QualityIssue]:
        """Get a specific issue by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM quality_issues WHERE id = ?", (issue_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_issue(row)
            return None
            
        finally:
            conn.close()
    
    def _row_to_issue(self, row) -> QualityIssue:
        """Convert database row to QualityIssue object."""
        # Parse extended category field
        category_parts = row[7].split('|') if row[7] else ['', '', '']
        base_category = category_parts[0] if len(category_parts) > 0 else ''
        
        return QualityIssue(
            id=row[0],
            project_id=row[1],
            file_path=row[2],
            line_number=row[3],
            column_number=row[4],
            issue_type=IssueType(row[5]),
            severity=Severity(row[6]),
            category=base_category,
            description=row[8],
            suggested_fix=row[9],
            auto_fixable=bool(row[10]),
            status=IssueStatus(row[11]),
            created_at=datetime.fromisoformat(row[12]),
            resolved_at=datetime.fromisoformat(row[13]) if row[13] else None,
            resolved_by=row[14],
            resolution_method=row[15]
        )
    
    async def get_resolution_metrics(self, project_id: Optional[str] = None,
                                   days: int = 30) -> IssueResolutionMetrics:
        """
        Get issue resolution metrics for analysis.
        
        Args:
            project_id: Filter by project
            days: Number of days to analyze
            
        Returns:
            IssueResolutionMetrics object
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Calculate date threshold
            threshold_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Base query conditions
            where_conditions = ["created_at >= ?"]
            params = [threshold_date.isoformat()]
            
            if project_id:
                where_conditions.append("project_id = ?")
                params.append(project_id)
            
            where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Get total issues
            cursor.execute(f"SELECT COUNT(*) FROM quality_issues {where_clause}", params)
            total_issues = cursor.fetchone()[0]
            
            # Get resolved issues
            resolved_params = params + ['resolved']
            cursor.execute(f"""
                SELECT COUNT(*) FROM quality_issues 
                {where_clause} AND status = ?
            """, resolved_params)
            resolved_issues = cursor.fetchone()[0]
            
            # Calculate resolution rate
            resolution_rate = (resolved_issues / total_issues * 100) if total_issues > 0 else 0
            
            # Get average resolution time
            cursor.execute(f"""
                SELECT AVG(
                    (julianday(resolved_at) - julianday(created_at)) * 24
                ) FROM quality_issues 
                {where_clause} AND status = 'resolved' AND resolved_at IS NOT NULL
            """, params)
            avg_resolution_time = cursor.fetchone()[0] or 0
            
            # Get issues by severity
            cursor.execute(f"""
                SELECT severity, COUNT(*) FROM quality_issues 
                {where_clause} GROUP BY severity
            """, params)
            issues_by_severity = dict(cursor.fetchall())
            
            # Get issues by type
            cursor.execute(f"""
                SELECT issue_type, COUNT(*) FROM quality_issues 
                {where_clause} GROUP BY issue_type
            """, params)
            issues_by_type = dict(cursor.fetchall())
            
            # Calculate auto-fix success rate
            # Need to modify where_clause to use qi. prefix for quality_issues table
            qi_where_clause = where_clause.replace("created_at", "qi.created_at").replace("project_id", "qi.project_id")
            cursor.execute(f"""
                SELECT 
                    COUNT(CASE WHEN afr.success = 1 THEN 1 END) as successful,
                    COUNT(*) as total
                FROM quality_issues qi
                LEFT JOIN auto_fix_results afr ON qi.id = afr.issue_id
                {qi_where_clause} AND qi.auto_fixable = 1
            """, params)
            auto_fix_result = cursor.fetchone()
            auto_fix_success_rate = (auto_fix_result[0] / auto_fix_result[1] * 100) if auto_fix_result[1] > 0 else 0
            
            return IssueResolutionMetrics(
                total_issues=total_issues,
                resolved_issues=resolved_issues,
                average_resolution_time=avg_resolution_time,
                resolution_rate=resolution_rate,
                issues_by_severity=issues_by_severity,
                issues_by_type=issues_by_type,
                auto_fix_success_rate=auto_fix_success_rate
            )
            
        finally:
            conn.close()
    
    async def escalate_stale_issues(self, hours_threshold: int = 24) -> List[QualityIssue]:
        """
        Identify and escalate issues that have been open too long.
        
        Args:
            hours_threshold: Hours after which to escalate
            
        Returns:
            List of escalated issues
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            threshold_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
            
            cursor.execute("""
                SELECT * FROM quality_issues 
                WHERE status = 'open' 
                AND created_at < ?
                AND severity IN ('high', 'critical')
            """, (threshold_time.isoformat(),))
            
            stale_issues = [self._row_to_issue(row) for row in cursor.fetchall()]
            
            # Log escalations
            for issue in stale_issues:
                self.logger.warning(
                    f"Escalating stale issue {issue.id}: {issue.description} "
                    f"(open for {hours_threshold}+ hours)"
                )
            
            return stale_issues
            
        finally:
            conn.close()
    
    async def bulk_update_issues(self, issue_ids: List[str], 
                               updates: QualityIssueUpdate) -> int:
        """
        Update multiple issues at once.
        
        Args:
            issue_ids: List of issue IDs to update
            updates: Update data to apply
            
        Returns:
            Number of issues updated
        """
        if not issue_ids:
            return 0
        
        updated_count = 0
        
        for issue_id in issue_ids:
            try:
                result = await self.update_issue(issue_id, updates)
                if result:
                    updated_count += 1
            except Exception as e:
                self.logger.error(f"Failed to update issue {issue_id}: {e}")
        
        return updated_count
    
    async def delete_issue(self, issue_id: str) -> bool:
        """
        Delete a quality issue (use with caution).
        
        Args:
            issue_id: ID of issue to delete
            
        Returns:
            True if successfully deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete related auto-fix results first
            cursor.execute("DELETE FROM auto_fix_results WHERE issue_id = ?", (issue_id,))
            
            # Delete the issue
            cursor.execute("DELETE FROM quality_issues WHERE id = ?", (issue_id,))
            
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.info(f"Deleted quality issue {issue_id}")
            
            return deleted
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to delete quality issue {issue_id}: {e}")
            raise
        finally:
            conn.close()