@echo off
REM DocXP Service Stop Script

echo 🛑 Stopping DocXP Services...
echo ===============================

echo Stopping Neo4j...
podman stop docxp-neo4j
if %errorlevel% equ 0 (
    echo ✅ Neo4j stopped
) else (
    echo ⚠️ Neo4j was not running
)

echo Stopping Redis...
podman stop docxp-redis
if %errorlevel% equ 0 (
    echo ✅ Redis stopped
) else (
    echo ⚠️ Redis was not running
)

echo.
echo ===============================
echo ✅ DocXP Services Stopped!
echo ===============================