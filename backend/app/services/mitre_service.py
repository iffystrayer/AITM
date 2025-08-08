"""
MITRE ATT&CK service for knowledge base management
"""

import json
import logging
from typing import Dict, List, Optional, Any
import aiofiles
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session, MitreAttack
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MitreAttackService:
    """Service for managing MITRE ATT&CK framework data"""
    
    def __init__(self):
        self.data_cache: Optional[Dict[str, Any]] = None
        self.techniques_cache: Dict[str, Dict[str, Any]] = {}
        self.tactics_cache: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self):
        """Initialize MITRE ATT&CK data"""
        logger.info("Initializing MITRE ATT&CK data...")
        
        try:
            # Check if we have data in database
            async with async_session() as db:
                result = await db.execute(select(MitreAttack).limit(1))
                existing_data = result.scalar_one_or_none()
                
                if not existing_data:
                    logger.info("No MITRE ATT&CK data found in database, loading from source...")
                    await self.load_and_store_data()
                else:
                    logger.info("MITRE ATT&CK data found in database, loading to cache...")
                    await self.load_from_database()
                    
        except Exception as e:
            logger.error(f"Failed to initialize MITRE ATT&CK data: {e}")
            # For MVP, we can create some basic sample data
            await self.create_sample_data()
    
    async def load_and_store_data(self):
        """Load MITRE ATT&CK data from official source and store in database"""
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Downloading MITRE ATT&CK data from {settings.mitre_attack_data_url}")
                response = await client.get(settings.mitre_attack_data_url, timeout=30.0)
                response.raise_for_status()
                
                self.data_cache = response.json()
                await self.parse_and_store_data(self.data_cache)
                
        except Exception as e:
            logger.error(f"Failed to load MITRE ATT&CK data: {e}")
            await self.create_sample_data()
    
    async def parse_and_store_data(self, data: Dict[str, Any]):
        """Parse and store MITRE ATT&CK data in database"""
        objects = data.get('objects', [])
        
        async with async_session() as db:
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
                        
                        # Create database entry
                        mitre_entry = MitreAttack(
                            technique_id=technique_id,
                            name=obj.get('name', ''),
                            tactic=', '.join(tactics),
                            description=obj.get('description', ''),
                            platforms=json.dumps(obj.get('x_mitre_platforms', [])),
                            data_sources=json.dumps(obj.get('x_mitre_data_sources', [])),
                            mitigations=json.dumps([])  # Will be populated separately
                        )
                        
                        db.add(mitre_entry)
                        
                        # Cache the technique
                        self.techniques_cache[technique_id] = {
                            'id': technique_id,
                            'name': obj.get('name', ''),
                            'description': obj.get('description', ''),
                            'tactics': tactics,
                            'platforms': obj.get('x_mitre_platforms', []),
                            'data_sources': obj.get('x_mitre_data_sources', [])
                        }
            
            await db.commit()
            logger.info(f"Stored {len(self.techniques_cache)} MITRE ATT&CK techniques")
    
    async def load_from_database(self):
        """Load MITRE ATT&CK data from database to cache"""
        async with async_session() as db:
            result = await db.execute(select(MitreAttack))
            techniques = result.scalars().all()
            
            for technique in techniques:
                self.techniques_cache[technique.technique_id] = {
                    'id': technique.technique_id,
                    'name': technique.name,
                    'description': technique.description,
                    'tactics': technique.tactic.split(', ') if technique.tactic else [],
                    'platforms': json.loads(technique.platforms) if technique.platforms else [],
                    'data_sources': json.loads(technique.data_sources) if technique.data_sources else []
                }
    
    async def create_sample_data(self):
        """Create sample MITRE ATT&CK data for MVP testing"""
        logger.info("Creating sample MITRE ATT&CK data for MVP...")
        
        sample_techniques = [
            {
                'id': 'T1190',
                'name': 'Exploit Public-Facing Application',
                'description': 'Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program using software, data, or commands in order to cause unintended or unanticipated behavior.',
                'tactics': ['initial-access'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Application logs', 'Web logs']
            },
            {
                'id': 'T1059',
                'name': 'Command and Scripting Interpreter',
                'description': 'Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries.',
                'tactics': ['execution'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Process monitoring', 'Command line parameters']
            },
            {
                'id': 'T1078',
                'name': 'Valid Accounts',
                'description': 'Adversaries may obtain and abuse credentials of existing accounts as a means of gaining Initial Access, Persistence, Privilege Escalation, or Defense Evasion.',
                'tactics': ['defense-evasion', 'persistence', 'privilege-escalation', 'initial-access'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Authentication logs', 'Account usage']
            },
            {
                'id': 'T1055',
                'name': 'Process Injection',
                'description': 'Adversaries may inject code into processes in order to evade process-based defenses as well as possibly elevate privileges.',
                'tactics': ['defense-evasion', 'privilege-escalation'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['Process monitoring', 'API monitoring']
            },
            {
                'id': 'T1083',
                'name': 'File and Directory Discovery',
                'description': 'Adversaries may enumerate files and directories or may search in specific locations for desired information within a file system.',
                'tactics': ['discovery'],
                'platforms': ['Windows', 'Linux', 'macOS'],
                'data_sources': ['File monitoring', 'Process command-line parameters']
            }
        ]
        
        async with async_session() as db:
            for technique_data in sample_techniques:
                # Store in database
                mitre_entry = MitreAttack(
                    technique_id=technique_data['id'],
                    name=technique_data['name'],
                    tactic=', '.join(technique_data['tactics']),
                    description=technique_data['description'],
                    platforms=json.dumps(technique_data['platforms']),
                    data_sources=json.dumps(technique_data['data_sources']),
                    mitigations=json.dumps([])
                )
                db.add(mitre_entry)
                
                # Store in cache
                self.techniques_cache[technique_data['id']] = technique_data
            
            await db.commit()
            logger.info(f"Created {len(sample_techniques)} sample MITRE ATT&CK techniques")
    
    def get_technique(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific technique by ID"""
        return self.techniques_cache.get(technique_id)
    
    def search_techniques_by_tactic(self, tactic: str) -> List[Dict[str, Any]]:
        """Search techniques by tactic"""
        results = []
        for technique in self.techniques_cache.values():
            if tactic in technique.get('tactics', []):
                results.append(technique)
        return results
    
    def search_techniques_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """Search techniques by platform"""
        results = []
        for technique in self.techniques_cache.values():
            if platform in technique.get('platforms', []):
                results.append(technique)
        return results
    
    def search_techniques_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Search techniques by keyword in name or description"""
        results = []
        keyword = keyword.lower()
        for technique in self.techniques_cache.values():
            if (keyword in technique.get('name', '').lower() or 
                keyword in technique.get('description', '').lower()):
                results.append(technique)
        return results
    
    def get_all_techniques(self) -> List[Dict[str, Any]]:
        """Get all techniques"""
        return list(self.techniques_cache.values())
    
    def get_tactics(self) -> List[str]:
        """Get all unique tactics"""
        tactics = set()
        for technique in self.techniques_cache.values():
            tactics.update(technique.get('tactics', []))
        return sorted(list(tactics))
    
    def suggest_techniques_for_system(self, 
                                   system_technologies: List[str], 
                                   asset_types: List[str]) -> List[Dict[str, Any]]:
        """Suggest relevant techniques based on system characteristics"""
        suggested = []
        
        # Map common technologies to platforms
        platform_mapping = {
            'windows': 'Windows',
            'linux': 'Linux', 
            'macos': 'macOS',
            'web': ['Windows', 'Linux', 'macOS'],
            'database': ['Windows', 'Linux'],
            'cloud': ['Windows', 'Linux', 'macOS']
        }
        
        # Determine relevant platforms
        relevant_platforms = set()
        for tech in system_technologies:
            tech_lower = tech.lower()
            for key, platforms in platform_mapping.items():
                if key in tech_lower:
                    if isinstance(platforms, list):
                        relevant_platforms.update(platforms)
                    else:
                        relevant_platforms.add(platforms)
        
        # If no specific platforms found, include all
        if not relevant_platforms:
            relevant_platforms = {'Windows', 'Linux', 'macOS'}
        
        # Find techniques for relevant platforms
        for technique in self.techniques_cache.values():
            technique_platforms = set(technique.get('platforms', []))
            if relevant_platforms.intersection(technique_platforms):
                suggested.append(technique)
        
        return suggested[:10]  # Return top 10 suggestions


# Global service instance
mitre_service = MitreAttackService()
