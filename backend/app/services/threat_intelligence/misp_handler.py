"""
MISP (Malware Information Sharing Platform) threat intelligence feed handler
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


class MISPFeedHandler(BaseThreatFeedHandler):
    """
    MISP threat intelligence feed handler
    
    Supports both MISP REST API and STIX format feeds
    """
    
    def __init__(self, feed: ThreatFeed):
        super().__init__(feed)
        self.validator = ThreatDataValidator()
        
        # MISP-specific configuration
        self.api_key = feed.api_key
        self.verify_ssl = feed.configuration.get('verify_ssl', True) if feed.configuration else True
        self.published_only = feed.configuration.get('published_only', True) if feed.configuration else True
        self.event_limit = feed.configuration.get('event_limit', 100) if feed.configuration else 100
        
        # MISP API endpoints
        self.events_endpoint = f"{feed.url.rstrip('/')}/events/restSearch"
        self.attributes_endpoint = f"{feed.url.rstrip('/')}/attributes/restSearch"
        self.health_endpoint = f"{feed.url.rstrip('/')}/servers/getVersion"
        
        self.logger = logging.getLogger(f"{__name__}.MISPFeedHandler")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get MISP-specific HTTP headers"""
        headers = super()._get_default_headers()
        if self.api_key:
            headers['Authorization'] = self.api_key
            headers['Accept'] = 'application/json'
        return headers
    
    async def authenticate(self) -> bool:
        """
        Authenticate with MISP API by testing version endpoint
        """
        try:
            response = await self._make_request(self.health_endpoint)
            
            if 'version' in response:
                self.logger.info(f"Successfully authenticated with MISP version {response.get('version')}")
                return True
            else:
                self.logger.error("MISP authentication failed: No version in response")
                return False
                
        except Exception as e:
            self.logger.error(f"MISP authentication failed: {e}")
            return False
    
    async def fetch_indicators(self, since: Optional[datetime] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Fetch threat indicators from MISP
        
        Args:
            since: Only fetch indicators updated since this timestamp
            
        Yields:
            Raw indicator data from MISP
        """
        try:
            # Build search parameters
            search_params = self._build_search_params(since)
            
            # Fetch events first
            async for event in self._fetch_events(search_params):
                # Extract attributes from each event
                async for attribute in self._extract_attributes_from_event(event):
                    yield attribute
                    
        except Exception as e:
            self.logger.error(f"Error fetching MISP indicators: {e}")
            raise
    
    def _build_search_params(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Build MISP search parameters"""
        params = {
            'returnFormat': 'json',
            'limit': self.event_limit,
            'published': self.published_only,
            'includeEventTags': True,
            'includeGalaxy': True,
            'metadata': False  # We want full event data
        }
        
        # Add timestamp filter if provided
        if since:
            # MISP expects timestamp in specific format
            params['timestamp'] = since.strftime('%Y-%m-%d')
        
        return params
    
    async def _fetch_events(self, search_params: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Fetch events from MISP
        
        Args:
            search_params: Search parameters for MISP API
            
        Yields:
            MISP event data
        """
        try:
            # Make request to events endpoint
            response = await self._make_request(
                self.events_endpoint,
                method='POST',
                json=search_params
            )
            
            # Handle different response formats
            events = []
            if isinstance(response, dict):
                if 'response' in response:
                    events = response['response']
                elif 'Event' in response:
                    events = [response]
                else:
                    events = [response]
            elif isinstance(response, list):
                events = response
            
            self.logger.info(f"Fetched {len(events)} events from MISP")
            
            for event in events:
                if isinstance(event, dict):
                    # Handle nested Event structure
                    if 'Event' in event:
                        yield event['Event']
                    else:
                        yield event
                        
        except Exception as e:
            self.logger.error(f"Error fetching MISP events: {e}")
            raise
    
    async def _extract_attributes_from_event(self, event: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Extract attributes (indicators) from a MISP event
        
        Args:
            event: MISP event data
            
        Yields:
            Individual attribute/indicator data
        """
        try:
            event_info = {
                'event_id': event.get('id'),
                'event_uuid': event.get('uuid'),
                'event_info': event.get('info'),
                'event_date': event.get('date'),
                'event_published': event.get('published'),
                'event_threat_level': event.get('threat_level_id'),
                'event_analysis': event.get('analysis'),
                'event_tags': self._extract_event_tags(event)
            }
            
            # Extract attributes
            attributes = event.get('Attribute', [])
            if not isinstance(attributes, list):
                attributes = [attributes] if attributes else []
            
            for attr in attributes:
                if self._is_valid_attribute(attr):
                    # Enrich attribute with event context
                    enriched_attr = {**attr, **event_info}
                    yield enriched_attr
            
            # Extract attributes from objects
            objects = event.get('Object', [])
            if not isinstance(objects, list):
                objects = [objects] if objects else []
            
            for obj in objects:
                async for attr in self._extract_attributes_from_object(obj, event_info):
                    yield attr
                    
        except Exception as e:
            self.logger.error(f"Error extracting attributes from event {event.get('id', 'unknown')}: {e}")
    
    async def _extract_attributes_from_object(self, obj: Dict[str, Any], 
                                           event_info: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Extract attributes from MISP objects
        
        Args:
            obj: MISP object data
            event_info: Event context information
            
        Yields:
            Individual attribute data from the object
        """
        try:
            object_info = {
                'object_name': obj.get('name'),
                'object_template_uuid': obj.get('template_uuid'),
                'object_description': obj.get('description')
            }
            
            attributes = obj.get('Attribute', [])
            if not isinstance(attributes, list):
                attributes = [attributes] if attributes else []
            
            for attr in attributes:
                if self._is_valid_attribute(attr):
                    # Enrich with both event and object context
                    enriched_attr = {**attr, **event_info, **object_info}
                    yield enriched_attr
                    
        except Exception as e:
            self.logger.error(f"Error extracting attributes from object: {e}")
    
    def _extract_event_tags(self, event: Dict[str, Any]) -> List[str]:
        """Extract tags from MISP event"""
        tags = []
        
        # Event tags
        event_tags = event.get('EventTag', [])
        if not isinstance(event_tags, list):
            event_tags = [event_tags] if event_tags else []
        
        for tag_obj in event_tags:
            if isinstance(tag_obj, dict) and 'Tag' in tag_obj:
                tag_name = tag_obj['Tag'].get('name')
                if tag_name:
                    tags.append(tag_name)
        
        # Galaxy clusters (advanced threat intelligence)
        galaxies = event.get('Galaxy', [])
        if not isinstance(galaxies, list):
            galaxies = [galaxies] if galaxies else []
        
        for galaxy in galaxies:
            galaxy_clusters = galaxy.get('GalaxyCluster', [])
            if not isinstance(galaxy_clusters, list):
                galaxy_clusters = [galaxy_clusters] if galaxy_clusters else []
            
            for cluster in galaxy_clusters:
                cluster_value = cluster.get('value')
                if cluster_value:
                    tags.append(f"galaxy:{cluster_value}")
        
        return tags
    
    def _is_valid_attribute(self, attr: Dict[str, Any]) -> bool:
        """Check if MISP attribute is valid for processing"""
        if not isinstance(attr, dict):
            return False
        
        # Must have value and type
        if not attr.get('value') or not attr.get('type'):
            return False
        
        # Skip deleted attributes
        if attr.get('deleted', False):
            return False
        
        # Skip attributes that are not for IDS (if configured)
        if not attr.get('to_ids', True):
            return False
        
        return True
    
    def normalize_indicator(self, raw_data: Dict[str, Any]) -> Optional[ThreatIndicatorCreate]:
        """
        Normalize MISP attribute data to standard format
        
        Args:
            raw_data: Raw MISP attribute data
            
        Returns:
            Normalized threat indicator or None if invalid
        """
        try:
            # Extract basic indicator data
            indicator_data = {
                'value': raw_data.get('value'),
                'type': self._map_misp_type(raw_data.get('type')),
                'category': raw_data.get('category'),
                'comment': raw_data.get('comment'),
                'first_seen': raw_data.get('first_seen'),
                'last_seen': raw_data.get('last_seen'),
                'timestamp': raw_data.get('timestamp'),
                'uuid': raw_data.get('uuid'),
                'event_id': raw_data.get('event_id'),
                'event_info': raw_data.get('event_info'),
                'event_date': raw_data.get('event_date'),
                'to_ids': raw_data.get('to_ids', False),
                'distribution': raw_data.get('distribution'),
                'sharing_group_id': raw_data.get('sharing_group_id')
            }
            
            # Add event-level tags
            event_tags = raw_data.get('event_tags', [])
            
            # Add attribute-level tags
            attr_tags = []
            attribute_tags = raw_data.get('AttributeTag', [])
            if not isinstance(attribute_tags, list):
                attribute_tags = [attribute_tags] if attribute_tags else []
            
            for tag_obj in attribute_tags:
                if isinstance(tag_obj, dict) and 'Tag' in tag_obj:
                    tag_name = tag_obj['Tag'].get('name')
                    if tag_name:
                        attr_tags.append(tag_name)
            
            # Combine all tags
            all_tags = event_tags + attr_tags
            if all_tags:
                indicator_data['tags'] = all_tags
            
            # Add threat level and analysis context
            threat_level = raw_data.get('event_threat_level')
            if threat_level:
                indicator_data['threat_level'] = threat_level
            
            analysis = raw_data.get('event_analysis')
            if analysis:
                indicator_data['analysis'] = analysis
            
            # Use the validator to normalize
            normalized = self.validator.validate_and_normalize(indicator_data, self.feed.name)
            
            if normalized:
                # Add MISP-specific metadata
                normalized.external_id = raw_data.get('uuid')
                normalized.feed_id = self.feed.id
                
                # Enhance confidence based on MISP-specific factors
                normalized.confidence = self._calculate_misp_confidence(raw_data, normalized.confidence)
                
                # Set severity based on MISP threat level
                normalized.severity = self._map_misp_threat_level(threat_level)
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing MISP indicator: {e}")
            return None
    
    def _map_misp_type(self, misp_type: str) -> str:
        """Map MISP attribute type to standard type"""
        if not misp_type:
            return 'unknown'
        
        # MISP type mapping
        type_mapping = {
            # Hashes
            'md5': 'hash',
            'sha1': 'hash', 
            'sha256': 'hash',
            'sha512': 'hash',
            'ssdeep': 'hash',
            'imphash': 'hash',
            'authentihash': 'hash',
            
            # Network
            'ip-src': 'ip',
            'ip-dst': 'ip',
            'hostname': 'domain',
            'domain': 'domain',
            'url': 'url',
            'uri': 'url',
            'email-src': 'email',
            'email-dst': 'email',
            'email-subject': 'email',
            
            # Files
            'filename': 'file',
            'filepath': 'file',
            'regkey': 'registry',
            
            # Malware
            'malware-sample': 'malware',
            'malware-type': 'malware',
            
            # Vulnerabilities
            'vulnerability': 'vulnerability',
            'cve': 'vulnerability',
            
            # MITRE ATT&CK
            'mitre-attack-pattern': 'ttp',
            'mitre-course-of-action': 'ttp',
            'mitre-intrusion-set': 'threat_actor',
            'mitre-malware': 'malware',
            'mitre-tool': 'tool'
        }
        
        return type_mapping.get(misp_type.lower(), misp_type)
    
    def _calculate_misp_confidence(self, raw_data: Dict[str, Any], base_confidence: float) -> float:
        """Calculate confidence score with MISP-specific factors"""
        confidence = base_confidence
        
        # Boost confidence for IDS-enabled attributes
        if raw_data.get('to_ids', False):
            confidence += 0.1
        
        # Boost confidence based on distribution level
        distribution = raw_data.get('distribution', 0)
        if distribution == 0:  # Your organization only
            confidence += 0.05
        elif distribution == 1:  # This community only
            confidence += 0.1
        elif distribution == 2:  # Connected communities
            confidence += 0.15
        elif distribution == 3:  # All communities
            confidence += 0.2
        
        # Boost confidence for published events
        if raw_data.get('event_published', False):
            confidence += 0.1
        
        # Adjust based on event analysis level
        analysis = raw_data.get('event_analysis', 0)
        if analysis == 2:  # Completed analysis
            confidence += 0.15
        elif analysis == 1:  # Ongoing analysis
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _map_misp_threat_level(self, threat_level: Optional[str]) -> str:
        """Map MISP threat level to severity"""
        if not threat_level:
            return 'medium'
        
        try:
            level = int(threat_level)
            if level == 1:  # High
                return 'high'
            elif level == 2:  # Medium
                return 'medium'
            elif level == 3:  # Low
                return 'low'
            elif level == 4:  # Undefined
                return 'medium'
        except (ValueError, TypeError):
            pass
        
        return 'medium'
    
    async def get_feed_info(self) -> Dict[str, Any]:
        """Get information about the MISP feed"""
        try:
            version_info = await self._make_request(self.health_endpoint)
            
            return {
                'name': self.feed.name,
                'url': self.feed.url,
                'version': version_info.get('version', 'unknown'),
                'api_version': version_info.get('perm_sync', 'unknown'),
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
            
            # Test API access (reuse authentication result)
            results['api_access'] = True
            
            # Test data retrieval
            try:
                search_params = {
                    'returnFormat': 'json',
                    'limit': 1,
                    'published': True
                }
                
                response = await self._make_request(
                    self.events_endpoint,
                    method='POST',
                    json=search_params
                )
                
                if response:
                    results['data_retrieval'] = True
                else:
                    results['errors'].append('No data returned from test query')
                    
            except Exception as e:
                results['errors'].append(f'Data retrieval failed: {e}')
        
        except Exception as e:
            results['errors'].append(f'Connection test failed: {e}')
        
        return results