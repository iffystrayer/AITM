"""
Threat Intelligence Processing Service

This service handles the core processing of threat intelligence data including:
- Async processing of threat indicators from multiple feeds
- Deduplication and merging of threat data
- Confidence scoring and source weighting
- Correlation with existing threat models
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.database import async_session
from app.models.threat_intelligence import ThreatIndicator, ThreatFeed, ThreatCorrelation
from app.models.threat_schemas import ThreatType, SeverityLevel, CorrelationType
from app.services.threat_intelligence.data_validator import ThreatDataValidator
from app.core.redis_config import redis_manager


logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for threat intelligence processing"""
    processed_count: int = 0
    deduplicated_count: int = 0
    merged_count: int = 0
    failed_count: int = 0
    correlation_count: int = 0
    processing_time: float = 0.0


@dataclass
class SourceWeight:
    """Weight configuration for threat intelligence sources"""
    source_name: str
    base_weight: float
    reliability_factor: float
    freshness_factor: float
    volume_factor: float


class ThreatIntelligenceService:
    """Core threat intelligence processing service"""
    
    def __init__(self):
        self.validator = ThreatDataValidator()
        self.redis_client = None
        self.source_weights = self._initialize_source_weights()
        self.deduplication_cache = {}
        
    async def _get_redis(self):
        """Get Redis client for caching"""
        if not self.redis_client:
            self.redis_client = await redis_manager.get_redis()
        return self.redis_client
    
    def _initialize_source_weights(self) -> Dict[str, SourceWeight]:
        """Initialize source weighting configuration"""
        return {
            'misp': SourceWeight('misp', 0.9, 0.95, 0.8, 0.7),
            'otx': SourceWeight('otx', 0.8, 0.85, 0.9, 0.8),
            'virustotal': SourceWeight('virustotal', 0.85, 0.9, 0.95, 0.9),
            'custom': SourceWeight('custom', 0.7, 0.8, 0.7, 0.6)
        }
    
    async def process_threat_indicators(
        self, 
        indicators: List[ThreatIndicator],
        feed_id: int
    ) -> ProcessingStats:
        """
        Process a batch of threat indicators with deduplication and scoring
        
        Args:
            indicators: List of threat indicators to process
            feed_id: ID of the threat feed source
            
        Returns:
            ProcessingStats: Statistics about the processing operation
        """
        start_time = datetime.utcnow()
        stats = ProcessingStats()
        
        try:
            async with async_session() as session:
                # Get feed information for source weighting
                feed = await session.get(ThreatFeed, feed_id)
                if not feed:
                    logger.error(f"Feed {feed_id} not found")
                    return stats
                
                # Process indicators in batches for better performance
                batch_size = 100
                for i in range(0, len(indicators), batch_size):
                    batch = indicators[i:i + batch_size]
                    batch_stats = await self._process_indicator_batch(
                        session, batch, feed, stats
                    )
                    stats.processed_count += batch_stats.processed_count
                    stats.deduplicated_count += batch_stats.deduplicated_count
                    stats.merged_count += batch_stats.merged_count
                    stats.failed_count += batch_stats.failed_count
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error processing threat indicators: {e}")
            stats.failed_count = len(indicators)
        
        finally:
            end_time = datetime.utcnow()
            stats.processing_time = (end_time - start_time).total_seconds()
            
        logger.info(f"Processed {stats.processed_count} indicators, "
                   f"deduplicated {stats.deduplicated_count}, "
                   f"merged {stats.merged_count}, "
                   f"failed {stats.failed_count} in {stats.processing_time:.2f}s")
        
        return stats
    
    async def _process_indicator_batch(
        self,
        session: AsyncSession,
        indicators: List[ThreatIndicator],
        feed: ThreatFeed,
        stats: ProcessingStats
    ) -> ProcessingStats:
        """Process a batch of indicators"""
        batch_stats = ProcessingStats()
        
        for indicator in indicators:
            try:
                # Validate indicator data
                if not self.validator.validate_indicator(indicator):
                    batch_stats.failed_count += 1
                    continue
                
                # Check for existing indicators (deduplication)
                existing = await self._find_existing_indicator(session, indicator)
                
                if existing:
                    # Merge with existing indicator
                    merged = await self._merge_indicators(existing, indicator, feed)
                    if merged:
                        batch_stats.merged_count += 1
                    else:
                        batch_stats.deduplicated_count += 1
                else:
                    # Calculate confidence score
                    indicator.confidence = self._calculate_confidence_score(
                        indicator, feed
                    )
                    
                    # Add new indicator
                    session.add(indicator)
                    batch_stats.processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing indicator {indicator.value}: {e}")
                batch_stats.failed_count += 1
        
        return batch_stats
    
    async def _find_existing_indicator(
        self,
        session: AsyncSession,
        indicator: ThreatIndicator
    ) -> Optional[ThreatIndicator]:
        """Find existing indicator for deduplication"""
        
        # Create a hash for the indicator value and type
        indicator_hash = self._create_indicator_hash(indicator)
        
        # Check cache first
        if indicator_hash in self.deduplication_cache:
            cached_id = self.deduplication_cache[indicator_hash]
            return await session.get(ThreatIndicator, cached_id)
        
        # Query database
        query = select(ThreatIndicator).where(
            and_(
                ThreatIndicator.value == indicator.value,
                ThreatIndicator.type == indicator.type
            )
        )
        
        result = await session.execute(query)
        existing = result.scalar_one_or_none()
        
        # Cache the result
        if existing:
            self.deduplication_cache[indicator_hash] = existing.id
        
        return existing
    
    def _create_indicator_hash(self, indicator: ThreatIndicator) -> str:
        """Create a hash for indicator deduplication"""
        hash_data = f"{indicator.value}:{indicator.type.value}"
        return hashlib.md5(hash_data.encode()).hexdigest()
    
    async def _merge_indicators(
        self,
        existing: ThreatIndicator,
        new: ThreatIndicator,
        feed: ThreatFeed
    ) -> bool:
        """
        Merge new indicator data with existing indicator
        
        Returns:
            bool: True if merge resulted in updates, False if no changes
        """
        updated = False
        
        # Update last seen timestamp
        if new.last_seen > existing.last_seen:
            existing.last_seen = new.last_seen
            updated = True
        
        # Update first seen if earlier
        if new.first_seen < existing.first_seen:
            existing.first_seen = new.first_seen
            updated = True
        
        # Merge tags
        existing_tags = set(existing.tags or [])
        new_tags = set(new.tags or [])
        merged_tags = existing_tags.union(new_tags)
        
        if merged_tags != existing_tags:
            existing.tags = list(merged_tags)
            updated = True
        
        # Update confidence score based on multiple sources
        new_confidence = self._calculate_merged_confidence(
            existing, new, feed
        )
        
        existing_conf = existing.confidence or 0.5
        if abs(new_confidence - existing_conf) > 0.01:
            existing.confidence = new_confidence
            updated = True
        
        # Update severity if new indicator has higher severity
        if new.severity and existing.severity:
            if self._is_higher_severity(new.severity, existing.severity):
                existing.severity = new.severity
                updated = True
        elif new.severity and not existing.severity:
            existing.severity = new.severity
            updated = True
        
        # Update metadata (only if it's a dict-like object)
        if new.metadata and hasattr(new.metadata, 'items'):
            existing_meta = existing.metadata or {}
            # Ensure existing_meta is also dict-like
            if hasattr(existing_meta, 'items'):
                for key, value in new.metadata.items():
                    if key not in existing_meta:
                        existing_meta[key] = value
                        updated = True
                
                if updated:
                    existing.metadata = existing_meta
        
        return updated
    
    def _calculate_confidence_score(
        self,
        indicator: ThreatIndicator,
        feed: ThreatFeed
    ) -> float:
        """Calculate confidence score for a threat indicator"""
        
        # Get source weight configuration
        source_weight = self.source_weights.get(
            feed.name.lower(), 
            self.source_weights['custom']
        )
        
        # Base confidence from source
        base_confidence = source_weight.base_weight
        
        # Adjust for indicator type
        type_multiplier = self._get_type_confidence_multiplier(indicator.type)
        
        # Adjust for freshness (newer indicators get higher confidence)
        freshness_multiplier = self._calculate_freshness_multiplier(
            indicator.last_seen
        )
        
        # Adjust for severity (higher severity gets slight confidence boost)
        severity_multiplier = self._get_severity_multiplier(indicator.severity)
        
        # Calculate final confidence
        confidence = (
            base_confidence * 
            type_multiplier * 
            freshness_multiplier * 
            severity_multiplier
        )
        
        # Ensure confidence is within valid range [0.0, 1.0]
        return max(0.0, min(1.0, confidence))
    
    def _calculate_merged_confidence(
        self,
        existing: ThreatIndicator,
        new: ThreatIndicator,
        feed: ThreatFeed
    ) -> float:
        """Calculate confidence when merging indicators from multiple sources"""
        
        # Get the new confidence score
        new_confidence = self._calculate_confidence_score(new, feed)
        
        # Use weighted average based on source reliability
        source_weight = self.source_weights.get(
            feed.name.lower(),
            self.source_weights['custom']
        )
        
        # Weight the existing confidence higher if it's from a more reliable source
        existing_weight = 0.7
        new_weight = source_weight.reliability_factor * 0.3
        
        existing_conf = existing.confidence or 0.5  # Default if None
        merged_confidence = (
            existing_conf * existing_weight + 
            new_confidence * new_weight
        )
        
        return max(0.0, min(1.0, merged_confidence))
    
    def _get_type_confidence_multiplier(self, threat_type: ThreatType) -> float:
        """Get confidence multiplier based on threat type"""
        multipliers = {
            ThreatType.IOC: 1.0,
            ThreatType.MALWARE: 0.95,
            ThreatType.VULNERABILITY: 0.9,
            ThreatType.CAMPAIGN: 0.85,
            ThreatType.THREAT_ACTOR: 0.8,
            ThreatType.TTP: 0.9,
            ThreatType.INFRASTRUCTURE: 0.85
        }
        return multipliers.get(threat_type, 0.8)
    
    def _calculate_freshness_multiplier(self, last_seen: datetime) -> float:
        """Calculate freshness multiplier based on how recent the indicator is"""
        now = datetime.utcnow()
        age_hours = (now - last_seen).total_seconds() / 3600
        
        # Fresh indicators (< 24 hours) get full confidence
        if age_hours < 24:
            return 1.0
        # Indicators up to 7 days get slight reduction
        elif age_hours < 168:  # 7 days
            return 0.95
        # Indicators up to 30 days get moderate reduction
        elif age_hours < 720:  # 30 days
            return 0.85
        # Older indicators get significant reduction
        else:
            return 0.7
    
    def _get_severity_multiplier(self, severity: SeverityLevel) -> float:
        """Get confidence multiplier based on severity level"""
        multipliers = {
            SeverityLevel.CRITICAL: 1.05,
            SeverityLevel.HIGH: 1.02,
            SeverityLevel.MEDIUM: 1.0,
            SeverityLevel.LOW: 0.98
        }
        return multipliers.get(severity, 1.0)
    
    def _is_higher_severity(self, severity1: SeverityLevel, severity2: SeverityLevel) -> bool:
        """Check if severity1 is higher than severity2"""
        severity_order = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
            SeverityLevel.CRITICAL: 4
        }
        return severity_order.get(severity1, 0) > severity_order.get(severity2, 0)
    
    async def get_threat_statistics(self) -> Dict:
        """Get threat intelligence statistics"""
        try:
            async with async_session() as session:
                # Total indicators
                total_query = select(func.count(ThreatIndicator.id))
                total_result = await session.execute(total_query)
                total_indicators = total_result.scalar()
                
                # Indicators by type
                type_query = select(
                    ThreatIndicator.type,
                    func.count(ThreatIndicator.id)
                ).group_by(ThreatIndicator.type)
                type_result = await session.execute(type_query)
                by_type = {row[0].value: row[1] for row in type_result}
                
                # Indicators by severity
                severity_query = select(
                    ThreatIndicator.severity,
                    func.count(ThreatIndicator.id)
                ).group_by(ThreatIndicator.severity)
                severity_result = await session.execute(severity_query)
                by_severity = {row[0].value: row[1] for row in severity_result}
                
                # Recent indicators (last 24 hours)
                recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                recent_query = select(func.count(ThreatIndicator.id)).where(
                    ThreatIndicator.last_seen >= recent_cutoff
                )
                recent_result = await session.execute(recent_query)
                recent_indicators = recent_result.scalar()
                
                return {
                    'total_indicators': total_indicators,
                    'by_type': by_type,
                    'by_severity': by_severity,
                    'recent_24h': recent_indicators,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting threat statistics: {e}")
            return {}
    
    async def search_threats(
        self,
        query: str = None,
        threat_types: List[ThreatType] = None,
        severity_levels: List[SeverityLevel] = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[ThreatIndicator], int]:
        """
        Search threat indicators with various filters
        
        Returns:
            Tuple of (indicators, total_count)
        """
        try:
            async with async_session() as session:
                # Build base query
                query_filters = []
                
                # Text search
                if query:
                    query_filters.append(
                        or_(
                            ThreatIndicator.value.ilike(f'%{query}%'),
                            ThreatIndicator.description.ilike(f'%{query}%')
                        )
                    )
                
                # Type filter
                if threat_types:
                    query_filters.append(ThreatIndicator.type.in_(threat_types))
                
                # Severity filter
                if severity_levels:
                    query_filters.append(ThreatIndicator.severity.in_(severity_levels))
                
                # Date range filter
                if date_from:
                    query_filters.append(ThreatIndicator.last_seen >= date_from)
                if date_to:
                    query_filters.append(ThreatIndicator.last_seen <= date_to)
                
                # Count query
                count_query = select(func.count(ThreatIndicator.id))
                if query_filters:
                    count_query = count_query.where(and_(*query_filters))
                
                count_result = await session.execute(count_query)
                total_count = count_result.scalar()
                
                # Data query
                data_query = select(ThreatIndicator).options(
                    selectinload(ThreatIndicator.feed)
                )
                
                if query_filters:
                    data_query = data_query.where(and_(*query_filters))
                
                data_query = data_query.order_by(
                    ThreatIndicator.last_seen.desc()
                ).limit(limit).offset(offset)
                
                data_result = await session.execute(data_query)
                indicators = data_result.scalars().all()
                
                return list(indicators), total_count
                
        except Exception as e:
            logger.error(f"Error searching threats: {e}")
            return [], 0
    
    async def cleanup_old_indicators(self, days_old: int = 90) -> int:
        """
        Clean up old threat indicators
        
        Args:
            days_old: Remove indicators older than this many days
            
        Returns:
            Number of indicators removed
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            async with async_session() as session:
                # Find old indicators
                old_query = select(ThreatIndicator).where(
                    ThreatIndicator.last_seen < cutoff_date
                )
                result = await session.execute(old_query)
                old_indicators = result.scalars().all()
                
                # Delete old indicators
                for indicator in old_indicators:
                    await session.delete(indicator)
                
                await session.commit()
                
                logger.info(f"Cleaned up {len(old_indicators)} old threat indicators")
                return len(old_indicators)
                
        except Exception as e:
            logger.error(f"Error cleaning up old indicators: {e}")
            return 0