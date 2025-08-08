#!/bin/bash

# AITM Development Startup Script
echo "🚀 Starting AITM Development Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running the application"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/data
mkdir -p backend/tests
mkdir -p frontend/src/{components,stores,utils,routes}

# Start backend in background
echo "🔧 Starting Backend (Port 38527)..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing backend dependencies..."
pip install -r requirements.txt

# Start backend server
echo "🚀 Starting backend server on port 38527..."
cd app && python main.py &
BACKEND_PID=$!
cd ..

# Go back to root and start frontend
cd ../frontend

echo "🎨 Starting Frontend (Port 41241)..."

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend server
echo "🚀 Starting frontend server on port 41241..."
npm run dev &
FRONTEND_PID=$!

# Wait for servers to start
echo "⏳ Waiting for servers to start..."
sleep 5

echo "✅ AITM Development Environment is ready!"
echo ""
echo "🌟 Access your application:"
echo "  🔗 Frontend: http://127.0.0.1:41241"
echo "  🔗 Backend API: http://127.0.0.1:38527"
echo "  📚 API Docs: http://127.0.0.1:38527/docs"
echo ""
echo "🛑 To stop the servers, press Ctrl+C"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Wait for processes
wait
