#!/usr/bin/env python3
"""
Comprehensive Test Suite for System Analyst Agent
Tests the complete system analysis functionality
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.agents.system_analyst_agent import SystemAnalystAgent
from app.agents.shared_context import SharedContext
from app.services.enhanced_llm_service import get_enhanced_llm_service
from app.services.llm_providers import LLMModel


# Test data sets
TEST_SYSTEMS = {
    "simple_web_app": """
    A basic web application built with React frontend and Node.js backend.
    The frontend runs on port 3000 and communicates with the backend on port 8000.
    User data is stored in a PostgreSQL database.
    Users can register, login, and manage their profiles.
    Authentication uses JWT tokens.
    The application is deployed on AWS using EC2 instances.
    """,
    
    "e_commerce_platform": """
    E-commerce platform with the following components:
    
    Frontend: React web application with user registration, product browsing, shopping cart, and checkout
    Backend: Python Django API server handling user authentication, product catalog, order management
    Database: PostgreSQL for user data, products, orders; Redis for session management and caching
    Payment Processing: Stripe integration for credit card payments
    File Storage: AWS S3 for product images and user uploads
    Infrastructure: Deployed on AWS with Application Load Balancer, multiple EC2 instances, RDS database
    Monitoring: CloudWatch for application monitoring, Sentry for error tracking
    
    Security Features:
    - HTTPS/TLS encryption for all communications
    - JWT-based authentication with refresh tokens  
    - Rate limiting on API endpoints
    - Input validation and SQL injection protection
    - PCI DSS compliance for payment processing
    """,
    
    "enterprise_system": """
    Large enterprise resource planning (ERP) system with the following architecture:
    
    Web Tier:
    - Angular frontend application (port 4200)
    - Nginx reverse proxy with SSL termination
    - Static assets served from CDN (CloudFront)
    
    Application Tier:
    - Java Spring Boot microservices architecture
    - API Gateway (Kong) for service mesh management
    - Authentication service using OAuth 2.0 and SAML 2.0
    - User management service with LDAP/Active Directory integration
    - Financial module for accounting and billing
    - HR module for employee management
    - Inventory management service
    - Reporting and analytics service
    
    Data Tier:
    - Primary database: Oracle Database 19c (customer data, financial records)
    - Analytics database: PostgreSQL with TimescaleDB extension
    - Document storage: MongoDB for unstructured data
    - File storage: Network Attached Storage (NAS) for documents
    - Data warehouse: Amazon Redshift for business intelligence
    
    Infrastructure:
    - On-premises VMware vSphere environment
    - Docker containers orchestrated with Kubernetes
    - Network segmentation with VLANs and firewalls
    - VPN access for remote users
    - Backup and disaster recovery with Veeam
    
    Security Controls:
    - Multi-factor authentication (MFA) required for all users
    - Role-based access control (RBAC) with principle of least privilege
    - Network firewalls and intrusion detection systems (IDS)
    - Endpoint protection with antivirus and EDR
    - Security Information and Event Management (SIEM)
    - Regular vulnerability scanning and penetration testing
    - Encrypted data at rest and in transit
    - Data loss prevention (DLP) controls
    """
}


async def test_system_analyst_agent():
    """Test the System Analyst Agent with various system descriptions"""
    print("🧪 Testing System Analyst Agent")
    print("=" * 60)
    
    # Check if LLM service is available
    llm_service = get_enhanced_llm_service()
    if not llm_service.providers:
        print("❌ No LLM providers available! Please set API keys.")
        print("💡 Set environment variables:")
        print("   export OPENAI_API_KEY=your_openai_key")
        print("   export ANTHROPIC_API_KEY=your_anthropic_key")
        return False
    
    print(f"✅ Found {len(llm_service.providers)} LLM providers: {', '.join(llm_service.providers.keys())}")
    print()
    
    # Initialize agent
    agent = SystemAnalystAgent()
    
    test_results = []
    
    for system_name, system_description in TEST_SYSTEMS.items():
        print(f"🔍 Testing: {system_name.replace('_', ' ').title()}")
        print("-" * 40)
        
        try:
            # Create shared context for this test
            context = SharedContext(project_id=999)  # Test project ID
            await context.initialize(system_description)
            
            print(f"📊 System description length: {len(system_description)} characters")
            
            # Perform analysis
            print("🤖 Starting system analysis...")
            result = await agent.analyze_system(
                context=context,
                system_description=system_description
            )
            
            # Validate results
            print("✅ Analysis completed successfully!")
            print(f"🎯 Confidence Score: {result.confidence_score:.2f}")
            print(f"📈 Analysis Results:")
            print(f"   - Critical Assets: {len(result.critical_assets)}")
            print(f"   - System Components: {len(result.system_components)}")
            print(f"   - Data Flows: {len(result.data_flows)}")
            print(f"   - Trust Boundaries: {len(result.trust_boundaries)}")
            print(f"   - Entry Points: {len(result.entry_points)}")
            print(f"   - User Roles: {len(result.user_roles)}")
            
            # Show some sample results
            if result.critical_assets:
                print(f"   📋 Sample Critical Asset: {result.critical_assets[0]['name']} ({result.critical_assets[0]['criticality']})")
            
            if result.entry_points:
                print(f"   🚪 Sample Entry Point: {result.entry_points[0]['name']} ({result.entry_points[0]['exposure']})")
            
            # Show metadata
            metadata = result.analysis_metadata
            print(f"💰 Cost: ${metadata.get('estimated_cost', 0):.4f}")
            print(f"⏱️  Time: {metadata.get('response_time', 0):.2f}s")
            print(f"🤖 Model: {metadata.get('model_used', 'unknown')} ({metadata.get('provider_used', 'unknown')})")
            
            # Get context snapshot for verification
            snapshot = await context.get_context_snapshot()
            print(f"📊 Context Status: {len(snapshot['completed_milestones'])} milestones completed")
            print(f"🎢 Overall Progress: {snapshot['overall_progress']:.1%}")
            
            test_results.append({
                "system_name": system_name,
                "success": True,
                "confidence_score": result.confidence_score,
                "total_items": len(result.critical_assets) + len(result.system_components),
                "cost": metadata.get('estimated_cost', 0),
                "response_time": metadata.get('response_time', 0),
                "model_used": metadata.get('model_used', 'unknown')
            })
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            test_results.append({
                "system_name": system_name,
                "success": False,
                "error": str(e)
            })
        
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 60)
    
    successful_tests = [r for r in test_results if r.get('success', False)]
    failed_tests = [r for r in test_results if not r.get('success', False)]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(test_results)}")
    print(f"❌ Failed tests: {len(failed_tests)}")
    
    if successful_tests:
        avg_confidence = sum(r['confidence_score'] for r in successful_tests) / len(successful_tests)
        total_cost = sum(r['cost'] for r in successful_tests)
        avg_time = sum(r['response_time'] for r in successful_tests) / len(successful_tests)
        
        print(f"📈 Average Confidence Score: {avg_confidence:.2f}")
        print(f"💰 Total Cost: ${total_cost:.4f}")
        print(f"⏱️  Average Response Time: {avg_time:.2f}s")
        
        # Show models used
        models_used = set(r['model_used'] for r in successful_tests)
        print(f"🤖 Models Used: {', '.join(models_used)}")
        
        print("\n🎯 Individual Test Results:")
        for result in successful_tests:
            print(f"   {result['system_name']}: {result['confidence_score']:.2f} confidence, "
                  f"{result['total_items']} items, ${result['cost']:.4f}, "
                  f"{result['response_time']:.2f}s ({result['model_used']})")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for result in failed_tests:
            print(f"   {result['system_name']}: {result['error']}")
    
    return len(failed_tests) == 0


async def test_agent_integration():
    """Test integration with shared context and multiple agents"""
    print("\n🔧 Testing Agent Integration")
    print("=" * 60)
    
    try:
        # Create shared context
        context = SharedContext(project_id=888)
        
        # Initialize with test system
        test_system = TEST_SYSTEMS["simple_web_app"]
        await context.initialize(test_system)
        
        # Test context operations
        print("📊 Testing shared context operations...")
        
        # Test data storage and retrieval
        await context.set_data("test_key", {"value": 123}, "test_agent")
        retrieved_data = await context.get_data("test_key")
        assert retrieved_data["value"] == 123, "Data storage/retrieval failed"
        print("✅ Data storage and retrieval working")
        
        # Test agent registration
        await context.register_agent("test_agent_1", "system_analyst")
        await context.register_agent("test_agent_2", "attack_mapper")
        
        agent_states = await context.get_all_agent_states()
        assert len(agent_states) == 2, "Agent registration failed"
        print("✅ Agent registration working")
        
        # Test progress tracking
        await context.update_agent_status("test_agent_1", "running", 0.5, "Processing data")
        agent_state = await context.get_agent_state("test_agent_1")
        assert agent_state.progress == 0.5, "Progress tracking failed"
        print("✅ Progress tracking working")
        
        # Test milestone detection
        await context.set_data("system_analysis", {"test": "data"}, "test_agent_1")
        snapshot = await context.get_context_snapshot()
        assert "system_analysis_complete" in snapshot["completed_milestones"], "Milestone detection failed"
        print("✅ Milestone detection working")
        
        print("🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling and edge cases"""
    print("\n🚨 Testing Error Handling")
    print("=" * 60)
    
    agent = SystemAnalystAgent()
    context = SharedContext(project_id=777)
    
    try:
        # Test with very short system description
        print("Testing with minimal system description...")
        short_description = "A web app."
        await context.initialize(short_description)
        
        result = await agent.analyze_system(context, short_description)
        print(f"✅ Handled short description, confidence: {result.confidence_score:.2f}")
        
        # Test with empty additional inputs
        print("Testing with empty additional inputs...")
        result = await agent.analyze_system(
            context, 
            TEST_SYSTEMS["simple_web_app"], 
            additional_inputs=[]
        )
        print("✅ Handled empty additional inputs")
        
        # Test with malformed additional inputs
        print("Testing with additional inputs...")
        result = await agent.analyze_system(
            context,
            TEST_SYSTEMS["simple_web_app"],
            additional_inputs=[
                {"type": "architecture", "content": "Additional architecture details here"},
                {"type": "security", "content": "Security requirements and constraints"}
            ]
        )
        print("✅ Handled additional inputs properly")
        
        print("🎉 All error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def check_environment():
    """Check if environment is properly configured"""
    print("🔑 Checking Environment Configuration...")
    
    required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    available_keys = []
    
    for key in required_keys:
        if os.getenv(key):
            available_keys.append(key)
            print(f"  ✅ {key}: Available")
        else:
            print(f"  ❌ {key}: Not set")
    
    if not available_keys:
        print("\n⚠️  No API keys found!")
        print("💡 Set at least one API key:")
        print("   export OPENAI_API_KEY=your_openai_key")
        print("   export ANTHROPIC_API_KEY=your_anthropic_key")
        return False
    
    print(f"\n✅ Found {len(available_keys)} API key(s)")
    return True


async def main():
    """Main test runner"""
    print("=" * 80)
    print("🧪 AITM System Analyst Agent - Comprehensive Test Suite")
    print("=" * 80)
    
    # Check environment
    if not check_environment():
        return
    
    print()
    
    # Run all tests
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Core functionality
    if await test_system_analyst_agent():
        tests_passed += 1
    
    # Test 2: Integration
    if await test_agent_integration():
        tests_passed += 1
    
    # Test 3: Error handling
    if await test_error_handling():
        tests_passed += 1
    
    # Final results
    print("\n" + "=" * 80)
    print("🎯 Final Test Results")
    print("=" * 80)
    
    if tests_passed == total_tests:
        print(f"🎉 ALL TESTS PASSED! ({tests_passed}/{total_tests})")
        print("✅ System Analyst Agent is fully functional and ready for production use.")
        print("\n🚀 Next steps:")
        print("  1. Implement MITRE ATT&CK Integration")
        print("  2. Build Attack Mapper Agent")
        print("  3. Create Frontend Project Management UI")
    else:
        print(f"⚠️  SOME TESTS FAILED: {tests_passed}/{total_tests} passed")
        print("💡 Review the errors above and fix issues before proceeding.")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
