# DocXP - Enterprise Code Intelligence Platform

![DocXP Logo](frontend/src/assets/docxp-logo.png)

## 🚀 Overview

DocXP is an enterprise-grade code intelligence platform that provides comprehensive analysis and insights for complex codebases. It combines semantic search, architectural analysis, static code analysis, and AI-powered documentation generation into a unified platform.

### ✨ Key Features

- **🔍 Semantic Search**: Advanced hybrid search (BM25 + k-NN) with embedding-based similarity
- **🏗️ Architectural Analysis**: Deep Java architecture analysis with jQAssistant integration
- **🛡️ Security Analysis**: Static code analysis with Semgrep for security vulnerabilities
- **📊 Code Intelligence**: Cross-technology flow analysis (JSP, Struts, Angular, CORBA)
- **💬 AI Chat Interface**: Conversational code exploration with AWS Bedrock Claude
- **📈 Quality Metrics**: Comprehensive code quality scoring and health assessments
- **🔄 Enterprise Scale**: Fault-tolerant processing for 100k+ files with checkpointing
- **🎯 Real-time Updates**: Live progress tracking with Server-Sent Events

## 📋 System Requirements

### Minimum Requirements
- **Python 3.10+** 
- **Node.js 18+ and npm**
- **Git**
- **4GB RAM** (8GB+ recommended for large repositories)
- **2GB free disk space** (more for large repositories)

### Required Services
- **AWS Account** with Bedrock access (**REQUIRED**)
- **AWS Credentials** configured (Access Keys or SSO Profile)
- **OpenSearch** (auto-configured locally)
- **Redis** (auto-configured locally)
- **PostgreSQL** (auto-configured locally)

### Optional Services (for advanced features)
- **Neo4j** for jQAssistant graph analysis
- **jQAssistant CLI** for Java architecture analysis
- **Semgrep** for static code analysis

## 🚀 Quick Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd docxp
```

### 2. Configure AWS Credentials (REQUIRED)

**Option A: AWS CLI Profile (Recommended)**
```bash
# Install AWS CLI if not already installed
# Windows: Download from https://aws.amazon.com/cli/
# Linux/Mac: pip install awscli

# Configure with SSO (preferred for enterprise)
aws configure sso

# Or configure with access keys
aws configure

# Verify credentials work
aws sts get-caller-identity
```

**Option B: Environment Variables**
```bash
# Windows
set AWS_ACCESS_KEY_ID=your-access-key
set AWS_SECRET_ACCESS_KEY=your-secret-key
set AWS_REGION=us-east-1

# Linux/Mac
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

### 3. Verify Bedrock Access
```bash
# Test Bedrock access (this should not error)
aws bedrock list-foundation-models --region us-east-1
```

### 4. Start DocXP

