"""
Core data models for code quality tracking and automated fixes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import uuid


class IssueType(str, Enum):
    """Types of code quality issues."""
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DUPLICATION = "duplication"


class Severity(str, Enum):
    """Severity levels for quality issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueStatus(str, Enum):
    """Status of quality issues."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    WONT_FIX = "wont_fix"


class FixType(str, Enum):
    """Types of automatic fixes."""
    FORMATTING = "formatting"
    IMPORTS = "imports"
    STYLE = "style"
    SIMPLE_REFACTOR = "simple_refactor"
    SECURITY_FIX = "security_fix"
    PERFORMANCE_FIX = "performance_fix"


class SafetyLevel(str, Enum):
    """Safety levels for automatic fixes."""
    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"


@dataclass
class QualityIssue:
    """Represents a code quality issue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    file_path: str = ""
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    issue_type: IssueType = IssueType.STYLE
    severity: Severity = Severity.MEDIUM
    category: str = ""
    description: str = ""
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    status: IssueStatus = IssueStatus.OPEN
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'issue_type': self.issue_type.value,
            'severity': self.severity.value,
            'category': self.category,
            'description': self.description,
            'suggested_fix': self.suggested_fix,
            'auto_fixable': self.auto_fixable,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'resolution_method': self.resolution_method
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityIssue':
        """Create instance from dictionary."""
        return cls(
            id=data['id'],
            project_id=data['project_id'],
            file_path=data['file_path'],
            line_number=data.get('line_number'),
            column_number=data.get('column_number'),
            issue_type=IssueType(data['issue_type']),
            severity=Severity(data['severity']),
            category=data['category'],
            description=data['description'],
            suggested_fix=data.get('suggested_fix'),
            auto_fixable=data.get('auto_fixable', False),
            status=IssueStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None,
            resolved_by=data.get('resolved_by'),
            resolution_method=data.get('resolution_method')
        )


@dataclass
class QualityMetrics:
    """Represents quality metrics for a project at a point in time."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    code_coverage: Optional[float] = None
    cyclomatic_complexity: Optional[float] = None
    maintainability_index: Optional[float] = None
    technical_debt_ratio: Optional[float] = None
    test_quality_score: Optional[float] = None
    security_score: Optional[float] = None
    performance_score: Optional[float] = None
    lines_of_code: Optional[int] = None
    duplicate_code_ratio: Optional[float] = None
    comment_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'timestamp': self.timestamp.isoformat(),
            'code_coverage': self.code_coverage,
            'cyclomatic_complexity': self.cyclomatic_complexity,
            'maintainability_index': self.maintainability_index,
            'technical_debt_ratio': self.technical_debt_ratio,
            'test_quality_score': self.test_quality_score,
            'security_score': self.security_score,
            'performance_score': self.performance_score,
            'lines_of_code': self.lines_of_code,
            'duplicate_code_ratio': self.duplicate_code_ratio,
            'comment_ratio': self.comment_ratio
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityMetrics':
        """Create instance from dictionary."""
        return cls(
            id=data['id'],
            project_id=data['project_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            code_coverage=data.get('code_coverage'),
            cyclomatic_complexity=data.get('cyclomatic_complexity'),
            maintainability_index=data.get('maintainability_index'),
            technical_debt_ratio=data.get('technical_debt_ratio'),
            test_quality_score=data.get('test_quality_score'),
            security_score=data.get('security_score'),
            performance_score=data.get('performance_score'),
            lines_of_code=data.get('lines_of_code'),
            duplicate_code_ratio=data.get('duplicate_code_ratio'),
            comment_ratio=data.get('comment_ratio')
        )


@dataclass
class AutoFixResult:
    """Represents the result of an automatic fix application."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issue_id: str = ""
    project_id: str = ""
    file_path: str = ""
    fix_type: FixType = FixType.FORMATTING
    original_content: Optional[str] = None
    fixed_content: Optional[str] = None
    success: bool = False
    error_message: Optional[str] = None
    applied_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    applied_by: Optional[str] = None
    rollback_id: Optional[str] = None
    is_rolled_back: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            'project_id': self.project_id,
            'file_path': self.file_path,
            'fix_type': self.fix_type.value,
            'original_content': self.original_content,
            'fixed_content': self.fixed_content,
            'success': self.success,
            'error_message': self.error_message,
            'applied_at': self.applied_at.isoformat(),
            'applied_by': self.applied_by,
            'rollback_id': self.rollback_id,
            'is_rolled_back': self.is_rolled_back
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutoFixResult':
        """Create instance from dictionary."""
        return cls(
            id=data['id'],
            issue_id=data['issue_id'],
            project_id=data['project_id'],
            file_path=data['file_path'],
            fix_type=FixType(data['fix_type']),
            original_content=data.get('original_content'),
            fixed_content=data.get('fixed_content'),
            success=data['success'],
            error_message=data.get('error_message'),
            applied_at=datetime.fromisoformat(data['applied_at']),
            applied_by=data.get('applied_by'),
            rollback_id=data.get('rollback_id'),
            is_rolled_back=data.get('is_rolled_back', False)
        )


# Pydantic models for API requests/responses
class QualityIssueCreate(BaseModel):
    """Model for creating quality issues via API."""
    project_id: str
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    issue_type: IssueType
    severity: Severity
    category: str
    description: str
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False


class QualityIssueUpdate(BaseModel):
    """Model for updating quality issues via API."""
    status: Optional[IssueStatus] = None
    resolved_by: Optional[str] = None
    resolution_method: Optional[str] = None


class QualityMetricsCreate(BaseModel):
    """Model for creating quality metrics via API."""
    project_id: str
    code_coverage: Optional[float] = Field(None, ge=0, le=100)
    cyclomatic_complexity: Optional[float] = Field(None, ge=0)
    maintainability_index: Optional[float] = Field(None, ge=0, le=100)
    technical_debt_ratio: Optional[float] = Field(None, ge=0, le=1)
    test_quality_score: Optional[float] = Field(None, ge=0, le=100)
    security_score: Optional[float] = Field(None, ge=0, le=100)
    performance_score: Optional[float] = Field(None, ge=0, le=100)
    lines_of_code: Optional[int] = Field(None, ge=0)
    duplicate_code_ratio: Optional[float] = Field(None, ge=0, le=1)
    comment_ratio: Optional[float] = Field(None, ge=0, le=1)


class AutoFixRequest(BaseModel):
    """Model for requesting automatic fixes."""
    issue_ids: List[str]
    fix_types: Optional[List[FixType]] = None
    safety_level: SafetyLevel = SafetyLevel.CONSERVATIVE
    backup_enabled: bool = True


class QualityStandard(BaseModel):
    """Model for quality standards configuration."""
    id: Optional[str] = None
    project_id: Optional[str] = None
    standard_name: str
    standard_type: str
    configuration: Dict[str, Any]
    is_active: bool = True


class QualityScanConfig(BaseModel):
    """Model for quality scan configuration."""
    project_id: str
    scan_type: str
    file_patterns: Optional[List[str]] = None
    excluded_patterns: Optional[List[str]] = None
    quality_standards: Optional[List[str]] = None
    auto_fix_enabled: bool = False
    safety_level: SafetyLevel = SafetyLevel.CONSERVATIVE


@dataclass
class QualityTrend:
    """Represents a quality trend data point."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trend_direction: Optional[str] = None  # 'up', 'down', 'stable'
    change_percentage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'timestamp': self.timestamp.isoformat(),
            'trend_direction': self.trend_direction,
            'change_percentage': self.change_percentage
        }