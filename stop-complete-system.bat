@echo off
REM ============================================================================
REM DocXP Complete System Shutdown Script
REM Stops all backend processes and infrastructure containers
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP Complete System Shutdown
echo ============================================================================
echo.

echo [1/3] Stopping backend processes...
tasklist | findstr python.exe >nul && (
    echo   - Stopping Python backend processes...
    powershell -c "Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*app.main*' -or $_.CommandLine -like '*uvicorn*' -or $_.CommandLine -like '*docxp*'} | Stop-Process -Force"
    timeout /t 2 >nul
    echo   - Backend processes stopped
) || (
    echo   - No Python backend processes found
)

echo [2/3] Stopping all DocXP containers...
podman stop docxp-opensearch docxp-postgres docxp-redis docxp-neo4j docxp-minio docxp-backend docxp-worker 2>nul
echo   - All DocXP containers stopped

echo [3/3] Verifying shutdown...
podman ps --filter name=docxp --format "table {{.Names}}\t{{.Status}}" 2>nul || echo   - No DocXP containers running

echo.
echo ============================================================================
echo   DocXP System Shutdown Complete
echo ============================================================================
echo   All backend processes and infrastructure containers have been stopped.
echo   To restart: run start-complete-system.bat
echo.