**All-in-One Startup (Recommended)**
```bash
# Windows
enhanced-start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

The startup process will:
1. ✅ Validate environment and AWS credentials
2. ✅ Install all dependencies (Python, Node.js)
3. ✅ Initialize local services (OpenSearch, Redis, PostgreSQL)
4. ✅ Create database schemas and indexes
5. ✅ Start backend API on http://localhost:8001
6. ✅ Start frontend on http://localhost:4200
7. ✅ Open browser automatically

## 🏗️ Architecture Overview

DocXP follows a modern microservices-inspired architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Angular 18)                   │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Chat Interface  │ Search Dashboard│ Architecture Analysis  │
│ Code Flow UI    │ Semantic Search │ Quality Metrics        │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                   │
├─────────────────┬─────────────────┬─────────────────────────┤
│ V1 Indexing     │ jQAssistant     │ Enhanced Search         │
│ Chat/AI         │ Semgrep         │ Code Flow Analysis      │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                  Processing Services                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│ V1 Indexing     │ jQAssistant     │ Code Flow Tracers       │
│ Embedding       │ Batch Service   │ Cross-tech Analysis     │
│ AWS Token Mgr   │ Static Analysis │ Unified Intelligence    │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│ PostgreSQL      │ OpenSearch      │ Redis                   │
│ (Jobs, Metadata)│ (Search Index)  │ (Cache, Queue)          │
│ Neo4j (Optional)│ AWS Bedrock     │ MinIO (Optional)        │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### Core Services

1. **V1 Indexing Service**: Fault-tolerant file processing with embedding generation
2. **jQAssistant Integration**: Java architecture analysis with dependency graphs
3. **Semgrep Integration**: Static code analysis for security and quality
4. **Code Flow Tracers**: Cross-technology flow analysis (JSP↔Struts↔Angular)
5. **AI Chat Service**: Conversational code exploration with AWS Bedrock
6. **Enhanced Search**: Hybrid search with RRF (Reciprocal Rank Fusion)

## 📚 Detailed Setup Guide

### AWS Configuration

#### For New AWS Users

1. **Create AWS Account**: Visit [aws.amazon.com](https://aws.amazon.com) and create an account
2. **Enable Bedrock Access**: 
   - Go to AWS Console → Bedrock → Model access
   - Request access to Claude models (may take a few minutes to hours)
3. **Create Access Keys**:
   - Go to AWS Console → IAM → Users → Your user → Security credentials
   - Create access key for CLI/API access
   - Save credentials securely

#### For Enterprise Users

If your organization uses AWS SSO:

1. **Get SSO Start URL** from your AWS administrator
2. **Configure AWS CLI**:
   ```bash
   aws configure sso
   # Follow prompts to set up SSO profile
   ```
3. **Set Profile**: `export AWS_PROFILE=your-sso-profile`

### Optional Service Installation

#### jQAssistant (for Java Architecture Analysis)

**Ubuntu/Debian:**
```bash
sudo apt-get install jqassistant
```

**macOS:**
```bash
brew install jqassistant
```

**Manual Installation:**
```bash
wget https://repo1.maven.org/maven2/com/buschmais/jqassistant/jqassistant-commandline-distribution/2.0.0/jqassistant-commandline-distribution-2.0.0-bin.zip
unzip jqassistant-commandline-distribution-2.0.0-bin.zip
sudo mv jqassistant-commandline-distribution-2.0.0 /opt/jqassistant
sudo ln -s /opt/jqassistant/bin/jqassistant.sh /usr/local/bin/jqassistant
```

#### Neo4j (for Advanced Graph Analysis)

```bash
# Install Neo4j
sudo apt-get install neo4j

# Configure Neo4j
sudo systemctl enable neo4j
sudo systemctl start neo4j

# Set initial password
neo4j-admin set-initial-password your-password
```

#### Semgrep (for Static Code Analysis)

```bash
# Install via pip
pip install semgrep

# Or via package manager
# Ubuntu/Debian
sudo apt-get install semgrep

# macOS
brew install semgrep
```

### Local Service Configuration

DocXP automatically configures local services, but you can customize them:

**PostgreSQL Configuration:**
```bash
# Default connection
postgresql://codebase_rag:codebase-rag-2024@localhost:5432/codebase_rag
```

**OpenSearch Configuration:**
```bash
# Default endpoint
http://localhost:9200
```

**Redis Configuration:**
```bash
# Default connection
redis://localhost:6379
```

## 🎯 Getting Started

### 1. First Analysis

Once DocXP is running, visit http://localhost:4200 and:

1. **Configure Repository**: Add a path to your codebase
2. **Start Indexing**: Choose "Enhanced Indexing" for full analysis
3. **Monitor Progress**: Watch real-time progress in the dashboard
4. **Explore Results**: Use semantic search, chat interface, or architecture views

### 2. Key Workflows

#### Semantic Search
- Navigate to "Search" tab
- Use natural language queries: "find user authentication logic"
- Filter by repository, file type, or commit
- Explore code with AI-generated context

#### Architecture Analysis
- Navigate to "Architecture" tab
- Start analysis for Java repositories
- View dependency graphs and violations
- Get architectural insights and recommendations

#### Chat with Codebase
- Open the chat interface
- Ask questions about your code: "How does user login work?"
- Get contextual answers with code references
- Follow up with clarifying questions

#### Quality Assessment
- View repository health scores
- Review architectural violations
- Monitor code quality trends
- Export detailed reports

## 🔧 Configuration

### Environment Variables

Create `backend/.env` for custom configuration:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_CHAT_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Database Configuration
POSTGRES_URL=postgresql://codebase_rag:codebase-rag-2024@localhost:5432/codebase_rag
OPENSEARCH_URL=http://localhost:9200
REDIS_URL=redis://localhost:6379

# Processing Configuration
INDEXING_MAX_FILES_PER_CHUNK=50
INDEXING_MAX_CHUNK_SIZE_MB=10
V1_MAX_CONCURRENT_JOBS=3
JQA_MAX_CONCURRENT_ANALYSES=2

# jQAssistant Configuration
JQA_NEO4J_URL=bolt://localhost:7687
JQA_NEO4J_USER=neo4j
JQA_NEO4J_PASSWORD=your-password
JQA_MAX_MEMORY_GB=8
JQA_ANALYSIS_TIMEOUT_HOURS=4

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Feature Configuration

**Disable Optional Features:**
```env
# Disable jQAssistant if not needed
ENABLE_JQASSISTANT=false

