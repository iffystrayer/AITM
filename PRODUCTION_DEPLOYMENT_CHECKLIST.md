# Production Deployment Checklist and Rollback Procedures

## Overview

This document provides a comprehensive checklist for deploying the AITM (AI-Powered Threat Modeler) system to production, along with detailed rollback procedures and risk mitigation strategies.

**Document Version:** 1.0  
**Last Updated:** December 8, 2025  
**System Version:** 1.0.0

---

## Pre-Deployment Checklist

### 🔐 Security Configuration (CRITICAL)

#### JWT and Authentication
- [ ] **CRITICAL**: Generate secure JWT_SECRET_KEY (minimum 32 characters)
  ```bash
  python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
  ```
- [ ] **CRITICAL**: Verify JWT_SECRET_KEY is not a default value
- [ ] **CRITICAL**: Set secure DB_PASSWORD (minimum 16 characters)
  ```bash
  python -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(16))"
  ```
- [ ] **CRITICAL**: Set secure GRAFANA_PASSWORD
- [ ] Verify JWT token expiration settings (15 minutes access, 7 days refresh)
- [ ] Confirm JWT algorithm is HS256

#### SSL/TLS Configuration
- [ ] **CRITICAL**: Obtain SSL certificates for production domain
- [ ] **CRITICAL**: Configure SSL certificate paths in environment
- [ ] **CRITICAL**: Set up ACME email for Let's Encrypt auto-renewal
- [ ] Verify HSTS configuration (enabled, 1-year max-age)
- [ ] Test HTTPS redirect functionality
- [ ] Validate SSL certificate expiration monitoring

#### Security Headers and Policies
- [ ] Verify Content Security Policy (CSP) configuration
- [ ] Confirm secure session cookie settings (Secure, HttpOnly, SameSite=strict)
- [ ] Validate CORS origins (no wildcards, no localhost)
- [ ] Test rate limiting configuration (100 req/5min)
- [ ] Verify security audit logging is enabled

### 🗄️ Database Configuration

#### Database Setup
- [ ] Create production PostgreSQL database
- [ ] Create database user with appropriate permissions
- [ ] Test database connectivity from application server
- [ ] Configure database connection pooling (20 connections, 30 overflow)
- [ ] Set up database backup strategy
- [ ] Test database backup and restore procedures
- [ ] Configure database monitoring and alerting

#### Data Migration
- [ ] Run database migration scripts
- [ ] Verify database schema integrity
- [ ] Test data integrity constraints
- [ ] Validate database indexes and performance
- [ ] Create initial admin user account

### 🌐 Infrastructure Configuration

#### Domain and DNS
- [ ] Configure production domain DNS records
- [ ] Set up API subdomain (api.domain.com)
- [ ] Configure monitoring subdomain (monitoring.domain.com)
- [ ] Test DNS resolution from multiple locations
- [ ] Configure CDN (if applicable)

#### Docker and Container Setup
- [ ] Build production Docker images
- [ ] Test container startup and health checks
- [ ] Verify container resource limits
- [ ] Configure container restart policies
- [ ] Test inter-container networking
- [ ] Validate volume mounts and persistence

#### Load Balancer and Reverse Proxy
- [ ] Configure Traefik reverse proxy
- [ ] Set up SSL termination
- [ ] Configure health check endpoints
- [ ] Test load balancing (if multiple instances)
- [ ] Verify request routing and headers

### 📊 Monitoring and Observability

#### Metrics and Monitoring
- [ ] Deploy Prometheus metrics collection
- [ ] Configure Grafana dashboards
- [ ] Set up application performance monitoring
- [ ] Configure database monitoring
- [ ] Test metrics collection and visualization

#### Logging and Alerting
- [ ] Deploy Loki log aggregation
- [ ] Configure Promtail log collection
- [ ] Set up centralized logging
- [ ] Configure log retention policies
- [ ] Set up alerting rules and notification channels
- [ ] Test alert escalation procedures

#### Health Checks
- [ ] Verify health check endpoints respond correctly
- [ ] Configure external health monitoring
- [ ] Set up synthetic monitoring (if applicable)
- [ ] Test health check alerting

### 🔑 API Keys and External Services

#### AI Service Integration
- [ ] Configure OpenAI API key
- [ ] Configure Anthropic API key
- [ ] Configure Google AI API key
- [ ] Test AI service connectivity and rate limits
- [ ] Verify API key permissions and quotas

#### External Services
- [ ] Configure MITRE ATT&CK data source
- [ ] Set up error tracking (Sentry DSN)
- [ ] Configure email service (SMTP settings)
- [ ] Test external service integrations

### 🔄 Backup and Recovery

