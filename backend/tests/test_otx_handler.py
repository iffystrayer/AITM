"""
Unit tests for OTX threat intelligence handler
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.threat_intelligence.otx_handler import OTXFeedHandler
from app.models.threat_intelligence import ThreatFeed
from app.models.threat_schemas import ThreatType, SeverityLevel


class TestOTXFeedHandler:
    """Test OTX feed handler"""
    
    def setup_method(self):
        # Create mock OTX feed
        self.mock_feed = Mock(spec=ThreatFeed)
        self.mock_feed.id = 1
        self.mock_feed.name = "Test OTX"
        self.mock_feed.url = "https://otx.alienvault.com/api/v1"
        self.mock_feed.api_key = "test-otx-api-key"
        self.mock_feed.rate_limit = 1000
        self.mock_feed.configuration = {
            'subscribed_only': False,
            'pulse_limit': 20,
            'min_pulse_score': 0
        }
        
        self.handler = OTXFeedHandler(self.mock_feed)
    
    def test_initialization(self):
        """Test OTX handler initialization"""
        assert self.handler.feed == self.mock_feed
        assert self.handler.api_key == "test-otx-api-key"
        assert self.handler.subscribed_only == False
        assert self.handler.pulse_limit == 20
        assert self.handler.min_pulse_score == 0
    
    def test_get_default_headers(self):
        """Test OTX-specific headers"""
        headers = self.handler._get_default_headers()
        
        assert 'X-OTX-API-KEY' in headers
        assert headers['X-OTX-API-KEY'] == "test-otx-api-key"
        assert headers['Accept'] == 'application/json'
        assert headers['User-Agent'] == 'AITM-ThreatIntelligence/1.0'
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful OTX authentication"""
        mock_response = {
            'username': 'testuser',
            'member_since': '2020-01-01',
            'reputation': 100
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_response):
            result = await self.handler.authenticate()
            assert result == True
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self):
        """Test failed OTX authentication"""
        with patch.object(self.handler, '_make_request', side_effect=Exception("Unauthorized")):
            result = await self.handler.authenticate()
            assert result == False
    
    def test_is_valid_pulse(self):
        """Test OTX pulse validation"""
        # Valid pulse
        valid_pulse = {
            'id': '12345',
            'name': 'Test Pulse',
            'pulse_score': 5,
            'indicators': [{'indicator': 'test.com', 'type': 'domain'}]
        }
        assert self.handler._is_valid_pulse(valid_pulse) == True
        
        # Invalid pulses
        invalid_pulses = [
            {},  # Empty
            {'name': 'Test'},  # No ID
            {'id': '123'},  # No name
            {'id': '123', 'name': 'Test', 'indicators': []},  # No indicators
        ]
        
        for pulse in invalid_pulses:
            assert self.handler._is_valid_pulse(pulse) == False
    
    def test_is_valid_indicator(self):
        """Test OTX indicator validation"""
        # Valid indicator
        valid_indicator = {
            'indicator': 'malicious.example.com',
            'type': 'domain',
            'is_active': True
        }
        assert self.handler._is_valid_indicator(valid_indicator) == True
        
        # Invalid indicators
        invalid_indicators = [
            {},  # Empty
            {'type': 'domain'},  # No indicator
            {'indicator': 'test.com'},  # No type
            {'indicator': 'test.com', 'type': 'domain', 'is_active': False}  # Inactive
        ]
        
        for indicator in invalid_indicators:
            assert self.handler._is_valid_indicator(indicator) == False
    
    def test_map_otx_type(self):
        """Test OTX type mapping"""
        test_cases = [
            ('FileHash-MD5', 'hash'),
            ('FileHash-SHA1', 'hash'),
            ('FileHash-SHA256', 'hash'),
            ('IPv4', 'ip'),
            ('IPv6', 'ip'),
            ('domain', 'domain'),
            ('hostname', 'domain'),
            ('URL', 'url'),
            ('email', 'email'),
            ('CVE', 'vulnerability'),
            ('YARA', 'yara'),
            ('BitcoinAddress', 'cryptocurrency'),
            ('unknown-type', 'unknown-type')  # Unmapped type
        ]
        
        for otx_type, expected in test_cases:
            result = self.handler._map_otx_type(otx_type)
            assert result == expected
    
    def test_determine_otx_severity(self):
        """Test OTX severity determination"""
        test_cases = [
            ({'role': 'malware'}, 'high'),
            ({'role': 'c2'}, 'high'),
            ({'role': 'exploit'}, 'high'),
            ({'role': 'reconnaissance'}, 'medium'),
            ({'pulse_malware_families': ['Zeus']}, 'high'),
            ({'pulse_attack_ids': ['T1055']}, 'medium'),
            ({'pulse_tlp': 'RED'}, 'high'),
            ({'pulse_tlp': 'AMBER'}, 'high'),
            ({'pulse_tlp': 'GREEN'}, 'medium'),
            ({}, 'medium')  # Default
        ]
        
        for raw_data, expected in test_cases:
            result = self.handler._determine_otx_severity(raw_data)
            assert result == expected
    
    def test_calculate_otx_confidence(self):
        """Test OTX-specific confidence calculation"""
        base_confidence = 0.5
        
        # Test with active indicator
        raw_data_active = {'is_active': True}
        confidence = self.handler._calculate_otx_confidence(raw_data_active, base_confidence)
        assert confidence > base_confidence
        
        # Test with pulse revision
        raw_data_revision = {'pulse_revision': 5}
        confidence = self.handler._calculate_otx_confidence(raw_data_revision, base_confidence)
        assert confidence > base_confidence
        
        # Test with malware role
        raw_data_role = {'role': 'malware'}
        confidence = self.handler._calculate_otx_confidence(raw_data_role, base_confidence)
        assert confidence > base_confidence
        
        # Test with TLP WHITE
        raw_data_tlp = {'pulse_tlp': 'WHITE'}
        confidence = self.handler._calculate_otx_confidence(raw_data_tlp, base_confidence)
        assert confidence > base_confidence
        
        # Test with MITRE ATT&CK
        raw_data_attack = {'pulse_attack_ids': ['T1055', 'T1059']}
        confidence = self.handler._calculate_otx_confidence(raw_data_attack, base_confidence)
        assert confidence > base_confidence
        
        # Test with malware families
        raw_data_malware = {'pulse_malware_families': ['Zeus', 'Emotet']}
        confidence = self.handler._calculate_otx_confidence(raw_data_malware, base_confidence)
        assert confidence > base_confidence
        
        # Test combined factors
        raw_data_combined = {
            'is_active': True,
            'pulse_revision': 3,
            'role': 'c2',
            'pulse_tlp': 'WHITE',
            'pulse_attack_ids': ['T1055'],
            'pulse_malware_families': ['APT1']
        }
        confidence = self.handler._calculate_otx_confidence(raw_data_combined, base_confidence)
        assert confidence > base_confidence
        assert confidence <= 1.0  # Should not exceed 1.0
    
    def test_normalize_indicator(self):
        """Test normalizing OTX indicator"""
        raw_otx_data = {
            'indicator': 'malicious.example.com',
            'type': 'domain',
            'description': 'Known C2 domain',
            'title': 'APT Campaign Infrastructure',
            'created': '2023-01-01T00:00:00Z',
            'modified': '2023-01-02T00:00:00Z',
            'pulse_id': '12345',
            'pulse_name': 'APT Campaign',
            'pulse_author': 'security_researcher',
            'pulse_created': '2023-01-01T00:00:00Z',
            'pulse_modified': '2023-01-02T00:00:00Z',
            'pulse_tlp': 'WHITE',
            'pulse_tags': ['apt', 'malware'],
            'pulse_malware_families': ['Zeus'],
            'pulse_attack_ids': ['T1055', 'T1059'],
            'pulse_industries': ['finance'],
            'pulse_targeted_countries': ['US', 'UK'],
            'is_active': True,
            'role': 'c2'
        }
        
        result = self.handler.normalize_indicator(raw_otx_data)
        
        assert result is not None
        assert result.value == 'malicious.example.com'
        assert result.type == ThreatType.IOC
        assert result.external_id == '12345'
        assert result.feed_id == 1
        assert result.severity == SeverityLevel.HIGH  # Based on role 'c2'
        assert result.confidence > 0.5  # Should be boosted by OTX factors
        
        # Check tags
        assert 'apt' in result.tags
        assert 'malware' in result.tags
        assert 'malware:Zeus' in result.tags
        assert 'mitre:T1055' in result.tags
        assert 'mitre:T1059' in result.tags
        assert 'industry:finance' in result.tags
        assert 'country:US' in result.tags
        assert 'country:UK' in result.tags
        assert 'tlp:white' in result.tags
    
    def test_normalize_indicator_invalid(self):
        """Test normalizing invalid OTX indicator"""
        invalid_data = {
            'type': 'domain',
            # Missing indicator value
            'pulse_id': '12345'
        }
        
        result = self.handler.normalize_indicator(invalid_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_feed_info_success(self):
        """Test getting OTX feed information"""
        mock_response = {
            'username': 'testuser',
            'member_since': '2020-01-01T00:00:00Z',
            'reputation': 150,
            'follower_count': 50,
            'following_count': 25,
            'indicator_count': 1000,
            'pulse_count': 100
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_response):
            info = await self.handler.get_feed_info()
            
            assert info['name'] == 'Test OTX'
            assert info['username'] == 'testuser'
            assert info['reputation'] == 150
            assert info['follower_count'] == 50
            assert info['pulse_count'] == 100
            assert info['status'] == 'connected'
    
    @pytest.mark.asyncio
    async def test_get_feed_info_error(self):
        """Test getting OTX feed information with error"""
        with patch.object(self.handler, '_make_request', side_effect=Exception("Connection failed")):
            info = await self.handler.get_feed_info()
            
            assert info['name'] == 'Test OTX'
            assert info['status'] == 'error'
            assert 'Connection failed' in info['error']
    
    @pytest.mark.asyncio
    async def test_test_connection_detailed_success(self):
        """Test detailed connection test - success"""
        mock_user = {'username': 'testuser'}
        mock_pulses = {'results': []}
        
        with patch.object(self.handler, '_make_request') as mock_request:
            mock_request.side_effect = [mock_user, mock_pulses]
            
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
    async def test_get_pulse_details(self):
        """Test getting pulse details"""
        pulse_id = '12345'
        mock_pulse = {
            'id': pulse_id,
            'name': 'Test Pulse',
            'description': 'Test pulse description',
            'indicators': []
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_pulse):
            result = await self.handler.get_pulse_details(pulse_id)
            
            assert result is not None
            assert result['id'] == pulse_id
            assert result['name'] == 'Test Pulse'
    
    @pytest.mark.asyncio
    async def test_search_indicators(self):
        """Test searching for indicators"""
        indicator_value = 'malicious.example.com'
        mock_response = {
            'pulse_info': {
                'pulses': [
                    {'id': '123', 'name': 'Pulse 1'},
                    {'id': '456', 'name': 'Pulse 2'}
                ]
            }
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_response):
            results = await self.handler.search_indicators(indicator_value)
            
            assert len(results) == 2
            assert results[0]['id'] == '123'
            assert results[1]['id'] == '456'
    
    @pytest.mark.asyncio
    async def test_fetch_indicators_integration(self):
        """Test fetching indicators - integration test"""
        # Mock OTX pulses response
        mock_pulses_response = {
            'results': [
                {
                    'id': '12345',
                    'name': 'APT Campaign Infrastructure',
                    'description': 'C2 infrastructure for APT campaign',
                    'author_name': 'security_researcher',
                    'created': '2023-01-01T00:00:00Z',
                    'modified': '2023-01-02T00:00:00Z',
                    'revision': 2,
                    'TLP': 'WHITE',
                    'tags': ['apt', 'c2'],
                    'malware_families': ['Zeus'],
                    'attack_ids': ['T1055'],
                    'industries': ['finance'],
                    'targeted_countries': ['US'],
                    'pulse_score': 8,
                    'indicators': [
                        {
                            'indicator': 'malicious.example.com',
                            'type': 'domain',
                            'description': 'C2 domain',
                            'is_active': True,
                            'role': 'c2'
                        },
                        {
                            'indicator': '192.168.100.50',
                            'type': 'IPv4',
                            'description': 'C2 server',
                            'is_active': True,
                            'role': 'c2'
                        }
                    ]
                }
            ],
            'has_next': False
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_pulses_response):
            indicators = []
            async for indicator in self.handler.fetch_indicators():
                indicators.append(indicator)
            
            assert len(indicators) == 2
            assert indicators[0]['indicator'] == 'malicious.example.com'
            assert indicators[0]['type'] == 'domain'
            assert indicators[0]['pulse_id'] == '12345'
            assert indicators[0]['pulse_name'] == 'APT Campaign Infrastructure'
            assert indicators[0]['pulse_tags'] == ['apt', 'c2']
            assert indicators[0]['pulse_malware_families'] == ['Zeus']
            assert indicators[0]['pulse_attack_ids'] == ['T1055']
            
            assert indicators[1]['indicator'] == '192.168.100.50'
            assert indicators[1]['type'] == 'IPv4'


if __name__ == '__main__':
    pytest.main([__file__])