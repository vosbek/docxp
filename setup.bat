@echo off
REM DocXP Quick Setup Script for Windows
REM Optimized for machines with existing infrastructure

echo 🚀 DocXP Quick Setup Starting...
echo ==============================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git not found. Please install Git
    pause
    exit /b 1
)

echo ✅ Git found

REM Check optional services
echo.
echo 🔍 Checking Optional Services...

podman --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Podman found
    set HAS_PODMAN=true
) else (
    echo ⚠️ Podman not found. Optional services will be skipped
    set HAS_PODMAN=false
)

aws --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ AWS CLI found
    set HAS_AWS=true
) else (
    echo ⚠️ AWS CLI not found. Bedrock features will be disabled
    set HAS_AWS=false
)

REM Setup Python environment
echo.
echo 🐍 Setting up Python Environment...

if not exist "docxp-env" (
    echo Creating virtual environment...
    python -m venv docxp-env
    echo ✅ Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call docxp-env\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r backend/requirements.txt
echo ✅ Dependencies installed

REM Create basic .env file if it doesn't exist
echo.
echo ⚙️ Setting up Configuration...

if not exist "backend\.env" (
    echo Creating configuration file...
    (
        echo # DocXP Configuration
        echo APP_NAME=DocXP
        echo DEBUG=false
        echo.
        echo # Core Database
        echo DATABASE_URL=sqlite+aiosqlite:///./docxp.db
        echo.
        echo # Processing Configuration
        echo MAX_CONCURRENT_REPOS=4
        echo BATCH_SIZE=50
        echo MAX_WORKERS=4
        echo PROCESSING_TIMEOUT=600
        echo.
        echo # Neo4j ^(Optional - will gracefully degrade if not available^)
        echo NEO4J_URI=bolt://localhost:7687
        echo NEO4J_USERNAME=neo4j
        echo NEO4J_PASSWORD=docxp-2024
        echo NEO4J_ENABLED=true
        echo.
        echo # Redis ^(Optional - will gracefully degrade if not available^)
        echo REDIS_URL=redis://localhost:6379
        echo RQ_REDIS_URL=redis://localhost:6379
        echo REDIS_ENABLED=true
        echo.
        echo # AWS Bedrock ^(Optional^)
        echo AWS_REGION=us-east-1
        echo BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
    ) > backend\.env
    echo ✅ Configuration file created at backend\.env
) else (
    echo Configuration file already exists
)

REM Offer to setup optional services with Podman
if "%HAS_PODMAN%" == "true" (
    echo.
    echo 🐳 Optional: Setup Enhanced Services with Podman
    set /p SETUP_SERVICES="Would you like to start Neo4j and Redis with Podman? (y/n): "
    
    if /i "%SETUP_SERVICES%" == "y" (
        echo Starting Neo4j with Podman...
        podman run -d --name docxp-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/docxp-2024 neo4j:latest >nul 2>&1
        
        echo Starting Redis with Podman...
        podman run -d --name docxp-redis -p 6379:6379 redis:latest >nul 2>&1
        
        echo ✅ Optional services started
        
        REM Wait a moment for services to start
        timeout /t 5 /nobreak >nul
    )
)

REM Run validation test
echo.
echo 🧪 Running Validation Test...

cd backend
python simple_golden_path_test.py

if %errorlevel% equ 0 (
    echo.
    echo ==============================================
    echo ✅ 🎉 DocXP Setup Complete!
    echo.
    echo Your DocXP installation is ready for enterprise use.
    echo.
    echo Next steps:
    echo   1. Analyze a repository:
    echo      cd backend ^&^& python analyze_repo.py
    echo.
    echo   2. Create a project:
    echo      cd backend ^&^& python project.py
    echo.
    echo   3. Review documentation:
    echo      - QUICK_DEPLOYMENT_GUIDE.md
    echo      - PHASE_1_COMPLETION_REPORT.md
    echo.
    if "%HAS_PODMAN%" == "true" (
        echo   4. Manage services:
        echo      podman start docxp-neo4j docxp-redis
        echo      podman stop docxp-neo4j docxp-redis
        echo.
    )
    echo ==============================================
) else (
    echo.
    echo ❌ Setup validation failed. Please check the error messages above.
    echo.
    echo Common fixes:
    echo   - Ensure Python 3.11+ is installed
    echo   - Check network connectivity
    echo   - Verify file permissions
    echo.
    echo For help, see QUICK_DEPLOYMENT_GUIDE.md
    pause
    exit /b 1
)

pause