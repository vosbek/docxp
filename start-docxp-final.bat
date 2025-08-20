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

echo [1/4] Force cleanup existing containers and volumes...
podman stop --force docxp-postgres docxp-redis docxp-opensearch docxp-neo4j docxp-minio 2>nul
podman rm --force docxp-postgres docxp-redis docxp-opensearch docxp-neo4j docxp-minio 2>nul
echo   Removing Neo4j volume data to fix version downgrade error...
podman volume rm neo4j_data 2>nul
podman volume rm neo4j_logs 2>nul
podman volume prune -f 2>nul

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

echo [4/4] Test each service individually...

echo   Testing PostgreSQL (port 5432)...
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
if errorlevel 1 (
    echo ❌ PostgreSQL port not accessible
    podman logs --tail 10 docxp-postgres
    exit /b 1
) else (
    echo ✅ PostgreSQL ready
)

echo   Testing Redis (using container health check)...
podman exec docxp-redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis not responding
    podman logs --tail 10 docxp-redis
    exit /b 1
) else (
    echo ✅ Redis ready
)

echo   Testing OpenSearch (may take 2+ minutes to initialize)...
echo   First checking if port 9200 is accessible...
powershell -c "Test-NetConnection -ComputerName localhost -Port 9200 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
if errorlevel 1 (
    echo   Port 9200 not yet accessible, waiting...
    timeout /t 10 >nul
    powershell -c "Test-NetConnection -ComputerName localhost -Port 9200 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
    if errorlevel 1 (
        echo ❌ OpenSearch port 9200 never became accessible
        echo Container status:
        podman ps --filter name=docxp-opensearch
        echo Recent logs:
        podman logs --tail 10 docxp-opensearch
        exit /b 1
    )
)

echo   Port accessible, testing OpenSearch API...
set /a opensearch_counter=0
:opensearch_wait
set /a opensearch_counter+=1
if %opensearch_counter% gtr 30 (
    echo ❌ OpenSearch API failed to respond within 150 seconds
    echo Testing with PowerShell:
    powershell -c "try { (Invoke-WebRequest -Uri 'http://localhost:9200/_cluster/health' -UseBasicParsing).Content } catch { $_.Exception.Message }"
    echo Recent container logs:
    podman logs --tail 20 docxp-opensearch
    exit /b 1
)

REM Try curl first
curl -s http://localhost:9200/_cluster/health >nul 2>&1
if errorlevel 1 (
    REM If curl fails, try PowerShell
    powershell -c "try { Invoke-WebRequest -Uri 'http://localhost:9200/_cluster/health' -UseBasicParsing -TimeoutSec 5 } catch { exit 1 }" >nul 2>&1
    if errorlevel 1 (
        echo   OpenSearch still initializing... (%opensearch_counter%/30)
        timeout /t 5 >nul
        goto opensearch_wait
    ) else (
        echo ✅ OpenSearch ready (via PowerShell)
    )
) else (
    echo ✅ OpenSearch ready (via curl)
)

echo   Testing Neo4j (may take 60+ seconds to initialize)...
echo   First checking if port 7474 is accessible...
powershell -c "Test-NetConnection -ComputerName localhost -Port 7474 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
if errorlevel 1 (
    echo   Port 7474 not yet accessible, waiting...
    timeout /t 15 >nul
    powershell -c "Test-NetConnection -ComputerName localhost -Port 7474 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul
    if errorlevel 1 (
        echo ❌ Neo4j port 7474 never became accessible
        echo Container status:
        podman ps --filter name=docxp-neo4j
        echo Recent logs:
        podman logs --tail 15 docxp-neo4j
        exit /b 1
    )
)

echo   Port accessible, testing Neo4j web interface...
set /a neo4j_counter=0
:neo4j_wait
set /a neo4j_counter+=1
if %neo4j_counter% gtr 20 (
    echo ❌ Neo4j web interface failed to respond within 100 seconds
    echo Testing with PowerShell:
    powershell -c "try { (Invoke-WebRequest -Uri 'http://localhost:7474' -UseBasicParsing -TimeoutSec 5).StatusCode } catch { $_.Exception.Message }"
    echo Recent container logs:
    podman logs --tail 20 docxp-neo4j
    exit /b 1
)

REM Try curl first
curl -s http://localhost:7474 >nul 2>&1
if errorlevel 1 (
    REM If curl fails, try PowerShell
    powershell -c "try { Invoke-WebRequest -Uri 'http://localhost:7474' -UseBasicParsing -TimeoutSec 5 } catch { exit 1 }" >nul 2>&1
    if errorlevel 1 (
        echo   Neo4j still initializing... (%neo4j_counter%/20)
        timeout /t 5 >nul
        goto neo4j_wait
    ) else (
        echo ✅ Neo4j ready (via PowerShell)
    )
) else (
    echo ✅ Neo4j ready (via curl)
)

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