# DocXP Deployment Guide

## 🚀 Deployment Options

### Option 1: Docker Deployment (Recommended for Production)

#### Prerequisites
- Docker and Docker Compose installed
- AWS credentials configured

#### Steps

1. **Clone and Configure**
```bash
cd C:\devl\workspaces\docxp
copy backend\.env.template backend\.env
# Edit backend\.env with your AWS credentials
```

2. **Build and Run with Docker Compose**
```bash
docker-compose up --build
```

3. **Access Application**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

#### Production Deployment

For production, modify `docker-compose.yml`:
```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/docxp
    # Add production database service
  
  frontend:
    ports:
      - "443:443"  # Use HTTPS in production
```

### Option 2: Kubernetes Deployment

#### Kubernetes Manifests

1. **Create namespace**
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: docxp
```

2. **Backend Deployment**
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docxp-backend
  namespace: docxp
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
        image: docxp-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: access-key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: secret-key
```

3. **Apply manifests**
```bash
kubectl apply -f namespace.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml
```

### Option 3: Cloud Deployment

#### AWS ECS Deployment

1. **Build and push images to ECR**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [your-ecr-uri]

docker build -t docxp-backend ./backend
docker tag docxp-backend:latest [your-ecr-uri]/docxp-backend:latest
docker push [your-ecr-uri]/docxp-backend:latest

docker build -t docxp-frontend ./frontend
docker tag docxp-frontend:latest [your-ecr-uri]/docxp-frontend:latest
docker push [your-ecr-uri]/docxp-frontend:latest
```

2. **Create ECS Task Definitions**
```json
{
  "family": "docxp-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "[your-ecr-uri]/docxp-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ],
      "secrets": [
        {
          "name": "AWS_ACCESS_KEY_ID",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:docxp/aws-credentials:access-key::"
        }
      ]
    }
  ]
}
```

3. **Create ECS Service**
```bash
aws ecs create-service \
  --cluster docxp-cluster \
  --service-name docxp-backend \
  --task-definition docxp-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

#### Azure Container Instances

```bash
# Create resource group
az group create --name docxp-rg --location eastus

# Create container instances
az container create \
  --resource-group docxp-rg \
  --name docxp-backend \
  --image docxp-backend:latest \
  --dns-name-label docxp-api \
  --ports 8000 \
  --environment-variables \
    AWS_REGION=us-east-1 \
  --secure-environment-variables \
    AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
```

### Option 4: Traditional Server Deployment

#### On-Premise Server Setup

1. **Install Dependencies**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3-pip nodejs npm nginx postgresql

# RHEL/CentOS
sudo yum install python3 nodejs postgresql nginx
```

2. **Setup Backend**
```bash
cd /opt/docxp/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo cat > /etc/systemd/system/docxp-backend.service << EOF
[Unit]
Description=DocXP Backend API
After=network.target

[Service]
Type=simple
User=docxp
WorkingDirectory=/opt/docxp/backend
Environment="PATH=/opt/docxp/backend/venv/bin"
ExecStart=/opt/docxp/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable docxp-backend
sudo systemctl start docxp-backend
```

3. **Setup Frontend**
```bash
cd /opt/docxp/frontend
npm install
npm run build

