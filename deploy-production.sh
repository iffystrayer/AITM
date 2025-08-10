#!/bin/bash

# AITM Production Deployment Script
# This script handles secure production deployment with pre-deployment checks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/deployment-$(date +%Y%m%d-%H%M%S).log"
BACKUP_DIR="${SCRIPT_DIR}/backups"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Banner
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                      AITM PRODUCTION DEPLOYMENT                             ║
║                    AI-Powered Threat Modeling System                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF

log "Starting AITM production deployment..."

# Pre-deployment checks
check_prerequisites() {
    log "Running pre-deployment checks..."
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        warn "Running as root is not recommended for security reasons"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Deployment aborted"
        fi
    fi
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "curl" "openssl" "git")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "$cmd is not installed or not in PATH"
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    
    # Check Docker Compose version
    local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [[ $(printf '%s\n' "1.25.0" "$compose_version" | sort -V | head -n1) != "1.25.0" ]]; then
        warn "Docker Compose version $compose_version might be too old (recommended: 1.25.0+)"
    fi
    
    # Check available disk space (minimum 10GB)
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 10485760 ]]; then
        error "Insufficient disk space. At least 10GB required"
    fi
    
    # Check for required files
    local required_files=("docker-compose.prod.yml" ".env.prod")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file $file not found"
        fi
    done
    
    log "Pre-deployment checks passed"
}

# Environment setup
setup_environment() {
    log "Setting up production environment..."
    
    # Create necessary directories
    local dirs=("data/postgres" "data/redis" "data/prometheus" "data/grafana" "data/loki" "logs" "uploads" "ssl" "monitoring" "scripts")
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        info "Created directory: $dir"
    done
    
    # Set proper permissions
    chmod 700 data/
    chmod 755 logs/ uploads/
    chmod 600 .env.prod
    
    # Create backup directory with timestamp
    mkdir -p "$BACKUP_DIR"
    
    log "Environment setup completed"
}

