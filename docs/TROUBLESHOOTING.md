# DocXP Troubleshooting Guide

## 🔧 Quick Diagnostic Commands

```bash
# Run comprehensive diagnostics
cd backend
python diagnose.py

# Check environment
python startup_check.py

# Test system
cd ..
test-system.bat

# Check health
curl http://localhost:8001/health/detailed
```

## 🚨 Common Issues & Solutions

### 1. Application Won't Start

#### Symptom: "Python is not installed or not in PATH"
**Solution:**
```bash
# Windows - Install Python 3.10+
1. Download from https://www.python.org/downloads/
2. During installation, CHECK "Add Python to PATH"
3. Restart terminal
4. Verify: python --version
```

#### Symptom: "Node.js is not installed or not in PATH"
**Solution:**
```bash
# Install Node.js 18+
1. Download from https://nodejs.org/
2. Install LTS version
3. Restart terminal
4. Verify: node --version
```

#### Symptom: "Port 8001 is already in use"
**Solution:**
```bash
# Windows - Find and kill process
netstat -ano | findstr :8001
# Note the PID in the last column
taskkill /F /PID <PID>

# Linux/Mac
lsof -i :8001
kill -9 <PID>

# Or change port in backend/main.py
uvicorn.run(app, host="0.0.0.0", port=8002)  # Use different port
```

#### Symptom: "Port 4200 is already in use"
**Solution:**
```bash
# Windows
netstat -ano | findstr :4200
taskkill /F /PID <PID>

# Or use different port
ng serve --port 4201
```

### 2. Backend Issues

#### Symptom: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:**
```bash
cd backend
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install requirements
pip install -r requirements.txt
```

#### Symptom: "AWS credentials not configured"
**Solution:**
```bash
# Option 1: Create .env file
cd backend
copy .env.template .env
# Edit .env and add your AWS credentials

# Option 2: Set environment variables
set AWS_ACCESS_KEY_ID=your-key
set AWS_SECRET_ACCESS_KEY=your-secret

# Option 3: Continue without AWS (uses mock mode)
# The app will work but AI features will use patterns instead
```

#### Symptom: "Database error" or "No such table"
**Solution:**
```bash
cd backend
# Delete old database
del docxp.db  # Windows
rm docxp.db   # Linux/Mac

# Recreate database
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

#### Symptom: "ImportError: cannot import name 'select'"
**Solution:**
```bash
# This has been fixed, but if you see it:
# Edit backend/app/api/documentation.py
# Add at top: from sqlalchemy import select
```

### 3. Frontend Issues

#### Symptom: "Cannot find module '@angular/core'"
**Solution:**
```bash
cd frontend
# Clean install
rmdir /s /q node_modules  # Windows
rm -rf node_modules        # Linux/Mac

npm cache clean --force
npm install
```

#### Symptom: "ng: command not found"
**Solution:**
```bash
# Install Angular CLI globally
npm install -g @angular/cli

# Or use local version
npx ng serve
```

#### Symptom: Frontend won't compile
**Solution:**
```bash
cd frontend
# Check for errors
npm run build

# Common fixes:
1. Delete node_modules and reinstall
2. Check TypeScript errors in VS Code
3. Clear Angular cache: rm -rf .angular
```

### 4. API Connection Issues

#### Symptom: "CORS error" in browser console
**Solution:**
```python
# Check backend/main.py has correct CORS settings:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Symptom: "Failed to fetch" or "Network error"
**Solution:**
```bash
# Verify backend is running
curl http://localhost:8001/health

# Check frontend API URL in api.service.ts
private apiUrl = 'http://localhost:8001/api';  # Should be 8001, not 8000
```

### 5. Documentation Generation Issues

#### Symptom: "Repository not found"
**Solution:**
```bash
# Use absolute paths
C:\projects\my-repo  # Windows
/home/user/projects/my-repo  # Linux/Mac

# Avoid:
./my-repo  # Relative paths may not work
~/my-repo  # Tilde expansion may fail
```

#### Symptom: Generation stuck at "pending"
**Solution:**
```bash
# Check logs for errors
type backend\logs\docxp.log  # Windows
tail -f backend/logs/docxp.log  # Linux/Mac

# Common causes:
1. Large repository (be patient)
2. AWS rate limiting (wait and retry)
3. Database locked (restart backend)
```

#### Symptom: "No business rules detected"
**Solution:**
```bash
# This is normal if:
1. AWS is not configured (using mock mode)
2. Code has no clear business logic
3. Repository is very small

# To get real AI analysis:
1. Configure AWS credentials
2. Enable Bedrock in your AWS account
```

### 6. Performance Issues

