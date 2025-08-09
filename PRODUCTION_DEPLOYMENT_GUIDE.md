# AITM Production Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the AITM (AI-Powered Threat Modeler) platform to production environments.

## Pre-Deployment Checklist ✅

### System Requirements
- [ ] **Operating System**: Ubuntu 20.04+ or RHEL 8+
- [ ] **Docker**: Version 20.10+
- [ ] **Docker Compose**: Version 2.0+
- [ ] **Memory**: Minimum 8GB RAM, Recommended 16GB+
- [ ] **Storage**: Minimum 50GB available space
- [ ] **Network**: Open ports 80, 443 (and custom ports if needed)

### Security Configuration
- [ ] **SSL Certificates**: Valid SSL certificates configured
- [ ] **Firewall Rules**: Properly configured firewall rules
- [ ] **Environment Variables**: All sensitive data in environment variables
- [ ] **Database Security**: Database credentials and access properly secured
- [ ] **API Keys**: LLM provider API keys securely stored
- [ ] **CORS Configuration**: Production CORS settings configured

### Environment Configuration

#### Required Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@db:5432/aitm_prod
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=aitm_production
DATABASE_USER=aitm_user
DATABASE_PASSWORD=secure_password_here

# Application Configuration  
ENVIRONMENT=production
SECRET_KEY=your_secure_secret_key_minimum_32_chars
DEBUG=false
LOG_LEVEL=INFO

# LLM Provider Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key

# API Configuration
API_HOST=0.0.0.0
API_PORT=38527
FRONTEND_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com

# Security
JWT_SECRET=your_jwt_secret_key_here
SESSION_SECRET=your_session_secret_here
BCRYPT_ROUNDS=12

# Email Configuration (if applicable)
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_user
SMTP_PASSWORD=your_smtp_password
FROM_EMAIL=noreply@your-domain.com
```

## Production Docker Configuration

### 1. Production Docker Compose
Create `docker-compose.prod.yml`:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - aitm-network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    expose:
      - "38527"
    volumes:
      - backend-data:/app/data
      - ./logs/backend:/app/logs
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
    env_file:
      - .env.production
    networks:
      - aitm-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:38527/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    expose:
      - "59000"
    environment:
      - NODE_ENV=production
      - VITE_API_BASE_URL=https://api.your-domain.com/api/v1
    networks:
      - aitm-network
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:59000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: aitm_production
      POSTGRES_USER: aitm_user
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - aitm-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - aitm-network
    restart: unless-stopped

volumes:
  backend-data:
    driver: local
  postgres-data:
    driver: local
  redis-data:
    driver: local

networks:
  aitm-network:
    driver: bridge
```

### 2. Production Dockerfiles

#### Backend Production Dockerfile
Create `backend/Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 aitm && chown -R aitm:aitm /app
USER aitm

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:38527/health || exit 1

# Production command
CMD ["python", "-m", "app.main"]
```

#### Frontend Production Dockerfile
Create `frontend/Dockerfile.prod`:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Build application
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:59000/ || exit 1

EXPOSE 59000

CMD ["nginx", "-g", "daemon off;"]
```

### 3. Nginx Configuration
Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:38527;
    }

    upstream frontend {
        server frontend:59000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=2r/s;

    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com www.your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # Frontend
        location / {
            limit_req zone=general burst=20 nodelay;
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API
        location /api/ {
            limit_req zone=api burst=50 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS
            add_header Access-Control-Allow-Origin "https://your-domain.com";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        }

        # Health checks
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

## Deployment Steps

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
sudo mkdir -p /opt/aitm
sudo chown $USER:$USER /opt/aitm
```

### 2. Application Deployment
```bash
# Clone repository
git clone https://github.com/your-org/aitm.git /opt/aitm
cd /opt/aitm

# Create production environment file
cp .env.example .env.production
# Edit .env.production with production values

# Create SSL directory and add certificates
mkdir -p ssl
# Copy your SSL certificates to ssl/cert.pem and ssl/key.pem

# Create log directories
mkdir -p logs/{nginx,backend}

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

### 3. Monitoring Setup
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Monitor resource usage
docker stats
```

## Performance Optimization

### 1. Database Optimization
- Configure PostgreSQL for production workloads
- Set up database connection pooling
- Implement database indexing strategy
- Schedule regular database maintenance

### 2. Caching Strategy
- Implement Redis caching for API responses
- Configure static asset caching
- Set up CDN for static resources

### 3. Load Balancing
- Configure multiple backend instances
- Implement health checks
- Set up auto-scaling policies

## Security Hardening

### 1. Network Security
- Configure firewall rules (UFW/iptables)
- Implement fail2ban for intrusion prevention
- Use VPN for administrative access

### 2. Application Security
- Regular security updates
- Dependency vulnerability scanning
- API rate limiting
- Input validation and sanitization

### 3. Data Protection
- Database encryption at rest
- Backup encryption
- Secure data transmission (TLS 1.3)

## Monitoring and Logging

### 1. Application Monitoring
```bash
# Install monitoring tools
docker run -d --name prometheus prom/prometheus
docker run -d --name grafana grafana/grafana
```

### 2. Log Management
```bash
# Configure log rotation
sudo logrotate /opt/aitm/logs/
```

### 3. Health Checks
- API endpoint monitoring
- Database connection monitoring  
- Disk space monitoring
- Memory usage alerts

## Backup Strategy

### 1. Database Backup
```bash
#!/bin/bash
# daily-backup.sh
BACKUP_DIR="/opt/aitm/backups"
DATE=$(date +%Y%m%d_%H%M%S)

docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U aitm_user aitm_production > "${BACKUP_DIR}/db_backup_${DATE}.sql"

# Keep only last 7 days
find ${BACKUP_DIR} -name "db_backup_*.sql" -mtime +7 -delete
```

### 2. Application Backup
```bash
# Backup application data and configurations
tar -czf /opt/backups/aitm_app_$(date +%Y%m%d).tar.gz \
  /opt/aitm \
  --exclude=/opt/aitm/logs \
  --exclude=/opt/aitm/node_modules
```

## Troubleshooting

### Common Issues
1. **Service won't start**: Check logs and environment variables
2. **Database connection failed**: Verify database credentials and network
3. **SSL certificate issues**: Validate certificate files and paths
4. **Performance issues**: Check resource usage and optimize accordingly

### Maintenance Commands
```bash
# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update application
git pull origin main
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Clean up unused Docker resources
docker system prune -a
```

## Support and Maintenance

### Regular Maintenance Tasks
- [ ] Weekly log review and cleanup
- [ ] Monthly security updates
- [ ] Quarterly performance review
- [ ] Semi-annual disaster recovery testing

### Performance Monitoring
- Response time monitoring
- Error rate tracking
- Resource utilization alerts
- User experience metrics

---

**Note**: This guide assumes a single-server deployment. For high-availability production deployments, consider implementing:
- Load balancer clusters
- Database clustering/replication
- Multi-region deployment
- Container orchestration (Kubernetes)
