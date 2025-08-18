# DocXP Enterprise Setup Guide

## Complete Setup Process for Production Machine

This guide provides step-by-step instructions for setting up DocXP on a machine with proper administrator access.

---

## 🚀 **Prerequisites**

### System Requirements
- **OS**: Windows 10/11 or Linux (Ubuntu 20.04+)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB+ free space
- **Network**: Internet access for AWS Bedrock

### Required Software
- **Podman Desktop** (with admin rights) or **Docker Desktop**
- **Python 3.10+**
- **Git**
- **AWS CLI** (configured with Bedrock access)

---

## 📦 **Step 1: Infrastructure Setup**

### 1.1 Clone Repository
```bash
git clone <repository-url>
cd docxp
```

### 1.2 Configure Environment
```bash
# Copy and configure environment
cp .env.example .env

# Edit .env with your AWS credentials
# Required variables:
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
```

### 1.3 Start Infrastructure Services
```bash
# Start all services (requires admin rights)
podman-compose -f podman-compose.yml up -d

# Or start core services only
podman-compose -f podman-compose.yml up -d neo4j postgres redis opensearch minio
```

### 1.4 Verify Service Health
```bash
# Check all services are running
podman ps

# Should see 5 containers:
# - docxp-neo4j (ports 7474, 7687)
# - docxp-postgres (port 5432)
# - docxp-redis (port 6379)
# - docxp-opensearch (ports 9200, 9600)
# - docxp-minio (ports 9000, 9001)
```

---

## 🧪 **Step 2: Service Verification**

### 2.1 Run Connectivity Tests
```bash
# Run comprehensive service tests
python test_services.py

# Expected output:
# ✅ Neo4j Knowledge Graph: Neo4j connection successful
# ✅ Redis Cache & Queue: Redis connection successful  
# ✅ OpenSearch Hybrid Search: OpenSearch connection successful
# ✅ PostgreSQL Database: PostgreSQL connection successful
```

### 2.2 Manual Service Checks
```bash
# Test Neo4j Browser
# Open: http://localhost:7474
# Login: neo4j / docxp-neo4j-2024

# Test OpenSearch
curl -X GET "localhost:9200/_cluster/health"

# Test PostgreSQL
podman exec -it docxp-postgres psql -U docxp_user -d docxp -c "SELECT current_user;"

# Test Redis
podman exec -it docxp-redis redis-cli ping

# Test MinIO Console
# Open: http://localhost:9001
# Login: docxp-root / docxp-local-dev-2024
```

---

## 🔧 **Step 3: Initialize Knowledge Graph**

### 3.1 Run Graph Schema Migration
```bash
cd backend
python -c "
import asyncio
from app.services.graph_migration_service import GraphMigrationService

async def setup():
    migration = GraphMigrationService()
    await migration.setup_initial_schema()
    print('✅ Neo4j schema initialized')

asyncio.run(setup())
"
```

### 3.2 Verify Graph Setup
```bash
# Test graph service
python -c "
import asyncio
from app.services.knowledge_graph_service import get_knowledge_graph_service

async def test():
    kg = await get_knowledge_graph_service()
    stats = await kg.get_graph_statistics()
    print(f'✅ Graph stats: {stats}')

asyncio.run(test())
"
```

---

## 🚀 **Step 4: Start Application**

### 4.1 Start Backend API
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 Start RQ Workers (separate terminal)
```bash
cd backend
python -m rq worker --url redis://localhost:6379/1 docxp_jobs
```

### 4.3 Verify Application
```bash
# Test API health
curl http://localhost:8000/health

# Test detailed health
curl http://localhost:8000/health/detailed
```

---

## 📋 **Week 1 Acceptance Criteria Verification**

### ✅ **Task 1.1: Neo4j Integration Setup**
- [ ] **Neo4j running and accessible via UI (localhost:7474)**
  ```bash
  # Open browser: http://localhost:7474
  # Login: neo4j / docxp-neo4j-2024
  # Should see Neo4j Browser interface
  ```

- [ ] **Graph service can create nodes and relationships**
  ```bash
  cd backend
  python -c "
  import asyncio
  from app.services.knowledge_graph_service import KnowledgeGraphService, GraphNode, NodeType

  async def test():
      kg = KnowledgeGraphService()
      await kg.connect()
      
      # Create test node
      node = GraphNode(
          id='test_acceptance',
          node_type=NodeType.CODE_ENTITY,
          properties={'name': 'acceptance_test', 'type': 'verification'}
      )
      
      success = await kg.create_node(node)
      print(f'✅ Node creation: {success}')
      
      await kg.disconnect()

  asyncio.run(test())
  "
  ```

- [ ] **Basic schema created with core entity types**
  ```cypher
  # In Neo4j Browser (http://localhost:7474), run:
  CALL db.constraints();
  CALL db.indexes();
  
  # Should see constraints for:
  # - CodeEntity(id)
  # - BusinessRule(id) 
  # - Repository(id)
  # - TechnologyComponent(name)
  ```

- [ ] **Sync service successfully imports existing PostgreSQL data**
  ```bash
  cd backend
  python -c "
  import asyncio
  from app.services.graph_sync_service import get_graph_sync_service

  async def test():
      sync = await get_graph_sync_service()
      await sync.sync_repositories_to_graph()
      print('✅ Repository sync completed')

  asyncio.run(test())
  "
  ```

---

## 📈 **Week 2: Business Rule Data Models Implementation**

### **Task 2.1: Enhanced Business Rule Models**

#### Create BusinessRuleTrace Model
```bash
# File: backend/app/models/business_rule_trace.py
```

