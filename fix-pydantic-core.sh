#!/bin/bash

echo "🔧 AITM Pydantic-Core Build Error Fix"
echo "====================================="

echo "🐍 Python version:"
python3 --version

echo ""
echo "📦 Fixing pydantic-core build issues..."

# Navigate to backend directory
cd backend

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run ./start-dev.sh first"
    exit 1
fi

# Upgrade build tools first
echo "🔧 Upgrading build tools..."
pip install --upgrade pip setuptools wheel

# Try installing just the core dependencies that work
echo "📦 Installing core dependencies individually..."

# Essential FastAPI stack
pip install --prefer-binary "fastapi>=0.108.0"
pip install --prefer-binary "uvicorn[standard]>=0.25.0"

# Try pydantic with specific version
echo "📦 Installing pydantic with compatible version..."
pip install --prefer-binary "pydantic>=2.8.2" || {
    echo "⚠️  Pydantic failed, trying alternative approach..."
    pip install --prefer-binary --no-build-isolation "pydantic>=2.5.0"
}

# Database essentials
pip install --prefer-binary "sqlalchemy>=2.0.23"
pip install --prefer-binary "aiosqlite>=0.19.0"

# Essential utilities
pip install --prefer-binary "httpx>=0.25.0"
pip install --prefer-binary "requests>=2.31.0"
pip install --prefer-binary "python-dotenv>=1.0.0"
pip install --prefer-binary "aiofiles>=23.2.1"

echo ""
echo "🔍 Testing imports..."

python3 -c "
import sys
packages = ['fastapi', 'uvicorn', 'pydantic', 'sqlalchemy', 'aiosqlite', 'httpx', 'requests']
failed = []

for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError as e:
        print(f'❌ {pkg}: {e}')
        failed.append(pkg)

if failed:
    print(f'\n⚠️  Failed imports: {failed}')
    print('💡 Try installing these manually:')
    for pkg in failed:
        print(f'   pip install --prefer-binary {pkg}')
else:
    print('\n🎉 All core dependencies working!')
"

echo ""
echo "💡 If you still have issues:"
echo "   1. Try using Python 3.11 or 3.12 instead of 3.13"
echo "   2. Install Rust compiler: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
echo "   3. Use the simplified requirements: backend/requirements-py313.txt"
echo ""
echo "🎯 To continue setup: ./start-dev.sh"
