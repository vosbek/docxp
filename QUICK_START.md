# DocXP Quick Start Guide

## 🚀 Get Started in 60 Seconds

### Step 1: System Check (10 seconds)
```batch
test-system.bat
```
This verifies all prerequisites are met.

### Step 2: Start DocXP (30 seconds)
```batch
enhanced-start.bat
```
This will:
- ✅ Validate environment
- ✅ Install dependencies
- ✅ Start all services
- ✅ Open browser automatically

### Step 3: Generate Your First Documentation (20 seconds)
1. Click **"Generate Documentation"** button
2. Enter your repository path (e.g., `C:\projects\my-app`)
3. Click **Generate**
4. Watch the real-time progress

That's it! Your documentation will be ready in minutes.

## 🎯 Quick Actions

### Generate Documentation
```bash
# Via UI
1. Navigate to http://localhost:4200
2. Click "Generate Documentation"
3. Follow the wizard

# Via API
curl -X POST http://localhost:8001/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "C:/path/to/repo",
    "depth": "standard",
    "include_diagrams": true,
    "include_business_rules": true
  }'
```

### Check Job Status
```bash
# Via UI
Look at the dashboard's "Recent Jobs" table

# Via API
curl http://localhost:8001/api/documentation/status/{job_id}
```

### Download Documentation
```bash
# Via UI
Click the download icon in the Recent Jobs table

# Via API
curl http://localhost:8001/api/documentation/download/{job_id} -o docs.zip
```

### Sync Repository (Incremental Updates)
```bash
# Via UI
Click "Sync Repository" in Quick Actions

# Via API
curl -X POST "http://localhost:8001/api/documentation/sync?repo_path=C:/path/to/repo"
```

## 🔍 Health Monitoring

### Quick Health Check
```bash
curl http://localhost:8001/health
```

### Detailed System Status
```bash
curl http://localhost:8001/health/detailed | python -m json.tool
```

### Dashboard Indicators
- 🟢 Green = Service healthy
- 🟡 Yellow = Service degraded
- 🔴 Red = Service down

## 🛠️ Configuration Options

### Documentation Depth Levels
- **Minimal**: Basic structure only (fastest)
- **Standard**: Recommended for most projects
- **Comprehensive**: Detailed analysis
- **Exhaustive**: Complete documentation (slowest)

### Focus Areas
- ✅ Classes and Objects
- ✅ Functions and Methods
- ✅ APIs and Endpoints
- ✅ Database Schemas
- ✅ Security Patterns
- ✅ Configuration Files

### Output Options
- 📊 Mermaid Diagrams
- 📋 Business Rules
- 📚 API Documentation
- 🔄 Incremental Updates

## 📁 Output Location

Generated documentation is saved to:
```
backend/output/{job_id}/
├── README.md           # Main documentation
├── architecture.md     # System architecture
├── business_rules.md   # Extracted rules
├── api_docs.md        # API documentation
└── diagrams/          # Mermaid diagrams
```

## ⚡ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + G` | Generate new documentation |
| `Ctrl + R` | Refresh dashboard |
| `Ctrl + H` | Show help |
| `F5` | Reload metrics |

## 🔧 Troubleshooting Quick Fixes

### Application Won't Start
```batch
# Run diagnostics
cd backend
python diagnose.py

# Follow the suggested fixes
```

### Port Already in Use
```batch
# Kill processes on ports
taskkill /F /IM node.exe
taskkill /F /IM python.exe

# Restart
enhanced-start.bat
```

### AWS Not Working
No problem! The app automatically uses mock mode for AI features.

### Database Locked
```batch
cd backend
del docxp.db
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

## 📊 Performance Tips

1. **Start Small**: Test with a small repository first
2. **Use Standard Depth**: Comprehensive is rarely needed
3. **Exclude Patterns**: Add `node_modules`, `.git`, etc.
4. **Incremental Sync**: Use sync for updates instead of regenerating

## 🎨 UI Features

### Dashboard
- **Real-time metrics** - Live updates every 30 seconds
- **Job tracking** - See all documentation jobs
- **Quick actions** - One-click common tasks
- **System status** - Health indicators

### Generation Wizard
1. **Repository Selection** - Browse or paste path
2. **Configuration** - Choose depth and options
3. **Review** - Confirm settings
4. **Progress** - Real-time updates
5. **Results** - Download or view

## 📝 Sample Repository Paths

```batch
# Python project
C:\projects\my-python-app

# Angular project
C:\workspaces\angular-frontend

# Mixed technology
C:\repos\enterprise-system

# Current directory
.
```

## 🚦 Status Indicators

| Status | Meaning | Action |
|--------|---------|--------|
| 🟢 Completed | Documentation ready | Download available |
| 🟡 Processing | Generation in progress | Wait or check status |
| 🔵 Pending | Queued for processing | Will start soon |
| 🔴 Failed | Error occurred | Check logs |

## 💡 Pro Tips

1. **Use the diagnostic tool** before reporting issues
2. **Check logs** for detailed error messages
3. **Monitor health endpoint** for system status
4. **Use Request-ID** from headers to trace issues
5. **Enable AWS** for better AI analysis (optional)

## 📞 Getting Help

1. **Built-in diagnostics**: `python backend/diagnose.py`
2. **System test**: `test-system.bat`
3. **API docs**: http://localhost:8001/docs
4. **Logs**: `backend/logs/docxp.log`
5. **Health check**: http://localhost:8001/health/detailed

---

**Ready to document your codebase? Start with `enhanced-start.bat`!** 🚀
