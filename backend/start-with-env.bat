@echo off
REM ============================================================================
REM DocXP Backend Startup with Proper Environment Loading
REM Ensures AWS credentials are properly loaded from .env.enterprise
REM ============================================================================

echo.
echo ============================================================================
echo   DocXP Backend Startup with Environment Configuration
echo ============================================================================
echo.

REM Step 1: Load environment variables from .env.enterprise
echo [1/4] Loading environment from .env.enterprise...

if exist ".env.enterprise" (
    echo   - Loading .env.enterprise file...
    
    REM Parse and set environment variables from .env.enterprise
    for /f "usebackq tokens=1,2 delims==" %%a in (".env.enterprise") do (
        if not "%%a"=="" (
            if not "%%a"=="REM" (
                if not "%%a"=="#" (
                    set "%%a=%%b"
                    echo     %%a=%%b
                )
            )
        )
    )
) else (
    echo   - ERROR: .env.enterprise file not found!
    echo   - Please ensure .env.enterprise exists in backend directory
    pause
    exit /b 1
)

echo.
echo [2/4] Setting AWS environment variables explicitly...
set AWS_PROFILE=msh
set AWS_REGION=us-east-1
set AWS_DEFAULT_REGION=us-east-1

echo   - AWS_PROFILE=%AWS_PROFILE%
echo   - AWS_REGION=%AWS_REGION%

echo.
echo [3/4] Verifying AWS credentials...
aws sts get-caller-identity --profile %AWS_PROFILE% >nul 2>&1
if errorlevel 1 (
    echo   - ERROR: AWS profile '%AWS_PROFILE%' not working
    echo   - Please run: aws sso login --profile %AWS_PROFILE%
    pause
    exit /b 1
) else (
    echo   - ✅ AWS profile '%AWS_PROFILE%' verified
)

echo.
echo [4/4] Starting DocXP Backend...
echo   - Environment loaded: .env.enterprise
echo   - AWS Profile: %AWS_PROFILE%
echo   - Starting on http://localhost:8001
echo.
echo ============================================================================
echo   DocXP Backend Starting with Proper AWS Configuration
echo ============================================================================
echo.

REM Start the Python application with all environment variables set
python main.py

echo.
echo ============================================================================
echo   DocXP Backend Stopped
echo ============================================================================