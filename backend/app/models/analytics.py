"""
Analytics Pydantic Models

Defines request and response models for analytics and reporting endpoints.
Includes dashboard metrics, trend analysis, and executive reporting schemas.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

# Enums for structured data
class ReportType(str, Enum):
    """Available report types"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class RiskLevel(str, Enum):
    """Risk level categorization"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class TrendDirection(str, Enum):
    """Trend direction indicators"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"

class AnalyticsPeriod(str, Enum):
    """Time periods for analytics"""
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    LAST_YEAR = "1y"

# Request Models
class DashboardMetricsRequest(BaseModel):
    """Request model for dashboard metrics"""
    period_days: Optional[int] = Field(default=30, ge=1, le=365, description="Number of days to analyze")
    include_trends: Optional[bool] = Field(default=True, description="Include trend analysis")
    include_predictions: Optional[bool] = Field(default=False, description="Include risk predictions")

class ProjectAnalyticsRequest(BaseModel):
    """Request model for detailed project analytics"""
    project_id: int = Field(..., description="Project ID to analyze")
    include_predictions: Optional[bool] = Field(default=True, description="Include risk predictions")
    include_recommendations: Optional[bool] = Field(default=True, description="Include recommendations analysis")

class TrendAnalysisRequest(BaseModel):
    """Request model for trend analysis"""
    period: AnalyticsPeriod = Field(default=AnalyticsPeriod.LAST_30_DAYS, description="Analysis period")
    metrics: List[str] = Field(default=["risk_score", "project_count"], description="Metrics to analyze")
    granularity: Literal["daily", "weekly", "monthly"] = Field(default="daily", description="Data granularity")

class ExecutiveReportRequest(BaseModel):
    """Request model for executive reports"""
    report_type: ReportType = Field(default=ReportType.MONTHLY, description="Type of report to generate")
    include_charts: Optional[bool] = Field(default=True, description="Include chart data")
    format: Literal["json", "pdf"] = Field(default="json", description="Report format")
    sections: Optional[List[str]] = Field(
        default=["summary", "metrics", "trends", "recommendations"], 
        description="Report sections to include"
    )

class RiskPredictionRequest(BaseModel):
    """Request model for AI risk predictions"""
    project_ids: Optional[List[int]] = Field(default=None, description="Specific projects to analyze (None for all)")
    prediction_horizon_days: Optional[int] = Field(default=30, ge=7, le=90, description="Prediction time horizon")
    confidence_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence level")

