# DocXP Production Deployment Guide
**Complete Setup - All Services Required**

---

## 🎯 **Production-Ready Installation**
**No graceful degradation - all services operational for full functionality**

This guide ensures **100% functional DocXP** with all services running properly on your target machine.

---

## 📋 **Required Infrastructure**

### **✅ Already Available on Target Machine**
- npm, node (for frontend)
- github, git (for repository access)  
- podman (for containerized services)
- aws profile (msh) (for Bedrock integration)

### **🔧 Services We'll Install**
- **Neo4j Knowledge Graph** (REQUIRED)
- **Redis Cache/Queue** (REQUIRED)
- **PostgreSQL Database** (REQUIRED)
- **Python 3.11+ Environment** (REQUIRED)

---

## 🚀 **Complete Installation Process**

### **Step 1: Clone and Setup Python Environment**
```bash
# Clone repository
git clone https://github.com/your-org/docxp.git
cd docxp

# Create Python environment
python -m venv docxp-env
source docxp-env/bin/activate  # Linux/Mac
# docxp-env\Scripts\activate   # Windows

# Install all dependencies
pip install -r backend/requirements.txt
```

### **Step 2: Start Required Services with Podman**
```bash
# Start Neo4j Knowledge Graph
podman run -d \
  --name docxp-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/docxp-production-2024 \
  -v docxp-neo4j-data:/data \
  neo4j:latest

# Start Redis Cache/Queue
podman run -d \
  --name docxp-redis \
  -p 6379:6379 \
  -v docxp-redis-data:/data \
  redis:latest

# Start PostgreSQL Database  
podman run -d \
  --name docxp-postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=docxp \
  -e POSTGRES_USER=docxp \
  -e POSTGRES_PASSWORD=docxp-production-2024 \
  -v docxp-postgres-data:/var/lib/postgresql/data \
  postgres:15
```

### **Step 3: Verify All Services Are Running**
```bash
# Check all containers are running
podman ps

# Verify Neo4j
curl http://localhost:7474
# Should return Neo4j browser interface

# Verify Redis
podman exec docxp-redis redis-cli ping
# Should return: PONG

# Verify PostgreSQL
podman exec docxp-postgres pg_isready -U docxp
# Should return: accepting connections
```

### **Step 4: Configure Production Environment**
Create `backend/.env` with **production configuration**:

```env
# Production DocXP Configuration
APP_NAME=DocXP
DEBUG=false
APP_ENV=production

# PostgreSQL Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://docxp:docxp-production-2024@localhost:5432/docxp

# Neo4j Knowledge Graph (REQUIRED)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=docxp-production-2024
NEO4J_DATABASE=neo4j
NEO4J_ENABLED=true
NEO4J_MAX_CONNECTION_LIFETIME=300
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60

# Redis Cache/Queue (REQUIRED)
REDIS_URL=redis://localhost:6379
RQ_REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_ENABLED=true

# AWS Bedrock (using your msh profile)
AWS_PROFILE=msh
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Production Performance Settings
MAX_CONCURRENT_REPOS=8
BATCH_SIZE=100
MAX_WORKERS=8
PROCESSING_TIMEOUT=1200

# Vector Database
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=./data/vector_db
VECTOR_DB_ENABLED=true

# File Processing
OUTPUT_DIR=./output
TEMP_DIR=./temp
CONFIGS_DIR=./configs
MAX_FILE_SIZE_MB=500

# Logging
LOG_LEVEL=INFO
```

### **Step 5: Initialize Database Schemas**
```bash
cd backend

# Initialize PostgreSQL tables
python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
print('✅ PostgreSQL database initialized')
"

# Initialize Neo4j indexes and constraints
python -c "
import asyncio
from app.services.knowledge_graph_service import get_knowledge_graph_service
async def init_neo4j():
    kg = await get_knowledge_graph_service()
    await kg.create_indexes()
    print('✅ Neo4j indexes created')
asyncio.run(init_neo4j())
"
```

