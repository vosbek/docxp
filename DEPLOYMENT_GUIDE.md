# DocXP Deployment Guide
**Enterprise Conversational Code Decomposition Platform**

---

## 🎯 Quick Start (Minimum Viable Deployment)

### **Prerequisites**
- Python 3.11+
- Git access to the DocXP repository
- Basic file system permissions

### **5-Minute Setup**
```bash
# 1. Clone the repository
git clone <repository-url> docxp
cd docxp

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run the simple test to validate core functionality
cd backend
python simple_golden_path_test.py

# 4. If test passes, you're ready for basic usage!
```

---

## 🏗 **Full Production Deployment**

### **Step 1: Environment Setup**

#### **Python Environment**
```bash
# Create virtual environment
python -m venv docxp-env
source docxp-env/bin/activate  # Linux/Mac
# or
docxp-env\Scripts\activate     # Windows

# Install dependencies
pip install -r backend/requirements.txt
```

#### **Environment Configuration**
Create a `.env` file in the `backend` directory:

```env
# Core Application
APP_NAME=DocXP
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///./docxp.db

# Neo4j Knowledge Graph (Optional - graceful degradation if not available)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j
NEO4J_ENABLED=true

# Redis (Optional - graceful degradation if not available)
REDIS_URL=redis://localhost:6379
RQ_REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true

# File Processing
MAX_CONCURRENT_REPOS=4
BATCH_SIZE=50
MAX_WORKERS=4
PROCESSING_TIMEOUT=600

# Vector Database (Optional)
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=./data/vector_db
VECTOR_DB_ENABLED=true

# AWS Bedrock (Optional)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

### **Step 2: Infrastructure Services (Optional)**

#### **Neo4j Knowledge Graph**
```bash
# Using Docker
docker run -d \
  --name docxp-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:latest

# Or install locally following Neo4j documentation
```

#### **Redis Cache/Queue**
```bash
# Using Docker
docker run -d \
  --name docxp-redis \
  -p 6379:6379 \
  redis:latest

# Or install locally following Redis documentation
```

### **Step 3: Application Startup**

#### **Basic Validation**
```bash
cd backend
python simple_golden_path_test.py
```

#### **Full Application Server**
```bash
# Start the FastAPI server (when implemented)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or use the application directly
python -m app.main
```

---

## 🔧 **Configuration Options**

### **Deployment Modes**

#### **1. Minimal Mode (No External Dependencies)**
- SQLite database only
- No Neo4j or Redis
- Local file processing
- Perfect for development and small projects

#### **2. Standard Mode (Recommended)**
- SQLite or PostgreSQL database
- Neo4j knowledge graph
- Redis for caching and queues
- Full feature set available

#### **3. Enterprise Mode**
- PostgreSQL database
- Neo4j cluster
- Redis cluster
- AWS Bedrock integration
- High availability configuration

### **Feature Flags**
```env
# Enable/disable major features
NEO4J_ENABLED=true          # Knowledge graph functionality
REDIS_ENABLED=true          # Caching and background jobs
VECTOR_DB_ENABLED=true      # Vector search capabilities
ENABLE_DB_ANALYSIS=true     # External database analysis
```

---

## 📊 **Validation & Testing**

### **Core Functionality Test**
```bash
cd backend
python simple_golden_path_test.py
```

**Expected Output:**
```
============================================================
DOCXP SIMPLE GOLDEN PATH TEST RESULTS
============================================================
Overall Status: PASSED
Tests Passed: 4
Tests Failed: 0

[SUCCESS] Simple Golden Path Test PASSED!
```

### **Advanced Integration Test**
```bash
# Full integration test (requires all services)
python golden_path_integration_test.py
```

### **Service Health Checks**
```bash
# Check individual services
python -c "
from app.services.knowledge_graph_service import get_knowledge_graph_service
from app.services.project_coordinator_service import get_project_coordinator_service
import asyncio

async def health_check():
    try:
        kg = await get_knowledge_graph_service()
        print('✅ Knowledge Graph Service: Ready')
    except Exception as e:
        print(f'⚠️ Knowledge Graph Service: {e}')
    
    try:
        pc = await get_project_coordinator_service()
        print('✅ Project Coordinator Service: Ready')
    except Exception as e:
        print(f'⚠️ Project Coordinator Service: {e}')

