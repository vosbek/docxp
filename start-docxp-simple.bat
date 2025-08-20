@echo off
REM ============================================================================
REM DocXP Simple Startup - No Custom Networks, Just Basic Containers
REM This is the most reliable way to start DocXP services
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP Simple Startup - Basic Container Management
echo ============================================================================
echo.

REM Check if podman is available
podman --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Podman is not available or not in PATH
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [1/6] Complete cleanup...
echo   - Stopping Python processes...
tasklist | findstr python.exe >nul && (
    powershell -c "Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*uvicorn*' -or $_.CommandLine -like '*main.py*'} | Stop-Process -Force"
    timeout /t 2 >nul
)

echo   - Removing existing containers...
podman stop --force docxp-postgres docxp-redis docxp-opensearch docxp-neo4j docxp-minio 2>nul
podman rm --force docxp-postgres docxp-redis docxp-opensearch docxp-neo4j docxp-minio 2>nul

echo [2/6] Starting PostgreSQL...
podman run -d --name docxp-postgres ^
    -p 5432:5432 ^
    -e POSTGRES_DB=docxp_enterprise ^
    -e POSTGRES_USER=docxp_user ^
    -e POSTGRES_PASSWORD=docxp_secure_2024 ^
    -v postgres_data:/var/lib/postgresql/data ^
    postgres:16-alpine
echo   - PostgreSQL starting...

echo [3/6] Starting Redis...
podman run -d --name docxp-redis ^
    -p 6379:6379 ^
    -v redis_data:/data ^
    redis:7-alpine redis-server --appendonly yes
echo   - Redis starting...

echo [4/6] Starting OpenSearch...
podman run -d --name docxp-opensearch ^
    -p 9200:9200 ^
    -p 9600:9600 ^
    -e "discovery.type=single-node" ^
    -e "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g" ^
    -e "DISABLE_INSTALL_DEMO_CONFIG=true" ^
    -e "DISABLE_SECURITY_PLUGIN=true" ^
    -e "bootstrap.memory_lock=true" ^
    --ulimit memlock=-1:-1 ^
    -v opensearch_data:/usr/share/opensearch/data ^
    opensearchproject/opensearch:2.11.0
echo   - OpenSearch starting...

echo [5/6] Starting Neo4j...
podman run -d --name docxp-neo4j ^
    -p 7474:7474 ^
    -p 7687:7687 ^
    -e NEO4J_AUTH=neo4j/docxp-neo4j-2024 ^
    -v neo4j_data:/data ^
    neo4j:5.11
echo   - Neo4j starting...

echo   - Container status:
podman ps --format "table {{.Names}} {{.Status}} {{.Ports}}"

echo [6/6] Waiting for services (60 seconds)...
timeout /t 60 >nul

echo   - Testing connectivity:
echo     PostgreSQL (port 5432):
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue" | findstr TcpTestSucceeded

echo     Redis (port 6379):
powershell -c "Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue" | findstr TcpTestSucceeded

echo     OpenSearch (port 9200):
powershell -c "Test-NetConnection -ComputerName localhost -Port 9200 -WarningAction SilentlyContinue" | findstr TcpTestSucceeded

echo     Neo4j (port 7474):
powershell -c "Test-NetConnection -ComputerName localhost -Port 7474 -WarningAction SilentlyContinue" | findstr TcpTestSucceeded

echo.
echo ============================================================================
echo   Infrastructure services started. You can now start the backend with:
echo   
echo   cd backend
echo   python fix_env_loading.py
echo   python main.py
echo.
echo   - Backend URL: http://localhost:8001
echo   - PostgreSQL: localhost:5432 (user: docxp_user, db: docxp_enterprise)
echo   - Redis: localhost:6379
echo   - OpenSearch: localhost:9200
echo   - Neo4j: localhost:7474 (user: neo4j, pass: docxp-neo4j-2024)
echo ============================================================================