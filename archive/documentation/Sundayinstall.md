# DocXP Complete Installation Guide
## Full Production Setup with PostgreSQL, Redis, and AWS Integration

**Target:** Get DocXP running with full functionality - no fallbacks, no graceful degradation.
**Requirements:** All features must work or the app should not start.

---

## 🚀 **CURRENT PROGRESS STATUS**
- ✅ **Step 1: PostgreSQL Installed** (Password needs fixing)
- ✅ **Step 2: Redis/Memurai Installed** (Service needs starting)
- ⏳ **NEXT: Fix PostgreSQL password and start services**

---

---

## 🎯 **Prerequisites Confirmed**
- ✅ Python 3.10+
- ✅ Node.js 18+
- ✅ npm
- ✅ Git
- ✅ Podman
- ✅ Java
- ✅ Repository checked out and updated

---

## 📦 **Step 1: Install PostgreSQL** ✅

### Windows (Using Chocolatey - COMPLETED)
```bash
# ALREADY COMPLETED ✅
choco install postgresql --version=15.8.0 --params '/Password:docxp2024'
# Note: Chocolatey ignored the password parameter and generated: c37e562786d949539dacd487616779ad
```

### 🔧 **Fix PostgreSQL Password**
```bash
# Refresh environment variables first
refreshenv

# Reset postgres user password to our desired password
psql -U postgres -h localhost
# When prompted, enter the generated password: c37e562786d949539dacd487616779ad

# Once connected, run this SQL command:
ALTER USER postgres PASSWORD 'docxp2024';

# Exit psql
\q
```

### Verify Fixed Installation
```bash
# Test PostgreSQL is running
psql --version
# Should show: psql (PostgreSQL) 15.x

# Test connection with new password
psql -U postgres -h localhost
# Enter password: docxp2024
# Type \q to exit
```

---

## 🔴 **Step 2: Install Redis** ✅

### Windows Installation (COMPLETED)
```bash
# ALREADY COMPLETED ✅
choco install redis-64
# Note: This installed Memurai Developer (Redis-compatible) instead of native Redis
# Memurai is Redis-compatible and works perfectly with DocXP
```

### 🔧 **Start Memurai Service**
```bash
# Refresh environment variables
refreshenv

# Start Memurai service (Redis-compatible)
net start Memurai

# Alternative: Use Services.msc and start "Memurai" service manually
```

### Verify Redis/Memurai Installation
```bash
# Test Redis connection (Memurai uses same commands)
redis-cli ping
# Should return: PONG

# If redis-cli is not found, try:
"C:\Program Files\Memurai\redis-cli.exe" ping
```

---

## 🗄️ **Step 3: Create DocXP Database**

```bash
# Connect to PostgreSQL as superuser
psql -U postgres -h localhost

# Create database and user
CREATE DATABASE docxp_enterprise;
CREATE USER docxp_user WITH PASSWORD 'docxp_secure_2024';
GRANT ALL PRIVILEGES ON DATABASE docxp_enterprise TO docxp_user;
ALTER USER docxp_user CREATEDB;

# Exit psql
\q
```

### Verify Database Setup
```bash
# Test connection with new user
psql -U docxp_user -d docxp_enterprise -h localhost
# Enter password: docxp_secure_2024
# Type \q to exit
```

---

## ⚙️ **Step 4: Configure Environment Variables**

Create `.env` file in `backend/` directory:

```bash
cd C:\devl\workspaces\docxp\backend
```

Create file `.env` with this content:
```env
# Application Environment
APP_ENV=production
DEBUG=false

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://docxp_user:docxp_secure_2024@localhost:5432/docxp_enterprise

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AWS Configuration
AWS_PROFILE=msh
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1

# Bedrock Configuration
EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
CHAT_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0

# OpenSearch Configuration (Local)
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USE_SSL=false
OPENSEARCH_VERIFY_CERTS=false

# Application Settings
LOG_LEVEL=INFO
API_PORT=8001
OUTPUT_DIR=./output
TEMP_DIR=./temp

# Security
AUTH_ENABLED=false

# V1 Indexing Configuration
CHUNK_SIZE=25
MAX_CONCURRENT_CHUNKS=4
MAX_RETRIES=3
AWS_API_TIMEOUT=30
BATCH_SIZE=50
MAX_CONCURRENT_REPOS=2
```

---

## 🐳 **Step 5: Start OpenSearch (Required for V1 Indexing)**

```bash
# Start OpenSearch container
podman run -d --name docxp-opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "plugins.security.disabled=true" \
  -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=DocXP2024!" \
  opensearchproject/opensearch:2.11.0

# Wait for OpenSearch to start (30 seconds)
timeout 30

# Verify OpenSearch is running
curl http://localhost:9200
# Should return OpenSearch cluster info JSON
```