asyncio.run(health_check())
"
```

---

## 🚀 **Usage Examples**

### **Analyze a Repository**
```python
from app.workers.repository_analysis_worker import analyze_repository
import asyncio

async def analyze_my_repo():
    result = await analyze_repository(
        repository_id="my-repo-1",
        project_id="my-project-1",
        analysis_type="full",
        local_path="/path/to/my/repository"
    )
    print(f"Analysis completed: {result['status']}")
    print(f"Files analyzed: {result['files_analyzed']}")
    print(f"Business rules discovered: {result['business_rules_discovered']}")

asyncio.run(analyze_my_repo())
```

### **Create a Project**
```python
from app.services.project_coordinator_service import get_project_coordinator_service
import asyncio

async def create_project():
    coordinator = await get_project_coordinator_service()
    
    project_id = await coordinator.create_project(
        name="Legacy System Modernization",
        description="Modernize legacy Struts application to Spring Boot",
        repository_ids=["repo1", "repo2", "repo3"],
        modernization_goals={
            "target_framework": "Spring Boot",
            "target_database": "PostgreSQL",
            "target_ui": "React"
        },
        business_sponsor="CTO",
        technical_lead="Senior Architect"
    )
    
    print(f"Created project: {project_id}")

asyncio.run(create_project())
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Import Errors**
```bash
# Ensure you're in the backend directory
cd backend

# Ensure Python path is correct
export PYTHONPATH=.

# Or on Windows
set PYTHONPATH=.
```

#### **Database Errors**
```bash
# SQLite permissions
chmod 755 .
chmod 664 docxp.db

# PostgreSQL connection
# Check connection string in .env file
```

#### **Neo4j Connection Issues**
```bash
# Check if Neo4j is running
curl http://localhost:7474

# Check authentication
# Verify NEO4J_PASSWORD in .env matches Neo4j setup
```

#### **Redis Connection Issues**
```bash
# Check if Redis is running
redis-cli ping

# Should return: PONG
```

### **Graceful Degradation**
DocXP is designed to work even when external services are unavailable:

- **No Neo4j**: Knowledge graph features disabled, basic analysis continues
- **No Redis**: Background jobs run synchronously, caching disabled
- **No AWS**: Local embeddings used instead of Bedrock

### **Log Analysis**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Or in .env file
LOG_LEVEL=DEBUG

# Check logs
tail -f logs/docxp.log
```

---

## 📈 **Performance Optimization**

### **For Large Repositories**
```env
# Increase processing limits
MAX_CONCURRENT_REPOS=8
BATCH_SIZE=100
MAX_WORKERS=8
PROCESSING_TIMEOUT=1200

# Optimize database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/docxp
```

### **For High Volume**
```env
# Enable caching
REDIS_ENABLED=true
VECTOR_DB_ENABLED=true

# Use cluster mode for Neo4j and Redis
NEO4J_URI=neo4j+s://cluster.example.com:7687
REDIS_URL=redis-cluster://cluster.example.com:6379
```

---

## 🔒 **Security Considerations**

### **Production Checklist**
- [ ] Change default passwords for Neo4j and Redis
- [ ] Use environment variables for all sensitive data
- [ ] Enable authentication for all services
- [ ] Configure firewall rules for service ports
- [ ] Use TLS/SSL for all connections
- [ ] Regular security updates for all dependencies

### **Environment Variables Security**
```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use system environment variables in production
export NEO4J_PASSWORD="secure-password"
export REDIS_PASSWORD="secure-password"
```

---

## 📞 **Support & Next Steps**

### **Validation Complete**
If the simple golden path test passes, you have a working DocXP installation ready for:
- Repository analysis
- Business rule discovery
- Architectural insight generation
- Project coordination

### **Phase 2 Development**
With a working Phase 1 installation, you're ready to begin Phase 2 development:
- Business Rule Engine (Week 7)
- Advanced Query Interface (Week 8)
- Insight Generation System (Week 9-10)

### **Get Help**
- Check the troubleshooting section above
- Review log files for specific error messages
- Validate your configuration against the examples provided

---

*Last Updated: 2025-08-18*  
*Version: Phase 1 Complete*