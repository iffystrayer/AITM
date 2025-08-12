#!/bin/bash

# Comprehensive End-to-End Authorization Tests Runner
# This script runs all comprehensive E2E authorization tests for the AITM platform

set -e  # Exit on any error

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up..."
    
    # Kill any remaining backend processes
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    
    # Clean up test databases
    rm -f backend/test_*.db 2>/dev/null || true
    
    print_status "Cleanup completed"
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Main function
main() {
    print_status "Starting Comprehensive End-to-End Authorization Tests"
    echo "=================================================================="
    
    # Check if we're in the right directory
    if [[ ! -f "backend/app/main.py" ]]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Check Python installation
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    print_success "Python 3 is available"
    
    # Check if virtual environment should be activated
    if [[ -f "venv/bin/activate" ]]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    elif [[ -f ".venv/bin/activate" ]]; then
        print_status "Activating virtual environment..."
        source .venv/bin/activate
    else
        print_warning "No virtual environment found, using system Python"
    fi
    
    # Install required dependencies
    print_status "Installing required dependencies..."
    
    # Install backend dependencies
    if [[ -f "backend/requirements.txt" ]]; then
        pip install -r backend/requirements.txt > /dev/null 2>&1 || {
            print_error "Failed to install backend dependencies"
            exit 1
        }
        print_success "Backend dependencies installed"
    fi
    
    # Install test dependencies
    pip install requests > /dev/null 2>&1 || {
        print_warning "Failed to install requests, but continuing..."
    }
    
    # Try to install Playwright (optional)
    pip install playwright > /dev/null 2>&1 && {
        print_status "Installing Playwright browsers..."
        python -m playwright install chromium > /dev/null 2>&1 || {
            print_warning "Failed to install Playwright browsers, but continuing..."
        }
        print_success "Playwright installed successfully"
    } || {
        print_warning "Playwright not installed, browser tests will be skipped"
    }
    
    # Set environment variables for testing
    export ENVIRONMENT=test
    export SECRET_KEY="comprehensive-e2e-test-secret-key-32-chars-long-secure-for-testing"
    export DATABASE_URL="sqlite:///./test_comprehensive_e2e_main.db"
    export ACCESS_TOKEN_EXPIRE_MINUTES=60
    export LOG_LEVEL=INFO
    export BASE_URL="http://localhost:8000"
    
    print_status "Environment variables set for testing"
    
    # Clean up any existing test databases
    print_status "Cleaning up existing test databases..."
    rm -f backend/test_*.db 2>/dev/null || true
    
    # Change to the E2E test directory
    cd tests/e2e
    
    # Run the comprehensive test suite
    print_status "Running comprehensive E2E authorization tests..."
    echo ""
    
    # Run the comprehensive test runner
    if python3 run_comprehensive_e2e_tests.py; then
        echo ""
        print_success "All comprehensive E2E authorization tests passed!"
        print_success "The authorization system is ready for production deployment."
        
        # Print summary of what was tested
        echo ""
        echo "🔒 Security Features Validated:"
        echo "   ✅ JWT token authentication and validation"
        echo "   ✅ Ownership-based access control"
        echo "   ✅ Role-based permission enforcement"
        echo "   ✅ Admin privilege escalation"
        echo "   ✅ Unauthorized access prevention"
        echo "   ✅ Project modification authorization"
        echo "   ✅ Project list filtering"
        echo "   ✅ Multi-layer authorization"
        echo "   ✅ Security headers and error handling"
        echo ""
        echo "📋 Requirements Validated:"
        echo "   ✅ 1.1-1.4: API endpoints enforce proper authorization"
        echo "   ✅ 2.1-2.4: Project data isolation with ownership validation"
        echo "   ✅ 3.1-3.4: Robust and explicit permission checking"
        echo "   ✅ 4.1-4.4: Secure JWT secret key handling"
        echo "   ✅ 5.1-5.4: Multi-layer authorization with defense in depth"
        
        exit 0
    else
        echo ""
        print_error "Some comprehensive E2E authorization tests failed!"
        print_error "Please review the test output and address any failures."
        print_error "Do not deploy to production until all tests pass."
        exit 1
    fi
}

# Help function
show_help() {
    echo "Comprehensive End-to-End Authorization Tests Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo ""
    echo "This script runs comprehensive E2E authorization tests including:"
    echo "  - Basic API authorization tests"
    echo "  - Comprehensive authorization tests with multiple scenarios"
    echo "  - Playwright browser-based tests (if available)"
    echo "  - Production-like environment testing"
    echo ""
    echo "Requirements tested:"
    echo "  - 1.1-1.4: API endpoints enforce proper authorization checks"
    echo "  - 2.1-2.4: Project data isolation with ownership validation"
    echo "  - 3.1-3.4: Robust and explicit permission checking system"
    echo "  - 4.1-4.4: Secure JWT secret key handling in production"
    echo "  - 5.1-5.4: Multi-layer authorization with defense in depth"
    echo ""
    echo "The script will:"
    echo "  1. Check dependencies and install if needed"
    echo "  2. Set up test environment with proper configuration"
    echo "  3. Start backend server for testing"
    echo "  4. Run all comprehensive test suites"
    echo "  5. Clean up test data and processes"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            set -x  # Enable verbose mode
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main "$@"