---

## 🔧 **Step 6: Install Python Dependencies & Setup Virtual Environment**

```bash
cd C:\devl\workspaces\docxp\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# 🚨 FIX SENTENCE_TRANSFORMERS COMPATIBILITY ISSUE
# Uninstall conflicting packages
pip uninstall sentence_transformers huggingface_hub transformers tokenizers -y

# Install compatible versions (CRITICAL FOR CHROMADB)
pip install "huggingface_hub>=0.16.0,<0.20.0" 
pip install "sentence_transformers>=2.2.0"
pip install "transformers>=4.21.0"

# 🚨 FIX OPENSEARCH IMPORT ERROR
pip install opensearch-py==2.4.2

# Test sentence_transformers installation
python -c "from sentence_transformers import SentenceTransformer; print('sentence_transformers working')"

# Test ChromaDB with SentenceTransformer
python -c "
import chromadb
from chromadb.utils import embedding_functions
ef = embedding_functions.SentenceTransformerEmbeddingFunction()
print('ChromaDB with SentenceTransformer working')
"

# Test OpenSearch imports
python -c "from opensearchpy import OpenSearch, AsyncOpenSearch; print('OpenSearch imports working')"

# Verify critical imports work
python validate_imports.py
# Should show: SUCCESS: ALL VALIDATION TESTS PASSED!
```

### 🛠️ Alternative Fix if Above Fails
If you still get `ImportError: cannot import name 'cached_download'`, use these specific versions:

```bash
# Force install older compatible versions
pip install "huggingface_hub==0.19.4"
pip install "sentence_transformers==2.2.2"
pip install "transformers==4.35.0"

# Test again
python -c "from sentence_transformers import SentenceTransformer; print('✅ sentence_transformers working')"
```

---

## 🚀 **Step 7: Initialize Database Schema**

```bash
# Still in backend/ directory with venv activated
python -c "
import asyncio
from app.core.database import init_db
print('Initializing database schema...')
asyncio.run(init_db())
print('✅ Database schema created successfully!')
"
```

---

## 🔑 **Step 8: AWS Configuration**

### On Your AWS Machine (where you can run AWS commands):
```bash
# Login to AWS SSO
aws sso login --profile msh

# Verify access to Bedrock
aws bedrock list-foundation-models --region us-east-1 --profile msh

# Verify Claude Sonnet access
aws bedrock invoke-model \
  --region us-east-1 \
  --profile msh \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --body '{"messages":[{"role":"user","content":"test"}],"max_tokens":10,"anthropic_version":"bedrock-2023-05-31"}' \
  --cli-binary-format raw-in-base64-out \
  output.json

# If successful, copy your AWS credentials to the development machine
```

### On Your Development Machine:
Copy the AWS credentials from `~/.aws/` on your AWS machine to your development machine, OR set these environment variables:

```env
# Add to your .env file
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token  # if using SSO
```

---

## 🧪 **Step 9: Validate Complete Setup**

```bash
# Run the comprehensive validation
python startup_check.py

# Should show:
# ✅ VALIDATION PASSED - DocXP is ready to start!
```

**If validation fails, DO NOT PROCEED. Fix all errors first.**

---

## 🌟 **Step 10: Start the Application**

### Start Backend
```bash
# In backend/ directory with venv activated
python main.py

# Should show:
# Starting DocXP Backend...
# Database initialized
# ✅ OpenSearch V1 search engine initialized
# Application startup complete
# Uvicorn running on http://0.0.0.0:8001
```

### Start Frontend (New Terminal)
```bash
cd C:\devl\workspaces\docxp\frontend

# Install dependencies if needed
npm install

# Start Angular dev server
npm start

# Should show:
# Local: http://localhost:4200
# Angular Live Development Server is listening
```

---

## ✅ **Step 11: Verify All Services**

### Test API Endpoints
```bash
# Health check
curl http://localhost:8001/health

# V1 Indexing health
curl http://localhost:8001/api/v1/indexing/health

# API documentation
# Open: http://localhost:8001/docs
```

### Test Database Connection
```bash
# Should return database info
curl http://localhost:8001/health/detailed
```

### Test OpenSearch
```bash
# Should return OpenSearch cluster status
curl http://localhost:9200/_cluster/health
```

---

## 🎯 **Step 12: Test Repository Indexing**

