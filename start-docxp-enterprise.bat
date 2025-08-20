@echo off
REM ============================================================================
REM DocXP Enterprise Startup - COMPREHENSIVE FIX
REM This script properly handles container lifecycle, networking, and dependencies
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP Enterprise Startup - Complete System Reset and Start
echo ============================================================================
echo.

REM Check if podman is available
podman --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Podman is not available or not in PATH
    echo Please install Podman or ensure it's in your PATH
    pause
    exit /b 1
)

REM Change to the correct directory
cd /d "%~dp0"

REM Step 1: Complete system shutdown and cleanup
echo [1/8] Complete system shutdown and cleanup...
echo   - Force stopping all backend processes...
tasklist | findstr python.exe >nul && (
    echo     Stopping Python processes...
    powershell -c "Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*uvicorn*' -or $_.CommandLine -like '*main.py*' -or $_.CommandLine -like '*DocXP*'} | Stop-Process -Force"
    timeout /t 3 >nul
)

echo   - Force stopping and removing all DocXP containers...
podman stop --force docxp-opensearch docxp-postgres docxp-redis docxp-neo4j docxp-minio docxp-backend docxp-worker postgres 2>nul
podman rm --force docxp-opensearch docxp-postgres docxp-redis docxp-neo4j docxp-minio docxp-backend docxp-worker postgres 2>nul
echo   - Container cleanup completed

echo   - Cleaning up Docker network conflicts...
podman network rm docxp-network 2>nul
echo   - Network cleanup completed

echo [2/8] Waiting for complete shutdown...
timeout /t 5 >nul

REM Step 2: Start infrastructure services using Podman Compose
echo [3/8] Starting infrastructure services with proper networking...
echo   - Using podman-compose.yml for correct service orchestration
echo   - This ensures proper networking and dependencies

REM Start only infrastructure services first (not backend)
podman-compose -f podman-compose.yml up -d postgres redis opensearch neo4j minio
if errorlevel 1 (
    echo ❌ Failed to start infrastructure services with podman-compose
    echo Attempting manual container creation...
    goto manual_start
)
echo   - Infrastructure services started with compose

goto wait_for_services

:manual_start
echo [3.1/8] Manual container startup fallback...
echo   - Creating DocXP network...
podman network create docxp-network --subnet=172.20.0.0/16 2>nul

echo   - Starting PostgreSQL...
podman run -d --name docxp-postgres ^
    --network docxp-network ^
    --hostname postgres ^
    -p 5432:5432 ^
    -e POSTGRES_DB=docxp ^
    -e POSTGRES_USER=docxp_user ^
    -e POSTGRES_PASSWORD=docxp_local_dev_2024 ^
    -e POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256" ^
    -v postgres_data:/var/lib/postgresql/data ^
    --restart unless-stopped ^
    postgres:16-alpine

echo   - Starting Redis...
podman run -d --name docxp-redis ^
    --network docxp-network ^
    --hostname redis ^
    -p 6379:6379 ^
    -v redis_data:/data ^
    --restart unless-stopped ^
    redis:7-alpine redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru

echo   - Starting OpenSearch...
podman run -d --name docxp-opensearch ^
    --network docxp-network ^
    --hostname opensearch ^
    -p 9200:9200 ^
    -p 9600:9600 ^
    -e "discovery.type=single-node" ^
    -e "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g" ^
    -e "DISABLE_INSTALL_DEMO_CONFIG=true" ^
    -e "DISABLE_SECURITY_PLUGIN=true" ^
    -e "cluster.name=docxp-cluster" ^
    -e "node.name=docxp-node" ^
    -e "bootstrap.memory_lock=true" ^
    --ulimit memlock=-1:-1 ^
    --ulimit nofile=65536:65536 ^
    -v opensearch_data:/usr/share/opensearch/data ^
    --restart unless-stopped ^
    opensearchproject/opensearch:2.11.0

echo   - Starting Neo4j...
podman run -d --name docxp-neo4j ^
    --network docxp-network ^
    --hostname neo4j ^
    -p 7474:7474 ^
    -p 7687:7687 ^
    -e NEO4J_AUTH=neo4j/docxp-neo4j-2024 ^
    -e NEO4J_PLUGINS='["graph-data-science"]' ^
    -e NEO4J_server_memory_pagecache_size=1G ^
    -e NEO4J_server_memory_heap_max__size=1G ^
    -e NEO4J_dbms_security_procedures_unrestricted='gds.*' ^
    -v neo4j_data:/data ^
    -v neo4j_logs:/logs ^
    -v neo4j_import:/var/lib/neo4j/import ^
    -v neo4j_plugins:/plugins ^
    --restart unless-stopped ^
    neo4j:5.11

