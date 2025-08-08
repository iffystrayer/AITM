#!/usr/bin/env python3
"""
Simple test script to verify backend imports and configuration
"""

import sys
import os

print("🧪 AITM Backend Import Test")
print("=" * 50)

print(f"🐍 Python version: {sys.version}")
print(f"📁 Current working directory: {os.getcwd()}")
print(f"📍 Python path: {sys.path}")
print()

# Test core imports
print("🔍 Testing core imports...")
try:
    import fastapi
    print(f"✅ FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"❌ FastAPI: {e}")

try:
    import uvicorn
    print(f"✅ Uvicorn: {uvicorn.__version__}")
except ImportError as e:
    print(f"❌ Uvicorn: {e}")

try:
    import pydantic
    print(f"✅ Pydantic: {pydantic.__version__}")
except ImportError as e:
    print(f"❌ Pydantic: {e}")

try:
    import sqlalchemy
    print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"❌ SQLAlchemy: {e}")

print()

# Test app module imports
print("🔍 Testing app module imports...")
try:
    from app.core.config import get_settings
    print("✅ app.core.config")
except ImportError as e:
    print(f"❌ app.core.config: {e}")

try:
    from app.core.database import init_db
    print("✅ app.core.database")
except ImportError as e:
    print(f"❌ app.core.database: {e}")

try:
    from app.core.logging import setup_logging
    print("✅ app.core.logging")
except ImportError as e:
    print(f"❌ app.core.logging: {e}")

try:
    from app.api.v1.router import api_router
    print("✅ app.api.v1.router")
except ImportError as e:
    print(f"❌ app.api.v1.router: {e}")

try:
    from app.services.mitre_service import MitreAttackService
    print("✅ app.services.mitre_service")
except ImportError as e:
    print(f"❌ app.services.mitre_service: {e}")

print()

# Test main module import
print("🔍 Testing main module import...")
try:
    import app.main
    print("✅ app.main module imported successfully")
except ImportError as e:
    print(f"❌ app.main: {e}")

print()
print("🎯 Import test complete!")
