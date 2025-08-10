# AITM Production Deployment Guide

This guide provides comprehensive instructions for deploying the AI-Powered Threat Modeling (AITM) system in production environments.

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/your-org/aitm.git
cd aitm

# 2. Configure environment
cp .env.prod.example .env.prod
# Edit .env.prod with your production values

# 3. Deploy
./deploy-production.sh
```

## 📋 Prerequisites

### System Requirements
- **CPU:** 4+ cores recommended
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 50GB+ SSD recommended
- **OS:** Linux (Ubuntu 20.04+ or CentOS 8+)

### Software Dependencies
- Docker 20.10+
- Docker Compose 1.25+
- Git 2.20+
- OpenSSL 1.1+
- curl

### Network Requirements
- Ports 80, 443 (HTTP/HTTPS)
- Port 22 (SSH admin access)
- Internal container communication

## 🔧 Configuration

### Environment Variables

Copy `.env.prod.example` to `.env.prod` and configure:

#### Security (Required)
```bash
JWT_SECRET_KEY=your-32-character-secret-key
DB_PASSWORD=your-secure-database-password
GRAFANA_PASSWORD=your-grafana-admin-password
```

#### API Keys (Required for AI features)
```bash
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
```

#### Domain Configuration
```bash
DOMAIN=your-domain.com
API_DOMAIN=api.your-domain.com
```

### SSL/TLS Certificates

#### Option 1: Let's Encrypt (Recommended)
```bash
# Update in .env.prod
ACME_EMAIL=admin@your-domain.com

# Traefik will automatically obtain certificates
```

#### Option 2: Custom Certificates
```bash
# Place your certificates in ssl/ directory
ssl/cert.pem      # SSL certificate
ssl/private.key   # Private key
ssl/ca-bundle.crt # Certificate authority bundle (if required)
```

#### Option 3: Self-Signed (Development Only)
```bash
# Auto-generated during deployment
# NOT recommended for production
```

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │────│    Frontend      │────│    Backend      │
│   (Traefik)     │    │   (Svelte)       │    │   (FastAPI)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         │──────────────│     Redis       │    │   PostgreSQL    │
                        │    (Cache)      │    │   (Database)    │
                        └─────────────────┘    └─────────────────┘
         │
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                             │
│  ┌───────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐│
│  │  Prometheus   │ │   Grafana   │ │    Loki     │ │ Promtail ││
│  │  (Metrics)    │ │(Dashboards) │ │   (Logs)    │ │(Log Coll)││
│  └───────────────┘ └─────────────┘ └─────────────┘ └──────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 🔐 Security Configuration

### 1. Access Control

#### Firewall Rules
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### SSH Hardening
```bash
# /etc/ssh/sshd_config
Port 2222                    # Change default port
PermitRootLogin no          # Disable root login
PasswordAuthentication no   # Use key-based auth only
```

### 2. Container Security

#### Non-Root User
All containers run as non-root users for security.

#### Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

#### Read-Only Filesystems
Critical configuration files are mounted read-only.

### 3. Network Security

#### Internal Network
All services communicate through a dedicated Docker network.

#### TLS Encryption
- Frontend-to-backend: HTTPS
- Database connections: TLS
- Redis connections: TLS (optional)

## 📊 Monitoring & Observability

### Metrics (Prometheus)
- **URL:** http://localhost:9090
- **Metrics:** Application performance, resource usage
- **Retention:** 30 days

### Dashboards (Grafana)
- **URL:** http://localhost:3000
- **Default Login:** admin/admin (change immediately)
- **Features:** Pre-configured dashboards, alerting

### Logging (Loki + Promtail)
- **URL:** http://localhost:3100
- **Collection:** Automatic log aggregation
- **Retention:** 30 days

### Health Checks
All services include health checks with automatic restart on failure.

## 💾 Backup & Recovery

### Automated Database Backups
```bash
# Run backup manually
docker exec aitm-postgres-prod pg_dump -U aitm_user -d aitm_prod > backup.sql