# Response Models - Basic Components
class MetricValue(BaseModel):
    """Basic metric value with metadata"""
    value: Union[int, float, str]
    change: Optional[float] = Field(default=None, description="Percentage change from previous period")
    trend: Optional[TrendDirection] = Field(default=None, description="Trend direction")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TrendPoint(BaseModel):
    """Single point in a trend analysis"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    value: float = Field(..., description="Metric value")
    count: Optional[int] = Field(default=None, description="Count if applicable")

class RiskDistribution(BaseModel):
    """Risk level distribution"""
    low: int = Field(default=0, description="Count of low-risk items")
    medium: int = Field(default=0, description="Count of medium-risk items")
    high: int = Field(default=0, description="Count of high-risk items")
    
    @property
    def total(self) -> int:
        return self.low + self.medium + self.high

class ThreatTechnique(BaseModel):
    """Common threat technique with frequency"""
    technique: str = Field(..., description="MITRE ATT&CK technique")
    count: int = Field(..., description="Frequency of occurrence")
    risk_level: Optional[RiskLevel] = Field(default=None, description="Associated risk level")

# Response Models - Complex Components
class ProjectMetrics(BaseModel):
    """Project-related metrics"""
    total_projects: int = Field(..., description="Total number of projects")
    recent_projects: int = Field(..., description="Recently created projects")
    active_projects: int = Field(..., description="Currently active projects")
    completion_rate: float = Field(..., description="Project completion rate percentage")
    status_distribution: Dict[str, int] = Field(..., description="Distribution by project status")

class RiskMetrics(BaseModel):
    """Risk assessment metrics"""
    average_risk_score: float = Field(..., ge=0.0, le=1.0, description="Average risk score")
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score")
    risk_distribution: RiskDistribution = Field(..., description="Risk level distribution")
    high_risk_projects: int = Field(..., description="Count of high-risk projects")
    risk_trend: TrendDirection = Field(..., description="Overall risk trend")

class ThreatMetrics(BaseModel):
    """Threat landscape metrics"""
    total_attack_paths: int = Field(..., description="Total attack paths identified")
    high_priority_paths: int = Field(..., description="High-priority attack paths")
    total_recommendations: int = Field(..., description="Total recommendations generated")
    critical_recommendations: int = Field(..., description="Critical recommendations count")
    common_techniques: List[ThreatTechnique] = Field(..., description="Most common attack techniques")
    threat_coverage: float = Field(..., description="MITRE ATT&CK coverage percentage")

class PerformanceMetrics(BaseModel):
    """System performance metrics"""
    average_analysis_time_minutes: float = Field(..., description="Average analysis completion time")
    success_rate: float = Field(..., description="Analysis success rate percentage")
    total_analyses: int = Field(..., description="Total analyses performed")
    successful_analyses: int = Field(..., description="Successfully completed analyses")
    system_efficiency: float = Field(..., description="Overall system efficiency score")

class TrendAnalysis(BaseModel):
    """Trend analysis results"""
    project_creation_trend: List[TrendPoint] = Field(..., description="Project creation trend over time")
    risk_score_trend: List[TrendPoint] = Field(..., description="Risk score trend over time")
    trend_analysis: Dict[str, str] = Field(..., description="Trend analysis insights")

class ExecutiveSummary(BaseModel):
    """Executive summary insights"""
    overall_status: str = Field(..., description="Overall security status")
    status_color: str = Field(..., description="Status indicator color")
    health_score: float = Field(..., ge=0.0, le=100.0, description="Overall health score")
    key_insight: str = Field(..., description="Key business insight")
    priority_action: str = Field(..., description="Priority action item")

# Main Response Models
class DashboardMetricsResponse(BaseModel):
    """Dashboard metrics response"""
    period: str = Field(..., description="Analysis period description")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    project_metrics: ProjectMetrics = Field(..., description="Project-related metrics")
    risk_metrics: RiskMetrics = Field(..., description="Risk assessment metrics")
    threat_metrics: ThreatMetrics = Field(..., description="Threat landscape metrics")
    performance_metrics: PerformanceMetrics = Field(..., description="System performance metrics")
    trends: TrendAnalysis = Field(..., description="Trend analysis data")
    summary: ExecutiveSummary = Field(..., description="Executive summary")

class ProjectAnalyticsResponse(BaseModel):
    """Detailed project analytics response"""
    project_info: Dict[str, Any] = Field(..., description="Project information")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment details")
    attack_paths: List[Dict[str, Any]] = Field(..., description="Identified attack paths")
    recommendations: List[Dict[str, Any]] = Field(..., description="Security recommendations")
    threat_intelligence: Optional[Dict[str, Any]] = Field(default=None, description="Threat intelligence data")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class TrendAnalysisResponse(BaseModel):
    """Trend analysis response"""
    period: str = Field(..., description="Analysis period")
    metrics: List[str] = Field(..., description="Analyzed metrics")
    trends: Dict[str, List[TrendPoint]] = Field(..., description="Trend data by metric")
    insights: Dict[str, str] = Field(..., description="Generated insights")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class StrategicRecommendation(BaseModel):
    """Strategic recommendation item"""
    priority: str = Field(..., description="Recommendation priority level")
    category: str = Field(..., description="Recommendation category")
    recommendation: str = Field(..., description="Recommendation text")
    impact: str = Field(..., description="Expected impact")

class ActionItem(BaseModel):
    """Action item for leadership"""
    action: str = Field(..., description="Action description")
    owner: str = Field(..., description="Responsible party")
    timeline: str = Field(..., description="Expected timeline")
    priority: str = Field(..., description="Priority level")

class RiskOutlook(BaseModel):
    """Risk outlook and predictions"""
    short_term: str = Field(..., description="Short-term risk outlook")
    long_term: str = Field(..., description="Long-term risk outlook")
    confidence: str = Field(..., description="Prediction confidence level")

class IndustryComparison(BaseModel):
    """Industry benchmarking data"""
    industry_average_risk: float = Field(..., description="Industry average risk score")
    industry_completion_rate: float = Field(..., description="Industry average completion rate")
    peer_comparison: str = Field(..., description="Peer comparison result")
    benchmark_date: datetime = Field(..., description="Benchmark data timestamp")

class ExecutiveReportResponse(BaseModel):
    """Executive report response"""
    report_type: str = Field(..., description="Report type")
    reporting_period: str = Field(..., description="Reporting period")
    generated_at: datetime = Field(..., description="Generation timestamp")
    executive_summary: ExecutiveSummary = Field(..., description="Executive summary")
    key_metrics: DashboardMetricsResponse = Field(..., description="Key performance metrics")
    strategic_insights: List[StrategicRecommendation] = Field(..., description="Strategic recommendations")
    industry_comparison: IndustryComparison = Field(..., description="Industry comparison")
    action_items: List[ActionItem] = Field(..., description="Priority action items")
    risk_outlook: RiskOutlook = Field(..., description="Risk outlook and predictions")

class RiskPredictionResult(BaseModel):
    """Individual risk prediction result"""
    project_id: int = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name")
    current_risk_score: float = Field(..., ge=0.0, le=1.0, description="Current risk score")
    predicted_risk_score: float = Field(..., ge=0.0, le=1.0, description="Predicted future risk score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    risk_factors: List[str] = Field(..., description="Key risk factors identified")
    recommendations: List[str] = Field(..., description="Risk mitigation recommendations")

class RiskPredictionResponse(BaseModel):
    """AI risk prediction response"""
    prediction_horizon_days: int = Field(..., description="Prediction time horizon")
    generated_at: datetime = Field(..., description="Prediction generation timestamp")
    total_projects_analyzed: int = Field(..., description="Number of projects analyzed")
    high_confidence_predictions: int = Field(..., description="Count of high-confidence predictions")
    predictions: List[RiskPredictionResult] = Field(..., description="Individual project predictions")
    summary_insights: Dict[str, str] = Field(..., description="Summary insights and trends")

# Error Response Models
class AnalyticsErrorResponse(BaseModel):
    """Error response for analytics endpoints"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Export configuration for report generation
class ReportExportConfig(BaseModel):
    """Configuration for report exports"""
    format: Literal["json", "pdf", "csv"] = Field(default="json", description="Export format")
    include_charts: bool = Field(default=True, description="Include chart data")
    template: Optional[str] = Field(default=None, description="Report template name")
    custom_branding: Optional[Dict[str, str]] = Field(default=None, description="Custom branding options")

# Caching configuration
class AnalyticsCacheConfig(BaseModel):
    """Analytics caching configuration"""
    cache_duration_minutes: int = Field(default=15, ge=1, le=1440, description="Cache duration in minutes")
    use_cache: bool = Field(default=True, description="Whether to use caching")
    cache_key_prefix: str = Field(default="analytics", description="Cache key prefix")

    @validator('cache_duration_minutes')
    def validate_cache_duration(cls, v):
        if v < 1 or v > 1440:  # Max 24 hours
            raise ValueError('Cache duration must be between 1 and 1440 minutes')
        return v
