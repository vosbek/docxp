# DocXP Enterprise Startup Guide

This document provides comprehensive guidance for starting DocXP on any target machine with reliable, deterministic results.

## Overview

DocXP is an Enterprise Conversational Code Decomposition Platform that requires a specific startup sequence to ensure all services initialize correctly. This guide eliminates the "whack-a-mole" pattern of startup errors by addressing all dependencies systematically.

## Prerequisites

### Required Software
- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Podman** (or Docker) for container orchestration
- **Git** for repository management
- **AWS CLI** with `msh` profile configured for Bedrock access

### Target Machine Requirements
- 8GB+ RAM (16GB recommended)
- 50GB+ available disk space
- Network connectivity to AWS Bedrock (us-east-1)
- Ports available: 8001 (API), 5432 (PostgreSQL), 6379 (Redis), 9200 (OpenSearch), 7474/7687 (Neo4j)

## Architecture Overview

```
DocXP Backend Startup Flow:
├── Configuration Loading (.env.enterprise + config.py)
├── Infrastructure Services (PostgreSQL, Redis, OpenSearch, Neo4j)
├── Database Schema Initialization
├── Service Dependencies (AWS Bedrock, strands-agents)
├── Application Services Initialization
└── Health Check Endpoints Activation
```

## Phase 1: Environment Setup

### 1.1 Python Environment
```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# CRITICAL: Install strands-agents (prevents import failures)
pip install strands-agents
```

### 1.2 Configuration Files
Ensure `.env.enterprise` exists with these critical settings:
```env
# Application
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://docxp_user:docxp_secure_2024@localhost:5432/docxp_enterprise
POSTGRESQL_VECTOR_URL=postgresql+asyncpg://docxp_user:docxp_secure_2024@localhost:5432/docxp_enterprise

# AWS Bedrock
AWS_REGION=us-east-1
AWS_PROFILE=msh
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
CHAT_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0

# Services
REDIS_URL=redis://localhost:6379/0
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_INDEX_NAME=docxp_v1_chunks
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=docxp-neo4j-2024

# Performance
API_PORT=8001
MAX_CONCURRENT_REPOS=2
BATCH_SIZE=50
```

## Phase 2: Infrastructure Services

### 2.1 Start Container Services
```powershell
# Start all infrastructure services
podman-compose up -d

# Verify services are running
podman ps
```

Expected containers:
- `docxp-postgres` (PostgreSQL with pgvector)
- `docxp-redis` (Redis cache)
- `docxp-opensearch` (OpenSearch engine)
- `docxp-neo4j` (Neo4j graph database)
- `docxp-minio` (S3-compatible storage)

### 2.2 Service Health Verification
```powershell
# Test PostgreSQL connectivity
python -c "import asyncpg; print('PostgreSQL driver available')"

# Test Redis connectivity
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(f'Redis ping: {r.ping()}')"

# Test OpenSearch connectivity
curl http://localhost:9200/_cluster/health

# Test Neo4j connectivity
curl http://localhost:7474/browser/
```

## Phase 3: Database Initialization

### 3.1 Database Schema Setup
```powershell
# Run database initialization
python -c "
from app.core.database import init_database
import asyncio
asyncio.run(init_database())
print('Database initialized successfully')
"
```

### 3.2 Vector Extensions
The PostgreSQL container includes pgvector extension for vector operations:
```sql
-- Verify pgvector is available
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

## Phase 4: Application Startup

### 4.1 Pre-flight Validation
```powershell
# Run comprehensive startup validation
python validate_startup.py

# Expected output: All green checkmarks ✅
```

### 4.2 Start Backend Application
```powershell
# Method 1: Direct Python execution
python -m app.main

# Method 2: Uvicorn server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Method 3: Using start script
.\start-backend.bat
```

### 4.3 Verify Startup Success
```powershell
# Basic health check
curl http://localhost:8001/health/

# Detailed health check
curl http://localhost:8001/health/detailed