#### Symptom: Slow documentation generation
**Solution:**
```python
# Optimize configuration:
1. Use "standard" depth instead of "comprehensive"
2. Exclude unnecessary patterns:
   - node_modules
   - .git
   - dist
   - build
3. Use incremental sync for updates
```

#### Symptom: High memory usage
**Solution:**
```bash
# Monitor memory
# Windows Task Manager or:
wmic process where name="python.exe" get ProcessId,WorkingSetSize

# Fixes:
1. Process smaller repositories
2. Increase system RAM
3. Close other applications
```

#### Symptom: Frontend lag
**Solution:**
```bash
# Use production build
cd frontend
npm run build --prod
# Serve from dist/ folder

# Or reduce polling frequency
# In dashboard.component.ts, change:
setInterval(() => {...}, 60000);  # Poll every 60s instead of 30s
```

### 7. Logging & Debugging

#### View Logs
```bash
# Application logs (JSON format)
type backend\logs\docxp.log

# Error-only logs
type backend\logs\errors.log

# Pretty-print JSON logs
python -m json.tool backend\logs\docxp.log

# Search for specific errors
findstr ERROR backend\logs\docxp.log  # Windows
grep ERROR backend/logs/docxp.log      # Linux/Mac
```

#### Enable Debug Logging
```python
# backend/app/core/logging_config.py
setup_logging(log_level="DEBUG")

# Or set environment variable
set LOG_LEVEL=DEBUG
```

#### Trace Specific Request
```bash
# Find request ID in response headers
curl -i http://localhost:8001/api/documentation/generate

# Search logs for that request ID
findstr "request-id-here" backend\logs\docxp.log
```

### 8. Docker Issues

#### Symptom: "docker: command not found"
**Solution:**
```bash
# Install Docker Desktop from:
https://www.docker.com/products/docker-desktop/
```

#### Symptom: Container won't start
**Solution:**
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

### 9. System Resource Issues

#### Symptom: "Insufficient disk space"
**Solution:**
```bash
# Check disk space
# Windows
fsutil volume diskfree c:

# Clean up
1. Delete old logs: del backend\logs\*.log
2. Clean output: rmdir /s /q backend\output
3. Clean temp: rmdir /s /q backend\temp
4. Clean npm cache: npm cache clean --force
```

#### Symptom: "Out of memory"
**Solution:**
```bash
# Check memory usage
tasklist /FI "IMAGENAME eq python.exe"

# Solutions:
1. Close other applications
2. Restart DocXP
3. Process smaller repositories
4. Add more RAM
```

### 10. Quick Recovery Steps

#### Complete Reset
```bash
# Stop all services
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Clean everything
cd backend
del docxp.db
rmdir /s /q output temp logs __pycache__
rmdir /s /q venv

cd ..\frontend
rmdir /s /q node_modules .angular dist

# Restart fresh
cd ..
enhanced-start.bat
```

#### Database Reset
```bash
cd backend
del docxp.db
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

#### Frontend Reset
```bash
cd frontend
rmdir /s /q node_modules .angular
npm cache clean --force
npm install
ng serve
```

## 🔍 Advanced Troubleshooting

### Enable Detailed Tracing
```python
# backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
```

### Check System Health
```bash
# Detailed health check
curl http://localhost:8001/health/detailed | python -m json.tool

# Interpret results:
- "healthy" = All good
- "degraded" = Some issues but working
- "unhealthy" = Critical problems
```

### Performance Profiling
```python
# Add to backend/main.py
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 📞 Getting Help

1. **Run diagnostics first:**
   ```bash
   python backend/diagnose.py
   ```

2. **Check the logs:**
   ```bash
   type backend\logs\docxp.log
   ```

3. **Verify system health:**
   ```bash
   curl http://localhost:8001/health/detailed
   ```

4. **Search for error message:**
   - Check this guide
   - Search in logs
   - Check GitHub issues

5. **Create detailed bug report with:**
   - Error message
   - Diagnostic report
   - Steps to reproduce
   - System information

## 💡 Prevention Tips

1. **Always run validation before starting:**
   ```bash
   python backend/startup_check.py
   ```

2. **Use the enhanced startup script:**
   ```bash
   enhanced-start.bat
   ```

3. **Monitor health regularly:**
   - Check dashboard indicators
   - Review logs daily
   - Run diagnostics weekly

4. **Keep dependencies updated:**
   ```bash
   pip install --upgrade -r requirements.txt
   npm update
   ```

5. **Regular maintenance:**
   - Clean old logs monthly
   - Backup database weekly
   - Clear temp files regularly

---

**Remember: Most issues can be solved by running `python backend/diagnose.py`!** 🔧