# Security validation
validate_security() {
    log "Validating security configuration..."
    
    # Check .env.prod for sensitive defaults
    local security_issues=0
    
    if grep -q "your-super-secure" .env.prod; then
        error "Default security values found in .env.prod - please update all placeholder values"
        ((security_issues++))
    fi
    
    if grep -q "your-.*-key-here" .env.prod; then
        warn "Placeholder API keys found in .env.prod"
        ((security_issues++))
    fi
    
    # Check JWT secret length
    local jwt_secret=$(grep '^JWT_SECRET_KEY=' .env.prod | cut -d'=' -f2)
    if [[ ${#jwt_secret} -lt 32 ]]; then
        error "JWT_SECRET_KEY must be at least 32 characters long"
        ((security_issues++))
    fi
    
    # Check database password strength
    local db_password=$(grep '^DB_PASSWORD=' .env.prod | cut -d'=' -f2)
    if [[ ${#db_password} -lt 16 ]]; then
        warn "DB_PASSWORD should be at least 16 characters long"
        ((security_issues++))
    fi
    
    if [[ $security_issues -eq 0 ]]; then
        log "Security validation passed"
    else
        warn "Security validation completed with $security_issues issues"
    fi
}

# SSL/TLS setup
setup_ssl() {
    log "Setting up SSL/TLS certificates..."
    
    if [[ ! -f "ssl/cert.pem" || ! -f "ssl/private.key" ]]; then
        info "SSL certificates not found, generating self-signed certificates for development"
        
        # Generate self-signed certificate
        openssl req -x509 -newkey rsa:4096 -keyout ssl/private.key -out ssl/cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=AITM/CN=aitm.local" 2>/dev/null
        
        chmod 600 ssl/private.key
        chmod 644 ssl/cert.pem
        
        warn "Using self-signed certificates. For production, use certificates from a trusted CA"
    else
        log "SSL certificates found"
    fi
}

# Database backup
backup_database() {
    log "Creating database backup..."
    
    local backup_file="${BACKUP_DIR}/aitm-backup-$(date +%Y%m%d-%H%M%S).sql"
    
    # Check if database container is running
    if docker ps --filter "name=aitm-postgres" --format "table {{.Names}}" | grep -q "aitm-postgres"; then
        info "Creating backup of existing database"
        
        # Create backup
        docker exec -i aitm-postgres pg_dump -U aitm_user -d aitm_prod > "$backup_file" 2>/dev/null || true
        
        if [[ -f "$backup_file" && -s "$backup_file" ]]; then
            log "Database backup created: $backup_file"
        else
            warn "Database backup failed or database is empty"
        fi
    else
        info "No existing database container found, skipping backup"
    fi
}

# Build and deploy
deploy_application() {
    log "Building and deploying AITM application..."
    
    # Pull latest images
    info "Pulling base images..."
    docker-compose -f docker-compose.prod.yml pull --quiet
    
    # Build custom images
    info "Building application images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start services in correct order
    info "Starting infrastructure services..."
    docker-compose -f docker-compose.prod.yml up -d postgres redis
    
    # Wait for database to be ready
    info "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        if docker exec aitm-postgres-prod pg_isready -U aitm_user -d aitm_prod &>/dev/null; then
            break
        fi
        ((attempt++))
        sleep 2
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "Database failed to start within timeout"
    fi
    
    info "Starting application services..."
    docker-compose -f docker-compose.prod.yml up -d backend frontend
    
    info "Starting monitoring services..."
    docker-compose -f docker-compose.prod.yml up -d traefik prometheus grafana loki promtail
    
    log "Application deployment completed"
}

# Health checks
run_health_checks() {
    log "Running health checks..."
    
    local max_attempts=30
    local services=("backend" "frontend")
    
    for service in "${services[@]}"; do
        info "Checking $service health..."
        local attempt=0
        
        while [[ $attempt -lt $max_attempts ]]; do
            case $service in
                "backend")
                    if curl -sf http://localhost:8000/api/v1/health &>/dev/null; then
                        log "$service is healthy"
                        break
                    fi
                    ;;
                "frontend")
                    if curl -sf http://localhost &>/dev/null; then
                        log "$service is healthy"
                        break
                    fi
                    ;;
            esac
            
            ((attempt++))
            sleep 3
        done
        
        if [[ $attempt -eq $max_attempts ]]; then
            warn "$service health check timed out"
        fi
    done
    
    # Display running services
    info "Container status:"
    docker-compose -f docker-compose.prod.yml ps
}

# Post-deployment tasks
post_deployment() {
    log "Running post-deployment tasks..."
    
    # Create default admin user (interactive)
    info "You may want to create an admin user"
    echo "Run the following command to create an admin user:"
    echo "docker exec -it aitm-backend-prod python -c \"from app.scripts.create_admin import create_admin_user; create_admin_user()\""
    
    # Set up monitoring dashboards
    info "Setting up monitoring dashboards..."
    echo "Grafana dashboard: http://localhost:3000 (admin/admin)"
    echo "Prometheus: http://localhost:9090"
    echo "Traefik dashboard: http://localhost:8080"
    
    # Security reminder
    warn "SECURITY REMINDERS:"
    echo "1. Change default passwords immediately"
    echo "2. Configure SSL certificates from a trusted CA"
    echo "3. Set up firewall rules to restrict access"
    echo "4. Configure log monitoring and alerting"
    echo "5. Set up automated backups"
    echo "6. Review and update security settings"
    
    log "Post-deployment tasks completed"
}

# Rollback function
rollback() {
    error "Deployment failed. Rolling back..."
    
    # Stop all services
    docker-compose -f docker-compose.prod.yml down
    
    # Clean up failed deployment
    docker system prune -f
    
    error "Rollback completed. Check logs for details: $LOG_FILE"
}

# Trap errors and rollback
trap rollback ERR

# Main deployment flow
main() {
    log "AITM Production Deployment Started"
    
    check_prerequisites
    setup_environment
    validate_security
    setup_ssl
    backup_database
    deploy_application
    run_health_checks
    post_deployment
    
    log "🎉 AITM Production Deployment Completed Successfully!"
    echo ""
    echo "Access your application at:"
    echo "  Frontend: https://localhost (or your configured domain)"
    echo "  Backend API: https://localhost:8000/api/v1"
    echo "  API Documentation: https://localhost:8000/docs"
    echo "  Monitoring: http://localhost:3000 (Grafana)"
    echo ""
    echo "Deployment log saved to: $LOG_FILE"
    echo ""
    echo "⚠️  Don't forget to:"
    echo "1. Update DNS records to point to this server"
    echo "2. Configure proper SSL certificates"
    echo "3. Set up automated backups"
    echo "4. Configure monitoring alerts"
    echo "5. Review security settings"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
