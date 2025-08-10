# AITM Production Deployment Guide - Complete Implementation

*Updated: 2025-08-10T05:20:00Z*

## 🚀 **Quick Production Deployment**

### **Prerequisites**
- Docker & Docker Compose installed
- Domain name configured (optional but recommended)
- SSL certificates (Let's Encrypt recommended)
- Basic server administration knowledge

### **1. Environment Setup**

Create production environment file:
```bash
# Create production environment
cp .env.example .env.production
```

**Required Environment Variables:**
```env
# Application Settings
NODE_ENV=production
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=your-super-secret-jwt-key-here-minimum-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (Production)
DATABASE_URL=postgresql://user:password@localhost:5432/aitm_prod
# OR SQLite for smaller deployments
DATABASE_URL=sqlite:///./data/aitm_production.db

# CORS Settings (restrict in production)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# External Services
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-gemini-key

# Monitoring
LOG_LEVEL=info
ENABLE_METRICS=true
```

### **2. Install Production Dependencies**

```bash
# Backend dependencies (in Docker or virtual environment)
cd backend
pip install -r requirements.txt

# Frontend build dependencies
cd ../frontend
npm ci --production
npm run build
```

### **3. Production Docker Setup**

**Create production Docker Compose:**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  aitm-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
    restart: unless-stopped

  aitm-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/ssl/certs
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - aitm-backend
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: aitm_prod
      POSTGRES_USER: aitm_user
      POSTGRES_PASSWORD: secure_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### **4. Production Dockerfiles**

**Backend Production Dockerfile:**
```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 aitm && chown -R aitm:aitm /app
USER aitm

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start application
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Frontend Production Dockerfile:**
```dockerfile
# frontend/Dockerfile.prod
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.prod.conf /etc/nginx/nginx.conf
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
```

### **5. SSL/TLS Configuration**

**Nginx SSL Configuration:**
```nginx
# nginx.prod.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server aitm-backend:8000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL certificates (Let's Encrypt)
        ssl_certificate /etc/ssl/certs/fullchain.pem;
        ssl_certificate_key /etc/ssl/certs/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### **6. Deploy to Production**

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### **7. Post-Deployment Setup**

**Create Admin User:**
```bash
# Access backend container
docker-compose -f docker-compose.prod.yml exec aitm-backend bash

# Create superuser (Python script)
python3 -c "
import asyncio
from app.core.database import async_session
from app.services.user_service import UserService
from app.core.auth import AuthService
from app.models.user import UserCreate

async def create_admin():
    auth_service = AuthService()
    user_service = UserService(auth_service)
    
    async with async_session() as db:
        admin_user = UserCreate(
            email='admin@yourdomain.com',
            password='SecureAdminPassword123!',
            full_name='System Administrator',
            is_superuser=True,
            is_active=True
        )
        
        user = await user_service.create_user(db, admin_user)
        await db.commit()
        print(f'Admin user created: {user.email}')

asyncio.run(create_admin())
"
```

**Database Migration (if needed):**
```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec aitm-backend alembic upgrade head
```

## 🔧 **Advanced Production Configuration**

### **Monitoring & Logging**

**Application Monitoring:**
```yaml
# Add to docker-compose.prod.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_grafana_password
```

**Log Management:**
```bash
# Configure log rotation
sudo tee /etc/logrotate.d/aitm << EOF
/var/log/aitm/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

### **Backup Strategy**

**Database Backup Script:**
```bash
#!/bin/bash
# backup-db.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database"

# Create backup directory
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
  -U aitm_user aitm_prod | gzip > $BACKUP_DIR/aitm_backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: aitm_backup_$DATE.sql.gz"
```

**Automated Backups (Crontab):**
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup-db.sh

# Weekly full system backup
0 3 * * 0 tar -czf /backups/system/aitm_full_$(date +%Y%m%d).tar.gz /opt/aitm
```

### **Security Hardening**

**Firewall Configuration:**
```bash
# UFW firewall setup
sudo ufw enable
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny 8000/tcp     # Block direct backend access
```

**Rate Limiting:**
```nginx
# Add to nginx.conf
http {
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        # Rate limiting for auth endpoints
        location /api/auth/ {
            limit_req zone=auth burst=3 nodelay;
            proxy_pass http://backend;
        }
        
        # Rate limiting for API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
        }
    }
}
```

### **Performance Optimization**

**Database Configuration:**
```sql
-- PostgreSQL optimization (production)
-- Add to postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
```

**Application Caching:**
```python
# Add Redis caching to backend
# backend/app/core/cache.py
import redis
import json
from typing import Optional, Any

redis_client = redis.Redis(host='redis', port=6379, db=0)

class CacheService:
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    
    @staticmethod
    async def set(key: str, value: Any, expire: int = 3600):
        redis_client.setex(key, expire, json.dumps(value))
    
    @staticmethod
    async def delete(key: str):
        redis_client.delete(key)
```

## 📊 **Production Monitoring**

### **Health Checks**

**Application Health Monitoring:**
```python
# backend/app/api/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
import psutil
import time

router = APIRouter()

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    
    # Database check
    try:
        await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # System metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    response_time = time.time() - start_time
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": time.time(),
        "response_time": response_time,
        "database": db_status,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": (disk.used / disk.total) * 100
        }
    }
```

### **Metrics Collection**

**Prometheus Metrics:**
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')

# Middleware for metrics collection
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

## 🔐 **Security Checklist**

### **Pre-Deployment Security**
- [ ] Change all default passwords and secrets
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure secure CORS origins
- [ ] Set up proper firewall rules
- [ ] Enable rate limiting
- [ ] Configure secure session management
- [ ] Set up monitoring and alerting
- [ ] Regular security updates scheduled

### **Post-Deployment Security**
- [ ] Monitor authentication logs
- [ ] Set up automated backups
- [ ] Configure intrusion detection
- [ ] Regular penetration testing
- [ ] Security audit trails
- [ ] Incident response plan
- [ ] Data retention policies
- [ ] Compliance documentation

## 🎯 **Production Verification**

### **Deployment Tests**
```bash
# Health check
curl -f https://yourdomain.com/health

# Authentication test
curl -X POST https://yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!","full_name":"Test User"}'

# API functionality
curl -X GET https://yourdomain.com/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN"

# Performance test
ab -n 100 -c 10 https://yourdomain.com/
```

### **Success Criteria**
- [ ] Application accessible via HTTPS
- [ ] All API endpoints responding correctly
- [ ] Authentication system working
- [ ] Database operations successful
- [ ] Frontend loading and functional
- [ ] Monitoring systems active
- [ ] Backup systems operational
- [ ] Performance within acceptable limits

## 🚀 **Go-Live Checklist**

1. **Infrastructure Ready**
   - [ ] Domain configured and DNS propagated
   - [ ] SSL certificates installed and valid
   - [ ] Firewall configured and tested
   - [ ] Load balancers configured (if applicable)

2. **Application Deployed**
   - [ ] All services running and healthy
   - [ ] Database migrated and accessible
   - [ ] Admin user created and tested
   - [ ] Authentication system validated

3. **Monitoring Active**
   - [ ] Health checks configured
   - [ ] Metrics collection active
   - [ ] Alerting rules configured
   - [ ] Log aggregation working

4. **Security Verified**
   - [ ] HTTPS enforced
   - [ ] Security headers configured
   - [ ] Rate limiting active
   - [ ] Vulnerability scan passed

5. **Backup Systems**
   - [ ] Database backups automated
   - [ ] File system backups configured
   - [ ] Backup restoration tested
   - [ ] Recovery procedures documented

---

## 📞 **Production Support**

**System Status:** Production-Ready  
**Documentation:** Complete  
**Security:** Hardened  
**Monitoring:** Active  
**Backup:** Automated  

**Next Steps After Deployment:**
1. Monitor system performance and user feedback
2. Implement additional security measures as needed
3. Scale infrastructure based on usage patterns
4. Regular security updates and maintenance
5. Feature enhancements based on user requirements

**Emergency Procedures:**
- Health check endpoints for monitoring
- Database backup and restore procedures
- Incident response contacts and escalation
- System rollback procedures if needed
