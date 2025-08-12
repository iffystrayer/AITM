#!/usr/bin/env python3
"""
E2E Test Setup Validation Script

This script validates that the E2E test environment is properly configured
and can run basic tests before executing the full comprehensive test suite.
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, found {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def check_dependencies():
    """Check if required dependencies are available"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'requests',
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'jwt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_backend_structure():
    """Check if backend structure is correct"""
    print("🏗️ Checking backend structure...")
    
    required_files = [
        'backend/app/main.py',
        'backend/app/core/auth.py',
        'backend/app/core/permissions.py',
        'backend/app/api/v1/endpoints/projects.py'
    ]
    
    project_root = Path(__file__).parent.parent.parent
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} is missing")
            return False
    
    return True

def test_backend_startup():
    """Test if backend can start successfully"""
    print("🚀 Testing backend startup...")
    
    backend_dir = Path(__file__).parent.parent.parent / "backend"
    env = os.environ.copy()
    env.update({
        "ENVIRONMENT": "test",
        "SECRET_KEY": "test-validation-secret-key-32-chars-long",
        "DATABASE_URL": "sqlite:///./test_validation.db",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60"
    })
    
    try:
        # Start backend process
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"],
            cwd=backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for backend to start
        base_url = "http://localhost:8001"
        max_wait = 30
        
        for attempt in range(max_wait):
            try:
                response = requests.get(f"{base_url}/api/v1/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Backend started successfully on port 8001")
                    
                    # Test basic endpoint
                    try:
                        health_data = response.json()
                        print(f"✅ Health endpoint returns: {health_data}")
                    except:
                        print("✅ Health endpoint responds (non-JSON)")
                    
                    # Clean up
                    process.terminate()
                    process.wait(timeout=10)
                    
                    # Clean up test database
                    test_db = backend_dir / "test_validation.db"
                    if test_db.exists():
                        test_db.unlink()
                    
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        print(f"❌ Backend failed to start within {max_wait} seconds")
        process.terminate()
        process.wait(timeout=10)
        return False
        
    except Exception as e:
        print(f"❌ Error testing backend startup: {e}")
        return False

def test_basic_auth_flow():
    """Test basic authentication flow"""
    print("🔐 Testing basic authentication flow...")
    
    # This is a simplified test - the full tests will be more comprehensive
    try:
        # Import auth service to test basic functionality
        from app.core.auth import AuthService
        
        auth_service = AuthService()
        
        # Test password hashing
        password = "TestPassword123!"
        hashed = auth_service.get_password_hash(password)
        
        if auth_service.verify_password(password, hashed):
            print("✅ Password hashing and verification works")
        else:
            print("❌ Password hashing and verification failed")
            return False
        
        # Test token creation (basic test)
        try:
            token = auth_service.create_access_token("test-user-id")
            if token and len(token) > 50:  # JWT tokens are typically longer
                print("✅ JWT token creation works")
            else:
                print("❌ JWT token creation failed")
                return False
        except Exception as e:
            print(f"❌ JWT token creation error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing authentication flow: {e}")
        return False

def test_permission_system():
    """Test basic permission system functionality"""
    print("👥 Testing permission system...")
    
    try:
        from app.core.permissions import PermissionService, Permission, Role
        
        permission_service = PermissionService()
        
        # Test role permissions
        admin_permissions = permission_service.get_role_permissions(Role.ADMIN)
        viewer_permissions = permission_service.get_role_permissions(Role.VIEWER)
        
        if Permission.CREATE_PROJECTS in admin_permissions:
            print("✅ Admin has CREATE_PROJECTS permission")
        else:
            print("❌ Admin missing CREATE_PROJECTS permission")
            return False
        
        if Permission.CREATE_PROJECTS not in viewer_permissions:
            print("✅ Viewer correctly lacks CREATE_PROJECTS permission")
        else:
            print("❌ Viewer incorrectly has CREATE_PROJECTS permission")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing permission system: {e}")
        return False

def validate_e2e_test_files():
    """Validate that E2E test files are present and importable"""
    print("📄 Validating E2E test files...")
    
    test_files = [
        'test_api_authorization_e2e.py',
        'test_comprehensive_authorization_e2e.py',
        'run_comprehensive_e2e_tests.py'
    ]
    
    test_dir = Path(__file__).parent
    
    for test_file in test_files:
        file_path = test_dir / test_file
        if file_path.exists():
            print(f"✅ {test_file} exists")
            
            # Try to import the test file
            try:
                if test_file == 'test_api_authorization_e2e.py':
                    from test_api_authorization_e2e import APIAuthorizationE2ETests
                    print(f"✅ {test_file} is importable")
                elif test_file == 'test_comprehensive_authorization_e2e.py':
                    from test_comprehensive_authorization_e2e import ComprehensiveAuthorizationE2ETests
                    print(f"✅ {test_file} is importable")
                elif test_file == 'run_comprehensive_e2e_tests.py':
                    from run_comprehensive_e2e_tests import ComprehensiveE2ETestRunner
                    print(f"✅ {test_file} is importable")
            except Exception as e:
                print(f"❌ {test_file} import error: {e}")
                return False
        else:
            print(f"❌ {test_file} is missing")
            return False
    
    return True

def main():
    """Main validation function"""
    print("🔍 E2E Test Setup Validation")
    print("=" * 50)
    
    validation_steps = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Backend Structure", check_backend_structure),
        ("Backend Startup", test_backend_startup),
        ("Authentication Flow", test_basic_auth_flow),
        ("Permission System", test_permission_system),
        ("E2E Test Files", validate_e2e_test_files)
    ]
    
    passed_steps = 0
    total_steps = len(validation_steps)
    
    for step_name, step_function in validation_steps:
        print(f"\n--- {step_name} ---")
        try:
            if step_function():
                passed_steps += 1
                print(f"✅ {step_name} validation passed")
            else:
                print(f"❌ {step_name} validation failed")
        except Exception as e:
            print(f"❌ {step_name} validation error: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"📊 Validation Summary")
    print(f"✅ Passed: {passed_steps}/{total_steps}")
    print(f"❌ Failed: {total_steps - passed_steps}/{total_steps}")
    print(f"📈 Success Rate: {(passed_steps/total_steps)*100:.1f}%")
    
    if passed_steps == total_steps:
        print(f"\n🎉 All validations passed!")
        print(f"   The E2E test environment is properly configured.")
        print(f"   You can now run the comprehensive E2E tests.")
        print(f"\n   Run: ./run_comprehensive_e2e_tests.sh")
        return 0
    else:
        print(f"\n⚠️  Some validations failed.")
        print(f"   Please address the issues before running E2E tests.")
        return 1

if __name__ == "__main__":
    sys.exit(main())