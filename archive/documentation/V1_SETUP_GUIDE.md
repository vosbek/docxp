# DocXP V1 Local-First Setup Guide

🚀 **Quick setup guide for the new V1 local-first architecture with OpenSearch, PostgreSQL, and RRF hybrid search**

## 📋 Prerequisites

### Required Software
- **Podman Desktop** or **Docker Desktop** (for container orchestration)
- **Git** (for cloning and version control)
- **AWS Account** with Bedrock access (**REQUIRED** for embeddings and AI)

### AWS Bedrock Requirements
- Active AWS account with Bedrock enabled
- Claude 3.5 Sonnet access approved in Bedrock console
- Titan Text Embedding v2 access approved
- Valid AWS credentials (CLI profile or environment variables)

## 🎯 Quick Start (5 Minutes)

### Step 1: Clone and Navigate
```bash
git clone <repository-url>
cd docxp
```

### Step 2: Configure AWS Credentials
Choose **one** method:

**Option A: AWS CLI (Recommended)**
```bash
# Install AWS CLI if needed
# Windows: Download from https://aws.amazon.com/cli/
# Linux/Mac: pip install awscli

# Configure credentials
aws configure

# Test access
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-east-1
```

**Option B: Environment Variables**
```bash
# Set environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key  
export AWS_REGION=us-east-1
```

**Option C: Create .env file**
```bash
# Copy template and edit
cp .env.example .env

# Edit .env with your AWS credentials:
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_REGION=us-east-1
```

### Step 3: Start V1 Stack
```bash
# Windows
start-v1.bat

# Linux/Mac (if podman-compose available)
podman-compose up --build
```

🎉 **That's it!** The V1 stack will start automatically with:
- ✅ OpenSearch (single-node with auto-detection)
- ✅ PostgreSQL (with golden questions sample data)
- ✅ Redis (queue + caching)
- ✅ MinIO (S3-compatible storage)
- ✅ FastAPI Backend (with hybrid search)
- ✅ RQ Worker (background processing)

## 🌐 Access Points

After startup, you can access:

| Service | URL | Purpose |
|---------|-----|---------|
| **Backend API** | http://localhost:8000 | Main API endpoints |
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | System status |
| **OpenSearch** | http://localhost:9200 | Search engine |
| **MinIO Console** | http://localhost:9001 | Storage management |

## 🔍 Test the Hybrid Search

### Quick Health Check
```bash
# Test system health
curl http://localhost:8000/health

# Test search engine health
curl http://localhost:8000/v1/search/health
```

### Demo Questions
```bash
# Test a golden question
curl -X POST http://localhost:8000/v1/search/golden-questions \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Where does Specified Amount come from?",
    "max_results": 3
  }'

# Get predefined demo questions
curl http://localhost:8000/v1/search/demo-questions
```

### Quick Search Test
```bash
# Simple search test
curl "http://localhost:8000/v1/search/quick-search?q=customer&limit=5"
```

## 📊 V1 Architecture

```
DocXP V1 Local-First Stack
├── OpenSearch (9200)          # BM25 + k-NN search with auto-detection
├── PostgreSQL (5432)          # Primary database (replaces dual SQLite)
├── Redis (6379)               # Queue management + caching
├── MinIO (9000/9001)          # S3-compatible object storage
├── FastAPI Backend (8000)     # RRF hybrid search + APIs
└── RQ Worker                  # Background job processing
```

## 🧪 Testing the System

### 1. Basic Health Checks
```bash
# System health
curl http://localhost:8000/health

# Search engine health  
curl http://localhost:8000/v1/search/health

# Database health
curl http://localhost:8000/health/db
```

### 2. Search Functionality
```bash
# Hybrid search
curl -X POST http://localhost:8000/v1/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "customer validation",
    "max_results": 10,
    "file_types": ["java", "jsp"]
  }'

# Golden questions (demo scenario)
curl -X POST http://localhost:8000/v1/search/golden-questions \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How is customer data validated?",
    "max_results": 3
  }'
```

### 3. Performance Validation
```bash
# Check search metrics
curl http://localhost:8000/v1/search/metrics

# Prometheus metrics
curl http://localhost:8000/metrics
```

## 🛠️ Development Setup

### Running Individual Services

If you need to run services individually for development:

```bash
# Start only infrastructure
podman-compose up postgres opensearch redis minio -d

# Run backend manually
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run worker manually  
cd backend
python -m rq worker --url redis://localhost:6379/1
```

### Environment Configuration

Key environment variables in `.env`:

```bash
# AWS Bedrock (REQUIRED)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0

# OpenSearch Configuration
OPENSEARCH_HOST=opensearch
OPENSEARCH_PORT=9200
OPENSEARCH_EMBED_DIM_AUTO_DETECT=true

# RRF Search Parameters (GPT-5 specified)
RRF_K=60
RRF_BM25_WEIGHT=1.2
RRF_KNN_WEIGHT=1.0

# Performance SLOs
TARGET_SEARCH_LATENCY_P50_MS=700
TARGET_SEARCH_LATENCY_P95_MS=1200
```

## 🐛 Troubleshooting

### Common Issues

**1. AWS Credentials Not Found**
```bash
# Verify credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

**2. Podman/Docker Issues**
```bash
# Restart podman
podman system reset

# Check containers
podman ps -a

# View logs
podman-compose logs backend
```

**3. OpenSearch Won't Start**
```bash
# Check ulimits (Linux/Mac)
ulimit -n 65536
ulimit -l unlimited

# Windows: Usually works out of the box
```

**4. Port Conflicts**
```bash
# Check what's using ports
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Kill processes if needed
taskkill /F /PID <PID>        # Windows  
kill -9 <PID>                 # Linux/Mac
```

### Service-Specific Logs

```bash
# View all logs
podman-compose logs

# View specific service logs
podman-compose logs backend
podman-compose logs opensearch
podman-compose logs postgres

# Follow logs in real-time
podman-compose logs -f backend
```

### Manual Testing

```bash
# Test OpenSearch directly
curl http://localhost:9200

# Test PostgreSQL connection
podman exec -it docxp-postgres-1 psql -U docxp_user -d docxp

# Test Redis connection
podman exec -it docxp-redis-1 redis-cli ping

# Test MinIO connection
curl http://localhost:9000/minio/health/live
```

## 🎯 Next Steps

Once the V1 stack is running:

1. **Index a Repository**: Use the repository processing endpoints to index code
2. **Test Golden Questions**: Try the demo questions to see citations in action  
3. **Performance Testing**: Run searches and check p50/p95 latencies
4. **Frontend Integration**: Connect the Angular frontend to the V1 APIs

## 📞 Support

**If you encounter issues:**

1. Check the health endpoints first: http://localhost:8000/health
2. Review service logs: `podman-compose logs`
3. Verify AWS credentials: `aws sts get-caller-identity`
4. Check the audit log: `AUDIT.md` for known issues

**Key Files:**
- `podman-compose.yml` - Service orchestration
- `.env.example` - Configuration template  
- `start-v1.bat` - Windows startup script
- `backend/app/core/opensearch_setup.py` - Auto-detection logic
- `AUDIT.md` - Implementation tracking

---

🚀 **DocXP V1 Local-First Architecture** - Ready for enterprise code exploration with hybrid search and grounded citations!