# Automated daily backups (configured in production)
# Schedule: 2 AM daily
# Retention: 30 days
# Location: ./database/backups/
```

### Application Data
```bash
# Backup volumes
docker run --rm \
  -v aitm_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres-data-$(date +%Y%m%d).tar.gz /data
```

### Recovery
```bash
# Restore database
docker exec -i aitm-postgres-prod psql -U aitm_user -d aitm_prod < backup.sql

# Restore volumes
docker run --rm \
  -v aitm_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/postgres-data-20240101.tar.gz -C /data --strip 1
```

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Database Migrations
```bash
# Run migrations
docker exec aitm-backend-prod alembic upgrade head
```

### Security Updates
```bash
# Update base images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# System updates
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
sudo yum update -y                      # CentOS/RHEL
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs [service-name]

# Check health
docker-compose -f docker-compose.prod.yml ps
```

#### 2. Database Connection Issues
```bash
# Check database health
docker exec aitm-postgres-prod pg_isready -U aitm_user

# Reset database connection
docker-compose -f docker-compose.prod.yml restart backend
```

#### 3. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Renew Let's Encrypt certificates
docker-compose -f docker-compose.prod.yml restart traefik
```

#### 4. Performance Issues
```bash
# Check resource usage
docker stats

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Log Locations
- Application logs: `./logs/`
- Container logs: `docker-compose logs`
- System logs: `/var/log/`

## 📈 Performance Optimization

### Database Tuning
```sql
-- PostgreSQL optimization (applied automatically)
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

### Redis Configuration
```
# Redis optimization
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

### Application Scaling
```bash
# Horizontal scaling
docker-compose -f docker-compose.prod.yml up -d --scale backend=3 --scale frontend=2

# Load balancing handled by Traefik
```

## 🛡️ Security Best Practices

### Regular Security Tasks

1. **Update Dependencies**
   - Weekly: Check for security updates
   - Monthly: Update base images
   - Quarterly: Review and update configurations

2. **Access Review**
   - Monthly: Review user access
   - Quarterly: Rotate API keys
   - Annually: Update SSL certificates

3. **Monitoring**
   - Daily: Review alerts and logs
   - Weekly: Security scan reports
   - Monthly: Performance review

### Compliance Features

#### GDPR Compliance
- Data encryption at rest and in transit
- User data export capabilities
- Data retention policies
- Audit logging

#### PCI DSS Features
- Secure payment data handling
- Network segmentation
- Access controls
- Logging and monitoring

## 📞 Support & Maintenance

### Production Checklist

- [ ] SSL certificates configured and valid
- [ ] All default passwords changed
- [ ] Firewall rules configured
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented
- [ ] Recovery procedures tested
- [ ] Security hardening applied
- [ ] Performance tuning completed
- [ ] Documentation updated
- [ ] Team trained on operations

### Maintenance Schedule

#### Daily
- Monitor system health
- Review alerts and logs
- Check backup completion

#### Weekly
- Review system performance
- Update dependencies
- Test backup restoration

#### Monthly
- Security vulnerability scan
- Performance optimization review
- Capacity planning assessment

#### Quarterly
- Full security audit
- Disaster recovery testing
- Configuration review

## 📚 Additional Resources

- [Docker Production Best Practices](https://docs.docker.com/config/containers/resource_constraints/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [FastAPI Production Deployment](https://fastapi.tiangolo.com/deployment/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Prometheus Monitoring](https://prometheus.io/docs/introduction/overview/)

## 🆘 Emergency Procedures

### System Down
1. Check service status: `docker-compose ps`
2. Review logs: `docker-compose logs`
3. Restart services: `docker-compose restart`
4. If critical, contact support team

### Data Corruption
1. Stop applications immediately
2. Restore from latest backup
3. Verify data integrity
4. Restart services
5. Post-incident review

### Security Breach
1. Isolate affected systems
2. Change all credentials
3. Review access logs
4. Apply security patches
5. Notify stakeholders

---

**⚠️ Important:** Always test changes in a staging environment before applying to production.

For additional support, contact your system administrator or refer to the project documentation.
