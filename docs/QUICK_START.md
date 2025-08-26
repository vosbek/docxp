# DocXP Quick Start Guide

## ⚡ Get Running in 5 Minutes

### Prerequisites Check
- ✅ Python 3.10+ installed
- ✅ Node.js 18+ installed  
- ✅ Git installed
- ✅ AWS account with Bedrock access (**REQUIRED**)

### Step 1: AWS Setup (2 minutes)
```bash
# Install AWS CLI if needed
# Windows: Download from https://aws.amazon.com/cli/
# Mac: brew install awscli
# Linux: pip install awscli

# Configure credentials (choose one):

# Option A: Access Keys
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)

# Option B: SSO (Enterprise)
aws configure sso

# Verify it works
aws sts get-caller-identity
```

### Step 2: Clone and Start (3 minutes)
```bash
# Clone repository
git clone <your-repo-url>
cd docxp

# Start everything (Windows)
enhanced-start.bat

# Start everything (Mac/Linux)
chmod +x start.sh
./start.sh
```

### Step 3: Verify It's Working
1. **Backend API**: http://localhost:8001/health
2. **Frontend**: http://localhost:4200 (opens automatically)
3. **API Docs**: http://localhost:8001/docs

## 🎯 First Analysis

### Analyze Your First Repository

1. **Open DocXP**: http://localhost:4200
2. **Navigate to "Enhanced Indexing" tab**
3. **Enter repository path**: `/path/to/your/code`
4. **Click "Start Enhanced Indexing"**
5. **Watch progress in real-time**

### What DocXP Will Do
- 📁 **Scan files** (Python, Java, JS, TS, etc.)
- 🔍 **Generate embeddings** for semantic search
- 🏗️ **Analyze architecture** (for Java projects)
- 🛡️ **Run security analysis** (if Semgrep installed)
- 💬 **Enable AI chat** with your codebase

## 🚀 Key Features to Try

### 1. Semantic Search
- Search: "find user authentication logic"
- Search: "database connection setup"
- Search: "error handling patterns"

### 2. AI Chat
- Ask: "How does user login work?"
- Ask: "Show me the main entry points"
- Ask: "What are the security vulnerabilities?"

### 3. Architecture Analysis (Java)
- View dependency graphs
- Check architectural violations
- Get quality metrics and recommendations

### 4. Code Flow Analysis
- Trace JSP → Struts → Service flows
- Find Angular component dependencies
- Analyze CORBA interface usage

## 🔧 Troubleshooting

### "AWS credentials not found"
```bash
# Check if credentials are configured
aws sts get-caller-identity

# If not working, reconfigure
aws configure
```

### "Bedrock access denied"
```bash
# Check Bedrock access (should list models)
aws bedrock list-foundation-models --region us-east-1

# If fails: Enable Bedrock in AWS Console → Bedrock → Model access
```

### "Port 8001 already in use"
```bash
# Windows
netstat -ano | findstr :8001
taskkill /F /PID <PID>

# Mac/Linux
lsof -i :8001
kill -9 <PID>
```

### Application won't start
```bash
# Check logs
tail -f backend/logs/docxp.log

# Run diagnostics
cd backend
python -m app.core.validator
```

## ⚙️ Quick Configuration

### For Large Repositories (>10k files)
Create `backend/.env`:
```env
INDEXING_MAX_FILES_PER_CHUNK=25
V1_MAX_CONCURRENT_JOBS=1
JQA_ANALYSIS_TIMEOUT_HOURS=8
```

### For Development/Testing
```env
INDEXING_MAX_FILES_PER_CHUNK=100
V1_MAX_CONCURRENT_JOBS=4
ENABLE_JQASSISTANT=false
ENABLE_SEMGREP=false
```

### Skip Optional Features
```env
# Skip Java architecture analysis
ENABLE_JQASSISTANT=false

# Skip static code analysis
ENABLE_SEMGREP=false

# Lightweight mode
INDEXING_MODE=lightweight
```

## 📊 Performance Expectations

| Repository Size | Expected Time | Memory Usage |
|-----------------|---------------|--------------|
| Small (<1k files) | 2-5 minutes | 2-4 GB |
| Medium (1-10k files) | 10-30 minutes | 4-8 GB |
| Large (10-50k files) | 1-3 hours | 8-16 GB |

## 🆘 Getting Help

### Health Checks
```bash
# Overall health
curl http://localhost:8001/health/detailed

# Component health
curl http://localhost:8001/health/aws
curl http://localhost:8001/health/database
curl http://localhost:8001/health/search
```

### View Logs
```bash
# Real-time logs
tail -f backend/logs/docxp.log

# Error logs only
grep ERROR backend/logs/docxp.log

# Last 100 lines
tail -100 backend/logs/docxp.log
```

### Common Solutions
```bash
# Reset everything (nuclear option)
cd backend
python -c "from app.core.database import reset_database; import asyncio; asyncio.run(reset_database())"
curl -X DELETE http://localhost:9200/docxp-*
redis-cli flushall

# Then restart
enhanced-start.bat  # Windows
./start.sh          # Mac/Linux
```

## 🎉 Success Indicators

You'll know DocXP is working when:
- ✅ Backend health check returns `{"status": "healthy"}`
- ✅ Frontend loads at http://localhost:4200
- ✅ You can start an indexing job
- ✅ Search returns results
- ✅ Chat interface responds

## 📚 Next Steps

1. **Read Full Documentation**: [README.md](README.md)
2. **Explore API**: http://localhost:8001/docs
3. **Configure Advanced Features**: [jQAssistant Guide](JQASSISTANT_INTEGRATION_GUIDE.md)
4. **Production Setup**: [Deployment Guide](DEPLOYMENT_GUIDE.md)

---

**Need Help?** Check http://localhost:8001/health/detailed and backend/logs/docxp.log for diagnostic information.
