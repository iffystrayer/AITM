"""
Test Suite for Enhanced MITRE ATT&CK Service
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json
from pathlib import Path

from app.services.enhanced_mitre_service import EnhancedMitreService, get_enhanced_mitre_service


class TestEnhancedMitreService:
    """Test Enhanced MITRE ATT&CK Service"""
    
    @pytest_asyncio.fixture
    async def mitre_service(self):
        """Create a fresh MITRE service instance for testing"""
        service = EnhancedMitreService()
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test service initialization"""
        service = EnhancedMitreService()
        
        assert not service.initialized
        assert len(service.techniques_cache) == 0
        
        # Initialize with sample data
        await service.initialize()
        
        assert service.initialized
        assert len(service.techniques_cache) > 0
        assert len(service.tactics_cache) > 0
        assert len(service.platforms_cache) > 0
    
    @pytest.mark.asyncio
    async def test_sample_data_creation(self, mitre_service):
        """Test creation of sample data"""
        # Check that we have expected sample techniques
        assert 'T1190' in mitre_service.techniques_cache  # Exploit Public-Facing Application
        assert 'T1059' in mitre_service.techniques_cache  # Command and Scripting Interpreter
        assert 'T1078' in mitre_service.techniques_cache  # Valid Accounts
        
        # Check technique details
        exploit_technique = mitre_service.get_technique('T1190')
        assert exploit_technique is not None
        assert exploit_technique['name'] == 'Exploit Public-Facing Application'
        assert 'initial-access' in exploit_technique['tactics']
        assert 'Windows' in exploit_technique['platforms']
    
    def test_get_technique(self, mitre_service):
        """Test getting individual techniques"""
        # Test existing technique
        technique = mitre_service.get_technique('T1190')
        assert technique is not None
        assert technique['id'] == 'T1190'
        
        # Test non-existent technique
        technique = mitre_service.get_technique('T9999')
        assert technique is None
    
    def test_get_techniques_by_tactic(self, mitre_service):
        """Test getting techniques by tactic"""
        # Test initial access techniques
        initial_access = mitre_service.get_techniques_by_tactic('initial-access')
        assert len(initial_access) > 0
        
        # Check that all returned techniques have the correct tactic
        for technique in initial_access:
            assert 'initial-access' in technique['tactics']
        
        # Test non-existent tactic
        empty_results = mitre_service.get_techniques_by_tactic('non-existent-tactic')
        assert len(empty_results) == 0
    
    def test_get_techniques_by_platform(self, mitre_service):
        """Test getting techniques by platform"""
        # Test Windows techniques
        windows_techniques = mitre_service.get_techniques_by_platform('Windows')
        assert len(windows_techniques) > 0
        
        # Check that all returned techniques support Windows
        for technique in windows_techniques:
            assert 'Windows' in technique['platforms']
        
        # Test non-existent platform
        empty_results = mitre_service.get_techniques_by_platform('NonExistentOS')
        assert len(empty_results) == 0
    
    def test_search_techniques(self, mitre_service):
        """Test technique search functionality"""
        # Test exact name match
        results = mitre_service.search_techniques('Phishing')
        assert len(results) > 0
        assert any(tech['name'] == 'Phishing' for tech in results)
        
        # Test partial name match
        results = mitre_service.search_techniques('exploit')
        assert len(results) > 0
        assert any('exploit' in tech['name'].lower() for tech in results)
        
        # Test description search
        results = mitre_service.search_techniques('adversaries')
        assert len(results) > 0
        
        # Test relevance scoring (exact matches should come first)
        results = mitre_service.search_techniques('Valid Accounts')
        assert len(results) > 0
        assert results[0]['name'] == 'Valid Accounts'
        
        # Test empty search
        results = mitre_service.search_techniques('nonexistentterm12345')
        assert len(results) == 0
    
    def test_get_mitigations_for_technique(self, mitre_service):
        """Test getting mitigations for techniques"""
        # Test technique with mitigations
        mitigations = mitre_service.get_mitigations_for_technique('T1190')
        assert len(mitigations) > 0
        
        # Test non-existent technique
        mitigations = mitre_service.get_mitigations_for_technique('T9999')
        assert len(mitigations) == 0
    
    def test_get_all_tactics(self, mitre_service):
        """Test getting all tactics"""
        tactics = mitre_service.get_all_tactics()
        
        assert len(tactics) > 0
        assert 'initial-access' in tactics
        assert 'execution' in tactics
        assert 'persistence' in tactics
        
        # Check that tactics are sorted
        assert tactics == sorted(tactics)
    
    def test_get_all_platforms(self, mitre_service):
        """Test getting all platforms"""
        platforms = mitre_service.get_all_platforms()
        
        assert len(platforms) > 0
        assert 'Windows' in platforms
        assert 'Linux' in platforms
        assert 'macOS' in platforms
        
        # Check that platforms are sorted
        assert platforms == sorted(platforms)
    
    def test_get_techniques_for_system_components(self, mitre_service):
        """Test getting techniques for system components"""
        components = [
            {
                'name': 'web-server',
                'type': 'web application',
                'technologies': ['nginx', 'linux']
            },
            {
                'name': 'database',
                'type': 'database server',
                'technologies': ['postgresql', 'linux']
            },
            {
                'name': 'api-gateway',
                'type': 'api service',
                'technologies': ['nodejs', 'docker']
            }
        ]
        
        results = mitre_service.get_techniques_for_system_components(components)
        
        # Check that we get results for each component
        assert 'web-server' in results
        assert 'database' in results
        assert 'api-gateway' in results
        
        # Check that results are limited per component
        for component_name, techniques in results.items():
            assert len(techniques) <= 10  # Default limit
            
            # Check that techniques have component relevance scores
            for technique in techniques:
                assert 'component_relevance' in technique
                assert technique['component_relevance'] > 0
    
    def test_get_techniques_for_entry_points(self, mitre_service):
        """Test getting techniques for entry points"""
        entry_points = [
            {
                'name': 'public-web-interface',
                'type': 'web application',
                'exposure': 'external',
                'authentication_required': False
            },
            {
                'name': 'admin-panel',
                'type': 'web application', 
                'exposure': 'internal',
                'authentication_required': True
            }
        ]
        
        results = mitre_service.get_techniques_for_entry_points(entry_points)
        
        assert len(results) > 0
        
        # External entry points should prioritize initial access techniques
        initial_access_count = sum(
            1 for tech in results 
            if 'initial-access' in tech.get('tactics', [])
        )
        assert initial_access_count > 0
    
    def test_generate_attack_paths(self, mitre_service):
        """Test attack path generation"""
        critical_assets = [
            {
                'name': 'customer-database',
                'type': 'database',
                'criticality': 'critical'
            }
        ]
        
        entry_points = [
            {
                'name': 'public-api',
                'type': 'api',
                'exposure': 'external',
                'authentication_required': False
            }
        ]
        
        components = [
            {'name': 'web-server', 'type': 'web application'},
            {'name': 'app-server', 'type': 'application server'},
            {'name': 'database-server', 'type': 'database'}
        ]
        
        paths = mitre_service.generate_attack_paths(
            critical_assets=critical_assets,
            entry_points=entry_points,
            components=components,
            paths_per_entry=2,
            max_path_length=4
        )
        
        assert len(paths) > 0
        
        # Check path structure
        for path in paths:
            assert 'path_id' in path
            assert 'name' in path
            assert 'techniques' in path
            assert 'likelihood' in path
            assert 'impact' in path
            
            # Check techniques in path
            techniques = path['techniques']
            assert len(techniques) > 0
            assert len(techniques) <= 4  # max_path_length
            
            # First technique should be initial access
            first_technique = techniques[0]
            assert first_technique['step'] == 1
            assert 'initial-access' in mitre_service.get_technique(first_technique['technique_id'])['tactics']
    
    def test_relevance_scoring(self, mitre_service):
        """Test relevance scoring logic"""
        # Test exact name match
        score1 = mitre_service._calculate_relevance_score(
            'Phishing', 'Phishing', 'Some description about phishing'
        )
        
        # Test partial match
        score2 = mitre_service._calculate_relevance_score(
            'phish', 'Phishing', 'Some description about phishing'
        )
        
        # Test description only match
        score3 = mitre_service._calculate_relevance_score(
            'description', 'Unrelated Name', 'Some description here'
        )
        
        # Exact name match should have highest score
        assert score1 > score2
        assert score2 > score3
        assert score3 > 0
    
    def test_component_relevance_scoring(self, mitre_service):
        """Test component relevance scoring"""
        technique = {
            'name': 'Exploit Public-Facing Application',
            'description': 'Adversaries may attempt to exploit web applications',
            'tactics': ['initial-access'],
            'platforms': ['Windows', 'Linux']
        }
        
        # Web component should have high relevance
        web_score = mitre_service._calculate_component_relevance(
            technique, 'web application', ['nginx', 'linux']
        )
        
        # Database component should have lower relevance
        db_score = mitre_service._calculate_component_relevance(
            technique, 'database server', ['postgresql']
        )
        
        assert web_score > db_score
        assert web_score > 1.0  # Should be above base score
    
    def test_singleton_pattern(self):
        """Test singleton pattern for service instance"""
        service1 = get_enhanced_mitre_service()
        service2 = get_enhanced_mitre_service()
        
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in service"""
        service = EnhancedMitreService()
        
        # Test initialization with network error (should fallback to sample data)
        with patch('httpx.AsyncClient.get', side_effect=Exception('Network error')):
            await service.initialize(force_download=True)
            
            # Should still be initialized with sample data
            assert service.initialized
            assert len(service.techniques_cache) > 0
    
    def test_technique_count(self, mitre_service):
        """Test technique count method"""
        count = mitre_service.get_technique_count()
        
        assert count > 0
        assert count == len(mitre_service.techniques_cache)
    
    def test_get_all_techniques(self, mitre_service):
        """Test getting all techniques"""
        all_techniques = mitre_service.get_all_techniques()
        
        assert len(all_techniques) > 0
        assert len(all_techniques) == len(mitre_service.techniques_cache)
        
        # Check that all techniques have required fields
        for technique in all_techniques:
            assert 'id' in technique
            assert 'name' in technique
            assert 'tactics' in technique
            assert 'platforms' in technique


if __name__ == "__main__":
    pytest.main([__file__])
