# DocXP Deployment Guide

## 🚀 Deployment Options

### Option 1: Local Development
Perfect for testing and single-user scenarios.

```batch
# Windows
enhanced-start.bat

# Linux/Mac
./enhanced-start.sh
```

### Option 2: Docker Deployment (Recommended for Production)
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: docxp-backend
    ports:
      - "8001:8001"
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./backend/output:/app/output
      - ./backend/logs:/app/logs
      - docxp-db:/app/database
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: docxp-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  docxp-db:
```

### Option 3: Kubernetes Deployment
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docxp-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docxp-backend
  template:
    metadata:
      labels:
        app: docxp-backend
    spec:
      containers:
      - name: backend
        image: docxp/backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          value: "postgresql://user:pass@postgres:5432/docxp"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

## 📋 Pre-Deployment Checklist

### System Requirements
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] 2GB RAM minimum (4GB recommended)
- [ ] 10GB disk space
- [ ] Network access to AWS Bedrock (optional)

### Environment Validation
```bash
# Run validation script
cd backend
python startup_check.py

# Run diagnostic tool
python diagnose.py

# Test system
cd ..
test-system.bat
```

### Security Checklist
- [ ] Change default passwords
- [ ] Configure HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Configure CORS properly
- [ ] Set secure session tokens
- [ ] Enable rate limiting

## 🔧 Configuration

### Environment Variables
```bash
# Required
DATABASE_URL=sqlite:///docxp.db  # or PostgreSQL for production
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Optional (for AI features)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-v2

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=300
MAX_FILE_SIZE=10485760
```

### Production Database (PostgreSQL)
```python
# backend/app/core/config.py
DATABASE_URL = "postgresql://user:password@localhost/docxp"
```

```sql
-- Create database
CREATE DATABASE docxp;
CREATE USER docxp_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE docxp TO docxp_user;
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name docxp.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name docxp.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Frontend
    location / {
        proxy_pass http://localhost:4200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running documentation generation
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Health checks
    location /health {
        proxy_pass http://localhost:8001/health;
        access_log off;
    }
}
```

## 🔍 Monitoring

### Health Check Endpoints
```bash
# Kubernetes/Docker health checks
/health/live    # Liveness probe
/health/ready   # Readiness probe
/health         # Basic health
/health/detailed # Full system status
```

### Prometheus Metrics (Future)
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'docxp'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
```

### Log Aggregation
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

## 🚀 Performance Optimization

### Backend Optimization
```python
# Use async processing
MAX_WORKERS = 4
ENABLE_CACHE = True
CACHE_TTL = 3600

# Database connection pooling
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_RECYCLE = 3600
```

### Frontend Optimization
```bash
# Production build
cd frontend
npm run build --prod

# Enable compression
npm install compression
```

### Caching Strategy
- **Redis** for session management
- **CDN** for static assets
- **Browser caching** for API responses
- **Database query caching**

## 🔒 Security Hardening

### API Security
```python
# Rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/documentation/generate")
@limiter.limit("10/minute")
async def generate_documentation():
    pass
```

### Authentication (Future)
```python
# JWT tokens
from fastapi_jwt_auth import AuthJWT

@app.post('/login')
def login(user: UserLogin, Authorize: AuthJWT = Depends()):
    access_token = Authorize.create_access_token(subject=user.username)
    return {"access_token": access_token}
```

## 📊 Scaling Considerations

### Horizontal Scaling
- Use **load balancer** (nginx, HAProxy)
- Deploy multiple **backend instances**
- Use **Redis** for shared session state
- Implement **message queue** (RabbitMQ, Celery)

### Vertical Scaling
- Increase **CPU cores** for parallel processing
- Add **RAM** for larger repositories
- Use **SSD storage** for faster I/O
- Optimize **database indexes**

## 🔄 Backup & Recovery

### Database Backup
```bash
# SQLite backup
cp docxp.db docxp_backup_$(date +%Y%m%d).db

# PostgreSQL backup
pg_dump docxp > docxp_backup_$(date +%Y%m%d).sql
```

### Documentation Backup
```bash
# Backup generated documentation
tar -czf output_backup_$(date +%Y%m%d).tar.gz output/
```

### Disaster Recovery Plan
1. **Daily backups** to cloud storage
2. **Point-in-time recovery** for database
3. **Redundant deployments** across regions
4. **Automated failover** with health checks

## 📈 Monitoring Dashboard

### Grafana Setup
```json
{
  "dashboard": {
    "title": "DocXP Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {"expr": "rate(http_requests_total[5m])"}
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {"expr": "rate(http_errors_total[5m])"}
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {"expr": "histogram_quantile(0.95, http_request_duration_seconds)"}
        ]
      }
    ]
  }
}
```

## 🚦 Deployment Steps

### 1. Pre-deployment
```bash
# Run tests
test-system.bat

# Validate environment
python backend/startup_check.py

# Build frontend
cd frontend
npm run build --prod
```

### 2. Deploy Backend
```bash
# Copy files to server
scp -r backend/ user@server:/app/

# Install dependencies
ssh user@server
cd /app/backend
pip install -r requirements.txt

# Start with systemd
sudo systemctl start docxp-backend
```

### 3. Deploy Frontend
```bash
# Copy built files
scp -r frontend/dist/ user@server:/var/www/docxp/

# Configure nginx
sudo nginx -s reload
```

### 4. Post-deployment
```bash
# Verify health
curl https://docxp.yourdomain.com/health/detailed

# Check logs
tail -f /app/backend/logs/docxp.log

# Monitor metrics
```

## 🔧 Troubleshooting Production Issues

### High Memory Usage
```bash
# Check memory
free -h
ps aux | grep python

# Restart services
sudo systemctl restart docxp-backend
```

### Slow Performance
```bash
# Check CPU
top -n 1

# Check disk I/O
iostat -x 1

# Analyze slow queries
tail -f logs/docxp.log | grep "duration"
```

### Connection Issues
```bash
# Check ports
netstat -tulpn | grep -E "8001|80"

# Test connectivity
curl -I http://localhost:8001/health

# Check firewall
sudo iptables -L
```

## 📞 Support

For production support:
- 📧 Email: enterprise@docxp.ai
- 📱 Phone: +1-555-DOCXP-00
- 💬 Slack: docxp-support.slack.com
- 📚 Docs: https://docs.docxp.ai

---

**DocXP Enterprise Deployment** - Ready for Production! 🚀
