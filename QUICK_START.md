# 🚀 AITM Quick Start Guide

## ✅ Current Status
- [x] Docker environment set up and running
- [x] Backend API healthy at http://localhost:38527
- [x] Frontend UI accessible at http://localhost:41241
- [x] CORS configured and working
- [x] Basic project structure in place

## 🎯 Ready to Start Development!

### **Option 1: LLM Service First (Recommended)**
**Why:** Core foundation for all AI agents
**Time:** 4-6 hours
**Impact:** Enables all other agent development

```bash
# Start here for robust multi-LLM integration
cd /Users/ifiokmoses/code/AITM
# Follow DEVELOPMENT_PLAN.md > Phase 1 > Task 1
```

**What you'll build:**
- Multi-provider LLM client (OpenAI, Anthropic, Gemini, Ollama)
- Rate limiting and retry mechanisms  
- Prompt template system
- Token usage tracking

### **Option 2: System Analyst Agent**
**Why:** First complete AI agent for system analysis
**Time:** 6-8 hours
**Impact:** Core threat modeling capability

**What you'll build:**
- Parse system descriptions
- Identify assets and components
- Detect technologies and architecture
- Generate structured analysis output

### **Option 3: Frontend Project Management**
**Why:** User interface for project creation and management
**Time:** 6-8 hours  
**Impact:** Complete user workflow

**What you'll build:**
- Project CRUD interface
- System input forms
- File upload capabilities
- Basic navigation

### **Option 4: MITRE ATT&CK Integration**
**Why:** Knowledge base for attack technique mapping
**Time:** 6-8 hours
**Impact:** Core security intelligence

**What you'll build:**
- ATT&CK data ingestion
- Technique search and mapping
- Mitigation recommendations
- Relationship queries

## 🛠️ Development Commands

### Start Development Environment
```bash
./docker-dev.sh up       # Start all containers
./docker-dev.sh logs     # View all logs  
./docker-dev.sh status   # Check container status
```

### Backend Development
```bash
./docker-dev.sh exec backend bash           # Access backend container
./docker-dev.sh exec backend python -m pytest  # Run tests
./docker-dev.sh restart backend            # Restart after major changes
```

### Frontend Development  
```bash
./docker-dev.sh exec frontend bash         # Access frontend container
./docker-dev.sh exec frontend npm test     # Run frontend tests
./docker-dev.sh restart frontend          # Restart after config changes
```

### Quick API Tests
```bash
# Test backend health
curl http://localhost:38527/health

# Test API documentation  
open http://localhost:38527/docs

# Test frontend
open http://localhost:41241
```

## 🔑 Environment Setup

### 1. Configure API Keys (Required for LLM Service)
```bash
# Edit .env file in project root
OPENAI_API_KEY=sk-your-openai-key           # Optional: For GPT-4/4o
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key # Optional: For Claude
GOOGLE_API_KEY=your-gemini-key              # Optional: For Gemini
OLLAMA_BASE_URL=http://localhost:11434      # Optional: For local models
```

### 2. Install Additional Dependencies (as needed)
```bash
# Backend: Add to requirements.txt and rebuild
./docker-dev.sh exec backend pip install openai anthropic google-generativeai

# Frontend: Add packages and rebuild
./docker-dev.sh exec frontend npm install lucide-svelte
```

## 📚 Documentation Links

- **[DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md)** - Complete 5-week development roadmap
- **[IMMEDIATE_TASKS.md](./IMMEDIATE_TASKS.md)** - Detailed 7-day implementation guide  
- **[Software Engineering Spec](./Software%20Engineering%20Specification%20AI-Powered%20Threat%20Modeler%20%28AITM%29.md)** - Full system specification
- **[API Docs](http://localhost:38527/docs)** - Interactive API documentation
- **[Docker README](./README-DOCKER.md)** - Docker setup and management

## 🎯 Success Targets

### Week 1 Goals:
- [ ] LLM service calling multiple providers
- [ ] System Analyst Agent analyzing sample systems
- [ ] Basic frontend project creation working
- [ ] MITRE ATT&CK data integrated and searchable

### Week 2 Goals:  
- [ ] Complete threat modeling workflow (input → analysis → results)
- [ ] Attack path generation using ATT&CK techniques
- [ ] Basic recommendations engine
- [ ] Results visualization in frontend

### MVP Complete Goals:
- [ ] End-to-end threat modeling for sample system
- [ ] Multi-agent analysis producing structured results
- [ ] User-friendly interface for non-technical users
- [ ] Export capabilities (PDF, JSON, CSV)
- [ ] Performance under 15 minutes for medium systems

## 🚨 Common Issues & Solutions

### Backend Won't Start:
```bash
./docker-dev.sh logs backend              # Check error logs
./docker-dev.sh rebuild backend           # Rebuild if dependency issues
```

### Frontend Build Errors:
```bash
./docker-dev.sh logs frontend            # Check build errors
./docker-dev.sh exec frontend npm install # Reinstall dependencies
```

### Database Issues:
```bash
./docker-dev.sh exec backend alembic upgrade head  # Run migrations
./docker-dev.sh volume prune              # Reset database (destructive)
```

### API Connection Issues:
```bash
# Check CORS settings in backend/app/main.py
# Verify containers can reach each other:
./docker-dev.sh exec frontend ping backend
```

## 🎯 Next Steps

**Immediate (Next 30 minutes):**
1. Choose your starting point from the options above
2. Set up any required API keys in `.env`
3. Review the relevant section in DEVELOPMENT_PLAN.md
4. Start coding!

**Today's Goal:**
- Pick one component and make meaningful progress
- Get basic functionality working end-to-end
- Write a few tests to validate implementation

**This Week's Goal:**
- Complete 2-3 major components
- Have basic threat modeling workflow functional
- Prepare for user testing with sample systems

## 💡 Development Tips

1. **Start Simple:** Begin with basic functionality, add complexity later
2. **Test Early:** Write tests as you develop, not afterward
3. **Use Git:** Commit frequently with descriptive messages  
4. **Documentation:** Update docs as you implement features
5. **Performance:** Focus on correctness first, optimization later

---

**Ready to build the future of threat modeling? 🛡️**

Choose your starting point and let's create an amazing AI-powered security tool!
