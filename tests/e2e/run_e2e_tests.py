#!/usr/bin/env python3
"""
Test runner for end-to-end authorization tests.
This script sets up the test environment and runs all E2E tests.
"""

import asyncio
import os
import sys
import subprocess
import time
import signal
import requests
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class E2ETestRunner:
    """Runner for end-to-end authorization tests"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.max_startup_wait = 60  # seconds
    
    def check_service_health(self, url: str, service_name: str) -> bool:
        """Check if a service is healthy and responding"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is healthy at {url}")
                return True
            else:
                print(f"⚠️ {service_name} returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ {service_name} health check failed: {e}")
            return False
    
    def wait_for_service(self, url: str, service_name: str) -> bool:
        """Wait for a service to become available"""
        print(f"⏳ Waiting for {service_name} to start at {url}...")
        
        for attempt in range(self.max_startup_wait):
            if self.check_service_health(url, service_name):
                return True
            
            if attempt % 10 == 0:  # Print every 10 seconds
                print(f"   Still waiting for {service_name}... ({attempt}s)")
            
            time.sleep(1)
        
        print(f"❌ {service_name} failed to start within {self.max_startup_wait} seconds")
        return False
    
    def start_backend(self) -> bool:
        """Start the backend server"""
        print("🚀 Starting backend server...")
        
        # Check if backend is already running
        if self.check_service_health(self.base_url, "Backend"):
            print("✅ Backend is already running")
            return True
        
        try:
            # Start the backend server
            backend_dir = project_root / "backend"
            env = os.environ.copy()
            env.update({
                "ENVIRONMENT": "test",
                "SECRET_KEY": "test-secret-key-for-e2e-tests-only",
                "DATABASE_URL": "sqlite:///./test_e2e.db",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "60"
            })
            
            self.backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for backend to start
            if self.wait_for_service(self.base_url, "Backend"):
                print("✅ Backend server started successfully")
                return True
            else:
                print("❌ Backend server failed to start")
                self.stop_backend()
                return False
                
        except Exception as e:
            print(f"❌ Error starting backend: {e}")
            return False
    
    def stop_backend(self):
        """Stop the backend server"""
        if self.backend_process:
            print("🛑 Stopping backend server...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            self.backend_process = None
    
    def start_frontend(self) -> bool:
        """Start the frontend server (if needed)"""
        print("🚀 Starting frontend server...")
        
        # Check if frontend is already running
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("✅ Frontend is already running")
                return True
        except requests.exceptions.RequestException:
            pass
        
        # For now, we'll skip frontend startup as we're testing API directly
        # In a real scenario, you would start your React/Vue/Angular frontend here
        print("ℹ️ Skipping frontend startup (testing API directly)")
        return True
    
    def stop_frontend(self):
        """Stop the frontend server"""
        if self.frontend_process:
            print("🛑 Stopping frontend server...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            self.frontend_process = None
    
    def install_playwright(self) -> bool:
        """Install Playwright browsers if needed"""
        print("📦 Checking Playwright installation...")
        
        try:
            # Check if playwright is installed
            result = subprocess.run([sys.executable, "-c", "import playwright"], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print("📦 Installing Playwright...")
                subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
            
            # Install browsers
            print("📦 Installing Playwright browsers...")
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            
            print("✅ Playwright installation complete")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Playwright: {e}")
            return False
    
    def run_authorization_tests(self) -> int:
        """Run the authorization E2E tests"""
        print("\n🧪 Running End-to-End Authorization Tests...")
        print("=" * 60)
        
        try:
            # Import and run the simplified API tests
            from test_api_authorization_e2e import APIAuthorizationE2ETests
            
            # Set environment variables for tests
            os.environ["BASE_URL"] = self.base_url
            os.environ["FRONTEND_URL"] = self.frontend_url
            
            # Run the tests
            tester = APIAuthorizationE2ETests(self.base_url)
            success = tester.run_all_tests()
            
            if success:
                print("\n🎉 All E2E authorization tests passed!")
                return 0
            else:
                print(f"\n❌ Some E2E authorization tests failed!")
                return 1
                
        except Exception as e:
            print(f"❌ Error running E2E tests: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        self.stop_backend()
        self.stop_frontend()
        
        # Clean up test database
        test_db_path = project_root / "backend" / "test_e2e.db"
        if test_db_path.exists():
            test_db_path.unlink()
            print("✅ Cleaned up test database")
    
    def run(self) -> int:
        """Run the complete E2E test suite"""
        print("🚀 Starting End-to-End Authorization Test Suite")
        print("=" * 60)
        
        exit_code = 1
        
        try:
            # Install Playwright if needed
            if not self.install_playwright():
                return 1
            
            # Start services
            if not self.start_backend():
                return 1
            
            if not self.start_frontend():
                return 1
            
            # Run tests
            exit_code = self.run_authorization_tests()
            
        except KeyboardInterrupt:
            print("\n⚠️ Test run interrupted by user")
            exit_code = 130
        except Exception as e:
            print(f"\n❌ Unexpected error during test run: {e}")
            import traceback
            traceback.print_exc()
            exit_code = 1
        finally:
            self.cleanup()
        
        return exit_code

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n⚠️ Received interrupt signal, cleaning up...")
    sys.exit(130)

def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the test suite
    runner = E2ETestRunner()
    exit_code = runner.run()
    
    if exit_code == 0:
        print("\n🎉 End-to-End Authorization Tests Completed Successfully!")
    else:
        print(f"\n❌ End-to-End Authorization Tests Failed (exit code: {exit_code})")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())