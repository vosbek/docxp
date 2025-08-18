@echo off
REM DocXP Service Status Script

echo 📊 DocXP Service Status
echo ===============================

echo Checking Podman containers...
podman ps --filter "name=docxp-neo4j" --filter "name=docxp-redis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo Checking service connectivity...

REM Test Neo4j
echo Testing Neo4j connection...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:7474' -TimeoutSec 5 -ErrorAction Stop; Write-Host '✅ Neo4j Web Interface: ACCESSIBLE' } catch { Write-Host '❌ Neo4j Web Interface: NOT ACCESSIBLE' }"

REM Test Redis
echo Testing Redis connection...
powershell -Command "try { $tcpClient = New-Object System.Net.Sockets.TcpClient; $tcpClient.Connect('localhost', 6379); $tcpClient.Close(); Write-Host '✅ Redis: ACCESSIBLE' } catch { Write-Host '❌ Redis: NOT ACCESSIBLE' }"

echo.
echo ===============================