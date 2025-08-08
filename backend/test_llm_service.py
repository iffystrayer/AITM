#!/usr/bin/env python3
"""
Test the enhanced LLM service functionality
Run this to verify the LLM providers are working correctly
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.enhanced_llm_service import get_enhanced_llm_service
from app.services.llm_providers import LLMModel
from app.core.prompts import get_system_analyst_prompt


async def test_llm_service():
    """Test the LLM service functionality"""
    print("🧪 Testing Enhanced LLM Service\n")
    
    # Initialize service
    llm_service = get_enhanced_llm_service()
    
    # Show provider info
    print("📋 Provider Information:")
    info = llm_service.get_provider_info()
    print(f"Total providers: {info['total_providers']}")
    for name, provider_info in info['providers'].items():
        print(f"  - {name}: {len(provider_info['supported_models'])} models")
        for model in provider_info['supported_models'][:3]:  # Show first 3 models
            print(f"    - {model}")
    print()
    
    if not llm_service.providers:
        print("❌ No LLM providers available!")
        print("💡 Set environment variables:")
        print("   export OPENAI_API_KEY=your_openai_key")
        print("   export ANTHROPIC_API_KEY=your_anthropic_key")
        return False
    
    # Test basic completion
    print("🤖 Testing Basic Completion...")
    try:
        response = await llm_service.generate_completion(
            prompt="What is threat modeling in cybersecurity? Give a brief 2-sentence answer.",
            max_tokens=100
        )
        
        print(f"✅ Success! Provider: {response.provider}")
        print(f"📊 Model: {response.model}")
        print(f"⏱️  Time: {response.response_time:.2f}s")
        if response.token_usage:
            print(f"🎯 Tokens: {response.token_usage.total}")
            print(f"💰 Cost: ${response.token_usage.estimated_cost:.4f}")
        print(f"📝 Response: {response.content[:200]}...")
        print()
        
    except Exception as e:
        print(f"❌ Basic completion failed: {e}")
        return False
    
    # Test structured completion with system analyst prompt
    print("🎯 Testing Structured Completion (System Analyst)...")
    try:
        # Sample system description
        system_desc = """
        Web application with React frontend, Node.js backend, PostgreSQL database.
        Deployed on AWS with load balancer. Users authenticate via OAuth2.
        Stores customer personal data and payment information.
        Admin panel for user management. REST API for mobile app integration.
        """
        
        system_prompt, user_prompt, response_format = get_system_analyst_prompt(system_desc)
        
        response = await llm_service.generate_structured_completion(
            prompt=user_prompt,
            response_schema=response_format,
            system_prompt=system_prompt,
            max_tokens=2000
        )
        
        print(f"✅ Success! Provider: {response.provider}")
        print(f"📊 Model: {response.model}")
        print(f"⏱️  Time: {response.response_time:.2f}s")
        if response.token_usage:
            print(f"🎯 Tokens: {response.token_usage.total}")
            print(f"💰 Cost: ${response.token_usage.estimated_cost:.4f}")
        
        # Try to parse JSON response
        try:
            analysis = json.loads(response.content)
            print(f"📋 Analysis Results:")
            print(f"  - Critical Assets: {len(analysis.get('critical_assets', []))}")
            print(f"  - System Components: {len(analysis.get('system_components', []))}")
            print(f"  - Data Flows: {len(analysis.get('data_flows', []))}")
            print(f"  - Trust Boundaries: {len(analysis.get('trust_boundaries', []))}")
            print(f"  - Entry Points: {len(analysis.get('entry_points', []))}")
            
            if analysis.get('critical_assets'):
                print(f"  First Asset: {analysis['critical_assets'][0].get('name', 'Unknown')}")
            
        except json.JSONDecodeError:
            print(f"⚠️  Response not valid JSON: {response.content[:200]}...")
        
        print()
        
    except Exception as e:
        print(f"❌ Structured completion failed: {e}")
        return False
    
    # Test health check
    print("🏥 Testing Health Check...")
    try:
        health = await llm_service.health_check()
        print(f"Overall Health: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}")
        for provider, status in health['providers'].items():
            if status['healthy']:
                print(f"  {provider}: ✅ {status['response_time']:.2f}s")
            else:
                print(f"  {provider}: ❌ {status['error']}")
        print()
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    print("🎉 All tests passed! LLM service is working correctly.")
    return True


def check_environment():
    """Check if environment variables are set"""
    print("🔑 Checking Environment Variables...")
    
    keys_to_check = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", 
        "GOOGLE_API_KEY"
    ]
    
    available_keys = []
    for key in keys_to_check:
        value = os.getenv(key)
        if value:
            available_keys.append(key)
            print(f"  ✅ {key}: Set ({value[:10]}...)")
        else:
            print(f"  ❌ {key}: Not set")
    
    if not available_keys:
        print("\n⚠️  No API keys found! Set at least one:")
        print("   export OPENAI_API_KEY=your_openai_key")
        print("   export ANTHROPIC_API_KEY=your_anthropic_key")
        print("   export GOOGLE_API_KEY=your_gemini_key")
        return False
    
    print(f"\n✅ Found {len(available_keys)} API keys")
    return True


async def main():
    """Main test function"""
    print("=" * 60)
    print("🚀 AITM Enhanced LLM Service Test")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        return
    
    print()
    
    # Run tests
    success = await test_llm_service()
    
    print("=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ Your LLM service is ready for development.")
    else:
        print("❌ Some tests failed.")
        print("💡 Check your API keys and network connection.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