### Start a V1 Indexing Job
```bash
curl -X POST "http://localhost:8001/api/v1/indexing/start" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "C:/path/to/your/test/repo",
    "job_type": "full",
    "file_patterns": ["*.java", "*.py", "*.js"],
    "force_reindex": true
  }'

# Should return:
# {"success": true, "job_id": "job_xxx", "message": "V1 indexing job started successfully"}
```

### Monitor Indexing Progress
```bash
# Replace job_xxx with actual job ID
curl http://localhost:8001/api/v1/indexing/jobs/job_xxx/status
```

---

## 💬 **Step 13: Test AI Chat**

1. Open frontend: http://localhost:4200
2. Navigate to Chat interface
3. Ask: "What repositories are indexed?"
4. Should get response from Claude Sonnet 3.5

---

## 🔍 **Troubleshooting**

### Python Package Compatibility Issues
```bash
# Issue: ImportError: cannot import name 'cached_download' from 'huggingface_hub'
# Fix: Version compatibility between sentence_transformers and huggingface_hub

# Uninstall conflicting packages
pip uninstall sentence_transformers huggingface_hub transformers tokenizers -y

# Install compatible versions
pip install "huggingface_hub>=0.16.0,<0.20.0" 
pip install "sentence_transformers>=2.2.0"
pip install "transformers>=4.21.0"

# Alternative: Use specific working versions
pip install "huggingface_hub==0.19.4"
pip install "sentence_transformers==2.2.2"
pip install "transformers==4.35.0"

# Test the fix
python -c "from sentence_transformers import SentenceTransformer; print('✅ Working')"
```

### PostgreSQL Issues
```bash
# Check if PostgreSQL is running
sc query postgresql-x64-15

# Restart PostgreSQL
net stop postgresql-x64-15
net start postgresql-x64-15
```

### Redis Issues
```bash
# Check Redis container
podman ps

# Restart Redis
podman restart docxp-redis
```

### OpenSearch Issues
```bash
# Check OpenSearch container
podman ps

# View OpenSearch logs
podman logs docxp-opensearch

# Restart OpenSearch
podman restart docxp-opensearch
```

### AWS Issues
```bash
# Test AWS credentials
aws sts get-caller-identity --profile msh

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1 --profile msh
```

---

## 🏢 **CURRENT ARCHITECTURE**

**DocXP uses a modern, enterprise-grade architecture:**

### Current Production Stack
- ✅ **PostgreSQL 15**: Primary database for metadata and jobs
- ✅ **OpenSearch 2.11**: Hybrid search engine (text + vector)
- ✅ **AWS Bedrock**: Titan embeddings + Claude 3.5 Sonnet
- ✅ **Redis + RQ**: Background job processing
- ✅ **Semgrep**: Security vulnerability scanning
- ✅ **jQAssistant**: Java architecture analysis

### What DocXP Does
**DocXP is Google for your codebase + AI expert assistant.**

You can ask questions like:
- "Where is user authentication implemented?"
- "How does payment processing work?"
- "Are there SQL injection vulnerabilities?"
- "Show me the data flow from JSP to database"

### Architecture Benefits
- 🚀 **Enterprise AI**: AWS Bedrock Titan (1024-dim embeddings)
- 🔍 **Hybrid Search**: OpenSearch combines text + semantic search
- 🏢 **Scalable**: Handles multi-GB codebases with 10M+ code chunks
- 🔒 **Secure**: Local-first, only API calls to AWS
- 📊 **Multi-tool**: Integrates Semgrep, jQAssistant, Neo4j

---

## 📁 **Expected File Structure After Setup**

```
docxp/
├── backend/
│   ├── venv/                    # Virtual environment
│   ├── .env                     # Environment variables
│   ├── docxp.db                 # Will be replaced by PostgreSQL
│   ├── logs/                    # Application logs
│   ├── output/                  # Generated documentation
│   └── temp/                    # Temporary files
├── frontend/
│   └── node_modules/            # Frontend dependencies
└── data/                        # Application data
```

---

## 🎉 **Success Criteria**

✅ All services running (PostgreSQL, Redis, OpenSearch)
✅ Backend API responding on port 8001
✅ Frontend serving on port 4200
✅ V1 indexing job completes successfully
✅ AI chat responds with Claude Sonnet 3.5
✅ No errors in logs
✅ All API endpoints functional

**If ANY of these fail, the setup is incomplete. Do not proceed with production use.**

---

## 📞 **Support Commands**

```bash
# Check all services
netstat -an | findstr "5432 6379 9200 8001 4200"

# View application logs
Get-Content backend\logs\docxp.log -Tail 50

# Stop all services
podman stop docxp-redis docxp-opensearch
net stop postgresql-x64-15
```

**This completes the full DocXP enterprise setup with zero tolerance for missing functionality.**