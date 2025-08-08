# 🐳 AITM Docker Development Setup

This guide provides a containerized development environment for AITM using Docker, eliminating system environment issues and ensuring consistent development across different machines.

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (v20.10+)
- **Docker Compose** (v2.0+)
- **Git** for cloning the repository

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd AITM
```

### 2. Environment Configuration

Create your environment file:
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `GOOGLE_API_KEY` - Google Gemini API key (recommended)
- Other LLM provider keys as needed

### 3. Start Development Environment

```bash
# Start all services
./docker-dev.sh start

# Or use docker-compose directly
docker-compose up --build -d
```

## 🎯 Access Points

Once started, you can access:

- **Frontend**: http://localhost:41241
- **Backend API**: http://localhost:38527
- **API Documentation**: http://localhost:38527/docs
- **Health Checks**: 
  - Backend: http://localhost:38527/health
  - Frontend: http://localhost:41241/

## 🛠️ Development Commands

The `docker-dev.sh` script provides convenient commands:

```bash
# Start services in development mode
./docker-dev.sh start

# Stop all services
./docker-dev.sh stop

# View logs (all services)
./docker-dev.sh logs

# View backend logs only
./docker-dev.sh backend

# View frontend logs only
./docker-dev.sh frontend

# Check container status
./docker-dev.sh status

# Rebuild containers from scratch
./docker-dev.sh rebuild

# Open shell in backend container
./docker-dev.sh shell

# Run backend tests
./docker-dev.sh test

# Clean up all containers and volumes
./docker-dev.sh clean
```

## 📁 Project Structure

```
AITM/
├── docker-compose.yml          # Multi-service orchestration
├── docker-dev.sh              # Development helper script
├── .env                       # Environment variables
│
├── backend/
│   ├── Dockerfile             # Backend container config
│   ├── requirements-py313.txt # Python dependencies
│   ├── app/                   # FastAPI application
│   └── data/                  # SQLite database (persisted)
│
└── frontend/
    ├── Dockerfile             # Frontend container config
    ├── package.json           # Node.js dependencies
    └── src/                   # SvelteKit application
```

## 🔧 Development Features

### Hot Reloading
- **Backend**: Python files are auto-reloaded on changes
- **Frontend**: Vite dev server provides instant updates
- **Code changes** are reflected immediately without container rebuilds

### Data Persistence
- **Database**: SQLite data persisted in Docker volume
- **Logs**: Container logs accessible via Docker commands

### Health Monitoring
- **Built-in health checks** for both services
- **Automatic restart** on failures
- **Service dependency management**

## 🐛 Debugging

### View Container Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Enter Container Shell
```bash
# Backend container
./docker-dev.sh shell

# Or directly
docker-compose exec backend /bin/bash
```

### Check Container Status
```bash
./docker-dev.sh status
```

### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
lsof -i :38527  # Backend
lsof -i :41241  # Frontend

# Stop conflicting services or change ports in docker-compose.yml
```

**Container Build Failures**
```bash
# Clean rebuild
./docker-dev.sh rebuild

# Or manually
docker-compose down
docker-compose build --no-cache
```

**Database Issues**
```bash
# Reset database volume
docker-compose down -v
docker-compose up -d
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
./docker-dev.sh test

# Run specific tests
docker-compose exec backend python -m pytest tests/test_specific.py -v
```

### API Testing
- **Interactive docs**: http://localhost:38527/docs
- **Manual testing** with curl or Postman
- **Health endpoint**: http://localhost:38527/health

## 🚢 Production Deployment

For production deployment:

1. **Build production images**:
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Use environment-specific configs**:
   - Separate `.env.production` file
   - Production-optimized Dockerfiles
   - Reverse proxy (nginx) for frontend
   - External database for backend

3. **Security considerations**:
   - Change default JWT secrets
   - Use secrets management
   - Enable HTTPS
   - Restrict CORS origins

## 🎯 Benefits of Docker Setup

1. **Environment Isolation**: No conflicts with system Python/Node
2. **Consistency**: Same environment across all developers
3. **Easy Onboarding**: One-command setup for new developers
4. **Dependency Management**: All dependencies containerized
5. **Easy Cleanup**: Remove everything with one command
6. **Production Parity**: Development mirrors production setup

## 🆘 Need Help?

- **Container issues**: Check `./docker-dev.sh status`
- **Build problems**: Try `./docker-dev.sh rebuild`
- **Clean start**: Use `./docker-dev.sh clean` then `./docker-dev.sh start`

For more detailed logs or debugging, use the individual docker-compose commands directly.
