@echo off
echo =================================================
echo   DocXP V1 Local-First Stack Startup
echo =================================================
echo.

echo Checking dependencies...
where podman >nul 2>&1
if errorlevel 1 (
    echo ERROR: Podman not found. Please install Podman Desktop.
    pause
    exit /b 1
)

echo ✓ Podman found

echo.
echo Checking environment file...
if not exist .env (
    echo WARNING: .env file not found. Copying from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your AWS credentials before proceeding.
    echo.
    pause
)

echo ✓ Environment file exists

echo.
echo Starting DocXP V1 services...
echo This will start:
echo - OpenSearch (single-node with auto-detection)
echo - PostgreSQL (with golden questions)
echo - Redis (queue + caching)
echo - MinIO (S3-compatible storage)
echo - FastAPI Backend (with auto-setup)
echo - RQ Worker (background jobs)
echo.

podman-compose up --build

echo.
echo =================================================
echo   DocXP V1 Services Started
echo =================================================
echo.
echo Access points:
echo - Backend API: http://localhost:8000
echo - API Documentation: http://localhost:8000/docs
echo - Health Check: http://localhost:8000/health
echo - OpenSearch: http://localhost:9200
echo - MinIO Console: http://localhost:9001
echo.
echo Logs are available in ./logs/
echo.
pause