# Disable Semgrep if not needed
ENABLE_SEMGREP=false

# Use lighter indexing for small repositories
INDEXING_MODE=lightweight
```

## 📊 API Documentation

### Interactive API Docs
Visit http://localhost:8001/docs for complete Swagger documentation

### Key Endpoints

#### Enhanced Indexing
```http
POST /api/enhanced-indexing/start
{
  "repository_path": "/path/to/repo",
  "job_type": "full",
  "enable_architectural_analysis": true
}
```

#### Semantic Search
```http
POST /api/v1-search/hybrid-search
{
  "query": "user authentication logic",
  "repository_filter": "my-project",
  "k": 10
}
```

#### Architecture Analysis
```http
POST /api/jqassistant/analyze/repository
{
  "repository_path": "/path/to/java/repo",
  "repository_id": "my-java-project",
  "commit_hash": "HEAD"
}
```

#### Chat Interface
```http
POST /api/chat/query
{
  "message": "How does user login work?",
  "repository_context": ["repo1", "repo2"]
}
```

## 🔍 Health Monitoring

### Health Endpoints
```bash
# Basic health check
curl http://localhost:8001/health

# Detailed health with all services
curl http://localhost:8001/health/detailed

# Readiness check
curl http://localhost:8001/health/ready

# Component-specific health
curl http://localhost:8001/health/aws
curl http://localhost:8001/health/database
curl http://localhost:8001/health/search
```

### Monitoring Dashboard
Visit http://localhost:4200/dashboard for:
- Real-time system status
- Job progress tracking
- Repository health scores
- Performance metrics
- Error tracking

## 🛠️ Troubleshooting

### Common Issues

#### Startup Failures
```bash
# 1. Verify AWS credentials
aws sts get-caller-identity

# 2. Check Bedrock access
aws bedrock list-foundation-models --region us-east-1

# 3. Run environment validation
cd backend
python -m app.core.validator

# 4. Check service status
curl http://localhost:8001/health/detailed

# 5. View logs
tail -f backend/logs/docxp.log
```

#### Service Connection Issues
```bash
# Check OpenSearch
curl http://localhost:9200/_cluster/health

# Check Redis
redis-cli ping

# Check PostgreSQL
psql postgresql://codebase_rag:codebase-rag-2024@localhost:5432/codebase_rag -c "SELECT 1"
```

#### Performance Issues
```bash
# Monitor resource usage
# Windows
tasklist | findstr "python\|node"

# Linux/Mac
ps aux | grep -E "(python|node)"

# Check disk space
df -h

# Monitor logs for errors
grep -i error backend/logs/docxp.log
```

#### Port Conflicts
```bash
# Windows
netstat -ano | findstr ":8001\|:4200\|:9200\|:6379\|:5432"

# Linux/Mac
lsof -i :8001,:4200,:9200,:6379,:5432
```

### Advanced Troubleshooting

#### Database Issues
```bash
# Reset database
cd backend
python -c "
from app.core.database import reset_database
import asyncio
asyncio.run(reset_database())
"

# Check database schema
python -c "
from app.core.database import check_database_schema
import asyncio
asyncio.run(check_database_schema())
"
```

#### Search Index Issues
```bash
# Recreate OpenSearch indexes
curl -X DELETE http://localhost:9200/docxp-*
curl -X POST http://localhost:8001/api/admin/recreate-indexes
```

#### Cache Issues
```bash
# Clear Redis cache
redis-cli flushall

