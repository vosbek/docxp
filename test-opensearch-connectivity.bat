@echo off
REM ============================================================================
REM Quick OpenSearch Connectivity Test
REM Tests if OpenSearch is accessible and responsive
REM ============================================================================

echo.
echo ============================================================================
echo   OpenSearch Connectivity Test
echo ============================================================================
echo.

echo [1/4] Testing basic connectivity...
curl -s -f http://localhost:9200 >nul 2>&1
if errorlevel 1 (
    echo ❌ OpenSearch is not accessible on http://localhost:9200
    echo Please ensure OpenSearch container is running
    goto :end
)
echo ✅ OpenSearch is accessible

echo [2/4] Testing cluster health...
for /f "delims=" %%i in ('curl -s http://localhost:9200/_cluster/health') do set health_response=%%i
echo Response: %health_response%

echo %health_response% | findstr "green\|yellow" >nul
if errorlevel 1 (
    echo ❌ OpenSearch cluster is not healthy
) else (
    echo ✅ OpenSearch cluster is healthy
)

echo [3/4] Testing index management...
curl -s -X DELETE http://localhost:9200/test_connectivity_index >nul 2>&1
curl -s -X PUT http://localhost:9200/test_connectivity_index -H "Content-Type: application/json" -d "{\"settings\":{\"number_of_shards\":1}}" >nul 2>&1
if errorlevel 1 (
    echo ❌ Cannot create test index
) else (
    echo ✅ Index creation successful
    curl -s -X DELETE http://localhost:9200/test_connectivity_index >nul 2>&1
)

echo [4/4] Testing from backend configuration...
cd /d "%~dp0backend"
if exist ".env.enterprise" (
    python -c "
from fix_env_loading import load_env_enterprise
load_env_enterprise()
from app.core.config import settings
print(f'OpenSearch Host: {settings.OPENSEARCH_HOST}')
print(f'OpenSearch Port: {settings.OPENSEARCH_PORT}')
print(f'OpenSearch Index: {settings.OPENSEARCH_INDEX_NAME}')
print(f'OpenSearch URL: http://{settings.OPENSEARCH_HOST}:{settings.OPENSEARCH_PORT}')
"
) else (
    echo ❌ .env.enterprise not found, cannot test backend configuration
)

:end
echo.
echo ============================================================================
echo   OpenSearch Test Complete
echo ============================================================================