#### Backup Configuration
- [ ] Configure automated database backups
- [ ] Set up backup encryption
- [ ] Configure backup retention policy (30 days)
- [ ] Set up backup monitoring and alerting
- [ ] Test backup restoration procedures

#### Disaster Recovery
- [ ] Document disaster recovery procedures
- [ ] Test disaster recovery scenarios
- [ ] Configure backup storage (S3 or equivalent)
- [ ] Set up cross-region backup replication (if required)

---

## Deployment Process

### Phase 1: Infrastructure Preparation

#### Step 1: Environment Setup
```bash
# 1. Create production environment file
cp .env.prod.example .env.prod

# 2. Generate secure secrets
echo "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env.prod
echo "DB_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(16))')" >> .env.prod
echo "GRAFANA_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(12))')" >> .env.prod

# 3. Edit .env.prod with production-specific values
nano .env.prod
```

#### Step 2: Security Validation
```bash
# Run security configuration validation
python validate_production_security.py --env-file .env.prod

# Ensure no critical issues before proceeding
if [ $? -eq 1 ]; then
    echo "CRITICAL: Security validation failed. Fix issues before deployment."
    exit 1
fi
```

#### Step 3: SSL Certificate Setup
```bash
# Option 1: Let's Encrypt (automated)
# Certificates will be obtained automatically by Traefik

# Option 2: Manual certificate installation
# Copy certificates to ssl/ directory
mkdir -p ssl
cp your-cert.pem ssl/cert.pem
cp your-private-key.pem ssl/private.key
chmod 600 ssl/private.key
```

### Phase 2: Database Deployment

#### Step 1: Database Container Deployment
```bash
# Deploy PostgreSQL container
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for database to be ready
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U aitm_user -d aitm_prod

# Verify database connectivity
docker-compose -f docker-compose.prod.yml logs postgres
```

#### Step 2: Database Migration
```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head

# Verify migration success
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import async_session
import asyncio
async def test_db():
    async with async_session() as db:
        result = await db.execute('SELECT version()')
        print(result.scalar())
asyncio.run(test_db())
"
```

### Phase 3: Application Deployment

#### Step 1: Backend Service Deployment
```bash
# Deploy backend service
docker-compose -f docker-compose.prod.yml up -d backend

# Wait for backend to be healthy
timeout 60 bash -c 'until curl -f http://localhost:8000/api/v1/health; do sleep 2; done'

# Verify backend logs
docker-compose -f docker-compose.prod.yml logs backend
```

#### Step 2: Frontend Service Deployment
```bash
# Deploy frontend service
docker-compose -f docker-compose.prod.yml up -d frontend

# Verify frontend accessibility
curl -f http://localhost/

# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend
```

#### Step 3: Reverse Proxy Deployment
```bash
# Deploy Traefik reverse proxy
docker-compose -f docker-compose.prod.yml up -d traefik

# Verify SSL certificate acquisition
docker-compose -f docker-compose.prod.yml logs traefik | grep -i certificate

# Test HTTPS access
curl -f https://your-domain.com/api/v1/health
```

### Phase 4: Monitoring Deployment

#### Step 1: Metrics Collection
```bash
# Deploy Prometheus and Grafana
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Verify Prometheus targets
curl -f http://localhost:9090/api/v1/targets

# Access Grafana dashboard
curl -f http://localhost:3000/api/health
```

#### Step 2: Log Aggregation
```bash
# Deploy Loki and Promtail
docker-compose -f docker-compose.prod.yml up -d loki promtail

# Verify log collection
curl -f http://localhost:3100/ready

# Check log ingestion
docker-compose -f docker-compose.prod.yml logs promtail
```

### Phase 5: Validation and Testing

#### Step 1: Health Check Validation
```bash
# Run monitoring validation
python validate_monitoring_setup.py --base-url https://your-domain.com

# Verify all health endpoints
curl -f https://your-domain.com/api/v1/health
curl -f https://your-domain.com/api/v1/health/detailed
```

#### Step 2: Security Testing
```bash
# Test authentication endpoints
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Verify security headers
curl -I https://your-domain.com/

# Test CORS configuration
curl -H "Origin: https://malicious-site.com" https://your-domain.com/api/v1/health
```

#### Step 3: Performance Testing
```bash
# Basic load test
ab -n 100 -c 10 https://your-domain.com/api/v1/health

# Monitor resource usage during test
docker stats
```

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

#### Emergency Stop
```bash
# Stop all production services immediately
docker-compose -f docker-compose.prod.yml down

# Verify all containers are stopped
docker ps | grep aitm
```

