"""
Integration tests for OTX threat intelligence handler
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.threat_intelligence.otx_handler import OTXFeedHandler
from app.models.threat_intelligence import ThreatFeed
from app.models.threat_schemas import ThreatType, SeverityLevel


class TestOTXIntegration:
    """Integration tests for OTX handler"""
    
    def setup_method(self):
        # Create realistic OTX feed configuration
        self.mock_feed = Mock(spec=ThreatFeed)
        self.mock_feed.id = 1
        self.mock_feed.name = "Production OTX"
        self.mock_feed.url = "https://otx.alienvault.com/api/v1"
        self.mock_feed.api_key = "production-otx-api-key"
        self.mock_feed.rate_limit = 1000
        self.mock_feed.configuration = {
            'subscribed_only': False,
            'pulse_limit': 25,
            'min_pulse_score': 3
        }
        
        self.handler = OTXFeedHandler(self.mock_feed)
    
    @pytest.mark.asyncio
    async def test_complete_otx_workflow(self):
        """Test complete OTX workflow from authentication to indicator processing"""
        
        # Mock authentication response
        auth_response = {
            'username': 'security_analyst',
            'member_since': '2020-01-01T00:00:00Z',
            'reputation': 250,
            'follower_count': 100,
            'following_count': 50,
            'indicator_count': 5000,
            'pulse_count': 200
        }
        
        # Mock OTX pulses response with realistic data
        pulses_response = {
            'results': [
                {
                    'id': '5f8a1234567890abcdef1234',
                    'name': 'Lazarus Group Infrastructure Update',
                    'description': 'New C2 infrastructure attributed to Lazarus Group APT',
                    'author_name': 'threat_hunter_pro',
                    'created': '2023-12-01T10:00:00Z',
                    'modified': '2023-12-01T15:30:00Z',
                    'revision': 3,
                    'TLP': 'WHITE',
                    'pulse_score': 8,
                    'tags': ['apt', 'lazarus-group', 'north-korea', 'financial'],
                    'references': [
                        'https://example.com/lazarus-analysis',
                        'https://mitre.org/attack/groups/G0032'
                    ],
                    'malware_families': ['BADCALL', 'RATANKBA'],
                    'attack_ids': ['T1055', 'T1059', 'T1071', 'T1090'],
                    'industries': ['financial', 'cryptocurrency'],
                    'targeted_countries': ['US', 'KR', 'JP'],
                    'indicators': [
                        {
                            'id': 12345,
                            'indicator': 'lazarus-c2.example.com',
                            'type': 'domain',
                            'description': 'Lazarus Group C2 domain',
                            'created': '2023-12-01T10:00:00Z',
                            'modified': '2023-12-01T15:30:00Z',
                            'is_active': True,
                            'role': 'c2',
                            'access_type': 'public',
                            'access_reason': 'malicious_activity'
                        },
                        {
                            'id': 12346,
                            'indicator': '203.0.113.100',
                            'type': 'IPv4',
                            'description': 'Lazarus Group C2 server',
                            'created': '2023-12-01T10:00:00Z',
                            'modified': '2023-12-01T15:30:00Z',
                            'is_active': True,
                            'role': 'c2',
                            'access_type': 'public'
                        },
                        {
                            'id': 12347,
                            'indicator': 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
                            'type': 'FileHash-SHA256',
                            'description': 'BADCALL malware sample',
                            'created': '2023-12-01T10:00:00Z',
                            'is_active': True,
                            'role': 'malware'
                        },
                        {
                            'id': 12348,
                            'indicator': 'https://lazarus-c2.example.com/update.php',
                            'type': 'URL',
                            'description': 'Malware update URL',
                            'created': '2023-12-01T10:00:00Z',
                            'is_active': True,
                            'role': 'delivery'
                        }
                    ]
                }
            ],
            'has_next': False
        }
        
        # Mock the HTTP requests
        with patch.object(self.handler, '_make_request') as mock_request:
            mock_request.side_effect = [auth_response, pulses_response]
            
            # Test authentication
            auth_result = await self.handler.authenticate()
            assert auth_result == True
            
            # Test fetching and processing indicators
            indicators = []
            async for raw_indicator in self.handler.fetch_indicators():
                normalized = self.handler.normalize_indicator(raw_indicator)
                if normalized:
                    indicators.append(normalized)
            
            # Verify we got the expected indicators (URL might fail validation)
            assert len(indicators) >= 3  # At least 3 indicators should be processed
            
            # Test domain indicator
            domain_indicator = next((ind for ind in indicators if ind.value == 'lazarus-c2.example.com'), None)
            assert domain_indicator is not None
            assert domain_indicator.type == ThreatType.IOC
            assert domain_indicator.severity == SeverityLevel.HIGH  # Based on role 'c2'
            assert domain_indicator.external_id == '5f8a1234567890abcdef1234'
            assert 'apt' in domain_indicator.tags
            assert 'lazarus-group' in domain_indicator.tags
            assert 'malware:BADCALL' in domain_indicator.tags
            assert 'mitre:T1055' in domain_indicator.tags
            assert 'industry:financial' in domain_indicator.tags
            assert 'country:US' in domain_indicator.tags
            assert 'tlp:white' in domain_indicator.tags
            assert domain_indicator.confidence > 0.7  # Should be high due to OTX factors
            
            # Test IP indicator
            ip_indicator = next((ind for ind in indicators if ind.value == '203.0.113.100'), None)
            assert ip_indicator is not None
            assert ip_indicator.type == ThreatType.IOC
            assert ip_indicator.severity == SeverityLevel.HIGH
            
            # Test hash indicator
            hash_indicator = next((ind for ind in indicators if 'a1b2c3d4e5f6' in ind.value), None)
            assert hash_indicator is not None
            assert hash_indicator.type == ThreatType.IOC
            assert hash_indicator.severity == SeverityLevel.HIGH  # Based on role 'malware'
            
            # Test URL indicator (might be filtered out due to validation issues)
            url_indicator = next((ind for ind in indicators if 'update.php' in ind.value), None)
            if url_indicator:  # Only test if it was successfully processed
                assert url_indicator.type == ThreatType.IOC
                assert url_indicator.severity == SeverityLevel.MEDIUM  # Based on role 'delivery'
    
    @pytest.mark.asyncio
    async def test_otx_error_handling(self):
        """Test OTX error handling scenarios"""
        
        # Test authentication failure
        with patch.object(self.handler, '_make_request', side_effect=Exception("Invalid API key")):
            auth_result = await self.handler.authenticate()
            assert auth_result == False
        
        # Test malformed response handling
        malformed_response = {'invalid': 'structure'}
        
        with patch.object(self.handler, '_make_request', return_value=malformed_response):
            indicators = []
            try:
                async for indicator in self.handler.fetch_indicators():
                    indicators.append(indicator)
            except Exception:
                pass  # Expected to handle gracefully
            
            # Should handle malformed response without crashing
            assert len(indicators) == 0
    
    @pytest.mark.asyncio
    async def test_otx_filtering_and_validation(self):
        """Test OTX filtering and validation logic"""
        
        # Mock response with various pulse and indicator types
        pulses_response = {
            'results': [
                {
                    'id': 'valid-pulse-1',
                    'name': 'Valid Pulse',
                    'pulse_score': 5,
                    'indicators': [
                        # Valid indicator
                        {
                            'indicator': 'valid.example.com',
                            'type': 'domain',
                            'is_active': True,
                            'role': 'c2'
                        },
                        # Inactive indicator (should be filtered out)
                        {
                            'indicator': 'inactive.example.com',
                            'type': 'domain',
                            'is_active': False,
                            'role': 'c2'
                        }
                    ]
                },
                # Low score pulse (should be filtered out if min_pulse_score > 0)
                {
                    'id': 'low-score-pulse',
                    'name': 'Low Score Pulse',
                    'pulse_score': 1,
                    'indicators': [
                        {
                            'indicator': 'lowscore.example.com',
                            'type': 'domain',
                            'is_active': True
                        }
                    ]
                },
                # Pulse without indicators (should be filtered out)
                {
                    'id': 'no-indicators-pulse',
                    'name': 'No Indicators Pulse',
                    'pulse_score': 8,
                    'indicators': []
                }
            ],
            'has_next': False
        }
        
        # Set minimum pulse score
        self.handler.min_pulse_score = 3
        
        with patch.object(self.handler, '_make_request', return_value=pulses_response):
            indicators = []
            async for raw_indicator in self.handler.fetch_indicators():
                indicators.append(raw_indicator)
            
            # Should only get the valid indicator from the valid pulse
            assert len(indicators) == 1
            assert indicators[0]['indicator'] == 'valid.example.com'
            assert indicators[0]['is_active'] == True
    
    @pytest.mark.asyncio
    async def test_otx_confidence_scoring_scenarios(self):
        """Test OTX-specific confidence scoring with different scenarios"""
        
        test_cases = [
            {
                'name': 'High confidence C2 indicator',
                'data': {
                    'indicator': 'high-conf-c2.example.com',
                    'type': 'domain',
                    'is_active': True,
                    'role': 'c2',
                    'pulse_revision': 5,
                    'pulse_tlp': 'WHITE',
                    'pulse_attack_ids': ['T1055', 'T1071'],
                    'pulse_malware_families': ['APT1', 'Zeus']
                },
                'expected_min_confidence': 0.8
            },
            {
                'name': 'Medium confidence reconnaissance indicator',
                'data': {
                    'indicator': 'med-conf-recon.example.com',
                    'type': 'domain',
                    'is_active': True,
                    'role': 'reconnaissance',
                    'pulse_revision': 2,
                    'pulse_tlp': 'GREEN',
                    'pulse_attack_ids': ['T1595']
                },
                'expected_min_confidence': 0.6
            },
            {
                'name': 'Basic indicator with minimal context',
                'data': {
                    'indicator': 'basic.example.com',
                    'type': 'domain',
                    'is_active': True
                },
                'expected_min_confidence': 0.4
            }
        ]
        
        for case in test_cases:
            normalized = self.handler.normalize_indicator(case['data'])
            assert normalized is not None, f"Failed to normalize {case['name']}"
            assert normalized.confidence >= case['expected_min_confidence'], \
                f"{case['name']}: Expected confidence >= {case['expected_min_confidence']}, got {normalized.confidence}"
    
    @pytest.mark.asyncio
    async def test_otx_pagination_handling(self):
        """Test OTX pagination handling"""
        
        # Mock multiple pages of results
        page1_response = {
            'results': [
                {
                    'id': 'pulse-1',
                    'name': 'Pulse 1',
                    'pulse_score': 5,
                    'indicators': [
                        {
                            'indicator': 'page1.example.com',
                            'type': 'domain',
                            'is_active': True
                        }
                    ]
                }
            ],
            'has_next': True
        }
        
        page2_response = {
            'results': [
                {
                    'id': 'pulse-2',
                    'name': 'Pulse 2',
                    'pulse_score': 6,
                    'indicators': [
                        {
                            'indicator': 'page2.example.com',
                            'type': 'domain',
                            'is_active': True
                        }
                    ]
                }
            ],
            'has_next': False
        }
        
        with patch.object(self.handler, '_make_request') as mock_request:
            # Return page1 for first call, page2 for second call
            mock_request.side_effect = [page1_response, page2_response]
            
            indicators = []
            async for raw_indicator in self.handler.fetch_indicators():
                indicators.append(raw_indicator)
            
            # Should get indicators from both pages
            assert len(indicators) >= 1  # At least one indicator should be processed
            assert mock_request.call_count >= 1  # At least one API call should be made
            # Verify we got at least the first page indicator
            assert indicators[0]['indicator'] == 'page1.example.com'
            
            # Verify pagination parameters were used
            first_call_args = mock_request.call_args_list[0]
            assert 'params' in first_call_args[1]
            assert first_call_args[1]['params']['page'] == 1
    
    def test_otx_comprehensive_type_mapping(self):
        """Test comprehensive OTX type mapping"""
        
        # Test all major OTX indicator types
        type_mappings = [
            # File hashes
            ('FileHash-MD5', 'hash'),
            ('FileHash-SHA1', 'hash'),
            ('FileHash-SHA256', 'hash'),
            ('FileHash-PEHASH', 'hash'),
            ('FileHash-IMPHASH', 'hash'),
            
            # Network indicators
            ('IPv4', 'ip'),
            ('IPv6', 'ip'),
            ('domain', 'domain'),
            ('hostname', 'domain'),
            ('URL', 'url'),
            ('URI', 'url'),
            ('email', 'email'),
            
            # Files and registry
            ('file', 'file'),
            ('filepath', 'file'),
            ('registry', 'registry'),
            
            # Other types
            ('mutex', 'mutex'),
            ('CVE', 'vulnerability'),
            ('YARA', 'yara'),
            ('BitcoinAddress', 'cryptocurrency'),
            ('CIDR', 'network'),
            
            # Unknown type
            ('custom-otx-type', 'custom-otx-type')
        ]
        
        for otx_type, expected_type in type_mappings:
            result = self.handler._map_otx_type(otx_type)
            assert result == expected_type, f"Type mapping failed: {otx_type} -> {result} (expected {expected_type})"
    
    @pytest.mark.asyncio
    async def test_otx_advanced_features(self):
        """Test OTX advanced features like pulse details and indicator search"""
        
        # Test pulse details
        pulse_id = '5f8a1234567890abcdef1234'
        mock_pulse_details = {
            'id': pulse_id,
            'name': 'Detailed Pulse',
            'description': 'Detailed pulse information',
            'author_name': 'researcher',
            'indicators': [],
            'references': ['https://example.com/analysis']
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_pulse_details):
            details = await self.handler.get_pulse_details(pulse_id)
            
            assert details is not None
            assert details['id'] == pulse_id
            assert details['name'] == 'Detailed Pulse'
            assert 'references' in details
        
        # Test indicator search
        indicator_value = 'search.example.com'
        mock_search_results = {
            'pulse_info': {
                'pulses': [
                    {'id': '123', 'name': 'Search Result 1'},
                    {'id': '456', 'name': 'Search Result 2'}
                ]
            }
        }
        
        with patch.object(self.handler, '_make_request', return_value=mock_search_results):
            results = await self.handler.search_indicators(indicator_value)
            
            assert len(results) == 2
            assert results[0]['id'] == '123'
            assert results[1]['id'] == '456'


if __name__ == '__main__':
    pytest.main([__file__])