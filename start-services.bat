@echo off
REM DocXP Service Management Script

echo 🚀 Starting DocXP Services...
echo ===============================

REM Stop and remove existing containers if they exist
echo Cleaning up existing containers...
podman stop docxp-neo4j docxp-redis >nul 2>&1
podman rm docxp-neo4j docxp-redis >nul 2>&1

echo Starting Neo4j Knowledge Graph...
podman run -d --name docxp-neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/docxp-production-2024 -e NEO4J_PLUGINS=[] neo4j:5.11
if %errorlevel% neq 0 (
    echo ❌ Failed to start Neo4j
    goto :error
) else (
    echo ✅ Neo4j started successfully
)

echo Starting Redis Cache...
podman run -d --name docxp-redis -p 6379:6379 redis:7-alpine
if %errorlevel% neq 0 (
    echo ❌ Failed to start Redis
    goto :error
) else (
    echo ✅ Redis started successfully
)

echo Waiting for services to initialize...
timeout /t 15 /nobreak >nul

echo Checking service status...
podman ps --filter "name=docxp-neo4j" --filter "name=docxp-redis" --format "{{.Names}} - {{.Status}}"

echo.
echo ===============================
echo ✅ DocXP Services Started!
echo.
echo Neo4j Browser: http://localhost:7474
echo Username: neo4j
echo Password: docxp-production-2024
echo.
echo Redis: localhost:6379
echo.
echo To stop services: stop-services.bat
echo ===============================
goto :end

:error
echo.
echo ❌ Service startup failed!
echo Please check:
echo 1. Podman is running
echo 2. Ports 7474, 7687, 6379 are available
echo 3. Internet connection for image downloads
pause
exit /b 1

:end