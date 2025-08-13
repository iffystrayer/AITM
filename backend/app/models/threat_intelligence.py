"""
Threat Intelligence data models
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base


class ThreatType(str, Enum):
    """Threat indicator types"""
    IOC = "ioc"  # Indicator of Compromise
    TTP = "ttp"  # Tactics, Techniques, and Procedures
    MALWARE = "malware"
    VULNERABILITY = "vulnerability"
    CAMPAIGN = "campaign"
    THREAT_ACTOR = "threat_actor"
    INFRASTRUCTURE = "infrastructure"


class SeverityLevel(str, Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedFormat(str, Enum):
    """Threat feed formats"""
    STIX = "stix"
    JSON = "json"
    XML = "xml"
    CSV = "csv"


class CorrelationType(str, Enum):
    """Threat correlation types"""
    ASSET_MATCH = "asset_match"
    TECHNIQUE_MATCH = "technique_match"
    INFRASTRUCTURE_MATCH = "infrastructure_match"
    BEHAVIORAL_MATCH = "behavioral_match"


class ThreatFeed(Base):
    """Threat intelligence feed configuration"""
    __tablename__ = "threat_feeds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    url = Column(String(1000), nullable=False)
    api_key = Column(String(500))  # Encrypted API key
    format = Column(String(50), nullable=False)  # STIX, JSON, XML, CSV
    polling_interval = Column(Integer, default=300)  # seconds
    rate_limit = Column(Integer, default=100)  # requests per hour
    is_active = Column(Boolean, default=True)
    last_update = Column(DateTime)
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    total_indicators = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuration JSON for feed-specific settings
    configuration = Column(JSON)
    
    # Relationships
    indicators = relationship("ThreatIndicator", back_populates="feed")


class ThreatIndicator(Base):
    """Threat intelligence indicators"""
    __tablename__ = "threat_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255))  # ID from external feed
    feed_id = Column(Integer, ForeignKey("threat_feeds.id"), nullable=False)
    
    # Core indicator data
    type = Column(String(50), nullable=False)  # IOC, TTP, Malware, etc.
    value = Column(Text, nullable=False)  # The actual indicator value
    confidence = Column(Float, default=0.5)  # 0.0 to 1.0
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Metadata
    title = Column(String(500))
    description = Column(Text)
    tags = Column(JSON)  # List of tags
    kill_chain_phases = Column(JSON)  # MITRE ATT&CK kill chain phases
    
    # Temporal data
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    
    # Source attribution
    source = Column(String(255), nullable=False)
    source_confidence = Column(Float, default=0.5)
    
    # Processing metadata
    is_active = Column(Boolean, default=True)
    is_false_positive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Raw data from feed (for debugging and reprocessing)
    raw_data = Column(JSON)
    
    # Relationships
    feed = relationship("ThreatFeed", back_populates="indicators")
    relationships = relationship("ThreatRelationship", 
                               foreign_keys="ThreatRelationship.source_indicator_id",
                               back_populates="source_indicator")
    correlations = relationship("ThreatCorrelation", back_populates="threat_indicator")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_threat_indicators_type_severity', 'type', 'severity'),
        Index('idx_threat_indicators_first_seen', 'first_seen'),
        Index('idx_threat_indicators_source', 'source'),
        Index('idx_threat_indicators_active', 'is_active'),
        Index('idx_threat_indicators_value_hash', 'value'),  # For deduplication
    )


class ThreatRelationship(Base):
    """Relationships between threat indicators"""
    __tablename__ = "threat_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    source_indicator_id = Column(Integer, ForeignKey("threat_indicators.id"), nullable=False)
    target_indicator_id = Column(Integer, ForeignKey("threat_indicators.id"), nullable=False)
    
    relationship_type = Column(String(100), nullable=False)  # uses, indicates, targets, etc.
    confidence = Column(Float, default=0.5)
    description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_indicator = relationship("ThreatIndicator", 
                                  foreign_keys=[source_indicator_id],
                                  back_populates="relationships")
    target_indicator = relationship("ThreatIndicator", foreign_keys=[target_indicator_id])


class ThreatCorrelation(Base):
    """Correlations between threat indicators and AITM projects"""
    __tablename__ = "threat_correlations"
    
    id = Column(Integer, primary_key=True, index=True)
    threat_indicator_id = Column(Integer, ForeignKey("threat_indicators.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"))  # Optional specific asset
    
    # Correlation metadata
    correlation_type = Column(String(100), nullable=False)
    relevance_score = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence = Column(Float, default=0.5)
    
    # Context
    description = Column(Text)
    matched_attributes = Column(JSON)  # What attributes matched
    
    # Status
    is_reviewed = Column(Boolean, default=False)
    is_false_positive = Column(Boolean, default=False)
    analyst_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    threat_indicator = relationship("ThreatIndicator", back_populates="correlations")
    project = relationship("Project")
    asset = relationship("Asset")
    
    # Indexes
    __table_args__ = (
        Index('idx_threat_correlations_project', 'project_id'),
        Index('idx_threat_correlations_relevance', 'relevance_score'),
        Index('idx_threat_correlations_reviewed', 'is_reviewed'),
    )


class ThreatAlert(Base):
    """Threat intelligence alerts"""
    __tablename__ = "threat_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    threat_indicator_id = Column(Integer, ForeignKey("threat_indicators.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))  # Optional project context
    
    # Alert metadata
    alert_type = Column(String(100), nullable=False)  # new_threat, correlation_match, etc.
    severity = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Status
    status = Column(String(50), default="open")  # open, acknowledged, resolved, false_positive
    assigned_to = Column(String(255))  # User ID
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Metadata
    alert_metadata = Column(JSON)
    
    # Relationships
    threat_indicator = relationship("ThreatIndicator")
    project = relationship("Project")
    
    # Indexes
    __table_args__ = (
        Index('idx_threat_alerts_status', 'status'),
        Index('idx_threat_alerts_severity', 'severity'),
        Index('idx_threat_alerts_triggered', 'triggered_at'),
    )


class ThreatIntelligenceCache(Base):
    """Cache for frequently accessed threat intelligence data"""
    __tablename__ = "threat_intelligence_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, nullable=False)
    cache_data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_threat_cache_key', 'cache_key'),
        Index('idx_threat_cache_expires', 'expires_at'),
    )


class ThreatIntelligenceMetrics(Base):
    """Metrics and statistics for threat intelligence"""
    __tablename__ = "threat_intelligence_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    
    # Dimensions
    feed_id = Column(Integer, ForeignKey("threat_feeds.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # Metadata
    tags = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feed = relationship("ThreatFeed")
    project = relationship("Project")
    
    # Indexes
    __table_args__ = (
        Index('idx_threat_metrics_name_time', 'metric_name', 'timestamp'),
        Index('idx_threat_metrics_feed', 'feed_id'),
    )