# Clear embedding cache
curl -X POST http://localhost:8001/api/admin/clear-cache
```

## 📈 Performance Optimization

### Repository Size Guidelines

| Repository Size | Files | Recommended Config | Expected Time |
|-----------------|-------|-------------------|---------------|
| Small | <1,000 | Default settings | 2-5 minutes |
| Medium | 1,000-10,000 | 8GB RAM, concurrent=2 | 10-30 minutes |
| Large | 10,000-50,000 | 16GB RAM, concurrent=1 | 1-3 hours |
| Enterprise | >50,000 | 32GB RAM, chunking=25 | 3-8 hours |

### Optimization Settings

**For Large Repositories:**
```env
# Reduce memory usage
INDEXING_MAX_FILES_PER_CHUNK=25
INDEXING_MAX_CHUNK_SIZE_MB=5
V1_MAX_CONCURRENT_JOBS=1

# Increase timeouts
JQA_ANALYSIS_TIMEOUT_HOURS=8
AWS_TOKEN_REFRESH_THRESHOLD_MINUTES=30

# Enable selective processing
INDEXING_MODE=selective
FILE_PATTERNS=["*.java", "*.py", "*.js", "*.ts"]
```

**For Development/Testing:**
```env
# Faster processing
INDEXING_MAX_FILES_PER_CHUNK=100
V1_MAX_CONCURRENT_JOBS=4
ENABLE_CACHING=true

# Skip heavy analysis
ENABLE_JQASSISTANT=false
ENABLE_SEMGREP=false
```

## 🔒 Security Configuration

### Production Security

**API Security:**
```python
# backend/app/core/config.py
CORS_ORIGINS = ["https://your-domain.com"]
ENABLE_HTTPS = True
API_KEY_REQUIRED = True
```

**AWS Security:**
```bash
# Use IAM roles instead of access keys
aws configure set region us-east-1
aws configure set output json
# Configure IAM role with minimum required permissions
```

**Database Security:**
```env
# Use strong passwords
POSTGRES_PASSWORD=your-strong-password
REDIS_PASSWORD=your-redis-password
NEO4J_PASSWORD=your-neo4j-password

# Enable SSL
POSTGRES_SSL=require
OPENSEARCH_SSL=true
```

### Audit Logging

DocXP provides comprehensive audit logging:

```bash
# View access logs
tail -f backend/logs/access.log

# View security events
grep -i "auth\|security\|unauthorized" backend/logs/docxp.log

# View API usage
grep -i "api_key\|rate_limit" backend/logs/docxp.log
```

## 🚀 Deployment

### Docker Deployment

**Build and Run:**
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Production Deployment

**Environment Setup:**
```bash
# Create production environment
cp .env.template .env.production

# Set production variables
export NODE_ENV=production
export FLASK_ENV=production
export LOG_LEVEL=WARNING
```

**Service Dependencies:**
```yaml
# docker-compose.production.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: codebase_rag
      POSTGRES_USER: codebase_rag
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
    volumes:
      - opensearch_data:/usr/share/opensearch/data

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

  docxp-backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://codebase_rag:${POSTGRES_PASSWORD}@postgres:5432/codebase_rag
      - OPENSEARCH_URL=http://opensearch:9200
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      - postgres
      - opensearch
      - redis

  docxp-frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - docxp-backend

volumes:
  postgres_data:
  opensearch_data:
  redis_data:
```

## 📚 Additional Documentation

- **[jQAssistant Integration Guide](JQASSISTANT_INTEGRATION_GUIDE.md)** - Comprehensive jQAssistant setup and usage
- **[API Reference](http://localhost:8001/docs)** - Complete API documentation
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[Architecture Guide](ARCHITECTURE.md)** - Detailed system architecture
- **[Migration Guide](MIGRATION_STRATEGY.md)** - Upgrading from previous versions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`npm test` and `pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AWS Bedrock** for AI capabilities
- **jQAssistant** for Java architecture analysis
- **Semgrep** for static code analysis
- **OpenSearch** for semantic search
- **Angular** for the frontend framework
- **FastAPI** for the high-performance backend

## 📞 Support

For issues and questions:

1. **Check Health Status**: http://localhost:8001/health/detailed
2. **View Logs**: `tail -f backend/logs/docxp.log`
3. **Run Diagnostics**: `python backend/app/core/validator.py`
4. **Documentation**: [API Docs](http://localhost:8001/docs)
5. **Issues**: Create a GitHub issue with logs and system information

---

**DocXP v3.0** - *Enterprise Code Intelligence Platform*

*Transforming legacy codebases into intelligent, searchable, and maintainable systems.*