"""
Threat intelligence data validation and normalization
"""

import re
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from ipaddress import ip_address, ip_network, AddressValueError
from urllib.parse import urlparse

from app.models.threat_schemas import ThreatIndicatorCreate, ThreatType, SeverityLevel


logger = logging.getLogger(__name__)


class ThreatDataValidator:
    """
    Validates and normalizes threat intelligence data
    """
    
    # Regex patterns for different indicator types
    PATTERNS = {
        'md5': re.compile(r'^[a-fA-F0-9]{32}$'),
        'sha1': re.compile(r'^[a-fA-F0-9]{40}$'),
        'sha256': re.compile(r'^[a-fA-F0-9]{64}$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'domain': re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'),
        'cve': re.compile(r'^CVE-\d{4}-\d{4,}$'),
        'mitre_technique': re.compile(r'^T\d{4}(\.\d{3})?$'),
    }
    
    # Confidence scoring weights
    CONFIDENCE_WEIGHTS = {
        'source_reputation': 0.2,
        'data_completeness': 0.15,
        'validation_score': 0.4,  # Higher weight for explicit confidence
        'freshness': 0.15,
        'context_richness': 0.1
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_and_normalize(self, raw_data: Dict[str, Any], source: str) -> Optional[ThreatIndicatorCreate]:
        """
        Validate and normalize raw threat indicator data
        
        Args:
            raw_data: Raw indicator data from feed
            source: Source feed name
            
        Returns:
            Normalized threat indicator or None if invalid
        """
        try:
            # Basic validation
            if not self._basic_validation(raw_data):
                return None
            
            # Extract and validate indicator value
            indicator_value = self._extract_indicator_value(raw_data)
            if not indicator_value:
                return None
            
            # Determine indicator type
            indicator_type = self._determine_indicator_type(indicator_value, raw_data)
            if not indicator_type:
                return None
            
            # Normalize the indicator value
            normalized_value = self._normalize_indicator_value(indicator_value, indicator_type)
            
            # Extract metadata
            title = self._extract_title(raw_data)
            description = self._extract_description(raw_data)
            tags = self._extract_tags(raw_data)
            kill_chain_phases = self._extract_kill_chain_phases(raw_data)
            
            # Extract temporal data
            first_seen, last_seen = self._extract_temporal_data(raw_data)
            valid_from, valid_until = self._extract_validity_period(raw_data)
            
            # Calculate confidence and severity
            confidence = self._calculate_confidence(raw_data, source)
            severity = self._determine_severity(raw_data, indicator_type)
            
            # Create normalized indicator
            normalized_indicator = ThreatIndicatorCreate(
                external_id=self._extract_external_id(raw_data),
                feed_id=0,  # Will be set by the handler
                type=indicator_type,
                value=normalized_value,
                confidence=confidence,
                severity=severity,
                title=title,
                description=description,
                tags=tags,
                kill_chain_phases=kill_chain_phases,
                first_seen=first_seen,
                last_seen=last_seen,
                valid_from=valid_from,
                valid_until=valid_until,
                source=source,
                source_confidence=self._get_source_confidence(source),
                raw_data=raw_data
            )
            
            return normalized_indicator
            
        except Exception as e:
            self.logger.error(f"Error normalizing indicator: {e}")
            return None
    
    def _basic_validation(self, data: Dict[str, Any]) -> bool:
        """Basic validation of raw data structure"""
        if not isinstance(data, dict):
            return False
        
        # Must have some form of indicator value
        value_fields = ['value', 'indicator', 'ioc', 'observable', 'pattern']
        if not any(field in data for field in value_fields):
            return False
        
        return True
    
    def _extract_indicator_value(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract the main indicator value from raw data"""
        value_fields = ['value', 'indicator', 'ioc', 'observable', 'pattern']
        
        for field in value_fields:
            if field in data and data[field]:
                value = str(data[field]).strip()
                if value:
                    return value
        
        return None
    
    def _determine_indicator_type(self, value: str, raw_data: Dict[str, Any]) -> Optional[ThreatType]:
        """Determine the type of threat indicator"""
        
        # Check explicit type field first
        type_fields = ['type', 'indicator_type', 'category', 'kind']
        for field in type_fields:
            if field in raw_data:
                explicit_type = self._map_explicit_type(str(raw_data[field]).lower())
                if explicit_type:
                    return explicit_type
        
        # Pattern-based detection
        value_lower = value.lower()
        
        # Hash patterns
        if self.PATTERNS['md5'].match(value):
            return ThreatType.IOC
        elif self.PATTERNS['sha1'].match(value):
            return ThreatType.IOC
        elif self.PATTERNS['sha256'].match(value):
            return ThreatType.IOC
        
        # CVE (check before network indicators)
        elif self.PATTERNS['cve'].match(value):
            return ThreatType.VULNERABILITY
        
        # MITRE ATT&CK technique (check before network indicators)
        elif self.PATTERNS['mitre_technique'].match(value):
            return ThreatType.TTP
        
        # Network indicators
        elif self._is_ip_address(value):
            return ThreatType.IOC
        elif self._is_domain(value):
            return ThreatType.IOC
        elif self._is_url(value):
            return ThreatType.IOC
        
        # Email
        elif self.PATTERNS['email'].match(value):
            return ThreatType.IOC
        

        
        # Default to IOC if we can't determine
        return ThreatType.IOC
    
    def _map_explicit_type(self, type_str: str) -> Optional[ThreatType]:
        """Map explicit type strings to ThreatType enum"""
        type_mapping = {
            'ioc': ThreatType.IOC,
            'indicator': ThreatType.IOC,
            'hash': ThreatType.IOC,
            'file': ThreatType.IOC,
            'ip': ThreatType.IOC,
            'domain': ThreatType.IOC,
            'url': ThreatType.IOC,
            'email': ThreatType.IOC,
            'malware': ThreatType.MALWARE,
            'vulnerability': ThreatType.VULNERABILITY,
            'cve': ThreatType.VULNERABILITY,
            'ttp': ThreatType.TTP,
            'technique': ThreatType.TTP,
            'tactic': ThreatType.TTP,
            'campaign': ThreatType.CAMPAIGN,
            'threat_actor': ThreatType.THREAT_ACTOR,
            'actor': ThreatType.THREAT_ACTOR,
            'infrastructure': ThreatType.INFRASTRUCTURE
        }
        
        return type_mapping.get(type_str)
    
    def _normalize_indicator_value(self, value: str, indicator_type: ThreatType) -> str:
        """Normalize indicator value based on type"""
        
        if indicator_type == ThreatType.IOC:
            # Hash normalization
            if any(self.PATTERNS[hash_type].match(value) for hash_type in ['md5', 'sha1', 'sha256']):
                return value.lower()
            
            # Domain normalization
            elif self._is_domain(value):
                return value.lower().strip('.')
            
            # IP normalization
            elif self._is_ip_address(value):
                try:
                    return str(ip_address(value))
                except AddressValueError:
                    pass
            
            # URL normalization
            elif self._is_url(value):
                return value.lower()
            
            # Email normalization
            elif self.PATTERNS['email'].match(value):
                return value.lower()
        
        # Default: strip and lowercase
        return value.strip().lower()
    
    def _extract_title(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract title/name from raw data"""
        title_fields = ['title', 'name', 'summary', 'label']
        
        for field in title_fields:
            if field in data and data[field]:
                title = str(data[field]).strip()
                if title:
                    return title[:500]  # Limit length
        
        return None
    
    def _extract_description(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract description from raw data"""
        desc_fields = ['description', 'details', 'comment', 'notes']
        
        for field in desc_fields:
            if field in data and data[field]:
                desc = str(data[field]).strip()
                if desc:
                    return desc
        
        return None
    
    def _extract_tags(self, data: Dict[str, Any]) -> Optional[List[str]]:
        """Extract tags from raw data"""
        tags = []
        tag_fields = ['tags', 'labels', 'categories', 'malware_families', 'groups']
        
        for field in tag_fields:
            if field in data:
                field_data = data[field]
                if isinstance(field_data, list):
                    tags.extend([str(tag).strip() for tag in field_data])
                elif isinstance(field_data, str):
                    # Handle comma-separated tags
                    tags.extend([tag.strip() for tag in field_data.split(',')])
        
        # Clean and deduplicate
        clean_tags = list(set(tag for tag in tags if tag and len(tag) > 0))
        return clean_tags if clean_tags else None
    
    def _extract_kill_chain_phases(self, data: Dict[str, Any]) -> Optional[List[str]]:
        """Extract kill chain phases from raw data"""
        phases = []
        phase_fields = ['kill_chain_phases', 'tactics', 'phases']
        
        for field in phase_fields:
            if field in data:
                field_data = data[field]
                if isinstance(field_data, list):
                    for phase in field_data:
                        if isinstance(phase, dict) and 'phase_name' in phase:
                            phases.append(phase['phase_name'])
                        elif isinstance(phase, str):
                            phases.append(phase)
                elif isinstance(field_data, str):
                    phases.append(field_data)
        
        return phases if phases else None
    
    def _extract_temporal_data(self, data: Dict[str, Any]) -> Tuple[datetime, datetime]:
        """Extract first_seen and last_seen timestamps"""
        now = datetime.utcnow()
        
        # Extract first_seen
        first_seen = None
        first_seen_fields = ['first_seen', 'created', 'created_at', 'first_observed']
        for field in first_seen_fields:
            if field in data:
                first_seen = self._parse_datetime(data[field])
                if first_seen:
                    break
        
        # Extract last_seen
        last_seen = None
        last_seen_fields = ['last_seen', 'updated', 'updated_at', 'last_observed', 'modified']
        for field in last_seen_fields:
            if field in data:
                last_seen = self._parse_datetime(data[field])
                if last_seen:
                    break
        
        # Set defaults
        if not first_seen:
            first_seen = now
        if not last_seen:
            last_seen = first_seen
        
        # Ensure last_seen >= first_seen
        if last_seen < first_seen:
            last_seen = first_seen
        
        return first_seen, last_seen
    
    def _extract_validity_period(self, data: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Extract validity period from raw data"""
        valid_from = None
        valid_until = None
        
        # Extract valid_from
        valid_from_fields = ['valid_from', 'valid_after', 'start_time']
        for field in valid_from_fields:
            if field in data:
                valid_from = self._parse_datetime(data[field])
                if valid_from:
                    break
        
        # Extract valid_until
        valid_until_fields = ['valid_until', 'valid_before', 'end_time', 'expires']
        for field in valid_until_fields:
            if field in data:
                valid_until = self._parse_datetime(data[field])
                if valid_until:
                    break
        
        return valid_from, valid_until
    
    def _extract_external_id(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract external ID from raw data"""
        id_fields = ['id', 'uuid', 'external_id', 'object_id']
        
        for field in id_fields:
            if field in data and data[field]:
                return str(data[field])
        
        return None
    
    def _calculate_confidence(self, data: Dict[str, Any], source: str) -> float:
        """Calculate confidence score for the indicator"""
        scores = {}
        
        # Source reputation score
        scores['source_reputation'] = self._get_source_confidence(source)
        
        # Data completeness score
        scores['data_completeness'] = self._calculate_completeness_score(data)
        
        # Validation score
        scores['validation_score'] = self._calculate_validation_score(data)
        
        # Freshness score
        scores['freshness'] = self._calculate_freshness_score(data)
        
        # Context richness score
        scores['context_richness'] = self._calculate_context_score(data)
        
        # Weighted average
        confidence = sum(
            scores[factor] * weight 
            for factor, weight in self.CONFIDENCE_WEIGHTS.items()
        )
        
        return max(0.0, min(1.0, confidence))
    
    def _get_source_confidence(self, source: str) -> float:
        """Get confidence score based on source reputation"""
        source_scores = {
            'misp': 0.9,
            'alienvault': 0.8,
            'otx': 0.8,
            'virustotal': 0.85,
            'mandiant': 0.95,
            'crowdstrike': 0.95,
            'fireeye': 0.9,
            'default': 0.7
        }
        
        source_lower = source.lower()
        for known_source, score in source_scores.items():
            if known_source in source_lower:
                return score
        
        return source_scores['default']
    
    def _calculate_completeness_score(self, data: Dict[str, Any]) -> float:
        """Calculate score based on data completeness"""
        important_fields = [
            'description', 'title', 'tags', 'first_seen', 'last_seen',
            'confidence', 'severity', 'type'
        ]
        
        present_fields = sum(1 for field in important_fields if field in data and data[field])
        return present_fields / len(important_fields)
    
    def _calculate_validation_score(self, data: Dict[str, Any]) -> float:
        """Calculate score based on data validation"""
        score = 0.5  # Base score
        
        # Bonus for explicit confidence - use the actual confidence value
        if 'confidence' in data:
            try:
                conf = float(data['confidence'])
                if 0 <= conf <= 1:
                    # Use explicit confidence as a major factor
                    score = conf * 0.8 + score * 0.2
            except (ValueError, TypeError):
                pass
        
        # Bonus for structured data
        if isinstance(data.get('tags'), list):
            score += 0.1
        
        if isinstance(data.get('kill_chain_phases'), list):
            score += 0.1
        
        # Bonus for temporal data
        if 'first_seen' in data or 'created' in data:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_freshness_score(self, data: Dict[str, Any]) -> float:
        """Calculate score based on data freshness"""
        now = datetime.utcnow()
        
        # Try to find the most recent timestamp
        timestamp_fields = ['last_seen', 'updated', 'modified', 'created']
        latest_time = None
        
        for field in timestamp_fields:
            if field in data:
                parsed_time = self._parse_datetime(data[field])
                if parsed_time and (not latest_time or parsed_time > latest_time):
                    latest_time = parsed_time
        
        if not latest_time:
            return 0.5  # Default score if no timestamp
        
        # Calculate age in days
        age_days = (now - latest_time).days
        
        # Scoring based on age
        if age_days <= 1:
            return 1.0
        elif age_days <= 7:
            return 0.9
        elif age_days <= 30:
            return 0.7
        elif age_days <= 90:
            return 0.5
        else:
            return 0.3
    
    def _calculate_context_score(self, data: Dict[str, Any]) -> float:
        """Calculate score based on context richness"""
        context_fields = [
            'description', 'tags', 'kill_chain_phases', 'malware_families',
            'references', 'related_indicators', 'campaigns'
        ]
        
        context_count = sum(1 for field in context_fields if field in data and data[field])
        return min(1.0, context_count / len(context_fields) * 2)  # Scale up
    
    def _determine_severity(self, data: Dict[str, Any], indicator_type: ThreatType) -> SeverityLevel:
        """Determine severity level for the indicator"""
        
        # Check explicit severity
        severity_fields = ['severity', 'priority', 'risk', 'threat_level']
        for field in severity_fields:
            if field in data:
                explicit_severity = self._map_explicit_severity(str(data[field]).lower())
                if explicit_severity:
                    return explicit_severity
        
        # Infer from confidence and type
        confidence = data.get('confidence', 0.5)
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = 0.5
        
        # Type-based severity
        if indicator_type == ThreatType.VULNERABILITY:
            return SeverityLevel.HIGH
        elif indicator_type == ThreatType.MALWARE:
            return SeverityLevel.HIGH
        elif indicator_type == ThreatType.CAMPAIGN:
            return SeverityLevel.HIGH
        elif indicator_type == ThreatType.THREAT_ACTOR:
            return SeverityLevel.MEDIUM
        
        # Confidence-based severity for IOCs
        if confidence >= 0.8:
            return SeverityLevel.HIGH
        elif confidence >= 0.6:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _map_explicit_severity(self, severity_str: str) -> Optional[SeverityLevel]:
        """Map explicit severity strings to SeverityLevel enum"""
        severity_mapping = {
            'low': SeverityLevel.LOW,
            'medium': SeverityLevel.MEDIUM,
            'high': SeverityLevel.HIGH,
            'critical': SeverityLevel.CRITICAL,
            'info': SeverityLevel.LOW,
            'warning': SeverityLevel.MEDIUM,
            'error': SeverityLevel.HIGH,
            'alert': SeverityLevel.HIGH
        }
        
        return severity_mapping.get(severity_str)
    
    def _is_ip_address(self, value: str) -> bool:
        """Check if value is a valid IP address"""
        try:
            ip_address(value)
            return True
        except AddressValueError:
            return False
    
    def _is_domain(self, value: str) -> bool:
        """Check if value is a valid domain"""
        return bool(self.PATTERNS['domain'].match(value))
    
    def _is_url(self, value: str) -> bool:
        """Check if value is a valid URL"""
        try:
            result = urlparse(value)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _parse_datetime(self, date_input: Any) -> Optional[datetime]:
        """Parse datetime from various input formats"""
        if not date_input:
            return None
        
        # If already datetime
        if isinstance(date_input, datetime):
            return date_input
        
        # Convert to string
        date_str = str(date_input).strip()
        if not date_str:
            return None
        
        # Common datetime formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO with microseconds
            '%Y-%m-%dT%H:%M:%SZ',     # ISO format
            '%Y-%m-%dT%H:%M:%S',      # ISO without Z
            '%Y-%m-%d %H:%M:%S',      # Standard format
            '%Y-%m-%d',               # Date only
            '%d/%m/%Y',               # DD/MM/YYYY
            '%m/%d/%Y',               # MM/DD/YYYY
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try parsing Unix timestamp
        try:
            timestamp = float(date_str)
            if timestamp > 1000000000:  # Reasonable timestamp range
                return datetime.fromtimestamp(timestamp)
        except (ValueError, OSError):
            pass
        
        self.logger.debug(f"Could not parse datetime: {date_str}")
        return None