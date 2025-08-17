# DocXP Complete Installation Guide

## 🎯 Overview

This guide provides step-by-step instructions for installing DocXP from scratch on any system. Follow this guide if you're setting up DocXP for the first time or need to reinstall.

## 📋 System Requirements

### Minimum Hardware Requirements
- **CPU**: 2 cores (4+ recommended)
- **RAM**: 4GB (8GB+ recommended for large repositories)
- **Storage**: 5GB free space (more for large repositories)
- **Network**: Internet connection for AWS services

### Operating System Support
- ✅ **Windows 10/11** (fully tested)
- ✅ **macOS 10.15+** (tested)
- ✅ **Ubuntu 20.04+** (tested)
- ✅ **CentOS/RHEL 8+** (community tested)

### Required Software
- **Python 3.10 or higher**
- **Node.js 18 or higher**
- **Git**
- **AWS CLI** (for credential management)

### Required Services
- **AWS Account** with Bedrock access
- **OpenSearch** (auto-installed locally)
- **Redis** (auto-installed locally)
- **PostgreSQL** (auto-installed locally)

## 🚀 Step-by-Step Installation

### Step 1: Install Prerequisites

#### Windows

**Install Python 3.10+:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer, check "Add Python to PATH"
3. Verify: `python --version`

**Install Node.js 18+:**
1. Download from [nodejs.org](https://nodejs.org/)
2. Run installer with default settings
3. Verify: `node --version` and `npm --version`

**Install Git:**
1. Download from [git-scm.com](https://git-scm.com/)
2. Run installer with default settings
3. Verify: `git --version`

**Install AWS CLI:**
1. Download from [AWS CLI Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. Run installer
3. Verify: `aws --version`

#### macOS

**Using Homebrew (recommended):**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install prerequisites
brew install python@3.10
brew install node@18
brew install git
brew install awscli

# Verify installations
python3 --version
node --version
npm --version
git --version
aws --version
```

#### Ubuntu/Debian

```bash
# Update package index
sudo apt update

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Git
sudo apt install git

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installations
python3 --version
node --version
npm --version
git --version
aws --version
```

#### CentOS/RHEL

```bash
# Install Python 3.10+
sudo dnf install python3.10 python3-pip

# Install Node.js 18+
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install nodejs

# Install Git
sudo dnf install git

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installations
python3 --version
node --version
npm --version
git --version
aws --version
```

### Step 2: AWS Configuration

#### Create AWS Account (if needed)

1. Visit [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow registration process
4. Verify email and add payment method

#### Enable Bedrock Access

1. Sign in to AWS Console
2. Navigate to **Amazon Bedrock**
3. Go to **Model access** in left sidebar
4. Click **Request model access**
5. Select **Anthropic Claude** models:
   - Claude 3 Sonnet
   - Claude 3.5 Sonnet (recommended)
6. Click **Request model access**
7. Wait for approval (usually 5-15 minutes)

#### Configure AWS Credentials

**Option A: Access Keys (Quick Setup)**
```bash
aws configure
```
Enter:
- **Access Key ID**: From AWS Console → IAM → Users → Security credentials
- **Secret Access Key**: From the same location
- **Default region**: `us-east-1`
- **Default output format**: `json`

**Option B: SSO (Enterprise/Recommended)**
```bash
aws configure sso
```
Follow prompts to set up SSO with your organization.

**Option C: Environment Variables**
```bash
# Windows
set AWS_ACCESS_KEY_ID=your-access-key-id
set AWS_SECRET_ACCESS_KEY=your-secret-access-key
set AWS_REGION=us-east-1

# Mac/Linux
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export AWS_REGION=us-east-1
```

**Verify AWS Configuration:**
```bash
# Test basic access
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### Step 3: Clone DocXP Repository

```bash
# Clone the repository
git clone <your-repository-url>
cd docxp

# Verify files are present
ls -la  # Mac/Linux
dir     # Windows
```

### Step 4: Install DocXP

#### Automatic Installation (Recommended)

**Windows:**
```batch
# Run the enhanced startup script
enhanced-start.bat
```

**Mac/Linux:**
```bash
# Make script executable
chmod +x start.sh

# Run the startup script
./start.sh
```

The startup script will:
1. ✅ Validate your environment
2. ✅ Install Python dependencies
3. ✅ Install Node.js dependencies
4. ✅ Initialize local services (PostgreSQL, OpenSearch, Redis)
5. ✅ Create database schemas
6. ✅ Start backend on http://localhost:8001
7. ✅ Start frontend on http://localhost:4200
8. ✅ Open browser automatically

#### Manual Installation (Advanced)

If the automatic installation fails, you can install manually:

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Start backend
python main.py
```

**Frontend Setup (in new terminal):**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Step 5: Verify Installation

#### Check Services

1. **Backend API**: http://localhost:8001/health
   - Should return: `{"status": "healthy"}`

2. **Frontend**: http://localhost:4200
   - Should load the DocXP interface

3. **API Documentation**: http://localhost:8001/docs
   - Should show Swagger/OpenAPI documentation

#### Run Health Checks

```bash
# Comprehensive health check
curl http://localhost:8001/health/detailed

# Individual service checks
curl http://localhost:8001/health/aws
curl http://localhost:8001/health/database
curl http://localhost:8001/health/search
```

#### Test Basic Functionality

1. **Navigate to**: http://localhost:4200
2. **Go to "Enhanced Indexing" tab**
3. **Enter a small repository path** (e.g., the DocXP repository itself)
4. **Click "Start Enhanced Indexing"**
5. **Watch for progress updates**

## 🔧 Optional Service Installation

### jQAssistant (Java Architecture Analysis)

**Ubuntu/Debian:**
```bash
# Add jQAssistant repository
curl -s https://packagecloud.io/install/repositories/buschmais/jqassistant/script.deb.sh | sudo bash

# Install jQAssistant
sudo apt-get install jqassistant
```

**macOS:**
```bash
brew install jqassistant
```

**Manual Installation:**
```bash
# Download jQAssistant
wget https://repo1.maven.org/maven2/com/buschmais/jqassistant/jqassistant-commandline-distribution/2.0.0/jqassistant-commandline-distribution-2.0.0-bin.zip

# Extract
unzip jqassistant-commandline-distribution-2.0.0-bin.zip

# Install to system
sudo mv jqassistant-commandline-distribution-2.0.0 /opt/jqassistant
sudo ln -s /opt/jqassistant/bin/jqassistant.sh /usr/local/bin/jqassistant

# Verify
jqassistant --version
```

### Neo4j (Advanced Graph Analysis)

**Ubuntu/Debian:**
```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 4.4' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update

# Install Neo4j
sudo apt-get install neo4j

# Configure and start
sudo systemctl enable neo4j
sudo systemctl start neo4j

# Set password
sudo neo4j-admin set-initial-password your-password
```

**macOS:**
```bash
brew install neo4j
brew services start neo4j

# Set password via web interface at http://localhost:7474
```

### Semgrep (Static Code Analysis)

```bash
# Install via pip
pip install semgrep

# Or via package manager
# Ubuntu/Debian:
sudo apt-get install semgrep

# macOS:
brew install semgrep

# Verify
semgrep --version
```

## 🛠️ Configuration

### Environment Variables

Create `backend/.env` file for custom configuration:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
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

# Optional Services
ENABLE_JQASSISTANT=true
ENABLE_SEMGREP=true
JQA_NEO4J_URL=bolt://localhost:7687
JQA_NEO4J_USER=neo4j
JQA_NEO4J_PASSWORD=your-neo4j-password

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Performance Tuning

**For Large Repositories:**
```env
INDEXING_MAX_FILES_PER_CHUNK=25
INDEXING_MAX_CHUNK_SIZE_MB=5
V1_MAX_CONCURRENT_JOBS=1
JQA_ANALYSIS_TIMEOUT_HOURS=8
```

**For Development:**
```env
INDEXING_MAX_FILES_PER_CHUNK=100
V1_MAX_CONCURRENT_JOBS=4
ENABLE_JQASSISTANT=false
ENABLE_SEMGREP=false
LOG_LEVEL=DEBUG
```

## 🚨 Troubleshooting

### Installation Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If Python 3.10+ not found, try:
python3 --version
python3.10 --version

# Update aliases if needed (Linux/Mac)
alias python=python3.10
```

#### Node.js Version Issues
```bash
# Check Node.js version
node --version

# If version < 18, update:
# Windows: Download from nodejs.org
# Mac: brew install node@18
# Ubuntu: Follow nodesource instructions above
```

#### Permission Issues (Linux/Mac)
```bash
# Fix permissions for installation directory
sudo chown -R $USER:$USER /path/to/docxp

# Fix pip permissions
pip install --user -r backend/requirements.txt
```

#### Port Conflicts
```bash
# Check what's using ports
# Windows:
netstat -ano | findstr ":8001\|:4200\|:9200\|:6379\|:5432"

# Mac/Linux:
lsof -i :8001,:4200,:9200,:6379,:5432

# Kill conflicting processes
# Windows:
taskkill /F /PID <PID>

# Mac/Linux:
kill -9 <PID>
```

### AWS Configuration Issues

#### Bedrock Access Denied
```bash
# Check if models are available
aws bedrock list-foundation-models --region us-east-1

# If access denied:
# 1. Check AWS Console → Bedrock → Model access
# 2. Request access to Claude models
# 3. Wait for approval (5-15 minutes)
```

#### Invalid Credentials
```bash
# Test credentials
aws sts get-caller-identity

# If invalid:
# 1. Check credentials in AWS Console → IAM
# 2. Regenerate access keys if needed
# 3. Reconfigure: aws configure
```

#### Region Issues
```bash
# Set correct region
aws configure set region us-east-1

# Or use environment variable
export AWS_DEFAULT_REGION=us-east-1
```

### Service Issues

#### Database Connection Failed
```bash
# Check if PostgreSQL is running
# Windows:
sc query postgresql

# Mac/Linux:
ps aux | grep postgres

# Restart database service
# Windows:
net start postgresql

# Mac:
brew services restart postgresql

# Linux:
sudo systemctl restart postgresql
```

#### OpenSearch Not Starting
```bash
# Check OpenSearch status
curl http://localhost:9200/_cluster/health

# Check logs
tail -f /usr/share/opensearch/logs/opensearch.log

# Restart OpenSearch
sudo systemctl restart opensearch
```

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping

# Should return: PONG

# Restart Redis
# Windows:
net restart redis

# Mac:
brew services restart redis

# Linux:
sudo systemctl restart redis
```

### Application Issues

#### Backend Won't Start
```bash
cd backend

# Check for errors in logs
tail -f logs/docxp.log

# Test imports
python -c "from app.core.config import settings; print('Config OK')"

# Check database connection
python -c "from app.core.database import engine; print('Database OK')"

# Start with debug logging
LOG_LEVEL=DEBUG python main.py
```

#### Frontend Won't Start
```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Start with verbose output
npm start --verbose
```

#### Search Not Working
```bash
# Check OpenSearch status
curl http://localhost:9200/_cat/indices

# Recreate indexes
curl -X DELETE http://localhost:9200/docxp-*
curl -X POST http://localhost:8001/api/admin/recreate-indexes
```

## 🔍 Verification Steps

### Complete Installation Verification

1. **System Health Check:**
   ```bash
   curl http://localhost:8001/health/detailed
   ```

2. **Service Connectivity:**
   ```bash
   # Database
   curl http://localhost:8001/health/database
   
   # Search
   curl http://localhost:8001/health/search
   
   # AWS
   curl http://localhost:8001/health/aws
   ```

3. **Frontend Accessibility:**
   - Visit http://localhost:4200
   - All tabs should load without errors

4. **Basic Functionality:**
   - Start an indexing job
   - Perform a search
   - Use the chat interface

5. **Optional Services:**
   ```bash
   # jQAssistant
   jqassistant --version
   
   # Semgrep
   semgrep --version
   
   # Neo4j
   curl http://localhost:7474/
   ```

### Performance Verification

Run a small test repository to verify performance:

```bash
# Create test directory
mkdir test-repo
cd test-repo
echo "print('Hello World')" > test.py
echo "console.log('Hello World')" > test.js

# Index via API
curl -X POST http://localhost:8001/api/enhanced-indexing/start \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "/path/to/test-repo",
    "job_type": "full"
  }'

# Check progress
curl http://localhost:8001/api/enhanced-indexing/status/{job_id}
```

## 🎉 Installation Complete

If you've reached this point successfully, DocXP is now installed and ready to use!

### Next Steps

1. **Read the Quick Start Guide**: [QUICK_START.md](QUICK_START.md)
2. **Explore Features**: Try indexing your first repository
3. **Configure Advanced Features**: [jQAssistant Guide](JQASSISTANT_INTEGRATION_GUIDE.md)
4. **Production Setup**: [Deployment Guide](DEPLOYMENT_GUIDE.md)

### Getting Help

- **Documentation**: [README.md](README.md)
- **API Reference**: http://localhost:8001/docs
- **Health Status**: http://localhost:8001/health/detailed
- **Logs**: `backend/logs/docxp.log`

---

**Welcome to DocXP!** 🎊 Your enterprise code intelligence platform is ready to transform your codebase analysis experience.