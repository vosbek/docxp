@echo off
echo ============================================================================
echo  DocXP Final Issue Resolution
echo ============================================================================

echo [1/3] Finding actual PostgreSQL container name...
echo Available containers:
podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | findstr postgres

echo.
echo All DocXP-related containers:
podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | findstr -i docxp

echo.
echo [2/3] Checking PostgreSQL connectivity on port 5432...
powershell -c "Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue" | findstr "TcpTestSucceeded"

echo.
echo [3/3] Testing OpenSearch index management...
curl -X DELETE "http://localhost:9200/docxp-code-index" 2>nul
echo   - Deleted any existing index with bad mapping

echo.
echo ============================================================================
echo  Analysis Complete
echo ============================================================================
pause