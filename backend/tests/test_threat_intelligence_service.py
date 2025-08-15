"""
Unit tests for ThreatIntelligenceService
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List

from app.services.threat_intelligence.threat_intelligence_service import (
    ThreatIntelligenceService, ProcessingStats, SourceWeight
)
from app.models.threat_intelligence import ThreatIndicator, ThreatFeed
from app.models.threat_schemas import ThreatType, SeverityLevel


class TestThreatIntelligenceService:
    """Test ThreatIntelligenceService"""
    
    def setup_method(self):
        self.service = ThreatIntelligenceService()
        
        # Mock feed
        self.mock_feed = Mock(spec=ThreatFeed)
        self.mock_feed.id = 1
        self.mock_feed.name = "test-feed"
        
        # Sample indicators
        self.sample_indicators = [
            ThreatIndicator(
                value="192.168.1.100",
                type=ThreatType.IOC,
                severity=SeverityLevel.HIGH,
                confidence=0.8,
                first_seen=datetime.utcnow() - timedelta(hours=1),
                last_seen=datetime.utcnow(),
                tags=["malware", "botnet"],
                feed_id=1
            ),
            ThreatIndicator(
                value="malicious.example.com",
                type=ThreatType.IOC,
                severity=SeverityLevel.MEDIUM,
                confidence=0.7,
                first_seen=datetime.utcnow() - timedelta(hours=2),
                last_seen=datetime.utcnow(),
                tags=["phishing"],
                feed_id=1
            )
        ]
    
    def test_initialization(self):
        """Test service initialization"""
        assert self.service.validator is not None
        assert len(self.service.source_weights) > 0
        assert 'misp' in self.service.source_weights
        assert 'otx' in self.service.source_weights
        assert 'virustotal' in self.service.source_weights
    
    def test_source_weights_configuration(self):
        """Test source weight configuration"""
        misp_weight = self.service.source_weights['misp']
        
        assert isinstance(misp_weight, SourceWeight)
        assert misp_weight.source_name == 'misp'
        assert 0.0 <= misp_weight.base_weight <= 1.0
        assert 0.0 <= misp_weight.reliability_factor <= 1.0
        assert 0.0 <= misp_weight.freshness_factor <= 1.0
        assert 0.0 <= misp_weight.volume_factor <= 1.0
    
    def test_create_indicator_hash(self):
        """Test indicator hash creation for deduplication"""
        indicator1 = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC
        )
        
        indicator2 = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC
        )
        
        indicator3 = ThreatIndicator(
            value="192.168.1.101",
            type=ThreatType.IOC
        )
        
        hash1 = self.service._create_indicator_hash(indicator1)
        hash2 = self.service._create_indicator_hash(indicator2)
        hash3 = self.service._create_indicator_hash(indicator3)
        
        # Same indicators should have same hash
        assert hash1 == hash2
        # Different indicators should have different hash
        assert hash1 != hash3
        # Hash should be consistent
        assert len(hash1) == 32  # MD5 hash length
    
    def test_get_type_confidence_multiplier(self):
        """Test confidence multiplier calculation by threat type"""
        # Test all threat types
        ioc_multiplier = self.service._get_type_confidence_multiplier(ThreatType.IOC)
        malware_multiplier = self.service._get_type_confidence_multiplier(ThreatType.MALWARE)
        vuln_multiplier = self.service._get_type_confidence_multiplier(ThreatType.VULNERABILITY)
        
        assert ioc_multiplier == 1.0
        assert 0.0 < malware_multiplier <= 1.0
        assert 0.0 < vuln_multiplier <= 1.0
    
    def test_calculate_freshness_multiplier(self):
        """Test freshness multiplier calculation"""
        now = datetime.utcnow()
        
        # Fresh indicator (1 hour old)
        fresh_time = now - timedelta(hours=1)
        fresh_multiplier = self.service._calculate_freshness_multiplier(fresh_time)
        assert fresh_multiplier == 1.0
        
        # Recent indicator (3 days old)
        recent_time = now - timedelta(days=3)
        recent_multiplier = self.service._calculate_freshness_multiplier(recent_time)
        assert 0.9 <= recent_multiplier <= 1.0
        
        # Old indicator (60 days old)
        old_time = now - timedelta(days=60)
        old_multiplier = self.service._calculate_freshness_multiplier(old_time)
        assert 0.6 <= old_multiplier < 0.9
    
    def test_get_severity_multiplier(self):
        """Test severity multiplier calculation"""
        critical_mult = self.service._get_severity_multiplier(SeverityLevel.CRITICAL)
        high_mult = self.service._get_severity_multiplier(SeverityLevel.HIGH)
        medium_mult = self.service._get_severity_multiplier(SeverityLevel.MEDIUM)
        low_mult = self.service._get_severity_multiplier(SeverityLevel.LOW)
        
        # Critical should have highest multiplier
        assert critical_mult > high_mult
        assert high_mult >= medium_mult
        assert medium_mult >= low_mult
        
        # All multipliers should be reasonable
        assert 0.9 <= critical_mult <= 1.1
        assert 0.9 <= low_mult <= 1.1
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation"""
        indicator = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            severity=SeverityLevel.HIGH,
            last_seen=datetime.utcnow()
        )
        
        confidence = self.service._calculate_confidence_score(indicator, self.mock_feed)
        
        # Confidence should be within valid range
        assert 0.0 <= confidence <= 1.0
        
        # Should be reasonably high for fresh, high-severity IOC
        assert confidence > 0.5
    
    def test_calculate_merged_confidence(self):
        """Test confidence calculation when merging indicators"""
        existing = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            confidence=0.8
        )
        
        new = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            severity=SeverityLevel.HIGH,
            last_seen=datetime.utcnow()
        )
        
        merged_confidence = self.service._calculate_merged_confidence(
            existing, new, self.mock_feed
        )
        
        # Merged confidence should be within valid range
        assert 0.0 <= merged_confidence <= 1.0
        
        # Should be influenced by both existing and new confidence
        assert merged_confidence != existing.confidence
    
    @pytest.mark.asyncio
    async def test_merge_indicators_updates_timestamps(self):
        """Test indicator merging updates timestamps correctly"""
        now = datetime.utcnow()
        
        existing = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            first_seen=now - timedelta(hours=5),
            last_seen=now - timedelta(hours=2),
            tags=["malware"],
            confidence=0.7,
            severity=SeverityLevel.MEDIUM
        )
        
        new = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            first_seen=now - timedelta(hours=3),  # Later first seen
            last_seen=now,  # More recent last seen
            tags=["botnet"],
            severity=SeverityLevel.HIGH
        )
        
        updated = await self.service._merge_indicators(existing, new, self.mock_feed)
        
        assert updated == True
        # Last seen should be updated to newer time
        assert existing.last_seen == new.last_seen
        # First seen should remain the earlier time
        assert existing.first_seen == now - timedelta(hours=5)
    
    @pytest.mark.asyncio
    async def test_merge_indicators_combines_tags(self):
        """Test indicator merging combines tags"""
        existing = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            first_seen=datetime.utcnow() - timedelta(hours=2),
            last_seen=datetime.utcnow() - timedelta(hours=1),
            tags=["malware", "botnet"],
            confidence=0.7
        )
        
        new = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            first_seen=datetime.utcnow() - timedelta(hours=1),
            last_seen=datetime.utcnow(),
            tags=["botnet", "trojan"],  # One duplicate, one new
            severity=SeverityLevel.HIGH
        )
        
        updated = await self.service._merge_indicators(existing, new, self.mock_feed)
        
        assert updated == True
        # Should have all unique tags
        expected_tags = {"malware", "botnet", "trojan"}
        assert set(existing.tags) == expected_tags
    
    @pytest.mark.asyncio
    async def test_merge_indicators_updates_severity(self):
        """Test indicator merging updates severity to higher level"""
        existing = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            severity=SeverityLevel.MEDIUM,
            first_seen=datetime.utcnow() - timedelta(hours=2),
            last_seen=datetime.utcnow() - timedelta(hours=1),
            confidence=0.7
        )
        
        new = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            severity=SeverityLevel.HIGH,  # Higher severity
            first_seen=datetime.utcnow() - timedelta(hours=1),
            last_seen=datetime.utcnow(),
            confidence=0.8
        )
        
        updated = await self.service._merge_indicators(existing, new, self.mock_feed)
        
        assert updated == True
        assert existing.severity == SeverityLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_merge_indicators_no_changes(self):
        """Test indicator merging when no updates are needed"""
        now = datetime.utcnow()
        
        existing = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            severity=SeverityLevel.HIGH,
            confidence=0.8,
            first_seen=now - timedelta(hours=2),
            last_seen=now,
            tags=["malware", "botnet"]
        )
        
        new = ThreatIndicator(
            value="192.168.1.100",
            type=ThreatType.IOC,
            severity=SeverityLevel.MEDIUM,  # Lower severity
            first_seen=now - timedelta(hours=1),  # Later first seen
            last_seen=now - timedelta(minutes=30),  # Earlier last seen
            tags=["malware"],  # Subset of existing tags
            confidence=0.6
        )
        
        updated = await self.service._merge_indicators(existing, new, self.mock_feed)
        
        # Should return False since no meaningful updates were made
        # (confidence might change slightly, but other fields shouldn't)
        assert existing.severity == SeverityLevel.HIGH  # Should remain high
        assert existing.first_seen == now - timedelta(hours=2)  # Should remain earlier
        assert existing.last_seen == now  # Should remain later
    
    @pytest.mark.asyncio
    @patch('app.services.threat_intelligence.threat_intelligence_service.async_session')
    async def test_get_threat_statistics(self, mock_session):
        """Test getting threat statistics"""
        # Mock database session and queries
        mock_db_session = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db_session
        
        # Mock query results
        mock_db_session.execute.side_effect = [
            # Total count
            Mock(scalar=Mock(return_value=1000)),
            # By type
            Mock(fetchall=Mock(return_value=[
                (ThreatType.IOC, 600),
                (ThreatType.MALWARE, 300),
                (ThreatType.VULNERABILITY, 100)
            ])),
            # By severity  
            Mock(fetchall=Mock(return_value=[
                (SeverityLevel.HIGH, 200),
                (SeverityLevel.MEDIUM, 500),
                (SeverityLevel.LOW, 300)
            ])),
            # Recent count
            Mock(scalar=Mock(return_value=50))
        ]
        
        # Mock the result objects to have the right methods
        for i, mock_result in enumerate(mock_db_session.execute.side_effect):
            if hasattr(mock_result, 'fetchall'):
                # For grouped queries, we need to iterate over results
                mock_result.__iter__ = Mock(return_value=iter(mock_result.fetchall.return_value))
        
        stats = await self.service.get_threat_statistics()
        
        assert stats['total_indicators'] == 1000
        assert stats['recent_24h'] == 50
        assert 'by_type' in stats
        assert 'by_severity' in stats
        assert 'last_updated' in stats
    
    @pytest.mark.asyncio
    @patch('app.services.threat_intelligence.threat_intelligence_service.async_session')
    async def test_search_threats_with_filters(self, mock_session):
        """Test threat search with various filters"""
        # Mock database session
        mock_db_session = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db_session
        
        # Mock query results
        mock_indicators = [
            Mock(spec=ThreatIndicator, value="192.168.1.100"),
            Mock(spec=ThreatIndicator, value="malicious.example.com")
        ]
        
        mock_db_session.execute.side_effect = [
            Mock(scalar=Mock(return_value=2)),  # Count query
            Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=mock_indicators))))  # Data query
        ]
        
        results, total = await self.service.search_threats(
            query="192.168",
            threat_types=[ThreatType.IOC],
            severity_levels=[SeverityLevel.HIGH],
            limit=10
        )
        
        assert total == 2
        assert len(results) == 2
        assert results[0].value == "192.168.1.100"
    
    @pytest.mark.asyncio
    @patch('app.services.threat_intelligence.threat_intelligence_service.async_session')
    async def test_cleanup_old_indicators(self, mock_session):
        """Test cleanup of old threat indicators"""
        # Mock database session
        mock_db_session = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db_session
        
        # Mock old indicators
        old_indicators = [
            Mock(spec=ThreatIndicator),
            Mock(spec=ThreatIndicator),
            Mock(spec=ThreatIndicator)
        ]
        
        mock_db_session.execute.return_value = Mock(
            scalars=Mock(return_value=Mock(all=Mock(return_value=old_indicators)))
        )
        
        deleted_count = await self.service.cleanup_old_indicators(days_old=90)
        
        assert deleted_count == 3
        # Verify delete was called for each indicator
        assert mock_db_session.delete.call_count == 3
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.threat_intelligence.threat_intelligence_service.async_session')
    async def test_process_threat_indicators_success(self, mock_session):
        """Test successful processing of threat indicators"""
        # Mock database session and feed
        mock_db_session = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db_session
        mock_db_session.get.return_value = self.mock_feed
        
        # Mock validator to return True
        self.service.validator.validate_indicator = Mock(return_value=True)
        
        # Mock no existing indicators (all new)
        mock_db_session.execute.return_value = Mock(
            scalar_one_or_none=Mock(return_value=None)
        )
        
        stats = await self.service.process_threat_indicators(
            self.sample_indicators, 
            feed_id=1
        )
        
        assert stats.processed_count == 2
        assert stats.failed_count == 0
        assert stats.processing_time > 0
        
        # Verify indicators were added to session
        assert mock_db_session.add.call_count == 2
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.threat_intelligence.threat_intelligence_service.async_session')
    async def test_process_threat_indicators_with_duplicates(self, mock_session):
        """Test processing indicators with duplicates"""
        # Mock database session and feed
        mock_db_session = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db_session
        mock_db_session.get.return_value = self.mock_feed
        
        # Mock validator to return True
        self.service.validator.validate_indicator = Mock(return_value=True)
        
        # Mock existing indicator for first sample
        existing_indicator = Mock(spec=ThreatIndicator)
        existing_indicator.value = self.sample_indicators[0].value
        existing_indicator.type = self.sample_indicators[0].type
        existing_indicator.last_seen = datetime.utcnow() - timedelta(hours=2)
        existing_indicator.first_seen = datetime.utcnow() - timedelta(hours=5)
        existing_indicator.tags = ["existing"]
        existing_indicator.confidence = 0.7
        existing_indicator.severity = SeverityLevel.MEDIUM
        existing_indicator.metadata = {}
        
        # Mock database queries to return existing for first, None for second
        mock_db_session.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=existing_indicator)),  # First indicator exists
            Mock(scalar_one_or_none=Mock(return_value=None))  # Second is new
        ]
        
        stats = await self.service.process_threat_indicators(
            self.sample_indicators,
            feed_id=1
        )
        
        # Should have 1 merged and 1 new
        assert stats.merged_count == 1
        assert stats.processed_count == 1
        assert stats.failed_count == 0
    
    @pytest.mark.asyncio
    @patch('app.services.threat_intelligence.threat_intelligence_service.async_session')
    async def test_process_threat_indicators_validation_failures(self, mock_session):
        """Test processing indicators with validation failures"""
        # Mock database session and feed
        mock_db_session = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db_session
        mock_db_session.get.return_value = self.mock_feed
        
        # Mock validator to fail for first indicator
        def mock_validate(indicator):
            return indicator.value != self.sample_indicators[0].value
        
        self.service.validator.validate_indicator = Mock(side_effect=mock_validate)
        
        # Mock no existing indicators
        mock_db_session.execute.return_value = Mock(
            scalar_one_or_none=Mock(return_value=None)
        )
        
        stats = await self.service.process_threat_indicators(
            self.sample_indicators,
            feed_id=1
        )
        
        # Should have 1 failed and 1 processed
        assert stats.failed_count == 1
        assert stats.processed_count == 1
        
        # Only one indicator should be added
        assert mock_db_session.add.call_count == 1


if __name__ == '__main__':
    pytest.main([__file__])