echo   - Starting MinIO (optional)...
podman run -d --name docxp-minio ^
    --network docxp-network ^
    --hostname minio ^
    -p 9000:9000 ^
    -p 9001:9001 ^
    -e MINIO_ROOT_USER=docxp-root ^
    -e MINIO_ROOT_PASSWORD=docxp-local-dev-2024 ^
    -e MINIO_DOMAIN=minio ^
    -v minio_data:/data ^
    --restart unless-stopped ^
    minio/minio:latest server /data --console-address ":9001"

:wait_for_services
echo [4/8] Waiting for infrastructure services to become healthy...
echo   - This may take up to 2 minutes for all services to initialize
echo   - Checking service health every 10 seconds...

set /a counter=0
:healthcheck
set /a counter+=1
if %counter% gtr 12 (
    echo ❌ Services failed to start within 2 minutes
    echo Running diagnostic checks...
    goto diagnostic
)

timeout /t 10 >nul
echo   - Health check attempt %counter%/12...

REM Check PostgreSQL
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue -InformationLevel Quiet" >nul 2>&1
if errorlevel 1 (
    echo     PostgreSQL not ready yet...
    goto healthcheck
)

REM Check Redis
redis-cli -h localhost -p 6379 ping >nul 2>&1
if errorlevel 1 (
    echo     Redis not ready yet...
    goto healthcheck
)

REM Check OpenSearch
curl -s -f http://localhost:9200/_cluster/health >nul 2>&1
if errorlevel 1 (
    echo     OpenSearch not ready yet...
    goto healthcheck
)

REM Check Neo4j HTTP interface
curl -s -f http://localhost:7474 >nul 2>&1
if errorlevel 1 (
    echo     Neo4j not ready yet...
    goto healthcheck
)

echo   - ✅ All infrastructure services are healthy!
goto check_env

:diagnostic
echo.
echo ============================================================================
echo   DIAGNOSTIC INFORMATION
echo ============================================================================
echo.
echo Container Status:
podman ps -a --filter name=docxp
echo.
echo Network Status:
podman network ls
echo.
echo Port Status:
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded"
powershell -c "Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded"
powershell -c "Test-NetConnection -ComputerName localhost -Port 9200 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded"
powershell -c "Test-NetConnection -ComputerName localhost -Port 7474 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded"
echo.
echo Recent container logs:
echo --- PostgreSQL ---
podman logs --tail 10 docxp-postgres
echo --- OpenSearch ---
podman logs --tail 10 docxp-opensearch
echo --- Neo4j ---
podman logs --tail 10 docxp-neo4j
echo.
echo Please check the diagnostic information above.
pause
exit /b 1

:check_env
echo [5/8] Validating environment configuration...
cd /d "%~dp0backend"

REM Check if .env.enterprise exists
if not exist ".env.enterprise" (
    echo ❌ .env.enterprise file not found in backend directory
    echo Please ensure the environment file exists at: %CD%\.env.enterprise
    pause
    exit /b 1
)

REM Activate virtual environment if available
if exist "..\docxp-env\Scripts\activate.bat" (
    echo   - Activating virtual environment...
    call "..\docxp-env\Scripts\activate.bat"
) else (
    echo   - Virtual environment not found, using system Python
)

echo [6/8] Testing environment and AWS configuration...
python fix_env_loading.py
if errorlevel 1 (
    echo.
    echo ❌ Environment configuration failed
    echo Please check your .env.enterprise file and AWS credentials
    pause
    exit /b 1
)

echo [7/8] Testing database connectivity...
python -c "
import asyncio
from app.core.config import settings
print(f'Database URL: {settings.DATABASE_URL}')
print(f'Vector DB Type: {settings.VECTOR_DB_TYPE}')
print(f'Embedding Provider: {settings.EMBEDDING_PROVIDER}')
if settings.DATABASE_URL.startswith('sqlite'):
    print('❌ ERROR: Still using SQLite instead of PostgreSQL!')
    exit(1)
else:
    print('✅ PostgreSQL configuration detected')
"
if errorlevel 1 (
    echo.
    echo ❌ Database configuration is still incorrect
    echo The application is configured to use SQLite instead of PostgreSQL
    pause
    exit /b 1
)

echo [8/8] Starting DocXP Backend...
echo   - All infrastructure services: HEALTHY
echo   - Environment: .env.enterprise loaded
echo   - Database: PostgreSQL configured
echo   - AWS Profile: %AWS_PROFILE%
echo   - Backend URL: http://localhost:8001
echo   - Health endpoint: http://localhost:8001/health
echo.

echo ============================================================================
echo   DocXP Enterprise Backend Starting...
echo   - Press Ctrl+C to stop the server
echo   - Infrastructure containers will continue running
echo ============================================================================
echo.

REM Start the backend
python main.py

echo.
echo ============================================================================
echo   DocXP Backend Stopped
echo ============================================================================
echo.
echo Infrastructure services are still running. To stop everything:
echo   podman stop docxp-opensearch docxp-redis docxp-neo4j docxp-postgres docxp-minio
echo.
echo To restart just the backend:
echo   cd backend ^&^& python main.py
echo.