# Readiness check
curl http://localhost:8001/health/ready
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-XX-XXXXX",
  "service": "DocXP Backend",
  "version": "1.0.0"
}
```

## Critical Dependencies Map

### Import Dependencies
```
app.main
├── app.core.config (Settings validation)
├── app.core.database (PostgreSQL + pgvector)
├── app.core.startup (Application state)
├── app.services.strands_agent_service (AI agents - CRITICAL)
├── app.services.knowledge_graph_service (Neo4j)
├── app.services.bedrock_embedding_service (AWS Bedrock)
└── app.api.* (All API routes)
```

### Service Dependencies
```
Backend Application
├── PostgreSQL (Database + vectors)
├── Redis (Caching + queues)
├── OpenSearch (Full-text + hybrid search)
├── Neo4j (Knowledge graph)
├── AWS Bedrock (Embeddings + chat)
├── MinIO (S3-compatible storage)
└── strands-agents (AI orchestration)
```

## Failure Modes & Solutions

### Common Startup Failures

#### 1. Pydantic Validation Errors
**Symptom**: `validation errors for Settings`
**Solution**: Verify all required fields in `.env.enterprise`
**Prevention**: Run `python -c "from app.core.config import settings; print('Config valid')"`

#### 2. strands-agents Import Error
**Symptom**: `ImportError: No module named 'strands'`
**Solution**: `pip install strands-agents`
**Prevention**: Add to requirements.txt and validate in pre-flight

#### 3. Database Connection Failures
**Symptom**: `Connection refused` to PostgreSQL
**Solution**: Ensure `podman-compose up -d` completed successfully
**Prevention**: Wait for health checks before starting backend

#### 4. AWS Credentials Issues
**Symptom**: `NoCredentialsError` for Bedrock
**Solution**: Verify `aws configure list-profiles` shows `msh` profile
**Prevention**: Test AWS connectivity in pre-flight validation

#### 5. Port Conflicts
**Symptom**: `Address already in use` errors
**Solution**: Check and terminate conflicting processes
**Prevention**: Use `netstat -an | findstr :8001` before startup

## Production Deployment Checklist

### Security Configuration
- [ ] `AUTH_ENABLED=true` for production
- [ ] SSL certificates configured
- [ ] AWS credentials secured (IAM roles preferred)
- [ ] Database passwords rotated from defaults
- [ ] Network security groups configured

### Performance Configuration
- [ ] `MAX_CONCURRENT_REPOS=4` (or based on hardware)
- [ ] `BATCH_SIZE=100` (or tuned for workload)
- [ ] Database connection pooling configured
- [ ] Redis memory limits set
- [ ] OpenSearch heap size tuned

### Monitoring Configuration
- [ ] Health check endpoints accessible
- [ ] Logging configured for production
- [ ] Metrics collection enabled
- [ ] Alert thresholds configured

## Troubleshooting Commands

### Diagnostic Commands
```powershell
# Check all service status
podman ps -a

# View backend logs
podman logs docxp-backend --tail 50

# Test database connectivity
python -c "
import asyncio
from app.core.database import test_connection
asyncio.run(test_connection())
"

# Test AWS Bedrock connectivity
aws bedrock list-foundation-models --region us-east-1 --profile msh

# Validate configuration
python -c "
from app.core.config import settings
print(f'Database: {settings.DATABASE_URL}')
print(f'AWS Region: {settings.AWS_REGION}')
print(f'API Port: {settings.API_PORT}')
"
```

### Service-Specific Logs
```powershell
# PostgreSQL logs
podman logs docxp-postgres

# Redis logs
podman logs docxp-redis

# OpenSearch logs
podman logs docxp-opensearch

# Neo4j logs
podman logs docxp-neo4j
```

## Recovery Procedures

### Hard Reset (Nuclear Option)
```powershell
# Stop all services
podman-compose down -v

# Remove all volumes (DATA LOSS WARNING)
podman volume prune -f

# Restart from clean state
podman-compose up -d

# Wait for services to initialize
Start-Sleep 30

# Reinitialize database
python -c "
from app.core.database import init_database
import asyncio
asyncio.run(init_database())
"

# Restart backend
python -m app.main
```

### Incremental Recovery
```powershell
# Restart just the backend
podman restart docxp-backend

# Restart specific service
podman restart docxp-postgres

# Clear Redis cache
podman exec docxp-redis redis-cli FLUSHALL
```

## Success Indicators

### Startup Complete Checklist
- [ ] All infrastructure containers running (`podman ps`)
- [ ] Backend application started without errors
- [ ] Health endpoint returns `"status": "healthy"`
- [ ] Detailed health shows all services operational
- [ ] AWS Bedrock connectivity confirmed
- [ ] Database schema initialized
- [ ] Neo4j graph database accessible

### Performance Indicators
- [ ] API response time < 200ms for health checks
- [ ] Memory usage < 4GB total
- [ ] Database connections < 10 active
- [ ] No error logs in first 60 seconds

## Support & Maintenance

### Regular Maintenance
- Monitor disk space (logs and database growth)
- Rotate database connection logs weekly
- Update dependencies monthly
- Backup Neo4j graph database weekly
- Monitor AWS Bedrock usage and costs

### Emergency Contacts
- Application logs: `backend/logs/`
- Service logs: `podman logs [container-name]`
- Configuration: `.env.enterprise`
- Health status: `http://localhost:8001/health/detailed`

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Maintained by**: DocXP Development Team

This startup guide ensures deterministic, reliable deployment of DocXP on any properly configured target machine. Follow the phases sequentially for best results.