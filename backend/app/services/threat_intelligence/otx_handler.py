"""
AlienVault OTX (Open Threat Exchange) threat intelligence feed handler
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, AsyncGenerator, List
import json

from app.services.threat_intelligence.base_feed_handler import BaseThreatFeedHandler
from app.services.threat_intelligence.data_validator import ThreatDataValidator
from app.models.threat_intelligence import ThreatFeed
from app.models.threat_schemas import ThreatIndicatorCreate, ThreatType


logger = logging.getLogger(__name__)


class OTXFeedHandler(BaseThreatFeedHandler):
    """
    AlienVault OTX threat intelligence feed handler
    
    Supports OTX REST API v1 for fetching pulses and indicators
    """
    
    def __init__(self, feed: ThreatFeed):
        super().__init__(feed)
        self.validator = ThreatDataValidator()
        
        # OTX-specific configuration
        self.api_key = feed.api_key
        self.subscribed_only = feed.configuration.get('subscribed_only', False) if feed.configuration else False
        self.pulse_limit = feed.configuration.get('pulse_limit', 50) if feed.configuration else 50
        self.min_pulse_score = feed.configuration.get('min_pulse_score', 0) if feed.configuration else 0
        
        # OTX API endpoints
        base_url = feed.url.rstrip('/')
        self.pulses_endpoint = f"{base_url}/pulses/subscribed" if self.subscribed_only else f"{base_url}/pulses/activity"
        self.pulse_detail_endpoint = f"{base_url}/pulses"
        self.indicators_endpoint = f"{base_url}/indicators"
        self.user_endpoint = f"{base_url}/user/me"
        
        self.logger = logging.getLogger(f"{__name__}.OTXFeedHandler")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get OTX-specific HTTP headers"""
        headers = super()._get_default_headers()
        if self.api_key:
            headers['X-OTX-API-KEY'] = self.api_key
        return headers
    
    async def authenticate(self) -> bool:
        """
        Authenticate with OTX API by testing user endpoint
        """
        try:
            response = await self._make_request(self.user_endpoint)
            
            if 'username' in response:
                self.logger.info(f"Successfully authenticated with OTX as user: {response.get('username')}")
                return True
            else:
                self.logger.error("OTX authentication failed: No username in response")
                return False
                
        except Exception as e:
            self.logger.error(f"OTX authentication failed: {e}")
            return False
    
    async def fetch_indicators(self, since: Optional[datetime] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Fetch threat indicators from OTX
        
        Args:
            since: Only fetch indicators updated since this timestamp
            
        Yields:
            Raw indicator data from OTX
        """
        try:
            # Fetch pulses first
            async for pulse in self._fetch_pulses(since):
                # Extract indicators from each pulse
                async for indicator in self._extract_indicators_from_pulse(pulse):
                    yield indicator
                    
        except Exception as e:
            self.logger.error(f"Error fetching OTX indicators: {e}")
            raise
    
    async def _fetch_pulses(self, since: Optional[datetime] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Fetch pulses from OTX
        
        Args:
            since: Only fetch pulses updated since this timestamp
            
        Yields:
            OTX pulse data
        """
        try:
            # Build query parameters
            params = {
                'limit': self.pulse_limit,
                'page': 1
            }
            
            # Add timestamp filter if provided
            if since:
                params['modified_since'] = since.strftime('%Y-%m-%dT%H:%M:%S')
            
            total_fetched = 0
            
            while total_fetched < self.max_indicators_per_run:
                # Make request to pulses endpoint
                response = await self._make_request(
                    self.pulses_endpoint,
                    params=params
                )
                
                # Extract pulses from response
                pulses = response.get('results', [])
                if not pulses:
                    break
                
                self.logger.info(f"Fetched {len(pulses)} pulses from OTX (page {params['page']})")
                
                for pulse in pulses:
                    if self._is_valid_pulse(pulse):
                        yield pulse
                        total_fetched += 1
                        
                        if total_fetched >= self.max_indicators_per_run:
                            break
                
                # Check if there are more pages
                if not response.get('has_next', False) or len(pulses) < self.pulse_limit:
                    break
                
                params['page'] += 1
                
        except Exception as e:
            self.logger.error(f"Error fetching OTX pulses: {e}")
            raise
    
    async def _extract_indicators_from_pulse(self, pulse: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Extract indicators from an OTX pulse
        
        Args:
            pulse: OTX pulse data
            
        Yields:
            Individual indicator data
        """
        try:
            # Extract pulse metadata
            pulse_info = {
                'pulse_id': pulse.get('id'),
                'pulse_name': pulse.get('name'),
                'pulse_description': pulse.get('description'),
                'pulse_author': pulse.get('author_name'),
                'pulse_created': pulse.get('created'),
                'pulse_modified': pulse.get('modified'),
                'pulse_revision': pulse.get('revision'),
                'pulse_tlp': pulse.get('TLP'),
                'pulse_tags': pulse.get('tags', []),
                'pulse_references': pulse.get('references', []),
                'pulse_malware_families': pulse.get('malware_families', []),
                'pulse_attack_ids': pulse.get('attack_ids', []),
                'pulse_industries': pulse.get('industries', []),
                'pulse_targeted_countries': pulse.get('targeted_countries', [])
            }
            
            # Extract indicators
            indicators = pulse.get('indicators', [])
            if not isinstance(indicators, list):
                indicators = [indicators] if indicators else []
            
            for indicator in indicators:
                if self._is_valid_indicator(indicator):
                    # Enrich indicator with pulse context
                    enriched_indicator = {**indicator, **pulse_info}
                    yield enriched_indicator
                    
        except Exception as e:
            self.logger.error(f"Error extracting indicators from pulse {pulse.get('id', 'unknown')}: {e}")
    
    def _is_valid_pulse(self, pulse: Dict[str, Any]) -> bool:
        """Check if OTX pulse is valid for processing"""
        if not isinstance(pulse, dict):
            return False
        
        # Must have ID and name
        if not pulse.get('id') or not pulse.get('name'):
            return False
        
        # Check minimum pulse score if configured
        pulse_score = pulse.get('pulse_score', 0)
        if pulse_score < self.min_pulse_score:
            return False
        
        # Must have indicators
        indicators = pulse.get('indicators', [])
        if not indicators:
            return False
        
        return True
    
    def _is_valid_indicator(self, indicator: Dict[str, Any]) -> bool:
        """Check if OTX indicator is valid for processing"""
        if not isinstance(indicator, dict):
            return False
        
        # Must have indicator value and type
        if not indicator.get('indicator') or not indicator.get('type'):
            return False
        
        # Skip inactive indicators
        if not indicator.get('is_active', True):
            return False
        
        return True
    
    def normalize_indicator(self, raw_data: Dict[str, Any]) -> Optional[ThreatIndicatorCreate]:
        """
        Normalize OTX indicator data to standard format
        
        Args:
            raw_data: Raw OTX indicator data
            
        Returns:
            Normalized threat indicator or None if invalid
        """
        try:
            # Extract basic indicator data
            indicator_data = {
                'value': raw_data.get('indicator'),
                'type': self._map_otx_type(raw_data.get('type')),
                'description': raw_data.get('description') or raw_data.get('pulse_description'),
                'title': raw_data.get('title') or raw_data.get('pulse_name'),
                'created': raw_data.get('created'),
                'modified': raw_data.get('modified'),
                'pulse_id': raw_data.get('pulse_id'),
                'pulse_name': raw_data.get('pulse_name'),
                'pulse_author': raw_data.get('pulse_author'),
                'pulse_created': raw_data.get('pulse_created'),
                'pulse_modified': raw_data.get('pulse_modified'),
                'pulse_tlp': raw_data.get('pulse_tlp'),
                'is_active': raw_data.get('is_active', True),
                'role': raw_data.get('role'),
                'access_type': raw_data.get('access_type'),
                'access_reason': raw_data.get('access_reason')
            }
            
            # Combine tags from multiple sources
            all_tags = []
            
            # Pulse tags
            pulse_tags = raw_data.get('pulse_tags', [])
            if pulse_tags:
                all_tags.extend(pulse_tags)
            
            # Malware families
            malware_families = raw_data.get('pulse_malware_families', [])
            if malware_families:
                all_tags.extend([f"malware:{family}" for family in malware_families])
            
            # Attack IDs (MITRE ATT&CK)
            attack_ids = raw_data.get('pulse_attack_ids', [])
            if attack_ids:
                all_tags.extend([f"mitre:{attack_id}" for attack_id in attack_ids])
            
            # Industries
            industries = raw_data.get('pulse_industries', [])
            if industries:
                all_tags.extend([f"industry:{industry}" for industry in industries])
            
            # Targeted countries
            countries = raw_data.get('pulse_targeted_countries', [])
            if countries:
                all_tags.extend([f"country:{country}" for country in countries])
            
            if all_tags:
                indicator_data['tags'] = all_tags
            
            # Add TLP as a tag if present
            tlp = raw_data.get('pulse_tlp')
            if tlp:
                if not indicator_data.get('tags'):
                    indicator_data['tags'] = []
                indicator_data['tags'].append(f"tlp:{tlp.lower()}")
            
            # Use the validator to normalize
            normalized = self.validator.validate_and_normalize(indicator_data, self.feed.name)
            
            if normalized:
                # Add OTX-specific metadata
                normalized.external_id = str(raw_data.get('pulse_id', ''))
                normalized.feed_id = self.feed.id
                
                # Enhance confidence based on OTX-specific factors
                normalized.confidence = self._calculate_otx_confidence(raw_data, normalized.confidence)
                
                # Set severity based on OTX factors
                normalized.severity = self._determine_otx_severity(raw_data)
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing OTX indicator: {e}")
            return None
    
    def _map_otx_type(self, otx_type: str) -> str:
        """Map OTX indicator type to standard type"""
        if not otx_type:
            return 'unknown'
        
        # OTX type mapping
        type_mapping = {
            # Hashes
            'FileHash-MD5': 'hash',
            'FileHash-SHA1': 'hash',
            'FileHash-SHA256': 'hash',
            'FileHash-PEHASH': 'hash',
            'FileHash-IMPHASH': 'hash',
            
            # Network
            'IPv4': 'ip',
            'IPv6': 'ip',
            'domain': 'domain',
            'hostname': 'domain',
            'URL': 'url',
            'URI': 'url',
            'email': 'email',
            
            # Files
            'file': 'file',
            'filepath': 'file',
            
            # Registry
            'registry': 'registry',
            
            # Mutex
            'mutex': 'mutex',
            
            # CVE
            'CVE': 'vulnerability',
            
            # YARA
            'YARA': 'yara',
            
            # Bitcoin
            'BitcoinAddress': 'cryptocurrency',
            
            # CIDR
            'CIDR': 'network'
        }
        
        return type_mapping.get(otx_type, otx_type.lower())
    
    def _calculate_otx_confidence(self, raw_data: Dict[str, Any], base_confidence: float) -> float:
        """Calculate confidence score with OTX-specific factors"""
        confidence = base_confidence
        
        # Boost confidence for active indicators
        if raw_data.get('is_active', True):
            confidence += 0.1
        
        # Boost confidence based on pulse revision (more revisions = more vetted)
        revision = raw_data.get('pulse_revision', 0)
        if revision > 1:
            confidence += min(0.1, revision * 0.02)
        
        # Boost confidence for indicators with specific roles
        role = raw_data.get('role')
        if role:
            if role in ['malware', 'c2', 'exploit']:
                confidence += 0.15
            elif role in ['reconnaissance', 'weaponization']:
                confidence += 0.1
        
        # Boost confidence based on TLP level (higher sharing = more trusted)
        tlp = raw_data.get('pulse_tlp', '').upper()
        if tlp == 'WHITE':
            confidence += 0.1
        elif tlp == 'GREEN':
            confidence += 0.05
        
        # Boost confidence for indicators with MITRE ATT&CK mapping
        attack_ids = raw_data.get('pulse_attack_ids', [])
        if attack_ids:
            confidence += 0.1
        
        # Boost confidence for indicators with malware family attribution
        malware_families = raw_data.get('pulse_malware_families', [])
        if malware_families:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _determine_otx_severity(self, raw_data: Dict[str, Any]) -> str:
        """Determine severity based on OTX factors"""
        
        # Check role-based severity
        role = raw_data.get('role', '').lower()
        if role in ['malware', 'c2', 'exploit']:
            return 'high'
        elif role in ['reconnaissance', 'weaponization', 'delivery']:
            return 'medium'
        
        # Check malware family presence
        malware_families = raw_data.get('pulse_malware_families', [])
        if malware_families:
            return 'high'
        
        # Check MITRE ATT&CK techniques
        attack_ids = raw_data.get('pulse_attack_ids', [])
        if attack_ids:
            return 'medium'
        
        # Check TLP level
        tlp = raw_data.get('pulse_tlp', '').upper()
        if tlp in ['RED', 'AMBER']:
            return 'high'
        elif tlp == 'GREEN':
            return 'medium'
        
        return 'medium'  # Default
    
    async def get_feed_info(self) -> Dict[str, Any]:
        """Get information about the OTX feed"""
        try:
            user_info = await self._make_request(self.user_endpoint)
            
            return {
                'name': self.feed.name,
                'url': self.feed.url,
                'username': user_info.get('username', 'unknown'),
                'member_since': user_info.get('member_since'),
                'reputation': user_info.get('reputation', 0),
                'follower_count': user_info.get('follower_count', 0),
                'following_count': user_info.get('following_count', 0),
                'indicator_count': user_info.get('indicator_count', 0),
                'pulse_count': user_info.get('pulse_count', 0),
                'status': 'connected',
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'name': self.feed.name,
                'url': self.feed.url,
                'status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    async def test_connection_detailed(self) -> Dict[str, Any]:
        """Perform detailed connection test"""
        results = {
            'authentication': False,
            'api_access': False,
            'data_retrieval': False,
            'errors': []
        }
        
        try:
            # Test authentication
            if await self.authenticate():
                results['authentication'] = True
            else:
                results['errors'].append('Authentication failed')
                return results
            
            # API access is confirmed by successful authentication
            results['api_access'] = True
            
            # Test data retrieval
            try:
                params = {'limit': 1}
                response = await self._make_request(self.pulses_endpoint, params=params)
                
                if 'results' in response:
                    results['data_retrieval'] = True
                else:
                    results['errors'].append('No results in pulse response')
                    
            except Exception as e:
                results['errors'].append(f'Data retrieval failed: {e}')
        
        except Exception as e:
            results['errors'].append(f'Connection test failed: {e}')
        
        return results
    
    async def get_pulse_details(self, pulse_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific pulse
        
        Args:
            pulse_id: OTX pulse ID
            
        Returns:
            Detailed pulse information or None if not found
        """
        try:
            url = f"{self.pulse_detail_endpoint}/{pulse_id}"
            response = await self._make_request(url)
            return response
            
        except Exception as e:
            self.logger.error(f"Error fetching pulse details for {pulse_id}: {e}")
            return None
    
    async def search_indicators(self, indicator_value: str, 
                              indicator_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for specific indicators in OTX
        
        Args:
            indicator_value: The indicator value to search for
            indicator_type: Optional indicator type filter
            
        Returns:
            List of matching indicators
        """
        try:
            # Build search URL
            if indicator_type:
                url = f"{self.indicators_endpoint}/{indicator_type}/{indicator_value}"
            else:
                url = f"{self.indicators_endpoint}/search/{indicator_value}"
            
            response = await self._make_request(url)
            
            # Extract indicators from response
            if isinstance(response, dict):
                return response.get('pulse_info', {}).get('pulses', [])
            elif isinstance(response, list):
                return response
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error searching for indicator {indicator_value}: {e}")
            return []