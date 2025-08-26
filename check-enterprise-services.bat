@echo off
echo ============================================================================
echo  DocXP Enterprise Service Status Check
echo ============================================================================

echo [1/4] Checking PostgreSQL (System Service vs Container)...
echo.
sc query postgresql-x64-* 2>nul | findstr "STATE" | findstr "RUNNING" >nul && (
    echo   ✅ PostgreSQL running as Windows Service
    set PG_STATUS=SERVICE
) || (
    podman ps | findstr postgres >nul && (
        echo   ✅ PostgreSQL running as Container
        set PG_STATUS=CONTAINER
    ) || (
        powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded.*True" >nul && (
            echo   ✅ PostgreSQL responding on port 5432 (unknown type)
            set PG_STATUS=UNKNOWN
        ) || (
            echo   ❌ PostgreSQL not accessible
            set PG_STATUS=NONE
        )
    )
)

echo [2/4] Checking Container Services...
echo.
echo   Redis Status:
podman ps | findstr docxp-redis && echo     ✅ Redis container running || echo     ❌ Redis container not running

echo   OpenSearch Status:
podman ps | findstr docxp-opensearch && echo     ✅ OpenSearch container running || echo     ❌ OpenSearch container not running

echo   Neo4j Status:
podman ps | findstr docxp-neo4j && echo     ✅ Neo4j container running || echo     ❌ Neo4j container not running

echo [3/4] Testing Service Connectivity...
echo.
echo   PostgreSQL (port 5432):
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded" 

echo   Redis (port 6379):
powershell -c "Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded" 

echo   OpenSearch (port 9200):
curl -s http://localhost:9200/_cluster/health | findstr "green\|yellow" >nul && echo     TcpTestSucceeded : True || echo     TcpTestSucceeded : False

echo   Neo4j (port 7474):
powershell -c "Test-NetConnection -ComputerName localhost -Port 7474 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded" 

echo [4/4] OpenSearch Index Status...
echo.
curl -s http://localhost:9200/docxp-code-index | findstr "error" >nul && (
    echo   ❌ Index has errors - needs recreation
) || (
    curl -s http://localhost:9200/docxp-code-index >nul 2>&1 && (
        echo   ✅ Index exists and accessible
    ) || (
        echo   ℹ️  Index doesn't exist (will be created on startup)
    )
)

echo.
echo ============================================================================
echo  Service Status Summary
echo ============================================================================
echo   PostgreSQL: %PG_STATUS%
echo   Enterprise setup detected with hybrid container/service architecture
echo ============================================================================