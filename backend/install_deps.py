#!/usr/bin/env python3
"""
Smart dependency installer for AITM backend
Handles Python version compatibility issues
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Run command and return result"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return e

def check_python_version():
    """Check Python version and return compatibility info"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3:
        print("❌ Python 3 is required")
        return False
    
    if version.minor >= 13:
        print("⚠️  Python 3.13+ detected - using compatibility mode")
        return "py313"
    elif version.minor >= 11:
        print("✅ Python 3.11+ detected - standard installation")
        return "standard"
    else:
        print("⚠️  Python < 3.11 detected - some packages may not be available")
        return "legacy"

def install_dependencies(mode="standard"):
    """Install dependencies based on Python version"""
    
    # Upgrade pip first
    print("📦 Upgrading pip...")
    result = run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    if mode == "py313":
        print("🐍 Using Python 3.13 compatible requirements...")
        requirements_file = "requirements-py313.txt"
    else:
        print("🐍 Using standard requirements...")
        requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"❌ Requirements file {requirements_file} not found")
        return False
    
    # Try installing with pre-built wheels first
    print("📦 Installing dependencies (preferring wheels)...")
    result = run_command([
        sys.executable, "-m", "pip", "install", 
        "--prefer-binary",
        "-r", requirements_file
    ], check=False)
    
    if result.returncode != 0:
        print("⚠️  Standard installation failed, trying alternatives...")
        
        if mode == "py313":
            # For Python 3.13, try installing core packages individually
            core_packages = [
                "fastapi>=0.108.0",
                "uvicorn[standard]>=0.25.0", 
                "pydantic>=2.8.2",
                "sqlalchemy>=2.0.23",
                "aiosqlite>=0.19.0",
                "httpx>=0.25.0",
                "requests>=2.31.0"
            ]
            
            print("📦 Installing core packages individually...")
            for package in core_packages:
                print(f"Installing {package}...")
                result = run_command([
                    sys.executable, "-m", "pip", "install", 
                    "--prefer-binary", package
                ], check=False)
                
                if result.returncode != 0:
                    print(f"⚠️  Failed to install {package}, continuing...")
        
        # Try without build dependencies for problematic packages
        print("📦 Trying installation without build isolation...")
        result = run_command([
            sys.executable, "-m", "pip", "install",
            "--no-build-isolation",
            "--prefer-binary", 
            "-r", requirements_file
        ], check=False)
    
    if result.returncode == 0:
        print("✅ Dependencies installed successfully!")
        return True
    else:
        print("❌ Some dependencies failed to install")
        print("💡 You may need to install missing dependencies manually")
        return False

def verify_installation():
    """Verify that core dependencies are installed"""
    core_imports = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "sqlalchemy",
        "aiosqlite"
    ]
    
    print("🔍 Verifying core dependencies...")
    failed = []
    
    for package in core_imports:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            failed.append(package)
    
    if failed:
        print(f"\n⚠️  Failed to import: {', '.join(failed)}")
        print("💡 Try installing manually:")
        for package in failed:
            print(f"   pip install {package}")
        return False
    else:
        print("✅ All core dependencies verified!")
        return True

def main():
    print("🚀 AITM Backend Dependency Installer")
    print("===================================")
    
    # Check Python version
    mode = check_python_version()
    if not mode:
        sys.exit(1)
    
    # Install dependencies
    success = install_dependencies(mode)
    
    # Verify installation
    if success:
        verify_installation()
    
    print("\n🎯 Installation complete!")
    print("💡 If there were errors, check the output above for manual installation steps")

if __name__ == "__main__":
    main()
