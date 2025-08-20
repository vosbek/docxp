@echo off
REM ============================================================================
REM DocXP Definitive Startup - NO FALLBACKS, NO ALTERNATIVES
REM Either it works or it fails with clear diagnostics
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP Definitive Startup
echo ============================================================================
echo.

REM Verify podman is available
podman --version >nul 2>&1
if errorlevel 1 (
    echo ❌ FATAL: Podman is not available or not in PATH
    exit /b 1
)

cd /d "%~dp0"

echo [1/4] Force cleanup existing containers...
podman stop --force docxp-postgres docxp-redis docxp-opensearch docxp-neo4j docxp-minio 2>nul
podman rm --force docxp-postgres docxp-redis docxp-opensearch docxp-neo4j docxp-minio 2>nul

echo [2/4] Create required network...
podman network rm docxp-network 2>nul
podman network prune -f 2>nul
podman network create docxp-network --driver bridge
if errorlevel 1 (
    echo ❌ FATAL: Network creation failed
    podman network ls
    exit /b 1
)

echo [3/4] Start containers in dependency order...
echo   Starting PostgreSQL...
podman run -d --name docxp-postgres ^
    --network docxp-network ^
    -p 5432:5432 ^
    -e POSTGRES_DB=docxp_enterprise ^
    -e POSTGRES_USER=docxp_user ^
    -e POSTGRES_PASSWORD=docxp_secure_2024 ^
    -v postgres_data:/var/lib/postgresql/data ^
    postgres:16-alpine
if errorlevel 1 (
    echo ❌ FATAL: PostgreSQL container failed to start
    exit /b 1
)

echo   Starting Redis...
podman run -d --name docxp-redis ^
    --network docxp-network ^
    -p 6379:6379 ^
    -v redis_data:/data ^
    redis:7-alpine redis-server --appendonly yes
if errorlevel 1 (
    echo ❌ FATAL: Redis container failed to start
    exit /b 1
)

echo   Starting OpenSearch...
podman run -d --name docxp-opensearch ^
    --network docxp-network ^
    -p 9200:9200 ^
    -e "discovery.type=single-node" ^
    -e "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g" ^
    -e "DISABLE_INSTALL_DEMO_CONFIG=true" ^
    -e "DISABLE_SECURITY_PLUGIN=true" ^
    -e "bootstrap.memory_lock=true" ^
    --ulimit memlock=-1:-1 ^
    -v opensearch_data:/usr/share/opensearch/data ^
    opensearchproject/opensearch:2.11.0
if errorlevel 1 (
    echo ❌ FATAL: OpenSearch container failed to start
    exit /b 1
)

echo   Starting Neo4j...
podman run -d --name docxp-neo4j ^
    --network docxp-network ^
    -p 7474:7474 ^
    -p 7687:7687 ^
    -e NEO4J_AUTH=neo4j/docxp-neo4j-2024 ^
    -v neo4j_data:/data ^
    neo4j:5.11
if errorlevel 1 (
    echo ❌ FATAL: Neo4j container failed to start
    exit /b 1
)

echo [4/4] Wait for services to be ready (120 seconds max)...
set /a counter=0
:wait_loop
set /a counter+=1
if %counter% gtr 24 (
    echo ❌ FATAL: Services did not become ready within 120 seconds
    echo Container status:
    podman ps -a --filter name=docxp-
    exit /b 1
)

timeout /t 5 >nul
echo   Checking services... (%counter%/24)

REM Check PostgreSQL
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue -InformationLevel Quiet" >nul 2>&1 || goto wait_loop

REM Check Redis  
redis-cli ping >nul 2>&1 || goto wait_loop

REM Check OpenSearch
curl -s -f http://localhost:9200/_cluster/health >nul 2>&1 || goto wait_loop

REM Check Neo4j
curl -s -f http://localhost:7474 >nul 2>&1 || goto wait_loop

echo ✅ All services are ready!

echo.
echo ============================================================================
echo   Infrastructure Ready - Starting Backend
echo ============================================================================
echo.

cd backend

if not exist ".env.enterprise" (
    echo ❌ FATAL: .env.enterprise file not found in backend directory
    exit /b 1
)

python fix_env_loading.py
if errorlevel 1 (
    echo ❌ FATAL: Environment configuration failed
    exit /b 1
)

python -c "from app.core.config import settings; print(f'Using database: {settings.DATABASE_URL}'); exit(1 if 'sqlite' in settings.DATABASE_URL else 0)"
if errorlevel 1 (
    echo ❌ FATAL: Still configured for SQLite instead of PostgreSQL
    exit /b 1
)

echo ✅ Configuration validated - Starting DocXP Backend...
echo   Backend URL: http://localhost:8001
echo   Press Ctrl+C to stop
echo.

python main.py