@echo off
REM ============================================================================
REM DocXP Status Checker - Quick diagnostic tool
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP System Status Check
echo ============================================================================
echo.

echo [1/4] Container Status:
podman ps -a --filter name=docxp- --format "table {{.Names}} {{.Status}} {{.Ports}}"

echo.
echo [2/4] Port Connectivity:
echo   PostgreSQL (5432):
powershell -c "try { Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded } catch { Write-Output 'Connection test failed' }"

echo   Redis (6379):
powershell -c "try { Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded } catch { Write-Output 'Connection test failed' }"

echo   OpenSearch (9200):
powershell -c "try { Test-NetConnection -ComputerName localhost -Port 9200 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded } catch { Write-Output 'Connection test failed' }"

echo   Neo4j (7474):
powershell -c "try { Test-NetConnection -ComputerName localhost -Port 7474 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded } catch { Write-Output 'Connection test failed' }"

echo   Backend API (8001):
powershell -c "try { Test-NetConnection -ComputerName localhost -Port 8001 -WarningAction SilentlyContinue | Select-Object TcpTestSucceeded } catch { Write-Output 'Connection test failed' }"

echo.
echo [3/4] Service Health Checks:
echo   OpenSearch Cluster:
curl -s http://localhost:9200/_cluster/health 2>nul | findstr "status" || echo   Not accessible

echo   PostgreSQL:
echo   (Connection test above indicates PostgreSQL availability)

echo   Redis:
redis-cli ping 2>nul || echo   Redis not responding

echo.
echo [4/4] Process Check:
echo   Python Backend Processes:
tasklist | findstr python.exe | findstr -v tasklist || echo   No Python processes found

echo.
echo ============================================================================
echo   Quick Actions:
echo   
echo   Start all services:     .\start-docxp-simple.bat
echo   Start backend only:     cd backend ^&^& python main.py  
echo   Stop all containers:    podman stop docxp-postgres docxp-redis docxp-opensearch docxp-neo4j
echo   View container logs:    podman logs docxp-[service-name]
echo ============================================================================