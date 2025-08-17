# DocXP Complete Installation Guide
## Full Production Setup with PostgreSQL, Redis, and AWS Integration

**Target:** Get DocXP running with full functionality - no fallbacks, no graceful degradation.
**Requirements:** All features must work or the app should not start.

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

## 📦 **Step 1: Install PostgreSQL**

### Windows (Using Chocolatey - Recommended)
```bash
# Install PostgreSQL 15
choco install postgresql --version=15.8.0 --params '/Password:docxp2024'

# Or download directly from:
# https://www.postgresql.org/download/windows/
# Use password: docxp2024
```

### Manual Installation
1. Download PostgreSQL 15+ from https://www.postgresql.org/download/windows/
2. Run installer with these settings:
   - **Port:** 5432
   - **Password:** `docxp2024`
   - **Locale:** Default
3. Add to PATH: `C:\Program Files\PostgreSQL\15\bin`

### Verify Installation
```bash
# Test PostgreSQL is running
psql --version
# Should show: psql (PostgreSQL) 15.x

# Test connection
psql -U postgres -h localhost
# Enter password: docxp2024
# Type \q to exit
```

---

## 🔴 **Step 2: Install Redis**

### Option A: Using Podman (Recommended)
```bash
# Start Redis container
podman run -d --name docxp-redis -p 6379:6379 redis:7-alpine

# Verify Redis is running
podman ps
# Should show redis container running on port 6379
```

### Option B: Native Windows Installation
```bash
# Using Chocolatey
choco install redis-64

# Or download from:
# https://github.com/microsoftarchive/redis/releases
```

### Verify Redis Installation
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
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

# Verify critical imports work
python validate_imports.py
# Should show: SUCCESS: ALL VALIDATION TESTS PASSED!
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