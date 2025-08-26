# DocXP Quick Deployment Guide
**For Target Machine with Existing Infrastructure**

---

## 🎯 **Prerequisites Already Available on Target Machine**
✅ **npm, node** - Ready for frontend  
✅ **github, git** - Ready for repository access  
✅ **podman** - Ready for containerized services  
✅ **aws profile (msh)** - Ready for Bedrock integration  

---

## 🚀 **5-Minute Deployment**

### **Option 1: Automated Setup (Recommended)**

#### **Linux/Mac:**
```bash
# Clone and run automated setup
git clone https://github.com/your-org/docxp.git
cd docxp
./setup.sh
```

#### **Windows:**
```cmd
# Clone and run automated setup
git clone https://github.com/your-org/docxp.git
cd docxp
setup.bat
```

### **Option 2: Manual Setup**

#### **Step 1: Clone and Setup**
```bash
# Clone the repository
git clone https://github.com/your-org/docxp.git
cd docxp

# Setup Python environment
python -m venv docxp-env
source docxp-env/bin/activate  # Linux/Mac
# OR on Windows:
# docxp-env\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

#### **Step 2: Quick Validation Test**
```bash
# Run the golden path test to validate core functionality
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

✅ **If test passes, DocXP is ready for basic use!**

---

## 🐳 **Optional: Enhanced Setup with Podman**

Since you have **podman** available, you can easily add the optional services:

### **Neo4j Knowledge Graph**
```bash
# Start Neo4j using podman
podman run -d \
  --name docxp-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/docxp-2024 \
  neo4j:latest

# Verify Neo4j is running
curl http://localhost:7474
```

### **Redis Cache/Queue**
```bash
# Start Redis using podman
podman run -d \
  --name docxp-redis \
  -p 6379:6379 \
  redis:latest

# Verify Redis is running
podman exec docxp-redis redis-cli ping
# Should return: PONG
```

### **Optional: Environment Configuration**
If you want to use the enhanced services, create `backend/.env`:

```env
# Core Application
APP_NAME=DocXP
DEBUG=false

# Neo4j Knowledge Graph
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=docxp-2024
NEO4J_ENABLED=true

# Redis Cache/Queue
REDIS_URL=redis://localhost:6379
RQ_REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true

# AWS Bedrock (using your existing 'msh' profile)
AWS_PROFILE=msh
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Processing Configuration
MAX_CONCURRENT_REPOS=4
BATCH_SIZE=50
MAX_WORKERS=4
```

---

## 🧪 **Validation & Testing**

### **Core Functionality Test**
```bash
cd backend
python simple_golden_path_test.py
```

### **Service Health Check**
```bash
# Test all services
python -c "
import asyncio
from app.services.knowledge_graph_service import get_knowledge_graph_service
from app.services.project_coordinator_service import get_project_coordinator_service

async def health_check():
    print('🔍 Checking DocXP Services...')
    
    try:
        kg = await get_knowledge_graph_service()
        print('✅ Knowledge Graph Service: Ready')
    except Exception as e:
        print(f'⚠️  Knowledge Graph Service: {e}')
    
    try:
        pc = await get_project_coordinator_service()
        print('✅ Project Coordinator Service: Ready')
    except Exception as e:
        print(f'⚠️  Project Coordinator Service: {e}')
    
    print('🎉 DocXP is ready for enterprise use!')

asyncio.run(health_check())
"
```

---

## 🚀 **Usage Examples**

### **Analyze a Local Repository**
```python
# Create analyze_repo.py
import asyncio
from app.workers.repository_analysis_worker import analyze_repository

async def analyze_my_repo():
    result = await analyze_repository(
        repository_id="my-legacy-app",
        project_id="modernization-project-1",
        analysis_type="full",
        local_path="/path/to/your/legacy/repository"
    )
    
    print(f"Analysis Status: {result['status']}")
    print(f"Files Analyzed: {result.get('files_analyzed', 0)}")
    print(f"Business Rules Discovered: {result.get('business_rules_discovered', 0)}")
    print(f"Insights Generated: {result.get('insights_generated', 0)}")

# Run the analysis
asyncio.run(analyze_my_repo())
```

```bash
# Run the analysis
python analyze_repo.py
```

### **Create an Enterprise Project**
```python
# Create project.py
import asyncio
from app.services.project_coordinator_service import get_project_coordinator_service

async def create_modernization_project():
    coordinator = await get_project_coordinator_service()
    
    project_id = await coordinator.create_project(
        name="Legacy Banking System Modernization",
        description="Modernize legacy Struts/CORBA banking application to Spring Boot/GraphQL",
        repository_ids=["banking-core", "banking-ui", "banking-services"],
        modernization_goals={
            "target_framework": "Spring Boot 3.x",
            "target_database": "PostgreSQL",
            "target_ui": "React + GraphQL",
            "target_integration": "REST APIs"
        },
        business_sponsor="CTO",
        technical_lead="Senior Architect",
        created_by="DocXP User"
    )
    
    print(f"✅ Created modernization project: {project_id}")
    
    # Get project status
    status = await coordinator.get_project_status(project_id)
    print(f"📊 Project Status: {status.get('status', 'unknown')}")
    print(f"📁 Repositories: {status.get('repositories', {}).get('total', 0)}")

asyncio.run(create_modernization_project())
```

```bash
# Run project creation
python project.py
```

---

## 🔧 **Podman Management Commands**

### **Start All Services**
```bash
# Start all DocXP services
podman start docxp-neo4j docxp-redis

# Check status
podman ps
```

### **Stop All Services**
```bash
# Stop all DocXP services
podman stop docxp-neo4j docxp-redis
```

### **View Logs**
```bash
# View Neo4j logs
podman logs docxp-neo4j

# View Redis logs
podman logs docxp-redis
```

### **Remove Services (if needed)**
```bash
# Remove containers (data will be lost)
podman rm -f docxp-neo4j docxp-redis
```

---

## ⚡ **Performance Tips for Your Environment**

### **Optimized Configuration**
Since your machine likely has good resources, you can increase performance:

```env
# Enhanced performance settings
MAX_CONCURRENT_REPOS=8
BATCH_SIZE=100
MAX_WORKERS=8
PROCESSING_TIMEOUT=1200

# Memory optimization
NEO4J_MAX_CONNECTION_POOL_SIZE=100
REDIS_ENABLED=true
```

### **AWS Bedrock Integration**
With your existing AWS profile (msh):

```bash
# Verify AWS profile
aws sts get-caller-identity --profile msh

# Test Bedrock access
aws bedrock list-foundation-models --profile msh --region us-east-1
```

---

## 🎯 **Next Steps**

1. **✅ Run the 5-minute deployment above**
2. **🧪 Validate with the golden path test**
3. **🚀 Start analyzing your first repository**
4. **📈 Scale up with podman services as needed**

---

## 🆘 **Quick Troubleshooting**

### **If Golden Path Test Fails**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep -E "(fastapi|sqlalchemy|neo4j|redis)"

# Check file permissions
ls -la backend/simple_golden_path_test.py
```

### **If Podman Services Won't Start**
```bash
# Check podman status
podman info

# Check port availability
netstat -tlnp | grep -E "(7474|7687|6379)"

# View detailed logs
podman logs -f docxp-neo4j
```

### **If AWS Profile Issues**
```bash
# List AWS profiles
aws configure list-profiles

# Test the msh profile
aws sts get-caller-identity --profile msh
```

---

**🎉 You're ready to modernize enterprise legacy systems with DocXP!**

*This guide is optimized for your existing infrastructure (npm, node, github, git, podman, aws profile msh)*