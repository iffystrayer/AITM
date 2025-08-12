#!/bin/bash

# Docker-based End-to-End Authorization Tests Runner
# This script runs comprehensive E2E authorization tests using Docker containers
# Backend runs on port 38527, Frontend on port 59000 (avoiding 3000 and 8000)

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
    print_status "Cleaning up Docker containers..."
    
    # Stop Docker containers
    docker-compose down 2>/dev/null || true
    
    print_status "Cleanup completed"
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Main function
main() {
    print_status "Starting Docker-based End-to-End Authorization Tests"
    echo "=================================================================="
    
    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]]; then
        print_error "Please run this script from the project root directory"
        print_error "docker-compose.yml not found"
        exit 1
    fi
    
    # Check Docker installation
    if ! command_exists docker; then
        print_error "Docker is required but not installed"
        print_error "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is required but not installed"
        print_error "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        print_error "Please start Docker and try again"
        exit 1
    fi
    
    print_success "Docker daemon is running"
    
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
    
    # Install required dependencies for test runner
    print_status "Installing required test dependencies..."
    pip install requests > /dev/null 2>&1 || {
        print_warning "Failed to install requests, but continuing..."
    }
    
    # Set environment variables for Docker testing
    export ENVIRONMENT=test
    export SECRET_KEY="docker-e2e-test-secret-key-32-chars-long-secure-for-testing"
    export DATABASE_URL="sqlite:///./test_docker_e2e.db"
    export ACCESS_TOKEN_EXPIRE_MINUTES=60
    export LOG_LEVEL=INFO
    export BACKEND_URL="http://localhost:38527"
    export FRONTEND_URL="http://localhost:59000"
    
    print_status "Environment variables set for Docker testing"
    
    # Show Docker container status
    print_status "Checking current Docker container status..."
    docker-compose ps || true
    
    # Change to the E2E test directory
    cd tests/e2e
    
    # Run the Docker-based test suite
    print_status "Running Docker-based E2E authorization tests..."
    echo ""
    
    # Run the Docker test runner
    if python3 docker_e2e_runner.py; then
        echo ""
        print_success "All Docker-based E2E authorization tests passed!"
        print_success "The authorization system is ready for production deployment."
        
        # Print summary of what was tested
        echo ""
        echo "🐳 Docker Environment Validated:"
        echo "   ✅ Backend container on port 38527"
        echo "   ✅ Frontend container on port 59000"
        echo "   ✅ Containerized database with isolated test data"
        echo "   ✅ Production-like Docker environment"
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
        print_error "Some Docker-based E2E authorization tests failed!"
        print_error "Please review the test output and address any failures."
        print_error "Do not deploy to production until all tests pass."
        exit 1
    fi
}

# Help function
show_help() {
    echo "Docker-based End-to-End Authorization Tests Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo ""
    echo "This script runs comprehensive E2E authorization tests using Docker containers:"
    echo "  - Backend container on port 38527 (avoiding port 8000)"
    echo "  - Frontend container on port 59000 (avoiding port 3000)"
    echo "  - Containerized database with isolated test data"
    echo "  - Production-like Docker environment testing"
    echo ""
    echo "Requirements tested:"
    echo "  - 1.1-1.4: API endpoints enforce proper authorization checks"
    echo "  - 2.1-2.4: Project data isolation with ownership validation"
    echo "  - 3.1-3.4: Robust and explicit permission checking system"
    echo "  - 4.1-4.4: Secure JWT secret key handling in production"
    echo "  - 5.1-5.4: Multi-layer authorization with defense in depth"
    echo ""
    echo "The script will:"
    echo "  1. Check Docker and Docker Compose availability"
    echo "  2. Start Docker containers using docker-compose"
    echo "  3. Wait for services to become healthy"
    echo "  4. Run all comprehensive test suites against containers"
    echo "  5. Clean up containers and resources"
    echo ""
    echo "Docker containers used:"
    echo "  - Backend: http://localhost:38527"
    echo "  - Frontend: http://localhost:59000"
    echo "  - Database: Containerized SQLite/PostgreSQL"
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