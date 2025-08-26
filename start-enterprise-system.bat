@echo off
REM ============================================================================
REM DocXP Enterprise System Startup - Hybrid Container/Service Architecture
REM Handles both containerized and Windows service infrastructure
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP Enterprise System Startup
echo ============================================================================
echo.

REM Step 1: Stop any existing backend processes
echo [1/5] Stopping any running backend processes...
tasklist | findstr python.exe >nul && (
    echo   - Found Python processes, attempting to stop gracefully...
    powershell -c "Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*app.main*' -or $_.CommandLine -like '*uvicorn*' -or $_.CommandLine -like '*docxp*'} | Stop-Process -Force"
    timeout /t 3 >nul
) || (
    echo   - No Python backend processes found
)

REM Step 2: Stop containers (but leave services alone)
echo [2/5] Managing infrastructure...
echo   - Stopping DocXP containers...
podman stop docxp-opensearch docxp-redis docxp-neo4j docxp-backend docxp-worker 2>nul
timeout /t 3 >nul

REM Step 3: Start required services
echo   - Starting infrastructure services...

REM PostgreSQL - Check if service or container
sc query postgresql-x64-* 2>nul | findstr "RUNNING" >nul && (
    echo     ✅ PostgreSQL service already running
) || (
    echo     - Starting PostgreSQL container...
    podman start docxp-postgres 2>nul || podman start postgres 2>nul || echo       PostgreSQL may be system service (checking connectivity...)
)

REM Container services
echo     - Starting Redis container...
podman start docxp-redis

echo     - Starting OpenSearch container...
podman start docxp-opensearch

echo     - Starting Neo4j container...
podman start docxp-neo4j

echo [3/5] Waiting for services to be ready...
echo   - Checking service availability (90 seconds max)...

set /a counter=0
:healthcheck
set /a counter+=1
if %counter% gtr 18 goto healthtimeout

timeout /t 5 >nul
echo   - Health check attempt %counter%/18...

REM Check PostgreSQL
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
if errorlevel 1 goto healthcheck

REM Check Redis
powershell -c "Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
if errorlevel 1 goto healthcheck

REM Check OpenSearch
curl -s http://localhost:9200/_cluster/health >nul 2>&1
if errorlevel 1 goto healthcheck

REM Check Neo4j
powershell -c "Test-NetConnection -ComputerName localhost -Port 7474 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
if errorlevel 1 goto healthcheck

echo   - ✅ All services are healthy!
goto cleanup_index

:healthtimeout
echo   - ⚠️  Some services may not be fully ready, but proceeding...

:cleanup_index
echo [4/5] Preparing OpenSearch index...
echo   - Clearing any bad index configuration...
curl -X DELETE "http://localhost:9200/docxp-code-index" 2>nul
curl -X DELETE "http://localhost:9200/docxp_v1_chunks" 2>nul
echo   - Index will be recreated with correct configuration

echo [5/5] Starting DocXP Backend with enterprise configuration...
cd /d "%~dp0backend"

REM Activate virtual environment
if exist "..\docxp-env\Scripts\activate.bat" (
    call "..\docxp-env\Scripts\activate.bat"
    echo   - ✅ Virtual environment activated
) else (
    echo   - ⚠️  Virtual environment not found, using system Python
)

echo   - Loading .env.enterprise configuration...
echo   - Starting FastAPI backend on http://localhost:8001...
echo.
echo ============================================================================
echo   DocXP Enterprise Backend Starting...
echo   - Infrastructure: PostgreSQL(service) + Redis/OpenSearch/Neo4j(containers)
echo   - Backend API: http://localhost:8001
echo   - Health Check: http://localhost:8001/health
echo   - Environment: Enterprise (.env.enterprise)
echo   - AWS Profile: msh
echo ============================================================================
echo.

REM Start with proper environment loading
python -c "import fix_env_loading; fix_env_loading.load_env_enterprise()" && python main.py

echo.
echo ============================================================================
echo   DocXP Enterprise System Shutdown
echo ============================================================================
echo Backend has been stopped. Infrastructure services remain running.
echo To stop containers: podman stop docxp-opensearch docxp-redis docxp-neo4j
echo PostgreSQL service (if running) remains active.
echo.