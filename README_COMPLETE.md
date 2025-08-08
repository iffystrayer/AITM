# AITM - AI-Powered Threat Modeler

An automated threat modeling system that leverages AI agents and the MITRE ATT&CK framework to identify, analyze, and mitigate cybersecurity threats.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized AI agents for different aspects of threat modeling
- **MITRE ATT&CK Integration**: Comprehensive mapping to ATT&CK techniques and tactics  
- **Multiple LLM Support**: Dynamic selection between OpenAI, Google Gemini, Ollama, and LiteLLM
- **Automated Analysis**: End-to-end threat modeling from system description to recommendations
- **Modern Tech Stack**: FastAPI backend with Svelte frontend
- **Containerized Deployment**: Docker support for easy deployment

## 🏗️ Architecture

### Backend (FastAPI + Langgraph)
- **System Analyst Agent**: Identifies assets, technologies, and entry points
- **ATT&CK Mapper Agent**: Maps system components to MITRE ATT&CK techniques
- **Control Evaluation Agent**: Assesses existing security controls and gaps
- **Master Orchestrator**: Coordinates the multi-agent workflow

### Frontend (Svelte + TailwindCSS)
- Project management interface
- Real-time analysis progress tracking
- Interactive threat model visualization
- Comprehensive reporting dashboard

### Monitoring & Observability
- **Langsmith**: LLM call tracking and debugging
- **Structured Logging**: JSON-formatted application logs
- **API Documentation**: Auto-generated OpenAPI docs

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Development Setup

1. **Clone and navigate to the project**:
   ```bash
   cd /Users/ifiokmoses/code/AITM
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start development environment**:
   ```bash
   ./start-dev.sh
   ```

This script will:
- Create Python virtual environment
- Install all dependencies
- Start backend on port **38527**
- Start frontend on port **41241**

### Access Points
- **Frontend UI**: http://127.0.0.1:41241
- **Backend API**: http://127.0.0.1:38527
- **API Documentation**: http://127.0.0.1:38527/docs

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

```env
# Database
DATABASE_URL=sqlite:///./aitm.db

# Ports (NEVER use 3000 or 8000)
BACKEND_PORT=38527
FRONTEND_PORT=41241

# LLM Providers (configure at least one)
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_PROVIDER=google

# Monitoring
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=aitm-development

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key
```

### LLM Provider Setup

The system supports multiple LLM providers with automatic fallback:

1. **Google Gemini** (Recommended for MVP)
   - Get API key from Google AI Studio
   - Set `GOOGLE_API_KEY` in `.env`

2. **OpenAI**
   - Get API key from OpenAI
   - Set `OPENAI_API_KEY` in `.env`

3. **Ollama** (Local models)
   - Install Ollama locally
   - Start Ollama service
   - Models will be downloaded automatically

4. **LiteLLM** (Unified API)
   - Supports various providers
   - Set `LITELLM_API_KEY` in `.env`

## 📖 Usage

### 1. Create a Threat Modeling Project

```bash
curl -X POST "http://127.0.0.1:38527/api/v1/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Web Application",
    "description": "E-commerce web application threat model"
  }'
```

### 2. Add System Description

```bash
curl -X POST "http://127.0.0.1:38527/api/v1/projects/1/inputs" \
  -H "Content-Type: application/json" \
  -d '{
    "input_type": "text",
    "content": "A web application running on AWS with React frontend, Node.js backend, PostgreSQL database, and Redis cache. Users can register, login, browse products, and make purchases. Payment processing via Stripe API."
  }'
```

### 3. Start Threat Modeling Analysis

```bash
curl -X POST "http://127.0.0.1:38527/api/v1/threat-modeling/1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_provider": "google",
    "analysis_depth": "standard",
    "include_mitigations": true
  }'
```

### 4. Check Analysis Status

```bash
curl "http://127.0.0.1:38527/api/v1/threat-modeling/1/status"
```

### 5. Get Results

```bash
# Get attack paths
curl "http://127.0.0.1:38527/api/v1/threat-modeling/1/results/attack-paths"

# Get recommendations
curl "http://127.0.0.1:38527/api/v1/threat-modeling/1/results/recommendations"

# Get full summary
curl "http://127.0.0.1:38527/api/v1/threat-modeling/1/results/summary"
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### API Testing
```bash
# Test health endpoint
curl http://127.0.0.1:38527/health

# View API documentation
open http://127.0.0.1:38527/docs
```

## 📁 Project Structure

```
AITM/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration, database
│   │   ├── models/         # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── tests/              # Backend tests
│   ├── Dockerfile          # Backend container
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/     # Svelte components
│   │   ├── routes/         # SvelteKit routes
│   │   ├── stores/         # State management
│   │   └── utils/          # Frontend utilities
│   ├── Dockerfile          # Frontend container
│   └── package.json        # Node dependencies
├── docs/                   # Documentation
├── docker-compose.yml      # Multi-container setup
├── start-dev.sh           # Development startup script
└── README.md              # This file
```

## 🔒 Security Notes

- Change default JWT secret in production
- Use environment variables for API keys
- Enable HTTPS in production
- Regularly update dependencies
- Monitor LLM usage and costs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Commit with conventional commits
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🆘 Support

- 📖 Documentation: `/docs`
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

**Built with ❤️ using FastAPI, Svelte, and AI**
