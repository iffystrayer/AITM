#!/bin/bash

echo "🔍 AITM MVP Setup Validation"
echo "=============================="

# Check Python version
echo ""
echo "1️⃣ Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python found: $PYTHON_VERSION"
else
    echo "❌ Python3 not found"
    exit 1
fi

# Check Node.js version
echo ""
echo "2️⃣ Checking Node.js environment..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js found: $NODE_VERSION"
else
    echo "❌ Node.js not found"
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ NPM found: $NPM_VERSION"
else
    echo "❌ NPM not found"
    exit 1
fi

# Check backend structure
echo ""
echo "3️⃣ Validating backend structure..."
REQUIRED_BACKEND_FILES=(
    "backend/requirements.txt"
    "backend/app/main.py"
    "backend/app/core/config.py"
    "backend/app/core/database.py"
    "backend/app/services/llm_service.py"
    "backend/app/agents/base_agent.py"
)

for file in "${REQUIRED_BACKEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Check frontend structure
echo ""
echo "4️⃣ Validating frontend structure..."
REQUIRED_FRONTEND_FILES=(
    "frontend/package.json"
    "frontend/svelte.config.js"
    "frontend/vite.config.ts"
    "frontend/src/app.html"
    "frontend/src/routes/+layout.svelte"
    "frontend/src/routes/+page.svelte"
)

for file in "${REQUIRED_FRONTEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Check configuration files
echo ""
echo "5️⃣ Validating configuration..."
if [ -f ".env.example" ]; then
    echo "✅ .env.example exists"
else
    echo "❌ .env.example missing"
    exit 1
fi

if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml exists"
else
    echo "❌ docker-compose.yml missing"
    exit 1
fi

if [ -f "start-dev.sh" ]; then
    echo "✅ start-dev.sh exists"
    if [ -x "start-dev.sh" ]; then
        echo "✅ start-dev.sh is executable"
    else
        echo "⚠️  start-dev.sh is not executable (run: chmod +x start-dev.sh)"
    fi
else
    echo "❌ start-dev.sh missing"
    exit 1
fi

# Validate backend requirements
echo ""
echo "6️⃣ Checking backend requirements..."
if grep -q "fastapi" backend/requirements.txt; then
    echo "✅ FastAPI found in requirements"
else
    echo "❌ FastAPI not found in requirements"
    exit 1
fi

if grep -q "aiosqlite" backend/requirements.txt; then
    echo "✅ aiosqlite found in requirements (sqlite3 issue fixed)"
else
    echo "❌ aiosqlite not found in requirements"
    exit 1
fi

if ! grep -q "sqlite3" backend/requirements.txt; then
    echo "✅ sqlite3 not in requirements (built into Python)"
else
    echo "⚠️  sqlite3 found in requirements (should be removed)"
fi

# Validate frontend dependencies
echo ""
echo "7️⃣ Checking frontend dependencies..."
if [ -d "frontend/node_modules" ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "⚠️  Frontend dependencies not installed (run: cd frontend && npm install)"
fi

# Check port configuration
echo ""
echo "8️⃣ Validating port configuration..."
if grep -q "38527" .env.example && grep -q "41241" .env.example; then
    echo "✅ Unique 5-digit ports configured (38527, 41241)"
else
    echo "❌ Port configuration issue"
    exit 1
fi

# Check for actual port usage (not comments)
if grep -v "^#" .env.example docker-compose.yml 2>/dev/null | grep -q "3000\|8000"; then
    echo "❌ Found problematic ports 3000 or 8000 in configuration"
    exit 1
else
    echo "✅ Avoided problematic ports 3000 and 8000"
fi

echo ""
echo "🎉 All validations passed!"
echo ""
echo "📋 Next steps:"
echo "1. Copy environment template: cp .env.example .env"
echo "2. Add your LLM API keys to .env file"
echo "3. Start development: ./start-dev.sh"
echo ""
echo "🌐 Expected endpoints:"
echo "   Frontend: http://127.0.0.1:41241"
echo "   Backend:  http://127.0.0.1:38527"
echo "   API Docs: http://127.0.0.1:38527/docs"
