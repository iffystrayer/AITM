"""
Pydantic schemas for Threat Intelligence API data validation
"""

from datetime import datetime
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums
class ThreatType(str, Enum):
    IOC = "ioc"
    TTP = "ttp"
    MALWARE = "malware"
    VULNERABILITY = "vulnerability"
    CAMPAIGN = "campaign"
    THREAT_ACTOR = "threat_actor"
    INFRASTRUCTURE = "infrastructure"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedFormat(str, Enum):
    STIX = "stix"
    JSON = "json"
    XML = "xml"
    CSV = "csv"


class CorrelationType(str, Enum):
    ASSET_MATCH = "asset_match"
    TECHNIQUE_MATCH = "technique_match"
    INFRASTRUCTURE_MATCH = "infrastructure_match"
    BEHAVIORAL_MATCH = "behavioral_match"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


# Threat Feed Schemas
class ThreatFeedBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=1000)
    format: FeedFormat
    polling_interval: int = Field(default=300, ge=60, le=86400)  # 1 minute to 24 hours
    rate_limit: int = Field(default=100, ge=1, le=10000)
    is_active: bool = True
    configuration: Optional[Dict[str, Any]] = None


class ThreatFeedCreate(ThreatFeedBase):
    api_key: Optional[str] = None


class ThreatFeedUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1, max_length=1000)
    api_key: Optional[str] = None
    format: Optional[FeedFormat] = None
    polling_interval: Optional[int] = Field(None, ge=60, le=86400)
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    is_active: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None


class ThreatFeedResponse(ThreatFeedBase):
    id: int
    last_update: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count: int
    total_indicators: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Threat Indicator Schemas
class ThreatIndicatorBase(BaseModel):
    type: ThreatType
    value: str = Field(..., min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    kill_chain_phases: Optional[List[str]] = None
    source: str = Field(..., min_length=1, max_length=255)
    source_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ThreatIndicatorCreate(ThreatIndicatorBase):
    external_id: Optional[str] = None
    feed_id: int
    first_seen: datetime
    last_seen: datetime
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None


class ThreatIndicatorUpdate(BaseModel):
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    severity: Optional[SeverityLevel] = None
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_false_positive: Optional[bool] = None
    last_seen: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class ThreatIndicatorResponse(ThreatIndicatorBase):
    id: int
    external_id: Optional[str] = None
    feed_id: int
    first_seen: datetime
    last_seen: datetime
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool
    is_false_positive: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Threat Relationship Schemas
class ThreatRelationshipCreate(BaseModel):
    source_indicator_id: int
    target_indicator_id: int
    relationship_type: str = Field(..., min_length=1, max_length=100)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    description: Optional[str] = None


class ThreatRelationshipResponse(ThreatRelationshipCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Threat Correlation Schemas
class ThreatCorrelationCreate(BaseModel):
    threat_indicator_id: int
    project_id: int
    asset_id: Optional[int] = None
    correlation_type: CorrelationType
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    description: Optional[str] = None
    matched_attributes: Optional[Dict[str, Any]] = None


class ThreatCorrelationUpdate(BaseModel):
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    description: Optional[str] = None
    is_reviewed: Optional[bool] = None
    is_false_positive: Optional[bool] = None
    analyst_notes: Optional[str] = None


class ThreatCorrelationResponse(ThreatCorrelationCreate):
    id: int
    is_reviewed: bool
    is_false_positive: bool
    analyst_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Threat Alert Schemas
class ThreatAlertCreate(BaseModel):
    threat_indicator_id: int
    project_id: Optional[int] = None
    alert_type: str = Field(..., min_length=1, max_length=100)
    severity: SeverityLevel
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ThreatAlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    assigned_to: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class ThreatAlertResponse(ThreatAlertCreate):
    id: int
    status: AlertStatus
    assigned_to: Optional[str] = None
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Search and Query Schemas
class ThreatSearchQuery(BaseModel):
    query: Optional[str] = None
    threat_types: Optional[List[ThreatType]] = None
    severity_levels: Optional[List[SeverityLevel]] = None
    sources: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    confidence_min: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_max: Optional[float] = Field(None, ge=0.0, le=1.0)
    first_seen_after: Optional[datetime] = None
    first_seen_before: Optional[datetime] = None
    is_active: Optional[bool] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ThreatSearchResult(BaseModel):
    indicators: List[ThreatIndicatorResponse]
    total_count: int
    query: ThreatSearchQuery


# Dashboard and Analytics Schemas
class ThreatIntelligenceSummary(BaseModel):
    total_indicators: int
    active_indicators: int
    indicators_by_type: Dict[str, int]
    indicators_by_severity: Dict[str, int]
    recent_indicators_count: int  # Last 24 hours
    feed_status: List[Dict[str, Any]]


class ThreatTrendData(BaseModel):
    date: datetime
    indicator_count: int
    severity_breakdown: Dict[str, int]


class ThreatAnalytics(BaseModel):
    summary: ThreatIntelligenceSummary
    trends: List[ThreatTrendData]
    top_sources: List[Dict[str, Union[str, int]]]
    correlation_stats: Dict[str, int]


# Feed Processing Schemas
class FeedProcessingStatus(BaseModel):
    feed_id: int
    feed_name: str
    status: str  # idle, processing, error, completed
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    indicators_processed: int
    errors: List[str] = []


class FeedProcessingResult(BaseModel):
    feed_id: int
    indicators_added: int
    indicators_updated: int
    indicators_skipped: int
    errors: List[str] = []
    processing_time: float
    completed_at: datetime


# Export Schemas
class ThreatExportRequest(BaseModel):
    format: str = Field(..., pattern="^(json|csv|stix|xml)$")
    query: Optional[ThreatSearchQuery] = None
    include_relationships: bool = False
    include_raw_data: bool = False


class ThreatExportResponse(BaseModel):
    export_id: str
    format: str
    status: str  # pending, processing, completed, failed
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


# Configuration Schemas
class ThreatIntelligenceConfig(BaseModel):
    auto_correlation_enabled: bool = True
    correlation_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    alert_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    data_retention_days: int = Field(default=90, ge=1, le=3650)
    max_indicators_per_feed: int = Field(default=100000, ge=1000)
    processing_batch_size: int = Field(default=1000, ge=100, le=10000)


# Validation Schemas
class ThreatIndicatorValidation(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    normalized_value: Optional[str] = None


# Bulk Operations Schemas
class BulkThreatIndicatorCreate(BaseModel):
    indicators: List[ThreatIndicatorCreate] = Field(..., max_items=1000)


class BulkThreatIndicatorResponse(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: List[Dict[str, Any]] = []


# WebSocket Message Schemas
class ThreatUpdateMessage(BaseModel):
    message_type: str = Field(..., pattern="^(new_indicator|updated_indicator|new_alert|correlation_found)$")
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ThreatSubscription(BaseModel):
    project_ids: Optional[List[int]] = None
    threat_types: Optional[List[ThreatType]] = None
    severity_levels: Optional[List[SeverityLevel]] = None
    sources: Optional[List[str]] = None