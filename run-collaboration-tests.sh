#!/bin/bash

# 🤝 AITM Collaboration E2E Test Runner
# This script helps run the collaboration feature tests with proper setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (Docker ports)
BACKEND_PORT=38527
FRONTEND_PORT=59000
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"
FRONTEND_URL="http://127.0.0.1:${FRONTEND_PORT}"

echo -e "${BLUE}🤝 AITM Collaboration E2E Test Runner${NC}"
echo "=================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    
    if lsof -i :$port >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service is NOT running on port $port${NC}"
        return 1
    fi
}

# Function to check service health
check_health() {
    local url=$1
    local service=$2
    
    if curl -s -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service health check passed${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ $service health check failed (might be expected)${NC}"
        return 1
    fi
}

# Pre-flight checks
echo -e "${BLUE}🔍 Pre-flight checks...${NC}"

# Check if backend is running
if check_port $BACKEND_PORT "Backend"; then
    # Try health check
    check_health "$BACKEND_URL/health" "Backend"
else
    echo -e "${YELLOW}💡 To start backend: cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port $BACKEND_PORT${NC}"
fi

# Check if frontend is running  
if check_port $FRONTEND_PORT "Frontend"; then
    # Try health check
    check_health "$FRONTEND_URL" "Frontend"
else
    echo -e "${YELLOW}💡 To start frontend: cd frontend && npm run dev -- --port $FRONTEND_PORT${NC}"
fi

# Check database
echo -e "${BLUE}🗄️ Checking database...${NC}"
if [ -f "backend/aitm_database.db" ]; then
    echo -e "${GREEN}✅ Database file exists${NC}"
    
    # Check if collaboration tables exist
    if sqlite3 backend/aitm_database.db ".tables" | grep -q "teams"; then
        echo -e "${GREEN}✅ Collaboration tables found${NC}"
    else
        echo -e "${YELLOW}⚠️ Collaboration tables not found${NC}"
        echo -e "${YELLOW}💡 To migrate: cd backend && python -m app.database.migrate_collaboration${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Database file not found${NC}"
fi

echo ""

# Parse command line arguments
HEADED=""
BROWSER=""
GREP=""
REPORTER=""
TRACE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --headed)
            HEADED="--headed"
            shift
            ;;
        --browser=*)
            BROWSER="--project=${1#*=}"
            shift
            ;;
        --grep=*)
            GREP="--grep=${1#*=}"
            shift
            ;;
        --reporter=*)
            REPORTER="--reporter=${1#*=}"
            shift
            ;;
        --trace)
            TRACE="--trace=on"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --headed           Run tests in headed mode (visible browser)"
            echo "  --browser=NAME     Run tests on specific browser (chromium, firefox, webkit)"
            echo "  --grep=PATTERN     Run tests matching pattern"
            echo "  --reporter=TYPE    Use specific reporter (html, json, line)"
            echo "  --trace            Enable tracing for debugging"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run all collaboration tests"
            echo "  $0 --headed                          # Run with visible browser"
            echo "  $0 --browser=chromium                # Run only on Chrome"
            echo "  $0 --grep=\"Team Management\"          # Run only team tests"
            echo "  $0 --reporter=html                   # Generate HTML report"
            echo "  $0 --trace --headed                  # Debug mode with tracing"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build test command
TEST_CMD="npx playwright test 08-collaboration-features.spec.ts"

if [ -n "$HEADED" ]; then
    TEST_CMD="$TEST_CMD $HEADED"
fi

if [ -n "$BROWSER" ]; then
    TEST_CMD="$TEST_CMD $BROWSER"
fi

if [ -n "$GREP" ]; then
    TEST_CMD="$TEST_CMD $GREP"
fi

if [ -n "$REPORTER" ]; then
    TEST_CMD="$TEST_CMD $REPORTER"
fi

if [ -n "$TRACE" ]; then
    TEST_CMD="$TEST_CMD $TRACE"
fi

# Create screenshots directory if it doesn't exist
mkdir -p frontend/screenshots

# Run the tests
echo -e "${BLUE}🚀 Running collaboration E2E tests...${NC}"
echo -e "${YELLOW}Command: $TEST_CMD${NC}"
echo ""

cd frontend

if eval $TEST_CMD; then
    echo ""
    echo -e "${GREEN}🎉 All collaboration tests passed!${NC}"
    
    # Show generated artifacts
    echo -e "${BLUE}📁 Generated artifacts:${NC}"
    if [ -d "screenshots" ] && [ "$(ls screenshots/collaboration-* 2>/dev/null)" ]; then
        echo -e "${GREEN}📷 Screenshots: $(ls screenshots/collaboration-* | wc -l) files${NC}"
        ls screenshots/collaboration-* | head -5
    fi
    
    if [ -d "playwright-report" ]; then
        echo -e "${GREEN}📊 Test report: playwright-report/index.html${NC}"
    fi
    
    if [ -d "test-results" ]; then
        echo -e "${GREEN}🔍 Test traces: Available in test-results/${NC}"
    fi
    
else
    echo ""
    echo -e "${RED}❌ Some collaboration tests failed${NC}"
    echo -e "${YELLOW}💡 Check the output above for details${NC}"
    echo -e "${YELLOW}💡 Use --headed flag to see tests running in browser${NC}"
    echo -e "${YELLOW}💡 Use --trace flag to enable debugging traces${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "• Review test screenshots in frontend/screenshots/"
echo -e "• Open HTML report: frontend/playwright-report/index.html"
echo -e "• Check console output for API integration results"
echo -e "• Consider adding more specific collaboration UI tests"
