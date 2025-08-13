#!/bin/bash

# Production Deployment Validation Script
# This script validates a production deployment of the AITM system

set -e  # Exit on any error

# Configuration
DOMAIN="${DOMAIN:-localhost}"
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-80}"
TIMEOUT=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validation functions
validate_docker_services() {
    log_info "Validating Docker services..."
    
    local services=("aitm-backend-prod" "aitm-frontend-prod" "aitm-postgres-prod" "aitm-redis-prod")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$service"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "no-healthcheck")
            if [[ "$status" == "healthy" ]] || [[ "$status" == "no-healthcheck" ]]; then
                log_success "Service $service is running"
            else
                log_error "Service $service is unhealthy (status: $status)"
                failed_services+=("$service")
            fi
        else
            log_error "Service $service is not running"
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "Failed services: ${failed_services[*]}"
        return 1
    fi
    
    log_success "All Docker services are running"
    return 0
}

validate_health_endpoints() {
    log_info "Validating health check endpoints..."
    
    local endpoints=(
        "http://${DOMAIN}:${API_PORT}/api/v1/health"
        "http://${DOMAIN}:${API_PORT}/api/v1/health/detailed"
        "http://${DOMAIN}:${API_PORT}/health"
    )
    
    local failed_endpoints=()
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s --max-time $TIMEOUT "$endpoint" > /dev/null; then
            log_success "Health endpoint $endpoint is responding"
        else
            log_error "Health endpoint $endpoint is not responding"
            failed_endpoints+=("$endpoint")
        fi
    done
    
    if [[ ${#failed_endpoints[@]} -gt 0 ]]; then
        log_error "Failed health endpoints: ${failed_endpoints[*]}"
        return 1
    fi
    
    log_success "All health endpoints are responding"
    return 0
}

validate_https_ssl() {
    log_info "Validating HTTPS and SSL configuration..."
    
    if [[ "$DOMAIN" == "localhost" ]]; then
        log_warning "Skipping SSL validation for localhost"
        return 0
    fi
    
    # Check if HTTPS endpoint is accessible
    if curl -f -s --max-time $TIMEOUT "https://${DOMAIN}/api/v1/health" > /dev/null; then
        log_success "HTTPS endpoint is accessible"
    else
        log_error "HTTPS endpoint is not accessible"
        return 1
    fi
    
    # Check SSL certificate validity
    local cert_info=$(echo | openssl s_client -servername "$DOMAIN" -connect "${DOMAIN}:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    if [[ $? -eq 0 ]]; then
        log_success "SSL certificate is valid"
        log_info "Certificate info: $cert_info"
    else
        log_error "SSL certificate validation failed"
        return 1
    fi
    
    return 0
}

validate_database_connectivity() {
    log_info "Validating database connectivity..."
    
    # Test database connectivity through the application
    local health_response=$(curl -f -s --max-time $TIMEOUT "http://${DOMAIN}:${API_PORT}/api/v1/health/detailed")
    if [[ $? -eq 0 ]]; then
        local db_status=$(echo "$health_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('components', {}).get('database', 'unknown'))
except:
    print('parse_error')
")
        
        if [[ "$db_status" == "healthy" ]]; then
            log_success "Database connectivity is healthy"
        else
            log_error "Database connectivity issue: $db_status"
            return 1
        fi
    else
        log_error "Could not retrieve database status"
        return 1
    fi
    
    return 0
}

validate_authentication_system() {
    log_info "Validating authentication system..."
    
    # Test authentication endpoint accessibility
    local auth_endpoint="http://${DOMAIN}:${API_PORT}/api/v1/auth/login"
    local response=$(curl -s -w "%{http_code}" -X POST "$auth_endpoint" \
        -H "Content-Type: application/json" \
        -d '{"username":"invalid","password":"invalid"}' \
        --max-time $TIMEOUT)
    
    local http_code="${response: -3}"
    
    if [[ "$http_code" == "401" ]] || [[ "$http_code" == "422" ]]; then
        log_success "Authentication endpoint is responding correctly"
    else
        log_error "Authentication endpoint returned unexpected status: $http_code"
        return 1
    fi
    
    return 0
}

validate_security_headers() {
    log_info "Validating security headers..."
    
    local endpoint="http://${DOMAIN}:${API_PORT}/api/v1/health"
    local headers=$(curl -s -I --max-time $TIMEOUT "$endpoint")
    
    local required_headers=(
        "X-Content-Type-Options"
        "X-Frame-Options"
        "X-XSS-Protection"
    )
    
    local missing_headers=()
    
    for header in "${required_headers[@]}"; do
        if echo "$headers" | grep -qi "$header"; then
            log_success "Security header $header is present"
        else
            log_warning "Security header $header is missing"
            missing_headers+=("$header")
        fi
    done
    
    if [[ ${#missing_headers[@]} -gt 0 ]]; then
        log_warning "Missing security headers: ${missing_headers[*]}"
        # Don't fail for missing headers, just warn
    fi
    
    return 0
}

validate_monitoring_services() {
    log_info "Validating monitoring services..."
    
    local monitoring_services=(
        "aitm-prometheus-prod:9090"
        "aitm-grafana-prod:3000"
        "aitm-loki-prod:3100"
    )
    
    local failed_services=()
    
    for service_port in "${monitoring_services[@]}"; do
        local service_name=$(echo "$service_port" | cut -d':' -f1)
        local port=$(echo "$service_port" | cut -d':' -f2)
        
        if docker ps --format "table {{.Names}}" | grep -q "$service_name"; then
            log_success "Monitoring service $service_name is running"
            
            # Test service endpoint if accessible
            if curl -f -s --max-time 5 "http://localhost:$port" > /dev/null 2>&1; then
                log_success "Monitoring service $service_name is accessible on port $port"
            else
                log_warning "Monitoring service $service_name is not accessible on port $port"
            fi
        else
            log_warning "Monitoring service $service_name is not running"
            failed_services+=("$service_name")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_warning "Some monitoring services are not running: ${failed_services[*]}"
        # Don't fail for monitoring services, just warn
    fi
    
    return 0
}

validate_performance() {
    log_info "Validating performance..."
    
    local endpoint="http://${DOMAIN}:${API_PORT}/api/v1/health"
    local response_time=$(curl -o /dev/null -s -w "%{time_total}" --max-time $TIMEOUT "$endpoint")
    
    # Convert to milliseconds for easier comparison
    local response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d'.' -f1)
    
    if [[ $response_time_ms -lt 2000 ]]; then
        log_success "Response time is acceptable: ${response_time_ms}ms"
    else
        log_warning "Response time is slow: ${response_time_ms}ms (>2000ms)"
    fi
    
    return 0
}

validate_logs() {
    log_info "Validating log output..."
    
    local services=("aitm-backend-prod" "aitm-frontend-prod")
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$service"; then
            local log_output=$(docker logs --tail 10 "$service" 2>&1)
            if echo "$log_output" | grep -qi "error\|exception\|failed"; then
                log_warning "Service $service has recent errors in logs"
                echo "$log_output" | tail -5
            else
                log_success "Service $service logs look healthy"
            fi
        fi
    done
    
    return 0
}

run_security_validation() {
    log_info "Running security configuration validation..."
    
    if [[ -f "validate_production_security.py" ]]; then
        if python3 validate_production_security.py --env-file .env.prod --quiet; then
            log_success "Security configuration validation passed"
        else
            log_error "Security configuration validation failed"
            return 1
        fi
    else
        log_warning "Security validation script not found"
    fi
    
    return 0
}

run_monitoring_validation() {
    log_info "Running monitoring setup validation..."
    
    if [[ -f "validate_monitoring_setup.py" ]]; then
        if python3 validate_monitoring_setup.py --base-url "http://${DOMAIN}" --backend-port "$API_PORT" --quiet; then
            log_success "Monitoring setup validation passed"
        else
            log_warning "Monitoring setup validation had warnings (this is expected if services are not running)"
        fi
    else
        log_warning "Monitoring validation script not found"
    fi
    
    return 0
}

# Main validation function
main() {
    echo "========================================"
    echo "AITM Production Deployment Validation"
    echo "========================================"
    echo "Domain: $DOMAIN"
    echo "API Port: $API_PORT"
    echo "Frontend Port: $FRONTEND_PORT"
    echo "Timeout: ${TIMEOUT}s"
    echo "========================================"
    echo
    
    local validation_functions=(
        "validate_docker_services"
        "validate_health_endpoints"
        "validate_https_ssl"
        "validate_database_connectivity"
        "validate_authentication_system"
        "validate_security_headers"
        "validate_monitoring_services"
        "validate_performance"
        "validate_logs"
        "run_security_validation"
        "run_monitoring_validation"
    )
    
    local passed=0
    local failed=0
    local warnings=0
    
    for func in "${validation_functions[@]}"; do
        echo
        if $func; then
            ((passed++))
        else
            ((failed++))
        fi
    done
    
    echo
    echo "========================================"
    echo "VALIDATION SUMMARY"
    echo "========================================"
    echo "Passed: $passed"
    echo "Failed: $failed"
    echo "Warnings: Check output above"
    echo
    
    if [[ $failed -eq 0 ]]; then
        log_success "All critical validations passed! Deployment appears successful."
        echo
        echo "Next steps:"
        echo "1. Monitor system performance for the next 24 hours"
        echo "2. Verify user acceptance testing"
        echo "3. Update documentation with any deployment notes"
        echo "4. Schedule post-deployment review"
        exit 0
    else
        log_error "$failed critical validations failed. Deployment may need attention."
        echo
        echo "Recommended actions:"
        echo "1. Review failed validations above"
        echo "2. Check service logs for detailed error information"
        echo "3. Consider rollback if issues are critical"
        echo "4. Contact technical team for assistance"
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --api-port)
            API_PORT="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --domain DOMAIN          Domain to validate (default: localhost)"
            echo "  --api-port PORT          API port (default: 8000)"
            echo "  --frontend-port PORT     Frontend port (default: 80)"
            echo "  --timeout SECONDS        Request timeout (default: 30)"
            echo "  --help                   Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check dependencies
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "docker is required but not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    log_error "python3 is required but not installed"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    log_error "bc is required but not installed"
    exit 1
fi

# Run main validation
main