### **Step 6: Validate Complete Installation**
```bash
# Run comprehensive validation
python -c "
import asyncio
from app.services.knowledge_graph_service import get_knowledge_graph_service
from app.services.project_coordinator_service import get_project_coordinator_service
from app.core.database import get_async_session

async def full_validation():
    print('🔍 Validating Complete DocXP Installation...')
    
    # Test PostgreSQL
    try:
        async with get_async_session() as session:
            await session.execute('SELECT 1')
        print('✅ PostgreSQL: Connected')
    except Exception as e:
        print(f'❌ PostgreSQL: {e}')
        return False
    
    # Test Neo4j
    try:
        kg = await get_knowledge_graph_service()
        stats = await kg.get_graph_statistics()
        print('✅ Neo4j: Connected')
    except Exception as e:
        print(f'❌ Neo4j: {e}')
        return False
    
    # Test Redis
    try:
        pc = await get_project_coordinator_service()
        if pc.redis_client:
            pc.redis_client.ping()
        print('✅ Redis: Connected')
    except Exception as e:
        print(f'❌ Redis: {e}')
        return False
    
    print('🎉 All services operational - DocXP ready for production!')
    return True

result = asyncio.run(full_validation())
if not result:
    print('❌ Validation failed - check service configuration')
    exit(1)
"

# Run golden path test
python simple_golden_path_test.py
```

---

## 🔧 **Service Management Commands**

### **Start All Services**
```bash
#!/bin/bash
# start-docxp.sh

echo "🚀 Starting DocXP Production Services..."

# Start PostgreSQL
podman start docxp-postgres || podman run -d \
  --name docxp-postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=docxp \
  -e POSTGRES_USER=docxp \
  -e POSTGRES_PASSWORD=docxp-production-2024 \
  -v docxp-postgres-data:/var/lib/postgresql/data \
  postgres:15

# Start Neo4j  
podman start docxp-neo4j || podman run -d \
  --name docxp-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/docxp-production-2024 \
  -v docxp-neo4j-data:/data \
  neo4j:latest

# Start Redis
podman start docxp-redis || podman run -d \
  --name docxp-redis \
  -p 6379:6379 \
  -v docxp-redis-data:/data \
  redis:latest

echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ All DocXP services started"
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### **Stop All Services**
```bash
#!/bin/bash
# stop-docxp.sh

echo "🛑 Stopping DocXP Services..."
podman stop docxp-postgres docxp-neo4j docxp-redis
echo "✅ All services stopped"
```

### **Service Health Check**
```bash
#!/bin/bash
# health-check.sh

echo "🔍 DocXP Service Health Check"
echo "=============================="

# Check PostgreSQL
if podman exec docxp-postgres pg_isready -U docxp &>/dev/null; then
    echo "✅ PostgreSQL: Healthy"
else
    echo "❌ PostgreSQL: Not responding"
fi

# Check Neo4j
if curl -s http://localhost:7474 &>/dev/null; then
    echo "✅ Neo4j: Healthy"
else
    echo "❌ Neo4j: Not responding"
fi

# Check Redis
if podman exec docxp-redis redis-cli ping &>/dev/null; then
    echo "✅ Redis: Healthy"
else
    echo "❌ Redis: Not responding"
fi
```

---

## 🚀 **Production Usage Examples**

### **Full Repository Analysis**
```bash
cd backend

# Analyze with all services operational
python -c "
import asyncio
from app.workers.repository_analysis_worker import analyze_repository

async def production_analysis():
    result = await analyze_repository(
        repository_id='production-repo-1',
        project_id='modernization-project-1',
        analysis_type='full',
        local_path='/path/to/your/repository'
    )
    
    print(f'Analysis Status: {result[\"status\"]}')
    print(f'Files Analyzed: {result.get(\"files_analyzed\", 0)}')
    print(f'Business Rules: {result.get(\"business_rules_discovered\", 0)}')
    print(f'Insights Generated: {result.get(\"insights_generated\", 0)}')

asyncio.run(production_analysis())
"
```

### **Enterprise Project Creation**
```bash
cd backend

