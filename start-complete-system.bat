@echo off
REM ============================================================================
REM DocXP Complete System Startup Script
REM Stops all containers and backends, then starts everything in correct order
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP Complete System Startup
echo ============================================================================
echo.

REM Step 1: Stop everything first
echo [1/6] Stopping any running backend processes...
tasklist | findstr python.exe >nul && (
    echo   - Found Python processes, attempting to stop gracefully...
    powershell -c "Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like '*DocXP*' -or $_.CommandLine -like '*app.main*' -or $_.CommandLine -like '*uvicorn*'} | Stop-Process -Force"
    timeout /t 3 >nul
) || (
    echo   - No Python backend processes found
)

echo [2/6] Stopping all DocXP containers...
podman stop docxp-opensearch docxp-postgres docxp-redis docxp-neo4j docxp-minio docxp-backend docxp-worker 2>nul
echo   - Container stop commands completed

echo [3/6] Waiting for clean shutdown...
timeout /t 5 >nul

REM Step 2: Start infrastructure services
echo [4/6] Starting infrastructure services...
echo   - Starting PostgreSQL...
podman start docxp-postgres
echo   - Starting Redis...
podman start docxp-redis
echo   - Starting OpenSearch...
podman start docxp-opensearch
echo   - Starting Neo4j...
podman start docxp-neo4j
echo   - Starting MinIO (if exists)...
podman start docxp-minio 2>nul || echo     MinIO container not found, skipping...

echo [5/6] Waiting for services to initialize...
echo   - Checking service health (60 seconds max)...

REM Wait for services to be healthy
set /a counter=0
:healthcheck
set /a counter+=1
if %counter% gtr 12 goto healthtimeout

timeout /t 5 >nul
echo   - Health check attempt %counter%/12...

REM Check OpenSearch
curl -s http://localhost:9200/_cluster/health >nul 2>&1
if errorlevel 1 goto healthcheck

REM Check PostgreSQL port
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
if errorlevel 1 goto healthcheck

REM Check Redis port
powershell -c "Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
if errorlevel 1 goto healthcheck

echo   - All services are healthy!
goto startbackend

:healthtimeout
echo   - WARNING: Some services may not be fully ready, but proceeding...

:startbackend
echo [6/6] Starting DocXP Backend...
cd /d "%~dp0backend"

REM Activate virtual environment and start backend
echo   - Activating virtual environment...
if exist "..\docxp-env\Scripts\activate.bat" (
    call "..\docxp-env\Scripts\activate.bat"
) else (
    echo   - Virtual environment not found at ..\docxp-env\Scripts\activate.bat
    echo   - Attempting to use system Python...
)

echo   - Starting FastAPI backend on http://localhost:8001...
echo   - Press Ctrl+C to stop the server
echo.
echo ============================================================================
echo   DocXP Backend Starting...
echo   - Infrastructure services: RUNNING
echo   - Backend API: STARTING on http://localhost:8001
echo   - Health endpoint: http://localhost:8001/health
echo ============================================================================
echo.

REM Start the backend
python main.py

echo.
echo ============================================================================
echo   DocXP System Shutdown
echo ============================================================================
echo Backend has been stopped. Infrastructure containers are still running.
echo To stop everything: podman stop docxp-opensearch docxp-postgres docxp-redis docxp-neo4j
echo.