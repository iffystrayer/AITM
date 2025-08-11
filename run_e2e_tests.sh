#!/bin/bash

# End-to-End Authorization Tests Runner
# This script sets up the environment and runs comprehensive E2E tests

set -e  # Exit on any error

echo "🚀 AITM API Authorization - End-to-End Test Suite"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

print_status "Python 3 found: $(python3 --version)"

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create and activate virtual environment
print_status "Setting up virtual environment for E2E tests..."
if [ ! -d "venv_e2e" ]; then
    python3 -m venv venv_e2e
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv_e2e/bin/activate
print_success "Virtual environment activated"

# Install E2E test requirements
print_status "Installing E2E test requirements..."
if [ -f "tests/e2e/requirements.txt" ]; then
    pip install -r tests/e2e/requirements.txt
    print_success "E2E test requirements installed"
else
    print_warning "E2E requirements file not found, installing basic requirements..."
    pip install playwright requests
fi

# Install Playwright browsers
print_status "Installing Playwright browsers..."
python -m playwright install chromium
print_success "Playwright browsers installed"

# Set environment variables for testing
export ENVIRONMENT=test
export SECRET_KEY=test-secret-key-for-e2e-tests-only-do-not-use-in-production
export DATABASE_URL=sqlite:///./test_e2e.db
export ACCESS_TOKEN_EXPIRE_MINUTES=60
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

print_status "Environment configured for testing"

# Run the E2E tests
print_status "Starting End-to-End Authorization Tests..."
echo ""

cd tests/e2e
python run_e2e_tests.py

# Capture exit code
EXIT_CODE=$?

# Clean up
print_status "Cleaning up test environment..."
if [ -f "../../backend/test_e2e.db" ]; then
    rm -f "../../backend/test_e2e.db"
    print_status "Test database cleaned up"
fi

# Deactivate virtual environment
deactivate 2>/dev/null || true

# Print final results
echo ""
echo "=================================================="
if [ $EXIT_CODE -eq 0 ]; then
    print_success "🎉 All End-to-End Authorization Tests Passed!"
    print_success "The API authorization system is working correctly."
    echo ""
    echo "✅ Verified Security Features:"
    echo "   • Ownership-based access control"
    echo "   • Admin privilege escalation"
    echo "   • Unauthorized access prevention"
    echo "   • Authentication requirement enforcement"
    echo "   • Project modification authorization"
    echo "   • Analysis endpoint security"
    echo "   • Project list filtering"
    echo ""
    echo "✅ Requirements Validated:"
    echo "   • 1.1-1.4: API endpoints enforce proper authorization"
    echo "   • 2.1-2.4: Project data isolation with ownership validation"
    echo "   • 3.1-3.4: Robust permission checking system"
    echo "   • 5.1-5.4: Multi-layer authorization implementation"
else
    print_error "❌ Some End-to-End Authorization Tests Failed!"
    print_error "Please review the test output above for details."
    echo ""
    echo "🔍 Common issues to check:"
    echo "   • Backend server startup problems"
    echo "   • Database connection issues"
    echo "   • Authentication/JWT token problems"
    echo "   • Permission logic errors"
    echo "   • Network connectivity issues"
fi

echo "=================================================="
exit $EXIT_CODE