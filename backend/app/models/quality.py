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


class TestType(str, Enum):
    """Types of tests."""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    E2E = "e2e"
    SMOKE = "smoke"
    REGRESSION = "regression"


class TestStatus(str, Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    FLAKY = "flaky"


@dataclass
class TestResult:
    """Represents a test execution result."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    test_file: str = ""
    test_name: str = ""
    test_type: TestType = TestType.UNIT
    status: TestStatus = TestStatus.PASSED
    execution_time: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    coverage_percentage: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'test_file': self.test_file,
            'test_name': self.test_name,
            'test_type': self.test_type.value,
            'status': self.status.value,
            'execution_time': self.execution_time,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'coverage_percentage': self.coverage_percentage,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TestCoverageData:
    """Represents test coverage data."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    file_path: str = ""
    lines_total: int = 0
    lines_covered: int = 0
    lines_missed: int = 0
    coverage_percentage: float = 0.0
    branches_total: int = 0
    branches_covered: int = 0
    branch_coverage_percentage: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'file_path': self.file_path,
            'lines_total': self.lines_total,
            'lines_covered': self.lines_covered,
            'lines_missed': self.lines_missed,
            'coverage_percentage': self.coverage_percentage,
            'branches_total': self.branches_total,
            'branches_covered': self.branches_covered,
            'branch_coverage_percentage': self.branch_coverage_percentage,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class FlakyTestData:
    """Represents flaky test detection data."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    test_file: str = ""
    test_name: str = ""
    total_runs: int = 0
    failed_runs: int = 0
    flakiness_score: float = 0.0  # 0.0 = stable, 1.0 = completely flaky
    last_failure: Optional[datetime] = None
    failure_patterns: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'test_file': self.test_file,
            'test_name': self.test_name,
            'total_runs': self.total_runs,
            'failed_runs': self.failed_runs,
            'flakiness_score': self.flakiness_score,
            'last_failure': self.last_failure.isoformat() if self.last_failure else None,
            'failure_patterns': self.failure_patterns,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TestQualityMetrics:
    """Represents comprehensive test quality metrics."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    total_tests: int = 0
    passing_tests: int = 0
    failing_tests: int = 0
    skipped_tests: int = 0
    flaky_tests: int = 0
    test_success_rate: float = 0.0
    average_execution_time: float = 0.0
    code_coverage: float = 0.0
    branch_coverage: float = 0.0
    test_density: float = 0.0  # tests per line of code
    assertion_density: float = 0.0  # assertions per test
    test_maintainability_score: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'total_tests': self.total_tests,
            'passing_tests': self.passing_tests,
            'failing_tests': self.failing_tests,
            'skipped_tests': self.skipped_tests,
            'flaky_tests': self.flaky_tests,
            'test_success_rate': self.test_success_rate,
            'average_execution_time': self.average_execution_time,
            'code_coverage': self.code_coverage,
            'branch_coverage': self.branch_coverage,
            'test_density': self.test_density,
            'assertion_density': self.assertion_density,
            'test_maintainability_score': self.test_maintainability_score,
            'timestamp': self.timestamp.isoformat()
        }


class AlertType(str, Enum):
    """Types of quality alerts."""
    THRESHOLD_VIOLATION = "threshold_violation"
    TREND_DEGRADATION = "trend_degradation"
    REGRESSION = "regression"
    IMPROVEMENT = "improvement"
    CRITICAL_ISSUE = "critical_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class AlertSeverity(str, Enum):
    """Severity levels for quality alerts."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, Enum):
    """Status of quality alerts."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


@dataclass
class QualityAlert:
    """Represents a quality alert."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    alert_type: AlertType = AlertType.THRESHOLD_VIOLATION
    severity: AlertSeverity = AlertSeverity.WARNING
    status: AlertStatus = AlertStatus.ACTIVE
    metric_name: str = ""
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    previous_value: Optional[float] = None
    regression_percentage: Optional[float] = None
    trend_direction: Optional[str] = None
    message: str = ""
    description: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'status': self.status.value,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'previous_value': self.previous_value,
            'regression_percentage': self.regression_percentage,
            'trend_direction': self.trend_direction,
            'message': self.message,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved': self.resolved
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityAlert':
        """Create instance from dictionary."""
        return cls(
            id=data['id'],
            project_id=data['project_id'],
            alert_type=AlertType(data['alert_type']),
            severity=AlertSeverity(data['severity']),
            status=AlertStatus(data['status']),
            metric_name=data['metric_name'],
            current_value=data.get('current_value'),
            threshold_value=data.get('threshold_value'),
            previous_value=data.get('previous_value'),
            regression_percentage=data.get('regression_percentage'),
            trend_direction=data.get('trend_direction'),
            message=data['message'],
            description=data.get('description'),
            created_at=datetime.fromisoformat(data['created_at']),
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None,
            resolved_by=data.get('resolved_by'),
            acknowledged_at=datetime.fromisoformat(data['acknowledged_at']) if data.get('acknowledged_at') else None,
            acknowledged_by=data.get('acknowledged_by'),
            resolved=data.get('resolved', False)
        )


@dataclass
class NotificationChannel:
    """Represents a notification channel configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    channel_type: str = ""  # email, slack, webhook, websocket
    configuration: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    alert_types: List[AlertType] = field(default_factory=list)
    severity_levels: List[AlertSeverity] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'id': self.id,
            'name': self.name,
            'channel_type': self.channel_type,
            'configuration': self.configuration,
            'enabled': self.enabled,
            'alert_types': [at.value for at in self.alert_types],
            'severity_levels': [sl.value for sl in self.severity_levels]
        }


class QualityAlertCreate(BaseModel):
    """Model for creating quality alerts via API."""
    project_id: str
    alert_type: AlertType
    severity: AlertSeverity
    metric_name: str
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    message: str
    description: Optional[str] = None


class QualityAlertUpdate(BaseModel):
    """Model for updating quality alerts via API."""
    status: Optional[AlertStatus] = None
    resolved_by: Optional[str] = None
    acknowledged_by: Optional[str] = None


class NotificationChannelCreate(BaseModel):
    """Model for creating notification channels via API."""
    name: str
    channel_type: str
    configuration: Dict[str, Any]
    enabled: bool = True
    alert_types: List[AlertType] = []
    severity_levels: List[AlertSeverity] = []