# Configure nginx
sudo cp -r dist/docxp-frontend/* /var/www/docxp/
sudo cp nginx.conf /etc/nginx/sites-available/docxp
sudo ln -s /etc/nginx/sites-available/docxp /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## 🔒 Security Considerations

### SSL/TLS Configuration

1. **Using Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d docxp.yourdomain.com
```

2. **Update nginx configuration**
```nginx
server {
    listen 443 ssl http2;
    server_name docxp.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/docxp.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docxp.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    location / {
        root /var/www/docxp;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Variables Security

1. **Use AWS Secrets Manager**
```python
import boto3
import json

def get_secret():
    secret_name = "docxp/production"
    region_name = "us-east-1"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
```

2. **Use HashiCorp Vault**
```bash
vault kv put secret/docxp \
  aws_access_key_id="..." \
  aws_secret_access_key="..." \
  database_url="..."
```

## 📊 Monitoring & Logging

### Application Monitoring

1. **Prometheus + Grafana**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'docxp-backend'
    static_configs:
      - targets: ['localhost:8000']
```

2. **ELK Stack Setup**
```bash
# Install Elasticsearch, Logstash, Kibana
docker-compose -f elk-stack.yml up -d

# Configure Logstash
input {
  file {
    path => "/var/log/docxp/*.log"
    start_position => "beginning"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "docxp-%{+YYYY.MM.dd}"
  }
}
```

### Health Checks

1. **Backend Health Endpoint**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": check_database_connection(),
        "aws": check_aws_connection()
    }
```

2. **Frontend Health Check**
```typescript
// health.service.ts
checkHealth(): Observable<HealthStatus> {
  return this.http.get<HealthStatus>('/api/health')
    .pipe(
      timeout(5000),
      catchError(() => of({ status: 'unhealthy' }))
    );
}
```

## 🔄 Backup & Recovery

### Database Backup

1. **Automated Backups**
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/docxp"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/opt/docxp/backend/docxp.db"

# SQLite backup
sqlite3 $DB_FILE ".backup ${BACKUP_DIR}/docxp_${DATE}.db"

# PostgreSQL backup (if using)
# pg_dump -U docxp -d docxp > ${BACKUP_DIR}/docxp_${DATE}.sql

# Compress and encrypt
tar czf ${BACKUP_DIR}/docxp_${DATE}.tar.gz ${BACKUP_DIR}/docxp_${DATE}.*
gpg --encrypt --recipient backup@company.com ${BACKUP_DIR}/docxp_${DATE}.tar.gz

# Upload to S3
aws s3 cp ${BACKUP_DIR}/docxp_${DATE}.tar.gz.gpg s3://docxp-backups/

# Clean old local backups
find ${BACKUP_DIR} -name "*.tar.gz*" -mtime +7 -delete
```

2. **Schedule with Cron**
```bash
# Add to crontab
0 2 * * * /opt/docxp/scripts/backup.sh
```

### Disaster Recovery

1. **Recovery Procedure**
```bash
# Download latest backup
aws s3 cp s3://docxp-backups/docxp_latest.tar.gz.gpg .

# Decrypt and extract
gpg --decrypt docxp_latest.tar.gz.gpg | tar xzf -

# Restore database
sqlite3 /opt/docxp/backend/docxp.db < docxp_backup.db

# Restart services
sudo systemctl restart docxp-backend
sudo systemctl restart nginx
```

## 🔧 Maintenance

### Updates and Patches

1. **Zero-Downtime Deployment**
```bash
# Blue-Green Deployment
docker-compose -f docker-compose.blue.yml up -d
# Test new version
# If successful, switch traffic
docker-compose -f docker-compose.green.yml down
```

2. **Rolling Updates (Kubernetes)**
```bash
kubectl set image deployment/docxp-backend \
  backend=docxp-backend:v1.1.0 \
  --record
  
kubectl rollout status deployment/docxp-backend
```

### Performance Tuning

1. **Backend Optimization**
```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
)
```

2. **Frontend Optimization**
```typescript
// Lazy loading modules
const routes: Routes = [
  {
    path: 'generation',
    loadChildren: () => import('./generation/generation.module')
      .then(m => m.GenerationModule)
  }
];
```

## 📈 Scaling Strategies

### Horizontal Scaling
- Add more backend instances behind load balancer
- Use Redis for session management
- Implement database read replicas

### Vertical Scaling
- Increase CPU/RAM for processing nodes
- Use GPU instances for AI processing
- Optimize database queries and indexes

## 🎯 Production Checklist

- [ ] SSL/TLS certificates configured
- [ ] Environment variables secured
- [ ] Database backups scheduled
- [ ] Monitoring and alerting setup
- [ ] Log aggregation configured
- [ ] Health checks implemented
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Security headers added
- [ ] Error tracking (Sentry) integrated
- [ ] Documentation updated
- [ ] Disaster recovery plan tested
- [ ] Performance benchmarks established
- [ ] Compliance requirements met
- [ ] User acceptance testing completed

---

For support, contact the DevOps team or refer to the troubleshooting guide.
