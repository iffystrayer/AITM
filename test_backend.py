#!/usr/bin/env python3
"""
Simple script to test the AITM backend
"""

import sys
import os

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    # Test imports
    print("Testing imports...")
    
    # Test basic imports
    import fastapi
    print(f"✅ FastAPI: {fastapi.__version__}")
    
    import uvicorn
    print(f"✅ Uvicorn: {uvicorn.__version__}")
    
    # Test AITM imports
    from app.core.config import get_settings
    print("✅ Config module imported")
    
    from app.core.database import Base
    print("✅ Database module imported")
    
    from app.services.llm_service import llm_service
    print("✅ LLM service imported")
    
    from app.services.mitre_service import mitre_service
    print("✅ MITRE service imported")
    
    # Test configuration
    settings = get_settings()
    print(f"✅ Settings loaded - Backend port: {settings.backend_port}")
    
    # Test LLM providers
    providers = llm_service.get_available_providers()
    print(f"✅ Available LLM providers: {providers}")
    
    print("\n🎉 All backend components imported successfully!")
    print("✅ Backend is ready to start")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all dependencies are installed:")
    print("   cd backend && pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