#### Quick Rollback to Previous Version
```bash
# If using tagged images, rollback to previous tag
docker-compose -f docker-compose.prod.yml down
docker tag aitm-backend:previous aitm-backend:latest
docker tag aitm-frontend:previous aitm-frontend:latest
docker-compose -f docker-compose.prod.yml up -d

# Verify rollback success
curl -f https://your-domain.com/api/v1/health
```

### Database Rollback (5-15 minutes)

#### Database Backup Restoration
```bash
# Stop application to prevent database writes
docker-compose -f docker-compose.prod.yml stop backend

# Create current database backup (safety measure)
docker-compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U aitm_user -d aitm_prod > backup_before_rollback.sql

# Restore from previous backup
docker-compose -f docker-compose.prod.yml exec postgres psql \
  -U aitm_user -d aitm_prod < backup_previous.sql

# Restart application
docker-compose -f docker-compose.prod.yml start backend

# Verify database rollback
curl -f https://your-domain.com/api/v1/health/detailed
```

#### Database Migration Rollback
```bash
# Rollback database migrations
docker-compose -f docker-compose.prod.yml exec backend \
  python -m alembic downgrade -1

# Verify migration rollback
docker-compose -f docker-compose.prod.yml exec backend \
  python -m alembic current
```

### Configuration Rollback (2-5 minutes)

#### Environment Configuration Rollback
```bash
# Restore previous environment configuration
cp .env.prod.backup .env.prod

# Restart services with previous configuration
docker-compose -f docker-compose.prod.yml restart

# Verify configuration rollback
docker-compose -f docker-compose.prod.yml logs backend | grep "Configuration loaded"
```

### Complete System Rollback (15-30 minutes)

#### Full Infrastructure Rollback
```bash
# 1. Stop all services
docker-compose -f docker-compose.prod.yml down

# 2. Restore previous Docker images
docker load < aitm-backend-previous.tar
docker load < aitm-frontend-previous.tar

# 3. Restore previous configuration
cp .env.prod.backup .env.prod
cp docker-compose.prod.yml.backup docker-compose.prod.yml

# 4. Restore database
docker-compose -f docker-compose.prod.yml up -d postgres
# Wait for database startup
sleep 30
docker-compose -f docker-compose.prod.yml exec postgres psql \
  -U aitm_user -d aitm_prod < full_backup_previous.sql

# 5. Start all services
docker-compose -f docker-compose.prod.yml up -d

# 6. Verify complete rollback
./validate_deployment.sh
```

---

## Risk Assessment and Mitigation

### High-Risk Scenarios

#### 1. Database Corruption or Loss
**Risk Level:** Critical  
**Impact:** Complete data loss, system unavailable  
**Probability:** Low  

**Mitigation Strategies:**
- Automated hourly database backups
- Cross-region backup replication
- Database transaction log backup
- Regular backup restoration testing
- Database clustering (future enhancement)

**Rollback Time:** 15-30 minutes

#### 2. SSL Certificate Expiration
**Risk Level:** High  
**Impact:** Service inaccessible via HTTPS  
**Probability:** Medium (if not monitored)  

**Mitigation Strategies:**
- Automated certificate renewal with Let's Encrypt
- Certificate expiration monitoring and alerting
- Manual certificate backup procedures
- Certificate validation in deployment pipeline

**Rollback Time:** 5-10 minutes

#### 3. Configuration Error
**Risk Level:** High  
**Impact:** Service malfunction or security vulnerability  
**Probability:** Medium  

**Mitigation Strategies:**
- Configuration validation scripts
- Environment-specific configuration files
- Configuration backup before changes
- Automated configuration testing

**Rollback Time:** 2-5 minutes

#### 4. Container Image Corruption
**Risk Level:** Medium  
**Impact:** Service fails to start  
**Probability:** Low  

**Mitigation Strategies:**
- Image integrity verification
- Multiple image registry replicas
- Previous version image retention
- Automated image building and testing

**Rollback Time:** 5-10 minutes

### Medium-Risk Scenarios

#### 1. Resource Exhaustion
**Risk Level:** Medium  
**Impact:** Performance degradation or service unavailability  
**Probability:** Medium  

**Mitigation Strategies:**
- Resource monitoring and alerting
- Container resource limits
- Auto-scaling configuration (future)
- Performance testing and capacity planning

**Recovery Time:** 5-15 minutes

#### 2. External Service Failure
**Risk Level:** Medium  
**Impact:** Reduced functionality  
**Probability:** Medium  

**Mitigation Strategies:**
- Circuit breaker patterns
- Service degradation handling
- Multiple provider configuration
- External service monitoring

**Recovery Time:** Automatic (graceful degradation)

### Low-Risk Scenarios

