# AITM Administrator Guide

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Installation & Setup](#installation--setup)
- [Configuration Management](#configuration-management)
- [User Management](#user-management)
- [System Monitoring](#system-monitoring)
- [Security Administration](#security-administration)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)
- [Maintenance Procedures](#maintenance-procedures)

## Overview

AITM (AI-Powered Threat Modeler) is an enterprise-grade threat modeling platform that combines artificial intelligence with cybersecurity expertise to provide comprehensive threat analysis and risk assessment capabilities.

### Key Administrative Responsibilities
- **System Deployment**: Installing and configuring the platform
- **User Management**: Managing user accounts, roles, and permissions
- **Security Configuration**: Implementing security policies and controls
- **Performance Monitoring**: Ensuring optimal system performance
- **Data Management**: Managing backups, updates, and system maintenance

## System Architecture

### Core Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (SvelteKit)   │◄──►│   (FastAPI)     │◄──►│ (PostgreSQL)    │
│   Port: 59000   │    │   Port: 38527   │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AI Services   │
                    │ (LLM Providers) │
                    └─────────────────┘
```

### Service Dependencies
- **Frontend**: Depends on Backend API
- **Backend**: Depends on Database and AI Services
- **Database**: Independent, persistent storage
- **AI Services**: External LLM providers (OpenAI, Anthropic, Google)

## Installation & Setup

### Prerequisites
- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **System Requirements**: 8GB RAM minimum, 16GB recommended
- **Storage**: 50GB minimum available space
- **Network**: Internet connectivity for AI services

### Development Installation
```bash
# Clone the repository
git clone https://github.com/your-org/aitm.git
cd aitm

# Create environment file
cp .env.example .env

# Start services
./docker-dev.sh start

# Verify installation
./docker-dev.sh status
```

### Production Installation
```bash
# Create production directory
sudo mkdir -p /opt/aitm
sudo chown $USER:$USER /opt/aitm

# Clone and configure
git clone https://github.com/your-org/aitm.git /opt/aitm
cd /opt/aitm

# Configure production environment
cp .env.example .env.production
# Edit .env.production with production values

# Deploy production services
docker-compose -f docker-compose.prod.yml up -d --build

# Initialize database
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

## Configuration Management

### Environment Variables

#### Core Configuration
```bash
# Application Settings
ENVIRONMENT=production          # Environment mode
DEBUG=false                    # Debug mode (false for production)
LOG_LEVEL=INFO                 # Logging level
SECRET_KEY=your_secret_key     # Application secret key

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=aitm_production
DATABASE_USER=aitm_user
DATABASE_PASSWORD=secure_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=38527
CORS_ORIGINS=https://yourdomain.com
```

#### AI Service Configuration
```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-api-key

# AI Service Settings
DEFAULT_LLM_PROVIDER=openai
MAX_TOKENS=4000
TEMPERATURE=0.7
```

#### Security Configuration
```bash
# Authentication
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION_HOURS=24
SESSION_SECRET=your-session-secret

# Security Headers
SECURE_COOKIES=true
CSRF_PROTECTION=true
RATE_LIMIT_ENABLED=true
```

### File-based Configuration

#### Docker Compose Configuration
**docker-compose.yml** (Development)
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "38527:38527"
    environment:
      - ENVIRONMENT=development
    volumes:
      - ./backend:/app
      - backend-data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "59000:59000"
    depends_on:
      - backend
```

#### Nginx Configuration (Production)
```nginx
# /etc/nginx/sites-available/aitm
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Frontend
    location / {
        proxy_pass http://localhost:59000;
        proxy_set_header Host $host;
    }
    
    # API
    location /api/ {
        proxy_pass http://localhost:38527;
        proxy_set_header Host $host;
    }
}
```

## User Management

### User Roles and Permissions

#### Administrator
- **Full system access**: All configuration and management functions
- **User management**: Create, modify, delete user accounts
- **System monitoring**: Access to logs, metrics, and health data
- **Security configuration**: Manage security policies and settings

#### Security Analyst
- **Threat modeling**: Create and manage threat models
- **Analysis tools**: Access to all analysis features
- **Report generation**: Create and export reports
- **Asset management**: Manage organizational assets

#### Viewer
- **Read-only access**: View existing threat models and reports
- **Limited analysis**: Basic threat analysis capabilities
- **No configuration**: Cannot modify system settings

### User Account Management

#### Creating Users
```bash
# Via CLI (if implemented)
docker-compose exec backend python -m app.cli create-user \
  --email admin@company.com \
  --name "System Administrator" \
  --role administrator

# Via API
curl -X POST http://localhost:38527/api/v1/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "email": "user@company.com",
    "name": "User Name",
    "role": "analyst",
    "password": "secure_password"
  }'
```

#### Modifying User Permissions
```bash
# Update user role
curl -X PUT http://localhost:38527/api/v1/users/123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"role": "administrator"}'

# Deactivate user
curl -X PUT http://localhost:38527/api/v1/users/123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"active": false}'
```

## System Monitoring

### Health Monitoring

#### Service Health Checks
```bash
# Check all services
docker-compose ps

# Check service health
curl http://localhost:38527/health
curl http://localhost:59000/health

# View service logs
docker-compose logs backend
docker-compose logs frontend
```

#### System Metrics
```bash
# Container resource usage
docker stats

# Disk usage
df -h /opt/aitm

# Memory usage
free -h

# CPU usage
top -p $(pgrep -f "python.*app.main")
```

### Application Monitoring

#### API Endpoint Monitoring
```bash
# Monitor API response times
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:38527/api/v1/projects/

# Monitor database connections
docker-compose exec backend python -c "
from app.database import get_db
db = next(get_db())
print('Database connection:', db.execute('SELECT 1').scalar())
"
```

#### Log Management
```bash
# Application logs location
/opt/aitm/logs/backend/app.log
/opt/aitm/logs/nginx/access.log
/opt/aitm/logs/nginx/error.log

# View recent logs
tail -f /opt/aitm/logs/backend/app.log

# Search logs for errors
grep ERROR /opt/aitm/logs/backend/app.log

# Log rotation configuration
cat > /etc/logrotate.d/aitm << EOF
/opt/aitm/logs/*/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

## Security Administration

### SSL/TLS Configuration
```bash
# Generate self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/aitm/ssl/key.pem \
  -out /opt/aitm/ssl/cert.pem

# Install Let's Encrypt certificate (production)
certbot --nginx -d yourdomain.com
```

### Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 38527/tcp  # Block direct backend access
sudo ufw deny 59000/tcp  # Block direct frontend access
```

### Security Scanning
```bash
# Container security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image aitm-backend:latest

# Dependency vulnerability scan
docker-compose exec backend pip-audit

# Network security scan
nmap -sS -O localhost
```

## Backup & Recovery

### Database Backup
```bash
#!/bin/bash
# /opt/aitm/scripts/backup-database.sh

BACKUP_DIR="/opt/aitm/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/aitm_db_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform database backup
docker-compose exec -T postgres pg_dump -U aitm_user aitm_production > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "aitm_db_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: ${BACKUP_FILE}.gz"
```

### Application Backup
```bash
#!/bin/bash
# /opt/aitm/scripts/backup-application.sh

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d)
APP_BACKUP="${BACKUP_DIR}/aitm_app_${DATE}.tar.gz"

# Create application backup
tar -czf $APP_BACKUP \
  --exclude='logs/*' \
  --exclude='node_modules' \
  --exclude='.git' \
  /opt/aitm

echo "Application backup completed: $APP_BACKUP"
```

### Recovery Procedures
```bash
# Database recovery
zcat /opt/aitm/backups/aitm_db_20250809.sql.gz | \
  docker-compose exec -T postgres psql -U aitm_user -d aitm_production

# Application recovery
cd /opt
tar -xzf /opt/backups/aitm_app_20250809.tar.gz
docker-compose -f /opt/aitm/docker-compose.prod.yml up -d --build
```

## Troubleshooting

### Common Issues

#### Services Not Starting
**Problem**: Docker containers fail to start
```bash
# Check docker logs
docker-compose logs backend
docker-compose logs frontend

# Common solutions:
# 1. Check port conflicts
netstat -tlnp | grep :38527
netstat -tlnp | grep :59000

# 2. Check disk space
df -h

# 3. Check memory usage
free -h

# 4. Rebuild containers
docker-compose down
docker-compose up --build
```

#### Database Connection Issues
**Problem**: Cannot connect to database
```bash
# Check database status
docker-compose exec postgres pg_isready -U aitm_user -d aitm_production

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U aitm_user -d aitm_production -c "SELECT 1;"

# Common solutions:
# 1. Verify credentials in .env file
# 2. Check database is running
# 3. Verify network connectivity
```

#### Performance Issues
**Problem**: Slow response times
```bash
# Check system resources
htop
iotop
docker stats

# Check database performance
docker-compose exec postgres psql -U aitm_user -d aitm_production -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;"

# Common solutions:
# 1. Scale resources (CPU, Memory)
# 2. Optimize database queries
# 3. Implement caching
```

### Diagnostic Commands
```bash
# System health check
./docker-dev.sh status

# Full system diagnostic
cat > /opt/aitm/scripts/diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== AITM System Diagnostic ==="
echo "Date: $(date)"
echo
echo "=== Docker Status ==="
docker-compose ps
echo
echo "=== System Resources ==="
free -h
df -h
echo
echo "=== Service Health ==="
curl -s http://localhost:38527/health | jq .
echo
echo "=== Recent Errors ==="
tail -20 /opt/aitm/logs/backend/app.log | grep ERROR
EOF

chmod +x /opt/aitm/scripts/diagnostic.sh
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
- [ ] Check service health status
- [ ] Review error logs
- [ ] Monitor system resources
- [ ] Verify backup completion

#### Weekly Tasks
- [ ] Update system packages
- [ ] Review security logs
- [ ] Check disk space usage
- [ ] Test backup restoration

#### Monthly Tasks
- [ ] Security vulnerability scan
- [ ] Performance optimization review
- [ ] Update documentation
- [ ] Audit user accounts

#### Quarterly Tasks
- [ ] Disaster recovery testing
- [ ] Security policy review
- [ ] System capacity planning
- [ ] Update SSL certificates

### Update Procedures

#### Application Updates
```bash
# 1. Backup current system
/opt/aitm/scripts/backup-application.sh

# 2. Pull latest changes
cd /opt/aitm
git pull origin main

# 3. Update dependencies
docker-compose build --no-cache

# 4. Run database migrations
docker-compose exec backend python -m alembic upgrade head

# 5. Restart services
docker-compose down
docker-compose up -d

# 6. Verify update
curl http://localhost:38527/health
```

#### Security Updates
```bash
# Update base images
docker-compose pull
docker-compose up -d --build

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update SSL certificates
certbot renew --dry-run
```

### Performance Optimization

#### Database Optimization
```sql
-- Analyze database performance
ANALYZE;

-- Update statistics
UPDATE pg_stat_statements_reset();

-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC;
```

#### Application Optimization
```bash
# Monitor application performance
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Optimize container resources
# Edit docker-compose.yml to adjust memory limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

---

## Support and Contact

### Internal Support
- **System Administrator**: admin@yourcompany.com
- **Development Team**: dev@yourcompany.com
- **Security Team**: security@yourcompany.com

### External Resources
- **Documentation**: https://docs.aitm.io
- **GitHub Repository**: https://github.com/your-org/aitm
- **Issue Tracker**: https://github.com/your-org/aitm/issues

### Emergency Procedures
1. **Critical System Failure**: Contact system administrator immediately
2. **Security Incident**: Follow incident response plan
3. **Data Loss**: Initiate disaster recovery procedures
4. **Service Outage**: Check system status and escalate if needed

---

*Last Updated: 2025-08-09*
*Document Version: 1.0*
