"""
Unit tests for MISP threat intelligence handler
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.threat_intelligence.misp_handler import MISPFeedHandler
from app.models.threat_intelligence import ThreatFeed
from app.models.threat_schemas import ThreatType, SeverityLevel


class TestMISPFeedHandler:
    """Test MISP feed handler"""
    
    def setup_method(self):
        # Create mock MISP feed
        self.mock_feed = Mock(spec=ThreatFeed)
        self.mock_feed.id = 1
        self.mock_feed.name = "Test MISP"
        self.mock_feed.url = "https://misp.example.com"
        self.mock_feed.api_key = "test-api-key"
        self.mock_feed.rate_limit = 100
        self.mock_feed.configuration = {
            'verify_ssl': True,
            'published_only': True,
            'event_limit': 10
        }
        
        self.handler = MISPFeedHandler(self.mock_feed)
    
    def test_initialization(self):
        """Test MISP handler initialization"""
        assert self.handler.feed == self.mock_feed
        assert self.handler.api_key == "test-api-key"
        assert self.handler.verify_ssl == True
        assert self.handler.published_only == True
        assert self.handler.event_limit == 10
    
    def test_get_default_headers(self):
        """Test MISP-specific headers"""
        headers = self.handler._get_default_headers()
        
        assert 'Authorization' in headers
        assert headers['Authorization'] == "test-api-key"
        assert headers['Accept'] == 'application/json'
        assert headers['User-Agent'] == 'AITM-ThreatIntelligence/1.0'
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful MISP authentication"""
        mock_response = {'version': '2.4.150'}
        
        with patch.object(self.handler, '_make_request', return_value=mock_response):
            result = await self.handler.authenticate()
            assert result == True
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self):
        """Test failed MISP authentication"""
        with patch.object(self.handler, '_make_request', side_effect=Exception("Connection failed")):
            result = await self.handler.authenticate()
            assert result == False
    
    def test_build_search_params(self):
        """Test building MISP search parameters"""
        # Test without timestamp
        params = self.handler._build_search_params()
        
        assert params['returnFormat'] == 'json'
        assert params['limit'] == 10
        assert params['published'] == True
        assert params['includeEventTags'] == True
        assert 'timestamp' not in params
        
        # Test with timestamp
        since = datetime(2023, 1, 1, 12, 0, 0)
        params_with_time = self.handler._build_search_params(since)
        
        assert params_with_time['timestamp'] == '2023-01-01'
    
    def test_is_valid_attribute(self):
        """Test MISP attribute validation"""
        # Valid attribute
        valid_attr = {
            'value': 'malicious.example.com',
            'type': 'domain',
            'deleted': False,
            'to_ids': True
        }
        assert self.handler._is_valid_attribute(valid_attr) == True
        
        # Invalid attributes
        invalid_attrs = [
            {},  # Empty
            {'type': 'domain'},  # No value
            {'value': 'test.com'},  # No type
            {'value': 'test.com', 'type': 'domain', 'deleted': True},  # Deleted
            {'value': 'test.com', 'type': 'domain', 'to_ids': False}  # Not for IDS
        ]
        
        for attr in invalid_attrs:
            assert self.handler._is_valid_attribute(attr) == False
    
    def test_map_misp_type(self):
        """Test MISP type mapping"""
        test_cases = [
            ('md5', 'hash'),
            ('sha256', 'hash'),
            ('ip-src', 'ip'),
            ('ip-dst', 'ip'),
            ('hostname', 'domain'),
            ('domain', 'domain'),
            ('url', 'url'),
            ('email-src', 'email'),
            ('vulnerability', 'vulnerability'),
            ('cve', 'vulnerability'),
            ('mitre-attack-pattern', 'ttp'),
            ('unknown-type', 'unknown-type')  # Unmapped type
        ]
        
        for misp_type, expected in test_cases:
            result = self.handler._map_misp_type(misp_type)
            assert result == expected
    
    def test_map_misp_threat_level(self):
        """Test MISP threat level mapping"""
        test_cases = [
            ('1', 'high'),
            ('2', 'medium'),
            ('3', 'low'),
            ('4', 'medium'),
            (None, 'medium'),
            ('invalid', 'medium')
        ]
        
        for threat_level, expected in test_cases:
            result = self.handler._map_misp_threat_level(threat_level)
            assert result == expected
    
    def test_calculate_misp_confidence(self):
        """Test MISP-specific confidence calculation"""
        base_confidence = 0.5
        
        # Test with IDS enabled
        raw_data_ids = {'to_ids': True}
        confidence = self.handler._calculate_misp_confidence(raw_data_ids, base_confidence)
        assert confidence > base_confidence
        
        # Test with high distribution
        raw_data_dist = {'distribution': 3}
        confidence = self.handler._calculate_misp_confidence(raw_data_dist, base_confidence)
        assert confidence > base_confidence
        
        # Test with published event
        raw_data_pub = {'event_published': True}
        confidence = self.handler._calculate_misp_confidence(raw_data_pub, base_confidence)
        assert confidence > base_confidence
        
        # Test with completed analysis
        raw_data_analysis = {'event_analysis': 2}
        confidence = self.handler._calculate_misp_confidence(raw_data_analysis, base_confidence)
        assert confidence > base_confidence
        
        # Test combined factors
        raw_data_combined = {
            'to_ids': True,
            'distribution': 3,
            'event_published': True,
            'event_analysis': 2
        }
        confidence = self.handler._calculate_misp_confidence(raw_data_combined, base_confidence)
        assert confidence > base_confidence
        assert confidence <= 1.0  # Should not exceed 1.0
    
    def test_extract_event_tags(self):
        """Test extracting tags from MISP event"""
        event_data = {
            'EventTag': [
                {'Tag': {'name': 'malware'}},
                {'Tag': {'name': 'apt'}}
            ],
            'Galaxy': [
                {
                    'GalaxyCluster': [
                        {'value': 'APT1'},
                        {'value': 'Lazarus Group'}
                    ]
                }
            ]
        }
        
        tags = self.handler._extract_event_tags(event_data)
        
        assert 'malware' in tags
        assert 'apt' in tags
        assert 'galaxy:APT1' in tags
        assert 'galaxy:Lazarus Group' in tags
    
    def test_normalize_indicator(self):
        """Test normalizing MISP indicator"""
        raw_misp_data = {
            'value': 'malicious.example.com',
            'type': 'domain',
            'category': 'Network activity',
            'comment': 'Known C2 domain',
            'uuid': '12345678-1234-1234-1234-123456789abc',
            'event_id': '123',
            'event_info': 'APT Campaign',
            'event_date': '2023-01-01',
            'to_ids': True,
            'distribution': 3,
            'event_published': True,
            'event_analysis': 2,
            'event_threat_level': '1',
            'event_tags': ['malware', 'apt'],
            'AttributeTag': [
                {'Tag': {'name': 'c2'}}
            ]
        }
        
        result = self.handler.normalize_indicator(raw_misp_data)
        
        assert result is not None
        assert result.value == 'malicious.example.com'
        assert result.type == ThreatType.IOC
        assert result.external_id == '12345678-1234-1234-1234-123456789abc'
        assert result.feed_id == 1
        assert result.severity == SeverityLevel.HIGH  # Based on threat level 1
        assert result.confidence > 0.5  # Should be boosted by MISP factors
        assert 'malware' in result.tags
        assert 'apt' in result.tags
        assert 'c2' in result.tags
    
    def test_normalize_indicator_invalid(self):
        """Test normalizing invalid MISP indicator"""
        invalid_data = {
            'type': 'domain',
            # Missing value
            'uuid': '12345678-1234-1234-1234-123456789abc'
        }
        
        result = self.handler.normalize_indicator(invalid_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_feed_info_success(self):
        """Test getting MISP feed information"""
        mock_response = {
            'version': '2.4.150',
            'perm_sync': '1'
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_response):
            info = await self.handler.get_feed_info()
            
            assert info['name'] == 'Test MISP'
            assert info['version'] == '2.4.150'
            assert info['api_version'] == '1'
            assert info['status'] == 'connected'
    
    @pytest.mark.asyncio
    async def test_get_feed_info_error(self):
        """Test getting MISP feed information with error"""
        with patch.object(self.handler, '_make_request', side_effect=Exception("Connection failed")):
            info = await self.handler.get_feed_info()
            
            assert info['name'] == 'Test MISP'
            assert info['status'] == 'error'
            assert 'Connection failed' in info['error']
    
    @pytest.mark.asyncio
    async def test_test_connection_detailed_success(self):
        """Test detailed connection test - success"""
        mock_version = {'version': '2.4.150'}
        mock_events = {'response': []}
        
        with patch.object(self.handler, '_make_request') as mock_request:
            mock_request.side_effect = [mock_version, mock_events]
            
            results = await self.handler.test_connection_detailed()
            
            assert results['authentication'] == True
            assert results['api_access'] == True
            assert results['data_retrieval'] == True
            assert len(results['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_test_connection_detailed_auth_failure(self):
        """Test detailed connection test - authentication failure"""
        with patch.object(self.handler, '_make_request', side_effect=Exception("Auth failed")):
            results = await self.handler.test_connection_detailed()
            
            assert results['authentication'] == False
            assert results['api_access'] == False
            assert results['data_retrieval'] == False
            assert 'Authentication failed' in results['errors']
    
    @pytest.mark.asyncio
    async def test_fetch_indicators_integration(self):
        """Test fetching indicators - integration test"""
        # Mock MISP event response
        mock_events_response = {
            'response': [
                {
                    'Event': {
                        'id': '123',
                        'uuid': 'event-uuid',
                        'info': 'Test Event',
                        'date': '2023-01-01',
                        'published': True,
                        'threat_level_id': '1',
                        'analysis': '2',
                        'EventTag': [
                            {'Tag': {'name': 'malware'}}
                        ],
                        'Attribute': [
                            {
                                'value': 'malicious.example.com',
                                'type': 'domain',
                                'category': 'Network activity',
                                'uuid': 'attr-uuid',
                                'to_ids': True,
                                'deleted': False
                            }
                        ]
                    }
                }
            ]
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_events_response):
            indicators = []
            async for indicator in self.handler.fetch_indicators():
                indicators.append(indicator)
            
            assert len(indicators) == 1
            assert indicators[0]['value'] == 'malicious.example.com'
            assert indicators[0]['type'] == 'domain'
            assert indicators[0]['event_id'] == '123'
            assert indicators[0]['event_tags'] == ['malware']


if __name__ == '__main__':
    pytest.main([__file__])