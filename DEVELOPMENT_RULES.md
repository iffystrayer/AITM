# AITM Development Rules and Preferences

## Technology Stack Requirements

### Backend
- **Framework**: FastAPI
- **Agent Framework**: Langgraph for multi-agent orchestration
- **Database**: SQLite for development, consider PostgreSQL/other for production
- **LLM Integration**: Support multiple providers with dynamic selection:
  - Gemini
  - Ollama (for local models)
  - LiteLLM (for provider abstraction)
  - OpenAI
  - Should allow dynamic selection based on availability

### Frontend
- **Framework**: Svelte
- **Build Tool**: Vite

### Port Configuration
- **CRITICAL**: Never use ports 3000 or 8000
- **Always use unique 5-digit port numbers** (10000-65535)
- Update CORS configuration when ports change
- Example: Backend 30641, Frontend 58533

### Database
- **Development**: SQLite for simplicity and quick setup
- **Production**: Consider scaling with PostgreSQL, MongoDB, or other suitable databases

### Deployment
- **Containerization**: Docker for all services
- **Orchestration**: Docker Compose for development

### Monitoring & Observability
- **LLM Monitoring**: Langsmith for LLM call tracking and debugging
- **Application Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with JSON format
- **Tracing**: OpenTelemetry for distributed tracing

### Development Practices
- **Version Control**: Always commit changes immediately after completing features
- **Testing**: Include unit tests and integration tests
- **Documentation**: Maintain comprehensive API documentation
- **Security**: Implement proper authentication and input validation from the start

## MVP Architecture Priorities

1. **Core Agent System**: Master Orchestrator + 2-3 key agents (SAA, AMA, CEA)
2. **Basic UI**: Simple threat modeling project creation and results display
3. **Essential APIs**: Project CRUD, threat modeling initiation, results retrieval
4. **LLM Integration**: Basic integration with at least 2 providers
5. **MITRE ATT&CK**: Basic knowledge base integration
6. **Minimal Viable Features**: End-to-end threat modeling workflow

## File Structure Requirements

```
AITM/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   ├── routes/
│   │   └── components/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── docs/
└── scripts/
```

## Environment Variables Template

```env
# LLM Providers
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434
LITELLM_API_KEY=your_key_here

# Monitoring
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT=aitm-development

# Database
DATABASE_URL=sqlite:///./aitm.db

# Ports (Update these to unique 5-digit numbers)
BACKEND_PORT=30641
FRONTEND_PORT=58533

# Security
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
```
