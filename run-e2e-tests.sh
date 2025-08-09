#!/bin/bash

# AITM End-to-End Test Runner
# This script starts the system and runs comprehensive E2E tests

set -e  # Exit on any error

echo "🚀 AITM End-to-End Test Runner"
echo "=============================="

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

# Check if required dependencies are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Check if system is already running
check_system_status() {
    print_status "Checking system status..."
    
    # Check if backend is running
    if curl -s http://127.0.0.1:38527/health > /dev/null 2>&1; then
        print_success "Backend is already running on port 38527"
        BACKEND_RUNNING=true
    else
        print_warning "Backend is not running"
        BACKEND_RUNNING=false
    fi
    
    # Check if frontend is running
    if curl -s http://127.0.0.1:41241 > /dev/null 2>&1; then
        print_success "Frontend is already running on port 41241"
        FRONTEND_RUNNING=true
    else
        print_warning "Frontend is not running"
        FRONTEND_RUNNING=false
    fi
}

# Start the system if not running
start_system() {
    if [ "$BACKEND_RUNNING" = false ] || [ "$FRONTEND_RUNNING" = false ]; then
        print_status "Starting AITM system..."
        
        # Check if docker-compose file exists
        if [ ! -f "docker-compose.yml" ]; then
            print_error "docker-compose.yml not found. Please run this script from the project root directory."
            exit 1
        fi
        
        # Start the system
        docker-compose up -d --build
        
        print_status "Waiting for services to be ready..."
        
        # Wait for backend to be healthy
        MAX_ATTEMPTS=30
        ATTEMPT=0
        while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
            if curl -s http://127.0.0.1:38527/health | grep -q "healthy"; then
                print_success "Backend is healthy"
                break
            fi
            
            ATTEMPT=$((ATTEMPT + 1))
            echo "Waiting for backend... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
            sleep 2
        done
        
        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            print_error "Backend failed to become healthy within timeout"
            exit 1
        fi
        
        # Wait for frontend to be ready
        ATTEMPT=0
        while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
            if curl -s http://127.0.0.1:41241 > /dev/null 2>&1; then
                print_success "Frontend is ready"
                break
            fi
            
            ATTEMPT=$((ATTEMPT + 1))
            echo "Waiting for frontend... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
            sleep 2
        done
        
        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            print_error "Frontend failed to become ready within timeout"
            exit 1
        fi
        
        print_success "AITM system is running successfully"
    else
        print_success "AITM system is already running"
    fi
}

# Install Playwright if needed
install_playwright() {
    print_status "Checking Playwright installation..."
    
    cd frontend
    
    if [ ! -d "node_modules/@playwright" ]; then
        print_status "Installing Playwright..."
        npm install
        npx playwright install
    else
        print_success "Playwright is already installed"
    fi
    
    cd ..
}

# Run E2E tests
run_tests() {
    print_status "Running End-to-End Tests..."
    
    cd frontend
    
    # Parse test type argument
    case "$1" in
        "smoke")
            print_status "Running smoke tests only..."
            npm run test:e2e:smoke
            ;;
        "projects")
            print_status "Running project management tests..."
            npm run test:e2e:projects
            ;;
        "analysis")
            print_status "Running threat analysis tests..."
            npm run test:e2e:analysis
            ;;
        "api")
            print_status "Running API integration tests..."
            npm run test:e2e:api
            ;;
        "ui")
            print_status "Running tests in UI mode..."
            npm run test:e2e:ui
            ;;
        "debug")
            print_status "Running tests in debug mode..."
            npm run test:e2e:debug
            ;;
        "headed")
            print_status "Running tests in headed mode..."
            npm run test:e2e:headed
            ;;
        *)
            print_status "Running all E2E tests..."
            npm run test:e2e
            ;;
    esac
    
    cd ..
}

# Show system logs if tests fail
show_logs() {
    if [ $? -ne 0 ]; then
        print_error "Tests failed. Showing system logs..."
        echo ""
        print_status "Backend logs:"
        docker-compose logs backend --tail=50
        echo ""
        print_status "Frontend logs:"
        docker-compose logs frontend --tail=50
    fi
}

# Cleanup function
cleanup() {
    if [ "$CLEANUP_ON_EXIT" = true ]; then
        print_status "Cleaning up..."
        docker-compose down
    fi
}

# Main execution
main() {
    echo ""
    print_status "Starting AITM E2E Test Suite"
    echo ""
    
    # Parse arguments
    TEST_TYPE="all"
    CLEANUP_ON_EXIT=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --test-type)
                TEST_TYPE="$2"
                shift 2
                ;;
            --cleanup)
                CLEANUP_ON_EXIT=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --test-type TYPE    Type of tests to run (all, smoke, projects, analysis, api, ui, debug, headed)"
                echo "  --cleanup           Stop services after tests complete"
                echo "  --help             Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                              # Run all tests"
                echo "  $0 --test-type smoke            # Run only smoke tests"
                echo "  $0 --test-type projects --cleanup # Run project tests and cleanup"
                echo "  $0 --test-type ui               # Run tests in interactive UI mode"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Set trap for cleanup
    trap cleanup EXIT
    trap show_logs ERR
    
    # Execute test pipeline
    check_dependencies
    check_system_status
    start_system
    install_playwright
    run_tests "$TEST_TYPE"
    
    print_success "All E2E tests completed successfully! 🎉"
    echo ""
    print_status "System is still running at:"
    echo "  Frontend: http://127.0.0.1:41241"
    echo "  Backend:  http://127.0.0.1:38527"
    echo "  API Docs: http://127.0.0.1:38527/docs"
    echo ""
    
    if [ "$CLEANUP_ON_EXIT" = true ]; then
        print_status "Stopping services as requested..."
        docker-compose down
        print_success "Services stopped"
    else
        print_status "Use 'docker-compose down' to stop the services when done"
    fi
}

# Run main function with all arguments
main "$@"
