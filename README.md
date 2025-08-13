# DocXP - AI-Powered Legacy Code Documentation Platform

![DocXP Logo](frontend/src/assets/docxp-logo.png)

## 🚀 Overview

DocXP is an enterprise-grade AI documentation platform that automatically analyzes and documents legacy codebases, extracting business rules, generating comprehensive documentation, and providing insights into complex systems.

### ✨ Key Features

- **Multi-Language Support**: Python, Java, JavaScript, TypeScript, Perl, Angular, Struts, Struts2, CORBA
- **AI-Powered Analysis**: Leverages AWS Bedrock Claude for intelligent code understanding
- **Business Rule Extraction**: Automatically identifies and documents business logic
- **Architecture Visualization**: Generates system diagrams and dependency graphs
- **Incremental Updates**: Smart documentation updates for evolving codebases
- **Production-Ready**: Comprehensive error handling, logging, and monitoring
- **One-Command Startup**: Simple deployment with validation and diagnostics

## 📋 Prerequisites

- **Python 3.10+** 
- **Node.js 18+ and npm**
- **Git**
- **AWS Account** with Bedrock access (**REQUIRED** - mock mode has been eliminated)
- **AWS Credentials** configured (Access Keys or SSO Profile)
- **1GB free disk space**

## 🚀 Installation & Setup

### First-Time Installation

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd docxp
```

#### Step 2: Configure AWS Credentials (REQUIRED)
Before running DocXP, you MUST configure AWS credentials. Choose one method:

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

**Option C: .env File**
```bash
cd backend
copy .env.template .env  # Windows
cp .env.template .env    # Linux/Mac

# Edit .env file with your credentials
```

#### Step 3: Verify Bedrock Access
```bash
# Test Bedrock access (this should not error)
aws bedrock list-foundation-models --region us-east-1
```

### Quick Start

#### Fastest Way (Windows)
```batch
# Run the enhanced startup script
enhanced-start.bat
```

#### Standard Way (All Platforms)
```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

The application will:
1. ✅ Validate your environment and AWS credentials
2. ✅ Install all dependencies
3. ✅ Create required directories
4. ✅ Initialize the database
5. ✅ Start backend on http://localhost:8001
6. ✅ Start frontend on http://localhost:4200
7. ✅ Open browser automatically

**Important**: The application will fail to start if AWS credentials are not configured.

## 🆘 First Time Setup Guide

### For Users New to AWS

If you're new to AWS or don't have credentials set up:

1. **Create AWS Account**: Visit [aws.amazon.com](https://aws.amazon.com) and create an account
2. **Enable Bedrock Access**: 
   - Go to AWS Console → Bedrock → Model access
   - Request access to Claude models (may take a few minutes to hours)
3. **Create Access Keys**:
   - Go to AWS Console → IAM → Users → Your user → Security credentials
   - Create access key for CLI/API access
   - Save the Access Key ID and Secret Access Key securely

### For Enterprise Users

If your organization uses AWS SSO:

1. **Get SSO Start URL** from your AWS administrator
2. **Configure AWS CLI**:
   ```bash
   aws configure sso
   # Follow prompts to set up SSO profile
   ```
3. **Set Profile**: `export AWS_PROFILE=your-sso-profile`

### Minimal Working Setup

For testing DocXP, you need at minimum:
- AWS Account with Bedrock access enabled
- Claude model access approved in Bedrock console
- Valid AWS credentials configured using one of the methods above

## 🏗️ Architecture

```
DocXP/
├── frontend/               # Angular 18 application
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── dashboard/        # Main dashboard with metrics
│   │   │   │   └── generation-wizard/ # 5-step documentation wizard
│   │   │   └── services/
│   │   │       └── api.service.ts    # Backend API integration
│   │   └── environments/
│   └── package.json
│
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/           # REST endpoints + health checks
│   │   ├── core/          # Configuration, database, logging
│   │   │   ├── logging_config.py    # Enhanced JSON logging
│   │   │   ├── error_handlers.py    # Global exception handling
│   │   │   └── validator.py         # Environment validation
│   │   ├── parsers/       # Language-specific parsers
│   │   ├── services/
│   │   │   └── ai_service.py        # AWS Bedrock integration
│   │   └── models/
│   ├── startup_check.py   # Pre-flight validation
│   ├── diagnose.py        # Diagnostic tool
│   └── requirements.txt
│
├── enhanced-start.bat     # Production startup script
├── test-system.bat        # System test suite
└── logs/                  # Application logs
```

## 🛠️ Production Features

### Health Monitoring
```bash
# Basic health check
curl http://localhost:8001/health

# Detailed health with metrics
curl http://localhost:8001/health/detailed

# Readiness check
curl http://localhost:8001/health/ready

# Liveness probe
curl http://localhost:8001/health/live
```

### Logging & Monitoring
- **Structured JSON logs** in `backend/logs/docxp.log`
- **Error-only logs** in `backend/logs/errors.log`
- **Request tracking** with unique Request-IDs
- **Performance metrics** in response headers
- **Automatic log rotation** (10MB max, 5 backups)

### Error Recovery
- **Automatic service restart** on failure
- **Graceful error handling** with detailed messages
- **Fast-fail with clear errors** when AWS unavailable
- **Database auto-initialization**
- **Port conflict detection**

## 🔧 Configuration

### AWS Setup (REQUIRED)

DocXP requires valid AWS credentials to function. Choose one of these methods:

#### Method 1: AWS CLI Profile (Recommended)
```bash
# Configure AWS CLI with SSO or access keys
aws configure sso
# or
aws configure

# Set profile in environment
export AWS_PROFILE=your-profile-name
```

#### Method 2: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_SESSION_TOKEN=your-token  # if using temporary credentials
export AWS_REGION=us-east-1
```

#### Method 3: .env File
```bash
cd backend
cp .env.template .env
# Edit .env with your credentials:
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
# AWS_REGION=us-east-1
```

**Note**: The application will fail to start without valid AWS credentials. Ensure your AWS account has Bedrock access enabled.

### Custom Configuration
```python
# backend/app/core/config.py
OUTPUT_DIR = "output"
TEMP_DIR = "temp"
LOG_LEVEL = "INFO"
MAX_FILE_SIZE = 10485760  # 10MB
```

## 📊 API Documentation

### Interactive API Docs
Visit http://localhost:8001/docs for Swagger UI

### Key Endpoints

#### Generate Documentation
```http
POST /api/documentation/generate
{
  "repository_path": "/path/to/repo",
  "depth": "comprehensive",
  "include_diagrams": true,
  "include_business_rules": true
}
```

#### Check Job Status
```http
GET /api/documentation/status/{job_id}
```

#### Sync Repository
```http
POST /api/documentation/sync?repo_path=/path/to/repo
```

#### Download Documentation
```http
GET /api/documentation/download/{job_id}
```

## 🔍 Diagnostic Tools

### System Test
```bash
# Run comprehensive system tests
test-system.bat
```

### Environment Validation
```bash
cd backend
python startup_check.py
```

### Troubleshooting
```bash
cd backend
python diagnose.py
```

### View Logs
```bash
# Real-time log monitoring
tail -f backend/logs/docxp.log

# Check for errors
grep ERROR backend/logs/docxp.log

# View as formatted JSON
python -m json.tool backend/logs/docxp.log
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8001
taskkill /F /PID <PID>

# Linux/Mac
lsof -i :8001
kill -9 <PID>
```

### Database Issues
```bash
cd backend
# Delete and recreate database
rm docxp.db  # or del docxp.db on Windows
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules
npm cache clean --force
npm install
```

### Startup Failures
```bash
# If the application fails to start, check these in order:

# 1. Verify AWS credentials
aws sts get-caller-identity

# 2. Check Bedrock access
aws bedrock list-foundation-models --region us-east-1

# 3. Run environment validation
cd backend
python startup_check.py

# 4. Check application logs
tail -f backend/logs/docxp.log

# 5. Manual backend start (for debugging)
cd backend
python main.py
```

### AWS Credentials Issues
The application requires valid AWS credentials and will fail to start without them.

**Common Issues:**
- **"No AWS credentials found"**: Configure credentials using one of the methods above
- **"Failed to initialize Bedrock client"**: Check your AWS region and Bedrock access
- **Permission errors**: Ensure your AWS user/role has Bedrock permissions

**To verify AWS setup:**
```bash
# Test AWS credentials
aws sts get-caller-identity

# Check Bedrock access (requires appropriate permissions)
aws bedrock list-foundation-models --region us-east-1
```

## 📈 Performance

- **Startup time**: ~30 seconds
- **Small repo (<100 files)**: 1-2 minutes
- **Medium repo (100-500 files)**: 3-5 minutes
- **Large repo (>500 files)**: 5-10 minutes
- **Request tracking**: X-Process-Time header
- **Health checks**: <100ms response time

## 🔒 Security Features

- **Request ID tracking** for audit trails
- **Sanitized error messages** (no sensitive data)
- **Input validation** with Pydantic
- **CORS restricted** to localhost
- **SQL injection prevention** via ORM
- **Comprehensive logging** for security audits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`test-system.bat`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📚 Documentation

- [API Reference](http://localhost:8001/docs)
- [Quick Start Guide](QUICK_START.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [TODO - Enterprise Features](TODO.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AWS Bedrock team for AI capabilities
- Angular team for the excellent framework
- FastAPI for high-performance backend
- PrimeNG for beautiful UI components

## 📞 Support

For issues and questions:
- Run diagnostics: `python backend/diagnose.py`
- Check health: http://localhost:8001/health/detailed
- View logs: `backend/logs/docxp.log`
- Email: support@docxp.ai
- Documentation: [docs.docxp.ai](https://docs.docxp.ai)

---

**DocXP v2.1** - *Production-Ready Enterprise Documentation Platform*