#### 1. Monitoring System Failure
**Risk Level:** Low  
**Impact:** Reduced visibility, no functional impact  
**Probability:** Low  

**Mitigation Strategies:**
- Redundant monitoring systems
- External monitoring services
- Monitoring system health checks
- Alert escalation procedures

**Recovery Time:** 10-20 minutes

---

## Post-Deployment Validation

### Immediate Validation (0-15 minutes)

#### Health and Connectivity
- [ ] All health check endpoints respond with 200 OK
- [ ] HTTPS access works correctly
- [ ] Database connectivity confirmed
- [ ] Authentication system functional
- [ ] API endpoints respond correctly

#### Security Validation
- [ ] SSL certificate valid and trusted
- [ ] Security headers present in responses
- [ ] CORS policy enforced correctly
- [ ] Rate limiting functional
- [ ] Security audit logging active

### Short-term Validation (15 minutes - 2 hours)

#### Performance and Stability
- [ ] Response times within acceptable limits (<2 seconds)
- [ ] No memory leaks or resource exhaustion
- [ ] Error rates within normal parameters (<1%)
- [ ] Database performance acceptable
- [ ] Log aggregation working correctly

#### Monitoring and Alerting
- [ ] Metrics collection active
- [ ] Dashboards displaying data
- [ ] Alert rules functional
- [ ] Log retention working
- [ ] Backup processes running

### Long-term Validation (2-24 hours)

#### System Stability
- [ ] No unexpected restarts or crashes
- [ ] Resource usage stable
- [ ] Performance metrics consistent
- [ ] Error patterns normal
- [ ] User experience satisfactory

#### Business Functionality
- [ ] All core features working
- [ ] AI integrations functional
- [ ] Report generation working
- [ ] User authentication stable
- [ ] Data integrity maintained

---

## Emergency Contacts and Procedures

### Escalation Matrix

#### Level 1: Development Team
- **Response Time:** 15 minutes
- **Scope:** Configuration issues, minor bugs, performance problems
- **Contact:** Primary developer on-call

#### Level 2: Technical Lead
- **Response Time:** 30 minutes
- **Scope:** Security issues, database problems, infrastructure failures
- **Contact:** Technical lead and senior developers

#### Level 3: Management
- **Response Time:** 1 hour
- **Scope:** Business-critical failures, security breaches, data loss
- **Contact:** Project manager, CTO, stakeholders

### Emergency Procedures

#### Security Incident Response
1. **Immediate:** Isolate affected systems
2. **5 minutes:** Notify security team
3. **15 minutes:** Assess impact and scope
4. **30 minutes:** Implement containment measures
5. **1 hour:** Begin forensic analysis
6. **2 hours:** Notify stakeholders and authorities (if required)

#### Data Loss Response
1. **Immediate:** Stop all write operations
2. **5 minutes:** Assess extent of data loss
3. **15 minutes:** Begin recovery from backups
4. **30 minutes:** Validate data integrity
5. **1 hour:** Resume operations with monitoring
6. **2 hours:** Conduct post-incident review

---

## Deployment Success Criteria

### Technical Criteria
- [ ] All services running and healthy
- [ ] Response times < 2 seconds for 95% of requests
- [ ] Error rate < 1%
- [ ] SSL certificate valid and properly configured
- [ ] All security validations pass
- [ ] Monitoring and alerting functional
- [ ] Backup processes operational

### Business Criteria
- [ ] All core features accessible
- [ ] User authentication working
- [ ] AI integrations functional
- [ ] Report generation working
- [ ] Performance meets user expectations
- [ ] No data loss or corruption
- [ ] Compliance requirements met

### Operational Criteria
- [ ] Deployment completed within planned window
- [ ] No unplanned downtime
- [ ] Rollback procedures tested and ready
- [ ] Documentation updated
- [ ] Team trained on new procedures
- [ ] Monitoring coverage complete
- [ ] Support procedures in place

---

## Conclusion

This deployment checklist and rollback procedures document provides comprehensive guidance for safely deploying the AITM system to production. The procedures are designed to minimize risk, ensure rapid recovery from issues, and maintain system security and reliability.

**Key Success Factors:**
1. Thorough pre-deployment validation
2. Systematic deployment process
3. Comprehensive monitoring and alerting
4. Well-tested rollback procedures
5. Clear escalation and communication procedures

**Remember:** Always test rollback procedures in a staging environment before production deployment, and ensure all team members are familiar with emergency procedures.

---

**Document Approval:**
- [ ] Technical Lead Review
- [ ] Security Team Review
- [ ] Operations Team Review
- [ ] Management Approval

**Next Review Date:** March 8, 2026