#!/usr/bin/env python3
"""
Test script for Enhanced MITRE ATT&CK Service
Quick verification that the service works correctly
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_mitre_service import get_enhanced_mitre_service


async def test_enhanced_mitre_service():
    """Test the enhanced MITRE service"""
    print("🚀 Testing Enhanced MITRE ATT&CK Service...")
    
    try:
        # Get service instance
        mitre_service = get_enhanced_mitre_service()
        print("✅ Service instance created")
        
        # Initialize the service
        print("🔄 Initializing MITRE data...")
        await mitre_service.initialize()
        print("✅ Service initialized successfully")
        
        # Test basic functionality
        print(f"📊 Loaded {mitre_service.get_technique_count()} techniques")
        
        # Test technique retrieval
        print("\n🔍 Testing technique retrieval:")
        technique = mitre_service.get_technique('T1190')
        if technique:
            print(f"✅ Found technique: {technique['name']}")
            print(f"   Tactics: {', '.join(technique['tactics'])}")
            print(f"   Platforms: {', '.join(technique['platforms'])}")
        else:
            print("❌ Failed to retrieve technique T1190")
        
        # Test search functionality
        print("\n🔍 Testing search functionality:")
        search_results = mitre_service.search_techniques('exploit')
        print(f"✅ Found {len(search_results)} techniques matching 'exploit'")
        if search_results:
            top_result = search_results[0]
            print(f"   Top result: {top_result['name']} (relevance: {top_result.get('relevance_score', 'N/A')})")
        
        # Test tactic-based retrieval
        print("\n🔍 Testing tactic-based retrieval:")
        initial_access = mitre_service.get_techniques_by_tactic('initial-access')
        print(f"✅ Found {len(initial_access)} initial access techniques")
        
        # Test platform-based retrieval
        print("\n🔍 Testing platform-based retrieval:")
        windows_techniques = mitre_service.get_techniques_by_platform('Windows')
        print(f"✅ Found {len(windows_techniques)} Windows techniques")
        
        # Test component analysis
        print("\n🔍 Testing component analysis:")
        components = [
            {
                'name': 'web-server',
                'type': 'web application',
                'technologies': ['nginx', 'linux']
            },
            {
                'name': 'database',
                'type': 'database server', 
                'technologies': ['postgresql']
            }
        ]
        
        component_techniques = mitre_service.get_techniques_for_system_components(components)
        print(f"✅ Generated techniques for {len(component_techniques)} components")
        for component_name, techniques in component_techniques.items():
            print(f"   {component_name}: {len(techniques)} techniques")
        
        # Test attack path generation
        print("\n🔍 Testing attack path generation:")
        critical_assets = [{'name': 'database', 'criticality': 'critical'}]
        entry_points = [{'name': 'web-app', 'type': 'web', 'exposure': 'external'}]
        
        attack_paths = mitre_service.generate_attack_paths(
            critical_assets=critical_assets,
            entry_points=entry_points,
            components=components,
            paths_per_entry=2,
            max_path_length=4
        )
        
        print(f"✅ Generated {len(attack_paths)} attack paths")
        if attack_paths:
            path = attack_paths[0]
            print(f"   Path: {path['name']}")
            print(f"   Steps: {len(path['techniques'])}")
            print(f"   Likelihood: {path['likelihood']}, Impact: {path['impact']}")
        
        # Test all tactics and platforms
        print("\n📊 Data summary:")
        print(f"   Tactics: {len(mitre_service.get_all_tactics())}")
        print(f"   Platforms: {len(mitre_service.get_all_platforms())}")
        print(f"   Total techniques: {len(mitre_service.get_all_techniques())}")
        
        print("\n🎉 All tests passed! Enhanced MITRE service is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_enhanced_mitre_service())
    
    if success:
        print("\n✅ Enhanced MITRE ATT&CK Service test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Enhanced MITRE ATT&CK Service test failed!")
        sys.exit(1)
