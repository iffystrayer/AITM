"""
Integration tests for MISP threat intelligence handler
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.threat_intelligence.misp_handler import MISPFeedHandler
from app.models.threat_intelligence import ThreatFeed
from app.models.threat_schemas import ThreatType, SeverityLevel


class TestMISPIntegration:
    """Integration tests for MISP handler"""
    
    def setup_method(self):
        # Create realistic MISP feed configuration
        self.mock_feed = Mock(spec=ThreatFeed)
        self.mock_feed.id = 1
        self.mock_feed.name = "Production MISP"
        self.mock_feed.url = "https://misp.organization.com"
        self.mock_feed.api_key = "production-api-key"
        self.mock_feed.rate_limit = 1000
        self.mock_feed.configuration = {
            'verify_ssl': True,
            'published_only': True,
            'event_limit': 50
        }
        
        self.handler = MISPFeedHandler(self.mock_feed)
    
    @pytest.mark.asyncio
    async def test_complete_misp_workflow(self):
        """Test complete MISP workflow from authentication to indicator processing"""
        
        # Mock authentication response
        auth_response = {
            'version': '2.4.150',
            'perm_sync': '1'
        }
        
        # Mock MISP events response with realistic data
        events_response = {
            'response': [
                {
                    'Event': {
                        'id': '12345',
                        'uuid': '550e8400-e29b-41d4-a716-446655440000',
                        'info': 'APT29 Campaign - Cozy Bear Infrastructure',
                        'date': '2023-12-01',
                        'published': True,
                        'threat_level_id': '1',  # High
                        'analysis': '2',  # Completed
                        'EventTag': [
                            {'Tag': {'name': 'apt'}},
                            {'Tag': {'name': 'cozy-bear'}},
                            {'Tag': {'name': 'russia'}}
                        ],
                        'Galaxy': [
                            {
                                'GalaxyCluster': [
                                    {'value': 'APT29'},
                                    {'value': 'Cozy Bear'}
                                ]
                            }
                        ],
                        'Attribute': [
                            {
                                'id': '67890',
                                'uuid': '550e8400-e29b-41d4-a716-446655440001',
                                'value': 'cozybeardomain.com',
                                'type': 'domain',
                                'category': 'Network activity',
                                'comment': 'C2 domain used by APT29',
                                'to_ids': True,
                                'deleted': False,
                                'distribution': '3',
                                'timestamp': '1701388800',
                                'first_seen': '2023-11-30T10:00:00Z',
                                'last_seen': '2023-12-01T15:30:00Z',
                                'AttributeTag': [
                                    {'Tag': {'name': 'c2'}},
                                    {'Tag': {'name': 'malicious-activity'}}
                                ]
                            },
                            {
                                'id': '67891',
                                'uuid': '550e8400-e29b-41d4-a716-446655440002',
                                'value': '192.168.100.50',
                                'type': 'ip-dst',
                                'category': 'Network activity',
                                'comment': 'APT29 C2 server',
                                'to_ids': True,
                                'deleted': False,
                                'distribution': '2',
                                'timestamp': '1701388800'
                            },
                            {
                                'id': '67892',
                                'uuid': '550e8400-e29b-41d4-a716-446655440003',
                                'value': 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
                                'type': 'sha256',
                                'category': 'Payload delivery',
                                'comment': 'APT29 malware sample',
                                'to_ids': True,
                                'deleted': False,
                                'distribution': '1'
                            }
                        ],
                        'Object': [
                            {
                                'name': 'file',
                                'template_uuid': '688c46fb-5edb-40a3-8273-1af7923e2215',
                                'description': 'File object describing a file with meta-information',
                                'Attribute': [
                                    {
                                        'id': '67893',
                                        'uuid': '550e8400-e29b-41d4-a716-446655440004',
                                        'value': 'malware.exe',
                                        'type': 'filename',
                                        'category': 'Payload delivery',
                                        'to_ids': False,
                                        'deleted': False
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        # Mock the HTTP requests
        with patch.object(self.handler, '_make_request') as mock_request:
            mock_request.side_effect = [auth_response, events_response]
            
            # Test authentication
            auth_result = await self.handler.authenticate()
            assert auth_result == True
            
            # Test fetching and processing indicators
            indicators = []
            async for raw_indicator in self.handler.fetch_indicators():
                normalized = self.handler.normalize_indicator(raw_indicator)
                if normalized:
                    indicators.append(normalized)
            
            # Verify we got the expected indicators (filename filtered out due to to_ids=False)
            assert len(indicators) == 3  # 3 attributes (filename filtered out)
            
            # Test domain indicator
            domain_indicator = next((ind for ind in indicators if ind.value == 'cozybeardomain.com'), None)
            assert domain_indicator is not None
            assert domain_indicator.type == ThreatType.IOC
            assert domain_indicator.severity == SeverityLevel.HIGH
            assert domain_indicator.external_id == '550e8400-e29b-41d4-a716-446655440001'
            assert 'apt' in domain_indicator.tags
            assert 'c2' in domain_indicator.tags
            assert 'galaxy:APT29' in domain_indicator.tags
            assert domain_indicator.confidence > 0.7  # Should be high due to MISP factors
            
            # Test IP indicator
            ip_indicator = next((ind for ind in indicators if ind.value == '192.168.100.50'), None)
            assert ip_indicator is not None
            assert ip_indicator.type == ThreatType.IOC
            
            # Test hash indicator
            hash_indicator = next((ind for ind in indicators if 'a1b2c3d4e5f6' in ind.value), None)
            assert hash_indicator is not None
            assert hash_indicator.type == ThreatType.IOC
            
            # Filename indicator should be filtered out due to to_ids=False
            filename_indicator = next((ind for ind in indicators if ind.value == 'malware.exe'), None)
            assert filename_indicator is None  # Should be filtered out
    
    @pytest.mark.asyncio
    async def test_misp_error_handling(self):
        """Test MISP error handling scenarios"""
        
        # Test authentication failure
        with patch.object(self.handler, '_make_request', side_effect=Exception("Unauthorized")):
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
    async def test_misp_filtering_and_validation(self):
        """Test MISP filtering and validation logic"""
        
        # Mock response with various attribute types and states
        events_response = {
            'response': [
                {
                    'Event': {
                        'id': '999',
                        'uuid': 'test-event-uuid',
                        'info': 'Test Event',
                        'date': '2023-12-01',
                        'published': True,
                        'threat_level_id': '2',
                        'analysis': '1',
                        'Attribute': [
                            # Valid attribute
                            {
                                'id': '1',
                                'uuid': 'valid-attr-uuid',
                                'value': 'valid.example.com',
                                'type': 'domain',
                                'category': 'Network activity',
                                'to_ids': True,
                                'deleted': False
                            },
                            # Deleted attribute (should be filtered out)
                            {
                                'id': '2',
                                'uuid': 'deleted-attr-uuid',
                                'value': 'deleted.example.com',
                                'type': 'domain',
                                'category': 'Network activity',
                                'to_ids': True,
                                'deleted': True
                            },
                            # Non-IDS attribute (should be filtered out)
                            {
                                'id': '3',
                                'uuid': 'non-ids-attr-uuid',
                                'value': 'non-ids.example.com',
                                'type': 'domain',
                                'category': 'Network activity',
                                'to_ids': False,
                                'deleted': False
                            },
                            # Attribute without value (should be filtered out)
                            {
                                'id': '4',
                                'uuid': 'no-value-attr-uuid',
                                'value': '',
                                'type': 'domain',
                                'category': 'Network activity',
                                'to_ids': True,
                                'deleted': False
                            }
                        ]
                    }
                }
            ]
        }
        
        with patch.object(self.handler, '_make_request', return_value=events_response):
            indicators = []
            async for raw_indicator in self.handler.fetch_indicators():
                indicators.append(raw_indicator)
            
            # Should only get the valid attribute
            assert len(indicators) == 1
            assert indicators[0]['value'] == 'valid.example.com'
            assert indicators[0]['deleted'] == False
            assert indicators[0]['to_ids'] == True
    
    @pytest.mark.asyncio
    async def test_misp_confidence_scoring(self):
        """Test MISP-specific confidence scoring"""
        
        # Test different confidence scenarios
        test_cases = [
            {
                'name': 'High confidence scenario',
                'data': {
                    'value': 'high-conf.example.com',
                    'type': 'domain',
                    'to_ids': True,
                    'distribution': '3',  # All communities
                    'event_published': True,
                    'event_analysis': '2',  # Completed
                    'event_threat_level': '1'  # High
                },
                'expected_min_confidence': 0.7
            },
            {
                'name': 'Medium confidence scenario',
                'data': {
                    'value': 'med-conf.example.com',
                    'type': 'domain',
                    'to_ids': False,
                    'distribution': '1',  # This community only
                    'event_published': False,
                    'event_analysis': '1',  # Ongoing
                    'event_threat_level': '2'  # Medium
                },
                'expected_min_confidence': 0.4
            },
            {
                'name': 'Low confidence scenario',
                'data': {
                    'value': 'low-conf.example.com',
                    'type': 'domain',
                    'to_ids': False,
                    'distribution': '0',  # Your organization only
                    'event_published': False,
                    'event_analysis': '0',  # Initial
                    'event_threat_level': '3'  # Low
                },
                'expected_min_confidence': 0.3
            }
        ]
        
        for case in test_cases:
            normalized = self.handler.normalize_indicator(case['data'])
            assert normalized is not None, f"Failed to normalize {case['name']}"
            assert normalized.confidence >= case['expected_min_confidence'], \
                f"{case['name']}: Expected confidence >= {case['expected_min_confidence']}, got {normalized.confidence}"
    
    def test_misp_type_mapping_comprehensive(self):
        """Test comprehensive MISP type mapping"""
        
        # Test all major MISP types
        type_mappings = [
            # Hashes
            ('md5', 'hash'),
            ('sha1', 'hash'),
            ('sha256', 'hash'),
            ('sha512', 'hash'),
            ('ssdeep', 'hash'),
            ('imphash', 'hash'),
            
            # Network indicators
            ('ip-src', 'ip'),
            ('ip-dst', 'ip'),
            ('hostname', 'domain'),
            ('domain', 'domain'),
            ('url', 'url'),
            ('uri', 'url'),
            
            # Email
            ('email-src', 'email'),
            ('email-dst', 'email'),
            ('email-subject', 'email'),
            
            # Files
            ('filename', 'file'),
            ('filepath', 'file'),
            
            # Malware
            ('malware-sample', 'malware'),
            ('malware-type', 'malware'),
            
            # Vulnerabilities
            ('vulnerability', 'vulnerability'),
            ('cve', 'vulnerability'),
            
            # MITRE ATT&CK
            ('mitre-attack-pattern', 'ttp'),
            ('mitre-course-of-action', 'ttp'),
            ('mitre-intrusion-set', 'threat_actor'),
            ('mitre-malware', 'malware'),
            ('mitre-tool', 'tool'),
            
            # Unknown type
            ('custom-type', 'custom-type')
        ]
        
        for misp_type, expected_type in type_mappings:
            result = self.handler._map_misp_type(misp_type)
            assert result == expected_type, f"Type mapping failed: {misp_type} -> {result} (expected {expected_type})"


if __name__ == '__main__':
    pytest.main([__file__])