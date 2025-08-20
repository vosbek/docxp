@echo off
REM ============================================================================
REM DocXP Backend Startup with Environment Fix
REM Ensures .env.enterprise is loaded and AWS credentials work
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP Backend Startup - Enterprise Configuration
echo ============================================================================
echo.

echo [1/3] Fixing environment configuration...
python fix_env_loading.py

if errorlevel 1 (
    echo.
    echo ❌ Environment configuration failed
    echo Please check .env.enterprise file and AWS credentials
    pause
    exit /b 1
)

echo.
echo [2/3] Setting additional environment variables...
set AWS_PROFILE=msh
set AWS_REGION=us-east-1
set AWS_DEFAULT_REGION=us-east-1

echo   - AWS_PROFILE=%AWS_PROFILE%
echo   - AWS_REGION=%AWS_REGION%

echo.
echo [3/3] Starting DocXP Backend with fixed environment...
echo   - Loading environment from: .env.enterprise
echo   - AWS Profile: %AWS_PROFILE%
echo   - Backend URL: http://localhost:8001
echo   - Health Check: http://localhost:8001/health
echo.
echo ============================================================================
echo   DocXP Backend Starting...
echo ============================================================================
echo.

REM Start with environment variables properly set
python -c "import fix_env_loading; fix_env_loading.load_env_enterprise()" && python main.py

echo.
echo ============================================================================
echo   DocXP Backend Stopped
echo ============================================================================