#### Implementation Steps:
1. **Create dedicated file for BusinessRuleTrace**
2. **Implement FlowStep model with technology stack tracking**
3. **Add SQLAlchemy models for persistence**
4. **Create Pydantic schemas for API serialization**

### **Task 2.2: Business Domain Classification**

#### Create Domain Taxonomy
```bash
# File: backend/app/models/business_domains.py
```

#### Implementation Steps:
1. **Define hierarchical domain structure**
2. **Create predefined business domains (Claims, Payments, etc.)**
3. **Implement domain classification service using Bedrock**
4. **Add confidence scoring and manual override capabilities**

### **Task 2.3: Knowledge Persistence Strategy**

#### Create ArchitecturalInsight Model
1. **Implement insight categorization (risk, recommendation, pattern)**
2. **Link insights to business rules and components**
3. **Add modernization impact assessment**
4. **Create architect notes and confidence tracking**

---

## 🔄 **Data Synchronization Workflow**

### Current Implementation Status:
✅ **KnowledgeGraphService**: Complete enterprise-grade implementation
✅ **Graph Entity Models**: Comprehensive data models for all technologies  
✅ **Migration Service**: Schema versioning and evolution management
✅ **Sync Service**: Event-driven synchronization framework

### Sync Flow Architecture:
```
PostgreSQL → Redis Queue → Graph Sync Service → Neo4j
     ↓              ↓              ↓               ↓
 Metadata      Event Queue    Processing      Knowledge Graph
 Storage       Management     Engine          Relationships
```

### Real-time Sync Events:
- **Repository Creation/Update** → Sync repository metadata to graph
- **Code Analysis Completion** → Create code entity nodes and relationships  
- **Business Rule Discovery** → Link business rules across technologies
- **Cross-Repository Dependencies** → Map inter-project relationships

---

## 📊 **Technology Flow Tracing**

### Implemented Capabilities:
- **JSP → Struts Action → Java Service → Database** flow mapping
- **Cross-technology relationship discovery**
- **Business rule extraction across technology boundaries**
- **Impact analysis for code changes**

### Usage Examples:
```python
# Find business rule paths
kg = await get_knowledge_graph_service()
paths = await kg.find_business_rule_path("summary.jsp", max_depth=8)

# Get technology flow chains  
chains = await kg.get_technology_flow_chain("JSP", "Database")

# Analyze change impact
impact = await kg.analyze_impact_of_change("UserService.java", "modification")
```

---

## 🎯 **Next Implementation Phases**

### **Phase 1, Week 3-6**: Multi-Repository Project Coordination
- **Project Management Service**: Orchestrate multi-repo analysis
- **Repository Federation**: Cross-repository dependency tracking
- **Resource Allocation**: Load balancing and progress tracking

### **Phase 2, Week 7-12**: Advanced Business Rule Extraction  
- **JSP Parser Enhancement**: Extract business logic from JSP pages
- **Struts Configuration Analysis**: Map actions to business processes
- **Java Code Flow Tracer**: Follow method calls across classes
- **CORBA Interface Mapping**: Legacy system integration points

### **Phase 3, Week 13-18**: Meta-Agent Orchestration
- **Workflow Coordination**: Complex multi-step analysis processes
- **Agent Specialization**: Domain-specific analysis agents
- **Quality Assurance**: Golden questions framework
- **Performance Optimization**: Concurrent processing pipelines

### **Phase 4, Week 19-26**: Enterprise Production Features
- **Authentication Integration**: SSO and RBAC implementation
- **Compliance Framework**: Audit trails and data governance
- **High Availability**: Clustering and failover mechanisms
- **Monitoring & Alerting**: Operational excellence features

---

## 🔍 **Troubleshooting Common Issues**

### Service Startup Issues
```bash
# Check logs for specific service
podman logs docxp-neo4j
podman logs docxp-postgres
podman logs docxp-opensearch

# Restart specific service
podman-compose restart neo4j

# Recreate all services
podman-compose down
podman-compose up -d
```

### Connection Issues
```bash
# Check port availability
netstat -an | grep -E "(7474|7687|5432|6379|9200)"

# Test service connectivity
curl localhost:9200/_cluster/health
redis-cli -h localhost ping
```

### Memory Issues
```bash
# Monitor resource usage
podman stats

# Adjust memory limits in podman-compose.yml:
# - NEO4J_server_memory_heap_max__size=2G
# - OPENSEARCH_JAVA_OPTS=-Xms4g -Xmx4g
```

---

## 📚 **Additional Resources**

### Neo4j Management
- **Browser**: http://localhost:7474
- **Bolt Protocol**: bolt://localhost:7687
- **Documentation**: https://neo4j.com/docs/

### OpenSearch Management  
- **Cluster API**: http://localhost:9200
- **Index Management**: http://localhost:9200/_cat/indices
- **Documentation**: https://opensearch.org/docs/

### MinIO Management
- **Console**: http://localhost:9001
- **API**: http://localhost:9000
- **Documentation**: https://min.io/docs/

---

## ✅ **Success Criteria**

### Week 1 Complete When:
- [ ] All 5 services running and healthy
- [ ] Neo4j accessible with graph schema initialized
- [ ] Basic node and relationship creation working
- [ ] PostgreSQL data successfully synced to graph
- [ ] Test suite passes all connectivity tests

### Ready for Week 2 When:
- [ ] Business rule tracing demonstrates JSP → Database flow
- [ ] Cross-repository dependency mapping functional
- [ ] Graph statistics show comprehensive entity relationships
- [ ] API health endpoints return all services healthy
- [ ] Knowledge graph contains sample technology components

---

This setup guide provides the complete foundation for DocXP enterprise deployment. Each step builds toward the sophisticated conversational code decomposition platform described in the TODO.md implementation plan.