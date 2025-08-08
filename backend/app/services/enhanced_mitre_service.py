"""
Enhanced MITRE ATT&CK Service
Provides advanced ATT&CK framework integration for threat modeling
"""

import json
import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
import aiofiles
import httpx
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session, MitreAttack
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EnhancedMitreService:
    """
    Enhanced service for managing MITRE ATT&CK framework data
    
    Features:
    - Comprehensive technique and tactic searching
    - Component-based technique mapping
    - Entry point attack vector analysis
    - Relevance scoring and sorting
    - Cached operations for performance
    """
    
    def __init__(self):
        # Technique data
        self.techniques_cache: Dict[str, Dict[str, Any]] = {}
        self.tactics_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.platforms_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Relationship data
        self.technique_to_mitigation: Dict[str, List[str]] = {}
        self.mitigation_to_technique: Dict[str, List[str]] = {}
        
        # Index data
        self.technique_search_index: Dict[str, Set[str]] = {}
        self.tactic_search_index: Dict[str, Set[str]] = {}
        
        # Status
        self.initialized: bool = False
        self.data_version: Optional[str] = None
        self.last_updated: Optional[datetime] = None
    
    async def initialize(self, force_download: bool = False):
        """Initialize MITRE ATT&CK data"""
        if self.initialized and not force_download:
            logger.info("MITRE ATT&CK data already initialized")
            return
        
        logger.info("Initializing MITRE ATT&CK data...")
        
        try:
            # Look for local cached file first
            data_dir = Path("/app/data/mitre")
            data_file = data_dir / "attack_data.json"
            
            if os.path.exists(data_file) and not force_download:
                await self._load_from_file(data_file)
            else:
                # Try loading from database first
                db_loaded = await self._load_from_database()
                
                if not db_loaded or force_download:
                    # Download fresh data
                    await self._download_and_parse_data()
            
            # Build search indexes
            self._build_search_indexes()
            
            self.initialized = True
            self.last_updated = datetime.now()
            
            logger.info(f"MITRE ATT&CK data initialized with {len(self.techniques_cache)} techniques")
            
        except Exception as e:
            logger.error(f"Failed to initialize MITRE ATT&CK data: {e}", exc_info=True)
            # Create sample data for testing
            await self._create_sample_data()
            self.initialized = True
    
    async def _load_from_file(self, file_path: Path) -> bool:
        """Load MITRE ATT&CK data from local file"""
        try:
            logger.info(f"Loading MITRE ATT&CK data from file: {file_path}")
            
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
                
            await self._parse_attack_data(data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to load MITRE ATT&CK data from file: {e}")
            return False
    
    async def _load_from_database(self) -> bool:
        """Load MITRE ATT&CK data from database"""
        try:
            logger.info("Loading MITRE ATT&CK data from database")
            
            async with async_session() as db:
                result = await db.execute(select(MitreAttack))
                techniques = result.scalars().all()
                
                if not techniques:
                    logger.info("No MITRE ATT&CK data found in database")
                    return False
                
                for technique in techniques:
                    # Parse data from database
                    self.techniques_cache[technique.technique_id] = {
                        'id': technique.technique_id,
                        'name': technique.name,
                        'description': technique.description,
                        'tactics': technique.tactic.split(', ') if technique.tactic else [],
                        'platforms': json.loads(technique.platforms) if technique.platforms else [],
                        'data_sources': json.loads(technique.data_sources) if technique.data_sources else [],
                        'mitigations': json.loads(technique.mitigations) if technique.mitigations else []
                    }
                    
                    # Cache tactic mappings
                    for tactic in self.techniques_cache[technique.technique_id]['tactics']:
                        if tactic not in self.tactics_cache:
                            self.tactics_cache[tactic] = []
                        self.tactics_cache[tactic].append(self.techniques_cache[technique.technique_id])
                    
                    # Cache platform mappings
                    for platform in self.techniques_cache[technique.technique_id]['platforms']:
                        if platform not in self.platforms_cache:
                            self.platforms_cache[platform] = []
                        self.platforms_cache[platform].append(self.techniques_cache[technique.technique_id])
                
                logger.info(f"Loaded {len(self.techniques_cache)} techniques from database")
                return len(self.techniques_cache) > 0
                
        except Exception as e:
            logger.error(f"Failed to load MITRE ATT&CK data from database: {e}")
            return False
    
    async def _download_and_parse_data(self):
        """Download MITRE ATT&CK data from source and parse it"""
        try:
            logger.info(f"Downloading MITRE ATT&CK data from {settings.mitre_attack_data_url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.mitre_attack_data_url, timeout=60.0)
                response.raise_for_status()
                data = response.json()
            
            # Save to file for future use
            data_dir = Path("/app/data/mitre")
            os.makedirs(data_dir, exist_ok=True)
            
            async with aiofiles.open(data_dir / "attack_data.json", 'w') as f:
                await f.write(json.dumps(data))
            
            # Parse the data
            await self._parse_attack_data(data)
            
            # Store in database
            await self._store_in_database()
            
        except Exception as e:
            logger.error(f"Failed to download and parse MITRE ATT&CK data: {e}")
            raise
    
    async def _parse_attack_data(self, data: Dict[str, Any]):
        """Parse MITRE ATT&CK data"""
        try:
            # Extract STIX version and bundle info
            self.data_version = data.get('spec_version', 'unknown')
            
            # Clear existing caches
            self.techniques_cache.clear()
            self.tactics_cache.clear()
            self.platforms_cache.clear()
            
            # Process all objects
            objects = data.get('objects', [])
            
            # First pass: identify techniques
            for obj in objects:
                if obj.get('type') == 'attack-pattern':
                    # This is a technique
                    technique_id = None
                    for ref in obj.get('external_references', []):
                        if ref.get('source_name') == 'mitre-attack':
                            technique_id = ref.get('external_id')
                            break
                    
                    if technique_id:
                        # Extract tactics
                        tactics = []
                        for phase in obj.get('kill_chain_phases', []):
                            if phase.get('kill_chain_name') == 'mitre-attack':
                                tactics.append(phase.get('phase_name'))
                        
                        # Store technique
                        self.techniques_cache[technique_id] = {
                            'id': technique_id,
                            'name': obj.get('name', ''),
                            'description': obj.get('description', ''),
                            'tactics': tactics,
                            'platforms': obj.get('x_mitre_platforms', []),
                            'data_sources': obj.get('x_mitre_data_sources', []),
                            'mitigations': [],  # Will be populated in second pass
                            'created': obj.get('created', ''),
                            'modified': obj.get('modified', '')
                        }
                        
                        # Cache by tactic
                        for tactic in tactics:
                            if tactic not in self.tactics_cache:
                                self.tactics_cache[tactic] = []
                            self.tactics_cache[tactic].append(self.techniques_cache[technique_id])
                        
                        # Cache by platform
                        for platform in obj.get('x_mitre_platforms', []):
                            if platform not in self.platforms_cache:
                                self.platforms_cache[platform] = []
                            self.platforms_cache[platform].append(self.techniques_cache[technique_id])
            
            # Second pass: identify mitigations and relationships
            for obj in objects:
                if obj.get('type') == 'course-of-action':
                    # This is a mitigation
                    mitigation_id = None
                    for ref in obj.get('external_references', []):
                        if ref.get('source_name') == 'mitre-attack':
                            mitigation_id = ref.get('external_id')
                            break
                    
                    if mitigation_id:
                        self.mitigation_to_technique[mitigation_id] = []
                
                elif obj.get('type') == 'relationship':
                    # Check for mitigation relationships
                    if obj.get('relationship_type') == 'mitigates':
                        source_ref = obj.get('source_ref', '')
                        target_ref = obj.get('target_ref', '')
                        
                        # Find the corresponding IDs
                        source_id = self._get_id_from_ref(source_ref, objects)
                        target_id = self._get_id_from_ref(target_ref, objects)
                        
                        if source_id and target_id:
                            # Add mitigation to technique
                            if target_id in self.techniques_cache:
                                self.techniques_cache[target_id]['mitigations'].append(source_id)
                            
                            # Add technique to mitigation
                            if source_id in self.mitigation_to_technique:
                                self.mitigation_to_technique[source_id].append(target_id)
            
            logger.info(f"Parsed {len(self.techniques_cache)} techniques from MITRE ATT&CK data")
            
        except Exception as e:
            logger.error(f"Failed to parse MITRE ATT&CK data: {e}")
            raise
    
    def _get_id_from_ref(self, ref: str, objects: List[Dict[str, Any]]) -> Optional[str]:
        """Get MITRE ATT&CK ID from STIX reference"""
        for obj in objects:
            if obj.get('id') == ref:
                for ext_ref in obj.get('external_references', []):
                    if ext_ref.get('source_name') == 'mitre-attack':
                        return ext_ref.get('external_id')
        return None
    
    async def _store_in_database(self):
        """Store MITRE ATT&CK data in database"""
        try:
            logger.info("Storing MITRE ATT&CK data in database")
            
            async with async_session() as db:
                # First, clear existing data
                await db.execute("DELETE FROM mitre_attack")
                
                # Then insert new data
                for technique_id, technique in self.techniques_cache.items():
                    mitre_entry = MitreAttack(
                        technique_id=technique_id,
                        name=technique['name'],
                        tactic=', '.join(technique['tactics']),
                        description=technique['description'],
                        platforms=json.dumps(technique['platforms']),
                        data_sources=json.dumps(technique['data_sources']),
                        mitigations=json.dumps(technique['mitigations'])
                    )
                    db.add(mitre_entry)
                
                await db.commit()
                logger.info(f"Stored {len(self.techniques_cache)} techniques in database")
                
        except Exception as e:
            logger.error(f"Failed to store MITRE ATT&CK data in database: {e}")
            raise
    
    def _build_search_indexes(self):
        """Build search indexes for fast lookups"""
        # Clear existing indexes
        self.technique_search_index.clear()
        self.tactic_search_index.clear()
        
        # Build technique search index
        for technique_id, technique in self.techniques_cache.items():
            # Split name and description into words
            name_words = set(technique['name'].lower().split())
            desc_words = set(technique['description'].lower().split())
            
            # Add to index
            words = name_words.union(desc_words)
            for word in words:
                if len(word) >= 3:  # Only index words of 3+ characters
                    if word not in self.technique_search_index:
                        self.technique_search_index[word] = set()
                    self.technique_search_index[word].add(technique_id)
        
        # Build tactic search index
        for tactic, techniques in self.tactics_cache.items():
            tactic_words = tactic.lower().replace('-', ' ').split()
            for word in tactic_words:
                if word not in self.tactic_search_index:
                    self.tactic_search_index[word] = set()
                self.tactic_search_index[word].add(tactic)
    
    async def _create_sample_data(self):
        """Create sample MITRE ATT&CK data for MVP testing"""
        logger.info("Creating sample MITRE ATT&CK data")
        
        # Clear caches
        self.techniques_cache.clear()
        self.tactics_cache.clear()
        self.platforms_cache.clear()
        
        # Sample techniques
        sample_techniques = [
            {
                'id': 'T1190',
                'name': 'Exploit Public-Facing Application',
                'description': 'Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program using software, data, or commands in order to cause unintended or unanticipated behavior.',
                'tactics': ['initial-access'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Application logs', 'Web logs'],
                'mitigations': ['M1048', 'M1050', 'M1051']
            },
            {
                'id': 'T1059',
                'name': 'Command and Scripting Interpreter',
                'description': 'Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries.',
                'tactics': ['execution'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Process monitoring', 'Command line parameters'],
                'mitigations': ['M1038', 'M1040', 'M1042']
            },
            {
                'id': 'T1078',
                'name': 'Valid Accounts',
                'description': 'Adversaries may obtain and abuse credentials of existing accounts as a means of gaining Initial Access, Persistence, Privilege Escalation, or Defense Evasion.',
                'tactics': ['defense-evasion', 'persistence', 'privilege-escalation', 'initial-access'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Authentication logs', 'Account usage'],
                'mitigations': ['M1026', 'M1032']
            },
            {
                'id': 'T1055',
                'name': 'Process Injection',
                'description': 'Adversaries may inject code into processes in order to evade process-based defenses as well as possibly elevate privileges.',
                'tactics': ['defense-evasion', 'privilege-escalation'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Process monitoring', 'API monitoring'],
                'mitigations': ['M1040', 'M1050']
            },
            {
                'id': 'T1083',
                'name': 'File and Directory Discovery',
                'description': 'Adversaries may enumerate files and directories or may search in specific locations for desired information within a file system.',
                'tactics': ['discovery'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['File monitoring', 'Process command-line parameters'],
                'mitigations': ['M1022', 'M1028']
            },
            {
                'id': 'T1566',
                'name': 'Phishing',
                'description': 'Adversaries may send phishing messages to gain access to victim systems. Phishing is a technique that uses social engineering to get users to reveal sensitive information or take harmful actions.',
                'tactics': ['initial-access'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Email gateway logs', 'Network traffic logs'],
                'mitigations': ['M1017', 'M1049']
            },
            {
                'id': 'T1027',
                'name': 'Obfuscated Files or Information',
                'description': 'Adversaries may attempt to make an executable or file difficult to discover or analyze by encrypting, encoding, or otherwise obfuscating its contents.',
                'tactics': ['defense-evasion'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['File monitoring', 'Process monitoring'],
                'mitigations': ['M1027', 'M1049']
            },
            {
                'id': 'T1133',
                'name': 'External Remote Services',
                'description': 'Adversaries may leverage external remote services to initially access and/or persist within a network.',
                'tactics': ['initial-access', 'persistence'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Authentication logs', 'Network traffic logs'],
                'mitigations': ['M1035', 'M1042']
            }
        ]
        
        # Sample mitigations
        sample_mitigations = {
            'M1017': 'User Training',
            'M1022': 'Restrict File and Directory Permissions',
            'M1026': 'Privileged Account Management',
            'M1027': 'Password Policies',
            'M1028': 'Antivirus/Antimalware',
            'M1032': 'Multi-factor Authentication',
            'M1035': 'Limit Access to Resource Over Network',
            'M1038': 'Execution Prevention',
            'M1040': 'Behavior Prevention on Endpoint',
            'M1042': 'Disable or Remove Feature or Program',
            'M1048': 'Application Isolation and Sandboxing',
            'M1049': 'Antivirus/Antimalware',
            'M1050': 'Exploit Protection',
            'M1051': 'Update Software',
        }
        
        # Store techniques
        for technique in sample_techniques:
            self.techniques_cache[technique['id']] = technique
            
            # Cache by tactic
            for tactic in technique['tactics']:
                if tactic not in self.tactics_cache:
                    self.tactics_cache[tactic] = []
                self.tactics_cache[tactic].append(technique)
            
            # Cache by platform
            for platform in technique['platforms']:
                if platform not in self.platforms_cache:
                    self.platforms_cache[platform] = []
                self.platforms_cache[platform].append(technique)
        
        # Build search indexes
        self._build_search_indexes()
        
        # Save to database
        try:
            async with async_session() as db:
                # Clear existing data
                await db.execute("DELETE FROM mitre_attack")
                
                # Insert sample data
                for technique_id, technique in self.techniques_cache.items():
                    mitre_entry = MitreAttack(
                        technique_id=technique_id,
                        name=technique['name'],
                        tactic=', '.join(technique['tactics']),
                        description=technique['description'],
                        platforms=json.dumps(technique['platforms']),
                        data_sources=json.dumps(technique['data_sources']),
                        mitigations=json.dumps(technique['mitigations'])
                    )
                    db.add(mitre_entry)
                
                await db.commit()
                logger.info(f"Stored {len(self.techniques_cache)} sample techniques in database")
                
        except Exception as e:
            logger.error(f"Failed to store sample MITRE ATT&CK data in database: {e}")
    
    #
    # Public API Methods
    #
    
    def get_technique(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """Get technique by ID"""
        return self.techniques_cache.get(technique_id)
    
    def get_techniques_by_tactic(self, tactic: str) -> List[Dict[str, Any]]:
        """Get techniques by tactic"""
        return self.tactics_cache.get(tactic.lower(), [])
    
    def get_techniques_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """Get techniques by platform"""
        return self.platforms_cache.get(platform, [])
    
    def search_techniques(self, query: str) -> List[Dict[str, Any]]:
        """Search techniques by keywords"""
        query = query.lower()
        matching_techniques = []
        seen_ids = set()
        
        # Direct match in name or description
        for technique_id, technique in self.techniques_cache.items():
            if (query in technique['name'].lower() or 
                query in technique['description'].lower()):
                
                # Add relevance score
                technique_copy = technique.copy()
                technique_copy['relevance_score'] = self._calculate_relevance_score(
                    query, technique['name'], technique['description']
                )
                matching_techniques.append(technique_copy)
                seen_ids.add(technique_id)
        
        # Word-based matching from index
        query_words = query.split()
        for word in query_words:
            if len(word) >= 3 and word in self.technique_search_index:
                for technique_id in self.technique_search_index[word]:
                    if technique_id not in seen_ids:
                        technique = self.techniques_cache[technique_id].copy()
                        technique['relevance_score'] = self._calculate_relevance_score(
                            query, technique['name'], technique['description']
                        )
                        matching_techniques.append(technique)
                        seen_ids.add(technique_id)
        
        # Sort by relevance
        matching_techniques.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return matching_techniques
    
    def get_mitigations_for_technique(self, technique_id: str) -> List[Dict[str, Any]]:
        """Get mitigations for a technique"""
        technique = self.techniques_cache.get(technique_id)
        if not technique:
            return []
        
        return [
            {'id': mid, 'name': f"Mitigation {mid}"} 
            for mid in technique.get('mitigations', [])
        ]
    
    def get_all_tactics(self) -> List[str]:
        """Get all tactics"""
        return sorted(list(self.tactics_cache.keys()))
    
    def get_all_platforms(self) -> List[str]:
        """Get all platforms"""
        return sorted(list(self.platforms_cache.keys()))
    
    def get_all_techniques(self) -> List[Dict[str, Any]]:
        """Get all techniques"""
        return list(self.techniques_cache.values())
    
    def get_technique_count(self) -> int:
        """Get count of techniques"""
        return len(self.techniques_cache)
    
    def get_techniques_for_system_components(
        self, 
        components: List[Dict[str, Any]],
        entry_points: Optional[List[Dict[str, Any]]] = None,
        limit_per_component: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get relevant techniques for system components"""
        result = {}
        
        for component in components:
            component_id = component.get('name', 'unknown')
            component_type = component.get('type', '').lower()
            component_technologies = [t.lower() for t in component.get('technologies', [])]
            
            # Get relevant techniques for this component
            relevant_techniques = []
            
            # Check by component type
            if 'web' in component_type or 'application' in component_type:
                relevant_techniques.extend(self._get_web_app_techniques())
            elif 'database' in component_type:
                relevant_techniques.extend(self._get_database_techniques())
            elif 'api' in component_type:
                relevant_techniques.extend(self._get_api_techniques())
            elif 'server' in component_type or 'host' in component_type:
                relevant_techniques.extend(self._get_server_techniques())
            elif 'network' in component_type:
                relevant_techniques.extend(self._get_network_techniques())
            
            # Check by technology
            for tech in component_technologies:
                if 'windows' in tech:
                    relevant_techniques.extend(self.get_techniques_by_platform('Windows'))
                elif 'linux' in tech:
                    relevant_techniques.extend(self.get_techniques_by_platform('Linux'))
                elif 'macos' in tech or 'mac' in tech:
                    relevant_techniques.extend(self.get_techniques_by_platform('macOS'))
                elif 'docker' in tech or 'container' in tech:
                    relevant_techniques.extend(self._get_container_techniques())
            
            # Process entry points if applicable
            if entry_points:
                for entry_point in entry_points:
                    if entry_point.get('target_component', '') == component_id:
                        entry_techniques = self._get_techniques_for_entry_point(entry_point)
                        relevant_techniques.extend(entry_techniques)
            
            # Deduplicate
            seen_ids = set()
            unique_techniques = []
            
            for technique in relevant_techniques:
                if technique['id'] not in seen_ids:
                    # Calculate component relevance score
                    technique = technique.copy()
                    technique['component_relevance'] = self._calculate_component_relevance(
                        technique, component_type, component_technologies
                    )
                    unique_techniques.append(technique)
                    seen_ids.add(technique['id'])
            
            # Sort by relevance and limit
            unique_techniques.sort(key=lambda x: x.get('component_relevance', 0), reverse=True)
            result[component_id] = unique_techniques[:limit_per_component]
        
        return result
    
    def get_techniques_for_entry_points(
        self, 
        entry_points: List[Dict[str, Any]],
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get relevant techniques for entry points"""
        all_techniques = []
        seen_ids = set()
        
        for entry_point in entry_points:
            # Get techniques for this entry point
            entry_techniques = self._get_techniques_for_entry_point(entry_point)
            
            # Add with deduplication
            for technique in entry_techniques:
                if technique['id'] not in seen_ids:
                    all_techniques.append(technique)
                    seen_ids.add(technique['id'])
        
        # Sort by relevance (initial access first)
        def entry_point_sort_key(technique):
            if 'initial-access' in technique.get('tactics', []):
                return 2
            if 'persistence' in technique.get('tactics', []):
                return 1
            return 0
        
        all_techniques.sort(key=entry_point_sort_key, reverse=True)
        return all_techniques[:limit]
    
    def generate_attack_paths(
        self,
        critical_assets: List[Dict[str, Any]],
        entry_points: List[Dict[str, Any]],
        components: List[Dict[str, Any]],
        paths_per_entry: int = 3,
        max_path_length: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate attack paths based on system analysis"""
        paths = []
        
        # Identify initial access points
        for entry_point in entry_points:
            # Only use external entry points
            if entry_point.get('exposure', '').lower() != 'external':
                continue
            
            # Find target component
            target_component = entry_point.get('name', '')
            
            # Generate paths from this entry point
            for i in range(paths_per_entry):
                # Generate a path
                path = self._generate_attack_path(
                    entry_point=entry_point,
                    components=components,
                    critical_assets=critical_assets,
                    path_id=f"AP-{len(paths)+1}",
                    max_length=max_path_length
                )
                
                if path:
                    paths.append(path)
        
        return paths
    
    #
    # Private Helper Methods
    #
    
    def _calculate_relevance_score(self, query: str, name: str, description: str) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query = query.lower()
        name = name.lower()
        description = description.lower()
        
        # Name match gets higher score
        if query in name:
            score += 2.0
            if name.startswith(query):
                score += 1.0
        
        # Description match
        if query in description:
            score += 1.0
        
        # Exact word matches get bonus
        for word in query.split():
            if word in name.split():
                score += 0.5
            if word in description.split():
                score += 0.3
        
        return score
    
    def _calculate_component_relevance(
        self, 
        technique: Dict[str, Any],
        component_type: str,
        technologies: List[str]
    ) -> float:
        """Calculate component-specific relevance score"""
        score = 1.0  # Base score
        
        # Higher score for exact type match
        type_keywords = {
            'web': ['web', 'browser', 'public-facing', 'internet'],
            'database': ['database', 'sql', 'data', 'storage'],
            'server': ['server', 'host', 'system'],
            'application': ['application', 'software', 'program'],
            'api': ['api', 'interface', 'service'],
            'network': ['network', 'communication']
        }
        
        # Check for component type keywords in technique
        component_key = next((k for k in type_keywords.keys() if k in component_type), None)
        if component_key:
            keywords = type_keywords[component_key]
            for keyword in keywords:
                if (keyword in technique['name'].lower() or 
                    keyword in technique['description'].lower()):
                    score += 0.5
        
        # Check for platform-specific techniques
        for tech in technologies:
            for platform in technique.get('platforms', []):
                if tech.lower() in platform.lower():
                    score += 0.5
                    break
        
        # Initial access techniques get a boost for entry points
        if 'initial-access' in technique.get('tactics', []):
            score += 0.5
        
        return score
    
    def _get_techniques_for_entry_point(self, entry_point: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get techniques relevant to a specific entry point"""
        entry_type = entry_point.get('type', '').lower()
        exposure = entry_point.get('exposure', '').lower()
        auth_required = entry_point.get('authentication_required', False)
        
        techniques = []
        
        # External entry points are high-priority targets
        if exposure == 'external':
            # Add initial access techniques
            techniques.extend(self.get_techniques_by_tactic('initial-access'))
            
            # Add type-specific techniques
            if 'web' in entry_type:
                techniques.extend(self._get_web_attack_techniques())
            elif 'api' in entry_type:
                techniques.extend(self._get_api_attack_techniques())
            elif 'remote' in entry_type or 'ssh' in entry_type or 'rdp' in entry_type:
                techniques.extend(self._get_remote_access_techniques())
        
        # Internal entry points with authentication
        elif auth_required:
            # Credential attacks
            for tid in ['T1078']:  # Valid Accounts
                if tid in self.techniques_cache:
                    techniques.append(self.techniques_cache[tid])
        
        return techniques
    
    def _generate_attack_path(
        self,
        entry_point: Dict[str, Any],
        components: List[Dict[str, Any]],
        critical_assets: List[Dict[str, Any]],
        path_id: str,
        max_length: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Generate a single attack path"""
        # Determine target critical asset
        if not critical_assets:
            return None
        
        target_asset = critical_assets[0]  # Default to first asset
        
        # Find most critical asset
        for asset in critical_assets:
            if asset.get('criticality', '').lower() == 'critical':
                target_asset = asset
                break
        
        # Start with entry point
        entry_techniques = self._get_techniques_for_entry_point(entry_point)
        if not entry_techniques:
            return None
        
        # Select a starting technique (prefer initial-access)
        initial_technique = next(
            (t for t in entry_techniques if 'initial-access' in t.get('tactics', [])),
            entry_techniques[0]
        )
        
        # Build attack steps
        attack_steps = []
        current_step = 1
        
        # Add initial technique
        attack_steps.append({
            'step': current_step,
            'technique_id': initial_technique['id'],
            'technique_name': initial_technique['name'],
            'tactic': initial_technique.get('tactics', ['initial-access'])[0],
            'target_component': entry_point.get('name', 'External Entry Point'),
            'description': f"Initial access via {entry_point.get('type', 'entry point')}"
        })
        
        # Add subsequent techniques
        used_techniques = {initial_technique['id']}
        current_step += 1
        
        # Chain of tactics to follow (typical attack progression)
        tactic_chain = [
            'execution', 
            'persistence', 
            'privilege-escalation', 
            'defense-evasion', 
            'discovery', 
            'lateral-movement', 
            'collection', 
            'exfiltration'
        ]
        
        # Build the path following the tactic chain
        for tactic in tactic_chain:
            if current_step > max_length:
                break
                
            # Get techniques for this tactic
            tactic_techniques = self.get_techniques_by_tactic(tactic)
            
            # Filter out already used techniques
            tactic_techniques = [t for t in tactic_techniques if t['id'] not in used_techniques]
            
            if not tactic_techniques:
                continue
                
            # Select a technique (could be improved with more intelligent selection)
            technique = tactic_techniques[0]
            
            # Determine target component for this step
            if current_step == 2:  # Second step
                # Use the entry point's target component
                target_component = entry_point.get('target_component', entry_point.get('name', ''))
            elif current_step == max_length:  # Last step
                # Target the critical asset
                target_component = target_asset.get('name', '')
            else:
                # Use a random component
                components_list = [c.get('name', '') for c in components]
                target_component = components_list[0] if components_list else ''
            
            # Add the step
            attack_steps.append({
                'step': current_step,
                'technique_id': technique['id'],
                'technique_name': technique['name'],
                'tactic': tactic,
                'target_component': target_component,
                'description': technique.get('description', '')[:100] + '...'  # Truncate description
            })
            
            used_techniques.add(technique['id'])
            current_step += 1
        
        # Determine likelihood and impact
        likelihood = "medium"
        if entry_point.get('exposure', '').lower() == 'external':
            likelihood = "high"
        
        impact = target_asset.get('criticality', 'medium')
        
        # Create the path
        return {
            'path_id': path_id,
            'name': f"Attack via {entry_point.get('name', 'Unknown Entry')}",
            'description': (
                f"Attack path starting from {entry_point.get('name', 'external entry point')} "
                f"targeting {target_asset.get('name', 'critical asset')}"
            ),
            'techniques': attack_steps,
            'likelihood': likelihood,
            'impact': impact,
            'complexity': "medium"
        }
    
    def _get_web_app_techniques(self) -> List[Dict[str, Any]]:
        """Get techniques relevant to web applications"""
        relevant_ids = ['T1190', 'T1059', 'T1078', 'T1566']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]
    
    def _get_database_techniques(self) -> List[Dict[str, Any]]:
        """Get techniques relevant to databases"""
        relevant_ids = ['T1078', 'T1083']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]
    
    def _get_api_techniques(self) -> List[Dict[str, Any]]:
        """Get techniques relevant to APIs"""
        relevant_ids = ['T1190', 'T1078']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]
    
    def _get_server_techniques(self) -> List[Dict[str, Any]]:
        """Get techniques relevant to servers"""
        relevant_ids = ['T1078', 'T1055', 'T1083', 'T1133']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]
    
    def _get_network_techniques(self) -> List[Dict[str, Any]]:
        """Get techniques relevant to network components"""
        relevant_ids = ['T1133', 'T1190']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]
    
    def _get_container_techniques(self) -> List[Dict[str, Any]]:
        """Get techniques relevant to containers"""
        relevant_ids = ['T1055', 'T1078', 'T1059']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]
    
    def _get_web_attack_techniques(self) -> List[Dict[str, Any]]:
        """Get web-specific attack techniques"""
        relevant_ids = ['T1190', 'T1059', 'T1078']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]
    
    def _get_api_attack_techniques(self) -> List[Dict[str, Any]]:
        """Get API-specific attack techniques"""
        relevant_ids = ['T1190', 'T1078']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]
    
    def _get_remote_access_techniques(self) -> List[Dict[str, Any]]:
        """Get remote access attack techniques"""
        relevant_ids = ['T1078', 'T1133']
        return [self.techniques_cache[tid] for tid in relevant_ids if tid in self.techniques_cache]


# Global service instance for singleton pattern
_enhanced_mitre_service: Optional[EnhancedMitreService] = None


def get_enhanced_mitre_service() -> EnhancedMitreService:
    """Get the global enhanced MITRE ATT&CK service instance"""
    global _enhanced_mitre_service
    if _enhanced_mitre_service is None:
        _enhanced_mitre_service = EnhancedMitreService()
    return _enhanced_mitre_service
