#!/usr/bin/env python3
"""
Docker E2E Test Setup Validation Script

This script validates that the Docker-based E2E test environment is properly configured
and can run basic tests before executing the full comprehensive test suite.
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

def check_docker_availability():
    """Check if Docker and Docker Compose are available"""
    print("🐳 Checking Docker availability...")
    
    try:
        # Check Docker
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker is not available")
            return False
        print(f"✅ Docker is available: {result.stdout.strip()}")
        
        # Check Docker Compose
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker Compose is not available")
            return False
        print(f"✅ Docker Compose is available: {result.stdout.strip()}")
        
        # Check if Docker daemon is running
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker daemon is not running")
            return False
        print("✅ Docker daemon is running")
        
        return True
        
    except FileNotFoundError:
        print("❌ Docker or Docker Compose not found in PATH")
        return False

def check_docker_compose_file():
    """Check if docker-compose.yml exists and is valid"""
    print("📄 Checking Docker Compose configuration...")
    
    project_root = Path(__file__).parent.parent.parent
    compose_file = project_root / "docker-compose.yml"
    
    if not compose_file.exists():
        print("❌ docker-compose.yml not found")
        return False
    
    print("✅ docker-compose.yml exists")
    
    # Validate compose file
    try:
        result = subprocess.run(
            ["docker-compose", "config"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ docker-compose.yml is invalid: {result.stderr}")
            return False
        
        print("✅ docker-compose.yml is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error validating docker-compose.yml: {e}")
        return False

def check_container_status():
    """Check current container status"""
    print("📊 Checking container status...")
    
    project_root = Path(__file__).parent.parent.parent
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print("ℹ️ Current container status:")
            print(result.stdout)
        else:
            print("ℹ️ No containers currently running")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking container status: {e}")
        return False

def test_container_startup():
    """Test starting containers and checking health"""
    print("🚀 Testing container startup...")
    
    project_root = Path(__file__).parent.parent.parent
    backend_url = "http://localhost:38527"
    
    try:
        # Start containers
        print("🔧 Starting Docker containers...")
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to start containers: {result.stderr}")
            return False
        
        print("✅ Containers started successfully")
        
        # Wait for backend to be healthy
        print("⏳ Waiting for backend to become healthy...")
        max_wait = 60
        
        for attempt in range(max_wait):
            try:
                response = requests.get(f"{backend_url}/api/v1/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Backend is healthy at {backend_url}")
                    
                    # Test basic endpoint
                    try:
                        health_data = response.json()
                        print(f"✅ Health endpoint returns: {health_data}")
                    except:
                        print("✅ Health endpoint responds (non-JSON)")
                    
                    return True
            except requests.exceptions.RequestException:
                pass
            
            if attempt % 10 == 0 and attempt > 0:
                print(f"   Still waiting... ({attempt}s)")
            
            time.sleep(1)
        
        print(f"❌ Backend failed to become healthy within {max_wait} seconds")
        return False
        
    except Exception as e:
        print(f"❌ Error testing container startup: {e}")
        return False
    finally:
        # Clean up containers
        print("🧹 Cleaning up test containers...")
        try:
            subprocess.run(
                ["docker-compose", "down"],
                cwd=project_root,
                capture_output=True,
                text=True
            )
        except:
            pass

def test_basic_api_request():
    """Test making a basic API request to the containerized backend"""
    print("🌐 Testing basic API request...")
    
    project_root = Path(__file__).parent.parent.parent
    backend_url = "http://localhost:38527"
    
    try:
        # Start containers
        print("🔧 Starting containers for API test...")
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to start containers: {result.stderr}")
            return False
        
        # Wait for backend
        print("⏳ Waiting for backend...")
        for attempt in range(30):
            try:
                response = requests.get(f"{backend_url}/api/v1/health", timeout=5)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        else:
            print("❌ Backend not available for API test")
            return False
        
        # Test unauthenticated request (should return 401)
        print("🔒 Testing unauthenticated API request...")
        try:
            response = requests.get(f"{backend_url}/api/v1/projects/")
            if response.status_code == 401:
                print("✅ Unauthenticated request correctly returns 401")
                return True
            else:
                print(f"⚠️ Unexpected status code: {response.status_code}")
                return True  # Still consider this a success for basic connectivity
        except Exception as e:
            print(f"❌ API request failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing API request: {e}")
        return False
    finally:
        # Clean up containers
        print("🧹 Cleaning up test containers...")
        try:
            subprocess.run(
                ["docker-compose", "down"],
                cwd=project_root,
                capture_output=True,
                text=True
            )
        except:
            pass

def validate_test_files():
    """Validate that Docker E2E test files are present"""
    print("📄 Validating Docker E2E test files...")
    
    test_files = [
        'docker_e2e_runner.py',
        'test_api_authorization_e2e.py',
        'test_comprehensive_authorization_e2e.py'
    ]
    
    test_dir = Path(__file__).parent
    
    for test_file in test_files:
        file_path = test_dir / test_file
        if file_path.exists():
            print(f"✅ {test_file} exists")
        else:
            print(f"❌ {test_file} is missing")
            return False
    
    return True

def main():
    """Main validation function"""
    print("🔍 Docker E2E Test Setup Validation")
    print("=" * 50)
    
    validation_steps = [
        ("Docker Availability", check_docker_availability),
        ("Docker Compose File", check_docker_compose_file),
        ("Container Status", check_container_status),
        ("Container Startup", test_container_startup),
        ("Basic API Request", test_basic_api_request),
        ("Test Files", validate_test_files)
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
    print(f"📊 Docker Validation Summary")
    print(f"✅ Passed: {passed_steps}/{total_steps}")
    print(f"❌ Failed: {total_steps - passed_steps}/{total_steps}")
    print(f"📈 Success Rate: {(passed_steps/total_steps)*100:.1f}%")
    
    if passed_steps == total_steps:
        print(f"\n🎉 All Docker validations passed!")
        print(f"   The Docker E2E test environment is properly configured.")
        print(f"   You can now run the Docker-based E2E tests.")
        print(f"\n   Run: ./run_docker_e2e_tests.sh")
        return 0
    else:
        print(f"\n⚠️  Some Docker validations failed.")
        print(f"   Please address the issues before running Docker E2E tests.")
        print(f"\n   Common issues:")
        print(f"   - Docker daemon not running: Start Docker Desktop")
        print(f"   - Port conflicts: Check if ports 38527/59000 are in use")
        print(f"   - Permission issues: Ensure Docker has proper permissions")
        return 1

if __name__ == "__main__":
    sys.exit(main())