# Create project with full service integration
python -c "
import asyncio
from app.services.project_coordinator_service import get_project_coordinator_service

async def create_enterprise_project():
    coordinator = await get_project_coordinator_service()
    
    project_id = await coordinator.create_project(
        name='Enterprise Banking Modernization',
        description='Complete modernization of legacy banking systems',
        repository_ids=['banking-core', 'banking-ui', 'banking-api', 'banking-batch'],
        modernization_goals={
            'target_framework': 'Spring Boot 3.x',
            'target_database': 'PostgreSQL',
            'target_ui': 'React + GraphQL',
            'target_cloud': 'AWS',
            'timeline': '18 months',
            'budget': 2000000
        },
        business_sponsor='Chief Technology Officer',
        technical_lead='Principal Architect',
        created_by='DocXP Production System'
    )
    
    print(f'✅ Enterprise project created: {project_id}')
    
    # Start analysis
    await coordinator.start_project_analysis(project_id, 'full')
    print('🚀 Project analysis started')

asyncio.run(create_enterprise_project())
"
```

---

## 🔒 **Production Security Configuration**

### **Secure Service Passwords**
```bash
# Generate secure passwords
NEO4J_PASSWORD=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Update .env file with secure passwords
sed -i "s/NEO4J_PASSWORD=.*/NEO4J_PASSWORD=${NEO4J_PASSWORD}/" backend/.env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" backend/.env
```

### **Network Security**
```bash
# Create dedicated network for DocXP services
podman network create docxp-network

# Restart services on dedicated network
podman stop docxp-postgres docxp-neo4j docxp-redis
podman rm docxp-postgres docxp-neo4j docxp-redis

# Restart with network isolation
# (Update container commands to include --network docxp-network)
```

---

## 📊 **Production Monitoring**

### **Service Monitoring Script**
```bash
#!/bin/bash
# monitor-docxp.sh

while true; do
    echo "$(date): Checking DocXP Services..."
    
    # Check each service
    ./health-check.sh
    
    # Log results
    echo "$(date): Health check completed" >> /var/log/docxp-health.log
    
    # Wait 5 minutes
    sleep 300
done
```

### **Performance Metrics**
```bash
cd backend

# Get system performance metrics
python -c "
import asyncio
from app.services.knowledge_graph_service import get_knowledge_graph_service
from app.services.project_coordinator_service import get_project_coordinator_service

async def get_metrics():
    # Neo4j stats
    kg = await get_knowledge_graph_service()
    neo4j_stats = await kg.get_graph_statistics()
    print(f'Neo4j Nodes: {neo4j_stats.get(\"total_nodes\", 0)}')
    print(f'Neo4j Relationships: {neo4j_stats.get(\"total_relationships\", 0)}')
    
    # Project stats
    pc = await get_project_coordinator_service()
    projects = await pc.list_active_projects()
    print(f'Active Projects: {len(projects)}')

asyncio.run(get_metrics())
"
```

---

## ✅ **Production Checklist**

### **Pre-Deployment**
- [ ] All services (PostgreSQL, Neo4j, Redis) running
- [ ] Secure passwords configured
- [ ] Environment variables set
- [ ] Database schemas initialized
- [ ] Network security configured

### **Post-Deployment**
- [ ] Full validation test passes
- [ ] All service health checks green
- [ ] Performance monitoring active
- [ ] Backup procedures in place
- [ ] Log rotation configured

### **Operational**
- [ ] Service management scripts created
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Support procedures established

---

## 🎯 **Success Criteria**

**DocXP is production-ready when:**
1. ✅ All services (PostgreSQL, Neo4j, Redis) operational
2. ✅ Full validation test passes without errors
3. ✅ Repository analysis completes successfully
4. ✅ Project creation and management functional
5. ✅ Knowledge graph queries return results
6. ✅ AWS Bedrock integration working
7. ✅ Performance meets enterprise requirements

---

**🎉 Complete Production Setup - No Compromises, Full Functionality!**

*This guide ensures 100% operational DocXP with all enterprise features enabled.*